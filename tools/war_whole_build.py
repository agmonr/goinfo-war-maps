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
        for a, m in zip(s["acts"], mins):
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
    return out


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
