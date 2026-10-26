"""Stopped/hold rig (a dev machine: ~/pw-venv/bin/python -I tools/war_stopped_rig.py URL OUTDIR): for each card in events.json "stopped" it seeks to before / during / after the stop and screenshots the place (zoom 10); prints per card the count of visible loss
markers (opacity>.3), visible stopped-side units, visible airplanes (Skyhawks) at 'during'. Reads the markers from the page's own markers (window.__a67.A.E.s)."""
import sys, json
from playwright.sync_api import sync_playwright
U, OUT = sys.argv[1], sys.argv[2]
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1100, 'height': 760}, user_agent='goinfo-test/site-stopped')
    pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0', wait_until='load'); pg.wait_for_timeout(3500)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")
    sp = pg.evaluate("window.__a67.A.scene.stopped||null")
    d = json.loads(pg.evaluate("fetch('../events.json').then(r=>r.text())")) if sp is None else None
    st = (d or {}).get('stopped') if sp is None else sp
    for cid, s in st.items():
        out = {}
        for nm, dt in (('before', -6), ('during', 2), ('after', 9)):
            pg.evaluate("(a)=>{window.__a67.seek(a)}", s['T'] + dt); pg.evaluate("(ll)=>window.__a67.map().setView(ll,10,{animate:false})", s['at']); pg.wait_for_timeout(500)
            out[nm] = pg.evaluate("""(a)=>{const A=window.__a67.A,e=A.E.s,r={loss:0,fly:0};A.scene.items.forEach((it,i)=>{const m=e['s'+i];if(!m||!m._icon)return;const o=+getComputedStyle(m._icon).opacity;if(o<=.3)return;
              if(it.type==='loss'&&Math.hypot(it.at[0]-a[0],it.at[1]-a[1])<.5)r.loss++;if(it.type==='fly'&&/סקייהוק/.test(it.label||''))r.fly++});return r}""", s['at'])
            pg.screenshot(path=f'{OUT}/stop_{cid}_{nm}.png')
        res[cid] = out
    b.close()
print(json.dumps(res, ensure_ascii=False))
