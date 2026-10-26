#!/usr/bin/env python3
"""R43 (the owner 10-26): every report of a surrender has a white flag above its place: each surrender mark ('נכנע' in a mark label) and each card whose text reports a surrender has a 'surrender' item in its window (near its place when
it has one). YK strict; the others reported.   python3 tools/test_war_surrender.py [events.json ...]"""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_surrender as ws
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
fail = 0
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8')); sc = d.get('scene') or {}
    acts = [x for x in sc.get('acts', []) if x.get('min') is not None]
    if not acts: continue
    items, places, bad, n = sc['items'], d.get('places', {}), [], 0
    fl = [x for x in items if x['type'] == 'surrender']
    for it in items:
        if it['type'] == 'mark' and 'נכנע' in (it.get('label') or ''):
            n += 1
            if not any(math.hypot(x['at'][0] - it['at'][0], x['at'][1] - it['at'][1]) < 0.01 for x in fl): bad.append(it['label'][:30])
    for c in d['events']:
        if not ws.SURR.search(c['title'] + ' ' + c['quote']): continue
        near = min(acts, key=lambda x: abs(x['min'] - c['start_min']))
        if abs(near['min'] - c['start_min']) > 90: continue
        n += 1; pl = [(places[g['place']]['lat'], places[g['place']]['lon']) for g in c.get('geometry', []) if g.get('place') in places]
        ok = any(near['s'] - 2 <= x['t'] <= near['s'] + 14 and (not pl or any(math.hypot(x['at'][0] - la, x['at'][1] - lo) <= ws.R for la, lo in pl)) for x in fl)
        if not ok: bad.append(c['id'])
    if n: print(f"{f}: {n - len(bad)}/{n} surrender reports have the white flag", ('FAIL ' + ', '.join(bad)) if bad else 'ok')
    if bad and f in explicit: fail += len(bad)
sys.exit(1 if fail else 0)
