#!/usr/bin/env python3
"""War maps (?daynight=1), the schematic-enemy rule (the owner 10-21): when one of our tanks is within 8 km of an impact (a tank fight), the page shows the other side there:
enemy armour already drawn within 8 km -> nothing added; none drawn -> three foot soldiers with a DASHED ring ("schematic, no unit record"), opposite side colour.
Scrubs every 1967 page forward every 0.5 s like a play-through and prints, per page: impacts, tank fights, enemy armour present (no symbol), inferred symbols added; FAILS when a visible
inferred symbol is not a dashed ring with three soldiers, or the legend line is hidden while one is visible. Counts are impacts with one of our drawn tanks within 8 km; an air strike near our tanks counts too (the owner 10-22: only GROUND fire, i.e. impacts whose sound-track entry is 'cannon', can get a schematic enemy; air strikes (boom) and bombing (thud) never do).
    python3 tools/test_war_inferred.py http://localhost:8000 [chrome-path]   (needs playwright + Chrome; goinfo-test UA, Google blocked)"""
import sys
from playwright.sync_api import sync_playwright
BASE = sys.argv[1].rstrip('/'); CHROME = sys.argv[2] if len(sys.argv) > 2 else '/usr/bin/google-chrome'
PAGES = ['7-april', '5-june', '6-june', '7-june', '8-june', '9-june', '10-june']
JS = """()=>{var s=window.__dn.inferState(),dots=[...document.querySelectorAll('.dn-inf')].filter(e=>{var m=e.closest('.leaflet-marker-icon');return m&&parseFloat(m.style.opacity||1)>0.05});
return {decided:s.decided,shown:s.shown,vis:dots.map(e=>[getComputedStyle(e).borderStyle,getComputedStyle(e).color,e.querySelectorAll('svg').length]),leg:(document.getElementById('dnInfLeg')||{}).hidden}}"""
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 390, 'height': 780}, user_agent='goinfo-test'); ctx.route('**/*google*', lambda r: r.abort()); ctx.route('**/wa.goinfo.co.il/**', lambda r: r.abort())
    pg = ctx.new_page()
    for s in PAGES:
        pg.goto('%s/war/1967/%s/map/index.html?daynight=1' % (BASE, s)); pg.wait_for_timeout(2500)
        if not pg.evaluate("!!window.__dn && !!window.__dn.inferState"): print(s, 'no daynight layer (static page)'); continue
        nboom = pg.evaluate("window.__a67.A.scene.items.filter(i=>i.type==='boom').length"); dec = {}; T = 0.0
        while T < 262:
            pg.evaluate("T=>window.__a67.seek(T)", T); r = pg.evaluate(JS)
            for k, v in r['decided']:
                dec[k] = v
                if v and not pg.evaluate("i=>{var A=window.__a67.A,t=A.scene.items[i].t;return A.sfx.some(x=>x[1]==='cannon'&&Math.abs(x[0]-t)<0.05)}", int(k.replace('inf', ''))):
                    bad += 1; print('FAIL', s, T, 'inferred enemy at a non-ground-fire impact (air strike / bombing)', k)
            for st, col, n in r['vis']:
                if st != 'dashed' or n != 3: bad += 1; print('FAIL', s, T, 'inferred symbol not dashed / not 3 soldiers', st, n)
            if r['vis'] and r['leg']: bad += 1; print('FAIL', s, T, 'legend hidden while an inferred symbol is shown')
            T += 0.5
        sym = sum(1 for v in dec.values() if v); armour_or_none = sum(1 for v in dec.values() if not v)
        print('%-8s impacts %3d | decided %3d | inferred foot-soldier symbols %3d | no symbol (armour present or no tank near) %3d' % (s, nboom, len(dec), sym, armour_or_none))
    b.close()
print('FAILED %d' % bad if bad else 'ok'); sys.exit(1 if bad else 0)
