#!/usr/bin/env python3
"""R45 (the owner 10-26): after a card that says a force was pushed out of an area, no unit of that side stands inside it (8 scene-seconds after the card). Specs live in each generator (PUSHOUT); this checks the DATA: for every
spec recorded in the event file (ev['pushout_specs']) the count of that side's units still in the box is 0.   python3 tools/test_war_pushout.py [events.json ...]"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_pushout as wp
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
fail = 0
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8')); specs = d.get('pushout_specs') or []
    if not specs: continue
    sc = d['scene']; bad = []
    for sp in specs:
        c = next((x for x in d['events'] if x['id'] == sp['card']), None)
        a = wp.act_of(sc, c)
        if not a: bad.append(sp['card'] + ' (no act)'); continue
        left = wp.units_in_box(sc['items'], sp['side'], sp['box'], a['s'] + 8)
        if left: bad.append(f"{sp['card']}: {len(left)} still there")
    print(f"{f}: {len(specs) - len(bad)}/{len(specs)} pushed-out cards leave the area empty", ('FAIL ' + ', '.join(bad)) if bad else 'ok')
    if bad and f in explicit: fail += len(bad)
sys.exit(1 if fail else 0)
