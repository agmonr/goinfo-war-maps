"""LAW R35 helper (the owner 10-26): a card that describes a battle must animate the fighting forces of BOTH sides at the place. fill(ev) adds, for every battle card where one side is not drawn at the place in the
card's window, a schematic force of the missing side AT THE PLACE for the card's act (an item of type walk, labelled "(סכמטי, מיקום משוער)", gone at the end of the act): the card itself says two sides fought there,
the source gives no position or strength for the missing one, so none is claimed. Called by a war's data generator after its scene is built; the check is tools/test_war_battles.py."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es, test_war_heavy_losses as hl, test_war_battles as tb, war_landcheck as lc
def fill(ev, names=None):
    names = names or {"il": "כוח ישראלי מול הקרב", "ar": "כוח הצד השני בקרב"}
    sc, places, n = ev["scene"], ev.get("places", {}), 0
    L = lc.load_mask()
    acts = sc["acts"]
    for c in ev["events"]:
        if not tb.BATTLE.search(c["title"] + " " + c["quote"]) or c.get("fight_ok"): continue
        cand = [x for x in acts if x.get("min") == c.get("start_min")]
        a = next((x for x in cand if c["title"][:12] in x["clock"]), None) or (cand[0] if cand else None)
        if not a:
            near = min((x for x in acts if x.get("min") is not None), key=lambda x: abs(x["min"] - c["start_min"]), default=None)
            a = near if near and abs(near["min"] - c["start_min"]) <= 90 else None
        if not a: continue
        pl = [(places[g["place"]]["lat"], places[g["place"]]["lon"]) for g in c.get("geometry", []) if g.get("place") in places]
        w0, w1 = a["s"], a["s"] + tb.WIN
        if tb.fighting(sc["items"], w0, w1, pl): continue
        got = {"il": [], "ar": []}
        for it in sc["items"]:
            sa, sb = es.span(it)
            if sb < w0 or sa > w1 or it["type"] in ("boom", "mark", "loss", "note", "sam", "shell"): continue
            sd = hl.side(it)
            if sd: got[sd] += es.pts(it)
        where = pl[0] if pl else None
        if where is None:
            pts = got["il"] + got["ar"]
            if not pts: continue
            where = (pts[0][0] + 0.03, pts[0][1] + 0.03)
        wet = not lc.near_land(L, where)      # R52/R53: a place on the sea (the Liberty): the force drawn there is a ship, not a soldier, and it is NOT moved to the shore
        for sd in ("il", "ar"):
            if any(math.hypot(p[0] - where[0], p[1] - where[1]) <= tb.R for p in got[sd]): continue
            t0 = a["s"] + 0.3
            sc["items"].append({"type": "walk", "label": (("ספינה ישראלית בקרב" if sd == "il" else "ספינת הצד השני בקרב") if (c.get("area") == "sea" or wet) else names[sd]) + " (סכמטי, מיקום משוער)", "cls": "iaf" if sd == "il" else "syr", "sym": "▣", "area": c.get("area") or "all", **({} if (c.get("area") == "sea" or wet) else {"trail": "foot"}), "lead": 0, "fill": c["id"],
                                "legs": [{"t0": round(t0, 2), "t1": round(t0 + 2, 2), "path": [[round(where[0] + (0.012 if sd == "il" else -0.012), 4), round(where[1] + 0.01, 4)], [round(where[0] + (0.011 if sd == "il" else -0.011), 4), round(where[1] + 0.011, 4)]]}],
                                "u": round(max(a["e"], a["s"] + 12), 2)})
            if sc["items"][-1]["area"] != "sea" and not wet:                 # a coastal place: the force stands on land (checklist 17)
                for p in sc["items"][-1]["legs"][0]["path"]: p[:] = [round(x, 4) for x in lc.snap(L, p)]
            n += 1
    ev["battle_fill"] = n
    return n
