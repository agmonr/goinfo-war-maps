#!/usr/bin/env python3
"""Static class test (the owner 10-26): every card of a war scene must produce something visible at its time. For each war/data/*-events.json that has a scene:
 - a card with a place (geometry marker): at least one scene item alive in [act.s, act.s+12] with a point within 0.45 deg of that place;
 - a card with no place: at least one scene item (a 'note' caption counts) alive in that window.
Prints counts per war for every data file (information); the files named on the command line are STRICT: exit 1 when a card there is not shown (verify.sh names the Yom Kippur file). Items drawn elsewhere do not satisfy a card that has a place.
(The browser audit tools/war_event_audit.py checks the same in a real page.)"""
import glob, json, math, os, sys
R, WIN = 0.45, 12.0
def pts(it):
    t = it.get('type')
    if t in ('mark',): return [it['at']] if it.get('at') else []
    if t == 'boom': return [it['at']] if isinstance(it.get('at'), list) else []
    if t == 'arrow': return it.get('path') or []
    if t == 'sam': return [it['c']] if it.get('c') else []
    if t in ('walk', 'fly'): return [p for l in it.get('legs', []) for p in (l.get('path') or ([l['orbit']] if l.get('orbit') else []))]
    return []
def span(it):
    t = it.get('type')
    if t in ('walk', 'fly'):
        L = it['legs']; u = it.get('u'); return L[0]['t0'] - 6, (u if u is not None else (L[-1]['t1'] + 10 if t == 'fly' else 1e9))
    if t == 'arrow': u = it.get('u'); return it['t0'] - 6, (u if u is not None else it['t1'] + (it.get('hold') or 22))
    if t in ('mark', 'note'): return it['t0'], (it.get('t1') if it.get('t1') is not None else 1e9)
    if 't' in it: return it['t'], it['t'] + (it.get('dur') or 3) + 3
    return -1, -1
def check(path):
    d = json.load(open(path, encoding='utf-8'))
    sc = d.get('scene')
    if not sc or not sc.get('acts') or not any('min' in a for a in sc['acts']): return None   # per-day files (no act minutes) are the retired Six-Day pages; the whole-war events.json is tested instead
    places, acts, items, bad = d.get('places', {}), sc['acts'], sc['items'], []
    ok = 0
    for i, c in enumerate(d['events']):
        cand = [x for x in acts if x.get('min') == c.get('start_min')]
        a = next((x for x in cand if c['title'][:12] in x['clock']), None) or (cand[0] if cand else None)
        if not a and c.get('start_min') is not None:
            near = min((x for x in acts if x.get('min') is not None), key=lambda x: abs(x['min'] - c['start_min']), default=None)
            a = near if near and abs(near['min'] - c['start_min']) <= 90 else None
        if not a: bad.append((c['id'], 'no act')); continue
        w0, w1 = a['s'], a['s'] + WIN
        pl = [(places[g['place']]['lat'], places[g['place']]['lon']) for g in c.get('geometry', []) if g.get('place') in places]
        live = [it for it in items if span(it)[1] >= w0 and span(it)[0] <= w1]
        if pl: hit = any(math.hypot(p[0] - la, p[1] - lo) <= R for it in live for p in pts(it) for la, lo in pl)
        else: hit = bool(live)
        if hit: ok += 1
        else: bad.append((c['id'], 'place' if pl else 'nothing alive'))
    return len(d['events']), ok, bad
if __name__ == '__main__':
    fail = 0
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]   # default strict file: Yom Kippur
    import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[1]}/{r[0]} cards shown', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[2])) if r[2] else 'ok')
            if f in explicit: fail += len(r[2])
    sys.exit(1 if fail else 0)
