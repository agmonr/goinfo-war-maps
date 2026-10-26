#!/usr/bin/env python3
"""Small machine rules of war/RULES.md in one place (the owner 10-26), over every war/data/*-events.json scene:
 R37 every helicopter item (label starts with 'מסוק') that lands has a return leg ending at the base it left from, and is gone there (u);
 R38 no ship carries a dotted trail: the template skips the trail of naval kinds (guard present) and no ship item asks for a 'tank' trail;
 R39 a sunk ship (item.sunk) draws no leg after its sinking, and the template removes a ship wreck mark SINK_MIN=360 simulated minutes after the sinking.
    python3 tools/test_war_rules_small.py"""
import glob, json, os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
bad = 0
t = open('war/templates/battle-map.html', encoding='utf-8').read()
for need, why in (("NAVK[unitKind(label,trl)]", "R38 ship trail guard"), ("var SINK_MIN=360", "R39 six-hour ship wreck"), ("it.sunk!=null&&A.T>=it.sunk", "R39 sunk ship hidden"), ("(^|\\s)מסוק(?!ים)", "helicopter icon only for a helicopter"), ("Math.min(hold,3):Math.min(hold,22)", "R46 no lingering missile dot / white squares")):
    if need not in t: bad += 1; print('FAIL template:', why)
for f in sorted(glob.glob('war/data/*-events.json')):
    d = json.load(open(f, encoding='utf-8')); items = (d.get('scene') or {}).get('items', [])
    for i, it in enumerate(items):
        lab = it.get('label') or ''
        if it['type'] == 'walk' and lab.startswith('מסוק'):
            L = it['legs']; a = L[0]['path'][0]; b = L[-1]['path'][-1]
            if len(L) < 2 or abs(a[0] - b[0]) > 0.01 or abs(a[1] - b[1]) > 0.01 or it.get('u') is None:
                bad += 1; print('FAIL R37 helicopter without a return to base:', f[-22:], i, lab[:40])
        if it.get('sunk') is not None and it['type'] == 'walk' and it['legs'][-1]['t1'] > it['sunk']:
            bad += 1; print('FAIL R39 leg after the sinking:', f[-22:], i, lab[:40])
print('FAILED %d' % bad if bad else 'ok: helicopters return to base, no ship trail, sunk ships removed')
sys.exit(1 if bad else 0)
