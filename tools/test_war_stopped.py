#!/usr/bin/env python3
"""LAW R49/R50 (the owner 10-26): "נבלם" means the force was fought until it could not move = DESTROYED; "בולמת/בלמה/עצרה התקדמות" = the defender holds the attacker, BOTH sides take heavy losses; "מאמץ עליון / בכל הכוח / במחיר כבד"
= very heavy casualty level (loss markers lvl 2, heavier sound). Keywords: tools/war_keywords.py (one list). For every card whose title/quote hits a family (and is not exempt with `stopped_ok`: reason):
  - the card is in ev["stopped"] (tools/war_stopped.py spec), with enough loss markers (>= 3 wrecks of the stopped side near the place, within the card's window); hold: also >= 1 wreck of the other side;
  - the stopped side has no moving unit within R of the place after the stop (its arrows/fill walks end: item "u" <= stop + 8 scene-seconds);
  - supreme: at least one loss marker with lvl 2 near the place, and a sound cue for it (war_sfx auto).
    python3 tools/test_war_stopped.py [events.json ...]   rc 1 when a STRICT file (named, default Yom Kippur) has offenders; the others are reported."""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_keywords as kw, war_sfx, war_pushout as po, war_stopped as ws
R = 0.30
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc or not any('min' in a for a in sc.get('acts', [])): return None
    items, bad, n = sc['items'], [], 0
    for c in d['events']:
        txt = c['title'] + ' ' + c['quote']; h = kw.hits(txt)
        if not any(h.values()) or c.get('stopped_ok'): continue
        n += 1; sp = d.get('stopped', {}).get(c['id']); why = []
        if not sp: bad.append((c['id'], 'no stopped/hold spec (tools/war_stopped.py)')); continue
        a = po.act_of(sc, c); at = sp['at']
        near = lambda p: math.hypot(p[0] - at[0], p[1] - at[1]) <= R + 0.2
        loss = [it for it in items if it['type'] == 'loss' and near(it['at']) and a and a['s'] - 2 <= it['t'] <= a['s'] + 60]
        mine = [it for it in loss if it['side'] == ('iaf' if sp['side'] == 'il' else 'ar')]
        other = [it for it in loss if it not in mine]
        if len(mine) < (1 if sp['fam'] == 'supreme' else 3): why.append(f'only {len(mine)} wrecks of the stopped side')
        if sp['fam'] == 'hold' and not other: why.append('no wreck of the other side (both sides must lose)')
        if (h['supreme'] or sp.get('lvl') == 2) and not any(it.get('lvl') == 2 for it in loss): why.append('supreme effort without very-heavy (lvl 2) markers')
        if h['supreme'] and not any(it.get('lvl') == 2 for it in loss) is False:
            cues = war_sfx.auto([it for it in loss if it.get('lvl') == 2])
            if len(cues) < 3: why.append('no heavier sound for lvl 2')
        if a and sp['fam'] != 'supreme':
            T = sp['T'] + 4
            moving = [it for it in items if it['type'] in ('arrow', 'walk') and po.hl.side(it) == sp['side'] and po.es.span(it)[0] <= T and (it.get('u') is None or it['u'] > T) and po.es.span(it)[1] < 5000
                      and (ws.pos_at(it, min(T, po.es.span(it)[1])) is not None and math.hypot(ws.pos_at(it, min(T, po.es.span(it)[1]))[0] - at[0], ws.pos_at(it, min(T, po.es.span(it)[1]))[1] - at[1]) <= R) and not (it.get('label') or '').startswith('נסיגה')]
            if moving: why.append('stopped force still on the map: ' + (moving[0].get('label') or '')[:30])
        if why: bad.append((c['id'], '; '.join(why)))
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} stopped/hold/supreme cards show the destruction', ('FAIL ' + ', '.join(f'{a}({b})' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
