#!/usr/bin/env python3
"""LAW R53 (the owner 10-26: "the Hermon battle looks like it happens in the south-east of the Golan"): a battle card with a PLACE is drawn AT that place. Every fire item (shell arc ends, impact bursts: key "fire" = card id) and every forced-in fighter ("fill" = card id) made for the card
lies within ANC degrees of the card's own place; the fallback "nearest pair of opposing items" never moves the fight away - when the pair is not at the place the missing side is drawn at the place instead. Also for each placed battle card at least one fire item exists at the place.
    python3 tools/test_war_anchor.py [events.json ...]   rc 1 when a STRICT file (named, default Yom Kippur) has offenders; the others are reported."""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from war_keywords import BATTLE
ANC = 0.12 + 0.03
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc: return None
    places, items, bad, n = d.get('places', {}), sc['items'], [], 0
    for c in d['events']:
        if not BATTLE.search(c['title'] + ' ' + c['quote']) or c.get('fight_ok'): continue
        pl = [(places[g['place']]['lat'], places[g['place']]['lon']) for g in c.get('geometry', []) if g.get('place') in places]
        if not pl: continue
        n += 1; far = []
        for it in items:
            if it.get('fire') != c['id'] and it.get('fill') != c['id']: continue
            pts = [it['at']] if it['type'] == 'boom' else [it['from'], it['to']] if it['type'] == 'shell' else [p for l in it.get('legs', []) for p in l.get('path', [])]
            for p in pts:
                if min(math.hypot(p[0] - la, p[1] - lo) for la, lo in pl) > ANC: far.append(round(min(math.hypot(p[0] - la, p[1] - lo) for la, lo in pl), 2)); break
        if far: bad.append((c['id'], f'{len(far)} fire/fill items up to {max(far)} deg from the card place'))
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} placed battle cards fight at their own place', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
