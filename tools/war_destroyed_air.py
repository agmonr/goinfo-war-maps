#!/usr/bin/env python3
"""War maps (the owner 10-22): destroyed aircraft. Adds to the committed scenes (war/data/1967-06-0X-events.json) the items the engine draws for a record that says aircraft were destroyed:
  wreck     {at, t, tg?, side, n, label}  parked planes at the named place from tg (the record says they were on the ground) until the hit t, then a wreck marker to the end of the day;
  destroyed {t, side, n, label}           the HUD counter 'aircraft destroyed so far' (the record's own number).
Positions are the record's own named place; a region is drawn at the scene's existing schematic point and the label says so; no place -> no wreck, counter only (never invented). Idempotent: its own items are
removed and re-added. Records handled (all days 5-10 June; the sentences are quoted in the labels' sources):
  5-june 07:45  197 Egyptian aircraft destroyed in the first wave, 8 of them in air combat; named airfields Arish, Bir Gifgafa, Bir Tamada, Jebel Libni, Fayid, Kabrit (the split between airfields is not given)
  5-june        Syrian air force loses 53 of 112 aircraft (Syria only: schematic point of the scene's Syrian airfields)
  6-june ~06:00 Iraqi Tupolev shot down, crashes inside Camp Amos (the scene's crash point, Afula area, as in the casualty record); the entry says one Tu-16 'or two': one drawn
  8-june        Lebanese Hunter shot down by an Israeli Mirage (no place in the record: the end of the scene's own schematic flight path)
    python3 tools/war_destroyed_air.py"""
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'war', 'data')

def load(day):
    p = os.path.join(ROOT, '1967-06-%s-events.json' % day); return p, json.load(open(p))

def clean(S): S['items'] = [x for x in S['items'] if x['type'] not in ('wreck', 'destroyed')]

def boom_t(S, at):
    return min((b['t'] for b in S['items'] if b['type'] == 'boom' and abs(b['at'][0] - at[0]) < 1e-6 and abs(b['at'][1] - at[1]) < 1e-6), default=None)

def save(p, D): json.dump(D, open(p, 'w'), ensure_ascii=False, indent=1)

# ---- 5 June
p, D = load('05'); S = D['scene']; clean(S); P = {k: [v['lat'], v['lon']] for k, v in D['places'].items()}
last = 0
for k, nm in (('arish', 'אל-עריש'), ('gif', 'ביר גפגפה'), ('tam', 'ביר תמדה'), ('jebel', "ג'בל ליבני"), ('fayid', 'פאיד'), ('kabrit', 'כברית')):
    t = boom_t(S, P[k]); last = max(last, t)
    S['items'].append({'type': 'wreck', 'at': P[k], 't': t, 'tg': 0, 'side': 'ar', 'n': 3, 'area': 'sinai',
                       'label': 'שדה התעופה ' + nm + ': מטוסים מצריים שהושמדו (חלק מ-197 בכל השדות; החלוקה בין השדות לא ידועה)'})
S['items'].append({'type': 'destroyed', 't': last, 'side': 'ar', 'n': 197, 'area': 'sinai', 'label': '197 מטוסים מצריים הושמדו בגל הראשון, 8 מהם בקרבות אוויר'})
SYA = [33.35, 36.35]; ts = boom_t(S, SYA)
S['items'].append({'type': 'wreck', 'at': SYA, 't': ts, 'side': 'ar', 'n': 53, 'area': 'golan', 'label': '53 מטוסים סוריים (מתוך 112) הושמדו (סכמטי: הערך מציין את סוריה בלבד, לא שדה מסוים)'})
S['items'].append({'type': 'destroyed', 't': ts, 'side': 'ar', 'n': 53, 'area': 'golan', 'label': 'חיל האוויר הסורי מאבד 53 מתוך 112 מטוסיו'})
save(p, D)
# ---- 6 June
p, D = load('06'); S = D['scene']; clean(S)
tu = [x for x in S['items'] if x['type'] == 'fly' and (x.get('label') or '').startswith('טופולב')][0]; end = tu['legs'][-1]['path'][-1]; tc = tu['legs'][-1]['t1']
S['items'].append({'type': 'wreck', 'at': end, 't': tc, 'side': 'ar', 'n': 1, 'area': 'center', 'label': 'טופולב עיראקי שהופל והתרסק במחנה עמוס (לפי הערך "טופולב 16 או שניים": מצוייר אחד; הנקודה סכמטית)'})
S['items'].append({'type': 'destroyed', 't': tc, 'side': 'ar', 'n': 1, 'area': 'center', 'label': 'טופולב עיראקי שהופל'})
save(p, D)
# ---- 8 June
p, D = load('08'); S = D['scene']; clean(S)
hu = [x for x in S['items'] if x['type'] == 'fly' and (x.get('label') or '').startswith('האנטר')][0]; end = hu['legs'][0]['path'][-1]; th = hu['legs'][0]['t1']
S['items'].append({'type': 'wreck', 'at': end, 't': th, 'side': 'ar', 'n': 1, 'area': 'golan', 'label': 'האנטר לבנוני שהופל על ידי מיראז׳ ישראלי (הערך אינו מציין מקום: הנקודה סכמטית, בסוף מסלול הטיסה המצויר)'})
S['items'].append({'type': 'destroyed', 't': th, 'side': 'ar', 'n': 1, 'area': 'golan', 'label': 'האנטר לבנוני שהופל'})
save(p, D)
print('ok')
