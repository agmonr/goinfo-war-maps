"""Trail rig (a dev machine: ~/pw-venv/bin/python -I tools/war_trail_rig.py URL [STEP]): R52 (the owner 10-26: no trails at sea, no soldier on the water). Seeks through the whole scene every STEP scene-seconds (default 8) and reads every drawn dotted trail / arrow line / smoke trail (A.E.s polylines, items with
water_ok excepted): each vertex must be on LAND (the page's own land mask, window.__dn.onLand). Also: no soldier/unit tip marker of an arrow with area sea / water_ok is visible. Prints counts and the first offenders; rc 1 on any."""
import sys, json
from playwright.sync_api import sync_playwright
U = sys.argv[1]; STEP = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
JS = """(a)=>{const A=window.__a67.A,S=A.scene,e=A.E.s,dn=window.__dn,bad=[];let n=0;
 const flat=(ll)=>{const o=[];(function f(x){if(Array.isArray(x))x.forEach(f);else if(x&&x.lat!==undefined)o.push(x)})(ll);return o};
 for(let T=0;T<=S.dur;T+=a.step){window.__a67.seek(T);
  S.items.forEach((it,i)=>{ if(it.water_ok)return; const ks=['s'+i,'s'+i+'tr','s'+i+'sm','s'+i+'t'];
   ks.forEach(k=>{const h=e[k];if(!h)return;(Array.isArray(h)?h:[h]).forEach(p=>{ if(!p||!p.getLatLngs||!p._path||(+p.options.opacity)<=0.05)return; if(p.options.color==='#e0301e')return; /* shell arcs are fire, not trails */
     flat(p.getLatLngs()).forEach(q=>{n++;if(!dn.onLand(q)&&bad.length<12)bad.push([T,i,k,(it.label||'').slice(0,28),+q.lat.toFixed(3),+q.lng.toFixed(3)])})})})});
 }return {n,bad}}"""
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1100, 'height': 760}, user_agent='goinfo-test/site-trails')
    pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0', wait_until='load'); pg.wait_for_timeout(4000)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()"); pg.evaluate("window.__a67.map().setView([31.5,34.5],6,{animate:false})")
    r = pg.evaluate(JS, {'step': STEP})
    print(json.dumps({'vertices_checked': r['n'], 'on_water': len(r['bad']), 'first': r['bad'][:6]}, ensure_ascii=False))
    sys.exit(1 if r['bad'] else 0)
