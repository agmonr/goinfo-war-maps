#!/usr/bin/env python3
"""LAW R51 (the owner 10-26): an aircraft is shot down only AFTER the shooting side has arrived in the area. For every fly item with a `down` block (hit time t, hit point on its own leg): at time t an item of the OTHER side that can shoot must already be within
RANGE degrees of the hit point: an aircraft (fly, in the air at t) or a SAM / anti-aircraft site (sam item, standing or firing) - ground units do not count - and it must have ARRIVED earlier (its own presence begins at least LEAD scene-seconds before t). Offenders are listed.
    python3 tools/test_war_shootdown_order.py [events.json ...]   rc 1 when a STRICT file (named, default Yom Kippur) has offenders; the others are reported."""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_landcheck as lc, test_war_event_shown as es, test_war_heavy_losses as hl
RANGE, LEAD = 0.5, 1.0
def side_of(it):
    s = it.get('side') or ''
    if s in ('iaf', 'il'): return 'il'
    if s in ('syr', 'ar', 'egy'): return 'ar'
    return hl.side(it)
def pos_at(it, T):
    if it['type'] == 'fly':
        for lg in it['legs']:
            if lg['t0'] <= T <= lg['t1']:
                if not lg.get('path'): return list(lg['orbit'][:2]) if lg.get('orbit') else None
                return lc.along(lg['path'], (T - lg['t0']) / max(1e-6, lg['t1'] - lg['t0']))
        return None
    if it['type'] == 'walk':
        for lg in it['legs']:
            if not lg.get('path'): continue
            if lg['t0'] <= T <= lg['t1']: return lc.along(lg['path'], lc.ease((T - lg['t0']) / max(1e-6, lg['t1'] - lg['t0'])))
        last = it['legs'][-1]
        return list(last['path'][-1]) if T > last['t1'] and last.get('path') else None
    if it['type'] == 'arrow':
        return lc.along(it['path'], lc.ease((T - it['t0']) / max(1e-6, it['t1'] - it['t0']))) if T >= it['t0'] else None
    if it['type'] == 'sam': return list(it.get('c') or it.get('at') or it.get('from') or [])[:2] or None
    return None
WINDOW = 40.0      # the shooter must have been in range within this many scene-seconds before the hit
def shooter_near(items, other, hp, t, skip=None):
    """an aircraft of `other` that was within RANGE of hp at some time in [t-WINDOW, t-LEAD], or a SAM site of `other` standing there then"""
    for o in items:
        if o is skip or o['type'] not in ('fly', 'sam') or side_of(o) != other: continue
        a, b = es.span(o)
        if o['type'] == 'sam':
            if a <= t - LEAD and b >= t - WINDOW and (lambda p: p and math.hypot(p[0] - hp[0], p[1] - hp[1]) <= RANGE)(pos_at(o, t)): return True
            continue
        for lg in o.get('legs', []):
            P = lg.get('path') or ([lg['orbit'][:2]] if lg.get('orbit') else [])
            if not P: continue
            for k in range(0, 41):
                T = t - WINDOW + (WINDOW - LEAD) * k / 40
                if T < lg['t0'] or T > lg['t1']: continue
                q = lc.along(P, (T - lg['t0']) / max(1e-6, lg['t1'] - lg['t0'])) if len(P) > 1 else P[0]
                if math.hypot(q[0] - hp[0], q[1] - hp[1]) <= RANGE: return True
    return False
def fire_before(items, hp, t):
    """a burst / shell of fire within 0.4 deg of the hit point in the 3.5 s before the hit"""
    return any(x['type'] == 'boom' and t - 3.5 <= x['t'] <= t + 0.1 and math.hypot(x['at'][0] - hp[0], x['at'][1] - hp[1]) <= 0.4 for x in items if x['type'] == 'boom' and isinstance(x.get('at'), list)) or \
           any(x['type'] == 'shell' and x['t0'] <= t <= x['t1'] + 1 and math.hypot(x['to'][0] - hp[0], x['to'][1] - hp[1]) <= 0.4 for x in items if x['type'] == 'shell')
def check(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene')
    if not sc: return None
    items, bad, n = sc['items'], [], 0
    for it in items:
        if it['type'] == 'fly' and it.get('down'):
            n += 1; t = it['down']['t']; me = side_of(it); hp = pos_at(it, t) or it['down'].get('at')
            if not hp or not shooter_near(items, 'il' if me == 'ar' else 'ar', hp, t, skip=it): bad.append((it.get('label') or '?', round(t, 1)))
            elif not fire_before(items, hp, t): bad.append(((it.get('label') or '?') + ' [no fire before the fall]', round(t, 1)))
        elif it['type'] == 'wreck' and it.get('at') and it.get('t') is not None and not it.get('nogate'):
            n += 1; t = it['t']
            if not shooter_near(items, 'il' if side_of(it) == 'ar' else 'ar', it['at'], t): bad.append(((it.get('label') or 'wreck')[:40], round(t, 1)))
    return n, bad
if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
    fail = 0
    for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
        r = check(f)
        if r:
            print(f'{f}: {r[0] - len(r[1])}/{r[0]} shot-down aircraft fall after the shooting side arrived', ('FAIL ' + '; '.join(f'{a}@{b}' for a, b in r[1])) if r[1] else 'ok')
            if f in explicit: fail += len(r[1])
    sys.exit(1 if fail else 0)
