#!/usr/bin/env python3
"""War maps (?daynight=1), aircraft multiplier rule (the owner 10-21: "4 drawn, 12 real -> x3"): a flight of N <= 4 aircraft is drawn with N aircraft and no label; N > 4 is a 4-aircraft wing with
the label x(max(2, round(N/4))) and the real number in the tooltip. Plays every 1967 page forward, finds every flight marker and checks drawn count + label against the item's own number.
    python3 tools/test_war_wings.py http://localhost:8000 [chrome]    (playwright + Chrome; goinfo-test UA, Google blocked)"""
import sys
from playwright.sync_api import sync_playwright
BASE = sys.argv[1].rstrip('/'); CHROME = sys.argv[2] if len(sys.argv) > 2 else '/usr/bin/google-chrome'
PAGES = ['7-april', '5-june', '6-june', '7-june', '8-june', '9-june', '10-june']
JS = """()=>{var A=window.__a67,S=A.A.E.s,IT=A.A.scene.items,out=[];Object.keys(S).forEach(function(k){var mm=/^s(\\d+)$/.exec(k);if(!mm)return;var it=IT[+mm[1]];if(!it||it.type!=='fly')return;var m=S[k],e=m.getElement&&m.getElement();if(!e||!e.getAttribute('data-dn'))return;
 var rot=e.querySelector('.rot'),forms=rot?rot.querySelectorAll('.dn-form').length+1:0,cn=e.querySelector('.dn-cnt');out.push([+mm[1],it.label||'',forms,cn?cn.textContent:'',cn?cn.getAttribute('title'):'',window.__dn.wings().filter(w=>w.i===+mm[1])[0].n])});return out}"""
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 390, 'height': 780}, user_agent='goinfo-test'); ctx.route('**/*google*', lambda r: r.abort()); ctx.route('**/wa.goinfo.co.il/**', lambda r: r.abort())
    pg = ctx.new_page()
    for s in PAGES:
        pg.goto('%s/war/1967/%s/map/index.html?daynight=1' % (BASE, s)); pg.wait_for_timeout(2500)
        if not pg.evaluate("!!window.__dn && !!window.__dn.wings"): print(s, 'no day/night layer'); continue
        seen = {}; T = 0.0
        while T < 262:
            pg.evaluate("T=>window.__a67.seek(T)", T)
            for i, lab, forms, txt, title, n in pg.evaluate(JS): seen[i] = (lab, forms, txt, title, n)
            T += 1.0
        mult = 0
        for i, (lab, forms, txt, title, n) in sorted(seen.items()):
            sort = 'תקיפות' in lab
            exp_forms = min(4, max(1, n)); exp_txt = '' if (n <= 4 or sort) else '×%d' % max(2, round(n / 4))
            if n > 4 and not sort: mult += 1
            if forms != exp_forms or txt != exp_txt or (n > 4 and not sort and str(n) not in (title or '')):
                bad += 1; print('FAIL', s, i, lab, 'N=%d drawn %d (want %d) label %r (want %r) title %r' % (n, forms, exp_forms, txt, exp_txt, title))
        print('%-8s flights %2d | with a multiplier %2d | examples: %s' % (s, len(seen), mult, [(n, txt) for (lab, forms, txt, title, n) in seen.values() if n > 4 and 'תקיפות' not in lab][:4]))
    b.close()
print('FAILED %d' % bad if bad else 'ok'); sys.exit(1 if bad else 0)
