#!/usr/bin/env python3
"""War maps (the owner 10-22): every record that names aircraft of a side must have that side's aircraft animated while the record is on screen. Static check over war/data/1967-*-events.json scenes:
a log record (scene.log entry) is an AIRCRAFT RECORD when its text has an aircraft count (digits or a number word before מטוס/מיג/גיחות/הנטר/מיראז'...) or names an air force/aircraft of a side
("מטוסי/חיל האוויר/הנטרים ה<ירדני|סורי|מצרי|עיראקי>"). It PASSES when a 'fly' item of that side (side taken from the sentence; ישראל = iaf, the others = ar; no side word = any) has a leg window overlapping
[t-1, t+30] of the record. EXCEPT lists records that are not flying aircraft (destroyed on the ground, losses stated afterwards), each with its reason: they are listed, never silently skipped.
A second rule (destroyed aircraft, the owner 10-22): a record SENTENCE that says aircraft were destroyed / shot down / lost / crashed needs a 'destroyed' counter item of the side with at least the record's number
(number from "<N> מטוסים", "מאבד <N> מתוך"; else 1) within 80 s of the record, and the same number of aircraft as 'wreck' markers' counter (a wreck marker with a position, unless the record names no place: then only the counter, listed
in NOPOS). EXCEPT_D lists sentences that only REFER to an earlier destroyed count.
    python3 tools/test_war_aircraft_records.py [--list]     (--list prints every aircraft record and what is drawn: the gap report)"""
import glob, json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NW = {'שני': 2, 'שתי': 2, 'שלושה': 3, 'שלוש': 3, 'ארבעה': 4, 'ארבע': 4, 'חמישה': 5, 'חמש': 5, 'שישה': 6, 'שבעה': 7, 'שמונה': 8, 'תשעה': 9, 'עשרה': 10, 'עשרות': 20}
AC = r"(?:מטוסי|מטוסים|מטוס|מיגים|מיג|גיחות|גיחה|הנטרים|הנטר|ווטורים|וטורים|מיראז'ים|מיראז|סוחוי|פוגה|מפציצים|מסוקים|מסוק)"
CNT = re.compile(r"(?:(?:כ-|כ־|~|למעלה מ-|מעל )?(\d+)|(" + '|'.join(NW) + r"))\s+(?:\S+\s+)?" + AC)
NAME = re.compile(r"(?:מטוסי|חיל האוויר|הנטרים|מיגים)\s+ה?(ירדני|סורי|מצרי|עיראקי|ישראלי)")
SIDEW = [('ar', 'ירדני'), ('ar', 'סורי'), ('ar', 'מצרי'), ('ar', 'עיראקי'), ('ar', 'ערבי'), ('iaf', 'ישראלי'), ('iaf', 'חיל האוויר הישראלי'), ('iaf', 'מוקד')]
EXCEPT = {('1967-06-05', 0.5): 'מטוסים מצריים שהושמדו על הקרקע (197): מצוירים כמטוסים על הקרקע ואז כשברים (wreck), לא כמטוסים בטיסה; הגל הישראלי מצויר',
          ('1967-06-05', 111): 'הפסדים שהצד הסורי ספג ("53 מתוך 112"): מצויר כשבר סכמטי; הגל עצמו מצויר',
          ('1967-06-05', 2): 'הגל הראשון פוגע בחיל האוויר המצרי (על הקרקע) ובלי מקום: הגל עצמו מצויר בשורות הקודמות; לא מטוסים מצריים בטיסה',
          ('1967-06-05', 97): 'ההקשר הוא משא ומתן להפסקת אש בירושלים; חיל האוויר המצרי מוזכר כמי שהושמד, בלי תנועה של מטוסים',
          ('1967-06-06', 100): 'סיכום "ארבעת הימים הראשונים": הפצצות של חיל האוויר הישראלי ברמת הגולן, בלי שעה, בלי מספר ובלי נקודת מקום: אין מה לצייר בלי להמציא',
          ('1967-06-08', 40): 'סיכום יום ("תקיפות רבות של חיל האוויר הישראלי"): בלי שעה, בלי מספר ובלי נקודת מקום: אין מה לצייר בלי להמציא',
          ('1967-06-08', 86): 'שני מיראז׳ים שתקפו את "ליברטי": מצוירים בקטע הקרוב (נבדק ידנית)'}

DEST = re.compile(r"(הושמדו|מושמדים|הושמד|הופלו|הופל|מאבד|איבד|התרסק)")
AIRN = re.compile(r"(מטוסים|מטוסי\s+\S+|מטוס|מיגים|מיג|הנטרים|האנטר|הנטר|טופולב|מיראז'?)")
EXCEPT_D = {('1967-06-05', 97): 'אזכור של הושמדו המטוסים המצריים בגל הראשון (הספירה, 197, ברשומה של 07:45 והיא נספרת שם)'}

def destroyed_n(sent):
    m = re.search(r"מאבד\s+(\d+)", sent) or re.search(r"(?:הושמדו|מושמדים|הופלו)\s+(\d+)", sent)
    return int(m.group(1)) if m else 1

def main():
    show = '--list' in sys.argv; bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'war', 'data', '1967-0[46]-*-events.json'))):
        day = os.path.basename(f)[:10]; D = json.load(open(f)); S = D.get('scene')
        if not S: print(day, 'no scene (static page): not checked'); continue
        fl = [x for x in S['items'] if x['type'] == 'fly']; win = lambda x: (min(l['t0'] for l in x['legs']), max(l['t1'] for l in x['legs']))
        dst = [x for x in S['items'] if x['type'] == 'destroyed']; wr = [x for x in S['items'] if x['type'] == 'wreck']
        for e in S['log']:
            for sent in re.split(r'(?<=[.!?])\s+', e['q']):
                if not (DEST.search(sent) and AIRN.search(sent)) or re.search(r'חטיבה|כוח השריון', sent): continue
                n = destroyed_n(sent); fw = re.search(r'(ישראלי|ירדני|סורי|מצרי|עיראקי|לבנוני)', sent); sd = 'iaf' if fw and fw.group(1) == 'ישראלי' and not re.search(r'על ידי[^.]*ישראלי', sent) else 'ar'
                got = sum(x['n'] for x in dst if x['side'] == sd and abs(x['t'] - e['t']) <= 80)
                exc = EXCEPT_D.get((day, e['t']))
                if show: print('%s t=%-5s DESTROYED need n=%d side=%s -> counter %d, wrecks %d%s | %s' % (day, e['t'], n, sd, got, len(wr), (' [EXCEPT: %s]' % exc) if exc else '', sent[:70]))
                if got < n and not exc: bad += 1; print('FAIL', day, e['t'], 'destroyed-aircraft record without a destroyed counter item of at least', n, '|', sent[:90])
        for e in S['log']:
            q = e['q']; sides = {s for s, w in SIDEW if w in q}
            cnt = [m.group(0) for m in CNT.finditer(q)]; nm = [m.group(0) for m in NAME.finditer(q)]
            if not (cnt or nm): continue
            need = {'iaf' if 'ישראלי' in n else 'ar' for n in nm} or sides or {'iaf', 'ar'}
            drawn = [x for x in fl if x['side'] in need and win(x)[0] <= e['t'] + 30 and win(x)[1] >= e['t'] - 1]
            exc = EXCEPT.get((day, e['t'])); ok = bool(drawn) or exc
            if show or not ok: print('%s t=%-5s %-12s need=%s counts=%s names=%s -> drawn %d%s' % (day, e['t'], e['clock'], sorted(need), cnt[:2], nm[:2], len(drawn), (' [EXCEPT: %s]' % exc) if exc else ''))
            if not ok: bad += 1; print('FAIL', day, e['t'], e['clock'], 'aircraft record with no animation of that side')
    print('FAILED %d' % bad if bad else 'ok'); sys.exit(1 if bad else 0)

if __name__ == '__main__': main()
