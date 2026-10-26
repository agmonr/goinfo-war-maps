"""R50 helper (the owner 10-26: "retreating tanks keep the gun toward the enemy, move in disorder, and some are hit on the way"): every retreat unit that war_pushout made (walk with "pushout": card) becomes a small disorderly GROUP:
`group` units (the original + clones), each with its own lateral offset, start delay, speed and 2 wiggle waypoints - all drawn from a generator seeded by the unit's own id (card + label + index), so the picture is identical on every
run and every reload. About a third of the units are HIT on the way: the unit stops at the hit point, burns (a 'loss' marker, no number - the sources give none for a drawn group) and is removed. The template turns a unit whose label starts
with נסיגה toward the enemy while it moves (m._rev); the group is schematic and labelled so. Land: every new path is snapped onto land (tools/war_landcheck.py).
apply(ev, L=None, group=6); bookkeeping ev["retreat"][card] = {units, hits, spread}. The check is tools/test_war_retreat.py."""
import math, os, random, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_landcheck as lc
def _rng(*parts): return random.Random(zlib.crc32("|".join(str(x) for x in parts).encode("utf-8")))
def _cut(path, f):
    """prefix of a polyline up to fraction f of its length, and the end point"""
    segs = [math.hypot(b[0] - a[0], (b[1] - a[1]) * .84) for a, b in zip(path, path[1:])]; tot = sum(segs) or 1.0; d = f * tot; out = [path[0]]
    for a, b, sg in zip(path, path[1:], segs):
        if d >= sg: out.append(b); d -= sg; continue
        g = d / sg if sg else 0.0; out.append([a[0] + (b[0] - a[0]) * g, a[1] + (b[1] - a[1]) * g]); break
    return out
def apply(ev, L=None, group=6):
    items = ev["scene"]["items"]
    for it in [x for x in items if x["type"] == "walk" and x.get("pushout_leg")]:      # a unit that got a retreat LEG appended: it ends where the leg begins, the leg becomes the retreating walk
        lg = it["legs"].pop(); card = it.pop("pushout_leg")
        items.append({"type": "walk", "label": "נסיגה: " + (it.get("label") or "").replace(" (סכמטי)", "") + " (סכמטי)", "cls": it.get("cls"), "sym": it.get("sym", "▣"), "area": it.get("area"), "trail": it.get("trail") or "tank", "lead": 0, "pushout": card, "legs": [lg]})
        it["u"] = round(lg["t0"], 2)
    base = [it for it in items if it["type"] == "walk" and it.get("pushout") and not it.get("retreat")]; n_out = 0
    for it in base:
        card = it["pushout"]; lg = it["legs"][0]; p, q = lg["path"][0], lg["path"][-1]; dur = lg["t1"] - lg["t0"]
        dl, dn = q[0] - p[0], q[1] - p[1]; ln = math.hypot(dl, dn) or 1.0; pl, pn = -dn / ln, dl / ln      # unit vector across the retreat line
        lab = (it.get("label") or "").replace(" (סכמטי)", "")
        out = []
        for i in range(group):
            r = _rng(card, lab, i); lat = (r.random() - .5) * 0.22 if i else 0.0
            t0 = lg["t0"] + (r.random() * 2.4 if i else 0.0); d = dur * (0.85 + r.random() * 0.9)
            way = [[p[0] + pl * lat, p[1] + pn * lat * 1.1]]
            for f in (0.34, 0.68):
                w = (r.random() - .5) * 0.07; v = (r.random() - .5) * 0.05
                way.append([p[0] + dl * f + pl * (lat + w) + dl / ln * v, p[1] + dn * f + pn * (lat + w) * 1.1 + dn / ln * v])
            way.append([q[0] + pl * lat * .6, q[1] + pn * lat * .6])
            if L: way = [lc.snap(L, w) for w in way]
            way = [[round(w[0], 4), round(w[1], 4)] for w in way]
            hit = i % 3 == 1 and r.random() < 0.9 or (i == 1)
            fh = 0.4 + r.random() * 0.4
            path = _cut(way, fh) if hit else way
            path = [[round(w[0], 4), round(w[1], 4)] for w in path]
            t1 = t0 + d * (fh if hit else 1.0)
            u = dict(it) if i == 0 else {k: v for k, v in it.items() if k not in ("legs", "u")}
            if i: u["label"] = "נסיגה (סכמטי)"      # the group's other units carry the short label (no wall of identical tooltips)
            u.update({"legs": [{"t0": round(t0, 2), "t1": round(t1, 2), "path": path}], "u": round(t1 + (0.9 if hit else 0.6), 2), "retreat": 1, "lead": 0})
            if hit: u["hit"] = 1
            out.append(u)
            if hit:
                e = path[-1]; side = "ar" if it.get("cls") == "syr" else "iaf"
                items.append({"type": "loss", "at": e, "t": round(t1, 2), "side": side, "kind": "tank", "label": "טנק נפגע בדרך הנסיגה (סכמטי; הערך אינו נותן מספר לקבוצה המצוירת)", "area": it.get("area")})
                items.append({"type": "boom", "at": e, "t": round(t1, 2), "area": it.get("area"), "big": 1})
        items.remove(it); items.extend(out)
        for u in out:
            if L and u.get("legs"): lc.densify_snap(u, L)
        sp = max(max(abs((u["legs"][0]["path"][0][0] - p[0]) * pl + (u["legs"][0]["path"][0][1] - p[1]) * pn) for u in out), 0)
        ev.setdefault("retreat", {}).setdefault(card, {"units": 0, "hits": 0, "spread": 0})
        r_ = ev["retreat"][card]; r_["units"] += len(out); r_["hits"] += sum(1 for u in out if u.get("hit")); r_["spread"] = round(max(r_["spread"], sp), 3); n_out += len(out)
    return n_out
