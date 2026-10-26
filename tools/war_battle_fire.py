"""LAW R36 helper (the owner 10-26: "in Yom Kippur you see forces move but you do not see battles"): a battle is VISIBLE when, during the card's window, the two sides FIRE at each other: shell arcs (muzzle burst, arc, impact burst - the
same item as the Six-Day artillery) go from each side's force to the other's, impact bursts land on both, and the forces are within contact range. fire(ev) adds, for every battle card whose window has no fire of one side at
the other, reciprocal shells + impact bursts between the nearest pair of opposing items at the place, for the duration the card's act gives (6-14 scene-seconds). The data of the battle itself (who, where, how long) is the card's;
the arcs are schematic and the card says nothing more precise. The check is tools/test_war_fire.py."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es, test_war_heavy_losses as hl, test_war_battles as tb, war_landcheck as lc
_LM = []
def LM():
    if not _LM: _LM.append(lc.load_mask())
    return _LM[0]
CONTACT_AIR = 0.5    # air battles: contact range in degrees (fighters close fast)
CONTACT = 0.2     # degrees (~20 km): forces further apart than this are not in contact
def sides_pts(items, w0, w1):
    got = {"il": [], "ar": []}
    for it in items:
        a, b = es.span(it)
        if b < w0 or a > w1 or it["type"] in ("boom", "mark", "loss", "note", "sam", "shell"): continue
        sd = hl.side(it)
        if sd:
            for p in es.pts(it): got[sd].append((p, it))
    return got
def nearest_pair(got, where):
    best = None
    for pi, _ in got["il"]:
        for pa, _ in got["ar"]:
            d = math.hypot(pi[0] - pa[0], pi[1] - pa[1]); c = math.hypot((pi[0] + pa[0]) / 2 - where[0], (pi[1] + pa[1]) / 2 - where[1])
            if c <= tb.R and (best is None or d < best[0]): best = (d, pi, pa)
    return best
ANC = 0.12     # R53 (the owner 10-26: "the Hermon battle is drawn in the south-east of the Golan"): for a card WITH a place the fight is anchored there: both fighters of the chosen pair stand within ANC deg of the card place
def anchored_pair(got, where):
    best = None
    for pi, _ in got["il"]:
        if math.hypot(pi[0] - where[0], pi[1] - where[1]) > ANC: continue
        for pa, _ in got["ar"]:
            if math.hypot(pa[0] - where[0], pa[1] - where[1]) > ANC: continue
            d = math.hypot(pi[0] - pa[0], pi[1] - pa[1])
            if best is None or d < best[0]: best = (d, pi, pa)
    return best
def card_window(c, acts):
    cand = [x for x in acts if x.get("min") == c.get("start_min")]
    a = next((x for x in cand if c["title"][:12] in x["clock"]), None) or (cand[0] if cand else None)
    if not a:
        near = min((x for x in acts if x.get("min") is not None), key=lambda x: abs(x["min"] - c["start_min"]), default=None)
        a = near if near and abs(near["min"] - c["start_min"]) <= 90 else None
    return a
def has_fire(items, w0, w1, where, side_n, rad=None):
    """shells of both sides + a burst, inside the window and within R of the place"""
    sh = {"iaf": 0, "ar": 0}; bo = 0
    for it in items:
        if it["type"] == "shell" and it["t1"] >= w0 and it["t0"] <= w1 and (math.hypot(it["from"][0] - where[0], it["from"][1] - where[1]) <= (rad or tb.R) or math.hypot(it["to"][0] - where[0], it["to"][1] - where[1]) <= (rad or tb.R)):
            sh["iaf" if it.get("side") == "iaf" else "ar"] += 1
        if it["type"] == "boom" and w0 <= it["t"] <= w1 and math.hypot(it["at"][0] - where[0], it["at"][1] - where[1]) <= (rad or tb.R): bo += 1
    return sh["iaf"] > 0 and sh["ar"] > 0 and bo > 0
def where_of(c, ev, items, w0, w1):
    places = ev.get("places", {})
    pl = [(places[g["place"]]["lat"], places[g["place"]]["lon"]) for g in c.get("geometry", []) if g.get("place") in places]
    if pl: return pl[0]
    got = sides_pts(items, w0, w1)
    pr = nearest_pair(got, (0, 0)) if False else None
    best = None
    for pi, _ in got["il"]:
        for pa, _ in got["ar"]:
            d = math.hypot(pi[0] - pa[0], pi[1] - pa[1])
            if best is None or d < best[0]: best = (d, ((pi[0] + pa[0]) / 2, (pi[1] + pa[1]) / 2))
    return best[1] if best else None
def fire(ev):
    sc, n = ev["scene"], 0
    for c in ev["events"]:
        if not tb.BATTLE.search(c["title"] + " " + c["quote"]) or c.get("fight_ok"): continue
        a = card_window(c, sc["acts"])
        if not a: continue
        w0 = a["s"]; dur = min(max(a["e"] - a["s"], 6.0), 14.0); w1 = a["s"] + dur
        where = where_of(c, ev, sc["items"], w0, a["s"] + tb.WIN)
        if where is None: continue
        placed = bool([1 for g in c.get("geometry", []) if g.get("place") in ev.get("places", {})])
        fired = has_fire(sc["items"], w0, a["s"] + tb.WIN, where, 0, ANC if placed else None)
        got = sides_pts(sc["items"], w0, a["s"] + tb.WIN)
        pr = anchored_pair(got, where) if placed else nearest_pair(got, where)
        if placed and not pr: pr = (9e9, None, None)           # nobody of one side stands at the place: both sides are drawn there below
        if not pr: continue
        lim = CONTACT_AIR if c.get("unit") == "mig" else CONTACT
        if pr[0] > lim:      # the forces drawn are not in contact at the place: BOTH sides get a schematic force at the place (labelled), as in war_battle_fill
            t0u = a["s"] + 0.3
            wet = c.get("area") != "sea" and not lc.near_land(LM(), where)       # a place on the sea: ships, never soldiers (R52)
            for far in ("il", "ar"):
                pos = [round(where[0] + (0.012 if far == "il" else -0.012), 4), round(where[1] + 0.01, 4)]
                if c.get("area") != "sea" and not wet: pos = [round(x, 4) for x in lc.snap(LM(), pos)]      # a force on land stands on land (checklist 17)
                sc["items"].append({"type": "walk", "label": (("ספינה ישראלית בקרב" if far == "il" else "ספינת הצד השני בקרב") if (c.get("area") == "sea" or wet) else ("כוח ישראלי בקרב" if far == "il" else "כוח הצד השני בקרב")) + " (סכמטי, מיקום משוער)", "cls": "iaf" if far == "il" else "syr", "sym": "▣", "area": c.get("area") or "all",
                                    **({} if (c.get("area") == "sea" or wet) else {"trail": "foot"}), "lead": 0, "fill": c["id"], "legs": [{"t0": round(t0u, 2), "t1": round(t0u + 2, 2), "path": [pos, [round(pos[0] + 0.001, 4), round(pos[1] + 0.001, 4)]]}], "u": round(max(a["e"], a["s"] + 12), 2)})
            got = sides_pts(sc["items"], w0, a["s"] + tb.WIN); pr = (anchored_pair(got, where) if placed else nearest_pair(got, where))
        if fired: n += 1; continue        # fire of both sides is already drawn here (another card's); the contact range above is still enforced
        _, pi, pa = pr
        sea = c.get("area") == "sea"
        area = c.get("area") or "all"
        t0 = w0 + 0.4
        for sd, fr, to in (("iaf", pi, pa), ("ar", pa, pi)):
            sc["items"].append({"type": "shell", "from": [round(fr[0], 4), round(fr[1], 4)], "to": [round(to[0], 4), round(to[1], 4)], "t0": round(t0 + (0.3 if sd == "ar" else 0), 2), "t1": round(w1, 2), "period": 1.3 if sd == "iaf" else 1.5,
                                "lift": 0.02, "area": area, "ship": 1, "side": sd, "fire": c["id"]})
            k = 0
            while t0 + 1.0 + k * 1.3 < w1 and k < 7:
                tx = t0 + 1.0 + k * 1.3 + (0.3 if sd == "ar" else 0)
                sc["items"].append({"type": "boom", "at": [round(to[0] + ((k * 5) % 3 - 1) * 0.006, 4), round(to[1] + ((k * 7) % 3 - 1) * 0.006, 4)], "t": round(tx, 2), "dur": 1.1, "big": 1, "area": area, "fire": c["id"]})
                k += 1
        n += 1
    ev["battle_fire"] = n
    return n
