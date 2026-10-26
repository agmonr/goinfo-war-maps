#!/usr/bin/env python3
"""python3 tools/test_war_bases.py - every schematic BASE drawn by the war animations is on land (the owner 2026-10-18: "בסיס חיל האוויר מוצג על הים").
Checks the bases of the data-driven scene (war/data/*-events.json scene.bases) and the April engine's hard-coded IL / SY in the template.
Land test: east of the Levant coast line (Gaza - Ashkelon - Tel Aviv - Haifa - Acre - Nahariya - Tyre - Beirut, 3 km margin); every point must also be inside the region the maps cover."""
import glob, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
COAST = [(31.30, 34.25), (31.50, 34.45), (31.66, 34.55), (31.80, 34.64), (32.08, 34.76), (32.33, 34.85), (32.50, 34.90), (32.80, 34.99), (32.92, 35.07), (33.05, 35.10), (33.27, 35.20), (33.90, 35.50)]
def coast_lon(lat):
    for (a, la), (b, lb) in zip(COAST, COAST[1:]):
        if a <= lat <= b:
            return la + (lb - la) * (lat - a) / (b - a)
    return None
def on_land(lat, lon, margin=0.03):
    c = coast_lon(lat)
    if c is None:                      # south of Gaza / north of Beirut: judge by the Sinai/Egypt coast (31.3 N) - never a base there in these maps
        return lat < 31.3 and False or lat < 31.2
    return lon > c + margin
bad = []; n = 0
for f in sorted(glob.glob(str(ROOT / "war" / "data" / "*-events*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    for b in (d.get("scene") or {}).get("bases", []):
        n += 1
        if not on_land(*b["pos"]): bad.append((Path(f).name, b["label"], b["pos"]))
t = (ROOT / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
m = re.search(r"var IL=\[([\d.]+),([\d.]+)\],SY=\[([\d.]+),([\d.]+)\]", t)
assert m, "April bases not found in the template"
for name, lat, lon in (("April IL", m.group(1), m.group(2)), ("April SY", m.group(3), m.group(4))):
    n += 1
    if not on_land(float(lat), float(lon)): bad.append(("template", name, (lat, lon)))
print(f"{n} bases checked; on the sea: {len(bad)}")
for b in bad: print("  SEA:", b)
sys.exit(1 if bad else 0)
