"""Next-event rig (a dev machine: ~/pw-venv/bin/python -I tools/war_nextevent_rig.py URL): click next-event while paused -> the clock jumps to the next card AND runs, AND the camera focuses on the event (its place inside the view, near its centre);
previous the same; a pause after stays paused."""
import sys, json
from playwright.sync_api import sync_playwright
U = sys.argv[1]; R = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-nextevent')
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0&autoreturn=0', wait_until='load'); pg.wait_for_timeout(3000)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")
    S = "({T:+window.__a67.A.T.toFixed(2),pl:window.__a67.A.playing})"
    V = """()=>{const m=window.__a67.map(),A=window.__a67.A,a=A.acts[A.cur],b=a.view,c=[(b[0][0]+b[1][0])/2,(b[0][1]+b[1][1])/2],B=m.getBounds(),ct=m.getCenter();return {centre_in_view:B.contains(c),dlat:+Math.abs(ct.lat-c[0]).toFixed(2),dlng:+Math.abs(ct.lng-c[1]).toFixed(2),span:+(B.getNorth()-B.getSouth()).toFixed(2)}}"""
    R['paused_start'] = pg.evaluate(S)
    for nm, btn in (('next', '#aNext'), ('prev', '#aPrev')):
        pg.click(btn); pg.wait_for_timeout(200); a = pg.evaluate(S); pg.wait_for_timeout(1800); c = pg.evaluate(S); v = pg.evaluate(V)
        R[nm] = dict(after_click=a, after=c, advancing=c['T'] > a['T'] and c['pl'], camera=v, focused=v['centre_in_view'] and v['dlat'] < v['span'] * .4)
    pg.click('#aPlay'); pg.wait_for_timeout(300); t1 = pg.evaluate(S); pg.wait_for_timeout(800); t2 = pg.evaluate(S)
    R['pause_stays'] = dict(playing=t2['pl'], still=t1['T'] == t2['T'])
    b.close()
print(json.dumps(R, ensure_ascii=False))
ok = all(R[k]['advancing'] and R[k]['focused'] for k in ('next', 'prev')) and not R['pause_stays']['playing'] and R['pause_stays']['still']
sys.exit(0 if ok else 1)
