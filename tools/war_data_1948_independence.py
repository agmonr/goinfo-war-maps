#!/usr/bin/env python3
"""Authors the War of Independence (1948-49) for /war/ as ONE scene on the shared engine: writes war/data/1948-05-15-events.json. Episode 1 here: the invasion, 15 May - 11 June 1948.

Rules (war-maps-checklist.md; the owner 10-23/24): the war starts with the first move of the INVADING side (15 May 1948) - no pre-war / civil-war background, no talks, no after cards; moves and battles only,
1-2 cards per battle; named formations as unit symbols with their own quotes; every quote segment is asserted by --check-quotes to be a substring of its pinned source (he.wikipedia, CC BY-SA 4.0,
plain-text extracts kept in SRC_DIR, not in git); schematic positions are labelled so; the sound cues come from the scene (war_sfx.auto); no scale overlay.
Run: python3 tools/war_data_1948_independence.py [--check-quotes]"""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import war_sfx
import war_landcheck as LC
LM = LC.load_mask()
S = lambda p: LC.snap(LM, p)      # a ground vertex that fell on water goes to the nearest land (checklist 17)

DATA = Path(__file__).resolve().parent.parent / "war" / "data"
SRC_DIR = Path("")
WIKI = {"main": ("מלחמת העצמאות", 44066102), "nirim": ("קרב נירים", 43938574), "tlvbomb": ("הפצצת תל אביב במלחמת העצמאות", 43856594), "jordanvalley": ("קרב עמק הירדן", 42502039),
        "gesher": ("הקרב על קיבוץ גשר", 43962754), "notredame": ("קרב נוטרדאם", 43793988), "yadmord": ("קרב יד מרדכי", 43021725), "ramatrachel": ("קרב רמת רחל", 43313297),
        "bn1": ("מבצע בן נון א'", 43584042), "bn2": ("מבצע בן נון ב'", 41706502), "pleshet": ("מבצע פלשת", 43705651), "jenin": ("הקרב על ג'נין (1948)", 42647990),
        "nitzanim": ("הקרב על ניצנים", 43555771), "brig8": ("חטיבה 8", 44096118), "harel": ("חטיבת הראל", 43805226), "tendays": ("קרבות עשרת הימים", 43165198), "danny": ("מבצע דני", 43258522), "dekel": ("מבצע דקל", 42975037), "brosh": ("מבצע ברוש", 42369809), "deathinv": ("מבצע מוות לפולש", 43792843),
        "kedem": ("מבצע קדם", 44072612), "anfar": ("מבצע אנ-פאר", 44095370), "galon": ("הקרב על גלאון", 42168150), "yoav": ("מבצע יואב", 44026592), "farouk": ("טיבוע אל-אמיר פארוק", 44100087),
        "hiram": ("מבצע חירם", 43173628), "horev": ("מבצע חורב", 44090064), "rafah49": ("קרב רפיח (1949)", 42370154), "uvda": ("מבצע עובדה", 43239855), "yitzuv": ("מבצע ייצוב", 40418292), "yoram": ("מבצע יורם", 41706509), "latrun": ("קרבות לטרון", 43792411)}
import datetime as _dt
EPISODES = [("1948-05-15", "1948-06-11", "הפלישה", "15 במאי – 11 ביוני 1948"), ("1948-07-08", "1948-07-19", "קרבות עשרת הימים", "8–19 ביולי 1948"), ("1948-10-15", "1948-10-22", "מבצע יואב", "15–22 באוקטובר 1948"),
            ("1948-10-28", "1948-10-31", "מבצע חירם", "28–31 באוקטובר 1948"), ("1948-12-22", "1949-01-08", "מבצע חורב", "22 בדצמבר 1948 – 8 בינואר 1949"), ("1949-03-02", "1949-03-10", "מבצע עובדה", "2–10 במרץ 1949")]
DAYS, EP_OF = [], []        # (date, label), episode index per day
for _e, (a, b, _n, _s) in enumerate(EPISODES):
    d0, d1 = _dt.date.fromisoformat(a), _dt.date.fromisoformat(b)
    while d0 <= d1:
        DAYS.append((d0.isoformat(), f"{d0.day}.{d0.month}")); EP_OF.append(_e); d0 += _dt.timedelta(days=1)
DUR, GAP, EGAP = 100, 6, 30    # 100 s of play per war day (a war of 70+ fighting days: the checklist exception "over 20 days >= 100 s"); 6 s between days, 30 s between episodes (the truce / pause)
_T0 = []
for _i in range(len(DAYS)):
    _T0.append(0 if _i == 0 else _T0[-1] + DUR + (EGAP if EP_OF[_i] != EP_OF[_i - 1] else GAP))
T0 = lambda d: _T0[d]
at = lambda day, minute: round(T0(day) + minute / 1440 * DUR, 2)
D = lambda date: [i for i, (d, _) in enumerate(DAYS) if d.endswith(date)][0]       # "05-18" -> day index (month-day is unique in the war's episodes)
BLUE, RED = "#1d5ea8", "#b3261e"
VIEWS = {"all": [[30.9, 33.9], [33.6, 36.3]], "south": [[31.1, 34.1], [31.95, 34.9]], "jer": [[31.6, 34.8], [31.95, 35.35]], "north": [[32.3, 35.0], [33.15, 35.8]], "eilat": [[29.4, 34.7], [29.8, 35.2]], "negev": [[30.9, 34.3], [31.7, 35.1]], "air": [[31.2, 34.0], [32.3, 34.95]]}
AREAS = [{"id": "all", "name": "הכל"}, {"id": "south", "name": "החזית הדרומית (מצרים)"}, {"id": "jer", "name": "ירושלים ולטרון (הלגיון)"}, {"id": "north", "name": "הצפון והעמק (סוריה, עיראק)"}]
CARDS, ITEMS, ACTS, LOG, GROW = [], [], [], [], []
PLACES = {}


def pl(name, lat, lon, side, basis=None, prec="exact", article=None):
    return {"name": name, "lat": lat, "lon": lon, "precision": prec, "side": side,
            "basis": basis if prec != "exact" else f'נקודת המקום בערך ״{article}״ בוויקיפדיה העברית'}


def place(pid, name, lat, lon, side, article=None, basis=None):
    PLACES[pid] = pl(name, lat, lon, side, basis, "approximate", None) if basis else pl(name, lat, lon, side, article=article)


EXT = {"palmach10": ("אתר הפלמ״ח: הגדוד העשירי – ״המשוריין״ (חטיבת הראל)", "https://palmach.org.il/history/database/?itemId=6203")}      # a non-Wikipedia source: the Palmach archive (R47 link goes to the page; the text is kept in the sources dir for the quote check)


def src(k):
    if k in EXT: return {"k": k, "u": EXT[k][1], "t": EXT[k][0], "s": "אתר הפלמ״ח"}
    t, r = WIKI[k]
    return {"k": k, "u": "https://he.wikipedia.org/w/index.php?title=" + urllib.parse.quote(t.replace(" ", "_")) + f"&oldid={r}", "t": f"ויקיפדיה העברית: {t}", "s": f"ויקיפדיה: {t}"}


def card(cid, k, day, clock, minute, area, unit, title, quote, geom=None, nopos=None, note="", prec="approximate", end=None, view=None):
    CARDS.append({"id": cid, "t": f"{DAYS[day][1]} {clock}", "time_label": f"{DAYS[day][1]} {clock}", "start_min": day * 1440 + minute, "end_min": day * 1440 + (end if end is not None else minute),
                  "time_precision": prec, "unit": unit, "title": title, "quote": quote, "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area, "src": src(k)})
    t = at(day, minute)
    ACTS.append({"s": t, "e": t + 5, "clock": f"{DAYS[day][1]} · {clock} · {title[:26]}", "min": day * 1440 + minute, "view": VIEWS[view or area], "caps": []})
    LOG.append({"t": t + 1, "clock": f"{DAYS[day][1]} · {clock}", "q": quote, "n": title, "area": area, "src": src(k)})
    return t


mk = lambda p, kind, note="": {"type": "marker", "place": p, "kind": kind, "note": note}
arrow = lambda path, t0, t1, label, color, area, trail="tank": {"type": "arrow", "path": path, "t0": t0, "t1": t1, "label": label + " (סכמטי)", "color": color, "hold": 2400, "area": area, "trail": trail}
boom = lambda pos, t, area, big=1: {"type": "boom", "at": pos, "t": t, "dur": 1.3, "big": big, "area": area}
TT = lambda m: at(m // 1440, m % 1440)
M = lambda d, h, m: d * 1440 + h * 60 + m


def unit(label, cls, path, m0, m1, area, q=None, sk=None, trail="tank"):
    it = {"type": "walk", "label": label + " (סכמטי)", "cls": cls, "sym": "▣", "area": area, "trail": trail, "legs": [{"t0": TT(m0), "t1": TT(m1), "path": path}]}
    if q: it["q"], it["sk"] = q, sk
    return it


def tag(m, pos, label, q, sk, dur=10, area="all"):
    return {"type": "mark", "at": pos, "t0": TT(m), "t1": TT(m) + dur, "label": label, "area": area, "q": q, "sk": sk, "s": f"ויקיפדיה: {WIKI[sk][0]}"}


def fly(label, side, area, a, b, m0, m1, back=True):
    legs = [{"t0": TT(m0), "t1": TT(m1), "path": [a, b]}] + ([{"t0": TT(m1 + 3), "t1": TT(m1 + 3 + (m1 - m0)), "path": [b, a]}] if back else [])
    return {"type": "fly", "side": side, "label": label + " (סכמטי)", "area": area, "off": None, "legs": legs}


# ---- places (coordinates = the article's own where it has them; otherwise approximate and said so) ----
place("nirim", "קיבוץ נירים", 31.23895833, 34.33815556, "il", "קרב נירים")
place("yadmord", "קיבוץ יד מרדכי", 31.58861111, 34.55833333, "il", "קרב יד מרדכי")
place("nitzanim", "קיבוץ ניצנים", 31.71659722, 34.6338, "il", "הקרב על ניצנים")
place("ashdod", "גשר עד הלום (אשדוד)", 31.76415, 34.66641389, "ar", "מבצע פלשת")
place("degania", "דגניה", 32.69645556, 35.59123889, "il", "קרב עמק הירדן")
place("jenin", "ג'נין", 32.46111111, 35.3, "ar", "הקרב על ג'נין (1948)")
place("latrun", "מתחם לטרון", 31.83844167, 34.98075278, "ar", "קרבות לטרון")
place("gesher", "קיבוץ גשר (קירוב)", 32.64, 35.56, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
place("notredame", "אכסניית נוטרדאם (קירוב)", 31.7845, 35.2255, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
place("jquarter", "הרובע היהודי (קירוב)", 31.7765, 35.2300, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
place("ramatrachel", "רמת רחל (קירוב)", 31.7425, 35.2145, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
place("sdedov", "שדה דב (קירוב)", 32.115, 34.78, "il", basis="הערך מזכיר את שדה דב ללא קואורדינטות; הנקודה היא קירוב שלנו")
place("rafah", "חבל רפיח (קירוב)", 31.30, 34.22, "ar", basis="הערך אינו מציין קואורדינטות; נקודת הכניסה המצרית היא קירוב שלנו")
place("zemah", "צמח (קירוב)", 32.71, 35.58, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
SHOW = []     # no permanent labels: the markers carry them while their card is on


# ================= episode 1: the invasion, 15 May - 11 June 1948 =================
d15 = D("05-15")
t = card("a1", "main", d15, "הפלישה", 0, "all", "tank", "15 במאי: צבאות סוריה, עיראק, עבר הירדן ומצרים פולשים לארץ, ובכך מתחיל השלב השני של המלחמה",
         'למחרת פלשו לתחומי הארץ הצבאות הסדירים של מספר מדינות ערביות (סוריה, עיראק, עבר הירדן ומצרים) בסיוע כוחות צבא קטנים יחסית מלבנון וערב הסעודית, ובכך החל השלב השני של מלחמת העצמאות',
         nopos=["נתיבי הפלישה: סכמטיים, ברמת הגזרה; הערך אינו מציין נקודות חצייה"])
ITEMS += [arrow([[31.28, 34.18], [31.35, 34.36], [31.58, 34.55]], t, t + 20, "חיל המשלוח המצרי נע צפונה", RED, "south"), arrow([[32.80, 35.95], [32.71, 35.62]], t + 1, t + 21, "הצבא הסורי לעמק הירדן", RED, "north"),
          arrow([[32.45, 35.60], [32.50, 35.30]], t + 2, t + 22, "חיל המשלוח העיראקי", RED, "north"), arrow([[31.85, 35.55], [31.80, 35.25]], t + 3, t + 23, "הלגיון הערבי לירושלים", RED, "jer")]
ITEMS += [unit("חיל המשלוח המצרי", "syr", [[31.28, 34.18], S([31.42, 34.30])], M(d15, 3, 0), M(d15, 8, 0), "south", 'פלשו לתחומי הארץ הצבאות הסדירים של מספר מדינות ערביות (סוריה, עיראק, עבר הירדן ומצרים)', "main"),
          unit("הצבא הסורי", "syr", [[32.85, 35.95], [32.80, 35.78]], M(d15, 3, 0), M(d15, 9, 0), "north"), unit("חיל המשלוח העיראקי", "syr", [[32.50, 35.62], [32.52, 35.45]], M(d15, 4, 0), M(d15, 10, 0), "north"),
          unit("הלגיון הערבי", "syr", [[31.86, 35.58], [31.84, 35.40]], M(d15, 4, 0), M(d15, 10, 0), "jer")]
t = card("a2", "nirim", d15, "05:30", 330, "south", "tank", "15 במאי 05:30: טור ממונע מצרי תוקף את קיבוץ נירים ונהדף",
         'קרב נירים התחולל בבוקר ה־15 במאי 1948, בין כוחות חיל המשלוח המצרי שפלש לשטחה הריבוני של מדינת ישראל ארבע עשרה שעות לאחר ההכרזה על הקמתה לבין חברי קיבוץ נירים [...] ב־05:30 התקרב למקום טור ממונע, שכלל ארבע שריוניות, 20  נושאי ברן ומשאיות נושאות חיילים',
         geom=[mk("nirim", "fight")], prec="approximate")
ITEMS += [boom([31.2390, 34.3382], t, "south", 1), arrow([[31.20, 34.25], [31.2390, 34.3382]], t - 3, t + 3, "הטור הממונע המצרי", RED, "south")]
t = card("a3", "tlvbomb", d15, "שעות אחדות אחרי ההכרזה", 420, "air", "mig", "15 במאי: ההפצצה המצרית הראשונה על תל אביב; מטרתה העיקרית שדה דב",
         'שיטת התקיפה המצרית הייתה בדרך כלל גיחה של שני מטוסי הפצצה, בדרך כלל מטוסי דקוטה, שלוו במטוס קרב אחד או שניים מדגם ספיטפייר. ההפצצה הראשונה הונחתה ב-15 במאי, שעות אחדות לאחר תום המנדט והכרזת המדינה, כאשר מטרתו המרכזית הייתה פגיעה בשדה דב',
         geom=[mk("sdedov", "bomb")], prec="approximate", nopos=["נתיב הטיסה ושעת הגיחה המדויקת: אינם בערך; הציור סכמטי"])
ITEMS += [fly("דקוטה מצרית (מפציץ)", "syr", "air", [31.50, 33.70], [32.115, 34.78], M(d15, 6, 40), M(d15, 7, 0)), fly("דקוטה מצרית (מפציץ)", "syr", "air", [31.46, 33.70], [32.10, 34.76], M(d15, 6, 41), M(d15, 7, 1)),
          fly("ספיטפייר מצרי (מלווה)", "syr", "air", [31.55, 33.70], [32.12, 34.80], M(d15, 6, 42), M(d15, 7, 2)), boom([32.115, 34.78], TT(M(d15, 7, 1)), "air", 2)]
# ---- the Jordan valley: Syrians (15-18 May Zemah falls, 20 May Degania) ----
d18, d20 = D("05-18"), D("05-20")
t = card("a4", "jordanvalley", d18, "18 במאי", 600, "north", "tank", "18 במאי: הסורים כובשים את צמח, שער הגולן ומסדה בעמק הירדן",
         'לאחר שהסורים כבשו את צמח, שער הגולן ומסדה', geom=[mk("zemah", "fight")], nopos=["שעת הכיבוש: אינה בערך"], prec="approximate")
ITEMS += [arrow([[32.78, 35.85], [32.71, 35.58]], t - 4, t + 8, "הצבא הסורי תוקף את צמח", RED, "north"), boom([32.71, 35.58], t + 6, "north", 1)]
t = card("a5", "jordanvalley", d20, "20 במאי", 600, "north", "tank", "20 במאי: הקרב על הדגניות - הסורים תוקפים את דגניה א׳ וב׳ ונהדפים",
         'הם תקפו את דגניה א\' ודגניה ב\' ונהדפו. בהמשך, נסוגו הסורים לעמדות המוצא שלהם סמוך לקו הגבול הבינלאומי', geom=[mk("degania", "fight")], prec="approximate", nopos=["שעת הקרב: אינה בציטוט"])
ITEMS += [arrow([[32.70, 35.70], [32.6965, 35.5912]], t - 3, t + 6, "הצבא הסורי תוקף את דגניה", RED, "north"), boom([32.6965, 35.5912], t + 5, "north", 2), arrow([[32.6965, 35.5912], [32.78, 35.88]], t + 8, t + 16, "הסורים נסוגים", RED, "north")]
d15g = D("05-15")
t = card("a6", "gesher", d15g, "15–22 במאי", 800, "north", "tank", "15–22 במאי: חיל המשלוח העיראקי תוקף את קיבוץ גשר",
         'והשני, לאחר הכרזת המדינה - התקפה של חיל המשלוח העיראקי (15 במאי 1948 − 22 במאי 1948)', geom=[mk("gesher", "fight")], end=7 * 1440, prec="approximate", nopos=["מקום גשר: אין קואורדינטות בערך; קירוב שלנו"])
ITEMS += [arrow([[32.58, 35.72], [32.64, 35.56]], t, t + 14, "חיל המשלוח העיראקי תוקף את גשר", RED, "north"), boom([32.64, 35.56], t + 12, "north", 1)]
# ---- Jerusalem: Notre Dame (15-24 May), Old City (28 May) ----
t = card("a7", "notredame", d15, "15–24 במאי", 900, "jer", "tank", "15–24 במאי: קרב נוטרדאם - נכשלים ניסיונות הלגיון הירדני לפרוץ לירושלים המערבית",
         'קרב נוטרדאם בירושלים נערך ב-15 במאי 1948 - 24 במאי 1948. זה היה אחד הקרבות המכריעים במערכה על ירושלים במלחמת העצמאות שבסופו נכשלו ניסיונות הלגיון הירדני לפרוץ לירושלים המערבית',
         geom=[mk("notredame", "fight")], end=9 * 1440, prec="approximate", nopos=["מקום האכסניה: קירוב שלנו"])
ITEMS += [arrow([[31.78, 35.36], [31.7845, 35.2255]], t, t + 14, "הלגיון הערבי נבלם ליד נוטרדאם", RED, "jer"), boom([31.7845, 35.2255], t + 10, "jer", 1)]
d28 = D("05-28")
t = card("a8", "main", d28, "28 במאי", 600, "jer", "tank", "28 במאי: הלגיון הערבי כובש את הרובע היהודי בעיר העתיקה",
         'ב-28 במאי כבש כוח זה את הרובע היהודי', geom=[mk("jquarter", "fight")], prec="approximate", nopos=["שעת הכיבוש: אינה בציטוט; מיקום הרובע: קירוב שלנו"])
ITEMS += [arrow([[31.78, 35.25], [31.7765, 35.2300]], t - 3, t + 6, "הלגיון הערבי נכנס לרובע", RED, "jer"), boom([31.7765, 35.2300], t + 5, "jer", 2)]
# ---- Egyptians: Yad Mordechai (18-23 May), Ashdod (29.5-3.6), Nitzanim (7 June) ----
d18, d23 = D("05-18"), D("05-23")
t = card("a9", "yadmord", d18, "18–23 במאי", 360, "south", "tank", "18–23 במאי: קרב יד מרדכי - 150 לוחמים בולמים שישה ימים חטיבה מצרית סדירה; הקיבוץ נעזב",
         'קרב יד מרדכי היה קרב בלימה שנערך במלחמת העצמאות בניסיון לעצור את הצבא המצרי הסדיר שנע צפונה לעבר תל אביב. במשך שישה ימים, החל מ-18 במאי ועד ל-23 במאי 1948, נערכו ניסיונות של חטיבה מצרית סדירה לכבוש את קיבוץ יד מרדכי, עליו הגנו 150 לוחמים עם 75 כלי נשק קלים',
         geom=[mk("yadmord", "fight")], end=5 * 1440, prec="approximate")
ITEMS += [arrow([[31.45, 34.45], [31.5886, 34.5583]], t, t + 22, "חטיבה מצרית תוקפת את יד מרדכי", RED, "south"), boom([31.5886, 34.5583], t + 10, "south", 2), boom([31.5886, 34.5583], t + 60, "south", 1)]
d29 = D("05-29")
t = card("a10", "pleshet", d29, "29 במאי – 3 ביוני", 600, "south", "tank", "29 במאי – 3 ביוני: הטור המצרי (500 כלי רכב) נבלם בגשר אשדוד - מבצע פלשת של גבעתי והנגב, והגיחה הראשונה של טייסת 101",
         'ב-29 במאי 1948, שבועיים לאחר פלישת צבאות ערב, החל טור ממונע של הצבא המצרי לנוע ממג\'דל צפונה [...] ביום בו נעצר לפני הגשר, הטור המצרי הותקף על ידי רביעיית מטוסי טייסת 101 בגיחתה הראשונה אי פעם',
         geom=[mk("ashdod", "fight")], end=5 * 1440, prec="approximate", nopos=["שעות הקרב: אינן בערך"])
ITEMS += [unit("הטור הממונע המצרי (מעל 500 כלי רכב)", "syr", [[31.63, 34.60], [31.76, 34.665]], M(d29, 6, 0), M(d29, 14, 0), "south", 'יותר מ-500 כלי רכב - מכוניות משא, זחלים, טנקים בינוניים ותותחים מכל הסוגים עברו על הכביש הראשי ממזרח לניצנים ופניהם לכיוון איסדוד', "pleshet"),
          fly("מטוס טייסת 101 (גיחה ראשונה)", "iaf", "south", [32.0, 34.75], [31.76, 34.665], M(d29, 12, 0), M(d29, 12, 10)), boom([31.76, 34.665], TT(M(d29, 12, 10)), "south", 2)]
d1j = D("06-01")
t = card("a11", "jenin", d1j, "1–4 ביוני", 1320, "north", "tank", "1–4 ביוני: מבצע יצחק - צה״ל תוקף את חיל המשלוח העיראקי בג׳נין, משתלט על יעדים וכמעט כולם נסוגים אחרי התקפת נגד",
         'הקרב על ג\'נין, שנקרא גם מבצע יצחק, נערך במסגרת הלחימה בחזית הצפון במלחמת העצמאות [...] תקפו כוחות של צה"ל את כוחות חיל המשלוח העיראקי', geom=[mk("jenin", "fight")], end=3 * 1440 - 1320, prec="approximate")
ITEMS += [arrow([[32.55, 35.25], [32.4611, 35.30]], t, t + 14, "כרמלי וגולני תוקפות בג׳נין", BLUE, "north"), boom([32.4611, 35.30], t + 12, "north", 1), arrow([[32.45, 35.40], [32.50, 35.22]], t + 20, t + 32, "התקפת נגד עיראקית", RED, "north"),
          boom([32.50, 35.24], t + 30, "north", 1)]
d7 = D("06-07")
t = card("a12", "nitzanim", d7, "7 ביוני", 420, "south", "tank", "7 ביוני: ניצנים נכבשת בידי חיל המשלוח המצרי אחרי קרב של עשר שעות",
         'הקרב על ניצנים הוא קרב שנערך במלחמת העצמאות, והסתיים בכיבוש קיבוץ ניצנים על ידי חיל המשלוח המצרי ב-7 ביוני 1948', geom=[mk("nitzanim", "fight")], prec="approximate")
ITEMS += [arrow([[31.66, 34.58], [31.7166, 34.6338]], t, t + 12, "הצבא המצרי תוקף את ניצנים", RED, "south"), boom([31.7166, 34.6338], t + 11, "south", 2)]
# ---- Latrun: Ben-Nun A (25 May), Ben-Nun B (30-31 May), Yoram (8-9 June) - the Arab Legion holds ----
d25, d30, d8 = D("05-25"), D("05-30"), D("06-08")
t = card("a13", "bn1", d25, "25 במאי", 780, "jer", "tank", "25 במאי: בן נון א׳ - הניסיון הראשון לכבוש את לטרון, בהשתתפות חטיבה 7 החדשה, נכשל",
         'מטרת המבצע, שנערך ב-25 במאי 1948, הייתה השתלטות על עמדות הלגיון הערבי באזור לטרון - שער הגיא [...] היה זה המבצע הראשון בו השתתפה חטיבה 7 של הצבא הישראלי', geom=[mk("latrun", "fight")], prec="approximate", nopos=["שעת ההתקפה: אינה בציטוט"])
ITEMS += [unit("חטיבה 7 (בן נון א׳)", "iaf", [[31.86, 34.88], [31.838, 34.98]], M(d25, 12, 30), M(d25, 14, 0), "jer", "היה זה המבצע הראשון בו השתתפה חטיבה 7 של הצבא הישראלי", "bn1"), boom([31.838, 34.98], TT(M(d25, 14, 0)), "jer", 2)]
t = card("a14", "bn2", d30, "ליל 30–31 במאי", 1380, "jer", "tank", "30–31 במאי: בן נון ב׳ - חטיבה 7 וגבעתי תוקפות את לטרון משני צדדיה, ונכשלות",
         'המבצע, שנערך בליל 30–31 במאי 1948, היה הניסיון הכושל השני לכבוש את מתחם לטרון [...] ניסו כוחות מחטיבה 7 ומחטיבת גבעתי לתקוף במקביל את החלק המזרחי ואת החלק המערבי של רכס לטרון', geom=[mk("latrun", "fight")], prec="approximate")
ITEMS += [arrow([[31.86, 34.88], [31.838, 34.98]], t, t + 10, "חטיבה 7 תוקפת", BLUE, "jer"), arrow([[31.80, 34.86], [31.832, 34.97]], t + 1, t + 11, "גבעתי תוקפת", BLUE, "jer"), boom([31.838, 34.98], t + 10, "jer", 2)]
t = card("a15", "yoram", d8, "ליל 8–9 ביוני", 1380, "jer", "tank", "8–9 ביוני: מבצע יורם - הניסיון השלישי לכבוש את לטרון, הקרוב ביותר להצלחה, נכשל גם הוא",
         'הוא נערך בלילה שבין 8 ל-9 ביוני 1948, לקראת כניסת ההפוגה הראשונה. כמו כל קודמיו, וכמו אלה שאחריו, ניסיון זה נכשל אף הוא', geom=[mk("latrun", "fight")], prec="approximate")
ITEMS += [arrow([[31.86, 34.90], [31.838, 34.985]], t, t + 10, "חטיבת הראל ופלמ״ח תוקפות", BLUE, "jer"), boom([31.838, 34.985], t + 10, "jer", 2)]
d11 = D("06-11")


# ================= episode 2: the Ten Days, 8-18 July 1948 =================
place("lydda", "לוד (קירוב)", 31.952, 34.895, "ar", basis="הערך אינו מציין קואורדינטות; מרכז העיר (קירוב שלנו)")
place("ramle", "רמלה (קירוב)", 31.927, 34.866, "ar", basis="הערך אינו מציין קואורדינטות; מרכז העיר (קירוב שלנו)")
place("dekel", "אזור מבצע דקל", 32.78150278, 35.20173889, "il", "מבצע דקל")
place("mishmar", "משמר הירדן (קירוב)", 33.0, 35.62, "il", basis="הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו")
place("deathinv", "אזור מבצע מוות לפולש", 31.64373611, 34.74451944, "ar", "מבצע מוות לפולש")
place("kedem", "העיר העתיקה (מבצע קדם)", 31.77810556, 35.2256, "ar", "מבצע קדם")
place("anfar", "אזור מבצע אנ-פאר (קירוב)", 31.66, 34.72, "ar", basis="הערך אינו מציין קואורדינטות; קירוב שלנו")
d8, d9, d10, d14, d16, d17 = D("07-08"), D("07-09"), D("07-10"), D("07-14"), D("07-16"), D("07-17")
t = card("b1", "anfar", d8, "8–11 ביולי", 540, "south", "tank", "8–11 ביולי: מבצע אנ-פאר - גבעתי והנגב מול הצבא המצרי; התקפות נגד עזות, הקו כמעט לא משתנה",
         'מבצע אנ-פאר (אנטי פארוק) היה מבצע צבאי של חטיבת גבעתי וחטיבת הנגב בחזית הדרום במלחמת העצמאות. המבצע היה חלק מקרבות עשרת הימים, ונערך בין 8 ל-11 ביולי 1948. המצרים הגיבו בהתקפות נגד עזות',
         geom=[mk("anfar", "fight")], end=3 * 1440, prec="approximate", nopos=["מקום המבצע: אין קואורדינטות בערך; קירוב שלנו"])
ITEMS += [arrow([S([31.76, 34.60]), [31.66, 34.72]], t, t + 12, "גבעתי והנגב תוקפות", BLUE, "south"), arrow([[31.60, 34.80], [31.68, 34.68]], t + 14, t + 24, "התקפת נגד מצרית", RED, "south"), boom([31.66, 34.72], t + 12, "south", 1)]
t = card("b2", "danny", d10, "10–18 ביולי", 480, "jer", "tank", "10–18 ביולי: מבצע דני - המבצע האוגדתי הראשון; לוד ורמלה נכבשות, לטרון ורמאללה לא",
         'מבצע דני היה המבצע העיקרי של צה"ל במהלך קרבות עשרת הימים במלחמת העצמאות, והתקיים מ-10 ביולי עד ל-18 ביולי 1948. בתחילה כונה המבצע "מבצע לרל"ר", ראשי תיבות של ארבעת היעדים המרכזיים שנקבעו לו: לוד, רמלה, לטרון ורמאללה. בפועל הושגו שני היעדים הראשונים בלבד',
         geom=[mk("lydda", "fight"), mk("ramle", "fight")], end=8 * 1440, prec="approximate", nopos=["מרכזי הערים: קירוב שלנו"])
ITEMS += [arrow([[32.05, 34.80], [31.952, 34.895]], t, t + 14, "מבצע דני: אל לוד", BLUE, "jer"), arrow([[31.98, 34.80], [31.927, 34.866]], t + 2, t + 16, "מבצע דני: אל רמלה", BLUE, "jer"), boom([31.952, 34.895], t + 14, "jer", 2), boom([31.927, 34.866], t + 16, "jer", 2),
          unit("חטיבות מבצע דני (המבצע האוגדתי הראשון)", "iaf", [[32.05, 34.80], [31.95, 34.88]], M(d10, 8, 0), M(d10, 20, 0), "jer", "היה זה המבצע האוגדתי הראשון שבוצע, ולראשונה הופעלו בו טנקים של צה\"ל", "danny")]
place("lodairport", "נמל התעופה לוד", 32.00944444, 34.87694444, "ar", article="נמל התעופה בן-גוריון")
place("beitjimal", "בית ג'ימאל", 31.725, 34.976389, "ar", article="בית ג'מאל")
t = card("b2a", "brig8", D("07-10"), "10 ביולי", 540, "jer", "tank", "10 ביולי: גדוד 82 - גדוד הטנקים הראשון של חטיבה 8 (״חטיבת הזקן״, יצחק שדה) - כובש את נמל התעופה לוד",
         'ב-10 ביולי 1948, במהלך מבצע דני, כבש הגדוד את נמל התעופה לוד ונטל חלק מרכזי בבלימת מתקפת הנגד של הלגיון הירדני', geom=[mk("lodairport", "fight")], prec="approximate",
         nopos=["שעת הכיבוש: אינה בערך; הציור סכמטי"])
ITEMS += [unit("גדוד 82 (טנקים), חטיבה 8, בפיקוד סא״ל פליקס באטוס (הרמן)", "iaf", [[32.03, 34.80], [32.0094, 34.8769]], M(D("07-10"), 9, 0), M(D("07-10"), 11, 0), "jer", "במהלך מבצע דני, כבש הגדוד את נמל התעופה לוד", "brig8"), boom([32.0094, 34.8769], t + 12, "jer", 2)]
t = card("b2b", "brig8", D("07-11"), "11 ביולי", 600, "jer", "tank", "11 ביולי: גדוד 89 (קומנדו, משה דיין) בולם את השריון הירדני ופורץ ללוד מלווה בשריונית; העיר נכנעת",
         'הצליח גדוד 89 לבלום את השריון הירדני ממזרח לדיר טריף ולמחרת, ב-11 ביולי בעקבות עצירת ההתקדמות של חטיבת יפתח פרץ הגדוד מלווה בשריונית הנמר הנוראי אל תוך העיר לוד והוביל לכניעתה וסיום כיבושה על ידי חטיבת יפתח',
         geom=[mk("lydda", "fight")], prec="approximate", nopos=["נקודת הבלימה (מזרחית לדיר טריף): אינה בערך; הציור סכמטי"])
ITEMS += [unit("גדוד 89 (קומנדו, חטיבה 8) עם השריונית ״הנמר הנוראי״", "iaf", [[31.99, 34.84], [31.952, 34.895]], M(D("07-11"), 10, 0), M(D("07-11"), 12, 0), "jer", "פרץ הגדוד מלווה בשריונית הנמר הנוראי אל תוך העיר לוד", "brig8"), boom([31.952, 34.895], t + 14, "jer", 2)]
t = card("h1", "palmach10", D("10-19"), "19 באוקטובר", 540, "jer", "tank", "19 באוקטובר: הגדוד העשירי של הפלמ״ח - ״המשוריין״ (חטיבת הראל) - פועל לראשונה: כיבוש בית ג'ימאל (מבצע ההר)",
         'הגדוד כלל משוריינים, שעליהם הורכבו מכונות הירייה הכבדות ומרגמות שלושה אינץ\', וכן הוסעו בהם אנשי חי"ר [...] הגדוד החל לפעול במבצע "ההר" (19.10.48 – 22.10.48). פעולתו הראשונה הייתה בכיבוש בית ג\'ימאל (19.10.48)',
         geom=[mk("beitjimal", "fight")], prec="approximate", nopos=["נתיב ההתקדמות ושעת הכיבוש: אינם בערך; הציור סכמטי"])
ITEMS += [unit("הגדוד העשירי של הפלמ״ח ״המשוריין״ (חטיבת הראל): משוריינים עם מקלעים כבדים ומרגמות 3 אינץ׳ ועליהם חי״ר", "iaf", [[31.76, 34.93], [31.725, 34.9764]], M(D("10-19"), 9, 0), M(D("10-19"), 12, 0), "jer", "הגדוד החל לפעול במבצע \"ההר\"", "palmach10"), boom([31.725, 34.9764], t + 12, "jer", 2)]
t = card("b3", "dekel", d9, "ליל 8–9 ביולי עד 19 ביולי", 120, "north", "tank", "8–19 ביולי: מבצע דקל - צה״ל כובש את הגליל המערבי ורוב הגליל התחתון, כולל נצרת, מול צבא ההצלה",
         'מבצע דקל היה אחד ממבצעי צה"ל במלחמת העצמאות, אשר נערך בעיקר נגד צבא ההצלה הערבי, כחלק מקרבות עשרת הימים, בין ליל 8–9 ביולי 1948 ועד 19 ביולי 1948 [...] צה"ל כבש שטחים נרחבים בגליל, כך שבסיומו היו בידי ישראל הגליל המערבי כולו, כמו גם רובו של הגליל התחתון, כולל נצרת, שפרעם, ציפורי וכפרים ערביים רבים נוספים',
         geom=[mk("dekel", "fight")], end=10 * 1440, prec="approximate")
ITEMS += [arrow([S([32.85, 35.05]), [32.70, 35.30]], t, t + 20, "מבצע דקל: אל נצרת", BLUE, "north"), arrow([[32.95, 35.20], [32.80, 35.35]], t + 4, t + 24, "מבצע דקל: הגליל התחתון", BLUE, "north"), boom([32.70, 35.30], t + 20, "north", 1)]
t = card("b4", "brosh", d9, "9–18 ביולי", 360, "north", "tank", "9–18 ביולי: מבצע ברוש - ראש הגשר הסורי במשמר הירדן לא נכבש, אך האיום הסורי לבתר את הגליל העליון הוסר",
         'מבצע ברוש היה מבצע צבאי של צה"ל שנערך במלחמת העצמאות בתאריכים 9 ביולי 1948 – 18 ביולי 1948, כחלק מקרבות עשרת הימים, ומטרתו הייתה כיבוש ראש הגשר הסורי במשמר הירדן. לאחר עשרה ימים של קרבות עקובים מדם, לא הושגה מטרת המבצע',
         geom=[mk("mishmar", "fight")], end=9 * 1440, prec="approximate", nopos=["מקום הקרב: קירוב שלנו"])
ITEMS += [arrow([[33.03, 35.45], [33.0, 35.62]], t, t + 18, "חטיבות צה״ל תוקפות את ראש הגשר", BLUE, "north"), arrow([[33.0, 35.75], [33.0, 35.64]], t + 6, t + 20, "הצבא הסורי מחזיק", RED, "north"), boom([33.0, 35.62], t + 18, "north", 1)]
t = card("b5", "galon", d14, "14 ביולי 09:30", 570, "south", "tank", "14 ביולי 09:30: הפגזה מצרית כבדה על קיבוץ גלאון והתקפה - קרב הגנה",
         'הקרב על קיבוץ גלאון במלחמת העצמאות היה קרב הגנה כנגד מתקפה של הצבא המצרי במהלך קרבות עשרת הימים, שנערך ב-14 ביולי 1948 [...] ביום 14 ביולי 1948 בשעה 9:30 החלה הפגזה ארטילרית מצרית כבדה על הקיבוץ',
         prec="approximate", nopos=["מקום הקיבוץ: אין קואורדינטות בערך; לא מסומן"])
t = card("b6", "kedem", d16, "ליל 16–17 ביולי", 1380, "jer", "tank", "16–17 ביולי: מבצע קדם - הניסיון האחרון לכבוש את העיר העתיקה, ערב ההפוגה השנייה, נכשל",
         '"מבצע קדם" היה הניסיון האחרון במלחמת העצמאות לכבוש את העיר העתיקה בירושלים. המבצע יצא לפועל בליל י\' בתמוז ה\'תש"ח (16-17 ביולי 1948), כחלק מקרבות עשרת הימים והסתיים בכישלון',
         geom=[mk("kedem", "fight")], prec="approximate")
ITEMS += [arrow([[31.785, 35.21], [31.7781, 35.2256]], t, t + 8, "מבצע קדם: מהשער החדש", BLUE, "jer"), boom([31.7781, 35.2256], t + 8, "jer", 2)]
t = card("b7", "deathinv", d17, "ליל 17–18 ביולי", 1380, "south", "tank", "17–18 ביולי: מבצע מוות לפולש - חטיבת הנגב תוקפת את משלטי כאוכבה וחוליקאת כדי לפרוץ לנגב; הנגב נשאר מנותק",
         'מבצע מוות לפולש היה מבצע של צה"ל במהלך קרבות עשרת הימים במלחמת העצמאות, שמטרתו לפרוץ את הדרך לנגב לפני כניסתה לתוקף של ההפוגה השנייה. הנגב נותר מנותק גם לאחר המבצע',
         geom=[mk("deathinv", "fight")], prec="approximate")
ITEMS += [arrow([[31.60, 34.70], [31.6437, 34.7445]], t, t + 10, "חטיבת הנגב תוקפת", BLUE, "south"), boom([31.6437, 34.7445], t + 10, "south", 2)]
# ================= episode 3: Operation Yoav (15-22 Oct), the Emir Farouk (22 Oct), Operation Hiram (28-31 Oct) =================
place("beersheva", "באר שבע (קירוב)", 31.2518, 34.7913, "ar", basis="הערך אינו מציין קואורדינטות; מרכז העיר (קירוב שלנו)")
place("fallujah", "כיס פאלוג'ה (קירוב)", 31.64, 34.75, "ar", basis="הערך אינו מציין קואורדינטות; קירוב שלנו (אזור מבצע ״מוות לפולש״)")
place("uppergal", "הגליל העליון (קירוב)", 33.03, 35.42, "il", basis="הערך אינו מציין קואורדינטות; מרכז הגליל העליון (קירוב שלנו)")
d15o, d21o, d22o, d28o = D("10-15"), D("10-21"), D("10-22"), D("10-28")
t = card("c1", "yoav", d15o, "15 באוקטובר", 480, "south", "tank", "15 באוקטובר: מבצע יואב נפתח במהלומת חיל האוויר - פריצת הדרך אל הנגב המנותק",
         'מבצע יואב היה מבצע של צבא הגנה לישראל במלחמת העצמאות שנערך בין 15 ל-22 באוקטובר 1948. מטרתו הייתה פריצת הדרך אל הנגב המנותק, ודחיקת הצבא המצרי ממנו. מבצע זה, שהיה אחד הגדולים באותה מלחמה, החל במהלומה של חיל האוויר',
         geom=[mk("fallujah", "fight")], end=7 * 1440, prec="approximate", nopos=["נתיבי ההתקפה והיעדים: אינם בערך; הציור סכמטי"])
ITEMS += [fly("מטוס חיל האוויר הישראלי", "iaf", "south", [31.95, 34.75], [31.55, 34.60], M(d15o, 8, 0), M(d15o, 8, 12)), fly("מטוס חיל האוויר הישראלי", "iaf", "south", [31.93, 34.73], [31.50, 34.55], M(d15o, 8, 1), M(d15o, 8, 13)),
          boom([31.55, 34.60], TT(M(d15o, 8, 12)), "south", 2), boom([31.50, 34.55], TT(M(d15o, 8, 13)), "south", 2),
          arrow([[31.62, 34.55], [31.50, 34.65], [31.40, 34.75]], t + 8, t + 24, "כוחות צה״ל פורצים לנגב", BLUE, "south")]
t = card("c2", "yoav", d21o, "21 באוקטובר", 600, "negev", "tank", "21 באוקטובר: באר שבע נכבשת; הדרך לנגב נפרצה וכוח מצרי גדול כותר בכיס פאלוג׳ה",
         'נחל המבצע הצלחה: הדרך לנגב נפרצה, השטח שתפס הצבא המצרי הצטמצם במידה ניכרת, וכוח מצרי גדול כותר בכיס פאלוג\'ה. לקראת סוף המבצע כבש צה"ל את באר שבע',
         geom=[mk("beersheva", "fight"), mk("fallujah", "fight")], prec="approximate", nopos=["מרכזי המקומות: קירוב שלנו; שעת הכיבוש אינה בציטוט"])
ITEMS += [arrow([[31.45, 34.60], [31.2518, 34.7913]], t, t + 14, "כיבוש באר שבע", BLUE, "negev"), boom([31.2518, 34.7913], t + 14, "negev", 2), unit("כוח מצרי מכותר בכיס פאלוג׳ה", "syr", [[31.66, 34.72], [31.64, 34.75]], M(d21o, 10, 0), M(d21o, 12, 0), "south", "וכוח מצרי גדול כותר בכיס פאלוג'ה", "yoav")]
t = card("c3", "farouk", d22o, "בצהרי 22 באוקטובר", 720, "south", "ship", "22 באוקטובר: סירות נפץ של חיל הים מטביעות מול חוף עזה את אל-אמיר פארוק, אוניית הדגל של הצי המצרי",
         'האונייה השתתפה בסיוע לחיל המשלוח המצרי בארץ ישראל, וטובעה מול חוף עזה בי"ט תשרי התש"ט - 22 באוקטובר 1948 על ידי סירות נפץ שרכש חיל הים הישראלי מעודפי הצבא האיטלקי ממלחמת העולם השנייה',
         prec="approximate", nopos=["מקום האונייה: ״מול חוף עזה״; הנקודה סכמטית"], view="south")
ITEMS += [{"type": "walk", "label": "אל-אמיר פארוק, אוניית הדגל המצרית (סכמטי)", "cls": "syr", "sym": "▣", "area": "south", "trail": None, "legs": [{"t0": TT(M(d22o, 11, 30)), "t1": TT(M(d22o, 12, 20)), "path": [[31.50, 34.38], [31.50, 34.36]]}]},
          {"type": "walk", "label": "סירות נפץ של חיל הים הישראלי (סכמטי)", "cls": "iaf", "sym": "▣", "area": "south", "trail": None, "legs": [{"t0": TT(M(d22o, 12, 0)), "t1": TT(M(d22o, 12, 20)), "path": [[31.60, 34.30], [31.50, 34.36]]}]},
          boom([31.50, 34.36], TT(M(d22o, 12, 20)), "south", 2)]
t = card("c4", "hiram", d28o, "28–31 באוקטובר", 1080, "north", "tank", "28–31 באוקטובר: מבצע חירם - צה״ל כובש את מרכז הגליל העליון וחלקים מהגליל התחתון ומשתלט על כל הגליל; צבא ההצלה נעקר",
         'מבצע חירם היה הגדול והמורכב במבצעי חזית הצפון (פיקוד צפון במושגי ימינו), במהלך מלחמת העצמאות. המבצע נערך בשלבים האחרונים של המלחמה, בין 28 ל-31 באוקטובר 1948 [...] ובמהלכו כבש צה"ל את מרכז הגליל העליון וחלקים מן הגליל התחתון, ובכך השתלטה ישראל על כל שטחו של הגליל',
         geom=[mk("uppergal", "fight")], end=3 * 1440, prec="approximate", nopos=["נתיבי ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.95, 35.20], [33.05, 35.42], [33.10, 35.50]], t, t + 24, "מבצע חירם: מרכז הגליל העליון", BLUE, "north"), arrow([[32.85, 35.30], [32.95, 35.40]], t + 6, t + 26, "מבצע חירם: הגליל התחתון", BLUE, "north"), boom([33.03, 35.42], t + 24, "north", 2),
          unit("צבא ההצלה נעקר מהגליל", "syr", [[33.0, 35.45], [33.15, 35.55]], M(D("10-30"), 6, 0), M(D("10-31"), 12, 0), "north", "נעקר צבא ההצלה בפיקוד פאוזי קאוקג'י מהאזור", "hiram")]
# ================= episode 4: Operation Horev (22 Dec 1948 - 8 Jan 1949) and episode 5: Operation Uvda (March 1949) =================
place("rafah49", "אזור קרב רפיח (1949)", 31.22586667, 34.21743333, "ar", "קרב רפיח (1949)")
place("eilat", "אום רשרש (אילת) (קירוב)", 29.5577, 34.9519, "il", basis="הערך אינו מציין קואורדינטות; מרכז אילת (קירוב שלנו)")
place("eingedi", "עין גדי (קירוב)", 31.46, 35.39, "il", basis="הערך אינו מציין קואורדינטות; קירוב שלנו")
d22d, d3j, d6m, d2m = D("12-22"), D("01-03"), D("03-06"), D("03-02")
t = card("d1", "horev", d22d, "22 בדצמבר – 7 בינואר", 600, "negev", "tank", "22 בדצמבר 1948 – 7 בינואר 1949: מבצע חורב - מתקפה רחבת היקף נגד חיל המשלוח המצרי בנגב ובמזרח סיני",
         'מבצע חורב, אשר נקרא גם מבצע עין, היה מתקפה רחבת היקף של צה"ל כנגד חיל המשלוח המצרי בנגב ובמזרח סיני, במהלך שלביה האחרונים של מלחמת העצמאות. המבצע, אשר החל ב-22 בדצמבר 1948 והסתיים ב-7 בינואר 1949, נחל הצלחה ברובו',
         end=16 * 1440, prec="approximate", nopos=["נתיבי ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[31.30, 34.60], [31.15, 34.35], [31.05, 34.20]], t, t + 30, "מבצע חורב: אל ניצנה ומזרח סיני", BLUE, "negev"), arrow([[31.25, 34.50], [31.10, 34.25]], t + 4, t + 34, "מבצע חורב", BLUE, "negev"), boom([31.05, 34.20], t + 30, "negev", 2)]
t = card("d2", "rafah49", d3j, "3–8 בינואר", 600, "south", "tank", "3–8 בינואר 1949: קרב רפיח - גולני והראל מכתרות כוח מצרי, ובסופו המצרים מסכימים לנהל משא ומתן על שביתת נשק",
         'קרב רפיח היה מערכה צבאית בין צבא ההגנה לישראל וצבא מצרים בשלב האחרון של מלחמת העצמאות. ב-3–8 בינואר 1949, מדרום לרפיח, היום ברצועת עזה. את הקרב יזמה ישראל במסגרת מבצע חורב',
         geom=[mk("rafah49", "fight")], end=5 * 1440, prec="approximate")
ITEMS += [arrow([[31.15, 34.35], [31.2259, 34.2174]], t, t + 20, "גולני והראל תוקפות", BLUE, "south"), boom([31.2259, 34.2174], t + 20, "south", 2)]
t = card("e1", "yitzuv", d2m, "2–9 במרץ", 600, "negev", "tank", "2–9 במרץ 1949: מבצע ייצוב - חטיבת אלכסנדרוני כובשת את עין גדי, מצדה ושטחים בהר חברון",
         'מבצע ייצוּב הוא מבצע שבו כבשה חטיבת אלכסנדרוני, בין 2 ל-9 במרץ 1949, את אזור עין גדי, מצדה ושטחים בהר חברון', geom=[mk("eingedi", "fight")], end=7 * 1440, prec="approximate", nopos=["מקומות: קירוב שלנו"], view="negev")
ITEMS += [arrow([[31.35, 35.15], [31.46, 35.39]], t, t + 18, "אלכסנדרוני: אל עין גדי", BLUE, "negev")]
t = card("e2", "uvda", d6m, "6–10 במרץ", 480, "eilat", "tank", "6–10 במרץ 1949: מבצע עובדה - כיבוש הנגב הדרומי וערבה הדרומית עד אום רשרש (אילת), כמעט בלי לחימה",
         'ובו נכבשו הנגב הדרומי ודרום עמק הערבה, לרבות אום רשרש (אילת) [...] המבצע היה בעיקרו מבצע לוגיסטי: כמעט ללא לחימה וללא אבדות לכוחות צה"ל',
         geom=[mk("eilat", "fight")], end=4 * 1440, prec="approximate", nopos=["נתיבי התנועה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[30.60, 34.80], [30.00, 34.92], [29.5577, 34.9519]], t, t + 30, "עובדה: דרומה לאום רשרש", BLUE, "eilat")]


def build_event_file():
    end = T0(len(DAYS) - 1) + DUR + 10
    date0 = _dt.date.fromisoformat(DAYS[0][0])
    days = [{"n": n + 1, "label": lab, "T0": T0(n), "min0": (_dt.date.fromisoformat(d) - date0).days * 1440, "dur": DUR, "date": d} for n, (d, lab) in enumerate(DAYS)]
    chapters = [{"name": nm, "sub": sb, "T0": T0(EP_OF.index(e)), "from": EP_OF.index(e) + 1, "to": len(EP_OF) - EP_OF[::-1].index(e)} for e, (_a, _b, nm, sb) in enumerate(EPISODES)]
    articles = {t: {"revid": r} for t, r in WIKI.values()}
    ev = {"source": {"title": "מלחמת העצמאות", "url": "https://he.wikipedia.org/wiki/" + urllib.parse.quote("מלחמת_העצמאות"), "revid": WIKI["main"][1], "revision_time": "2026-10",
                     "license": "CC BY-SA 4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.he",
                     "permalink": "https://he.wikipedia.org/w/index.php?title=" + urllib.parse.quote("מלחמת_העצמאות") + f"&oldid={WIKI['main'][1]}",
                     "authors_url": "https://he.wikipedia.org/w/index.php?title=" + urllib.parse.quote("מלחמת_העצמאות") + "&action=history", "articles": articles},
          "places": PLACES, "areas": {}, "events": sorted(CARDS, key=lambda c: c["start_min"]), "time_range": [0, len(DAYS) * 1440], "area_filter": AREAS, "views": VIEWS, "still_views": VIEWS, "view": VIEWS["all"],
          "cards_title": "אירועי המלחמה (סיכום שלנו, מצוטט מהערכים)", "casualties": [],
          "scene": {"dur": end, "view0": VIEWS["all"], "acts": sorted(ACTS, key=lambda a: a["s"]), "log": sorted(LOG, key=lambda l: l["t"]), "sfx": war_sfx.auto(ITEMS), "items": ITEMS, "bases": [], "areas": [], "show_places": SHOW,
                    "icons": True, "control": {"label": "עיגול שליטה (סכמטי)", "grow": GROW}},
          "whole": {"date0": DAYS[0][0], "days": days, "chapters": chapters, "skip_idle": True, "slow_cam": True,
                    "start_T": at(0, 0) + 0.5, "alt": {"t0": 0.5, "t1": at(D("05-17"), 0), "period": 10, "views": [VIEWS["south"], VIEWS["north"], VIEWS["jer"]]}}}
    for it in ev["scene"]["items"]:
        if it["type"] in ("arrow", "walk", "fly", "shell") and "u" not in it:
            t0 = it["t0"] if "t0" in it else it["legs"][0]["t0"]
            d = max(i for i in range(len(DAYS)) if T0(i) <= t0); last = max(i for i in range(len(DAYS)) if EP_OF[i] == EP_OF[d]); it["u"] = T0(last) + DUR + 8   # a unit lives to the end of its episode
    import war_battle_fill   # LAW R35 (the owner 10-26): every battle card animates both sides at its place; the missing side is drawn schematically at the place (tools/war_battle_fill.py)
    import war_foot_expiry; war_foot_expiry.apply(ev)  # R44 (first): foot units leave the map 6 simulated hours after their last update; then every battle card gets its missing side
    war_battle_fill.fill(ev)
    import war_battle_fire      # LAW R36 / R40 (the owner 10-26): battles are visible (both sides fire) and every noisy item has a sound cue
    war_battle_fire.fire(ev)
    import war_stopped      # R49 (the owner 10-26): בולמים = both sides lose (Yad Mordechai); נבלם = destroyed (the Egyptian column at Ashdod bridge, hit by four 101 Squadron aircraft)
    war_stopped.apply(ev, [{"card": "a9", "fam": "hold", "side": "ar", "wrecks": 3, "dwrecks": 2}, {"card": "b2b", "fam": "hold", "side": "ar", "wrecks": 3, "dwrecks": 2}, {"card": "a10", "fam": "stopped", "side": "ar", "wrecks": 4, "air": 4, "air_label": "מטוס טייסת 101", "air_from": [31.95, 34.85]}], area="south")
    import war_source_links; war_source_links.apply(ev)    # R47: card titles link to their source passage
    import war_intro_data; war_intro_data.intro(ev, 'מלחמת העצמאות', il_name='ישראל והיישוב', ar_name='הצד הערבי', note='הנתונים בערך הם למלחמה כולה (30.11.1947 - 20.7.1949)')   # R48 opening screen
    # R47 (the owner 10-26): every card title links to its passage in the source (pinned revision + text fragment); gaps are listed, never guessed
    import war_surrender; war_surrender.fill(ev)      # R43: white flag over every surrender report
    war_sfx.cover(ev["scene"])
    return ev


def _norm(s):
    import unicodedata
    return "".join(c for c in s if unicodedata.category(c) not in ("Cf", "Zs", "Cc") and not c.isspace() and not "֑" <= c <= "ׇ")


def check_quotes(ev):
    bad = 0; cache = {}
    def src_text(k):
        if k not in cache: cache[k] = _norm((SRC_DIR / f"{k}.txt").read_text(encoding="utf-8"))
        return cache[k]
    for c in ev["events"]:
        for seg in [x.strip() for x in c["quote"].replace("[...]", "\n").split("\n") if x.strip()]:
            if _norm(seg) not in src_text(c["src"]["k"]): bad += 1; print("QUOTE NOT IN", c["src"]["k"], ":", c["id"], seg[:70])
    for it in ev["scene"]["items"]:
        if it.get("q"):
            for seg in [x.strip() for x in it["q"].replace("[...]", "\n").split("\n") if x.strip()]:
                if _norm(seg) not in src_text(it["sk"]): bad += 1; print("ITEM QUOTE NOT IN", it["sk"], ":", it.get("label"), seg[:60])
    return bad


if __name__ == "__main__":
    ev = build_event_file()
    if "--check-quotes" in sys.argv:
        sys.exit(1 if check_quotes(ev) else 0)
    (DATA / "1948-05-15-events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(CARDS)} cards, {len(ITEMS)} scene items, dur {ev['scene']['dur']}")
