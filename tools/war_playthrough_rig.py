"""Play-through rig (a dev machine: ~/pw-venv/bin/python -I tools/war_playthrough_rig.py URL [speed_clicks] [max_wall_s]).
Plays a war page from the start at fast speed and asserts: the scene clock strictly advances, no JS error, no stall longer than STALL s of wall time, the end of the scene is reached.
Prints JSON: reached_end, errors, stalls [(T, wall_s)], samples every 1 s. GA/wa blocked, UA goinfo-test/site-playthrough."""
import sys, json, time
from playwright.sync_api import sync_playwright
U = sys.argv[1]; CLICKS = int(sys.argv[2]) if len(sys.argv) > 2 else 3; MAXW = float(sys.argv[3]) if len(sys.argv) > 3 else 420
STALL = 4.0
errs, stalls, samples = [], [], []
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-playthrough')
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.on('console', lambda m: errs.append('console.error: ' + m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto(U + ('&' if '?' in U else '?') + 'intro=0', wait_until='load'); pg.wait_for_timeout(3000)
    for _ in range(CLICKS): pg.evaluate("document.getElementById('aSp')&&document.getElementById('aSp').click()") if False else pg.keyboard.press('+')
    pg.evaluate("window.__a67.A.playing||document.getElementById('aPlay').click()")
    t0 = time.time(); last_T = -1; last_move = time.time(); end = False
    while time.time() - t0 < MAXW:
        pg.wait_for_timeout(500)
        s = pg.evaluate("({T:window.__a67.A.T,pl:window.__a67.A.playing,DUR:window.__a67.A.DUR,sp:window.__a67.A.sp,cur:window.__a67.A.cur})")
        now = time.time()
        if s['T'] > last_T + 1e-6: last_move = now; last_T = s['T']
        elif s['pl'] and now - last_move > STALL:
            stalls.append((round(s['T'], 2), round(now - last_move, 1)))
            last_move = now
        if int((now - t0) * 2) % 2 == 0: samples.append((round(now - t0), round(s['T'], 1), s['sp'], s['cur']))
        if s['T'] >= s['DUR'] - 0.05 or (not s['pl'] and s['T'] > 1): end = s['T'] >= s['DUR'] - 0.5; break
    b.close()
out = dict(reached_end=end, errors=errs[:10], stalls=stalls, last_sample=samples[-1] if samples else None, n=len(samples))
print(json.dumps(out, ensure_ascii=False))
if errs or stalls or not end: sys.exit(1)
