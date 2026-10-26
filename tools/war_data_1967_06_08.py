#!/usr/bin/env python3
"""Authors the FOURTH day of the Six-Day War (8 June 1967) for /war/: writes war/data/1967-06-08.json (page text + timeline), war/data/1967-06-08-events.json
(places, events, animation scene) and adds the day-3 casualty events ("jun8") to war/data/1967-casualties.json.

Same rules as the earlier days: every event carries a short quote from a pinned he.wikipedia revision (elisions marked [...], names of anyone killed left out), times are
the article's own wording, everything not given a coordinate is drawn SCHEMATICALLY and labelled so. Run: python3 tools/war_data_1967_06_08.py
"""
import copy
import json
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "war" / "data"
D1 = json.loads((DATA / "1967-06-05-events.json").read_text(encoding="utf-8"))
D3 = json.loads((DATA / "1967-06-07-events.json").read_text(encoding="utf-8"))
CAS = json.loads((DATA / "1967-casualties.json").read_text(encoding="utf-8"))

def pl(name, lat, lon, basis_kind="נקודת המקום"):
    return {"name": name, "lat": lat, "lon": lon, "precision": "exact", "basis": f'קואורדינטות הערך "{name}" בוויקיפדיה העברית ({basis_kind})'}
PLACES = copy.deepcopy(D3["places"])
PLACES.update({
    "hebron": pl("חברון", 31.53333333, 35.095, "נקודת העיר"), "adam": pl("גשר אדם (דאמיה)", 32.102575, 35.53540556), "romani": pl("רומני (סיני)", 31.01027778, 32.66527778),
    "ashdod": pl("אשדוד", 31.79550745, 34.64966134, "נקודת העיר"), "suez": pl("סואץ", 29.96666667, 32.55, "נקודת העיר"),
    "liberty": {"name": "מיקום ליברטי (קירוב)", "lat": 31.32, "lon": 33.80, "precision": "approximate",
                "basis": "הערך: הספינה במרחק 21 ק\"מ מהחוף באל-עריש; נקודה שחישבנו צפונה מנקודת העיר אל-עריש"}})
P = {k: [v["lat"], v["lon"]] for k, v in PLACES.items()}
AREAS = {"lahfan": D1["areas"]["lahfan"]}
SRC = copy.deepcopy(D1["source"])  # the page credits every revision it quotes: the day-1 list plus the articles this day also quotes
SRC["articles"]['תקרית ליברטי'] = {"revid": 43991651}
EVENTS = []
def ev(i, area, clock, a, b, unit, title, quote, geom=None, nopos=None, note="", prec="exact", at=0):
    EVENTS.append({"id": i, "t": clock, "time_label": clock, "start_min": a, "end_min": b, "time_precision": prec, "unit": unit, "title": title, "quote": quote,
                   "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area, "_at": at})
mk = lambda place, kind, note="": {"type": "marker", "place": place, "kind": kind, "note": note}
tr = lambda a, b, label: {"type": "track", "from": a, "to": b, "label": label}
# ---------------- sinai ----------------
ev("s0", "sinai", "בלילה שבין 7 ל-8", 0, 360, "tank", "משחתת מצרית מפגיזה כוח שריון ישראלי באזור רומני",
   'בלילה שבין ה-7 ל-8 ביוני הופגז כוח שריון בפיקוד [...] שנע באזור רומני על ידי משחתת מצרית.', [mk("romani", "shell")], prec="approximate", at=1)
ev("s1", "sinai", "03:00", 180, 180, "tank", "ביר גפגפה – אסמעיליה: שריון מצרי תוקף כוח של אוגדה 84",
   'בכביש ביר גפגפה-אסמעיליה חנה כוח של אוגדה 84. ב-3:00 ב-8 ביוני הותקף הכוח בידי שריון מצרי. הכוח הישראלי, שכלל טנקים קלים, מצא את עצמו בנחיתות מול טנקי T-55 המצריים, אך הצליח לשחוק אותם עד להגעת פלוגת טנקי שרמן מגדוד 268, שסיימו את הקרב בסיוע חיל האוויר. ביום 8 ביוני, לאחר בלימת המתקפה המשיכו כוחות אוגדה 84 מערבה, כשהם מטהרים את הציר ומשמידים כ-70 טנקים מצריים.',
   [mk("gif", "fight", "ביר גפגפה")], ["כביש ביר גפגפה–אסמעיליה: מסומנת נקודת ביר גפגפה"], at=10)
ev("s2", "sinai", "בשעות הצהריים", 720, 840, "tank", "ליברטי: נדרשת תגובה למשחתת מצרית מפגיזה; שלוש טרפדות יוצאות מאשדוד",
   'לפני הצהריים שינתה "ליברטי" כיוון דרומה, לעבר חצי האי סיני, לאחר ששטה בכיוון מזרח. הספינה הפליגה במהירות של 5 קשר מחוץ לגבול המים הטריטוריאליים שקבעו המצרים בסיני, מרחק של 21 קילומטרים מהחוף באל-עריש. [...] בשעות הצהריים הגיעה למפקדת חיל הים דרישה לטפל במשחתת מצרית המפגיזה את כוחות צה"ל באל-עריש. [...] ושלחו מנמל אשדוד שלוש טרפדות ליירוט האונייה.',
   [mk("liberty", "fight", "ליברטי: מיקום משוער"), mk("ashdod", "fight", "יציאת הטרפדות")], prec="approximate", at=72)
ev("s3", "sinai", "14:00", 840, 840, "mig", "מיראז'ים תוקפים את ליברטי בתותחים וברקטות; אחר כך מפציצים בנפל\"ם",
   'בשעה שתיים אחר הצהריים תקפו את "ליברטי" שני מיראז\'ים בירי תותחים וברקטות. לאחר מכן הפציצו אותה מטוסים אחרים בפצצות נפל"ם.',
   [mk("liberty", "bomb", "ליברטי: מיקום משוער")], at=86)
ev("s4", "sinai", "כעשרים דקות אחרי", 860, 900, "tank", "טרפדות תוקפות את ליברטי; 34 הרוגים ו-171 פצועים",
   'הטרפדות דיווחו למפקדת חיל הים ”הוא יורה עלי” וקיבלו אישור לתקיפה. הטרפדות נכנסו לתקיפה וירו חמישה טילי טורפדו. "ליברטי" נקטה בהתחמקות ורק אחד מטילי הטורפדו פגע במרכז "ליברטי" בצידה הימני, ופער בה חור גדול. [...] מתוך 294 ימאים אמריקאיים בצוות "ליברטי", נהרגו 34 ונפצעו 171.',
   [mk("liberty", "bomb", "ליברטי: מיקום משוער")], prec="approximate", note="הערך: התקיפה האווירית ב-14:00, והטרפדות כעשרים דקות לאחר מכן (לפי קפטן הספינה)", at=100)
ev("s5", "sinai", "8 ביוני", 0, 1440, "tank", "הכוחות שנחתו בשארם א-שייח' מגיעים לא-טור",
   'הכוחות שנחתו בשארם א-שייח\' הגיעו לא-טור ב-8 ביוני, וב-9 נפגשו עם כוח שבא מראס סודר באזור אבו רודס.', [mk("sharm", "fight"), mk("tur", "fight")], prec="approximate", at=116)
ev("s6", "sinai", "21:30", 1290, 1290, "tank", "מצרים מסכימה להפסקת אש; הכוחות הישראליים מתייצבים על גדת התעלה",
   'ב-21:30 ב-8 ביוני הודיעה מצרים כי היא מסכימה להפסקת אש. הכוחות הישראליים התייצבו על גדת התעלה עד ל-1:00 ב-9 ביוני.', [mk("suez", "fight", "העיר סואץ על גדת התעלה")], prec="approximate", note="הכוחות התייצבו על הגדה עד 01:00 ב-9 ביוני", at=150)
# ---------------- center ----------------
ev("c0", "center", "עם שחר ו-10:30", 330, 630, "tank", "חטיבה 16 כובשת את חברון ומתחברת עם כוחות גוש לכיש; הושלם כיבוש הגדה",
   'עם שחר 8 ביוני המשיכו כוחות החטיבה בהתקדמותם, כבשו את חברון, ובשעה 10:30 חברו עם כוחות גוש לכיש דרומית לדאהרייה, ובכך השלימו את כיבוש הגדה המערבית.',
   [mk("hebron", "fight")], ["גוש לכיש ודאהרייה: אין קואורדינטות בערך"], prec="approximate", at=26)
ev("c1", "center", "13:00", 780, 780, "tank", "פיצוץ גשרי הירדן בגזרת יריחו ובמרחב דאמיה",
   'מאוחר יותר באותו היום, בשעה 13:00, הושלם פיצוצם של גשרי הירדן, על ידי חטיבה 10 בגזרת יריחו ועל ידי חטיבה 45 במרחב דאמיה.',
   [mk("jericho", "bomb", "גזרת יריחו"), mk("adam", "bomb", "מרחב דאמיה")], at=60)
# ---------------- golan ----------------
ev("g0", "golan", "8 ביוני", 0, 1440, "tank", "הקרבות בסיני ובגדה שככו; הפגזות הדדיות בצפון ותקיפות חיל האוויר נמשכות",
   'ביום זה שככו הקרבות בסיני ובגדה המערבית ובמועצת הביטחון של האו"ם צברו תאוצה הדיונים על הפסקת האש. גם ביום זה המשיכו ההפגזות של יישובי הצפון שנענו בהפגזות נגד ובתקיפות רבות של חיל האוויר הישראלי.',
   [], ["הערך לא נותן מקום ושעה"], prec="approximate", at=40)
ev("g1", "golan", "בבוקר ובצהריים", 480, 780, "tank", "חטיבות 37 ו-45 נעות מהגדה לצפון, לצומת גולני",
   'שתי חטיבות נוספות הועברו לגזרה הצפונית: חטיבת השריון 37 החלה את תנועתה בבוקר 8 ביוני מאזור שכם צפונה, והחטיבה הממוכנת 45 החלה בתנועה צפונה בשעות הצהריים. שתי החטיבות קיבלו הוראה לנוע לצומת גולני, דבר שגרם להסתבכות השיירות זו בזו ולעיכובים.',
   [mk("nablus", "fight", "נקודת היציאה של חטיבה 37")], ["צומת גולני: אין קואורדינטות בערך"], prec="approximate", at=46)
ev("g2", "golan", "10:00", 600, 600, "tank", "דיין אינו מאשר את תוכנית ההתקפה של פיקוד הצפון",
   'ב-8 ביוני בשעה 10:00 הוצגה לדיין תוכנית ההתקפה של פיקוד צפון אך הוא לא אישר אותה. [...] ורבין הסביר כי אינו יכול לאשר את התוכנית כיוון ששר הביטחון מתנגד לה.',
   [], ["החלטה: אין מקום על המפה"], at=54)
ev("g3", "golan", "8 ביוני", 0, 1440, "mig", "לבנון מצטרפת רשמית למלחמה; האנטר לבנוני מופל",
   'לבנון הצטרפה באופן רשמי למלחמה ב-8 ביוני, אך לא הוציאה לפועל פעולות מלחמתיות, פרט לגיחה של מטוס האנטר שהתקרב לגבול הישראלי והופל על ידי מטוס מיראז\' ישראלי.',
   [], ["הערך לא נותן מקום ושעה"], prec="approximate", at=130)
ev("g4", "golan", "19:10", 1150, 1150, "tank", "ועדת השרים דנה בהתקפה בחזית הסורית; משלחת יישובי אצבע הגליל מופיעה בפניה",
   'באותו הבוקר קיבלו יישובי אצבע הגליל את ההודעה כי ההתקפה שתוכננה בוטלה. משלחת שכללה שלושה נציגים מהיישובים הגיעה לתל אביב כדי לפגוש את שרי הממשלה ולשכנעם בנחיצות המתקפה. בשעה 19:10 התכנסה בתל אביב ועדת השרים לענייני ביטחון לדון בהתקפה בחזית הסורית. [...] אולם עמדתו של דיין לא השתנתה.',
   [], ["הדיון בתל אביב: מחוץ למסגרת המפה"], at=140)
ev("g5", "golan", "בלילה שבין 8 ל-9", 1440, 1440, "tank", "ממשלת סוריה מחליטה לקבל את הפסקת האש",
   'בינתיים, בלילה שבין 8 ו-9 ביוני החליטה ממשלת סוריה לקבל את הפסקת האש והודעה על כך שודרה על ידי רדיו דמשק ב-9 ביוני לפנות בוקר.', [], ["הודעה ברדיו דמשק: אין מקום על המפה"], prec="approximate", at=168)
EVENTS.sort(key=lambda e: e["_at"])
LOGT = {e["id"]: e.pop("_at") for e in EVENTS}
IL = [31.62, 34.93]; SYB = [33.4, 36.6]; JOB = [32.05, 35.75]
ITEMS, SFX = [], []
def add(it): ITEMS.append(it); return it
def sfx(t, k): SFX.append([round(t, 2), k])
def boom(at, t, big=0, area="center", k="cannon", dur=1.2):
    it = {"type": "boom", "at": at, "t": t, "dur": dur, "area": area}
    if big: it["big"] = 1; it["dur"] = 1.4
    add(it); sfx(t, k)
def sortie(label, target, t0, t_hit, t_back, area, base=IL, side="iaf", via=None, off=None, big=1):
    path = [base] + ([via] if via else []) + [target]
    add({"type": "fly", "side": side, "label": label, "area": area, "off": off, "legs": [{"t0": t0, "t1": t_hit, "path": path}, {"t0": t_hit + .3, "t1": t_back, "path": list(reversed(path))}]})
    sfx(t0 + .3, "jet"); boom(target, t_hit, big, area, "boom", 1.4)
def arrow(path, t0, t1, label, area, color="#1d5ea8", hold=10):
    add({"type": "arrow", "path": path, "t0": t0, "t1": t1, "label": label, "color": color, "hold": hold, "area": area})
def walk(label, path, t0, t1, area, cls="iaf"):
    add({"type": "walk", "label": label, "cls": cls, "sym": "▣", "legs": [{"t0": t0, "t1": t1, "path": path}], "area": area})
def mark(at, t0, t1, label, area): add({"type": "mark", "at": at, "t0": t0, "t1": t1, "label": label, "area": area})
def shell(frm, to, t0, t1, area, period=1.4, lift=.04): add({"type": "shell", "from": frm, "to": to, "t0": t0, "t1": t1, "period": period, "lift": lift, "area": area})
LIB = P["liberty"]
# act 0 (0-10) night: Egyptian destroyer shells an armoured force near Romani
shell([31.25, 32.55], P["romani"], 1, 8, "sinai", 1.2, .05)
walk("כוח שריון ישראלי (סכמטי)", [[31.0, 32.95], P["romani"]], 1.5, 6, "sinai")
for t_ in (4, 6, 8): boom([P["romani"][0] + .004 * (t_ % 3), P["romani"][1] + .01], t_, area="sinai", k="thud")
# act 1 (10-26) 03:00 Bir Gifgafa-Ismailia road
walk("טנקי T-55 מצריים (סכמטי)", [[30.40, 32.72], P["gif"]], 10.5, 15, "sinai", "syr")
for i in range(5): boom([P["gif"][0] + .012 * ((i * 5) % 3 - 1), P["gif"][1] - .015 * (i % 3)], 14 + .9 * i, area="sinai", k="thud" if i % 2 else "cannon")
arrow([[30.58, 33.62], P["gif"]], 16.5, 19.5, "פלוגת שרמן מגדוד 268 (סכמטי)", "sinai", hold=6)
sortie("חיל האוויר מסייע (סכמטי)", [30.42, 33.0], 16, 19, 23, "sinai", via=[30.9, 33.9], big=0)
arrow([P["gif"], [30.38, 32.62]], 21, 26, "אוגדה 84: ניקוי הציר מערבה (סכמטי)", "sinai", hold=8)
# act 2 (26-40) Hebron
arrow([P["gush"], P["hebron"]], 26.5, 31, "חטיבה 16 (סכמטי)", "center", hold=8)
mark(P["hebron"], 31.5, 36, "עם שחר: חברון נכבשה", "center")
arrow([P["hebron"], [31.38, 34.96]], 35, 39, "חיבור עם כוחות גוש לכיש, 10:30 (סכמטי)", "center", hold=4)
# act 3 (40-52) Golan: brigades north
mark([33.0, 35.6], 40.5, 52, "הפגזות הדדיות ותקיפות חיל האוויר (הערך לא נותן מקום)", "golan")
walk("חטיבה 37 מאזור שכם צפונה (סכמטי)", [P["nablus"], [32.50, 35.40], [32.78, 35.45]], 46, 51.8, "golan")
walk("חטיבה 45 צפונה (סכמטי)", [P["hawara"], [32.50, 35.38], [32.76, 35.44]], 47, 51.8, "golan")
# act 4 (52-60)
mark([32.9, 35.55], 54, 60, "10:00: דיין אינו מאשר את התוכנית", "golan")
# act 5 (60-72) bridges
for t_, at_ in ((62, [31.874, 35.54]), (64, P["adam"])): boom(at_, t_, big=1, area="center", k="boom", dur=1.4)
mark([31.874, 35.54], 64.5, 72, "13:00: גשרי הירדן מפוצצים (גזרת יריחו)", "center")
mark(P["adam"], 66, 72, "13:00: גשר דאמיה מפוצץ", "center")
# act 6-8 Liberty (72-116)
mark(LIB, 73, 116, "ליברטי (מיקום משוער)", "sinai")
walk("שלוש טרפדות מאשדוד (סכמטי)", [P["ashdod"], [31.55, 34.2], LIB], 74.5, 100, "sinai")
sortie("מיראז'ים תוקפים את ליברטי (סכמטי)", LIB, 86, 91, 97, "sinai", via=[31.45, 34.3])
boom(LIB, 93, big=1, area="sinai", k="boom", dur=1.4)
for t_ in (101, 103.5): boom([LIB[0] + .004 * (t_ % 2), LIB[1] + .01], t_, big=1, area="sinai", k="boom", dur=1.4)
mark(LIB, 108, 116, "טורפדו אחד פוגע; הספינה נשארת צפה", "sinai")
# act 10 (116-128) A-Tur
walk("כוחות שחולצו מהמסוקים: א-טור (סכמטי)", [P["sharm"], [28.1, 34.2], P["tur"]], 116.5, 124, "sinai")
mark(P["tur"], 124, 128, "8 ביוני: הגיעו לא-טור", "sinai")
# act 11 (128-138) Lebanon
add({"type": "fly", "side": "ar", "label": "האנטר לבנוני (סכמטי)", "area": "golan", "legs": [{"t0": 128.5, "t1": 132, "path": [[33.45, 35.75], [33.1, 35.5]]}]}); sfx(129, "jet")
boom([33.1, 35.5], 132.4, area="golan", k="boom", dur=1.4)
mark([33.2, 35.4], 133, 138, "לבנון: גיחה בודדת", "golan")
# act 12 (138-150)
mark([32.95, 35.5], 139, 150, "19:10: ועדת השרים (בתל אביב) דנה בהתקפה בצפון", "golan")
# act 13 (150-166) Egypt accepts the ceasefire
arrow([P["gif"], [30.62, 32.36]], 150.5, 158, "אוגדה 84: עד גדת התעלה (סכמטי)", "sinai", hold=10)
mark([30.62, 32.34], 158, 166, "21:30: מצרים מסכימה להפסקת אש", "sinai")
# act 14 (166-186) Syria
mark([33.35, 36.05], 167, 186, "לפנות בוקר 9 ביוני: רדיו דמשק מודיע על קבלת הפסקת האש", "golan")
V = {"all": [[27.7, 32.0], [33.7, 36.8]], "sinai": [[27.7, 32.0], [31.8, 34.9]], "center": [[31.2, 34.6], [32.5, 35.7]], "golan": [[32.5, 35.0], [33.6, 36.7]]}
A_ = lambda s, e, c, v: {"s": s, "e": e, "clock": c, "view": V[v], "caps": []}
ACTS = [A_(0, 10, "בלילה · רומני", "sinai"), A_(10, 26, "03:00 · ביר גפגפה", "sinai"), A_(26, 40, "עם שחר · חברון", "center"), A_(40, 52, "בוקר · הצפון", "golan"),
        A_(52, 60, "10:00 · החלטת שר הביטחון", "golan"), A_(60, 72, "13:00 · גשרי הירדן", "center"), A_(72, 86, "צהריים · ליברטי", "sinai"), A_(86, 100, "14:00 · ליברטי", "sinai"),
        A_(100, 116, "כעשרים דקות אחרי · ליברטי", "sinai"), A_(116, 128, "8 ביוני · א-טור", "sinai"), A_(128, 138, "לבנון", "golan"), A_(138, 150, "19:10 · ועדת השרים", "golan"),
        A_(150, 166, "21:30 · הפסקת האש המצרית", "sinai"), A_(166, 200, "בלילה · סוריה מקבלת", "golan")]
LOG = [{"t": LOGT[e["id"]], "clock": e["t"], "q": e["quote"], "n": ", ".join([p_["label"] for p_ in e["geometry"] if p_.get("label")] or [PLACES[g["place"]]["name"] for g in e["geometry"] if g["type"] == "marker"]), "area": e["area"]} for e in EVENTS]
TRAIL = [("חטיבה 16", "tank"), ("חטיבה 37", "tank"), ("חטיבה 45", "tank"), ("פלוגת שרמן", "tank"), ("אוגדה 84", "tank"), ("כוח שריון ישראלי", "tank"), ("טנקי T-55", "tank"), ("שלוש טרפדות", None), ("כוחות שחולצו", "foot")]
for it_ in ITEMS:
    if it_["type"] in ("walk", "arrow"):
        for key_, kind_ in TRAIL:
            if (it_.get("label") or "").startswith(key_):
                if kind_: it_["trail"] = kind_
                break
CIRC = lambda i, c, r, t0, t1, a, lab: {"id": i, "center": c, "radius_m": r, "t0": t0, "t1": t1, "area": a, "label": "קו חזית משוער: " + lab, "lab_to": 0 if t1 <= 1 else t1 + 9}
CARRY = [(g["id"], g["center"], g["radius_m"], g["area"], g["label"].replace("קו חזית משוער: ", "")) for g in D3["scene"]["control"]["grow"]]
GROW = [CIRC(i, c, r, 0, 1, a, l) for i, c, r, a, l in CARRY]
GROW += [CIRC("hebron", P["hebron"], 4500, 31, 37, "center", "חברון (עם שחר)"), CIRC("tur", P["tur"], 3500, 120, 126, "sinai", "א-טור")]
CONTROL = {"label": "קו חזית משוער, לא גבול מדויק", "base": json.loads(json.dumps(D1["scene"]["control"]["base"])), "grow": GROW}
SCENE = {"dur": 200, "view0": V["all"], "acts": ACTS, "log": LOG, "sfx": SFX, "items": ITEMS,
         "bases": [{"pos": IL, "label": "בסיס חיל האוויר"}, {"pos": SYB, "label": "בסיס סורי"}, {"pos": JOB, "label": "בסיס ירדני"}],
         "areas": [], "show_places": ["gif", "romani", "liberty", "ashdod", "arish", "suez", "sharm", "tur", "hebron", "jericho", "adam", "nablus", "hawara", "gush"],
         "control": CONTROL}
OUT = {"source": SRC, "places": PLACES, "areas": AREAS, "events": EVENTS, "time_range": [0, 1440], "area_filter": D1["area_filter"],
       "views": {"all": V["all"], "sinai": [[27.7, 32.0], [31.8, 34.9]], "center": [[31.2, 34.6], [32.5, 35.7]], "golan": [[32.8, 35.2], [33.4, 35.9]]},
       "still_views": {"all": [[29.0, 32.0], [33.4, 36.4]], "sinai": [[30.5, 33.0], [31.8, 34.5]], "center": [[31.3, 34.9], [32.3, 35.7]], "golan": [[32.4, 35.0], [33.6, 36.0]]},
       "view": [[27.7, 32.0], [33.6, 36.7]], "cards_title": D1["cards_title"], "scene": SCENE}
(DATA / "1967-06-08-events.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
named = lambda e: ", ".join(PLACES[g["place"]]["name"] for g in e["geometry"] if g["type"] == "marker") or ""
TL = [{"clock": e["t"], "text": e["quote"], "place": named(e) or "; ".join(e["no_position"]) or "ללא מקום", "place_precision": "exact" if named(e) and not any(g.get("place") == "liberty" for g in e["geometry"]) else ("approximate" if named(e) else "none"), "area": e["area"], "start": e["start_min"]} for e in EVENTS]
PAGE = {"slug": "8-june", "cas_key": "jun8", "day_he": "היום הרביעי", "year": 1967, "date": "1967-06-08", "hebrew_date": "כ\"ט באייר תשכ\"ז", "multi": True,
        "title": "8 ביוני 1967: היום הרביעי של מלחמת ששת הימים, לפי שלוש זירות",
        "h1": "8 ביוני 1967: היום הרביעי של מלחמת ששת הימים",
        "context": "היום הרביעי של מלחמת ששת הימים - 8 ביוני 1967",
        "description": "הרדיפה בסיני, תקרית ליברטי, כיבוש חברון והפסקת האש המצרית.",
        "lead": "ב-8 ביוני 1967, ביום חמישי, שככו הקרבות בסיני ובגדה המערבית: חברון נכבשה עם שחר, ובשעה 13:00 פוצצו גשרי הירדן. בסיני נחלמה מתקפה מצרית על כוח של אוגדה 84 בכביש ביר גפגפה–אסמעיליה, ובערב הודיעה מצרים על הסכמה להפסקת אש. בצהריים הותקפה בטעות ספינת הביון האמריקאית ליברטי מול החוף של אל-עריש. בצפון נמשכו ההפגזות, ושר הביטחון עדיין סירב לאשר התקפה על סוריה.",
        "summary": ["העמוד מחולק לשלוש זירות: סיני ורצועת עזה, ירושלים והגדה המערבית, רמת הגולן והצפון. לכל זירה ציר זמן ומפה משלה. אפשר לעבור ביניהן בכפתורים (או בקישור ישיר: #sinai, #center, #golan).",
                    "כל אירוע מצוטט מערך בוויקיפדיה העברית שקובעת גרסתו, עם שעה כפי שהערך כותב אותה. מה שהערך לא נותן לו מקום מצויר סכמטית ומסומן כך. מיקום ליברטי הוא קירוב שחישבנו מהמרחק שהערך נותן.",
                    "הרוגים ופצועים: ביום הזה הנתון היחיד הוא של צוות ליברטי האמריקאי, שאינו צד בלחימה, ולכן הוא מוצג בשורה נפרדת ולא תחת ישראל או צד ערב. לשאר האירועים הערכים לא נותנים מספרים."],
        "aftermath": ["סיני: בלילה לאחר מכן, ב-00:30 ב-9 ביוני, הגיע חוד אוגדה 84 לגדת התעלה; הכוחות התייצבו על הגדה עד 01:00.",
                      "רמת הגולן: בלילה שבין 8 ל-9 ביוני החליטה ממשלת סוריה לקבל את הפסקת האש; הקרב היבשתי החל בצהרי 9 ביוני.",
                      "הגדה המערבית: כל הכוחות שנותרו בה הוכפפו לפיקוד המרכז."],
        "places": [{"name": "נקודות מסומנות: יישובים וערים", "precision": "exact", "basis": "קואורדינטות הערכים בוויקיפדיה העברית; נקודת היישוב או המקום, לא מיקום האירוע במדויק"},
                   {"name": "מיקום ליברטי", "precision": "approximate", "basis": "הערך: 21 ק\"מ מהחוף באל-עריש; נקודה שחישבנו"},
                   {"name": "חיצי התקדמות וקו החזית", "precision": "schematic", "basis": "כיווני התקדמות כלליים; הערכים לא מפרטים מסלולים. קו החזית משוער ומצויר ביד"}],
        "still_t": None, "still_alt": "מפה סכמטית של סיני ב-8 ביוני 1967: ביר גפגפה, גדת תעלת סואץ ומיקום ספינת הביון ליברטי מול אל-עריש",
        "areas": [{"id": "sinai", "name": "סיני ורצועת עזה", "short": "סיני", "view": [[27.7, 32.0], [31.8, 34.9]],
                   "intro": "בלילה הופגז כוח שריון ישראלי ליד רומני, ב-03:00 נחלמה מתקפה מצרית בכביש ביר גפגפה–אסמעיליה, בצהריים הותקפה ליברטי ובערב הודיעה מצרים על הסכמה להפסקת אש.",
                   "note": "הלחימה בסיני נמשכה עד 9 ביוני; כאן מוצג רק היום הרביעי."},
                  {"id": "center", "name": "ירושלים והגדה המערבית", "short": "מרכז", "view": [[31.2, 34.6], [32.5, 35.7]],
                   "intro": "ביום הזה נכבשה חברון והושלם כיבוש הגדה המערבית, ובשעה 13:00 פוצצו גשרי הירדן.", "note": "זירה שקטה יחסית: הערכים לא מתארים קרבות נוספים ב-8 ביוני."},
                  {"id": "golan", "name": "רמת הגולן והצפון", "short": "גולן", "view": [[32.8, 35.2], [33.4, 35.9]],
                   "intro": "הצפון הוא מוקד ההחלטות של היום: חטיבות מהגדה נעות צפונה, שר הביטחון אינו מאשר את תוכנית ההתקפה, ובלילה סוריה מקבלת את הפסקת האש.",
                   "note": "המלחמה היבשתית ברמת הגולן הוכרעה רק ב-9 וב-10 ביוני."}],
        "timeline": TL, "still_ts": {"all": 104, "sinai": 104, "center": 66, "golan": 134},
        "credit_notes": ["הקשר: היום הרביעי של מלחמת ששת הימים - 8 ביוני 1967.",
                         "מה שלא מופיע: צומת גולני, גוש לכיש, מסלולי הטרפדות והמטוסים ומיקומם המדויק של ליברטי. הערכים לא נותנים קואורדינטות, והם מצוירים סכמטית ומסומנים כך."]}
(DATA / "1967-06-08.json").write_text(json.dumps(PAGE, ensure_ascii=False, indent=1), encoding="utf-8")
CAS["articles"].update({"he_liberty": {"lang": "he", "title": "תקרית ליברטי", "revid": 43991651}, "en_liberty": {"lang": "en", "title": "USS Liberty incident", "revid": 1376316362},
                        "de_liberty": {"lang": "de", "title": "Liberty-Zwischenfall", "revid": 267195624}})
F = lambda what, val, art, quote, qual="דיווח", scope="": {"what": what, "val": val, "art": art, "quote": quote, "qual": qual, "scope": scope}
D4 = [{"id": "f1", "area": "sinai", "clock": "14:00–כעשרים דקות אחרי", "name": "ליברטי (ספינת ביון אמריקאית)", "il": [], "ar": [],
       "oth": [F("k", "34", "he_liberty", 'מתוך 294 ימאים אמריקאיים בצוות "ליברטי", נהרגו 34 ונפצעו 171.', scope="צוות ליברטי, מתוך 294"), F("w", "171", "he_liberty", 'מתוך 294 ימאים אמריקאיים בצוות "ליברטי", נהרגו 34 ונפצעו 171.', scope="צוות ליברטי, מתוך 294"),
               F("k", "34", "en_liberty", "The attack killed 34 crew members", scope="צוות ליברטי"), F("w", "171", "en_liberty", "wounded 171 crew members", scope="צוות ליברטי"),
               F("k", "34", "de_liberty", "Insgesamt wurden 34 Besatzungsmitglieder getötet und 172 verletzt.", scope="צוות ליברטי"), F("w", "172", "de_liberty", "Insgesamt wurden 34 Besatzungsmitglieder getötet und 172 verletzt.", scope="צוות ליברטי")], "t": LOGT["s4"], "at": "liberty"}]
CAS["data"]["jun8"] = D4
(DATA / "1967-casualties.json").write_text(json.dumps(CAS, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(ITEMS), "items,", len(SFX), "sound cues,", len(LOG), "log entries,", len(ACTS), "acts,", len(D4), "casualty events")
