#!/usr/bin/env python3
"""R40 (the owner 10-26: "there is no sound" at a Yom Kippur sea battle): every animated item type that makes a noise has a sound cue at its start - boom, fly, arrow, shell, loss: a cue within 1.5 s in scene.sfx.
Lists the uncovered items per war (YK strict; Six-Day/Kadesh/Independence/civil reported, they get cover() from their generators)."""
import bisect, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_sfx
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
fail = 0
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8')); sc = d.get('scene') or {}
    if not sc.get('items'): continue
    have = sorted(c[0] for c in sc.get('sfx', []))
    miss = {}
    for it in sc['items']:
        if it['type'] not in war_sfx.CUE_TYPES: continue
        t = war_sfx.start_of(it)
        if t is None: continue
        i = bisect.bisect_left(have, t - 1.5)
        if i >= len(have) or have[i] > t + 1.5: miss[it['type']] = miss.get(it['type'], 0) + 1
    print(f'{f}: ' + ('ok' if not miss else 'silent items ' + json.dumps(miss)))
    if miss and f in explicit: fail += 1
sys.exit(1 if fail else 0)
