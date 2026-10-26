"""Recorded-track rig for the war heading rule (a dev machine): python tools/war_spin_rig.py URL T0 T1 STEP OUT.json records every ground-unit marker (screen x, y, heading) per seek; then analyse() counts spin events (heading change >= 40 deg while moving < 4 px, or >= 150 deg of turning within 6 s with < 12 px net). Six-Day live before the fix: 12 events on 7 of 26 tanks (one 260 deg turn with 0 px); after: 1."""
import json,sys
from playwright.sync_api import sync_playwright
U=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8000/war/1973/yomkippur/map/'
T0=float(sys.argv[2]) if len(sys.argv)>2 else 380; T1=float(sys.argv[3]) if len(sys.argv)>3 else 395
STEP=float(sys.argv[4]) if len(sys.argv)>4 else 0.25
OUT=sys.argv[5] if len(sys.argv)>5 else '/tmp/spin.json'
with sync_playwright() as p:
  b=p.chromium.launch(channel='chrome'); pg=b.new_page(viewport={'width':1100,'height':800},user_agent='goinfo-test/site-spin')
  pg.route('**/*',lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager','google-analytics','wa.goinfo')) else r.continue_())
  pg.goto(U,wait_until='load'); pg.wait_for_timeout(5000)
  print(pg.evaluate("Object.keys(window.__a67||{})"))
  res=pg.evaluate("""([a,b,STEP])=>{const out=[];const A=window.__a67;A.map().setView([30.6,32.55],11,{animate:false});
    for(let T=a;T<=b;T+=STEP){A.seek(T);const tanks=[...document.querySelectorAll('.ap.gu .rot')].filter(e=>e.parentElement.parentElement.style.opacity!=='0'&&getComputedStyle(e.closest('.leaflet-marker-icon')).opacity>0.05);
      out.push([T,tanks.map(e=>{const m=e.closest('.leaflet-marker-icon');const tr=m.style.transform;const mm=/translate3d\\(([-\\d.]+)px, ([-\\d.]+)px/.exec(tr)||[0,0,0];const rot=/rotate\\(([-\\d.]+)deg\\)/.exec(e.style.transform);return [Math.round(+mm[1]*10)/10,Math.round(+mm[2]*10)/10,rot?Math.round(+rot[1]):null]})])}
    return out}""",[T0,T1,STEP])
  json.dump(res,open(OUT,'w'))
  print(len(res),'frames; tanks visible per frame',[len(r[1]) for r in res][:12])
  b.close()


# ---- analysis ----
import math
def dh(a,b): return (b-a+180)%360-180
def analyse(fn,step):
    fr=json.load(open(fn)); n=max(len(f[1]) for f in fr)
    ev=[]
    for i in range(n):
        seq=[(f[0],f[1][i]) for f in fr if i<len(f[1])]
        # events: heading change >=40deg in one step with displacement <4px
        for k in range(len(seq)-1):
            (t0,a),(t1,b)=seq[k],seq[k+1]
            if a[2] is None or b[2] is None: continue
            d=math.hypot(b[0]-a[0],b[1]-a[1]); h=abs(dh(a[2],b[2]))
            if h>=40 and d<4: ev.append((i,t0,round(h),round(d,1)))
        # circling: cumulative |dheading| >=180 within 6s while net displacement <12px
        w=int(6/step)
        for k in range(0,len(seq)-w,max(1,w//3)):
            seg=seq[k:k+w+1]
            if any(s[1][2] is None for s in seg): continue
            cum=sum(abs(dh(seg[j][1][2],seg[j+1][1][2])) for j in range(len(seg)-1))
            net=math.hypot(seg[-1][1][0]-seg[0][1][0],seg[-1][1][1]-seg[0][1][1])
            if cum>=150 and net<12: ev.append((i,seg[0][0],'circle',round(cum),round(net,1)))
    tanks=sorted({e[0] for e in ev})
    return n,len(ev),tanks,ev[:8]
