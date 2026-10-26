"""R45 helper (the owner 10-26: "it says all the Syrian tanks were pushed back, but you still see them on the Golan"): a card that says a force was pushed out of / withdrew from an area must show that force LEAVE the area and be gone:
for each spec {card, side, box, to} every ground unit of that side standing inside the box at the card's time (walk / arrow, alive, last position in the box) gets a retreat leg (walk) or a reverse arrow to `to` (their own side, outside the
box) at the card's act, then is removed. The check is tools/test_war_pushout.py: after the card (+8 scene-seconds) no unit of that side stands in the box."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es, test_war_heavy_losses as hl
def last_pos(it): return it["legs"][-1]["path"][-1] if it["type"] == "walk" else it["path"][-1]
def inside(p, box): return box[0][0] <= p[0] <= box[1][0] and box[0][1] <= p[1] <= box[1][1]
def units_in_box(items, side, box, T):
    out = []
    for i, it in enumerate(items):
        if it["type"] not in ("walk", "arrow") or hl.side(it) != side or it.get("fill"): continue
        lab = it.get("label") or ""
        if lab.startswith("מסוק") or "טיל" in lab: continue
        a, b = es.span(it)
        if a <= T <= b and inside(last_pos(it), box): out.append(i)
    return out
def act_of(sc, c):
    if not c: return None
    exact = next((x for x in sc["acts"] if x.get("min") == c["start_min"]), None)
    if exact: return exact
    near = min((x for x in sc["acts"] if x.get("min") is not None), key=lambda x: abs(x["min"] - c["start_min"]), default=None)
    return near if near and abs(near["min"] - c["start_min"]) <= 90 else None
def apply(ev, specs):
    sc = ev["scene"]; items = sc["items"]; n = 0
    cards = {c["id"]: c for c in ev["events"]}
    for sp in specs:
        c = cards.get(sp["card"])
        a = act_of(sc, c)
        if not a: continue
        T = a["s"]
        for k, i in enumerate(units_in_box(items, sp["side"], sp["box"], T)):
            it = items[i]; p = last_pos(it); t0 = T + 1.0 + 0.25 * k; t1 = t0 + 4.0
            lab = (it.get("label") or "").replace(" (סכמטי)", "")
            if it["type"] == "walk" and it["legs"][-1]["t1"] <= t0:
                it["legs"].append({"t0": round(t0, 2), "t1": round(t1, 2), "path": [p, sp["to"]]})
            else:
                items.append({"type": "walk", "label": f"נסיגה: {lab} (סכמטי)", "cls": "syr" if sp["side"] == "ar" else "iaf", "sym": "▣", "area": it.get("area"), "trail": it.get("trail") or "tank", "lead": 0, "pushout": sp["card"],
                              "legs": [{"t0": round(t0, 2), "t1": round(t1, 2), "path": [p, sp["to"]]}]})
                it["u"] = round(t0, 2)       # the arrow's unit symbol is replaced by the retreating unit
                items[-1]["u"] = round(t1 + 0.6, 2)
                continue
            it["u"] = round(t1 + 0.6, 2); n += 1
        ev.setdefault("pushout", {})[sp["card"]] = len(units_in_box(items, sp["side"], sp["box"], T + 8))
        n += 1
    return n
