#!/usr/bin/env python3
"""Sound on the /war/ maps: the AudioContext must reach "running" after the visitor's first gesture, the speaker button must toggle (and remember),
and the visitor must be told that sound is off. Real Chrome, desktop and phone emulation.

  python3 tools/war_build.py --stage /tmp/ws && python3 tools/test_war_sound.py --stage /tmp/ws     (needs playwright + Chrome; run on a dev machine)

History: 2026-10-19 the owner: "it looks like there is no sound". Causes found: (1) the sound hint lived in a HUD that the day pages do not show, so
nothing said sound was off; (2) only phones unlocked audio on the first tap; (3) the desktop speaker button passed its click event as the `auto`
argument, so it could only turn sound ON; (4) on phones the first tap on the speaker ran the unlock AND the button toggle, turning it off again.
"""
import argparse, functools, http.server, socketserver, sys, threading
INIT = """(()=>{window.__aud={osc:0,src:0};const AC=window.AudioContext||window.webkitAudioContext;const O=AC.prototype.createOscillator,S=AC.prototype.createBufferSource;
AC.prototype.createOscillator=function(){window.__aud.osc++;return O.apply(this,arguments)};AC.prototype.createBufferSource=function(){window.__aud.src++;return S.apply(this,arguments)};})();"""
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--chrome", default="/usr/bin/google-chrome"); a = ap.parse_args()
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.stage))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/war/1967/"
    from playwright.sync_api import sync_playwright
    res = []
    def chk(n, c):
        res.append((n, bool(c))); print(("PASS " if c else "FAIL ") + n)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=a.chrome, args=["--no-sandbox"])
        for dev, w, h, touch in (("desktop", 1280, 800, False), ("phone", 390, 844, True)):
            for scen in ("anywhere", "button", "key"):
                if touch and scen == "key":
                    continue
                c = b.new_context(user_agent="goinfo-test/war-sound", viewport={"width": w, "height": h}, locale="he-IL", has_touch=touch, is_mobile=touch)
                c.add_init_script(INIT)
                c.route("**/*", lambda r: r.abort() if any(k in r.request.url for k in ("googletagmanager", "google-analytics", "wa.goinfo")) else r.continue_())
                pg = c.new_page(); pg.goto(base + "6-june/", wait_until="load"); pg.wait_for_timeout(3500)
                fr = [f for f in pg.frames if f.url.rstrip("/").endswith("/map")][0]; tag = f"{dev}/{scen}: "
                btn = "#aSndM" if touch else "#aSnd"
                chk(tag + "visitor is told sound is off", fr.evaluate("!document.getElementById('sndToast').hidden"))
                if scen == "anywhere":
                    fr.locator("body").tap(position={"x": 200, "y": 300}) if touch else fr.locator("body").click(position={"x": 300, "y": 400})
                elif scen == "button":
                    fr.locator(btn).tap() if touch else fr.locator(btn).click()
                else:
                    fr.evaluate("window.focus()"); pg.keyboard.press("Space")
                pg.wait_for_timeout(1500)
                st = fr.evaluate("({muted:__a67.A.muted,state:__a67.A.ctx&&__a67.A.ctx.state,toast:document.getElementById('sndToast').hidden,btn:document.getElementById('aSnd').textContent})")
                chk(tag + "AudioContext running, not muted, 🔊, toast gone", st["muted"] is False and st["state"] == "running" and st["btn"] == "🔊" and st["toast"])
                fr.evaluate("(()=>{__a67.A.sp=1;const r=document.getElementById('aT');r.value=1200;r.dispatchEvent(new Event('input',{bubbles:true}))})()"); pg.wait_for_timeout(2500)
                aud = fr.evaluate("window.__aud"); chk(tag + "audio nodes are created while the animation runs", aud["osc"] + aud["src"] > 0)
                if scen == "button":
                    fr.locator(btn).tap() if touch else fr.locator(btn).click(); pg.wait_for_timeout(600)
                    s2 = fr.evaluate("({muted:__a67.A.muted,pref:localStorage.getItem('apr67snd')})"); chk(tag + "second press turns it off and remembers", s2["muted"] and s2["pref"] == "off")
                    pg.reload(wait_until="load"); pg.wait_for_timeout(3000); fr = [f for f in pg.frames if f.url.rstrip("/").endswith("/map")][0]
                    chk(tag + "after reload it stays off and does not nag", fr.evaluate("__a67.A.muted && (!document.getElementById('sndToast') || document.getElementById('sndToast').hidden)"))
                c.close()
        b.close()
    bad = [n for n, o in res if not o]
    print("FAILED:", bad)
    sys.exit(1 if bad else 0)
if __name__ == "__main__":
    main()
