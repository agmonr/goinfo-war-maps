#!/usr/bin/env python3
"""Checklist 17: no LAND unit on WATER. Ground units (walk) and ground arrows (trail foot/tank) of every war events json must start/end on land
per war/land-mask.json (Natural Earth 1:10m land, public domain; rings of [lat, lng]; the canal is inside the mask = land). Ships, boats, aircraft, helicopters
(fly), shells and booms are exempt. A point outside the mask's bounding box is not judged.
    python3 tools/war_landcheck.py [events.json ...]   (default war/data/*-events.json)   rc 1 + list of offenders."""
import base64, glob, json, math, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
NAVAL = re.compile(r"מסוק|ליברטי|טורפדו|אוניית|אונייה|סירות נפץ|טרפד|אח״י|אוסה|סטי״ל|נחתת|סירת|ספינת|משחתת|צוללת")
def load_mask():
    return json.load(open(ROOT / "war" / "land-mask.json"))
_WM = None
def water_cell(lat, lng):
    """True when the OSM-tile water mask (tools/war_watermask.json: Sinai, the canal zone, the delta coast, the lagoons Manzala/Bardawil, Bitter Lakes, Gulf of Suez) says the point AND its whole 3x3 cell neighbourhood is water."""
    global _WM
    if _WM is None:
        m = json.load(open(ROOT / "tools" / "war_watermask.json"))
        _WM = (m, [base64.b64decode(r) for r in m["data"]])
    m, rows = _WM
    Z, C = m["z"], m["cell_px"]
    px = ((lng + 180) / 360 * 2 ** Z - m["x0"]) * 256
    r = math.radians(lat)
    py = ((1 - math.asinh(math.tan(r)) / math.pi) / 2 * 2 ** Z - m["y0"]) * 256
    cx, cy = int(px // C), int(py // C)
    if not (1 <= cx < m["cols"] - 1 and 1 <= cy < m["rows"] - 1): return False
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x = cx + dx
            if not (rows[cy + dy][x >> 3] >> (7 - (x & 7))) & 1: return False
    return True
def on_land(L, lat, lng):
    if water_cell(lat, lng): return False
    if lat < 27 or lat > 35 or lng < 31 or lng > 37.5: return True
    for ring in L:
        c = False
        n = len(ring)
        for i in range(n):
            a, b = ring[i - 1], ring[i]
            if (a[1] > lng) != (b[1] > lng) and lat < (b[0] - a[0]) * (lng - a[1]) / (b[1] - a[1]) + a[0]: c = not c
        if c: return True
    return False
def near_land(L, p, r=0.008):
    """on land, or within r degrees (~0.9 km, the water mask's own resolution) of land: a shore-hugging track is not a unit at sea"""
    if on_land(L, p[0], p[1]): return True
    return any(on_land(L, p[0] + i * r, p[1] + j * r) for i in (-1, 0, 1) for j in (-1, 0, 1) if i or j)
def snap(L, p, step=0.004, maxd=0.3):
    """The nearest land point (square rings of growing radius) for a vertex that fell on water; a point already on land is returned unchanged."""
    if on_land(L, p[0], p[1]): return list(p)
    k = 1
    while k * step <= maxd:
        best = None
        for i in range(-k, k + 1):
            for j in range(-k, k + 1):
                if max(abs(i), abs(j)) != k: continue
                q = [round(p[0] + i * step, 5), round(p[1] + j * step, 5)]
                if on_land(L, q[0], q[1]):
                    d = i * i + j * j
                    if best is None or d < best[0]: best = (d, q)
        if best: return best[1]
        k += 1
    return list(p)
def points(it):
    """The vertices of a ground item (a leg's or arrow's start, bends and end). The stretch BETWEEN two land vertices may cross the canal or a lake: that is a crossing, drawn on purpose."""
    t = it["type"]
    if t == "walk":
        for l in it.get("legs", []):
            yield from l["path"]
    elif t == "arrow":
        yield from (it.get("path") or it.get("pts") or [])
MISSILE = re.compile(r"טיל|טילי|רקטות|סאגר|גבריאל|סטיקס|פגז")
def ease(f):
    f = max(0.0, min(1.0, f)); return 2 * f * f if f < .5 else 1 - (-2 * f + 2) ** 2 / 2
def along(path, f):
    segs = [math.hypot(b[0] - a[0], (b[1] - a[1]) * .84) for a, b in zip(path, path[1:])]; tot = sum(segs) or 1.0; d = f * tot
    for i, sg in enumerate(segs):
        if d <= sg or i == len(segs) - 1:
            g = min(1.0, d / sg) if sg else 0.0; a, b = path[i], path[i + 1]; return [a[0] + (b[0] - a[0]) * g, a[1] + (b[1] - a[1]) * g]
    return list(path[0])
def interp_points(it, step=1.0):
    """Every position a foot/ground unit really occupies on screen, at `step` scene-seconds over the whole scene (the owner 10-26: foot soldiers on the sea; the vertex check missed the stretches BETWEEN vertices)."""
    legs = it["legs"] if it["type"] == "walk" else ([{"t0": it["t0"], "t1": it["t1"], "path": it.get("path") or it.get("pts") or []}] if it["type"] == "arrow" else [])
    for lg in legs:
        P = lg["path"]
        if len(P) < 2: continue
        t = lg["t0"]
        while t <= lg["t1"] + 1e-9:
            yield along(P, ease((t - lg["t0"]) / max(1e-6, lg["t1"] - lg["t0"]))), t
            t += step
        yield list(P[-1]), lg["t1"]
def densify_snap(it, L, step=0.004):
    """Put every path of a ground item on land: a point every `step` degrees along each segment, each snapped to the nearest land (the canal is land in the mask, so a straight crossing stays straight)."""
    def fix(P):
        out = []
        for a, b in zip(P, P[1:]):
            k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
            for q in range(k):
                t = q / k; out.append(snap(L, [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]))
        out.append(snap(L, list(P[-1]))); return [[round(x, 5) for x in p] for p in out]
    if it["type"] == "walk":
        for lg in it["legs"]:
            if len(lg["path"]) >= 2: lg["path"] = fix(lg["path"])
    elif it["type"] == "arrow" and len(it.get("path") or []) >= 2:
        it["path"] = fix(it["path"])
def land_item(it):
    t = it["type"]
    if it.get("area") == "sea" or it.get("water_ok"): return False   # water_ok: drawn on purpose over water (bombs into the sea, an air-defence envelope outline)          # ships, boats, naval gunfire, missiles at sea: authored on the sea scene
    if t == "arrow": return it.get("trail") in ("foot", "tank") and not (MISSILE.search(it.get("label") or "") and not re.search(r"חיילים|חי\"ר|חי״ר|צנחנים|קומנדו|גל ", it.get("label") or ""))
    if t == "walk":
        if it.get("trail") in ("foot", "tank"): return True
        return not NAVAL.search(it.get("label") or "")
    return False
def wet1(lat, lng):
    """True when the water mask's own cell under the point is water (no 3x3 neighbourhood: this judges a FIXED mark, a tag or a stronghold, where one wet cell is already a symbol on the sea)."""
    water_cell(lat, lng)
    m, rows = _WM
    Z, C = m["z"], m["cell_px"]
    px = ((lng + 180) / 360 * 2 ** Z - m["x0"]) * 256
    r = math.radians(lat)
    py = ((1 - math.asinh(math.tan(r)) / math.pi) / 2 * 2 ** Z - m["y0"]) * 256
    cx, cy = int(px // C), int(py // C)
    if not (1 <= cx < m["cols"] - 1 and 1 <= cy < m["rows"] - 1): return False
    return bool((rows[cy][cx >> 3] >> (7 - (cx & 7))) & 1)
def check(f, L=None):
    L = L or load_mask()
    d = json.load(open(f)); sc = d.get("scene") or d
    bad = []
    for n, it in enumerate(sc.get("items", [])):
        # the owner 10-26 ("infantry on the sea" at Port Said): a FIXED mark (stronghold, tag) on a land card must not sit on a water cell either, unless water_ok (a stronghold at the article's own coordinates)
        if it.get("type") == "mark" and it.get("at") and it.get("area") != "sea" and not it.get("water_ok") and not NAVAL.search(it.get("label") or "") and wet1(*it["at"]):
            bad.append((n, "mark", it.get("label"), it["at"])); continue
        if not land_item(it): continue
        for p in points(it):
            if not on_land(L, p[0], p[1]): bad.append((n, it["type"], it.get("label"), p)); break
        else:
            for p, t in interp_points(it):                      # between the vertices too (1 scene-second steps)
                if not near_land(L, p): bad.append((n, it["type"], it.get("label"), [round(x, 3) for x in p], "interpolated t=%.1f" % t)); break
    return bad
def main():
    fs = sys.argv[1:] or sorted(glob.glob(str(ROOT / "war/data/*-events.json")))
    L = load_mask(); rc = 0
    for f in fs:
        b = check(f, L)
        print(f"{Path(f).name}: {len(b)} land item point(s) on water")
        for x in b: print("   ", x); rc = 1
    sys.exit(rc)
if __name__ == "__main__": main()
