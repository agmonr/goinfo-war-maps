#!/usr/bin/env python3
"""LAW (the owner 10-26): a card that names a battle with heavy losses must SHOW the battle: both fighting sides drawn in contact at the place, and a loss marker (item type 'loss': burning wreck icons, a count only when the source gives one).
For every war/data/*-events.json scene and every card whose title/quote says heavy losses / destroyed / sunk (keywords below): in the card's act window [s, s+WIN] there must be
 (a) at least one item of each side (blue Israeli / red other side) with a point within R degrees of the card's place (or of the card's own loss marker when the card has no place), and
 (b) at least one 'loss' item within R of the place whose time is in the window.
A card whose text names heavy losses but is not a battle drawn by us may carry "heavy_ok": reason on its card dict (none yet).
    python3 tools/test_war_heavy_losses.py [events.json ...]   rc 1 when a STRICT file (named on the command line, default the Yom Kippur file) has offenders; the others are reported."""
import glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es
KW = re.compile(r'(?<![א-ת])(?:אבדות(?: מצריות| סוריות)? כבדות|ספג\w* אבדות כבדות|הושמד(?:ה|ו|ים)?|הוטבע(?:ו)?|טובע|נסוגה בכבדות|המחיר היה כבד|הטבח)(?![א-ת])')   # NOT a bare 'כבדות' ("heavy mortars" is not heavy losses)
import war_keywords as kw      # stopped / hold / supreme families (the owner 10-26)
R, WIN = 0.45, 60.0
def side(it):
    s = it.get('side') or it.get('cls') or it.get('color') or ''
    if s in ('iaf', '#1d5ea8', 'il') or it.get('cls') == 'iaf': return 'il'
    if s in ('ar', 'syr', '#b3261e'): return 'ar'
    return None
def sides_near(items, w0, w1, pl):
    got = set()
    for it in items:
        a, b = es.span(it)
        if b < w0 or a > w1: continue
        sd = side(it)
        if not sd or it['type'] in ('boom', 'mark', 'loss', 'note', 'sam'): continue
        if any(math.hypot(p[0] - la, p[1] - lo) <= R for p in es.pts(it) for la, lo in pl): got.add(sd)
    return got
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc or not any('min' in a for a in sc.get('acts', [])): return None
    acts, items, places, bad, n = sc['acts'], sc['items'], d.get('places', {}), [], 0
    for c in d['events']:
        if not (KW.search(c['title'] + ' ' + c['quote']) or any(kw.hits(c['title'] + ' ' + c['quote']).values())) or c.get('heavy_ok') or (c.get('stopped_ok') and not KW.search(c['title'] + ' ' + c['quote'])): continue
        cand = [x for x in acts if x.get('min') == c.get('start_min')]
        a = next((x for x in cand if c['title'][:12] in x['clock']), None) or (cand[0] if cand else None)
        if not a: continue
        n += 1; w0, w1 = a["s"], a["s"] + WIN   # a card's battle can be drawn minutes of war time after the card begins (night battles)
        pl = [(places[g['place']]['lat'], places[g['place']]['lon']) for g in c.get('geometry', []) if g.get('place') in places]
        loss = [it for it in items if it['type'] == 'loss' and w0 - 1 <= it['t'] <= w1 and (not pl or any(math.hypot(it['at'][0] - la, it['at'][1] - lo) <= R for la, lo in pl))]
        # the Six-Day pages' own loss marker: a casualty record with a map point (the face symbol) at the place, dated in the window
        cas = [x for x in d.get('casualties', []) if x.get('at') and w0 - 5 <= x.get('t', -1e9) <= w1 + 5 and (not pl or any(math.hypot(x['at'][0] - la, x['at'][1] - lo) <= R for la, lo in pl))]
        loss = loss or cas
        if not pl and loss: pl = [tuple((loss[0].get('at')))]
        sd = sides_near(items, w0, w1, pl) if pl else set()
        why = [x for x, ok in (('no loss marker', bool(loss)), ('no Israeli force at the place', 'il' in sd), ('no other-side force at the place', 'ar' in sd)) if not ok]
        if why: bad.append((c['id'], '; '.join(why)))
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} heavy-loss cards show the fight + loss', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
