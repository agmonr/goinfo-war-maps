"""Next-event rig (a dev machine: ~/pw-venv/bin/python -I tools/war_nextevent_rig.py URL): click the next-event button while paused -> the clock jumps to the next card AND runs; click previous -> same; a pause after stays paused."""
import sys, json
from playwright.sync_api import sync_playwright
U = sys.argv[1]; R = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-nextevent')
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0&autoreturn=0', wait_until='load'); pg.wait_for_timeout(3000)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")      # paused
    S = "({T:+window.__a67.A.T.toFixed(2),pl:window.__a67.A.playing})"
    R['paused_start'] = pg.evaluate(S)
    pg.click('#aNext'); pg.wait_for_timeout(200); a = pg.evaluate(S); pg.wait_for_timeout(1200); c = pg.evaluate(S)
    R['next'] = dict(after_click=a, after_1_2s=c, advancing=c['T'] > a['T'] and c['pl'])
    pg.click('#aPrev'); pg.wait_for_timeout(200); a = pg.evaluate(S); pg.wait_for_timeout(1200); c = pg.evaluate(S)
    R['prev'] = dict(after_click=a, after_1_2s=c, advancing=c['T'] > a['T'] and c['pl'])
    pg.click('#aPlay'); pg.wait_for_timeout(300); t1 = pg.evaluate(S); pg.wait_for_timeout(800); t2 = pg.evaluate(S)
    R['pause_stays'] = dict(playing=t2['pl'], still=t1['T'] == t2['T'])
    b.close()
print(json.dumps(R, ensure_ascii=False))
sys.exit(0 if R['next']['advancing'] and R['prev']['advancing'] and not R['pause_stays']['playing'] and R['pause_stays']['still'] else 1)
