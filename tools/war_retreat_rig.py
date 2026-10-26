"""Retreat rig (a dev machine: ~/pw-venv/bin/python -I tools/war_retreat_rig.py URL [SHOT.png]): for every retreat unit (walk with `retreat`) seek to the middle of its leg; the unit is moving AWAY from the enemy, yet its sprite must face the enemy
(Syrians retreating east face west = 225..315 deg; Egyptians retreating west face east = 45..135; Israelis the other way round). Prints facing + movement bearing per unit and fails when more than 1 unit points along its travel."""
import sys, json, math
from playwright.sync_api import sync_playwright
U = sys.argv[1]; SH = sys.argv[2] if len(sys.argv) > 2 else None
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); ctx = b.new_context(viewport={'width': 1100, 'height': 760}, user_agent='goinfo-test/site-retreat')
    pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?intro=0', wait_until='load'); pg.wait_for_timeout(3500)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")
    res = pg.evaluate("""()=>{const A=window.__a67.A,S=A.scene,out=[];const idx=[];S.items.forEach((it,i)=>{if(it.type==='walk'&&it.retreat&&!it.hit)idx.push(i)});
      const T0=Math.min(...idx.map(i=>S.items[i].legs[0].t0)),T1=Math.max(...idx.map(i=>S.items[i].legs[0].t1));
      window.__a67.seek(T0-1);window.__a67.map().setView([32.95,35.95],9,{animate:false});
      for(let T=T0;T<=T1;T+=0.5){window.__a67.seek(T);}
      idx.forEach(i=>{const it=S.items[i],lg=it.legs[0],tm=(lg.t0+lg.t1)/2;window.__a67.seek(lg.t0-1);window.__a67.seek(tm);const m=A.E.s['s'+i];if(!m||!m._icon){out.push({i,none:1});return}
        const r=m._icon.querySelector('.rot'),a=r?/rotate\\(([-\\d.]+)deg/.exec(r.style.transform):null,P=lg.path,dl=P[P.length-1][0]-P[0][0],dn=(P[P.length-1][1]-P[0][1])*.84,mv=(Math.atan2(dn,dl)*180/Math.PI+360)%360;
        out.push({i,label:it.label,face:a?((+a[1]%360)+360)%360:null,travel:mv,cls:it.cls})});return out}""")
    if SH: pg.screenshot(path=SH)
    bad = []
    for r in res:
        if r.get('none') or r['face'] is None: bad.append(r); continue
        d = abs(((r['face'] - r['travel'] + 540) % 360) - 180)      # 0 = faces along its travel
        r['dev'] = round(d)
        if d < 90: bad.append(r)
    print(json.dumps({'units': len(res), 'along_travel_or_missing': len(bad), 'sample': res[:3]}, ensure_ascii=False))
    sys.exit(1 if len(bad) > 1 else 0)
