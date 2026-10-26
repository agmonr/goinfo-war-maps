#!/usr/bin/env python3
"""Authors the THIRD day of the Six-Day War (7 June 1967) for /war/: writes war/data/1967-06-07.json (page text + timeline), war/data/1967-06-07-events.json
(places, events, animation scene) and adds the day-3 casualty events ("jun7") to war/data/1967-casualties.json.

Same rules as 5 and 6 June: every event carries a short quote from a pinned he.wikipedia revision (elisions marked [...], names of anyone killed left out), times are
the article's own wording, everything not given a coordinate is drawn SCHEMATICALLY and labelled so. Run: python3 tools/war_data_1967_06_07.py
"""
import copy
import json
from pathlib import Path
DATA = Path(__file__).resolve().parent.parent / "war" / "data"
D1 = json.loads((DATA / "1967-06-05-events.json").read_text(encoding="utf-8"))
D2 = json.loads((DATA / "1967-06-06-events.json").read_text(encoding="utf-8"))
CAS = json.loads((DATA / "1967-casualties.json").read_text(encoding="utf-8"))

def pl(name, lat, lon, basis_kind="נקודת המקום"):
    return {"name": name, "lat": lat, "lon": lon, "precision": "exact", "basis": f'קואורדינטות הערך "{name}" בוויקיפדיה העברית ({basis_kind})'}
PLACES = copy.deepcopy(D2["places"])
PLACES.update({
    "sharm": pl("שארם א-שייח'", 27.95, 34.37, "נקודת העיר"), "eilat": pl("אילת", 29.55391689, 34.94421963, "נקודת העיר"), "tur": pl("א-טור", 28.24166667, 33.62222222, "נקודת העיר"),
    "nasrani": pl("ראס נצרני", 27.96471944, 34.41611111), "kusseima": pl("קוסיימה", 30.666667, 34.37), "nablus": pl("שכם", 32.22027778, 35.27888889, "נקודת העיר"),
    "tulkarm": pl("טולכרם", 32.31152778, 35.02703889, "נקודת העיר"), "bethlehem": pl("בית לחם", 31.703056, 35.195556, "נקודת העיר"), "beitjala": pl("בית ג'אלא", 31.71583333, 35.1875, "נקודת היישוב"),
    "gush": pl("גוש עציון", 31.657778, 35.120833), "lions": pl("שער האריות", 31.78083333, 35.23694444), "wall": pl("הכותל המערבי", 31.77694722, 35.23425),
    "old": pl("העיר העתיקה", 31.77666667, 35.23416667), "dung": pl("שער האשפות", 31.77472222, 35.23388889), "augusta": pl("מתחם אוגוסטה ויקטוריה", 31.78666667, 35.24916667),
    "hawara": pl("חווארה", 32.15241944, 35.25659444), "telkatzir": pl("תל קציר", 32.70502631, 35.61771321), "marelias": pl("מנזר מאר אליאס", 31.734817, 35.211166),
    "mataos": pl("גבעת המטוס", 31.73889722, 35.20830556), "humma": pl("הר חומה", 31.72484444, 35.22167778)})
P = {k: [v["lat"], v["lon"]] for k, v in PLACES.items()}
AREAS = {"lahfan": D1["areas"]["lahfan"]}
SRC = copy.deepcopy(D1["source"])  # the page credits every revision it quotes: the day-1 list plus the articles this day also quotes
SRC["articles"]["תפיסת שארם א-שייח' במלחמת ששת הימים"] = {"revid": 39922591}
EVENTS = []
def ev(i, area, clock, a, b, unit, title, quote, geom=None, nopos=None, note="", prec="exact", at=0):
    EVENTS.append({"id": i, "t": clock, "time_label": clock, "start_min": a, "end_min": b, "time_precision": prec, "unit": unit, "title": title, "quote": quote,
                   "geometry": geom or [], "no_position": nopos or [], "note": note, "area": area, "_at": at})
mk = lambda place, kind, note="": {"type": "marker", "place": place, "kind": kind, "note": note}
tr = lambda a, b, label: {"type": "track", "from": a, "to": b, "label": label}
# ---------------- center ----------------
ev("c0", "center", "01:00", 60, 60, "tank", "ארצות הברית וברית המועצות מסכימות על הפסקת אש; חוסיין מבטל את הוראת הנסיגה",
   'בשעה 19:00 בערב על פי שעון ניו יורק, 1:00 לפנות בוקר על פי שעון ישראל ו-2:00 לפנות בוקר על פי שעון ירדן, הגיעו ארצות הברית וברית המועצות להסכמה על הפסקת אש בין הצדדים. המלך חוסיין הביע את הסכמתו, בתקווה שבכך תימנע המשך ההתמוטטות ביהודה ושומרון; הוא ביטל את הוראת הנסיגה שהוציא הגנרל עבד אל-מונעם ריאד שעה קודם לכן, והורה לכל היחידות להישאר במקומן ולהחזיק בעמדותיהן.',
   [], ["החלטה בינלאומית: אין מקום על המפה"], prec="approximate", at=1)
ev("c1", "center", "06:15", 375, 375, "tank", "שר הביטחון מורה רשמית להיכנס לעיר העתיקה",
   'ביום רביעי, 7 ביוני בשעה 6:15 בבוקר, הורה שר הביטחון רשמית לרמטכ"ל, רב-אלוף יצחק רבין, להיכנס לעיר העתיקה. [...] אך זו לא הייתה יכולה להתבצע לפני כיבוש רכס הר הזיתים.',
   [mk("old", "fight", "העיר העתיקה")], at=8)
ev("c2", "center", "07:00–09:05", 420, 545, "tank", "מתחם אוגוסטה ויקטוריה: הפצצת חיל האוויר והסתערות הצנחנים",
   'בשעה 7:00 בבוקר החלה חטיבה 55 בניסיון נוסף לכבוש את רכס אוגוסטה ויקטוריה. החל משעה 8:00 בבוקר החל חיל האוויר הישראלי בהפצצת הרכס [...] והגדוד השלים את כיבוש המתחם עד השעה 9:05, עם חלל אחד בלבד',
   [mk("augusta", "fight")], at=12)
ev("c3", "center", "09:30–10:00", 570, 600, "tank", "הצנחנים נכנסים בשער האריות ומגיעים להר הבית",
   'בשעה 9:30, עם השלמת ההשתלטות על הרכס, ניתן האישור הסופי לכניסה. [...] בשעה 9:45 הגיע זחל"ם המח"ט לשער האריות, עקף את הטנקים שלא היו יכולים להיכנס דרך השער הצר, ונע פנימה בתוואי רחוב ויה דולורוזה. [...] בשעה 10:00 הודיע [...] ברשת הקשר את המשפט המפורסם: ”הר הבית בידינו”.',
   [mk("lions", "fight"), mk("wall", "fight", "הר הבית והכותל")], at=58)
ev("c4", "center", "לפני 10:00", 560, 600, "tank", "חטיבת ירושלים נכנסת דרך שער האשפות; הר ציון נכבש ללא קרב",
   'נכנסו דרך שער האשפות שלוש פלוגות מגדוד 163 של החטיבה הירושלמית [...] הכוח כבש את הר ציון ללא קרב. לפני השעה 10 נכנסו פלוגות א\' וד\' של הגדוד דרך שער האשפות לעיר העתיקה ופאתי שכונת המוגרבים שליד הכותל.',
   [mk("dung", "fight"), mk("zion", "fight")], prec="approximate", at=72)
ev("c5", "center", "10:25 ו-11:00", 625, 660, "tank", "חטיבה ירדנית 29 מקבלת הוראת נסיגה; הכניעה בהר הבית",
   'בשעה 10:25 קיבל מפקד החטיבה הירדנית הוראת נסיגה, והחל בביצועה. [...] בשעה 11:00 הגיע מושל ירושלים מטעם ממשלת ירדן, [...] לרחבת הר הבית, ושם חתם על כתב הכניעה. [...] במהלך היום נמשכו היתקלויות בתוך העיר מול צלפים ירדניים, אך עד שעות אחר הצוהריים הסתיימה ההשתלטות על העיר.',
   [mk("old", "fight", "העיר העתיקה")], ["מיקום חטיבה 29: מדרום לירושלים; אין נקודה בערך"], at=84)
ev("c6", "center", "במהלך היום", 480, 1080, "tank", "חטיבה 37 כובשת את שכם; חטיבה 5 את טול כרם",
   'במהלך היום כבשה חטיבה 37 את שכם, בסיוע גדוד 17, ואילו חטיבה 45 הגיעה עד לאזור הג\'יפתליק. [...] בעוד חטיבה 5 כבשה את טול כרם והתקדמה ללא הפרעה לכיוון שכם, עד שנבלמה על פי פקודה מחשש להיתקלות בכוחות פיקוד הצפון בגזרה זו.',
   [mk("nablus", "fight"), mk("tulkarm", "fight"), mk("hawara", "fight", "גדוד 104 נבלם במחנה חווארה")], ["הג'יפתליק: אין קואורדינטות בערך"], prec="approximate", at=98)
ev("c7", "center", "בשעות הצהריים", 720, 960, "tank", "החטיבה הירושלמית נעה דרומה: מאר אליאס, גבעת המטוס, בית לחם",
   'בשעות הצהריים הורה הפיקוד לחטיבה הירושלמית לנוע דרומה ולכבוש את העמדות הירדניות שמדרום לעיר. [...] ביחד עם פלוגה א\' מגדוד 161 שכבשה את מוצב טבליה (גבעת המטוס). במקביל כבשה הפלס"ר החטיבתי את ג\'בל אבו ע\'וניים (כיום שכונת הר חומה) והמשיכה לגוש עציון וחברון דרך פאתי בית לחם.',
   [mk("marelias", "fight"), mk("mataos", "fight"), mk("humma", "fight"), mk("bethlehem", "fight")], prec="approximate", at=130)
ev("c8", "center", "לפנות ערב", 1020, 1080, "tank", "גדוד 161 בבית לחם, בית ג'אלה ובית סחור: כניעת נכבדי העיר",
   'גדוד 161 נכנס לבית לחם, בית ג\'אלה ובית סחור [...] קיבל לפנות ערב להפתעתו את הכניעה של נכבדי הכנסייה והעיר ונכבדי בית ג\'אלה ובית סחור בחדר גדול בכנסיית המולד',
   [mk("bethlehem", "fight"), mk("beitjala", "fight")], ["בית סחור: אין קואורדינטות בערך"], prec="approximate", at=142)
ev("c9", "center", "בצהרי היום", 720, 1080, "tank", "חטיבה 16 משחררת את גוש עציון",
   'בצהרי 7 ביוני אושר לחטיבה 16 לכבוש את הר חברון, ועד רדת החשכה הצליחו כוחותיה שלא נתקלו בהתנגדות של ממש, לשחרר את גוש עציון.',
   [mk("gush", "fight")], prec="approximate", at=150)
ev("c10", "center", "19:20", 1160, 1160, "tank", "חטיבה 10 כובשת את יריחו",
   'שאר כוחות חטיבה 10 החלו לנוע בבוקר 7 ביוני לעבר יריחו, אולם נבלמו מחשש לפגיעה באגפם על ידי חטיבת השריון ה-60, ורק לאחר שנתבדה החשש חידשה החטיבה את התקדמותה וכבשה את יריחו בשעה 19:20.',
   [mk("jericho", "fight")], at=162)
# ---------------- sinai ----------------
ev("s0", "sinai", "07:01–11:30", 421, 690, "tank", "חיל הים נכנס למעגן שארם א-שייח': העמדה במצר נטושה",
   'ב-7 ביוני בשעה 07:01 יצא מאילת כוח שכלל 4 נחתות [...] כאשר הגיע הכוח לטווח התותחים המצרים בראס נצרני, החוסמת את המצר, התברר כי העמדה נטושה. בשעה 11:30 נכנסו הטרפדות למעגן שארם א-שייח\', שנמצא נטוש וצוותיהן הניפו את דגל ישראל על בנין בית החולים במקום',
   [tr("eilat", "sharm", "סכמטי"), mk("nasrani", "fight"), mk("sharm", "fight")], at=24)
ev("s1", "sinai", "בוקר", 360, 720, "tank", "כוח של אוגדת שרון כובש את קוסיימה",
   'כוח אחר של שרון נע בבוקר 7 ביוני וכבש את קוסיימה לאחר נסיגת חטיבה 10 המצרית שהחזיקה בה.', [mk("kusseima", "fight")], prec="approximate", at=42)
ev("s2", "sinai", "בצהרי 7 ביוני", 720, 720, "tank", "רצועת עזה: הושלם כיבוש העיר עזה ושאר מרחב הרצועה",
   'ורק בצהרי 7 ביוני הושלמו כיבוש העיר עזה ושאר מרחב הרצועה בסיוע חטיבה 35.', [mk("gaza", "fight")], at=118)
ev("s3", "sinai", "7 ביוני", 0, 1440, "tank", "מצרים מבטלת את פקודת הנסיגה, אך הכוחות כבר נסוגים",
   'ב-7 ביוני בוטלה פקודת הנסיגה המצרית, אך באותה שעה כבר היו הכוחות המצריים נתונים בעיצומה של נסיגה וללא יכולת לשנות.', [], ["הערך לא נותן שעה ומקום"], prec="approximate", at=174)
ev("s4", "sinai", "בערב", 1080, 1260, "tank", "מעבר המיתלה: גדוד של אוגדה 31 תופס את המעבר לפני המצרים",
   'בערב 7 ביוני נעשה ניסיון להקים קו הגנה מצרי בפתחת הצירים - על כביש אל-עריש-קנטרה, כביש ביר גפגפה–אסמעיליה, מעבר הגידי ומעבר המיתלה. במעבר המיתלה הקדים גדוד של אוגדה 31 בפיקוד [...] את הכוחות המצריים ותפס את המעבר, וחטיבה מצרית שנסגה מנח\'ל הושמדה במשולב על ידי כוח השריון וחיל האוויר.',
   [mk("mitla", "fight"), mk("gidi", "fight"), mk("nakhl", "fight")], prec="approximate", at=184)
# ---------------- golan ----------------
ev("g0", "golan", "מאור ראשון", 330, 720, "mig", "חיל האוויר וארטילריה תוקפים את הצבא הסורי; הפגזה סורית על עמק החולה",
   'ב-7 ביוני תקף חיל האוויר את הצבא הסורי החל מאור ראשון ובמקביל הנחית צה"ל אש ארטילרית כבדה על הצבא הסורי. הסורים הגיבו בהפגזה ארטילרית, שכוונה בעיקר על היישובים האזרחיים בעמק החולה ועמק הירדן. בתל קציר נהרס חדר האוכל אך מלבד זאת לא נגרמו נזקים כבדים.',
   [mk("telkatzir", "shell")], ["עמק החולה ועמק הירדן: אזורים, בלי נקודה"], prec="approximate", at=48)
ev("g1", "golan", "בשעות הערב", 1080, 1260, "tank", "דיין מתיר התקפה מול הסורים רק עד הגבול הבינלאומי",
   'כאמור, ב-7 ביוני בשעות הערב הורה שר הביטחון דיין כי התקפה מול הסורים מותרת רק עד קו הגבול הבינלאומי.', [], ["הוראה כללית: אין מקום על המפה"], prec="approximate", at=192)
EVENTS.sort(key=lambda e: e["_at"])
LOGT = {e["id"]: e.pop("_at") for e in EVENTS}

# ---------------- scene ----------------
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
# act 0 (0-8) 01:00 ceasefire agreed
mark(P["jer"], 1, 8, "01:00: הסכמה על הפסקת אש (בינלאומית)", "center")
# act 1 (8-24) 06:15 order, 07:00 Augusta Victoria
mark(P["old"], 8.5, 14, "06:15: הוראה להיכנס לעיר העתיקה", "center")
sortie("חיל האוויר מפציץ את רכס אוגוסטה ויקטוריה (סכמטי)", P["augusta"], 12, 16, 21, "center", via=[31.65, 35.05])
arrow([P["scopus"], P["augusta"]], 13, 18, "גדוד 66 (סכמטי)", "center", hold=6)
arrow([[31.775, 35.255], P["augusta"]], 13.5, 18.5, "גדוד 71 (סכמטי)", "center", hold=6)
for i in range(3): boom([P["augusta"][0] + .003 * i, P["augusta"][1] - .004 * i], 17 + 1.1 * i, area="center")
mark(P["augusta"], 20.5, 24, "09:05: המתחם נכבש", "center")
# act 2 (24-40) Sharm
add({"type": "fly", "side": "iaf", "label": "כוח חיל הים: נחתות וטרפדות (סכמטי)", "area": "sinai", "legs": [{"t0": 24.5, "t1": 31, "path": [P["eilat"], [28.7, 34.9], P["nasrani"]]}, {"t0": 31, "t1": 36, "path": [P["nasrani"], P["sharm"]]}]}); sfx(25, "jet")
mark(P["nasrani"], 31, 36, "ראס נצרני: העמדה נטושה", "sinai")
mark(P["sharm"], 36.5, 40, "11:30: המעגן נכבש", "sinai")
# act 3 (40-48) Kusseima
arrow([[30.80, 34.20], P["kusseima"]], 40.5, 45, "כוח של אוגדת שרון (סכמטי)", "sinai", hold=6)
for i in range(3): boom([P["kusseima"][0] + .006 * i, P["kusseima"][1] - .008 * i], 44 + 1 * i, area="sinai")
# act 4 (48-58) Golan morning
sortie("חיל האוויר תוקף את הצבא הסורי (סכמטי)", [33.25, 36.2], 48, 53, 57, "golan", via=[32.5, 35.4])
shell([33.1, 35.9], P["telkatzir"], 49, 56, "golan", 1.1, .05)
shell([33.25, 35.95], [33.05, 35.62], 49.5, 56, "golan", 1.3, .05)
boom(P["telkatzir"], 53, area="golan", k="thud")
shell([32.85, 35.9], [33.20, 36.05], 50, 56, "golan", 1.6, .05)
# act 5 (58-72) Lions' Gate, Temple Mount
arrow([P["augusta"], P["lions"], P["wall"]], 58.5, 66, "חטיבה 55 (סכמטי)", "center", hold=10)
for i in range(3): boom([P["lions"][0] + .002 * i, P["lions"][1] - .003 * i], 61 + 1.1 * i, area="center", k="thud")
mark(P["wall"], 67, 72, "10:00: הר הבית בידינו", "center")
# act 6 (72-80) Jerusalem Brigade, Dung Gate, Mount Zion
arrow([[31.76, 35.22], P["dung"]], 72.5, 76, "גדוד 163 (סכמטי)", "center", hold=5)
mark(P["zion"], 76.5, 80, "הר ציון: נכבש ללא קרב", "center")
# act 7 (80-96) retreat order, surrender
walk("חטיבה ירדנית 29: נסיגה דרומה (סכמטי)", [P["marelias"], [31.70, 35.15], [31.60, 35.10]], 80.5, 87, "center", "syr")
mark(P["old"], 88, 96, "11:00: כתב הכניעה ביד ירדן נחתם בהר הבית", "center")
# act 8 (96-108) Nablus
arrow([P["ramallah"], [32.05, 35.25], P["nablus"]], 96.5, 104, "חטיבה 37 (סכמטי)", "center", hold=8)
for i in range(3): boom([P["nablus"][0] - .01 * i, P["nablus"][1] + .01 * i], 102 + 1.1 * i, area="center")
# act 9 (108-116) Tulkarm, Hawara
arrow([P["qalqilya"], P["tulkarm"]], 108.5, 112, "חטיבה 5 (סכמטי)", "center", hold=6)
mark(P["hawara"], 112.5, 116, "גדוד 104 נבלם במחנה חווארה", "center")
# act 10 (116-128) Gaza finish
arrow([[31.47, 34.43], P["gaza"]], 116.5, 120, "חטיבה 35 (סכמטי)", "sinai", hold=6)
for i in range(4): boom([P["gaza"][0] + .01 * (i % 2) - .005, P["gaza"][1] + .012 * (i // 2) - .006], 118 + 1.3 * i, area="sinai", k="cannon" if i % 2 else "thud")
mark(P["gaza"], 124, 128, "בצהרי 7 ביוני: הושלם כיבוש עזה והרצועה", "sinai")
# act 11 (128-146) Jerusalem Brigade south
arrow([P["rachel"], P["marelias"]], 128.5, 133, "גדוד 62 (סכמטי)", "center", hold=6)
arrow([P["rachel"], P["mataos"]], 129, 133, "פלוגה א' גדוד 161 (סכמטי)", "center", hold=6)
arrow([P["humma"], P["bethlehem"], P["gush"]], 133, 142, "הפלס\"ר החטיבתי (סכמטי)", "center", hold=6)
for k_, t_ in (("marelias", 132), ("mataos", 132.8)): boom(P[k_], t_, area="center")
mark(P["bethlehem"], 142, 146, "לפנות ערב: כניעת נכבדי בית לחם", "center")
# act 12 (146-158) Gush Etzion
arrow([[31.68, 35.15], P["gush"]], 146.5, 152, "חטיבה 16 (סכמטי)", "center", hold=6)
mark(P["gush"], 152.5, 158, "גוש עציון שוחרר", "center")
# act 13 (158-172) Jericho
walk("חטיבה 10 (סכמטי)", [P["ramallah"], [31.88, 35.35], P["jericho"]], 158.5, 166, "center")
mark(P["jericho"], 166.5, 172, "19:20: יריחו נכבשה", "center")
# act 14 (172-190) Egypt cancels the retreat, Mitla
walk("נסיגה מצרית (סכמטי)", [[30.50, 33.55], P["hasana"], P["tam"], P["gidi"]], 173, 183, "sinai", "syr")
add({"type": "walk", "label": "גדוד של אוגדה 31 (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 175, "t1": 183, "path": [P["tam"], P["mitla"]]}], "area": "sinai"})
sortie("חיל האוויר: חטיבה מצרית נסוגה מנח'ל (סכמטי)", [29.95, 33.65], 178, 184, 189, "sinai", via=[30.5, 34.2])
boom([30.0, 33.7], 184.5, area="sinai", k="thud"); boom([29.97, 33.72], 186, area="sinai", k="thud")
mark(P["mitla"], 184, 190, "מעבר המיתלה נתפס בידי גדוד של אוגדה 31", "sinai")
# act 15 (190-205) Golan evening
mark([32.9, 35.6], 190.5, 205, "הוראה: התקפה רק עד הגבול הבינלאומי", "golan")
V = {"all": [[29.9, 32.0], [33.7, 36.8]], "sinai": [[27.7, 32.0], [31.8, 34.9]], "center": [[31.4, 34.6], [32.5, 35.7]], "golan": [[32.5, 35.0], [33.6, 36.1]]}
A_ = lambda s, e, c, v: {"s": s, "e": e, "clock": c, "view": V[v], "caps": []}
ACTS = [A_(0, 8, "01:00 · הפסקת אש בינלאומית", "center"), A_(8, 24, "06:15–09:05 · אוגוסטה ויקטוריה", "center"), A_(24, 40, "07:01–11:30 · שארם א-שייח'", "sinai"),
        A_(40, 48, "בוקר · קוסיימה", "sinai"), A_(48, 58, "מאור ראשון · רמת הגולן", "golan"), A_(58, 72, "09:45–10:00 · העיר העתיקה", "center"),
        A_(72, 80, "לפני 10:00 · שער האשפות", "center"), A_(80, 96, "10:25–11:00 · הכניעה", "center"), A_(96, 108, "במהלך היום · שכם", "center"),
        A_(108, 116, "במהלך היום · טול כרם", "center"), A_(116, 128, "בצהריים · עזה", "sinai"), A_(128, 146, "בצהריים · דרומה מירושלים", "center"),
        A_(146, 158, "עד רדת החשכה · גוש עציון", "center"), A_(158, 172, "19:20 · יריחו", "center"), A_(172, 190, "בערב · מעבר המיתלה", "sinai"),
        A_(190, 220, "בערב · הוראת שר הביטחון", "golan")]
LOG = [{"t": LOGT[e["id"]], "clock": e["t"], "q": e["quote"], "n": ", ".join([p_["label"] for p_ in e["geometry"] if p_.get("label")] or [PLACES[g["place"]]["name"] for g in e["geometry"] if g["type"] == "marker"]), "area": e["area"]} for e in EVENTS]
TRAIL = [("חטיבה 55", "foot"), ("גדוד 66", "foot"), ("גדוד 71", "foot"), ("גדוד 163", "foot"), ("גדוד 62", "tank"), ("פלוגה א'", "tank"), ("הפלס", "tank"), ("חטיבה 37", "tank"), ("חטיבה 5", "tank"),
         ("חטיבה 35", "tank"), ("חטיבה 16", "tank"), ("חטיבה 10", "tank"), ("חטיבה ירדנית", "tank"), ("נסיגה מצרית", "tank"), ("גדוד של אוגדה 31", "tank"), ("כוח של אוגדת שרון", "tank")]
for it_ in ITEMS:
    if it_["type"] in ("walk", "arrow"):
        for key_, kind_ in TRAIL:
            if (it_.get("label") or "").startswith(key_):
                it_["trail"] = kind_; break
CIRC = lambda i, c, r, t0, t1, a, lab: {"id": i, "center": c, "radius_m": r, "t0": t0, "t1": t1, "area": a, "label": "קו חזית משוער: " + lab, "lab_to": 0 if t1 <= 1 else t1 + 9}
CARRY = [(g["id"], g["center"], g["radius_m"], g["area"], g["label"].replace("קו חזית משוער: ", "")) for g in json.loads((DATA / "1967-06-06-events.json").read_text(encoding="utf-8"))["scene"]["control"]["grow"]]
GROW = [CIRC(i, c, r, 0, 1, a, l) for i, c, r, a, l in CARRY]
GROW += [CIRC("augusta", P["augusta"], 1100, 17, 21, "center", "מתחם אוגוסטה ויקטוריה (09:05)"),
         CIRC("oldcity", P["old"], 1100, 86, 96, "center", "העיר העתיקה (אחר הצהריים)"),
         CIRC("sharm", P["sharm"], 3500, 36, 40, "sinai", "מעגן שארם א-שייח' (11:30)"),
         CIRC("kusseima", P["kusseima"], 3000, 44, 48, "sinai", "קוסיימה"),
         CIRC("nablus", P["nablus"], 4500, 101, 108, "center", "שכם"),
         CIRC("tulkarm", P["tulkarm"], 3200, 109, 114, "center", "טול כרם"),
         CIRC("gaza", P["gaza"], 7000, 120, 126, "sinai", "העיר עזה ושאר הרצועה (צהריים)"),
         CIRC("south", P["marelias"], 2000, 131, 136, "center", "מאר אליאס, גבעת המטוס, הר חומה"),
         CIRC("bethlehem", P["bethlehem"], 3500, 141, 146, "center", "בית לחם ובית ג'אלא"),
         CIRC("gush", P["gush"], 3200, 151, 157, "center", "גוש עציון"),
         CIRC("jericho", P["jericho"], 4500, 165, 171, "center", "יריחו (19:20)"),
         CIRC("mitla", P["mitla"], 3000, 183, 189, "sinai", "מעבר המיתלה (בערב)")]
CONTROL = {"label": "קו חזית משוער, לא גבול מדויק", "base": json.loads(json.dumps(D1["scene"]["control"]["base"])), "grow": GROW}
SCENE = {"dur": 220, "view0": V["all"], "acts": ACTS, "log": LOG, "sfx": SFX, "items": ITEMS,
         "bases": [{"pos": IL, "label": "בסיס חיל האוויר"}, {"pos": SYB, "label": "בסיס סורי"}, {"pos": JOB, "label": "בסיס ירדני"}],
         "areas": [{"name": "מקור האש הסורית", "center": [33.1, 35.95], "radius_m": 9000, "label": "מקור ההפגזה הסורית (סכמטי; לא צוין)"}],
         "show_places": ["gaza", "kusseima", "mitla", "tam", "sharm", "eilat", "jer", "old", "lions", "wall", "augusta", "bethlehem", "gush", "ramallah", "nablus", "tulkarm", "jericho", "telkatzir"],
         "control": CONTROL}
OUT = {"source": SRC, "places": PLACES, "areas": AREAS, "events": EVENTS, "time_range": [0, 1440], "area_filter": D1["area_filter"],
       "views": {"all": [[29.9, 32.0], [33.7, 36.8]], "sinai": [[27.7, 32.0], [31.8, 34.9]], "center": [[31.4, 34.6], [32.5, 35.7]], "golan": [[32.8, 35.2], [33.4, 35.9]]},
       "still_views": {"all": [[29.0, 32.4], [33.4, 36.4]], "sinai": [[27.7, 33.0], [29.6, 34.9]], "center": [[31.55, 34.95], [31.95, 35.5]], "golan": [[32.9, 35.3], [33.3, 35.9]]},
       "view": [[29.9, 32.2], [33.6, 36.7]], "cards_title": D1["cards_title"], "scene": SCENE}
(DATA / "1967-06-07-events.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
named = lambda e: ", ".join(PLACES[g["place"]]["name"] for g in e["geometry"] if g["type"] == "marker") or ""
TL = [{"clock": e["t"], "text": e["quote"], "place": named(e) or "; ".join(e["no_position"]) or "ללא מקום", "place_precision": "exact" if named(e) else "none", "area": e["area"], "start": e["start_min"]} for e in EVENTS]
PAGE = {"slug": "7-june", "cas_key": "jun7", "day_he": "היום השלישי", "year": 1967, "date": "1967-06-07", "hebrew_date": "כ\"ח באייר תשכ\"ז", "multi": True,
        "title": "7 ביוני 1967: היום השלישי של מלחמת ששת הימים, לפי שלוש זירות",
        "h1": "7 ביוני 1967: היום השלישי של מלחמת ששת הימים",
        "context": "היום השלישי של מלחמת ששת הימים - 7 ביוני 1967",
        "description": "הכניסה לעיר העתיקה, מתחם אוגוסטה ויקטוריה, שארם א-שייח', שכם ויריחו וסיום כיבוש עזה.",
        "lead": "ב-7 ביוני 1967, ביום רביעי, נכנסו כוחות צה\"ל לעיר העתיקה בירושלים: לפנות בוקר נכבש מתחם אוגוסטה ויקטוריה בהר הזיתים, בסביבות 10:00 הגיעו הצנחנים להר הבית ולכותל, ובשעה 11:00 נחתם כתב הכניעה. באותו יום נכבשו בגדה המערבית שכם, טול כרם ויריחו, החטיבה הירושלמית נעה דרומה לבית לחם ולגוש עציון, בסיני נכבש מעגן שארם א-שייח' ובצהרים הושלם כיבוש עזה. בצפון תקפו חיל האוויר והארטילריה את הצבא הסורי, ושר הביטחון הגביל את ההתקפה לגבול הבינלאומי.",
        "summary": ["העמוד מחולק לשלוש זירות: סיני ורצועת עזה, ירושלים והגדה המערבית, רמת הגולן והצפון. לכל זירה ציר זמן ומפה משלה. אפשר לעבור ביניהן בכפתורים (או בקישור ישיר: #sinai, #center, #golan).",
                    "כל אירוע מצוטט מערך בוויקיפדיה העברית שקובעת גרסתו, עם שעה כפי שהערך כותב אותה. מה שהערך לא נותן לו מקום מצויר סכמטית ומסומן כך.",
                    "ההרוגים והפצועים: לרוב אירועי היום הערכים אינם נותנים מספרים, ולכן הטבלה קצרה. מה שלא צוין מסומן \"לא צוין\" ולא כאפס."],
        "aftermath": ["סיני: ב-8 ביוני נמשכה הרדיפה לעבר התעלה, ובלילו הגיע חוד אוגדה 84 לגדת התעלה; מצרים הסכימה להפסקת אש ב-21:30 ב-8 ביוני.",
                      "הגדה המערבית: עם שחר 8 ביוני נכבשה חברון, ובשעה 10:30 הושלם כיבוש הגדה המערבית לפי הערך על החזית הירדנית.",
                      "רמת הגולן: הקרב היבשתי החל רק ב-9 ביוני, וב-10 ביוני הצבא הסורי נסוג."],
        "places": [{"name": "נקודות מסומנות: יישובים וערים (סיני, ירושלים והגדה המערבית, הצפון)", "precision": "exact", "basis": "קואורדינטות הערכים בוויקיפדיה העברית; נקודת היישוב או המקום, לא מיקום האירוע במדויק"},
                   {"name": "אזורים שצוירו", "precision": "approximate", "basis": "המקור מתאר את האזור במילים; עיגול שציירנו"},
                   {"name": "חיצי התקפה וקו החזית", "precision": "schematic", "basis": "כיווני התקדמות כלליים; הערכים לא מפרטים מסלולים. קו החזית משוער ומצויר ביד"}],
        "still_t": None,
        "still_alt": "מפה סכמטית של ירושלים והעיר העתיקה ב-7 ביוני 1967: מתחם אוגוסטה ויקטוריה, שער האריות, הר הבית ובית לחם",
        "areas": [{"id": "sinai", "name": "סיני ורצועת עזה", "short": "סיני", "view": [[27.7, 32.0], [31.8, 34.9]],
                   "intro": "ב-7 ביוני נכבש מעגן שארם א-שייח' בידי חיל הים, קוסיימה נכבשה, ובצהרים הושלם כיבוש עזה. בערב נעשה ניסיון מצרי לקיים קו הגנה בפתחת הצירים, ובמיתלה הקדים גדוד ישראלי את המצרים.",
                   "note": "הלחימה בסיני נמשכה עד 9 ביוני; כאן מוצג רק היום השלישי."},
                  {"id": "center", "name": "ירושלים והגדה המערבית", "short": "מרכז", "view": [[31.4, 34.6], [32.5, 35.7]],
                   "intro": "הכניסה לעיר העתיקה, כיבוש שכם, טול כרם ויריחו, והחטיבה הירושלמית דרומה לבית לחם ולגוש עציון.",
                   "note": "חברון נכבשה עם שחר 8 ביוני; היא לא מופיעה כאן כנכבשת."},
                  {"id": "golan", "name": "רמת הגולן והצפון", "short": "גולן", "view": [[32.8, 35.2], [33.4, 35.9]],
                   "intro": "ב-7 ביוני תקפו חיל האוויר והארטילריה את הצבא הסורי, והסורים הפגיזו את עמק החולה ועמק הירדן. בערב הגביל שר הביטחון את ההתקפה לגבול הבינלאומי.",
                   "note": "המלחמה היבשתית ברמת הגולן הוכרעה רק ב-9 וב-10 ביוני."}],
        "timeline": TL, "still_ts": {"all": 150, "sinai": 38, "center": 150, "golan": 53},
        "credit_notes": ["הקשר: היום השלישי של מלחמת ששת הימים - 7 ביוני 1967.",
                         "מה שלא מופיע: מוצבי ירדן שמדרום לירושלים, הג'יפתליק, בית סחור ומסלולי הטיסה. הערכים לא נותנים להם קואורדינטות, והם מצוירים סכמטית ומסומנים כך."]}
(DATA / "1967-06-07.json").write_text(json.dumps(PAGE, ensure_ascii=False, indent=1), encoding="utf-8")
CAS["articles"].update({"he_sharm": {"lang": "he", "title": "תפיסת שארם א-שייח' במלחמת ששת הימים", "revid": 39922591}})
F = lambda what, val, art, quote, qual="דיווח", scope="": {"what": what, "val": val, "art": art, "quote": quote, "qual": qual, "scope": scope}
D3 = [{"id": "e1", "area": "center", "clock": "07:00–09:05", "name": "מתחם אוגוסטה ויקטוריה",
       "il": [F("k", "1", "he_jer", "עם חלל אחד בלבד", scope="גדוד 66, עד 9:05")],
       "ar": [F("g", "אבדות כבדות (ללא מספר)", "he_jer", "והסבו למגינים הירדניים אבדות כבדות", "איכותי", "הפצצת חיל האוויר")], "t": LOGT["c2"], "at": "augusta"}]
CAS["data"]["jun7"] = D3
(DATA / "1967-casualties.json").write_text(json.dumps(CAS, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(ITEMS), "items,", len(SFX), "sound cues,", len(LOG), "log entries,", len(ACTS), "acts,", len(D3), "casualty events")
