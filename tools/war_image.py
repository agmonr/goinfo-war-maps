#!/usr/bin/env python3
"""Static image of a battle's key moment (repeatable step for every battle in /war/).

  python3 tools/war_image.py --stage DIR --battle 1967-04-07 --out IMAGES_DIR      (needs: playwright + Chrome; run on a dev machine)

Serves the stage (tools/war_build.py output) on localhost, opens the battle's own map page in "still" mode (?still=<seconds> from the
battle json: the key moment) at 1200x630 and writes IMAGES_DIR/<battle>/og.jpg (the og:image) and still.jpg (the inline image).
The still shows the map, the units at that moment and the permanent line "אנימציה סכמטית - בסיסים ומסלולים אינם מדויקים · מקור:
ויקיפדיה העברית, CC BY-SA 4.0". Map tiles come from OpenStreetMap on the fly (needs network); nothing else is fetched.
"""
import argparse, functools, http.server, json, socketserver, threading
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--battle", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    a = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    meta = json.loads((root / "war" / "data" / f"{a.battle}.json").read_text(encoding="utf-8"))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.stage)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    out = Path(a.out) / a.battle; out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=a.chrome, args=["--no-sandbox"])
        pg = b.new_context(user_agent="goinfo-test/war-image", viewport={"width": 1200, "height": 630}, locale="he-IL").new_page()
        pg.route("**/*", lambda r: r.abort() if any(k in r.request.url for k in ("googletagmanager", "google-analytics", "wa.goinfo")) else r.continue_())
        base = f"http://127.0.0.1:{port}/war/{meta['year']}/{meta['slug']}/"
        shots = [("map/?still=%s" % meta["still_t"], "og.jpg", "still.jpg")] if not meta.get("multi") else [(f"map/?still={meta['still_ts']['all']}&area=all", None, "still-all.jpg")] + [(f"map/?still={meta['still_ts'][t['id']]}&area={t['id']}", None, f"still-{t['id']}.jpg") for t in meta["areas"]]
        for rel, og, name in shots:
            pg.goto(base + rel, wait_until="networkidle"); pg.wait_for_timeout(3500)      # tiles load after the map is laid out
            pg.screenshot(path=str(out / name), type="jpeg", quality=86)
            if og:
                (out / og).write_bytes((out / name).read_bytes())
        if meta.get("multi"):                                                              # og:image = the whole-front still
            (out / "og.jpg").write_bytes((out / "still-all.jpg").read_bytes())
        b.close()
    srv.shutdown()
    print("wrote", out / "og.jpg", (out / "og.jpg").stat().st_size, "bytes")

if __name__ == "__main__":
    main()
