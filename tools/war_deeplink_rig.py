"""Browser rig for the war deep links (a dev machine, Chrome + Firefox, 390/1280, GA aborted): python tools/war_deeplink_rig.py [URL of a war map page]. Checks: a #t=&z=&c= link restores time (paused, follow off), zoom and centre; the hash follows pan/zoom without growing history; invalid hashes fall back to the default view with no error; the copy button copies the current link."""
import json,sys
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8000/war/1967/six-days/map/'
with sync_playwright() as p:
  for bn,l in (('chrome',lambda:p.chromium.launch(channel='chrome')),('firefox',lambda:p.firefox.launch())):
    br=l()
    for w,h,tag in ((1280,800,'d'),(390,800,'m')):
      ctx=br.new_context(viewport={'width':w,'height':h},user_agent='goinfo-test/site-dl'); pg=ctx.new_page(); errs=[]; evs=[]
      pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
      pg.route('**/*',lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager','google-analytics','wa.goinfo')) else r.continue_())
      pg.goto(B,wait_until='load'); pg.wait_for_timeout(4500)
      m=pg.evaluate("(()=>{const A=window.__a67;const T=A.A.DUR*0.4;return [A.simMin(T),T]})()")
      # 1 restore
      url=B+'#t=%d&z=9&c=31.4,34.6'%round(m[0]); pg.goto('about:blank'); pg.goto(url,wait_until='load'); pg.wait_for_timeout(4500)
      st=pg.evaluate("(()=>{const A=window.__a67;const c=A.map().getCenter();return {T:A.A.T,playing:A.A.playing,follow:A.A.follow,z:A.map().getZoom(),c:[+c.lat.toFixed(2),+c.lng.toFixed(2)],hash:location.hash}})()")
      ok1=abs(st['T']-m[1])<A_TOL if False else abs(st['T']-m[1])<2
      print(bn,tag,'restore',st,'T~expected',round(m[1],1),'OK' if ok1 and not st['playing'] and not st['follow'] and st['z']==9 and st['c']==[31.4,34.6] else 'CHECK')
      # 2 pan updates hash, no history growth
      h0=pg.evaluate("history.length"); pg.evaluate("window.__a67.map().panBy([150,80],{animate:false});window.__a67.map().setZoom(8,{animate:false})"); pg.wait_for_timeout(900)
      print(bn,tag,'hash after pan/zoom',pg.evaluate("location.hash"),'history.length',h0,'->',pg.evaluate("history.length"))
      # 3 invalid
      for bad in ('#t=abc&z=99&c=x,y','#t=999999999','#z=','#c=100,500&z=5','#sinai','#t=&&=&'):
          pg.goto('about:blank'); pg.goto(B+bad,wait_until='load'); pg.wait_for_timeout(3000)
          print(bn,tag,'invalid',bad,'->',pg.evaluate("({T:window.__a67.A.T,z:window.__a67.map().getZoom()})"),'errors',errs[-1:] )
      # 4 copy button
      pg.goto('about:blank'); pg.goto(url,wait_until='load'); pg.wait_for_timeout(4000)
      pg.evaluate("window.__copied=null;window.goinfo&&(window.goinfo.ev=(n,o)=>{(window.__evs=window.__evs||[]).push([n,o])});try{navigator.clipboard.writeText=(t)=>{window.__copied=t;return Promise.resolve()}}catch(e){}")
      exists=pg.evaluate("!!document.getElementById('bLink')")
      if exists:
          pg.evaluate("document.getElementById('bLink').click()"); pg.wait_for_timeout(600)
          print(bn,tag,'copy',pg.evaluate("window.__copied"),pg.evaluate("window.__evs||null"),'toast',pg.evaluate("(document.getElementById('dlToast')||{}).textContent"))
      else: print(bn,tag,'NO bLink button')
      print(bn,tag,'overflow',pg.evaluate("document.documentElement.scrollWidth"),'errors',errs)
      if bn=='chrome': pg.screenshot(path=f'/tmp/dl-{tag}.png')
      ctx.close()
    br.close()
