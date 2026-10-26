#!/usr/bin/env python3
"""LAW (the owner 10-26): EVERY card that describes a battle (land, sea, air: battle / attack / assault / raid / shelling / clash / dogfight words) is animated with the FIGHTING FORCES of both sides in contact at the
place, in the card's window. Not only the heavy-loss cards (tools/test_war_heavy_losses.py adds the loss marker for those). A card the sources give no place for is judged at the place of its drawn items
(it needs both sides drawn near each other somewhere in its window); a card with `fight_ok` is exempt with its reason (none yet).
    python3 tools/test_war_battles.py [events.json ...]   rc 1 when a STRICT file (named, default Yom Kippur) has offenders; the others are reported."""
import glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es, test_war_heavy_losses as hl
from war_keywords import BATTLE      # one shared keyword list (the owner 10-26)
R, WIN = 0.45, 60.0
def fighting(items, w0, w1, pl, need_both=True):
    il, ar = [], []
    for it in items:
        a, b = es.span(it)
        if b < w0 or a > w1 or it['type'] in ('boom', 'mark', 'loss', 'note', 'sam', 'shell'): continue
        sd = hl.side(it)
        if sd: (il if sd == 'il' else ar).append(es.pts(it))
    def near(P, c): return any(math.hypot(p[0] - c[0], p[1] - c[1]) <= R for pts in P for p in pts)
    if pl: return any(near(il, c) for c in pl) and any(near(ar, c) for c in pl) if need_both else None
    # no place in the data: both sides must be drawn within R of each other
    return any(math.hypot(p[0] - q[0], p[1] - q[1]) <= R for A in il for p in A for B in ar for q in B)
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc or not any('min' in a for a in sc.get('acts', [])): return None
    acts, items, places, bad, n = sc['acts'], sc['items'], d.get('places', {}), [], 0
    for c in d['events']:
        if not BATTLE.search(c['title'] + ' ' + c['quote']) or c.get('fight_ok'): continue
        cand = [x for x in acts if x.get('min') == c.get('start_min')]
        a = next((x for x in cand if c['title'][:12] in x['clock']), None) or (cand[0] if cand else None)
        if not a:
            near = min((x for x in acts if x.get('min') is not None), key=lambda x: abs(x['min'] - c['start_min']), default=None)
            a = near if near and abs(near['min'] - c['start_min']) <= 90 else None
        if not a: continue
        n += 1
        pl = [(places[g['place']]['lat'], places[g['place']]['lon']) for g in c.get('geometry', []) if g.get('place') in places]
        if not fighting(items, a['s'], a['s'] + WIN, pl): bad.append(c['id'])
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} battle cards animate both fighting sides', ('FAIL ' + ', '.join(r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
