#!/usr/bin/env python3
"""A war page must make SOUND: play ~12 s from just before its first sound cue with sound on and assert audio nodes were created (the owner 2026-10-23: Yom Kippur had none).
  python3 tools/war_one_build.py /tmp/ws yomkippur && python3 tools/test_war_sfx_play.py --stage /tmp/ws --page war/1973/yomkippur/map/    (needs playwright + Chrome; run on a dev machine)
Also asserts the scene has a non-empty cue track and the three movement loops are in the stage (war/sound/)."""
import argparse, functools, http.server, json, socketserver, sys, threading
from pathlib import Path
INIT = """(()=>{window.__aud={osc:0,src:0};const AC=window.AudioContext||window.webkitAudioContext;const O=AC.prototype.createOscillator,S=AC.prototype.createBufferSource;
AC.prototype.createOscillator=function(){window.__aud.osc++;return O.apply(this,arguments)};AC.prototype.createBufferSource=function(){window.__aud.src++;return S.apply(this,arguments)}})()"""
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--page", required=True); ap.add_argument("--chrome", default="/usr/bin/google-chrome"); a = ap.parse_args()
    ev = json.loads((Path(a.stage) / a.page.replace("map/", "") / "events.json").read_text(encoding="utf-8"))
    cues = ev["scene"]["sfx"]; bad = 0
    def chk(n, c):
        nonlocal bad
        print(("PASS " if c else "FAIL ") + n); bad += 0 if c else 1
    chk(f"scene has a cue track ({len(cues)} cues)", len(cues) > 0)
    chk("movement loops in the stage (war/sound/*.mp3)", all((Path(a.stage) / "war" / "sound" / f).exists() for f in ("tank.mp3", "jet.mp3", "march.mp3")))
    ncards = len(ev.get("events") or [])
    chk(f"cue density: {len(cues)} cues for {ncards} cards (>= 3 per card: attacks drawn as arrows carry cues too)", len(cues) >= 3 * ncards)
    if cues:
        socketserver.TCPServer.allow_reuse_address = True
        srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.stage))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=a.chrome, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            pg = b.new_context(viewport={"width": 1200, "height": 800}).new_page(); pg.route("**/*google*", lambda r: r.abort()); pg.add_init_script(INIT)
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); mp3 = []
            pg.on("response", lambda r: mp3.append((r.url, r.status)) if ".mp3" in r.url else None)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/{a.page}index.html"); pg.wait_for_timeout(2000)
            pg.click("#aSnd"); pg.wait_for_timeout(300)                      # the visitor's gesture: sound on
            t0 = min(c[0] for c in cues)
            pg.evaluate(f"()=>window.__a67.seek({max(0, t0 - 2)})"); pg.wait_for_timeout(300)
            pg.evaluate("()=>{if(!window.__a67.A.playing)document.getElementById('aPlay').click()}")
            pg.wait_for_timeout(12000)
            aud = pg.evaluate("()=>window.__aud")
            chk(f"audio nodes created while playing 12 s ({aud})", aud["osc"] + aud["src"] > 0)
            chk(f"every audio URL the page requested returns 200 ({len(mp3)} requests)", bool(mp3) and all(st == 200 for _, st in mp3))
            starts = sorted(c["start_min"] for c in ev["events"]); acts = sorted(ev["scene"].get("acts") or [], key=lambda x: x["s"])
            for k in sorted({0, len(acts) // 2, len(acts) - 1}) if acts else []:     # sampled cards: a 7 s window from the card's own start must make sound (the 1947-48 "no sound" class)
                pg.evaluate("()=>{window.__aud.osc=0;window.__aud.src=0}"); pg.evaluate(f"()=>window.__a67.seek({acts[k]['s']})"); pg.wait_for_timeout(7000)
                w = pg.evaluate("()=>window.__aud"); chk(f"7 s from act {k} ({acts[k]['clock'][:30]}) makes sound ({w})", w["osc"] + w["src"] > 0)
            chk("no page errors", not errs)
            b.close()
    sys.exit(1 if bad else 0)
if __name__ == "__main__":
    main()
