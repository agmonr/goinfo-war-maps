"""Seek screenshot (a dev machine: ~/pw-venv/bin/python -I tools/war_seek_shot.py URL T LAT LON ZOOM OUT.png): open the war page, seek to scene time T, centre on LAT/LON at ZOOM, screenshot (before/after pairs for the owner; GA blocked)."""
import sys
from playwright.sync_api import sync_playwright
U, T, LA, LO, Z, OUT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1100, 'height': 760}, user_agent='goinfo-test/site-seekshot')
    pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + ('&' if '?' in U else '?') + 'intro=0', wait_until='load'); pg.wait_for_timeout(3500)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")
    pg.evaluate("(a)=>{window.__a67.seek(a[0]);window.__a67.map().setView([a[1],a[2]],a[3],{animate:false})}", [T, LA, LO, Z]); pg.wait_for_timeout(700)
    pg.screenshot(path=OUT); b.close()
