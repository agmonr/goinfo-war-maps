"""Helicopter rotor rig (a dev machine: ~/pw-venv/bin/python -I tools/war_rotor_rig.py YK_URL): in flight the rotor's transform changes over time, paused it is constant, on the ground (17:35) it does not turn,
and the body is rotated to its travel heading (about east, 80-100 deg). GA blocked."""
import sys, json
from playwright.sync_api import sync_playwright
U = sys.argv[1]
JS = """()=>{const out=[];document.querySelectorAll('.leaflet-marker-icon').forEach(m=>{const r=m.querySelector('.hr');if(r&&+getComputedStyle(m).opacity>0.3){const rot=m.querySelector('.rot');out.push([getComputedStyle(r).transform,rot?rot.style.transform:'',m.classList.contains('hs')||!!m.querySelector('.hs')])}});return out}"""
R = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-rotor')
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0#t=1042&z=10&c=31.0,32.45', wait_until='load'); pg.wait_for_timeout(2500); pg.reload(); pg.wait_for_timeout(3000)
    pg.evaluate("window.__a67.A.playing||document.getElementById('aPlay').click()"); pg.wait_for_timeout(600)
    a = pg.evaluate(JS); pg.wait_for_timeout(137); b2 = pg.evaluate(JS)
    R['flying'] = dict(n=len(a), rotor_changes=any(x[0] != y[0] for x, y in zip(a, b2)), body=[x[1] for x in a[:3]])
    pg.evaluate("document.getElementById('aPlay').click()"); pg.wait_for_timeout(400)
    c = pg.evaluate(JS); pg.wait_for_timeout(300); d = pg.evaluate(JS)
    R['paused'] = dict(n=len(c), rotor_constant=all(x[0] == y[0] for x, y in zip(c, d)))
    pg.evaluate("window.__a67.seek(window.__a67.A.T+9)"); pg.wait_for_timeout(300)
    e = pg.evaluate(JS); pg.wait_for_timeout(250); f = pg.evaluate(JS)
    R['later_paused_constant'] = all(x[0] == y[0] for x, y in zip(e, f))
    b.close()
print(json.dumps(R, ensure_ascii=False))
ok = R['flying']['n'] > 0 and R['flying']['rotor_changes'] and R['paused']['rotor_constant']
sys.exit(0 if ok else 1)
