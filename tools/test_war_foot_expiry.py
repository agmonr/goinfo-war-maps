#!/usr/bin/env python3
"""R44 (the owner 10-26): a foot unit leaves the map 6 simulated hours after its last update: every foot item has `u`, and u <= the time of (last update + 6 h) (+ tolerance).   YK strict; the others reported."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_foot_expiry as fe
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
fail = 0
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8'))
    if not (d.get('scene') or {}).get('items') or not any('min' in a for a in d['scene'].get('acts', [])): continue
    ma, ta = fe.maps(d); bad = []
    foot = [it for it in d['scene']['items'] if fe.is_foot(it)]
    for it in [x for x in foot if not x.get('fill')]:     # the units brought in for a battle card (fill) live for that card's act
        u, _ = fe.expiry(d, it, ma, ta)
        if it.get('u') is None or it['u'] > max(u, fe.end_of(it) + 1.0) + 0.05: bad.append((it.get('label') or '')[:28])
    n, alive = fe.alive_counts(d)
    print(f"{f}: {len(foot) - len(bad)}/{len(foot)} foot units expire 6 sim-hours after their last update; alive at 25/50/90% of the scene: {alive}", ('FAIL ' + ', '.join(bad[:4])) if bad else 'ok')
    if bad and f in explicit: fail += len(bad)
sys.exit(1 if fail else 0)
