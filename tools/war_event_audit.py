"""Every card of a war page must SHOW something at its time (the owner 10-26: "go over all the events and make sure they are displayed").
Run on a dev machine: ~/pw-venv/bin/python -I tools/war_event_audit.py URL DATA.json OUT.json
For each card: seek into its act window, list the scene elements that are visible (marker with opacity>0, path with stroke/fill opacity>0) and find those within RADIUS deg of the card's places.
Verdict: Y (a visible element at its place), C (no place in the sources: caption on the map says so), E (visible elements in the window, none at its place), N (nothing visible), T (text-only card: no place in the data, something visible elsewhere or nothing)."""
import sys, json, math
from playwright.sync_api import sync_playwright
U, DATA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
RADIUS = 0.45
D = json.load(open(DATA, encoding='utf-8'))
cards = D['events']; acts = D['scene']['acts']; places = D['places']
def places_of(c):
    out = []
    for g in c.get('geometry', []):
        p = places.get(g.get('place'))
        if p: out.append((p['lat'], p['lon']))
    return out
JS = """() => {const A=window.__a67.A,out=[];const g=A.E.g;g.eachLayer(l=>{try{
 if(l.getLatLng&&l._icon){const o=+getComputedStyle(l._icon).opacity;if(o>0.05&&l._icon.style.display!=='none'){const ll=l.getLatLng();if(ll.lat||ll.lng)out.push(['m',ll.lat,ll.lng,o])}}
 else if(l._path&&l.getBounds){const o=Math.max(l.options.opacity||0,l.options.fillOpacity||0);if(o>0.05){const c=l.getBounds().getCenter();out.push(['p',c.lat,c.lng,o])}}}catch(e){}});return out}"""
res = []
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome'); pg = b.new_page(viewport={'width': 1280, 'height': 800}, user_agent='goinfo-test/site-audit')
    pg.route('**/*', lambda r: r.abort() if any(x in r.request.url for x in ('googletagmanager', 'google-analytics', 'wa.goinfo')) else r.continue_())
    pg.goto(U + '?autoreturn=0', wait_until='load'); pg.wait_for_timeout(4000)
    pg.evaluate("window.__a67.A.playing&&document.getElementById('aPlay').click()")
    pg.evaluate("window.__a67.map().setView([31.2,33.5],7,{animate:false})")
    for i, c in enumerate(cards):
        cand = [x for x in acts if x.get('min') == c.get('start_min')]
        a = next((x for x in cand if c['title'][:12] in x['clock']), None) or (cand[0] if cand else None)
        if not a and c.get('start_min') is not None:
            near = min((x for x in acts if x.get('min') is not None), key=lambda x: abs(x['min'] - c['start_min']), default=None)
            a = near if near and abs(near['min'] - c['start_min']) <= 90 else None
        if not a:
            res.append(dict(id=c['id'], verdict='N', why='no act')); continue
        pl = places_of(c); seen = []
        pg.evaluate("T=>window.__a67.seek(T)", max(0, a['s'] - 0.4)); pg.wait_for_timeout(120); base = pg.evaluate(JS)
        isnew = lambda x: not any(abs(x[1] - y[1]) < 0.004 and abs(x[2] - y[2]) < 0.004 and x[0] == y[0] for y in base)
        for dt in (0.15, 0.6, 1.5, 3, 6, 10):
            T = a['s'] + dt
            pg.evaluate("T=>window.__a67.seek(T)", T); pg.wait_for_timeout(120)
            els = [x for x in pg.evaluate(JS) if isnew(x)]
            cap = pg.evaluate("(document.getElementById('evn')||{}).textContent||''")
            if cap and c['title'][:25] in cap: els.append(['c', 0, 0, 1])
            seen.append((dt, els))
        near = any(math.hypot(x[1] - la, x[2] - lo) <= RADIUS for _, els in seen for x in els for la, lo in pl)
        anyv = any(els for _, els in seen)
        capd = any(x[0] == 'c' for _, els in seen for x in els)
        v = ('Y' if near else 'E' if anyv else 'N') if pl else ('C' if capd else 'T' if anyv else 'T0')
        first = next((dt for dt, els in seen if any(math.hypot(x[1] - la, x[2] - lo) <= RADIUS for x in els for la, lo in pl)), None) if pl else None
        res.append(dict(id=c['id'], t=c.get('time_label'), title=c['title'][:70], area=c.get('area'), places=[g.get('place') for g in c.get('geometry', [])],
                        nopos=c.get('no_position'), verdict=v, first_visible_dt=first, n_elems=[len(e) for _, e in seen]))
    b.close()
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
import collections
print(collections.Counter(r['verdict'] for r in res))
