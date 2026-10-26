"""Shot-down rig (a dev machine: ~/pw-venv/bin/python -I tools/war_shotdown_rig.py URL [SHOTDIR]): every fly item with a `down` block must (1) be in the air before the hit, (2) fall: smoke trail, plane scaled below 1 and still visible mid-fall,
(3) after the crash: plane gone (opacity 0), crash burst then a wreck mark at the crash point. Count of wreck marks == count of down items. Also with prefers-reduced-motion: no arc, wreck mark right after the hit."""
import sys, json
from playwright.sync_api import sync_playwright
U = sys.argv[1]; SH = sys.argv[2] if len(sys.argv) > 2 else None
JS = """(a)=>{const A=window.__a67.A,S=A.scene,e=A.E.s,i=a.i,res={};A.T=a.T;window.__a67.seek(a.T);
 const m=e['s'+i],w=e['s'+i+'wr'],sm=e['s'+i+'sm'];res.plane=m&&m._icon?+getComputedStyle(m._icon).opacity:null;
 const r=m&&m._icon&&m._icon.querySelector('.rot');res.tf=r?r.style.transform:'';res.wreck=w&&w._icon?+getComputedStyle(w._icon).opacity:0;res.smoke=sm?sm[0].options.opacity:0;
 res.ll=m?[m.getLatLng().lat,m.getLatLng().lng]:null;return res}"""
out = {'items': [], 'fail': []}
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    for rm in (False, True):
        ctx = b.new_context(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-shotdown', reduced_motion='reduce' if rm else 'no-preference')
        pg = ctx.new_page(); pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
        pg.goto(U + '?intro=0', wait_until='load'); pg.wait_for_timeout(3500)
        pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()"); pg.evaluate("window.__a67.map().setView([29.5,33],6,{animate:false})")
        items = pg.evaluate("window.__a67.A.scene.items.map((x,i)=>x.down?[i,x.down.t,x.down.dur,x.label]:null).filter(Boolean)")
        for k, (i, t, dur, lab) in enumerate(items):
            r0 = pg.evaluate(JS, {'i': i, 'T': t - 0.3}); pg.wait_for_timeout(50)
            r1 = pg.evaluate(JS, {'i': i, 'T': t + dur * 0.5}); r2 = pg.evaluate(JS, {'i': i, 'T': t + dur + 1.0}); r3 = pg.evaluate(JS, {'i': i, 'T': t + dur + 4})
            if k == 0 and SH and not rm:
                for nm, T in (('0', t - 0.3), ('1', t + dur * 0.5), ('2', t + dur + 0.4), ('3', t + dur + 4)):
                    pg.evaluate(JS, {'i': i, 'T': T}); pg.evaluate("(ll)=>window.__a67.map().setView(ll,9,{animate:false})", r0['ll']); pg.wait_for_timeout(250); pg.screenshot(path=f'{SH}/down_{nm}.png')
            ok = r0['plane'] is not None and r0['plane'] > .05 and (r1['wreck'] > .3 if rm else (r1['smoke'] and r1['plane'] and r1['plane'] > .3)) and not r2['plane'] and r2['wreck'] > .3 and r3['wreck'] > .3 and not r0['wreck']
            if not ok: out['fail'].append([lab, r0, r1, r2, r3, 'reduced' if rm else ''])
            if not rm: out['items'].append(lab)
        ctx.close()
    b.close()
print(json.dumps({'down_items': len(out['items']), 'fail': out['fail'][:3], 'n_fail': len(out['fail'])}, ensure_ascii=False))
sys.exit(1 if out['fail'] or not out['items'] else 0)
