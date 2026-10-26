#!/usr/bin/env python3
"""Authors Operation Kadesh / the Sinai War (29 Oct - 5 Nov 1956) for /war/ as ONE scene on the Six-Day engine: writes war/data/1956-10-29-events.json.

Source: he.wikipedia "מלחמת סיני" (the redirect target of "מבצע קדש"), pinned revision 43748748 (2026-08-13), CC BY-SA 4.0.
Rules (same as the 1967 days): every card carries a quote that IS a substring of that revision (elisions marked [...], nobody killed is named); times are the article's own
wording; a move is drawn only where a quote says the unit went there, every path is schematic and labelled so; what the article does not say stays blank.
Run: python3 tools/war_data_1956_kadesh.py [--check-quotes ARTICLE.txt]   (the plain text of the pinned revision; the build asserts every quote against it)
"""
import json, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "war" / "data"
REV = 43748748
DAYS = [("1956-10-29", "29.10"), ("1956-10-30", "30.10"), ("1956-10-31", "31.10"), ("1956-11-01", "1.11"), ("1956-11-02", "2.11"), ("1956-11-03", "3.11"), ("1956-11-04", "4.11"), ("1956-11-05", "5.11")]
DUR, GAP = 150, 8                      # animation units per day / pause between days
T0 = lambda d: d * (DUR + GAP)

def pl(name, lat, lon, side, basis="נקודת המקום בוויקיפדיה העברית", prec="exact"):
    return {"name": name, "lat": lat, "lon": lon, "precision": prec, "side": side, "basis": f'קואורדינטות הערך "{name}": {basis}' if prec == "exact" else basis}

PLACES = {
    "kuntilla": pl("כונתילה", 30.00296, 34.68193, "ar"), "mitla": pl("מעבר המיתלה", 30.04944444, 33.02416667, "ar"),
    "naqb": pl("ראס אל-נקב (מעבר נטפים)", 29.598884, 34.867816, "ar", "ראס אל-נקב: נקודת מעבר נטפים בוויקיפדיה העברית, קירוב", "approximate"),
    "qataf": pl("אום כתף", 30.83885, 34.25582778, "ar"), "ageila": pl("אבו עגילה", 30.84313889, 34.11773333, "ar"), "kusseima": pl("קוסיימה", 30.666667, 34.37, "ar"),
    "nitzana": pl("ניצנה", 30.88612852, 34.42155274, "il"), "gifgafa": pl("ביר גפגפה", 30.40722222, 33.15416667, "ar"), "libni": pl("ג'בל ליבני", 30.72986, 33.8395, "ar"),
    "arish": pl("אל-עריש", 31.13, 33.8, "ar"), "rafah": pl("רפיח", 31.28861111, 34.25194444, "ar"), "khan": pl("ח'אן יונס", 31.34431944, 34.30303, "ar"),
    "gaza": pl("עזה", 31.5075, 34.45972222, "ar"), "dahab": pl("דהב", 28.49305556, 34.50472222, "ar"), "nasrani": pl("ראס נצרני", 27.96471944, 34.41611111, "ar"),
    "sharm": pl("שארם א-שייח'", 27.95, 34.37, "ar"), "tor": pl("א-טור", 28.2417, 33.6222, "ar", "קואורדינטות א-טור: ויקינתונים (נקודת העיר), קירוב", "approximate"),
    "qantara": pl("קנטרה", 30.85, 32.31666667, "ar"), "portsaid": pl("פורט סעיד", 31.26, 32.29, "ar"), "ismailia": pl("אסמעיליה", 30.5833, 32.2667, "ar", "קואורדינטות אסמעיליה: ויקינתונים (נקודת העיר), קירוב", "approximate"),
    "haifa": pl("חיפה", 32.82, 34.99, "il", "נקודת העיר", "approximate"), "eilat": pl("אילת", 29.5577, 34.9519, "il", "נקודת העיר", "approximate"),
    "tmain": pl("רמת דוד (שדה תעופה)", 32.665, 35.18, "il", "מקום שחילות האוויר יצאו ממנו אינו נמסר בערך; הנקודה סכמטית בנגב", "approximate"),
}
P = {k: [v["lat"], v["lon"]] for k, v in PLACES.items()}
AREAS = [{"id": "all", "name": "הכל"}, {"id": "north", "name": "צפון סיני ועזה"}, {"id": "center", "name": "מרכז סיני והמיתלה"}, {"id": "south", "name": "דרום סיני ושארם"}]
BLUE, RED = "#1d5ea8", "#b3261e"

CARDS, ITEMS, ACTS, LOG, SFX, GROW = [], [], [], [], [], []
def at(day, minute):               # animation time of a clock minute inside a day (linear over the day's 0..1440 minutes)
    return round(T0(day) + minute / 1440 * DUR, 2)

def card(cid, day, clock, minute, area, unit, title, quote, geom=None, nopos=None, note="", prec="exact", end=None):
    CARDS.append({"id": cid, "t": f"{DAYS[day][1]} {clock}", "time_label": f"{DAYS[day][1]} {clock}", "start_min": day * 1440 + minute, "end_min": day * 1440 + (end if end is not None else minute),
                  "time_precision": prec, "unit": unit, "title": title, "quote": quote, "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area})
    t = at(day, minute)
    ACTS.append({"s": t, "e": t + 6, "clock": f"יום {day + 1} ({DAYS[day][1]}) · {clock} · {title[:28]}", "min": day * 1440 + minute, "view": VIEWS[area], "caps": [], "_c": cid})
    LOG.append({"t": t + 1, "clock": f"{DAYS[day][1]} · {clock}", "q": quote, "n": title, "area": area})
    return t

VIEWS = {"all": [[27.7, 32.0], [32.9, 35.3]], "north": [[30.7, 32.2], [31.7, 34.7]], "center": [[29.9, 32.7], [31.2, 34.8]], "south": [[27.7, 33.2], [29.9, 35.1]]}
mk = lambda place, kind, note="": {"type": "marker", "place": place, "kind": kind, "note": note}
arrow = lambda path, t0, t1, label, color, area, trail="tank", hold=2400: {"type": "arrow", "path": path, "t0": t0, "t1": t1, "label": label, "color": color, "hold": hold, "area": area, "trail": trail}
boom = lambda p, t, area, big=1: {"type": "boom", "at": P[p] if isinstance(p, str) else p, "t": t, "dur": 1.3, "big": big, "area": area}
mark = lambda p, t0, t1, label, area: {"type": "mark", "at": P[p] if isinstance(p, str) else p, "t0": t0, "t1": t1, "label": label, "area": area}
def fly(legs, label, area, side="iaf"):
    return {"type": "fly", "side": side, "label": label, "area": area, "off": None, "legs": [{"t0": a, "t1": b, "path": p} for a, b, p in legs]}
def circle(pid, day, minute, label, area, radius=6000):
    t = at(day, minute); GROW.append({"id": pid, "center": P[pid], "radius_m": radius, "t0": t, "t1": t + 3, "area": area, "label": f"קו חזית משוער: {label}", "lab_to": t + 40})

# ---- day 1: 29 Oct
t = card("k0", 0, "15:00", 900, "center", "para", "הצנחה בפתח המזרחי של מעבר המיתלה (מבצע מכבש)",
         'ביום ב\' 29 באוקטובר 1956 בשעה 15:00 הוצנח גדוד הצנחנים 890, בפיקודו של רס"ן רפאל איתן, בפתח המזרחי של מעבר המיתלה, כ-70 ק"מ ממזרח לתעלת סואץ',
         [mk("mitla", "para", "ההצנחה")], ["נקודת ההמראה אינה נמסרת בערך: מצוירת סכמטית מהנגב"])
ITEMS += [fly([(t - 6, t, [P["tmain"], [31.0, 33.9], P["mitla"]]), (t + 0.5, t + 6, [P["mitla"], [30.9, 34.0], P["tmain"]])], "מטוסי דקוטה: הצנחה (סכמטי)", "center"),
          mark("mitla", t, t + 25, "גדוד 890 מוצנח: 15:00", "center"), boom("mitla", t, "center")]
t = card("k1", 0, "לפי הערך: 29 באוקטובר", 1080, "south", "tank", "חטיבה 202 כובשת את כונתילה וביר חמד ונעה מערבה אל המיתלה",
         'בהתאם לתוכנית, כבשה חטיבת הצנחנים 202 את כונתילה ואת ביר חמד, הסמוכים לגבול, והחלה לנוע מערבה אל עבר מעבר המיתלה',
         [mk("kuntilla", "fight")], ["ביר חמד: אין קואורדינטות בערך; מסומנת כונתילה"], prec="approximate")
ITEMS.append(arrow([P["kuntilla"], [30.02, 34.0], [30.05, 33.3], [30.05, 33.15]], t, t + 60, "חטיבה 202 (סכמטי)", BLUE, "center", "tank"))
circle("kuntilla", 0, 1080, "כונתילה (29–30 באוקטובר)", "south", 5000)
t = card("k2", 0, "בלילה", 1320, "center", "tank", "חטיבה 4 מקבלת פקודה לכבוש את מתחם קוסיימה",
         'ב-29 באוקטובר בלילה קיבלה חטיבת החי"ר 4 פקודה לכבוש את מתחם קוסיימה, ולהיות מוכנה לחבור אל גדוד הצנחנים שבמעבר המיתלה', [mk("kusseima", "fight")], prec="approximate")
ITEMS.append(arrow([P["nitzana"], [30.75, 34.4], P["kusseima"]], t, t + 20, "חטיבה 4 (סכמטי: ממערב לניצנה)", BLUE, "center", "foot"))
# ---- day 2: 30 Oct
t = card("k3", 1, "בבוקר", 480, "center", "tank", "קוסיימה נכבשת (חטיבות 7 ו-4)", 'הושלם כיבוש מתחם קוסיימה בבוקר 30 באוקטובר', [mk("kusseima", "fight")], prec="approximate")
ITEMS.append(boom("kusseima", t, "center")); circle("kusseima", 1, 480, "קוסיימה (30 באוקטובר)", "center", 7000)
t = card("k4", 1, "אחר הצהריים", 840, "center", "tank", "חטיבה 10 מקבלת פקודה לפרוץ אל אום-כתף",
         'בשעות אחר הצהריים של 30 באוקטובר הורה הרמטכ"ל דיין לחטיבה 10 לפרוץ את כביש ניצנה - אבו עגילה, ולכבוש את אום-כתף', [mk("qataf", "fight"), mk("nitzana", "fight")], prec="approximate",
         note='הערך מציין בכותרת "כישלון ההתקפה על אום-כתף"; המתחם נכבש למחרת ללא קרב.')
ITEMS.append(arrow([P["nitzana"], [30.85, 34.35], P["qataf"]], t, t + 12, "חטיבה 10 (סכמטי)", BLUE, "center", "foot"))
t = card("k5", 1, "30 באוקטובר", 600, "center", "mig", "קרב אוויר מעל המיתלה: מיג מצרי אחד מופל",
         'ב-30 באוקטובר עלו לאוויר מטוסי דאסו מיסטר על מנת לחפות על הכוח הקרקעי במעבר המיתלה, וכנגדם הוזנקו כ-20 מטוסי קרב מצריים. בקרב הופל מטוס מיג אחד', [mk("mitla", "bomb")], prec="approximate")
ITEMS += [fly([(t, t + 6, [[30.4, 33.8], [30.2, 33.4], P["mitla"]]), (t + 6.5, t + 11, [P["mitla"], [30.4, 33.8], [30.9, 34.2]])], "מטוסי מיסטר מחפים על המעבר (סכמטי)", "center"),
          {"type": "destroyed", "t": t + 6, "side": "ar", "n": 1, "area": "center", "label": "מיג מצרי שהופל"}]
t = card("k6", 1, "בלילה שבין 30 ל-31", 1380, "center", "tank", "חטיבה 202 חוברת אל גדוד 890 סמוך למצבת פרקר",
         'ובלילה שבין 30 ל-31 באוקטובר חברה אל גדוד הצנחנים בפתח מעבר המיתלה, סמוך למצבת פרקר', [mk("mitla", "fight")], prec="approximate")
circle("mitla", 1, 1380, "פתח מעבר המיתלה (30–31 באוקטובר)", "center", 7000)
# ---- day 3: 31 Oct
t = card("k7", 2, "בבוקר", 480, "center", "tank", "גדוד 82 של חטיבה 7 כובש את מתחם אבו עגילה",
         'בבוקר יום 31 באוקטובר כבש גדוד 82 של חטיבה 7 את מתחם אבו עגילה', [mk("ageila", "fight")], prec="approximate")
ITEMS += [arrow([P["nitzana"], [30.86, 34.3], P["ageila"]], t, t + 12, "גדוד 82, חטיבה 7 (סכמטי)", BLUE, "center", "tank"), boom("ageila", t + 12, "center", 2),
          arrow([P["ageila"], [30.78, 34.0], P["libni"]], t + 20, t + 40, "גדוד 82: צומת ג'בל ליבני (סכמטי)", BLUE, "center", "tank")]
circle("ageila", 2, 480, "אבו עגילה (31 באוקטובר)", "center", 8000)
card("k8", 2, "ביום", 540, "center", "tank", "אום-כתף נתפסת למעשה ללא קרב", 'גדוד 82 תפס את צומת ג\'בל ליבני', [mk("qataf", "fight"), mk("libni", "fight")], prec="approximate",
     note='לפי הערך, בעקבות נסיגה מצרית כללית נכבש מתחם אום-כתף ביום המחרת ללא קרב; כאן מסומן צומת ג\'בל ליבני שגדוד 82 תפס.')
t = card("k9", 2, "בצהרי 31 באוקטובר", 720, "center", "para", "הקרב במעבר המיתלה: אש כבדה על כוח הסיור של הצנחנים",
         'כשנכנס כוח הסיור הגדודי למעבר המזרחי, בצהרי 31 באוקטובר, נפתחה עליו אש כבדה ויעילה [...] הצליחו הצנחנים לטהר את המעבר. המחיר היה כבד - 38 צנחנים הרוגים, וכ-120 פצועים',
         [mk("mitla", "fight")], ["מיקומי האויב במערות ובנקיקים: אינם בערך"], prec="approximate", end=1440 + 480)
ITEMS += [arrow([[30.05, 33.15], P["mitla"]], t, t + 30, "כוח סיור של חטיבה 202 במעבר (סכמטי)", BLUE, "center", "foot"), boom("mitla", t + 6, "center", 2), boom([30.047, 33.04], t + 14, "center", 2)]
t = card("k10", 2, "31 באוקטובר", 600, "center", "mig", "זוג מיסטר מפיל ארבעה ומפירים מצריים",
         'ב-31 באוקטובר, נתקל זוג מטוסי מיסטר ברביעיית מטוסי ומפייר מצריים [...] הצליח זוג המטוסים הישראלי להפיל את ארבעת המטוסים המצריים', [], ["מקום הקרב: אינו בערך"], prec="approximate")
ITEMS.append({"type": "destroyed", "t": t, "side": "ar", "n": 4, "area": "center", "label": "ארבעה ומפירים מצריים שהופלו"})
t = card("k11", 2, "השכם בבוקר", 360, "north", "ship", "המשחתת איברהים אל-אוואל תוקפת את חיפה ונשבית",
         'אחרי שזו תקפה השכם בבוקר 31 באוקטובר את חיפה באש תותחים [...] האונייה נשבתה על 150 מלחיה', [mk("haifa", "bomb")], ["הלכידה: סמוך לחיפה; המקום המדויק אינו בערך"], prec="approximate")
ITEMS += [boom("haifa", t, "north", 1), mark("haifa", t, t + 20, "המשחתת המצרית נשבית", "north")]
t = card("k12", 2, "בערב", 1080, "north", "tank", "אוגדה 77 מופעלת בציר הצפוני",
         'בערבו של 31 באוקטובר, משדעכו החששות מפני התגובה המצרית, הופעלה גם אוגדה 77 [...] משימתה הייתה לפתוח את ציר התנועה בצפון סיני, ולהגיע עד למרחק של 15 ק"מ מהתעלה',
         [mk("rafah", "fight"), mk("arish", "fight")], ["נקודת היציאה והמסלול המדויק: אינם בערך; מצוירים סכמטית על הציר"], prec="approximate")
ITEMS.append(arrow([P["rafah"], P["arish"], [31.0, 33.0], [30.95, 32.5]], t, t + 55, "אוגדה 77: ציר צפון סיני (סכמטי)", BLUE, "north", "tank"))
# ---- day 4: 1 Nov
t = card("k13", 3, "1 בנובמבר", 480, "north", "mig", "חיל האוויר הבריטי והצרפתי מצטרף ומשתק את חיל האוויר המצרי",
         'ב-1 בנובמבר הצטרפו חילות האוויר של הממלכה המאוחדת ושל צרפת למערכה, והצליחו לשתק את חיל האוויר של מצרים', [], ["מיקום הפעולות: אינו בערך; מסומן אזור התעלה"], prec="approximate")
ITEMS.append(mark([30.9, 32.4], t, t + 30, "חילות האוויר הבריטי והצרפתי (מיקום סכמטי)", "north"))
t = card("k14", 3, "1–2 בנובמבר", 1080, "north", "tank", "רפיח נכבשת",
         'ב-1–2 בנובמבר כבש צה"ל את רפיח וב-3 בנובמבר נכבשה ח\'אן יונס', [mk("rafah", "fight")], prec="approximate", end=1440 + 360)
ITEMS.append(boom("rafah", t, "north", 2)); circle("rafah", 3, 1200, "רפיח (1–2 בנובמבר)", "north", 6000)
# ---- day 5: 2 Nov
t = card("k15", 4, "אור ליום 2 בנובמבר", 120, "north", "tank", "פקודה לכבוש את רצועת עזה",
         'אור ליום 2 בנובמבר הורה ראש אג"מ, מאיר עמית לשמחוני לכבוש את רצועת עזה', [mk("gaza", "fight")], prec="approximate")
t = card("k16", 4, "2 בנובמבר", 600, "north", "tank", "הפיקוד המצרי מורה על נסיגה מסיני",
         'ב-2 בנובמבר הורה הפיקוד המצרי על נסיגה מסיני', [], ["מסלולי הנסיגה: אינם בערך; מצוירת נסיגה סכמטית לכיוון התעלה"], prec="approximate")
ITEMS.append(arrow([P["ageila"], [30.8, 33.4], [30.6, 32.6], P["ismailia"]], t, t + 40, "נסיגה מצרית (סכמטי)", RED, "center", "foot"))
t = card("k17", 4, "2 בנובמבר", 780, "south", "para", "גדוד 88 מוצנח בא-טור", 'שהוצנח בא-טור ב-2 בנובמבר', [mk("tor", "para")], ["השעה: אינה בערך"], prec="approximate")
ITEMS += [mark("tor", t, t + 40, "גדוד 88 מוצנח בא-טור", "south"), arrow([P["tor"], [28.1, 34.0], P["sharm"]], t + 80, t + 150 + 60, "גדוד 88: לאורך החוף אל שארם (סכמטי)", BLUE, "south", "foot")]
t = card("k18", 4, "2–5 בנובמבר", 900, "south", "tank", "חטיבה 9 נעה מראס אל-נקב דרומה, דרך דהב",
         'בין 2 ל-5 בנובמבר נעה חטיבת המילואים הממונעת (חטיבה 9) מראס אל-נקב לדרום סיני [...] עברה דרך כפר החוף ד\'הב', [mk("naqb", "fight"), mk("dahab", "fight")], prec="approximate", end=3 * 1440 + 1440)
ITEMS.append(arrow([P["eilat"], P["naqb"], P["dahab"]], t, t + 3 * (DUR + GAP) - 20, "חטיבה 9: אל-נקב, דהב (סכמטי; הימים לפי הטווח 2–5 בנובמבר)", BLUE, "south", "tank"))
# ---- day 6: 3 Nov
t = card("k19", 5, "3 בנובמבר", 720, "north", "tank", "ח'אן יונס נכבשת", 'ב-1–2 בנובמבר כבש צה"ל את רפיח וב-3 בנובמבר נכבשה ח\'אן יונס', [mk("khan", "fight")], prec="approximate")
ITEMS += [arrow([P["rafah"], P["khan"]], t, t + 14, "חטיבה 11 (סכמטי)", BLUE, "north", "tank"), boom("khan", t + 14, "north", 2)]; circle("khan", 5, 720, "ח'אן יונס (3 בנובמבר)", "north", 5000)
# ---- day 8: by 5 Nov
t = card("k20", 7, "עד 5 בנובמבר", 720, "south", "tank", "חטיבה 9 כובשת את ראס נצרני ואת שארם א-שייח'",
         'כבשה את מתחם תותחי החוף בראס נצרני, ולמחרת כבשה גם את שארם א-שייח', [mk("nasrani", "fight"), mk("sharm", "fight")], ["היום והשעה: אינם בערך; הטווח של הערך הוא 2–5 בנובמבר"], prec="approximate")
ITEMS += [boom("nasrani", t, "south", 2), boom("sharm", t + 10, "south", 2)]; circle("sharm", 7, 720, "ראס נצרני ושארם א-שייח' (עד 5 בנובמבר)", "south", 9000)
t = card("k21", 7, "5 בנובמבר", 1080, "all", "ship", "ברית המועצות שולחת אגרות חריפות לצרפת, לבריטניה ולישראל",
         'ב-5 בנובמבר שיגר ראש ממשלת ברית המועצות, ניקולאי בולגנין, אגרות חריפות לצרפת, הממלכה המאוחדת וישראל', [], ["אירוע מדיני: אין לו מיקום על המפה"])
LOG.append({"t": at(7, 1200), "clock": "סיכום", "q": 'ישראל: 172 הרוגים, 817 פצועים [...] מצרים: לפי ההערכות במלחמה נהרגו בין 1,500 ל-3,000 חיילים מצריים. כ-4,000 נפלו בשבי', "n": "אבדות (כפי שהערך מוסר)", "area": "all"})

def build_event_file():
    end = T0(7) + DUR
    acts = []
    for i, a in enumerate(sorted(ACTS, key=lambda a: a["s"])):
        a = dict(a); a.pop("_c"); acts.append(a)
    for i in range(len(acts) - 1):
        acts[i]["e"] = acts[i + 1]["s"]
    acts[-1]["e"] = end
    days = [{"n": n + 1, "label": lab, "T0": T0(n), "min0": n * 1440, "dur": DUR, "date": d} for n, (d, lab) in enumerate(DAYS)]
    ev = {"source": {"title": "מלחמת סיני", "url": "https://he.wikipedia.org/wiki/%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%A1%D7%99%D7%A0%D7%99", "revid": REV, "revision_time": "2026-08",
                     "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
                     "permalink": f"https://he.wikipedia.org/w/index.php?title=%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%A1%D7%99%D7%A0%D7%99&oldid={REV}", "authors_url": "https://he.wikipedia.org/w/index.php?title=%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%A1%D7%99%D7%A0%D7%99&action=history"},
          "places": PLACES, "areas": {}, "events": CARDS, "time_range": [0, len(DAYS) * 1440], "area_filter": AREAS, "views": VIEWS, "still_views": VIEWS, "view": VIEWS["all"],
          "cards_title": "אירועי המלחמה (סיכום שלנו על בסיס הערך)", "casualties": [],
          "scene": {"dur": end, "view0": VIEWS["all"], "acts": acts, "log": sorted(LOG, key=lambda l: l["t"]), "sfx": SFX, "items": ITEMS, "bases": [], "areas": [],
                    "show_places": list(PLACES), "icons": True,
                    "control": {"label": 'עיגול שליטה: מקום שהערך מזכיר שכוחות צה"ל נכנסו אליו (סכמטי)', "grow": GROW}},
          "whole": {"date0": DAYS[0][0], "days": days}}
    for it in ev["scene"]["items"]:                          # a unit marker lives to the end of ITS day (same rule as the six-days page)
        if it["type"] in ("arrow", "walk", "fly", "shell"):
            k = int((it.get("t0") if "t0" in it else it["legs"][0]["t0"]) // (DUR + GAP)); it["u"] = T0(k) + DUR
            if it.get("label", "").startswith(("חטיבה 9", "גדוד 88")):      # the two multi-day moves (2-5 Nov) live to the end of the war
                it["u"] = T0(7) + DUR
    return ev

def check_quotes(ev, article):
    txt = Path(article).read_text(encoding="utf-8"); bad = 0
    for c in ev["events"]:
        for seg in [s.strip() for s in c["quote"].replace("[...]", "\n").split("\n") if s.strip()]:
            if seg not in txt:
                bad += 1; print("QUOTE NOT IN ARTICLE:", c["id"], seg[:70])
    return bad

if __name__ == "__main__":
    ev = build_event_file()
    if "--check-quotes" in sys.argv:
        sys.exit(1 if check_quotes(ev, sys.argv[sys.argv.index("--check-quotes") + 1]) else 0)
    (DATA / "1956-10-29-events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(CARDS)} cards, {len(ITEMS)} scene items, {len(GROW)} control circles, dur {ev['scene']['dur']}")
