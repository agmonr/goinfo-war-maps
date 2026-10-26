#!/usr/bin/env python3
"""Authors the Yom Kippur War (6-24 Oct 1973, 19 days) for /war/ as ONE scene on the Six-Day engine: writes war/data/1973-10-06-events.json.

Source: he.wikipedia "מלחמת יום הכיפורים", pinned revision 44036138 (2026-10-07), CC BY-SA 4.0. Chapters = the article's own three phases ("את 19 ימי הלחימה נהוג לחלק לשלושה שלבים"):
(1) holding the Arab attack 6-10 Oct, (2) 11-14 Oct, (3) 15-24 Oct. Same rules as the other war pages: every card quote is asserted by --check-quotes to be a substring of
that revision (elisions [...]); a move is drawn only where a quote names the unit and the place, every path is schematic and labelled so; nothing the article does not say is added.
Run: python3 tools/war_data_1973_yomkippur.py [--check-quotes ARTICLE.txt]
"""
import json, sys
import war_sfx
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "war" / "data"
REV = 44036138
DAYS = [(f"1973-10-{6 + i:02d}", f"{6 + i}.10") for i in range(19)]
CHAPTERS = [dict(name="שלב 1: הבלימה", sub="6–10 באוקטובר", a=0, b=4), dict(name="שלב 2: 11–14 באוקטובר", sub="מתקפה בסוריה; ההתקפה המצרית נהדפת", a=5, b=8),
            dict(name="שלב 3: 15–24 באוקטובר", sub="הצליחה, הכיתור והפסקת האש", a=9, b=18)]
DUR, GAP = 150, 6   # 150 s of play per war day at 1x (the Six-Day page runs 180-240 s per day); was 80 and felt fast (the owner 10-23)
T0 = lambda d: d * (DUR + GAP)
CH_END = lambda d: T0(next(c["b"] for c in CHAPTERS if c["a"] <= d <= c["b"])) + DUR

def pl(name, lat, lon, side, basis="נקודת המקום בוויקיפדיה העברית", prec="exact"):
    return {"name": name, "lat": lat, "lon": lon, "precision": prec, "side": side, "basis": f'קואורדינטות הערך "{name}": {basis}' if prec == "exact" else basis}

PLACES = {
    "quneitra": pl("קוניטרה", 33.11666667, 35.81666667, "ar"), "hermon": pl("מוצב החרמון", 33.304502, 35.797561, "il"), "damascus": pl("דמשק", 33.51305556, 36.29194444, "ar"),
    "hushniya": pl("ח'ושניה", 32.99888889, 35.81111111, "il"), "nafakh": pl("נפח (מחנה)", 33.0, 35.77, "il", "אין קואורדינטות בערך; הנקודה סכמטית בלב רמת הגולן", "approximate"),
    "bridge": pl("גשר בנות יעקב", 33.01028333, 35.62828611, "il"), "katzrin": pl("קצרין", 32.99277029, 35.68795316, "il"), "gamla": pl("אזור גמלא", 32.88, 35.74, "il", "אין קואורדינטות בערך; הנקודה סכמטית ממזרח לכנרת (7 ק\"מ מהים)", "approximate"),
    "elal": pl("אזור אל-על", 32.78, 35.72, "il", "אין קואורדינטות בערך; הנקודה סכמטית בדרום רמת הגולן", "approximate"),
    "latakia": pl("לטקיה (חוף סוריה)", 35.51333333, 35.77055556, "ar", "הערך: סמוך לחופי סוריה; הנקודה היא נמל לטקיה", "approximate"),
    "qantara": pl("קנטרה", 30.85, 32.31666667, "ar"), "ismailia": pl("אסמעיליה", 30.5833, 32.2667, "ar", "קואורדינטות אסמעיליה: ויקינתונים (נקודת העיר), קירוב", "approximate"),
    "suez": pl("סואץ", 29.9668, 32.5498, "ar", "קואורדינטות סואץ: ויקינתונים (נקודת העיר), קירוב", "approximate"), "budapest": pl("מעוז בודפסט", 31.1875, 32.36916667, "il"),
    "lakes": pl("האגמים המרים", 30.33333333, 32.38333333, "ar"), "chinese": pl("החווה הסינית", 30.45, 32.4, "ar", "קרב החווה הסינית: הערך מציין את הנקודה", "approximate"),
    "portsaid": pl("פורט סעיד", 31.26, 32.29, "ar"), "cairo": pl("קהיר", 30.03333333, 31.21666667, "ar"),
    "km101": pl("הק\"מ ה-101 מקהיר", 29.96, 32.3, "ar", "הק\"מ ה-101 בדרך קהיר–סואץ: חישוב שלנו מהדרך, קירוב", "approximate"),
    "eilat": pl("אילת", 29.55391689, 34.94421963, "il"),
}
P = {k: [v["lat"], v["lon"]] for k, v in PLACES.items()}
AREAS = [{"id": "all", "name": "הכל"}, {"id": "golan", "name": "רמת הגולן וסוריה"}, {"id": "sinai", "name": "סיני ותעלת סואץ"}, {"id": "sea", "name": "הים"}]
VIEWS = {"all": [[29.0, 31.4], [34.3, 36.9]], "golan": [[32.6, 35.4], [33.8, 36.6]], "sinai": [[29.6, 31.6], [31.6, 33.5]], "sea": [[31.0, 32.0], [35.8, 36.0]]}
BLUE, RED = "#1d5ea8", "#b3261e"
CARDS, ITEMS, ACTS, LOG, SFX, GROW = [], [], [], [], [], []
at = lambda day, minute: round(T0(day) + minute / 1440 * DUR, 2)

CTX_SEQ = {"רקע": -2000, "סיכום": 40000, "אחרי": 41000}
# the owner 10-23: a war page is about how the forces MOVED: 1-2 cards per battle, no talks / background / after, no totals. KEEP is the whole selection; every other card (and the scene items that
# were drawn for it) is dropped at build time, its data stays here.
KEEP = set("y1 y2 y3 y5 w4 w3 y8 y9 y10 i10 y11 i11 w9 y12 y14 i50 y16 y19 y20 i51 w10 y21 y22 w13 y24 y26 w16 w17 w18 w19 w21 y27 w22 y28 i17 y29 w24 y30 y31 i20 w20 o1 o2 o3 o4 o5 o6 o7 s1 r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12 r13 ln dm r14 w1 w2 w11 w14 sa am fu w5 adv1 adv2 adv3".split())
OWN, _LAST, DROPPED = {}, [None, 0], set()
CTX_ON = {"סיכום"}                 # add "רקע" / "אחרי" to bring those groups back
CTX_N = {"רקע": 0, "סיכום": 0, "אחרי": 0}
CTX_BASE = T0(18) + DUR + 2
def card(cid, day, clock, minute, area, unit, title, quote, geom=None, nopos=None, note="", prec="exact", end=None, view=None, src=None, ctx=None):
    """ctx = "רקע" / "סיכום" / "אחרי": a card of the list with NO clock and no scene act (context before the war, results, what followed); src = {k,t,u,p?}: the card's own source (default: the main article)."""
    if _LAST[0]:
        OWN[_LAST[0]] = (_LAST[1], len(ITEMS))        # the scene items appended since the previous card belong to it
    _LAST[0], _LAST[1] = cid, len(ITEMS)
    if cid not in KEEP:
        DROPPED.add(cid)
        return None if ctx else at(day, minute)                       # the owner 10-23: no background and no "after" cards on a war page (the war starts with the invasion); the data stays here, behind CTX_ON
    if ctx:
        CTX_SEQ[ctx] += 1
        CARDS.append({"id": cid, "t": ctx, "time_label": ctx, "start_min": CTX_SEQ[ctx], "end_min": CTX_SEQ[ctx], "time_precision": "none", "unit": unit, "title": title, "quote": quote,
                      "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area, **({"src": src} if src else {})})
        # the animation shows the card too: background cards play first (T 0.6..29, the quiet hours before the first dated card), summaries and "after" cards after 24.10 (the bar ends later)
        k = CTX_N[ctx]; CTX_N[ctx] += 1
        t = round(0.6 + 3.2 * k, 2) if ctx == "רקע" else round(CTX_BASE + 3.4 * (CTX_N["סיכום"] + CTX_N["אחרי"] - 1), 2)
        ACTS.append({"s": t, "e": t + 3, "clock": ctx, "min": 0 if ctx == "רקע" else 18 * 1440 + 1439, "view": VIEWS[area], "caps": []})
        LOG.append({"t": t + 0.2, "clock": ctx, "q": quote, "n": title, "area": area, **({"src": src} if src else {})})
        return None
    CARDS.append({"id": cid, "t": f"{DAYS[day][1]} {clock}", "time_label": f"{DAYS[day][1]} {clock}", "start_min": day * 1440 + minute, "end_min": day * 1440 + (end if end is not None else minute),
                  "time_precision": prec, "unit": unit, "title": title, "quote": quote, "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area, **({"src": src} if src else {})})
    t = at(day, minute)
    ACTS.append({"s": t, "e": t + 5, "clock": f"יום {day + 1} ({DAYS[day][1]}) · {clock} · {title[:26]}", "min": day * 1440 + minute, "view": VIEWS[view or area], "caps": []})
    LOG.append({"t": t + 1, "clock": f"{DAYS[day][1]} · {clock}", "q": quote, "n": title, "area": area, **({"src": src} if src else {})})
    return t

mk = lambda place, kind, note="": {"type": "marker", "place": place, "kind": kind, "note": note}
arrow = lambda path, t0, t1, label, color, area, trail="tank": {"type": "arrow", "path": path, "t0": t0, "t1": t1, "label": label, "color": color, "hold": 2400, "area": area, "trail": trail}
boom = lambda p, t, area, big=1: {"type": "boom", "at": P[p] if isinstance(p, str) else p, "t": t, "dur": 1.3, "big": big, "area": area}
mark = lambda p, t0, t1, label, area: {"type": "mark", "at": P[p] if isinstance(p, str) else p, "t0": t0, "t1": t1, "label": label, "area": area}
def circle(cid, center, radius, day, minute, label, area):
    t = at(day, minute); GROW.append({"id": cid, "center": center, "radius_m": radius, "t0": t, "t1": t + 3, "area": area, "label": f"קו חזית משוער: {label}", "lab_to": t + 40})

# ================= chapter 1: 6-10 Oct =================
card("y0", 0, "בבוקר", 540, "all", "tank", "ראש הממשלה מכריעה לגייס את המילואים, שעות לפני פרוץ המלחמה",
     'ביום הכיפורים עצמו, שעות לפני פרוץ המלחמה, הכריעה ראש הממשלה גולדה מאיר לגייס את המילואים לבקשתו של הרמטכ"ל דוד אלעזר', [], ["החלטה מדינית: אין לה מיקום על המפה; השעה אינה בערך"], prec="approximate")
t = card("y1", 0, "13:55", 835, "all", "tank", "13:55: ההתקפה המצרית והסורית המתואמת נפתחת בדרום ובצפון",
         'ביום שבת, 6 באוקטובר, יום הכיפורים, בשעה 13:55, פתחו הכוחות המצריים והסוריים בהתקפה מתואמת מראש על כוחות צה"ל בדרום ובצפון [...] ותקיפה אווירית רבת עוצמה בהיקף של כ-750 גיחות, מהן כ-450 נגד מטרות בסיני ובצפון',
         [mk("qantara", "bomb"), mk("quneitra", "bomb")], ["מקומות התקיפה האווירית: אינם בערך"])
ITEMS += [boom("qantara", t, "sinai", 2), boom("quneitra", t, "golan", 2)]
t = card("y2", 0, "אחרי 13:55", 850, "sinai", "tank", "הצליחה המצרית: חמש דיוויזיות חי\"ר לאורך גדת התעלה",
         'בצליחת התעלה השתתפו חמש דיוויזיות חי"ר מצריות, שהתבססו לאורך גדתה המזרחית, ברצועה שרוחבה בין 3 ל-4 ק"מ',
         [mk("qantara", "fight"), mk("ismailia", "fight"), mk("suez", "fight")], ["נקודות הצליחה המדויקות: אינן בערך; מסומנות קנטרה, אסמעיליה וסואץ על התעלה"], prec="approximate")
ITEMS += [arrow([[30.85, 32.30], [30.85, 32.42]], t, t + 10, "צליחה מצרית (סכמטי)", RED, "sinai", "foot"), arrow([[30.58, 32.27], [30.58, 32.40]], t + 1, t + 11, "צליחה מצרית (סכמטי)", RED, "sinai", "foot"),
          arrow([[29.97, 32.50], [29.97, 32.60]], t + 2, t + 12, "צליחה מצרית (סכמטי)", RED, "sinai", "foot")]
t = card("y3", 0, "אחרי 13:55", 860, "golan", "tank", "הסורים תוקפים לאורך כל הגבול ברמת הגולן",
         'בחזית הצפון תקפו שלוש דיוויזיות סוריות של חיל רגלים ממוכן ברמת הגולן (שכללו כ-800 טנקים) ו-1,200 קני ארטילריה, לכל אורך הגבול הסורי-ישראלי', [mk("quneitra", "fight")], ["קווי ההתקפה המדויקים: אינם בערך"])
ITEMS += [arrow([[33.1, 36.0], [33.05, 35.85]], t, t + 10, "התקפה סורית (סכמטי)", RED, "golan", "tank"), arrow([[32.82, 35.95], [32.80, 35.75]], t + 1, t + 11, "התקפה סורית (סכמטי)", RED, "golan", "tank")]
card("y4", 0, "משעת פתיחת המלחמה", 870, "sinai", "tank", "בחזית התעלה: אוגדת סיני, חטיבת טנקים אחת ו-20 מעוזים",
     'מול הכוחות המצריים עמדה אוגדת סיני עם 7 סוללות ארטילריה, כאשר רק חטיבת טנקים אחת (חטיבה 14) שחנתה בקו התעוזים ו-457 לוחמים ב-20 מעוזים נמצאים בחזית',
     [mk("budapest", "fight")], ["מיקומי המעוזים: אינם בערך; מסומן מעוז בודפסט שהערך נוקב בו"], prec="approximate")
t = card("y5", 0, "לא צוין", 900, "golan", "para", "מוצב החרמון נופל בידי קומנדו סורי",
         'מוצב החרמון הישראלי, ששימש מוצב תצפית חשוב של המודיעין וחיל האוויר, נפל בידי כוח קומנדו סורי אשר הונחת מארבעה מסוקים ומרביתו הגיע ברגל מהחרמון הסורי', [mk("hermon", "fight")], ["הערך אינו מציין מתי נפל המוצב (הפסקה על הפתיחה); מוצב בפרק הפתיחה"], prec="approximate")
ITEMS.append(boom("hermon", t, "golan", 1))
t = card("y6", 0, "בלילה", 1380, "sea", "ship", "קרב סטי\"לים ראשון בסמוך לחופי סוריה",
         'כבר בלילה הראשון למלחמה, יזם חיל הים קרב סטי"לים בסמוך לחופי סוריה, שהיה קרב טילי ים-ים הראשון בהיסטוריה, ובו הושמדו מספר ספינות סוריות ללא אבדות לישראל',
         [mk("latakia", "bomb")], ["מקום הקרב: 'סמוך לחופי סוריה'; הנקודה סכמטית"], prec="approximate")
ITEMS += [boom("latakia", t, "sea", 2), {"type": "destroyed", "t": t, "side": "ar", "n": 1, "area": "sea", "label": "ספינות סוריות שהושמדו (הערך: מספר ספינות; מצויירת אחת)"}]
t = card("y7", 1, "בבוקר", 480, "golan", "tank", "ההוראה להכין את גשרי הירדן לפיצוץ", 'בבוקר 7 באוקטובר ניתנה ההוראה להכין את גשרי הירדן לפיצוץ', [mk("bridge", "bomb")])
t = card("y8", 1, "7 באוקטובר", 720, "golan", "tank", "הסורים חודרים למרכז הגולן: קרב חושניה; בערב נבלמים",
         'וחדרו בחלק המרכזי עד למרכז הגולן, לאזור חושניה ונפח (קרב חושניה) [...] לעת ערב נבלמו הסורים', [mk("hushniya", "fight"), mk("nafakh", "fight")], ["מיקום נפח: אין קואורדינטות בערך"], prec="approximate", end=1080)
ITEMS += [arrow([[33.05, 35.95], P["hushniya"], P["nafakh"]], t, t + 22, "חדירה סורית למרכז הגולן (סכמטי)", RED, "golan", "tank"), boom("hushniya", t + 12, "golan", 2)]
t = card("y9", 1, "7 באוקטובר", 800, "golan", "mig", "בדרום הגולן: כוח סורי מגיע לאזור גמלא ונבלם בידי סקייהוקים",
         'כוח אחר הגיע לאזור גמלא, מרחק 7 ק"מ מים כנרת, ושם נבלמו בידי מטוסי סקיהוק ישראלים', [mk("gamla", "bomb")], ["נקודת גמלא: אין קואורדינטות בערך"], prec="approximate")
ITEMS.append(arrow([[32.84, 35.95], P["gamla"]], t, t + 14, "כוח סורי (סכמטי)", RED, "golan", "tank"))
t = card("y10", 1, "7 באוקטובר", 900, "sinai", "tank", "מגיעים המילואים; שלוש אוגדות מייצבות קו בלימה בציר החת\"ם",
         'ב-7 באוקטובר כיממה לאחר תחילת המלחמה, החלו להגיע כוחות המילואים והוטלו למערכה בשלוש אוגדות ישראליות [...] שלוש האוגדות הצליחו לייצב קו בלימה לאורך ציר החת"ם כ-10 ק"מ מזרחית לתעלה',
         [], ["ציר החת\"ם: אין קואורדינטות בערך; הקו מצויר סכמטית כ-10 ק\"מ מזרחית לתעלה"], prec="approximate")
ITEMS.append(arrow([[31.0, 32.62], [30.5, 32.62], [30.05, 32.72]], t, t + 20, "קו הבלימה (סכמטי): כ-10 ק\"מ ממזרח לתעלה", BLUE, "sinai", "tank"))
t = card("y11", 2, "8 באוקטובר", 600, "sinai", "tank", "מתקפת הנגד המדורגת בדרום נכשלת",
         'ב-8 באוקטובר החלה מתקפת נגד מדורגת של שתי האוגדות, תחילה בצפון ולאחר מכן במרכז. מתקפה זו נכשלה, ואוגדה 162 ספגה אבדות כבדות', [], ["מקומות ההתקפה: אינם בערך"], prec="approximate")
t = card("y12", 2, "8 באוקטובר", 660, "golan", "tank", "מתקפת הנגד הישראלית בדרום רמת הגולן", 'ב-8 באוקטובר החלה מתקפת הנגד הישראלית בדרום רמת הגולן', [mk("elal", "fight")], ["קווי ההתקפה: אינם בערך"], prec="approximate")
ITEMS.append(arrow([P["elal"], [32.88, 35.95], [32.95, 36.0]], t, t + 18, "מתקפת נגד ישראלית (סכמטי)", BLUE, "golan", "tank"))
t = card("y13", 2, "8 באוקטובר", 1260, "sea", "ship", "קרב טילים בסמוך לחופי מצרים: שלוש סטי\"לים מצריות טובעות",
         'ב-8 באוקטובר, יזם קרב טילים דומה בסמוך לחופי מצרים – גם בקרב זה טיבע חיל הים שלוש סטי"לים מצריות', [mk("portsaid", "bomb")], ["מקום הקרב: 'סמוך לחופי מצרים'; מסומנת פורט סעיד (סכמטי)"], prec="approximate")
ITEMS += [boom("portsaid", t, "sea", 2), {"type": "destroyed", "t": t, "side": "ar", "n": 3, "area": "sea", "label": "שלוש סטי\"לים מצריות שטובעו"}]
t = card("y14", 3, "9 באוקטובר", 600, "golan", "tank", "קרב עמק הבכא: אוגדת איתן בולמת מתקפת שריון גדולה", 'ב-9 באוקטובר בלמה אוגדת איתן מתקפת שריון גדולה (קרב עמק הבכא)', [], ["אין קואורדינטות לעמק הבכא בערך"], prec="approximate")
t = card("y15", 3, "עד 9 באוקטובר", 900, "sinai", "tank", "קו בר-לב קורס, למעט מעוז בודפסט",
         'עד 9 באוקטובר התמוטט קו בר-לב למעט מעוז בודפשט (שנשאר בידי ישראל עד סוף המלחמה)', [mk("budapest", "fight")], prec="approximate")
t = card("y16", 4, "10 באוקטובר", 600, "golan", "tank", "הושלמה דחיקת הסורים מהשטחים שכבשו; החרמון נשאר בידיהם",
         'ב-10 באוקטובר הושלמה הדיפת הסורים מכל השטחים שכבשו בתחילת המלחמה, למעט מוצב החרמון, לאחר שהסורים איבדו כ-900 טנקים', [mk("hermon", "fight")], prec="approximate")
card("y17", 4, "10 באוקטובר", 660, "sinai", "tank", "הרמטכ\"ל לשעבר חיים בר-לב מקבל את הפיקוד על חזית הדרום", 'ב-10 באוקטובר קיבל הרמטכ"ל לשעבר, חיים בר-לב, את הפיקוד על החזית', [], ["החלטת פיקוד: אין לה מיקום על המפה"], prec="approximate")
card("y18", 4, "סיכום חמשת הימים", 1200, "all", "tank", "חמשת הימים הראשונים: כמחצית מאבדות צה\"ל",
     'בחמשת ימי הלחימה הראשונים, שבהם ניכרה השפעת ההפתעה וצה"ל ניהל קרבות בלימה מרים, ספג צה"ל כמחצית מכלל אבדותיו בלוחמים, במטוסים ובטנקים', [], ["אין מספרי אבדות מדויקים בציטוט; הערך נותן אחוז משוער"], prec="approximate")
# ================= chapter 2: 11-14 Oct =================
t = card("y19", 5, "11 באוקטובר", 600, "golan", "tank", "צה\"ל תוקף לתוך סוריה; תוך יומיים 35 ק\"מ מנמל התעופה של דמשק",
         'ב-11 באוקטובר פתח צה"ל במתקפה לתוך שטח סוריה, ותוך יומיים הגיע למרחק 35 ק"מ (טווח תותחים) מנמל התעופה הבין-לאומי של דמשק', [mk("damascus", "fight")], ["הכיוון והנקודה הסופית: אינם בערך; הדרך מצוירת סכמטית לכיוון דמשק"], prec="approximate", end=1440 + 720)
ITEMS.append(arrow([P["quneitra"], [33.25, 36.05], [33.37, 36.12]], t, t + 90, "צה\"ל בתוך סוריה (סכמטי)", BLUE, "golan", "tank"))
circle("syria", [33.28, 36.05], 11300, 5, 600, "המובלעת הסורית (כ-400 קמ\"ר)", "golan")
card("y20", 6, "12 באוקטובר", 600, "golan", "tank", "כוחות עיראקיים מצטרפים ומאלצים את צה\"ל לעצור",
     'ב-12 באוקטובר הצטרפו ללחימה כוחות מחיל המשלוח העיראקי אשר הכריחו את צה"ל לעצור את המתקפה', [], ["מיקום הלחימה: אינו בערך"], prec="approximate")
card("y21", 7, "13 באוקטובר", 600, "sinai", "tank", "מוצב המזח נכנע", 'אנשי מוצב המזח נכנעו ב-13 באוקטובר 1973', [], ["מיקום מוצב המזח: אין קואורדינטות בערך"], prec="approximate")
t = card("y22", 8, "בבוקר", 480, "sinai", "tank", "14 באוקטובר: ההתקפה המצרית הרבתי נהדפת עד הצהריים",
         'ופתחו בהתקפה רבתי על כוחות צה"ל בשעות הבוקר של 14 באוקטובר. עד שעות הצהריים של אותו יום נהדפה ההתקפה תוך אבדות מצריות כבדות', [], ["מקומות הקרב: אינם בערך; מצוירת התקפה סכמטית ממזרח לתעלה"], prec="approximate")
ITEMS += [arrow([[30.6, 32.5], [30.6, 32.95]], t, t + 18, "התקפה מצרית (סכמטי)", RED, "sinai", "tank"), arrow([[30.2, 32.55], [30.2, 32.95]], t + 1, t + 19, "התקפה מצרית (סכמטי)", RED, "sinai", "tank"),
          {"type": "destroyed", "t": t + 18, "side": "ar", "n": 5, "area": "sinai", "label": "הערך: 200 טנקים מצריים אבדו מול 20 ישראליים (נמסר כמספר, מצוייר כסמל)"}]
card("y23", 8, "14 באוקטובר", 780, "sinai", "tank", "ואדי מבעוק וקרב השריון: 200 טנקים מצריים מול 20 ישראליים",
     'המצרים איבדו במהלך זה 200 טנקים, לעומת 20 טנקים שאבדו לצה"ל', [], ["מקומות הקרבות: אינם בערך"], prec="approximate")
# ================= chapter 3: 15-24 Oct =================
t = card("y24", 9, "עם ערב", 1080, "sinai", "para", "מבצע אבירי לב: ראש גשר צפונית לאגם המר הגדול",
         'ב-15 באוקטובר, עם ערב, החל מבצע אבירי לב של צה"ל לצליחת תעלת סואץ [...] ביססו ראש גשר באמצעות העברת כוחות צנחנים בסירות גומי וטנקים מחטיבה 421 ב"תמסחים" צפונית לאגם המר הגדול',
         [mk("lakes", "fight"), mk("chinese", "fight")], ["נקודת הצליחה המדויקת והחווה הסינית: קירוב"], prec="approximate")
ITEMS += [arrow([[30.50, 32.38], [30.50, 32.27]], t, t + 14, "צליחה ישראלית (סכמטי)", BLUE, "sinai", "foot"), boom("chinese", t + 6, "sinai", 1)]
circle("chinese", P["chinese"], 5000, 9, 1080, "ראש הגשר: החווה הסינית ומעבר לתעלה (15 באוקטובר)", "sinai")
t = card("y25", 10, "בבוקר", 420, "sinai", "tank", "16 באוקטובר: הציר לא נפתח; שני גדודים בלבד בגדה המערבית",
         'כאשר האיר הבוקר של יום 16 באוקטובר הציר לא נפתח ובצד המערבי של התעלה היו שני גדודים ישראליים בלבד', [mk("chinese", "fight")], prec="approximate")
t = card("y26", 10, "בלילה", 1320, "sinai", "tank", "גדוד 890 פותח את הציר בחווה הסינית; גשר הדוברות מונח",
         'בלילה נשלח גדוד 890 לפתוח את הציר בחווה הסינית, הגדוד ספג אבדות כבדות אולם הצליח לפתוח את הציר וגשר הדוברות הונח על התעלה', [mk("chinese", "fight")], prec="approximate")
ITEMS += [arrow([[30.45, 32.55], P["chinese"], [30.45, 32.28]], t, t + 16, "גדוד 890 (סכמטי)", BLUE, "sinai", "tank"), boom("chinese", t + 8, "sinai", 2)]
t = card("y27", 12, "אחרי 16 באוקטובר", 720, "sinai", "tank", "שטח של 1,600 קמ\"ר בגדה המערבית של התעלה",
         'האוגדות השתלטו על שטח של 1,600 קילומטרים מרובעים בגדה המערבית של תעלת סואץ', [], ["הערך אומר 'בסופו של דבר'; הזמן והצורה: אינם בערך; העיגול סכמטי"], prec="approximate")
circle("west", [30.38, 32.05], 22600, 12, 720, "הגדה המערבית (כ-1,600 קמ\"ר)", "sinai")
t = card("y28", 13, "22 באוקטובר", 720, "sinai", "tank", "כביש קהיר–סואץ נותק; הארמייה השלישית מכותרת",
         'ב-22 באוקטובר ניתק צה"ל את כביש קהיר–סואץ, והארמייה המצרית השלישית, שנמצאה ממזרח לתעלת סואץ, כותרה בכיתור כפול על ידי שתיים מן האוגדות ונותרה ללא מקורות אספקה', [mk("suez", "fight")], ["הכיתור: נקודת סואץ סכמטית"], prec="approximate")
ITEMS.append(boom("suez", t, "sinai", 2))
t = card("y29", 15, "21–22 באוקטובר", 1380, "golan", "para", "גולני כובשת את מוצב החרמון (12 שעות)",
         'בקרב קשה ורב נפגעים, שנערך ב-21–22 באוקטובר ונמשך 12 שעות, כבש כוח של חטיבת גולני את מוצב החרמון', [mk("hermon", "fight")], prec="approximate", end=1440 + 360)
ITEMS.append(boom("hermon", t + 6, "golan", 2)); circle("hermon", P["hermon"], 3500, 15, 1400, "מוצב החרמון (21–22 באוקטובר)", "golan")
t = card("y30", 18, "24 באוקטובר", 600, "sinai", "tank", "גדוד הנדסה 601 מגיע לק\"מ ה-101 מקהיר",
         'בתאריך 24 באוקטובר, כוח הנדסה מגדוד 601 הגיע לאזור הק"מ ה-101 מקהיר במצרים, והיו הכוח הראשון שהגיע למקום עמוק בתוך מצרים', [mk("km101", "fight")], ["הנקודה: חישוב שלנו (הק\"מ ה-101 בדרך קהיר–סואץ)"], prec="approximate")
ITEMS.append(arrow([[30.2, 32.4], P["km101"]], t, t + 14, "כוח הנדסה, גדוד 601 (סכמטי)", BLUE, "sinai", "tank"))
card("y31", 18, "24 באוקטובר", 720, "all", "tank", "הפסקת האש נכנסת לתוקף בשתי החזיתות", 'הפסקת האש נכנסה בשתי החזיתות לתוקף ב-24 באוקטובר', [], ["החלטה מדינית: אין לה מיקום על המפה"], prec="approximate")
card("y32", 18, "24 באוקטובר", 780, "all", "ship", "מסר חריף מברז'נייב לנשיא ארצות הברית",
     'הלחץ הגיע לשיאו ב-24 באוקטובר במסר חריף מברז\'נייב לנשיא ארצות הברית', [], ["אירוע מדיני: אין לו מיקום על המפה"], prec="approximate")
# (the closing casualty line was cut: the owner 10-23, movement only)

import war_data_1973_yk_more as MORE
MORE.add(globals())

def build_event_file():
    if _LAST[0]:
        OWN[_LAST[0]] = (_LAST[1], len(ITEMS))
    gone = {i for c in DROPPED if c in OWN for i in range(*OWN[c])}
    ITEMS[:] = [it for i, it in enumerate(ITEMS) if i not in gone]
    _LAST[0] = None
    end = max(T0(18) + DUR, max(a["s"] for a in ACTS) + 6)
    CARDS.sort(key=lambda c: c["start_min"])
    acts = sorted(ACTS, key=lambda a: a["s"])
    for i in range(len(acts) - 1):
        acts[i]["e"] = acts[i + 1]["s"]
    acts[-1]["e"] = end
    days = [{"n": n + 1, "label": lab, "T0": T0(n), "min0": n * 1440, "dur": DUR, "date": d} for n, (d, lab) in enumerate(DAYS)]
    chapters = [{"name": c["name"], "sub": c["sub"], "T0": T0(c["a"]), "from": c["a"] + 1, "to": c["b"] + 1} for c in CHAPTERS]
    ev = {"source": {"title": "מלחמת יום הכיפורים", "url": "https://he.wikipedia.org/wiki/%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%99%D7%95%D7%9D_%D7%94%D7%9B%D7%99%D7%A4%D7%95%D7%A8%D7%99%D7%9D", "revid": REV, "revision_time": "2026-10",
                     "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
                     "permalink": f"https://he.wikipedia.org/w/index.php?title=%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%99%D7%95%D7%9D_%D7%94%D7%9B%D7%99%D7%A4%D7%95%D7%A8%D7%99%D7%9D&oldid={REV}",
                     "authors_url": "https://he.wikipedia.org/w/index.php?title=%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%99%D7%95%D7%9D_%D7%94%D7%9B%D7%99%D7%A4%D7%95%D7%A8%D7%99%D7%9D&action=history", "articles": {"מלחמת יום הכיפורים": {"revid": REV}, **MORE.articles({c["src"]["k"] for c in CARDS if c.get("src")} | {i["sk"] for i in ITEMS if i.get("sk")})}},
          "places": PLACES, "areas": {}, "events": CARDS, "time_range": [0, len(DAYS) * 1440], "area_filter": AREAS, "views": VIEWS, "still_views": VIEWS, "view": VIEWS["all"],
          "cards_title": "אירועי המלחמה (סיכום שלנו, מצוטט מהמקורות)", "casualties": [],
          "scene": {"dur": end, "view0": VIEWS["all"], "acts": acts, "log": sorted(LOG, key=lambda l: l["t"]), "sfx": war_sfx.auto(ITEMS) + SFX, "items": ITEMS, "bases": [], "areas": [],
                    "show_places": [k for k in PLACES if k not in MORE.HIDDEN], "icons": True, "control": {"label": 'עיגול שליטה: מקום שהערך מזכיר שכוחות צה"ל נכנסו אליו (סכמטי)', "grow": GROW}},
          "whole": {"date0": DAYS[0][0], "days": days, "chapters": chapters, "skip_idle": True, "slow_cam": True, "start_T": at(0, 835) - 1.5, "alt": MORE.alt(at(0, 835) - 1.5, at(0, 1440), VIEWS)}}
    for it in ev["scene"]["items"]:                       # a unit marker lives to the end of its CHAPTER (the front stays for days), never into the next one
        if it["type"] in ("arrow", "walk", "fly", "shell") and "u" not in it:
            d = int((it["t0"] if "t0" in it else it["legs"][0]["t0"]) // (DUR + GAP)); it["u"] = CH_END(d)
    return ev

def _norm(s):
    """other sources (PDF text, article extracts): compared without whitespace, bidi marks and niqqud (the PDF text extraction scrambles spacing and punctuation next to numerals)"""
    import unicodedata
    return "".join(c for c in s if unicodedata.category(c) not in ("Cf", "Zs", "Cc") and not c.isspace() and not "\u0591" <= c <= "\u05c7")

def check_quotes(ev, article):
    txt = Path(article).read_text(encoding="utf-8"); bad = 0; cache = {}
    for c in ev["events"]:
        k = (c.get("src") or {}).get("k")
        for seg in [s.strip() for s in c["quote"].replace("[...]", "\n").split("\n") if s.strip()]:
            if not k:
                if seg not in txt:
                    bad += 1; print("QUOTE NOT IN ARTICLE:", c["id"], seg[:70])
            else:
                if k not in cache:
                    f = MORE.SRC_DIR / MORE.SRC_FILES[k]
                    cache[k] = [_norm(x) for x in f.read_text(encoding="utf-8").split("\f")] if k == "idf" else [_norm(f.read_text(encoding="utf-8"))]
                if not any(_norm(seg) in pg for pg in cache[k]):
                    bad += 1; print("QUOTE NOT IN", k, ":", c["id"], seg[:70])
                if k == "idf":
                    pgs = [i + 1 for i, pg in enumerate(cache[k]) if _norm(seg) in pg]
                    if pgs and c["src"].get("p") not in pgs:
                        bad += 1; print("PAGE MISMATCH", c["id"], c["src"].get("p"), pgs)
    for it in ev["scene"]["items"]:                  # item-level quotes (stronghold markers): asserted against their own source
        if it.get("q"):
            k = it["sk"]
            if k not in cache:
                f = MORE.SRC_DIR / MORE.SRC_FILES[k]; cache[k] = [_norm(f.read_text(encoding="utf-8"))]
            if not any(_norm(it["q"]) in pg for pg in cache[k]):
                bad += 1; print("ITEM QUOTE NOT IN", k, ":", it["label"], it["q"][:60])
    return bad

if __name__ == "__main__":
    ev = build_event_file()
    if "--check-quotes" in sys.argv:
        sys.exit(1 if check_quotes(ev, sys.argv[sys.argv.index("--check-quotes") + 1]) else 0)
    (DATA / "1973-10-06-events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(CARDS)} cards, {len(ITEMS)} scene items, {len(GROW)} control circles, dur {ev['scene']['dur']}")
