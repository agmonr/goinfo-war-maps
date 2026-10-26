"""The whole Six-Day War (5-10 June 1967) as ONE map page: the six per-day scenes joined on one continuous timeline.

    python3 tools/war_whole_build.py --stage DIR        -> DIR/war/1967/six-days/{map/index.html, events.json, daynight.js, land-mask.json}

A TEST page (the owner 10-22): noindex, no sitemap line, no link from anywhere. Nothing new is researched - every card, move, wreck and casualty record comes from the
per-day files (war/data/1967-06-05..10-events.json); this only (1) shifts each day's animation clock by the days before it, (2) gives every act its absolute
simulated minute (day*1440 + minute of day) so the sun layer follows the real date, (3) prefixes act and log clocks with the day. The progress bar and its
marks are drawn by the template when events.json carries "whole".
"""
import argparse, copy, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import war_build as wb

ROOT = wb.ROOT
DAYS = [("1967-06-05", "jun"), ("1967-06-06", "jun6"), ("1967-06-07", "jun7"), ("1967-06-08", "jun8"), ("1967-06-09", "jun9"), ("1967-06-10", "jun10")]
WORDS = [("אחר הצהריים", 930), ("לפנות בוקר", 300), ("עם שחר", 330), ("בצהריים", 750), ("צהריים", 750), ("בבוקר", 480), ("בוקר", 480), ("הערב", 1140), ("ערב", 1140), ("בלילה", 1320), ("חצות", 1440)]
GAP = 6        # animation units of pause between two days (the day change is not drawn as action)


def day_minutes(acts):
    """Port of simPts() in battle-map.html: the simulated minute of each act's start, monotone. 'בלילה' on the first act of a day that goes on with a small-hours
    time is the small hours of THAT date, not 22:00 (the single-day page has the same quirk; here it would put the day's start after its own end)."""
    pts, prev = [], -1
    for i, a in enumerate(acts):
        c = str(a.get("clock") or "").split("·")[0]
        m = None
        t = re.search(r"(\d{1,2}):(\d{2})", c)
        if t:
            m = int(t.group(1)) * 60 + int(t.group(2))
        else:
            for w, v in WORDS:
                if w in c:
                    m = v
                    break
        if m is not None and m >= 1200 and "בלילה" in c and not t and prev < 720:
            m = 30 + 10 * i          # 'at night' before any daytime act is the small hours of this date, not 22:00
        if m is not None:
            if prev >= 0 and m < prev - 300:
                m += 1440
            prev = m
        pts.append([a["s"], m])
    known = [i for i, p in enumerate(pts) if p[1] is not None]
    vals = [None] * len(pts)
    for i, p in enumerate(pts):
        if p[1] is not None:
            vals[i] = p[1]
            continue
        lo = max((j for j in known if j < i), default=None)
        hi = min((j for j in known if j > i), default=None)
        if lo is not None and hi is not None:
            vals[i] = pts[lo][1] + (pts[hi][1] - pts[lo][1]) * (p[0] - pts[lo][0]) / max(1e-6, pts[hi][0] - pts[lo][0])
        elif lo is not None:
            vals[i] = pts[lo][1] + (p[0] - pts[lo][0]) * 0.7
        else:
            vals[i] = pts[hi][1] - (pts[hi][0] - p[0]) * 0.7
    mx = -1e9
    for i, v in enumerate(vals):
        if v < mx:
            v = mx + 0.01
        mx = v
        vals[i] = v
    return vals


def shift_item(it, d):
    for k in ("t", "t0", "t1"):
        if isinstance(it.get(k), (int, float)):
            it[k] += d
    for lg in it.get("legs") or []:
        for k in ("t0", "t1"):
            if isinstance(lg.get(k), (int, float)):
                lg[k] += d
    return it


# the owner 10-23/24 (rule for ALL war pages: no talks / diplomacy): three Six-Day cards are diplomacy only and are dropped from the merged page - the UN-observer ceasefire attempt (5.6), Syria's ceasefire
# announcement and the Security Council diplomacy (9.6). Per day: the card ids, the act start times and the log times that belong to them (the day files stay as authored). The four cards that change where
# forces stop or go (d3-c0, d4-s6, d6-g3, d6-g9) stay.
DROP = {"1967-06-05": {"cards": {"c5"}, "acts": {96}, "log": {97}}, "1967-06-09": {"cards": {"g0", "g13"}, "acts": {10, 200}, "log": {12, 204}}}


def merge(data, cas):
    evs = [json.loads((data / f"{d}-events.json").read_text(encoding="utf-8")) for d, _ in DAYS]
    base = copy.deepcopy(evs[0])
    out = {k: base[k] for k in ("source", "views", "still_views", "view", "area_filter") if k in base}
    out["cards_title"] = "ששת הימים: כל המלחמה"
    places, events, items, acts, log, sfx, grow, bases, areas, show, casualties, days = {}, [], [], [], [], [], [], [], [], [], [], []
    T0, prev_min = 0.0, 0.0
    for n, ((date, ckey), e) in enumerate(zip(DAYS, evs)):
        e = copy.deepcopy(e)
        wb.add_place_sides(e, wb._il_taken(data, date)); wb._icons_on(e, date)
        s = e["scene"]
        label = f"{int(date[8:])}.{int(date[5:7])}"
        for k, v in e["places"].items():
            places.setdefault(k, v)
        mins = day_minutes(s["acts"])
        drop = DROP.get(date, {})
        for a, m in zip(s["acts"], mins):
            if a["s"] in drop.get("acts", ()):               # a dropped (diplomacy) act: the previous act simply runs on over it
                if acts: acts[-1]["e"] = a["e"] + T0
                continue
            a2 = dict(a); a2["s"] += T0; a2["e"] += T0
            absm = max(n * 1440 + min(m, 1439), prev_min + 0.01); prev_min = absm
            a2["min"] = absm
            a2["clock"] = f"יום {n + 1} ({label}) · {a['clock']}"
            acts.append(a2)
        for it in s["items"]:
            it2 = shift_item(copy.deepcopy(it), T0)
            if it2.get("type") in ("arrow", "walk", "fly", "shell"):
                it2["u"] = T0 + s["dur"]        # a unit marker is carried to the end of ITS day, not into the next (the per-day pages do the same)
            items.append(it2)
        for l in s["log"]:
            if l["t"] in drop.get("log", ()): continue
            l2 = dict(l); l2["t"] += T0; l2["clock"] = f"{label} · {l['clock']}"; log.append(l2)
        sfx += [[t + T0, k] for t, k in s["sfx"]]
        for g in (s.get("control") or {}).get("grow", []):
            g2 = dict(g)
            for k in ("t0", "t1"):
                if isinstance(g2.get(k), (int, float)):
                    g2[k] += T0
            if not any(x.get("id") == g2.get("id") for x in grow):
                grow.append(g2)
        bases += [b for b in s.get("bases", []) if b not in bases]
        areas += [b for b in s.get("areas", []) if b not in areas]
        show += [p for p in s.get("show_places", []) if p not in show]
        for c in wb.casualties_anim(cas, ckey, e["places"]):
            c["t"] += T0; c["clock"] = f"{label} · {c['clock']}"
            casualties.append(c)
        for c in e["events"]:
            if c["id"] in drop.get("cards", ()): continue
            c2 = dict(c); c2["id"] = f"d{n + 1}-{c['id']}"
            for k in ("start_min", "end_min"):
                if isinstance(c2.get(k), (int, float)):
                    c2[k] += n * 1440
            c2["t"] = f"{label} {c.get('t', '')}".strip(); c2["time_label"] = f"{label} {c.get('time_label', '')}".strip()
            events.append(c2)
        days.append({"n": n + 1, "label": label, "T0": T0, "min0": n * 1440, "dur": s["dur"], "date": date})
        T0 += s["dur"] + GAP
    ctl = copy.deepcopy(evs[0]["scene"]["control"]); ctl["grow"] = grow
    cas_t = {}
    for (date, ckey), e in zip(DAYS, evs):
        pass
    out["places"] = places
    out["areas"] = evs[0]["areas"]
    out["events"] = events
    out["time_range"] = [0, 6 * 1440]
    out["scene"] = {"dur": T0 - GAP, "view0": evs[0]["scene"]["view0"], "acts": acts, "log": log, "sfx": sfx, "items": items, "bases": bases, "areas": areas,
                    "show_places": show, "control": ctl, "icons": True}
    # cas_t (record id -> hit time) belongs to the day it was written for
    off = 0.0
    for (date, ckey), e in zip(DAYS, evs):
        for k, v in (e["scene"].get("cas_t") or {}).items():
            out["scene"].setdefault("cas_t", {})[k] = v + off
        off += e["scene"]["dur"] + GAP
    out["casualties"] = casualties
    out["whole"] = {"date0": DAYS[0][0], "days": days}
    if AUDIT_MARKS:
        audit_marks(out)
    if LABEL_FIX:
        label_fix(out)
    if BATTLE_FILL:
        import war_battle_fill
        war_battle_fill.fill(out, {"il": "כוח צה״ל בקרב", "ar": "הכוח הערבי בקרב"})
    if BATTLE_FIRE:
        import war_battle_fire
        war_battle_fire.fire(out)   # R36: both sides fire at each other (the owner 10-26)
    if INTRO_SCREEN:
        out["intro"] = SIX_INTRO     # R48 opening screen (the owner 10-26); figures from war/data/1967-casualties.json, each side's ranges as the sources give them
    if SOURCE_LINKS:
        mp = ROOT / "war" / "data" / "1967-source-links.json"      # made by `war_source_links.py --map` (network at authoring time, none at deploy)
        if mp.exists():
            m = json.loads(mp.read_text(encoding="utf-8")); curl = set(m.pop("_current", [])); byt = {}; byq = {}; curq = set()
            for c in out["events"]:
                if c["id"] in m:
                    c["source_url"] = m[c["id"]]; byt[c["title"]] = m[c["id"]]; byq[c["quote"]] = m[c["id"]]
                    if c["id"] in curl: c["source_cur"] = 1; curq.add(c["quote"])      # re-pinned to the CURRENT article text: our card summarises that passage, it is not a verbatim quote of the pinned revision
            for l in out["scene"]["log"]:
                h = byq.get(l.get("q")) or byt.get(l.get("n"))
                if h:
                    l["href"] = h
                    if l.get("q") in curq: l["hcur"] = 1
    if STOPPED:
        import war_stopped
        for c in out["events"]:
            if c["id"] in STOP_EXEMPT: c["stopped_ok"] = STOP_EXEMPT[c["id"]]
        war_stopped.apply(out, STOPS, area="sinai")    # R49 (the owner 10-26): נבלם = destroyed, בולמת = both sides lose, מאמץ עליון = very heavy
    if SHOOTERS:
        import war_shooters
        war_shooters.apply(out)      # R51 (the owner 10-26): a shoot-down comes after the shooting side's aircraft arrived, with fire before the fall
    if SURRENDER_FLAG:
        import war_surrender
        war_surrender.fill(out)    # R43: a white flag over every surrender report (the owner 10-26)
    if PUSHOUT:
        import war_pushout
        out['pushout_specs'] = PUSHOUT_SPECS
        war_pushout.apply(out, PUSHOUT_SPECS)   # R45: a force a card says withdrew/was pushed out LEAVES the area (the owner 10-26)
        import war_retreat, war_landcheck
        war_retreat.apply(out, war_landcheck.load_mask())      # R50: the retreat is a disorderly group, gun toward the enemy (template), some hit on the way (seeded)
    if FOOT_EXPIRY:
        import war_foot_expiry
        war_foot_expiry.apply(out)   # R44: a foot unit leaves the map 6 simulated hours after its last update (the owner 10-26)
    if SFX_COVER:
        import war_sfx
        war_sfx.cover(out["scene"])    # R40: every noisy item has a cue
    return out


AUDIT_MARKS = True   # the owner 10-26 event audit: a card with a place and nothing drawn there at its time gets a labelled marker at its own place (separate commit, so the owner can pick)
BATTLE_FIRE = True   # LAW R36 (the owner 10-26): a battle is visible - both sides fire at each other, impacts, contact (separate flag/commit)
INTRO_SCREEN = True    # R48 opening screen with war name, dates, casualties of both sides (separate flag)
SIX_INTRO = {"title": "מלחמת ששת הימים", "dates": "5–10 ביוני 1967",
             "sides": [{"k": "il", "name": "ישראל", "lines": ["הרוגים 776–983 (כ-780 לפי הערך העברי; 776–983 בערבי; פחות מ-1,000 באנגלי)", "פצועים כ-2,590 (עברי) · 4,517 (ערבי)"]},
                       {"k": "ar", "name": "מצרים, ירדן, סוריה ועיראק", "lines": ["הרוגים 15,000–25,000 (טווח הערכות; מצרים לבדה 10,000–15,000)", "אין נתון אחיד לפצועים ולשבויים בערכים שמצוטטים"]}],
             "src": {"t": "ויקיפדיה: מלחמת ששת הימים (הגרסה המצוינת) ועוד ערכים בטבלת האבדות", "u": "https://he.wikipedia.org/w/index.php?title=%D7%9E%D7%9C%D7%97%D7%9E%D7%AA_%D7%A9%D7%A9%D7%AA_%D7%94%D7%99%D7%9E%D7%99%D7%9D&oldid=44044273"},
             "note": "מספרים משתנים בין מקורות - מוצגים כטווח"}
SOURCE_LINKS = True    # R47 card titles link to the source passage (separate flag)
SHOOTERS = True     # R51 (separate flag): shooters arrive before every shoot-down
STOPPED = True    # R49 (separate flag): the stopped / holds / very-heavy families (tools/war_keywords.py)
STOPS = [{"card": "d2-s0", "fam": "hold", "side": "ar", "wrecks": 3, "dwrecks": 2}]      # brigade 520 holds the Egyptian tank battalion of brigade 114 at Jebel Libni: both sides lose
STOP_EXEMPT = {"d2-s3": "the same sentence says the Egyptian force withdrew to the Jebel Libni - Bir Hasana line: held, not destroyed (decision for the owner)",
               "d3-c10": "brigade 10 'נבלמו מחשש לפגיעה באגפם': a halt by the brigade's own caution, no enemy action: no destruction"}
SURRENDER_FLAG = True   # R43 white flag, 2 simulated hours, over each surrender report (separate flag)
PUSHOUT = True       # R45 (separate flag): units of a side leave the area its card says it was driven from
PUSHOUT_SPECS = [   # our reading of the cards: area boxes are approximate (labelled retreats), destinations are the side's own lines
    {"card": "d2-s7", "side": "ar", "box": [[29.6, 32.55], [31.3, 34.35]], "to": [30.4, 32.2]},      # general Egyptian withdrawal across the Suez canal
    {"card": "d2-c11", "side": "ar", "box": [[31.4, 34.9], [32.6, 35.6]], "to": [31.9, 35.95]},     # Jordan orders the withdrawal from the West Bank
    {"card": "d6-g1", "side": "ar", "box": [[32.55, 35.55], [33.25, 35.97]], "to": [33.25, 36.42]}, # withdrawal order to the Syrian army (the Golan)
]
FOOT_EXPIRY = True   # R44 foot units expire 6 simulated hours after their last update (separate flag)
SFX_COVER = True     # R40: sound cue for every noisy item (separate flag/commit)
BATTLE_FILL = True   # LAW R35 (the owner 10-26): every battle card animates both sides at its place; the missing side is drawn schematically (separate commit)
LABEL_FIX = True     # checklist 14: every moving symbol says (סכמטי) (separate commit)


def audit_marks(out):
    import math
    import test_war_event_shown as es
    sc, places, n = out["scene"], out["places"], 0
    for c in out["events"]:
        pl = [(places[g["place"]]["lat"], places[g["place"]]["lon"]) for g in c.get("geometry", []) if g.get("place") in places]
        if not pl:
            continue
        cand = [x for x in sc["acts"] if x.get("min") is not None]
        a = min(cand, key=lambda x: abs(x["min"] - c["start_min"]), default=None)
        if not a or abs(a["min"] - c["start_min"]) > 90:
            continue
        live = [it for it in sc["items"] if es.span(it)[1] >= a["s"] and a["s"] - 0.5 <= es.span(it)[0] + (6 if it["type"] in ("walk", "fly", "arrow") else 0) <= a["s"] + es.WIN]   # NEW at the card's time (what the browser audit counts), not a unit already standing there
        if any(math.hypot(p[0] - la, p[1] - lo) <= es.R for it in live for p in es.pts(it) for la, lo in pl):
            continue
        src = c.get("src") or {}
        sc["items"].append({"type": "mark", "at": [round(pl[0][0], 5), round(pl[0][1], 5)], "t0": round(a["s"] + 0.2, 2), "t1": round(a["s"] + 9, 2), "label": c["title"][:90], "area": c.get("area") or "all",
                            "q": c["quote"][:300], "s": src.get("s") or "", "audit": 1})
        n += 1
    out["audit_marks"] = n


def label_fix(out):
    for it in out["scene"]["items"]:
        if it["type"] in ("walk", "fly") and "סכמטי" not in (it.get("label") or "") and not it.get("sk") and it.get("label"):
            it["label"] += " (סכמטי)"


def build(stage):
    """write the six-days page into STAGE/war/1967/six-days/ (called by war_build.main, and by main() below for a stand-alone LAN stage)"""
    data = ROOT / "war" / "data"
    cas = json.loads((data / "1967-casualties.json").read_text(encoding="utf-8"))
    ev = merge(data, cas)
    out = Path(stage) / "war" / "1967" / "six-days"
    b = {"date": DAYS[0][0], "title": "ששת הימים: כל המלחמה על מפה אחת", "h1": "ששת הימים", "description": "כל מלחמת ששת הימים, 5-10 ביוני 1967, על ציר זמן אחד: מפה ואנימציה סכמטית.",
         "context": "מפה ואנימציה סכמטית.", "credit_notes": ["ששת הימים כולה על ציר זמן אחד, מחוברת מנתוני ששת הימים. אין בה נתון שאינו בנתוני הימים."], "src_bar": wb.src_bar(ev)}
    template = (ROOT / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
    wb.write(out / "map" / "index.html", wb.map_page(template, b, "https://goinfo.co.il/war/1967/six-days/map/", "../events.json", "anim", wb.credit_html(b, ev, cas, "jun")))
    wb.write(out / "events.json", json.dumps(ev, ensure_ascii=False, indent=1))
    import ga_inject      # a stand-alone LAN stage has no /src/: the inline host fallback keeps a twin out of GA (10-26), the same step war_build.py runs over its stage
    pg = out / "map" / "index.html"; pg.write_text(ga_inject.host_fallback(ga_inject.ensure(pg.read_text(encoding="utf-8"))), encoding="utf-8")
    for f in ("daynight.js", "land-mask.json"):
        (out / f).write_bytes((ROOT / "war" / f).read_bytes())
    return ev, out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True)
    a = ap.parse_args()
    ev, out = build(a.stage)
    print(f"wrote {out} - {len(ev['events'])} cards, {len(ev['scene']['items'])} scene items, dur {ev['scene']['dur']:.0f}")


if __name__ == "__main__":
    main()
