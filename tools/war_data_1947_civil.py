#!/usr/bin/env python3
"""Authors the guerrilla war BEFORE the War of Independence, 30 Nov 1947 - 14 May 1948, for /war/ as ONE scene on the shared engine: writes war/data/1947-11-30-events.json.

Same rules as the other war pages (war-maps-checklist.md; the owner 10-23/24): moves and battles only, 1-2 cards per battle, no background / talks / after cards, named formations as unit symbols with their
own quotes, every quote segment asserted by --check-quotes to be a substring of its pinned source (he.wikipedia, CC BY-SA 4.0, plain-text extracts in SRC_DIR, not in git), schematic positions labelled,
sound from the scene (war_sfx.auto), no scale overlay, no casualty totals (the owner/coordinator 10-24: events with civilian victims are dated movements in the article's words), disputed figures not used.
Episodes of consecutive real days; the gaps between them are skipped. Run: python3 tools/war_data_1947_civil.py [--check-quotes]"""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import war_sfx
import war_landcheck as LC
LM = LC.load_mask()
S = lambda p: LC.snap(LM, p)      # a ground vertex that fell on water goes to the nearest land (checklist 17)

DATA = Path(__file__).resolve().parent.parent / "war" / "data"
SRC_DIR = Path("")
WIKI = {"main": ["מלחמת העצמאות", 44066102], "tirat": ["קרב טירת צבי", 42192091], "yehiam": ["שיירת יחיעם", 43439513], "nabidan": ["שיירת נבי דניאל", 43217268], "semiramis": ["פיצוץ מלון סמירמיס", 43925974], "benyehuda": ["הפיגוע ברחוב בן-יהודה (1948)", 42194411], "ala": ["צבא ההצלה", 43796548], "lamedhe": ["מחלקת הל\"ה", 43953913], "kastel": ["קרב הקסטל", 44034282], "nachshon": ["מבצע נחשון", 43383704], "mishmar": ["קרב משמר העמק", 40951568], "deiry": ["פרשת דיר יאסין", 44007429], "hadassah": ["שיירת הדסה", 43356030], "tiberias": ["הקרב על טבריה", 42647988], "haifa": ["הקרב על חיפה", 42647986], "nabisam": ["קרב נבי סמואל", 42839781], "hametz": ["מבצע חמץ", 43483130], "yiftach": ["מבצע יפתח", 41422724], "safed": ["הקרב על צפת", 44029942], "etzion": ["הקרב על גוש עציון", 43234056]}
import datetime as _dt
EPISODES = [("1947-11-30", "1947-12-01", "ההתקפה הראשונה", "30 בנובמבר – 1 בדצמבר 1947"), ("1948-01-05", "1948-01-06", "פיצוץ מלון סמירמיס", "5–6 בינואר 1948"),
            ("1948-01-15", "1948-01-21", "הל״ה וצבא ההצלה", "15–21 בינואר 1948"), ("1948-02-16", "1948-02-17", "טירת צבי", "16–17 בפברואר 1948"),
            ("1948-02-22", "1948-02-23", "רחוב בן-יהודה", "22–23 בפברואר 1948"), ("1948-03-26", "1948-03-28", "שיירות נבי דניאל ויחיעם", "26–28 במרץ 1948"),
            ("1948-04-03", "1948-04-18", "הקסטל, נחשון ומשמר העמק", "3–18 באפריל 1948"), ("1948-04-21", "1948-04-29", "חיפה, יבוסי ויפו", "21–29 באפריל 1948"), ("1948-05-12", "1948-05-14", "גוש עציון", "12–14 במאי 1948")]
DAYS, EP_OF = [], []        # (date, label), episode index per day
for _e, (a, b, _n, _s) in enumerate(EPISODES):
    d0, d1 = _dt.date.fromisoformat(a), _dt.date.fromisoformat(b)
    while d0 <= d1:
        DAYS.append((d0.isoformat(), f"{d0.day}.{d0.month}")); EP_OF.append(_e); d0 += _dt.timedelta(days=1)
DUR, GAP, EGAP = 100, 6, 30    # 100 s of play per war day (46 days: the over-20-days exception of checklist 09), 6 s between days, 30 s between episodes (the weeks skipped)
_T0 = []
for _i in range(len(DAYS)):
    _T0.append(0 if _i == 0 else _T0[-1] + DUR + (EGAP if EP_OF[_i] != EP_OF[_i - 1] else GAP))
T0 = lambda d: _T0[d]
at = lambda day, minute: round(T0(day) + minute / 1440 * DUR, 2)
D = lambda date: [i for i, (d, _) in enumerate(DAYS) if d.endswith(date)][0]       # "01-20" -> day index (month-day is unique here)
BLUE, RED = "#1d5ea8", "#b3261e"
VIEWS = {"all": [[31.5, 34.7], [33.2, 35.9]], "jer": [[31.55, 34.9], [31.95, 35.4]], "north": [[32.25, 35.0], [33.15, 35.8]]}
AREAS = [{"id": "all", "name": "הכל"}, {"id": "jer", "name": "ירושלים והדרך אליה"}, {"id": "north", "name": "הגליל והעמקים"}]
CARDS, ITEMS, ACTS, LOG, GROW = [], [], [], [], []
PLACES = {}


def pl(name, lat, lon, side, basis=None, prec="exact", article=None):
    return {"name": name, "lat": lat, "lon": lon, "precision": prec, "side": side,
            "basis": basis if prec != "exact" else f'נקודת המקום בערך ״{article}״ בוויקיפדיה העברית'}


def place(pid, name, lat, lon, side, article=None, basis=None):
    PLACES[pid] = pl(name, lat, lon, side, basis, "approximate", None) if basis else pl(name, lat, lon, side, article=article)


def src(k):
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


# ---- places: the articles give no coordinates for these events, so every point is an approximation of ours and says so ----
AP = "הערך אינו מציין קואורדינטות; הנקודה היא קירוב שלנו"
place("tlv_jlm", "הדרך תל אביב-ירושלים (קירוב)", 31.95, 35.00, "il", basis=AP)
place("katamon", "קטמון, ירושלים (קירוב)", 31.7585, 35.2115, "il", basis=AP)
place("etzion_road", "הדרך לגוש עציון (קירוב)", 31.68, 35.07, "il", basis=AP)
place("tirat", "קיבוץ טירת צבי (קירוב)", 32.425, 35.527, "il", basis=AP)
place("benyehuda", "רחוב בן-יהודה, ירושלים (קירוב)", 31.7829, 35.2198, "il", basis=AP)
place("kabri", "הדרך נהריה-יחיעם, ליד כאברי (קירוב)", 33.000, 35.150, "ar", basis=AP)
place("yehiam", "קיבוץ יחיעם (קירוב)", 32.99, 35.22, "il", basis=AP)
place("nebidan", "נבי דניאל, הדרך לגוש עציון (קירוב)", 31.67, 35.17, "ar", basis=AP)
SHOW = []


# ================= the events =================
# ---- 30 Nov 1947: the first attack ----
d1 = D("11-30")
t = card("c1", "main", d1, "ביום", 600, "all", "tank", "30 בנובמבר 1947: ההתקפה על אוטובוס אגד בדרך לירושלים - ראשית הלחימה",
         'כיריית הפתיחה במלחמה זו נחשבת ההתקפה על אוטובוס 2094 של אגד, ב-30 בנובמבר 1947', geom=[mk("tlv_jlm", "fight")], prec="approximate",
         nopos=["מקום ההתקפה: אינו בציטוט; הדרך מתל אביב לירושלים סכמטית"])
ITEMS += [unit("אוטובוס אגד בדרך לירושלים", "iaf", [[32.07, 34.80], [31.97, 34.96], [31.90, 35.05]], M(d1, 9, 50), M(d1, 10, 30), "all"), arrow([[32.0, 35.12], [31.96, 34.99]], t, t + 14, "ההתקפה על האוטובוס", RED, "all", "foot"), boom([31.96, 34.99], t + 14, "all", 1)]

# ---- 5 Jan 1948: the Semiramis hotel in Katamon ----
d2 = D("01-05")
t = card("c2", "semiramis", d2, "בלילה", 60, "jer", "tank", "5 בינואר 1948: פיצוץ מלון סמירמיס בקטמון",
         'המלון פוצץ על ידי אנשי ארגון "ההגנה" בתחילת מלחמת העצמאות, ב-5 בינואר 1948, עקב זיהויו, השגוי ככל הנראה, של הבניין כמפקדת הנג\'אדה', geom=[mk("katamon", "fight")], prec="approximate",
         nopos=["מסלול החבלנים: אינו בציטוט; הציור סכמטי"])
ITEMS += [arrow([[31.7700, 35.2000], [31.7585, 35.2115]], t, t + 12, "אנשי ההגנה אל המלון", BLUE, "jer", "foot"), boom([31.7585, 35.2115], t + 12, "jer", 2)]

# ---- 15-21 Jan 1948: the Lamed-Heh platoon; the Liberation Army enters; the attack on Yehiam ----
d3 = D("01-15"); d4 = D("01-20")
t = card("c3", "lamedhe", d3, "אור ל-16 בינואר", 1380, "jer", "tank", "15–16 בינואר 1948: מחלקת הל״ה יוצאת לתגבר את גוש עציון המנותק ומותקפת בדרך",
         '35 מאנשיה (בגימטריה - "ל"ה") יצאו לתגבר את גוש עציון המנותק [...] לפנות בוקר התגלתה המחלקה, כותרה על ידי המוני ערבים מהסביבה',
         geom=[mk("etzion_road", "fight")], end=1500, prec="approximate", nopos=["מסלול המחלקה: אינו בציטוט; הציור סכמטי"])
ITEMS += [unit("מחלקת הל״ה", "iaf", [[31.73, 35.00], [31.70, 35.04], [31.66, 35.08]], M(d3, 23, 30), M(d3 + 1, 5, 0), "jer", 'על המחלקה פיקד דני מס', "lamedhe"), arrow([[31.71, 35.12], [31.69, 35.05]], t + 5, t + 18, "כיתור המחלקה", RED, "jer", "foot"), boom([31.69, 35.05], t + 18, "jer", 2)]
t = card("c4", "tirat", d4, "ביום", 540, "north", "tank", "20 בינואר 1948: גדוד הירמוך של צבא ההצלה חוצה את גשר דמיה ומתמקם ליד טובאס",
         "ב-20 בינואר 1948 חצה גדוד הירמוך הראשון של 'צבא ההצלה' את גשר דמיה בשיירה ארוכה והתמקם בסביבות טובאס", geom=[mk("tirat", "fight")], prec="approximate",
         nopos=["מסלול השיירה: אינו בציטוט; הציור סכמטי"])
ITEMS += [unit("גדוד הירמוך הראשון (צבא ההצלה)", "syr", [[32.19, 35.57], [32.30, 35.45], [32.32, 35.37]], M(d4, 9, 0), M(d4, 15, 0), "north", "גדוד הירמוך הראשון של 'צבא ההצלה', בפיקודו של מוחמד צפא", "tirat"),
          tag(M(d4, 9, 10), [32.23, 35.52], "צבא ההצלה: מתנדבים מארצות ערב שנכנסו מינואר 1948", 'שפלש לתחום המנדט החל בינואר 1948 בלי שנתקל בהתנגדות בריטית', "ala", dur=12, area="north")]
t = card("c5", "yehiam", d4, "ביום", 780, "north", "tank", "20 בינואר 1948: התקפה גדולה על יחיעם; משוריין נתקף בדרך",
         'ב-20 בינואר 1948, הותקף משוריין באזור, במהלך התקפה גדולה על יחיעם', geom=[mk("yehiam", "fight")], prec="approximate", nopos=["מסלול המשוריין: אינו בציטוט; הציור סכמטי"])
ITEMS += [unit("משוריין לשיירת יחיעם", "iaf", [[33.00, 35.09], [33.00, 35.14], [32.99, 35.20]], M(d4, 12, 30), M(d4, 13, 30), "north"), arrow([[33.03, 35.17], [33.00, 35.14]], t, t + 14, "התקפה על המשוריין", RED, "north", "foot"), boom([33.00, 35.14], t + 14, "north", 1)]

# ---- 16 Feb 1948: Tirat Tzvi ----
d5 = D("02-16")
t = card("c6", "tirat", d5, "ביום", 600, "north", "tank", "16 בפברואר 1948: גדוד הירמוך הראשון תוקף את טירת צבי בעמק בית שאן; ההתקפה נהדפת",
         "ב-16 בפברואר 1948 התקיף גדוד הירמוך הראשון של 'צבא ההצלה', בפיקודו של מוחמד צפא, את קיבוץ טירת צבי בעמק בית שאן. ההתקפה נהדפה", geom=[mk("tirat", "fight")], prec="approximate",
         nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.34, 35.40], [32.425, 35.527]], t, t + 18, "גדוד הירמוך הראשון תוקף", RED, "north"), arrow([[32.425, 35.527], [32.39, 35.46]], t + 20, t + 30, "ההתקפה נהדפת", BLUE, "north", "foot"), boom([32.425, 35.527], t + 14, "north", 2)]

# ---- 22 Feb 1948: Ben Yehuda Street ----
d6 = D("02-22")
t = card("c7", "benyehuda", d6, "בבוקר", 390, "jer", "tank", "22 בפברואר 1948: משאיות תופת מגיעות לרחוב בן-יהודה בירושלים והפיצוץ הורס שלושה בניינים",
         'ביום י"ב באדר א\' תש"ח, 22 בפברואר 1948. הוא תוכנן על ידי עבד אל-קאדר אל-חוסייני ופאוזי אל-כותוב ובוצע על ידי חיילים שערקו מהצבא הבריטי ועשו שימוש בכלי רכב ובנשק של הצבא הבריטי [...] שלושה בניינים ברחוב בן-יהודה בירושלים (שני בתי מלון ובניין מגורים) נהרסו',
         geom=[mk("benyehuda", "fight")], prec="approximate", nopos=["מסלול המשאיות: אינו בציטוט; הציור סכמטי"])
ITEMS += [unit("משאיות ושריונית בריטית (שערקו)", "syr", [[31.80, 35.13], [31.79, 35.19], [31.7829, 35.2198]], M(d6, 6, 0), M(d6, 6, 28), "jer", "ובוצע על ידי חיילים שערקו מהצבא הבריטי", "benyehuda"), boom([31.7829, 35.2198], at(d6, 390) + 4, "jer", 2)]

# ---- 27 Mar 1948: the Nebi Daniel convoy and the Yehiam convoy ----
d7 = D("03-27")
t = card("c8", "nabidan", d7, "ביום", 600, "jer", "tank", "27 במרץ 1948: שיירת נבי דניאל יוצאת מירושלים לגוש עציון הנצור ונתקלת במארב בחזרה",
         'שיירת נבי דניאל הייתה שיירה גדולה שיצאה בט"ז באדר ב\', 27 במרץ 1948, מירושלים לעזרת גוש עציון הנצור, במטרה להעביר אספקה. בחזרתה לירושלים נתקלה השיירה במארב',
         geom=[mk("nebidan", "fight")], prec="approximate", nopos=["מסלול השיירה: אינו בציטוט; הציור סכמטי"], end=900)
ITEMS += [unit("שיירת נבי דניאל (גדוד מכמש)", "iaf", [[31.775, 35.20], [31.70, 35.19], [31.65, 35.12]], M(d7, 7, 0), M(d7, 11, 0), "jer", 'רוב הלוחמים היו מגדוד מכמש מירושלים בפיקודו של אברהם טריינין (טמיר)', "nabidan"),
          unit("שיירת נבי דניאל בחזרה", "iaf", [[31.65, 35.12], [31.67, 35.17], [31.70, 35.19]], M(d7, 12, 0), M(d7, 14, 0), "jer"), arrow([[31.70, 35.23], [31.67, 35.17]], at(d7, 770), at(d7, 770) + 14, "מארב על השיירה", RED, "jer", "foot"), boom([31.67, 35.17], at(d7, 770) + 14, "jer", 2)]
t = card("c9", "yehiam", d7, "אחר הצהריים", 840, "north", "tank", "27 במרץ 1948: שיירת יחיעם יוצאת מנהריה ונקלעת למארב ליד כאברי",
         'שיירת יחיעם הייתה שיירת אספקה של חטיבת כרמלי במלחמת העצמאות שיצאה ב-27 במרץ 1948 מנהריה לקיבוץ יחיעם שהיה מנותק. השיירה נקלעה למארב, והותקפה על ידי כנופיות וכפריים ערבים בסמוך לכאברי',
         geom=[mk("kabri", "fight")], prec="approximate", nopos=["מסלול השיירה: אינו בציטוט; הציור סכמטי"], end=1000)
ITEMS += [unit("שיירת יחיעם (גדוד 21, חטיבת כרמלי)", "iaf", [[33.005, 35.095], [33.00, 35.15], [32.99, 35.20]], M(d7, 14, 0), M(d7, 15, 30), "north", 'בן עמי פכטר, שהיה מפקד גדוד 21 של חטיבת כרמלי', "yehiam"), arrow([[33.03, 35.17], [33.00, 35.15]], at(d7, 880), at(d7, 880) + 16, "מארב כנופיות וכפריים", RED, "north", "foot"), boom([33.00, 35.15], at(d7, 880) + 16, "north", 2),
          tag(M(d7, 14, 5), [33.04, 35.12], "גדוד ירמוך השני של צבא ההצלה באזור", 'אדיב שישכלי, שהיה מפקד גדוד ירמוך השני בצבא ההצלה באזור', "yehiam", dur=12, area="north")]

# ================= episode 7: 3-18 April 1948 =================
place("kastel", "הקסטל (קירוב)", 31.7939, 35.1486, "ar", basis=AP)
place("dy", "דיר יאסין (קירוב)", 31.7867, 35.1747, "ar", basis=AP)
place("scopus", "הדרך להר הצופים, שייח' ג'ראח (קירוב)", 31.7950, 35.2300, "il", basis=AP)
place("mishmar", "קיבוץ משמר העמק (קירוב)", 32.6050, 35.1230, "il", basis=AP)
place("tiberias", "טבריה (קירוב)", 32.7922, 35.5312, "ar", basis=AP)
place("safed", "צפת (קירוב)", 32.9646, 35.4960, "ar", basis=AP)
place("bab", "ציר נחשון: שער הגיא - ירושלים (קירוב)", 31.80, 35.05, "il", basis=AP)
d8 = D("04-03"); d9 = D("04-05"); d10 = D("04-04"); d11 = D("04-08"); d12 = D("04-09"); d13 = D("04-13"); d14 = D("04-16")
t = card("c10", "kastel", d8, "בלילה", 1320, "jer", "tank", "3–9 באפריל 1948: קרב הקסטל על הדרך לירושלים (מבצע נחשון)",
         'קרב הקסטל במלחמת העצמאות נערך בתאריכים 3–9 באפריל 1948 במסגרת מבצע נחשון, בין כוחות ההגנה שכללו יחידות מחטיבת עציוני ומהפלמ"ח לבין כוחות ערביים לא סדירים [...] בקרב נהרג עבד אל-קאדר אל-חוסייני, מנהיג הכוחות הערבים באזור ירושלים במלחמת העצמאות',
         geom=[mk("kastel", "fight")], end=1440 * 6, prec="approximate", nopos=["מסלולי ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [unit("יחידות חטיבת עציוני והפלמ״ח", "iaf", [[31.80, 35.08], [31.80, 35.12], [31.7939, 35.1486]], M(d8, 22, 0), M(d8, 30, 0), "jer", 'בין כוחות ההגנה שכללו יחידות מחטיבת עציוני ומהפלמ"ח', "kastel"),
          unit("צבא הג׳יהאד הקדוש (עבד אל-קאדר אל-חוסייני)", "syr", [[31.78, 35.20], [31.79, 35.17], [31.7939, 35.1486]], M(d8, 23, 0), M(d8, 29, 0), "jer", "עבד אל-קאדר אל-חוסייני, מפקד צבא הג'יהאד הקדוש באזור ירושלים", "kastel"), boom([31.7939, 35.1486], t + 20, "jer", 2)]
t = card("c11", "nachshon", d9, "בליל 5–6 באפריל", 1380, "jer", "tank", "5–16 באפריל 1948: מבצע נחשון - פריצת הדרך לירושלים",
         'מבצע נחשון היה מבצע של ההגנה במלחמת העצמאות, שהחל בליל 5–6 באפריל 1948 והסתיים ב-16 באפריל. מטרתו הייתה לפרוץ את הדרך לירושלים, באמצעות יצירת ציר מאובטח',
         geom=[mk("bab", "fight")], end=1440 * 10, prec="approximate", nopos=["תוואי הציר: אינו בציטוט; הציור סכמטי"])
ITEMS += [arrow([[31.88, 34.85], [31.84, 34.98], [31.80, 35.06], [31.79, 35.17]], t, t + 40, "מבצע נחשון: ציר לירושלים", BLUE, "jer")]
t = card("c12", "mishmar", d10, "ביום", 360, "north", "tank", "4–15 באפריל 1948: צבא ההצלה תוקף את משמר העמק; ההתקפה נהדפת",
         '4 באפריל – 15 באפריל 1948, בין כוחות ערביים של צבא ההצלה ולוחמים מקומיים, בפיקודו של פאוזי אל-קאוקג\'י, לבין מגיני קיבוץ משמר העמק, יחד עם הגדוד הראשון של הפלמ"ח, כוח תגבור של חטיבת גולני',
         geom=[mk("mishmar", "fight")], end=1440 * 11, prec="approximate", nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.55, 35.04], [32.6050, 35.1230]], t, t + 24, "צבא ההצלה תוקף", RED, "north"), unit("הגדוד הראשון של הפלמ״ח וכוח מגולני", "iaf", [[32.64, 35.16], [32.6050, 35.1230]], M(d10, 8, 0), M(d10, 16, 0), "north", 'יחד עם הגדוד הראשון של הפלמ"ח, כוח תגבור של חטיבת גולני', "mishmar"), boom([32.6050, 35.1230], t + 24, "north", 2)]
t = card("c13", "tiberias", d11, "ביום", 600, "north", "tank", "8–18 באפריל 1948: הקרב על טבריה",
         'הקרב על טבריה במלחמת העצמאות נערך בין 8 באפריל ל-18 באפריל 1948 בין כוחות ההגנה לכוחות ערביים מקומיים. הקרב הסתיים בניצחון ה"הגנה"',
         geom=[mk("tiberias", "fight")], end=1440 * 10, prec="approximate", nopos=["כיווני הלחימה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.80, 35.50], [32.7922, 35.5312]], t, t + 20, "כוחות ההגנה בטבריה", BLUE, "north", "foot"), boom([32.7922, 35.5312], t + 20, "north", 1)]
t = card("c14", "deiry", d12, "בבוקר", 300, "jer", "tank", "9 באפריל 1948: כיבוש הכפר דיר יאסין בידי האצ״ל והלח״י",
         'עוסקת בכיבוש הכפר הערבי דיר יאסין, ממערב לירושלים, ב-9 באפריל 1948, במסגרת המערכה על ירושלים במלחמת העצמאות. הכפר נכבש במתקפה מתוכננת על ידי לוחמי האצ"ל והלח"י',
         geom=[mk("dy", "fight")], prec="approximate", nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [unit("לוחמי האצ״ל והלח״י", "iaf", [[31.78, 35.20], [31.7867, 35.1747]], M(d12, 4, 30), M(d12, 8, 0), "jer", 'על ידי לוחמי האצ"ל והלח"י', "deiry"), boom([31.7867, 35.1747], t + 10, "jer", 1)]
t = card("c15", "hadassah", d13, "בבוקר", 540, "jer", "tank", "13 באפריל 1948: שיירת הדסה לבית החולים בהר הצופים מותקפת בשייח' ג'ראח",
         'שיירת "הדסה" (או שיירת הר הצופים) הייתה שיירת משוריינים ישראלית אשר עשתה דרכה להר הצופים ב-13 באפריל 1948 [...] בעת שעברה בשכונה הערבית שייח\' ג\'ראח, הותקפה השיירה בידי פורעים ערבים',
         geom=[mk("scopus", "fight")], prec="approximate", nopos=["מסלול השיירה: אינו בציטוט; הציור סכמטי"])
ITEMS += [unit("שיירת הדסה להר הצופים", "iaf", [[31.78, 35.215], [31.7875, 35.228], [31.795, 35.243]], M(d13, 9, 0), M(d13, 10, 0), "jer"), arrow([[31.81, 35.23], [31.7875, 35.228]], t + 4, t + 16, "התקפה על השיירה", RED, "jer", "foot"), boom([31.7875, 35.228], t + 16, "jer", 2)]
t = card("c16", "safed", d14, "ביום", 600, "north", "tank", "16 באפריל – 11 במאי 1948: הקרב על צפת - תחילתו",
         'הקרב על צפת במלחמת העצמאות נערך בין 16 באפריל ל-11 במאי 1948 בין כוח המגן העברי לכוחות צבא ההצלה הערבי', geom=[mk("safed", "fight")], prec="approximate", nopos=["כיווני הלחימה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.93, 35.45], [32.9646, 35.4960]], t, t + 20, "כוח המגן העברי בצפת", BLUE, "north", "foot")]

# ================= episode 8: 21-29 April 1948 =================
place("haifa", "חיפה (קירוב)", 32.8184, 34.9885, "ar", basis=AP)
place("nabisam", "נבי סמואל (קירוב)", 31.8317, 35.1814, "ar", basis=AP)
place("jaffa", "יפו וסביבתה (קירוב)", 32.0500, 34.7500, "ar", basis=AP)
place("galilee_e", "הגליל העליון המזרחי (קירוב)", 33.00, 35.55, "ar", basis=AP)
d15 = D("04-21"); d16 = D("04-22"); d17 = D("04-28")
t = card("c17", "haifa", d15, "ביום", 600, "north", "tank", "21 באפריל 1948: הקרב המכריע על חיפה (מבצע ביעור חמץ)",
         'הקרב המכריע (מבצע \'ביעור חמץ\') החל ב-21 באפריל 1948 והסתיים כעבור 24 שעות בניצחון כוחות חטיבת כרמלי על הכוחות הערביים', geom=[mk("haifa", "fight")], end=1440 + 600, prec="approximate", nopos=["כיווני הלחימה: אינם בציטוט; הציור סכמטי"])
ITEMS += [unit("חטיבת כרמלי (גדוד 21 וגדוד 22)", "iaf", [[32.80, 35.02], [32.8184, 34.9885]], M(d15, 10, 0), M(d15, 22, 0), "north", 'חטיבת כרמלי (גדוד 21 ובעיקר גדוד 22)', "haifa"), boom([32.8184, 34.9885], t + 10, "north", 2)]
t = card("c18", "nabisam", d16, "בערב ליל הסדר", 1200, "jer", "tank", "22–23 באפריל 1948: חטיבת הראל תוקפת את נבי סמואל (מבצע יבוסי); הניסיון כושל",
         'קרב נבי סמואל היה ניסיון השתלטות כושל של חטיבת הראל מהפלמ"ח על הכפר נבי סמואל מצפון לירושלים, שנערך ב-22–23 באפריל 1948 במסגרת מבצע יבוסי', geom=[mk("nabisam", "fight")], end=1440 + 400, prec="approximate", nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [unit("הגדוד הרביעי - גדוד הפורצים (חטיבת הראל)", "iaf", [[31.80, 35.15], [31.8317, 35.1814]], M(d16, 20, 0), M(d16, 28, 0), "jer", 'על הגדוד הרביעי – גדוד הפורצים בפיקוד יוסף טבנקין', "nabisam"), boom([31.8317, 35.1814], t + 12, "jer", 1)]
t = card("c19", "hametz", d17, "ביום", 600, "all", "tank", "28 באפריל 1948: מבצע חמץ - כיבוש הכפרים סביב יפו",
         'מבצע חמץ היה מבצע לכיבוש סביבתה של יפו במלחמת העצמאות על ידי חטיבות ההגנה: אלכסנדרוני, גבעתי וקרייתי [...] המבצע החל ב-28 באפריל 1948', geom=[mk("jaffa", "fight")], prec="approximate", nopos=["כיווני התנועה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[32.10, 34.90], [32.06, 34.80]], t, t + 20, "אלכסנדרוני וקרייתי", BLUE, "all"), arrow([[31.98, 34.85], [32.02, 34.78]], t + 4, t + 24, "גבעתי", BLUE, "all")]
t = card("c20", "yiftach", d17, "ביום", 900, "north", "tank", "28 באפריל 1948: מבצע יפתח בגליל המזרחי",
         'מבצע יפתח (28 באפריל עד 29 במאי 1948) היה מבצע צבאי של ההגנה בגליל המזרחי [...] במבצע השתתפו הגדוד הראשון והגדוד השלישי של הפלמ"ח וכן גדוד חי"ש 11 של חטיבת גולני', geom=[mk("galilee_e", "fight")], prec="approximate", nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [unit("הגדוד הראשון והשלישי של הפלמ״ח", "iaf", [[32.90, 35.50], [33.00, 35.55]], M(d17, 15, 0), M(d17, 23, 0), "north", 'הגדוד הראשון והגדוד השלישי של הפלמ"ח', "yiftach")]

# ================= episode 9: 12-14 May 1948 =================
place("etzion", "גוש עציון (קירוב)", 31.6500, 35.1170, "il", basis=AP)
d18 = D("05-13")
t = card("c21", "etzion", d18, "ביום", 600, "jer", "tank", "13–14 במאי 1948: גוש עציון נופל בידי הלגיון הערבי",
         'הקרב על גוש עציון, הידוע גם בשם הטבח בגוש עציון, החל בראשית מלחמת העצמאות, למחרת ההכרזה על תוכנית החלוקה ב-29 בנובמבר 1947, והסתיים ב-14 במאי 1948, יום הכרזת העצמאות, עם נפילת גוש עציון כולו בידי כוחות הלגיון הערבי',
         geom=[mk("etzion", "fight")], end=1440 + 600, prec="approximate", nopos=["כיווני ההתקפה: אינם בציטוט; הציור סכמטי"])
ITEMS += [arrow([[31.70, 35.20], [31.65, 35.117]], t, t + 24, "הלגיון הערבי וכוחות מקומיים", RED, "jer"), boom([31.65, 35.117], t + 24, "jer", 2)]
# LAW (the owner 10-26): a battle with heavy losses shows both sides and a loss marker. The quote names "הטבח בגוש עציון" and the fall of the whole Gush; no number in the quote, so none is drawn.
ITEMS += [{"type": "walk", "label": "יישובי גוש עציון (סכמטי, מיקום משוער)", "cls": "iaf", "sym": "▣", "area": "jer", "trail": "foot", "hold": 1, "legs": [{"t0": t, "t1": t + 2, "path": [[31.652, 35.118], [31.651, 35.119]]}]},
          {"type": "loss", "at": [31.648, 35.114], "t": t + 25, "side": "iaf", "kind": "inf", "label": "הטבח בגוש עציון: נפילת הגוש (הסימון סכמטי, מיקום משוער; המקור בציטוט אינו נותן מספר)", "area": "jer"}]


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
                    "start_T": at(0, 0) + 0.5}}
    for it in ev["scene"]["items"]:
        if it["type"] in ("arrow", "walk", "fly", "shell", "loss") and "u" not in it:
            t0 = it["t0"] if "t0" in it else it["t"] if it["type"] == "loss" else it["legs"][0]["t0"]
            d = max(i for i in range(len(DAYS)) if T0(i) <= t0); last = max(i for i in range(len(DAYS)) if EP_OF[i] == EP_OF[d]); it["u"] = T0(last) + DUR + 8   # a unit lives to the end of its episode
    import war_battle_fill   # LAW R35 (the owner 10-26): every battle card animates both sides at its place; the missing side is drawn schematically at the place (tools/war_battle_fill.py)
    import war_foot_expiry; war_foot_expiry.apply(ev)  # R44 (first): foot units leave the map 6 simulated hours after their last update; then every battle card gets its missing side
    war_battle_fill.fill(ev)
    import war_battle_fire      # LAW R36 / R40 (the owner 10-26): battles are visible (both sides fire) and every noisy item has a sound cue
    war_battle_fire.fire(ev)
    import war_source_links; war_source_links.apply(ev)    # R47: card titles link to their source passage
    import war_intro_data; war_intro_data.intro(ev, 'מלחמת האזרחים בארץ ישראל', il_name='היישוב', ar_name='הצד הערבי', dates='30 בנובמבר 1947 – 14 במאי 1948', note='אין בערך נתון נפרד לשלב זה: הנתונים הם למלחמת העצמאות כולה (עד 20.7.1949)')   # R48 opening screen
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
    (DATA / "1947-11-30-events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(CARDS)} cards, {len(ITEMS)} scene items, dur {ev['scene']['dur']}")
