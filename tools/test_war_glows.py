#!/usr/bin/env python3
"""War maps (?daynight=1): DOM checks on what is DRAWN, every scene, scrubbed every 0.5 s (the owner 10-21).
  1. every visible impact glow is centred on its marker coordinate (<= 2 px) at three zoom levels
  2. every visible glow has a drawn unit symbol (tank / flight / foot / gun) within 15 km, on screen; else it must be a quiet mark
  3. the two tanks are centred on the unit's true position and never drawn in the sea (a unit whose own position is in the sea is listed as DATA, not a failure)
  4. the two tanks of a moving column lie ON the heading line (offset between them parallel to their rotation, <= 6 deg), one behind the other
  python3 tools/test_war_glows.py http://localhost:8000 [scene,scene] ; needs playwright + Chrome; sets UA goinfo-test and blocks Google (GA law)."""
import sys
from playwright.sync_api import sync_playwright
BASE = sys.argv[1].rstrip('/')
SC = sys.argv[2].split(',') if len(sys.argv) > 2 else ['5-june', '6-june', '7-june', '8-june', '9-june', '10-june']
import os
ZS = tuple(int(x) for x in os.environ.get('ZOOMS', '7,9,11').split(','))
CHROME = sys.argv[3] if len(sys.argv) > 3 else '/usr/bin/google-chrome'
JS = """()=>{var A=window.__a67,M=A.map(),S=A.A.E.s,IT=A.A.scene.items,sz=M.getSize(),R={g:[],u:[],t:[]};
function vis(m,t){return m&&m.options&&m.options.opacity>t}
Object.keys(S).forEach(function(k){var m=S[k],mm=/^s(\\d+)(o?)(t?)(g?)$/.exec(k);if(!m||!m.getLatLng||!mm)return;var it=IT[+mm[1]];if(!it)return;var ll=m.getLatLng(),pt=M.latLngToContainerPoint(ll);
 if(it.type==='boom'&&!mm[2]&&!mm[3]&&!mm[4]&&vis(m,0.3)){var el=m.getElement().firstChild,r=el.getBoundingClientRect(),c=M.getContainer().getBoundingClientRect();
   R.g.push({k:k,op:m.options.opacity,it:JSON.stringify(it).slice(0,80),px:pt.x,py:pt.y,dx:r.left+r.width/2-c.left-pt.x,dy:r.top+r.height/2-c.top-pt.y,ll:[ll.lat,ll.lng],on:pt.x>=0&&pt.y>=0&&pt.x<=sz.x&&pt.y<=sz.y});return}
 if(vis(m,0.15)&&((it.type==='arrow'&&mm[3])||((it.type==='walk'||it.type==='fly')&&!mm[2]&&!mm[3]&&!mm[4])||(it.type==='shell'&&mm[4]))){if(pt.x>=-10&&pt.y>=-10&&pt.x<=sz.x+10&&pt.y<=sz.y+10)R.u.push({k:k,ll:[ll.lat,ll.lng]})}
 if(it.trail==='tank'&&(it.type==='walk'||it.type==='arrow')&&vis(m,0.5)&&!mm[2]&&!mm[4]){var tk=m.getElement().querySelectorAll('.dn-tank');if(tk.length===2){var a=tk[0].getBoundingClientRect(),b=tk[1].getBoundingClientRect(),
   mv=it.type==='walk'?(it.legs||[]).some(function(l){return A.A.T>=l.t0&&A.A.T<=l.t1}):(A.A.T>=it.t0&&A.A.T<=it.t1),rot=/rotate\\((-?[\\d.]+)deg\\)/.exec(tk[0].style.transform);
   var cp=M.latLngToContainerPoint(m.getLatLng()),cr=M.getContainer().getBoundingClientRect(),ic=function(r){return M.containerPointToLatLng([r.left+r.width/2-cr.left,r.top+r.height/2-cr.top])};
   R.t.push({k:k,mx:(a.left+a.width/2+b.left+b.width/2)/2-cr.left-cp.x,my:(a.top+a.height/2+b.top+b.height/2)/2-cr.top-cp.y,sea:[!window.__land(ic(a)),!window.__land(ic(b))],seaC:!window.__land(m.getLatLng()),mv:mv,vx:(b.left+b.width/2)-(a.left+a.width/2),vy:(b.top+b.height/2)-(a.top+a.height/2),rot:rot?+rot[1]:null})}}});
R.d=function(){};return R}"""
DIST = "([a,b])=>window.__a67.map().distance(a,b)"
bad = []
data = set()
with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    ctx = br.new_context(viewport={'width': 390, 'height': 780}, user_agent='goinfo-test')
    ctx.route('**/*google*', lambda r: r.abort()); ctx.route('**/wa.goinfo.co.il/**', lambda r: r.abort())
    pg = ctx.new_page(); nglow = ntank = 0
    for s in SC:
        pg.goto('%s/war/1967/%s/map/index.html?daynight=1' % (BASE, s)); pg.wait_for_timeout(2500)
        pg.evaluate("""async(u)=>{const L=await (await fetch(u)).json();window.__land=function(ll){var y=ll.lat,x=ll.lng;if(y<27||y>35||x<31||x>37.5)return true;for(var r=0;r<L.length;r++){var ring=L[r],c=false;for(var i=0,n=ring.length;i<n;i++){var a=ring[i?i-1:n-1],b=ring[i];if((a[1]>x)!==(b[1]>x)&&y<(b[0]-a[0])*(x-a[1])/(b[1]-a[1])+a[0])c=!c}if(c)return true}return false}}""", '%s/war/1967/%s/land-mask.json' % (BASE, s))
        for z in ZS:
            pg.evaluate("z=>window.__a67.map().setView([30.9,34.0],z,{animate:false})", z)
            T = 0.0
            while T < 262:
                pg.evaluate("T=>window.__a67.seek(T)", T)
                r = pg.evaluate(JS)
                for g in r['g']:
                    if not g['on']: continue
                    nglow += 1
                    if abs(g['dx']) > 2 or abs(g['dy']) > 2: bad.append((s, z, T, g['k'], 'glow centre off its coordinate by', round(g['dx']), round(g['dy']), 'px'))
                    if z == 9:
                        near = min([pg.evaluate(DIST, [g['ll'], u['ll']]) for u in r['u']], default=1e9)
                        if near > 15000: bad.append((s, z, T, g['k'], 'glow with no drawn unit within 15 km (nearest %d km) op=%s %s' % (near / 1000 if near < 1e8 else -1, g['op'], g['it'])))
                if z == 9:
                    import math
                    for t in r['t']:
                        if (t['sea'][0] or t['sea'][1]) and not t['seaC']: bad.append((s, z, T, t['k'], 'tank icon drawn in the sea although the unit position is on land'))
                        if t['seaC']: data.add((s, t['k']))
                        if t['mv'] is not None and (abs(t['mx']) > 2 or abs(t['my']) > 2): bad.append((s, z, T, t['k'], 'tank pair not centred on the unit position, off by %d,%d px' % (t['mx'], t['my'])))
                        if not t['mv'] or t['rot'] is None or math.hypot(t['vx'], t['vy']) < 3: continue
                        d = abs(((math.degrees(math.atan2(t['vy'], t['vx'])) - t['rot']) + 90) % 180 - 90)
                        ntank += 1
                        if d > 6: bad.append((s, z, T, t['k'], 'moving tank pair not on the heading line, off by %d deg' % d))
                T += 0.5
    br.close()
print('glow frames checked %d, moving tank-pair frames %d, failures %d' % (nglow, ntank, len(bad)))
print('units whose own position is in the sea (data, not failures):', sorted(data))
seen = set()
for b in bad:
    key = (b[0], b[3], str(b[4])[:24])
    if key in seen: continue
    seen.add(key); print(*b)
sys.exit(1 if bad else 0)
