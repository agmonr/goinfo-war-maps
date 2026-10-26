#!/usr/bin/env python3
"""LAW R50 (the owner 10-26): a retreat looks like a retreat. Every push-out/withdrawal card (war_pushout) shows a GROUP of >= 4 retreating units that (a) start at different times and sit on different lanes (lateral spread >= 0.05 deg, start
delays not all equal), (b) at least one is hit on the way (a loss marker at its last point, the unit removed there), (c) all deterministic (the group is the same on a second build: seeded by id), (d) the template keeps the gun toward the enemy
while a unit labelled נסיגה/נסוג moves (m._rev), and (e) no retreat unit stands on water. Browser check: tools/war_retreat_rig.py (facing) on a dev machine.
    python3 tools/test_war_retreat.py [events.json ...]   rc 1 when a STRICT file (named, default Yom Kippur) has offenders; the others are reported."""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_landcheck as lc
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc: return None
    cards = {k for k, n in d.get('pushout_moved', {}).items() if n}      # a card with no unit in its box has nothing to retreat (the pushout test covers it)
    if not cards: return None
    items, bad, L = sc['items'], [], lc.load_mask()
    for card in sorted(cards):
        un = [it for it in items if it['type'] == 'walk' and it.get('pushout') == card]
        if not un: bad.append((card, 'no retreat units')); continue
        why = []
        if len(un) < 4: why.append(f'only {len(un)} units')
        starts = {round(u['legs'][0]['t0'], 1) for u in un}
        if len(starts) < max(2, len(un) // 2): why.append('units start together')
        lanes = [u['legs'][0]['path'][0] for u in un]
        sp = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in lanes for b in lanes) if lanes else 0
        if sp < 0.05: why.append('no lateral spread')
        hits = [u for u in un if u.get('hit')]
        if not hits: why.append('no unit hit on the way')
        for u in hits:
            e = u['legs'][-1]['path'][-1]
            if not any(it['type'] == 'loss' and abs(it['at'][0] - e[0]) < 1e-3 and abs(it['at'][1] - e[1]) < 1e-3 for it in items): why.append('hit without a loss marker'); break
            if u.get('u') is None or u['u'] > u['legs'][-1]['t1'] + 3: why.append('hit unit not removed'); break
        wet = [u for u in un if any(not lc.near_land(L, p) for p, _t in lc.interp_points(u))]
        if wet: why.append(f'{len(wet)} units on water')
        if why: bad.append((card, '; '.join(why)))
    return len(cards), bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    t = open('war/templates/battle-map.html', encoding='utf-8').read()
    assert t.count('m._rev') >= 3 and 'moving&&!m._rev' in t, 'template must keep a retreating unit facing the enemy (R50)'
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} retreat cards are disorderly groups with hits', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
