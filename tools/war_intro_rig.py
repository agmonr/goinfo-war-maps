"""Opening-screen rig (a dev machine: ~/pw-venv/bin/python -I tools/war_intro_rig.py URL OUTDIR): the page opens PAUSED on the still map with the overlay (name, dates, both sides' casualties, source link); nothing moves for 9 s; the Start button (or a tap, or a key)
starts the play, unlocks audio (context running) and fires intro_start; #t= and ?intro=0 skip the overlay. Screenshots 1280 and 390. GA blocked, UA goinfo-test/site-intro."""
import sys, json
from playwright.sync_api import sync_playwright
U, OUT = sys.argv[1], sys.argv[2]
BLOCK = ('googletagmanager', 'google-analytics', 'wa.goinfo'); HOOK = "window.__evs=[];window.goinfo={ev:function(n,f){window.__evs.push([n,f&&f.v])}};"
R = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=document-user-activation-required'])
    for tag, vp, mob in (('1280', {'width': 1280, 'height': 800}, False), ('390', {'width': 390, 'height': 800}, True)):
        for how in ('button', 'tap'):
            ctx = b.new_context(viewport=vp, user_agent='goinfo-test/site-intro', has_touch=mob, is_mobile=mob); ctx.add_init_script(HOOK)
            pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in BLOCK) else r.continue_())
            pg.goto(U, wait_until='load'); pg.wait_for_timeout(1200)
            if how == 'button': pg.screenshot(path=f'{OUT}/intro_{tag}_1s.png')
            T0 = pg.evaluate("window.__a67.A.T"); pg.wait_for_timeout(7500)
            if how == 'button': pg.screenshot(path=f'{OUT}/intro_{tag}_8s.png')
            st = pg.evaluate("({T:window.__a67.A.T,pl:window.__a67.A.playing,ov:getComputedStyle(document.getElementById('intro')).display,src:!!document.querySelector('#iS a'),sides:document.querySelectorAll('#iC .nb').length})")
            if how == 'button': pg.click('#iGo')
            else: pg.mouse.click(vp['width'] // 2, 40) if not mob else pg.touchscreen.tap(vp['width'] // 2, 40)
            pg.wait_for_timeout(2200)
            aft = pg.evaluate("({T:window.__a67.A.T,pl:window.__a67.A.playing,body:document.body.className,ctx:window.__a67.A.ctx?window.__a67.A.ctx.state:null,ev:window.__evs.map(e=>e[0]+':'+e[1])})")
            R[f'{tag}_{how}'] = dict(T_start=T0, before=st, after=aft); ctx.close()
    # a visitor who muted earlier: the start tap turns sound on again (the owner 10-26); a deep link shows the card first and then plays from the linked moment
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-intro'); ctx.add_init_script("try{localStorage.setItem('apr67snd','off')}catch(e){}"); ctx.add_init_script(HOOK)
    pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in BLOCK) else r.continue_()); pg.goto(U.split('?')[0] + '#t=60', wait_until='load'); pg.wait_for_timeout(2500)
    R['deeplink_muted'] = dict(card=pg.evaluate("document.body.classList.contains('intro')"), paused=pg.evaluate("!window.__a67.A.playing"), T0=pg.evaluate("window.__a67.A.T")); pg.click('#iGo'); pg.wait_for_timeout(2500)
    R['deeplink_muted'].update(pg.evaluate("({pl:window.__a67.A.playing,T:window.__a67.A.T,muted:window.__a67.A.muted,ctx:window.__a67.A.ctx?window.__a67.A.ctx.state:null,pref:localStorage.getItem('apr67snd')})")); ctx.close()
    for name, url in (('intro0', U + '&intro=0' if '?' in U else U + '?intro=0'),):
        ctx = b.new_context(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-intro'); pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in BLOCK) else r.continue_())
        pg.goto(url, wait_until='load'); pg.wait_for_timeout(2500)
        R[name] = pg.evaluate("({intro:document.body.classList.contains('intro')})"); ctx.close()
    b.close()
print(json.dumps(R, ensure_ascii=False, indent=1))
ok = all(R[k]['before']['T'] == R[k]['T_start'] and not R[k]['before']['pl'] and R[k]['before']['ov'] != 'none' and R[k]['after']['pl'] and R[k]['after']['ctx'] == 'running' and any(e.startswith('intro_start') for e in R[k]['after']['ev']) for k in R if k[0].isdigit()) and not R['intro0']['intro'] and R['deeplink_muted']['card'] and R['deeplink_muted']['paused'] and R['deeplink_muted']['pl'] and R['deeplink_muted']['T'] > R['deeplink_muted']['T0'] and not R['deeplink_muted']['muted'] and R['deeplink_muted']['ctx'] == 'running' and R['deeplink_muted']['pref'] == 'on'
sys.exit(0 if ok else 1)
