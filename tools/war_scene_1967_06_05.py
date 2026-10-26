#!/usr/bin/env python3
"""Builds the animation scene of 5 June 1967 (the whole front, one clock) and writes it into war/data/1967-06-05-events.json under "scene".

Everything drawn is either a named place (Wikipedia coordinates, in D.places) or SCHEMATIC (bases, routes, arrows, firing positions, the areas
the articles only describe) and labelled so. No aircraft counts or times beyond what the articles state. Times here are animation seconds;
the clock label of each act is the article's own wording. Run: python3 tools/war_scene_1967_06_05.py
"""
import json
from pathlib import Path
F = Path(__file__).resolve().parent.parent / "war" / "data" / "1967-06-05-events.json"
D = json.loads(F.read_text(encoding="utf-8"))
P = {k: [v["lat"], v["lon"]] for k, v in D["places"].items()}
IL = [31.62, 34.93]                    # schematic IAF base ON LAND inland of the southern coast (no airfield named in the sources; the owner 2026-10-18: never on the sea)
SYB = [33.4, 36.6]                       # schematic Syrian base
JOB = [32.05, 35.75]                     # schematic Jordanian air base
JOF = [31.85, 35.38]                     # schematic Jordanian firing position east of Jerusalem
JOF2 = [32.1, 35.2]                      # schematic Jordanian guns facing the coast plain
IQB = [32.75, 36.75]                     # schematic start of the Iraqi Hunters (H-3 is far to the east)
SEA = [31.8, 33.4]
ITEMS, SFX = [], []
def add(it): ITEMS.append(it); return it
def sfx(t, k): SFX.append([round(t, 2), k])
def sortie(key, label, target, t0, t_hit, t_back, area, base=IL, side="iaf", via=None, boomk=True, off=None):
    path = [base] + ([via] if via else []) + [target]
    add({"type": "fly", "side": side, "label": label, "area": area, "off": off, "legs": [{"t0": t0, "t1": t_hit, "path": path}, {"t0": t_hit + 0.3, "t1": t_back, "path": list(reversed(path))}]})
    sfx(t0 + .3, "jet")
    if boomk:
        add({"type": "boom", "at": target, "t": t_hit, "dur": 1.4, "big": 1, "area": area}); sfx(t_hit, "boom")
# ---- act 1: Operation Focus, first wave (07:45-09:05) ----
tg = [("arish", "אל-עריש"), ("jebel", "ג'בל ליבני"), ("gif", "ביר גפגפה"), ("tam", "ביר תמדה"), ("suweir", "אבו סואר"), ("fayid", "פאיד"), ("kabrit", "כברית"), ("cairo", "קהיר")]
for i, (k, nm) in enumerate(tg):
    sortie("f" + k, "מטס מבצע מוקד (סכמטי)" if i == 0 else None, P[k], 0.6 + 0.25 * i, 6.5 + 0.35 * i, 12 + 0.4 * i, "sinai", via=SEA if k not in ("arish",) else [31.5, 34.1])
# ---- act 2: Fouga trainers on the forward area (~08:00) ----
sortie("fouga", "פוגה מגיסטר (סכמטי)", [31.2, 34.2], 12.5, 17.5, 22, "sinai")
add({"type": "boom", "at": [31.17, 34.28], "t": 18.5, "dur": 1.2, "area": "sinai"})
# ---- act 3: 08:15 ground attack, three divisions (schematic arrows) ----
LAH = [31.0, 33.85]
add({"type": "arrow", "path": [P["khan"], P["rafah"], P["arish"]], "t0": 22, "t1": 33, "label": "אוגדת טל: ציר החוף (סכמטי)", "color": "#1d5ea8", "hold": 30, "area": "sinai"})
add({"type": "arrow", "path": [P["nitz"], [30.95, 34.1], LAH], "t0": 22.5, "t1": 34, "label": "אוגדת יפה: דרך ואדי חרידין (סכמטי)", "color": "#1d5ea8", "hold": 30, "area": "sinai"})
add({"type": "arrow", "path": [P["nitz"], P["umm"], P["abu"]], "t0": 23, "t1": 34, "label": "אוגדת שרון: אום כתף – אבו עגילה (סכמטי)", "color": "#1d5ea8", "hold": 30, "area": "sinai"})
for i in range(4):
    add({"type": "boom", "at": [P["umm"][0] + .01 * i, P["umm"][1] - .02 * i], "t": 28 + 1.4 * i, "dur": 1.2, "area": "sinai"}); sfx(28 + 1.4 * i, "cannon")
# ---- act 4: 08:45 7th Brigade into Gaza at Khan Yunis ----
add({"type": "walk", "label": "חטיבה 7 (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 35, "t1": 38, "path": [[31.38, 34.42], P["khan"]]}, {"t0": 38, "t1": 44, "path": [P["khan"], P["rafah"]]}], "area": "sinai"})
for i in range(2): add({"type": "boom", "at": [P["khan"][0] + .01 * i, P["khan"][1]], "t": 37 + 1.2 * i, "dur": 1.2, "area": "sinai"}); sfx(37 + 1.2 * i, "cannon")
# ---- act 5: 09:40 Jordan opens fire on Jerusalem and Mount Scopus ----
add({"type": "shell", "from": JOF, "to": P["jer"], "t0": 45, "t1": 53, "period": 1.3, "lift": .04, "area": "center"})
add({"type": "shell", "from": [31.9, 35.3], "to": P["mevaseret"], "t0": 46, "t1": 53, "period": 1.5, "lift": .05, "area": "center"})
add({"type": "boom", "at": P["scopus"], "t": 47, "dur": 1.2, "area": "center"}); add({"type": "boom", "at": P["jer"], "t": 49.5, "dur": 1.2, "area": "center"})
for t in (46, 48, 50, 52): sfx(t, "cannon")
# ---- act 6: ~10:00 barrage on Tel Aviv, Ramat David, west Jerusalem ----
add({"type": "shell", "from": JOF2, "to": P["tlv"], "t0": 55, "t1": 63, "period": 1.6, "lift": .04, "area": "center"})
add({"type": "shell", "from": [32.45, 35.3], "to": P["ramd"], "t0": 55, "t1": 63, "period": 1.7, "lift": .04, "area": "center"})
add({"type": "shell", "from": JOF, "to": P["jer"], "t0": 55, "t1": 63, "period": 1.4, "lift": .04, "area": "center"})
for k, t in (("tlv", 58), ("ramd", 59.5), ("jer", 61)): add({"type": "boom", "at": P[k], "t": t, "dur": 1.3, "area": "center"}); sfx(t, "thud")
# ---- act 7: 11:40 airfields shelled, Hunters on Netanya and Kfar Saba ----
for k, t in (("lod", 66), ("ramd", 67.5)): add({"type": "boom", "at": P[k], "t": t, "dur": 1.3, "area": "center"}); sfx(t, "thud")
sortie("hn", "הנטרים ירדניים (סכמטי)", P["netanya"], 64.5, 69, 74, "center", base=JOB, side="ar")
sortie("hk", None, P["kfs"], 65, 69.8, 74, "center", base=JOB, side="ar", off=[0.03, 0.03])
# ---- act 8: 11:50 twelve Syrian MiGs ----
mig = [{"t0": 76, "t1": 79.5, "path": [SYB, P["degania"]]}, {"t0": 79.5, "t1": 81.5, "path": [P["degania"], P["hores"]]}, {"t0": 81.5, "t1": 83, "path": [P["hores"], P["megiddo"]]}, {"t0": 83.5, "t1": 89, "path": [P["megiddo"], P["hores"], SYB]}]
add({"type": "fly", "side": "ar", "label": "12 מיגים סוריים (הכמות לפי הערך)", "legs": mig, "area": "golan"}); sfx(76.3, "jet")
for k, t in (("degania", 79.5), ("hores", 81.5), ("megiddo", 83)): add({"type": "boom", "at": P[k], "t": t, "dur": 1.3, "area": "golan"}); sfx(t, "boom")
# ---- act 9: 11:55 L-charges ----
for k, t in (("abutor", 90), ("zion", 91.2), ("mandel", 92.4)): add({"type": "boom", "at": P[k], "t": t, "dur": 1.4, "big": 1, "area": "center"}); sfx(t, "boom")
# ---- act 11: 12:45 third wave on Syrian and Jordanian airfields (areas only, locations not given) ----
SYA, JOA = [33.35, 36.35], [31.95, 36.1]
sortie("w3s", "חיל האוויר: שדות התעופה בסוריה (סכמטי)", SYA, 104, 111, 116, "golan", via=[32.9, 35.2])
sortie("w3j", "חיל האוויר: שדות התעופה בירדן (סכמטי)", JOA, 104.5, 110.5, 116, "center", via=[32.2, 35.0])
# ---- act 12: noon, Rafah ----
add({"type": "walk", "label": "אוגדה 84 (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 117, "t1": 126, "path": [[31.36, 34.45], P["rafah"]]}], "area": "sinai"})
add({"type": "walk", "label": "חטיבה 60 (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 118, "t1": 127, "path": [[31.12, 34.3], [31.18, 34.15]]}], "area": "sinai"})
for i in range(5): add({"type": "boom", "at": [P["rafah"][0] + .008 * (i % 3) - .008, P["rafah"][1] + .01 * (i % 2)], "t": 119 + 1.5 * i, "dur": 1.2, "area": "sinai"}); sfx(119 + 1.5 * i, "cannon" if i % 2 else "thud")
# ---- act 13: 13:30 Jordanians take Government House ----
GOV = P["gov"]
add({"type": "walk", "label": "פלוגה ירדנית (סכמטי)", "cls": "syr", "sym": "▣", "legs": [{"t0": 130, "t1": 136, "path": [[31.752, 35.30], GOV]}], "area": "center"}); add({"type": "boom", "at": GOV, "t": 136, "dur": 1.3, "area": "center"}); sfx(136, "cannon")
add({"type": "mark", "at": GOV, "t0": 136.5, "t1": 156, "label": "ארמון הנציב: נכבש בידי הירדנים", "area": "center"})
# ---- act 14: 14:30 Iraqi Hunters on Nahalal ----
sortie("iq", "הנטרים עיראקיים (סכמטי)", P["nahalal"], 140, 145, 150, "center", base=IQB, side="ar")
# ---- act 15: 15:00 Jiradi complex ----
JIR = [lerp for lerp in [P["rafah"][0] + .55 * (P["arish"][0] - P["rafah"][0]), P["rafah"][1] + .55 * (P["arish"][1] - P["rafah"][1])]]
add({"type": "walk", "label": "כוח ישראלי ראשון (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 152, "t1": 160, "path": [P["rafah"], JIR]}], "area": "sinai"})
add({"type": "mark", "at": JIR, "t0": 160, "t1": 172, "label": "מתחם הג'יראדי (סכמטי)", "area": "sinai"})
for i in range(4): add({"type": "boom", "at": [JIR[0] + .006 * i, JIR[1] - .008 * i], "t": 160 + 1.8 * i, "dur": 1.2, "area": "sinai"}); sfx(160 + 1.8 * i, "cannon")
# ---- act 16: 15:10 counter-attack on Government House ----
add({"type": "walk", "label": "חטיבת ירושלים (סכמטי)", "cls": "iaf", "sym": "▣", "legs": [{"t0": 160, "t1": 164, "path": [[31.738, 35.225], GOV]}], "area": "center"})
add({"type": "boom", "at": GOV, "t": 164, "dur": 1.5, "big": 1, "area": "center"}); sfx(164, "boom")
add({"type": "walk", "label": "הכוח הירדני נסוג (סכמטי)", "cls": "syr", "sym": "▣", "legs": [{"t0": 164.5, "t1": 170, "path": [GOV, [31.76, 35.33]]}], "area": "center"})
# ---- act 17: afternoon, compound 181 ----
C181 = [30.93, 34.235]
add({"type": "arrow", "path": [[30.88, 34.28], C181], "t0": 172, "t1": 178, "label": "כוח ניר (סכמטי)", "color": "#1d5ea8", "hold": 10, "area": "sinai"})
sortie("n181", "חיל האוויר (סכמטי)", C181, 173, 178, 183, "sinai")
# ---- act 18: 17:15 Harel brigade ----
add({"type": "arrow", "path": [[31.80, 35.04], P["tul"]], "t0": 184, "t1": 192, "label": "חטיבת הראל (סכמטי)", "color": "#1d5ea8", "hold": 14, "area": "center"})
for i in range(3): add({"type": "boom", "at": [P["tul"][0] - .01 * i, P["tul"][1] - .02 * i], "t": 188 + 1.2 * i, "dur": 1.2, "area": "center"}); sfx(188 + 1.2 * i, "cannon")
# ---- act 19: night, Yoffe at Bir Lahfan + Gaza ----
for i in range(4): add({"type": "boom", "at": [LAH[0] + .02 * (i % 2), LAH[1] + .02 * (i // 2)], "t": 198 + 1.3 * i, "dur": 1.2, "area": "sinai"}); sfx(198 + 1.3 * i, "cannon")
add({"type": "boom", "at": P["gaza"], "t": 199, "dur": 1.4, "area": "sinai"}); add({"type": "boom", "at": P["gaza"], "t": 203, "dur": 1.4, "area": "sinai"})
# ---- act 20: midnight, the Syrian plan is cancelled ----
add({"type": "arrow", "path": [[33.15, 35.95], [32.95, 35.7]], "t0": 207, "t1": 211, "label": "תוכנית ההתקפה הסורית (בוטלה; סכמטי)", "color": "#b3261e", "hold": 6, "area": "golan"})
# ---- act 21: 22:00-22:40 Umm Katef night attack ----
add({"type": "arrow", "path": [[30.86, 34.2], P["umm"]], "t0": 215, "t1": 222, "label": "חטיבת חי\"ר 99 (סכמטי)", "color": "#1d5ea8", "hold": 14, "area": "sinai"})
for i in range(12): add({"type": "boom", "at": [P["umm"][0] + .012 * ((i * 7) % 5 - 2) / 2, P["umm"][1] + .012 * ((i * 3) % 5 - 2) / 2], "t": 216 + .55 * i, "dur": 1.0, "area": "sinai"}); sfx(216 + .55 * i, "thud" if i % 3 else "cannon")
# ---- act 22: 02:15-02:30 (6 June) Ammunition Hill begins ----
add({"type": "arrow", "path": [[31.795, 35.205], P["ammo"]], "t0": 229, "t1": 233, "label": "חטיבה 55 (סכמטי)", "color": "#1d5ea8", "hold": 10, "area": "center"})
for i in range(3): add({"type": "boom", "at": [P["ammo"][0] + .003 * i, P["ammo"][1] - .004 * i], "t": 231 + 1.0 * i, "dur": 1.1, "area": "center"}); sfx(231 + i, "cannon")
for t in (126.2, 160.5): sfx(t, "cannon")
V = {"all": [[29.9, 32.0], [33.7, 36.8]], "sinai": [[29.9, 32.0], [31.8, 34.8]], "center": [[31.5, 34.6], [32.9, 35.8]], "golan": [[32.2, 34.9], [33.6, 36.7]]}
A_ = lambda s, e, c, v: {"s": s, "e": e, "clock": c, "view": V[v], "caps": []}
ACTS = [A_(0, 12, "07:45 · מבצע מוקד", "sinai"), A_(12, 22, "כ-08:00", "sinai"), A_(22, 35, "08:15 · סדין אדום", "sinai"), A_(35, 45, "08:45 · רצועת עזה", "sinai"),
        A_(45, 55, "09:40 · ירושלים", "center"), A_(55, 64, "כ-10:00 · הפגזה", "center"), A_(64, 76, "11:40 · שדות תעופה", "center"), A_(76, 90, "11:50 · מיגים סוריים", "golan"),
        A_(90, 96, "11:55 · מטעני ל'", "center"), A_(96, 104, "12:00-13:30", "center"), A_(104, 117, "12:45 · הגל השלישי", "all"), A_(117, 130, "בצהריים · רפיח", "sinai"),
        A_(130, 140, "13:30 · ארמון הנציב", "center"), A_(140, 152, "14:30 · נהלל", "center"), A_(152, 160, "15:00 · הג'יראדי", "sinai"), A_(160, 172, "15:10 · ארמון הנציב", "center"),
        A_(172, 184, "אחר הצהריים · מתחם 181", "sinai"), A_(184, 196, "17:15 · חטיבת הראל", "center"), A_(196, 206, "בלילה · ביר לחפן ועזה", "sinai"), A_(206, 214, "חצות · סוריה", "golan"),
        A_(214, 228, "22:00-22:40 · אום כתף", "sinai"), A_(228, 240, "02:30 (6 ביוני) · גבעת התחמושת", "center")]
LT = {"sinai": [0.5, 7, 12.5, 22, 26, 35, 119, 152, 172, 198, 201, 216], "center": [1, 45, 55, 66, 90, 97, 99, 130, 160, 184, 214, 229],
      "golan": [2, 76, 104, 111, 207]}
tl = D.get("_tl")
meta = json.loads((F.parent / "1967-06-05.json").read_text(encoding="utf-8"))
cnt = {"sinai": 0, "center": 0, "golan": 0}; LOG = []
for e in meta["timeline"]:
    a = e["area"]; t = LT[a][cnt[a]]; cnt[a] += 1
    LOG.append({"t": t, "clock": e["clock"], "q": e["text"], "n": e["place"], "area": a})
D["scene"] = {"dur": 240, "view0": V["all"], "acts": ACTS, "log": LOG, "sfx": SFX, "items": ITEMS,
              "bases": [{"pos": IL, "label": "בסיס חיל האוויר"}, {"pos": SYB, "label": "בסיס סורי"}, {"pos": JOB, "label": "בסיס ירדני"}],
              "areas": [{"name": "שדות תעופה בסוריה", "center": SYA, "radius_m": 30000, "label": "שדות התעופה בסוריה (סכמטי; לא צוינו)"}, {"name": "שדות תעופה בירדן", "center": JOA, "radius_m": 30000, "label": "שדות התעופה בירדן (סכמטי; לא צוינו)"},
                        {"name": "מוצבי האש הירדנית", "center": JOF, "radius_m": 8000, "label": "מקור האש הירדנית (סכמטי; לא צוין)"}],
              "show_places": ["rafah", "khan", "arish", "umm", "abu", "gaza", "jer", "scopus", "gov", "ammo", "tul", "netanya", "kfs", "nahalal", "ramd", "lod", "tlv", "megiddo", "degania", "hores", "nitz"]}
# ---- ground-unit trails (the owner 10-18): tank = caterpillar tracks, foot = boot prints; by the unit's own label (armour/infantry as the article describes the force)
TRAIL = [("חטיבה 7", "tank"), ("אוגדה 84", "tank"), ("חטיבה 60", "tank"), ("פלוגה ירדנית", "foot"), ("כוח ישראלי ראשון", "tank"), ("חטיבת ירושלים", "tank"), ("הכוח הירדני נסוג", "foot"),
         ("אוגדת טל", "tank"), ("אוגדת יפה", "tank"), ("אוגדת שרון", "tank"), ("כוח ניר", "tank"), ("חטיבת הראל", "tank"), ('חטיבת חי"ר 99', "foot"), ("חטיבה 55", "foot")]
for it_ in ITEMS:
    if it_["type"] in ("walk", "arrow") and "בוטלה" not in (it_.get("label") or ""):
        for key_, kind_ in TRAIL:
            if (it_.get("label") or "").startswith(key_):
                it_["trail"] = kind_; break
# ---- control layer (the owner 10-18: "when the forces advance show how Israel's borders expand"): SCHEMATIC. Start state = Israel inside the 1949
# armistice lines drawn by hand (no external boundary data; labelled schematic). Growth only where the article's own log says Israeli forces
# entered/took a named place on day 1: Khan Yunis (t35), Rafah (southern positions only AFTER DARK, t199+; at noon t119 it was an attack with heavy losses, not control), Government House retaken (t160). Nothing else.
# Not shown as Israeli control: Jiradi (the Egyptians re-took the block), Gaza city, Umm Katef (decided on 6 June), Bir Lahfan (no coordinates).
IL49 = [[31.60, 34.55], [31.80, 34.62], [32.10, 34.75], [32.50, 34.90], [33.05, 35.10], [33.09, 35.55], [33.28, 35.58], [32.70, 35.57], [32.50, 35.52],
        [32.40, 35.05], [32.05, 34.98], [31.85, 35.04], [31.83, 35.10], [31.80, 35.215], [31.74, 35.215], [31.70, 35.12], [31.55, 34.95], [31.35, 35.05], [31.20, 35.15], [30.50, 35.15], [29.55, 34.95],
        [30.00, 34.77], [30.90, 34.35], [31.22, 34.27], [31.35, 34.37], [31.50, 34.50]]
CONTROL = {"label": "קו חזית משוער, לא גבול מדויק", "base": {"poly": IL49, "label_at": [30.55, 35.0], "label": "ישראל בקווי שביתת הנשק 1949 (קו סכמטי)"},
           "grow": [{"id": "khan", "center": P["khan"], "radius_m": 5000, "t0": 35, "t1": 48, "area": "sinai", "label": "קו חזית משוער: ח'אן יונס"},
                    {"id": "rafah", "center": P["rafah"], "radius_m": 3500, "t0": 199, "t1": 210, "area": "sinai", "label": "קו חזית משוער: רפיח, המוצבים הדרומיים (אחרי החשכה)"},
                    {"id": "gov", "center": P["gov"], "radius_m": 1100, "t0": 160, "t1": 170, "area": "center", "label": "קו חזית משוער: ארמון הנציב"}]}
D["scene"]["control"] = CONTROL
D["scene"]["icons"] = True   # one icon per kind of force + black place dots (the owner 2026-10-19; 5 June first, the other days follow after his yes)
F.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(ITEMS), "items,", len(SFX), "sound cues,", len(LOG), "log entries,", len(ACTS), "acts")
