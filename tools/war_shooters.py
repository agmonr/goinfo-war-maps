"""R51 helper (the owner 10-26: "aircraft are shot down only after the shooting side's aircraft have reached the area"): for every shot-down item (fly with a `down` block, or a wreck marker) the test (tools/test_war_shootdown_order.py) finds no aircraft/SAM of the other side
within range in the 40 scene-seconds before the hit, add the SHOOTERS: a pair (4 for 5+ victims) of fighters of the other side that ARRIVE at the place about 4 s before the first hit, circle there while the hits happen (muzzle bursts at each victim's hit point) and leave afterwards.
Order on screen: the strike force / victims fly in -> the interceptors arrive -> burst -> the aircraft falls. Schematic (labelled), the sources give neither routes nor types of the shooters beyond the article's own words.
apply(ev) -> number of shooter flights added; bookkeeping ev["shooters"] = [{at, t, n}]."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_shootdown_order as so
def offenders(items):
    out = []
    for it in items:
        if it["type"] == "fly" and it.get("down"):
            t = it["down"]["t"]; hp = so.pos_at(it, t) or it["down"].get("at"); me = so.side_of(it)
            if hp and not so.shooter_near(items, "il" if me == "ar" else "ar", hp, t, skip=it): out.append((t, list(hp), "il" if me == "ar" else "ar", it.get("area")))
        elif it["type"] == "wreck" and it.get("at") and it.get("t") is not None and not it.get("nogate"):
            me = so.side_of(it)
            if not so.shooter_near(items, "il" if me == "ar" else "ar", it["at"], it["t"]): out.append((it["t"], list(it["at"]), "il" if me == "ar" else "ar", it.get("area")))
    return sorted(out)
def apply(ev):
    items = ev["scene"]["items"]; off = offenders(items); cl = []
    for o in off:                                    # cluster by time and place
        for c in cl:
            if o[2] == c[0][2] and abs(o[0] - c[-1][0]) <= 14 and math.hypot(o[1][0] - c[0][1][0], o[1][1] - c[0][1][1]) <= 0.6: c.append(o); break
        else: cl.append([o])
    n = 0
    for c in cl:
        side = c[0][2]; area = c[0][3]; t0 = min(x[0] for x in c); t1 = max(x[0] for x in c)
        cx = sum(x[1][0] for x in c) / len(c); cy = sum(x[1][1] for x in c) / len(c); k = 4 if len(c) >= 5 else 2
        lab = "מיירט מיג 21 מצרי" if side == "ar" else "מטוס קרב ישראלי"
        for i in range(k):
            ang = 0.8 + 2.1 * i + (0.4 if side == "il" else 0.0); r = 0.55 + 0.08 * i
            S = [round(cx + r * math.cos(ang), 4), round(cy + r * 1.2 * math.sin(ang), 4)]; C = [round(cx + 0.03 * (i - k / 2), 4), round(cy + 0.03 * i, 4)]; E = [round(cx - r * math.cos(ang) * .9, 4), round(cy - r * 1.2 * math.sin(ang) * .9, 4)]
            a0 = t0 - 11 + 0.15 * i
            items.append({"type": "fly", "side": "iaf" if side == "il" else "syr", "label": f"{lab} {i + 1} (סכמטי)", "area": area, "off": None,
                          "legs": [{"t0": round(a0, 2), "t1": round(t0 - 3.5 + 0.15 * i, 2), "path": [S, C]}, {"t0": round(t1 + 1.0 + 0.15 * i, 2), "t1": round(t1 + 8.0 + 0.15 * i, 2), "path": [C, E]}], "shooter": 1})
            n += 1
        for x in c:                                  # a burst of fire at each victim's hit point, 0.8 s before the hit
            items.append({"type": "boom", "at": [round(x[1][0], 4), round(x[1][1], 4)], "t": round(x[0] - 0.8, 2), "area": area, "big": 1})
        ev.setdefault("shooters", []).append({"at": [round(cx, 3), round(cy, 3)], "t": round(t0, 1), "n": len(c), "side": side})
    # every shot-down aircraft: a burst of fire at its hit point just before it falls (the dogfight fire the shoot-down comes from); R51
    for it in [x for x in items if x["type"] == "fly" and x.get("down")]:
        t = it["down"]["t"]; hp = so.pos_at(it, t) or it["down"].get("at")
        if hp and not so.fire_before(items, hp, t): items.append({"type": "boom", "at": [round(hp[0], 4), round(hp[1], 4)], "t": round(t - 0.8, 2), "area": it.get("area"), "big": 1})
    return n
