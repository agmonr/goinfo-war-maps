#!/usr/bin/env python3
"""War pages (the owner 10-22): scene.cas_t = {casualty card id: hit time}. A casualty record of an AIR attack shows only when the attack lands, never earlier than the record.
Checks: every id names a card of that day, the time is a real scene time, it is not earlier than the card's own time, and the template applies it; a wreck fades after WRECK_MIN."""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(H, '..', 'war')
cas = json.load(open(os.path.join(R, 'data', '1967-casualties.json')))['data']
DAYS = {'05': 'jun', '06': 'jun6', '07': 'jun7', '08': 'jun8', '09': 'jun9', '10': 'jun10'}
bad = 0
for d, key in DAYS.items():
    sc = json.load(open(os.path.join(R, 'data', f'1967-06-{d}-events.json')))['scene']
    cards = {c['id']: c for c in cas[key]}
    for cid, t in (sc.get('cas_t') or {}).items():
        c = cards.get(cid)
        if not c: print('FAIL', d, cid, 'no such card'); bad += 1; continue
        if not (0 <= t <= sc['dur']): print('FAIL', d, cid, 'time outside the scene'); bad += 1
        if t < c['t']: print('FAIL', d, cid, 'hit time earlier than the record', t, c['t']); bad += 1
        if not c.get('at'): print('FAIL', d, cid, 'card has no place, nothing to delay'); bad += 1
tpl = open(os.path.join(R, 'templates', 'battle-map.html'), encoding='utf8').read()
for needle in ('S.cas_t', 'WRECK_MIN=180', 'WRECK_FADE'):
    if needle not in tpl: print('FAIL template lacks', needle); bad += 1
js = open(os.path.join(R, 'daynight.js'), encoding='utf8').read()
if "kind === 'inf') return" not in js: print('FAIL foot-soldier echelon badge is back'); bad += 1
print('ok' if not bad else f'{bad} FAIL'); sys.exit(1 if bad else 0)
