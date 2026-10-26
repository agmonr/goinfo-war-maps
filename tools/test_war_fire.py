#!/usr/bin/env python3
"""R36 (the owner 10-26: "you see forces moving, not battles"): a battle card is VISIBLE when, in its window, shells of BOTH sides fly (muzzle burst, arc, impact), impact bursts land at the place, AND the two forces come within contact range (0.2 deg)
at the place. tools/war_battle_fire.py draws the fire where the data had only presence. YK strict; the other wars are reported.   python3 tools/test_war_fire.py [events.json ...]"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_battles as tb, war_battle_fire as bf
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc or not any('min' in a for a in sc.get('acts', [])): return None
    bad, n = [], 0
    for c in d['events']:
        if not tb.BATTLE.search(c['title'] + ' ' + c['quote']) or c.get('fight_ok'): continue
        a = bf.card_window(c, sc['acts'])
        if not a: continue
        n += 1; w1 = a['s'] + tb.WIN
        where = bf.where_of(c, d, sc['items'], a['s'], w1)
        if where is None: bad.append((c['id'], 'no place')); continue
        why = []
        if not bf.has_fire(sc['items'], a['s'], w1, where, 0): why.append('no fire of both sides + impacts')
        pr = bf.nearest_pair(bf.sides_pts(sc['items'], a['s'], w1), where)
        if not pr or pr[0] > (bf.CONTACT_AIR if c.get('unit') == 'mig' else bf.CONTACT): why.append('forces not within contact range')
        if why: bad.append((c['id'], '; '.join(why)))
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} battle cards show the fight (fire of both sides, impacts, contact)', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
