#!/usr/bin/env python3
"""LAW R52 (the owner 10-26: "remove the soldier from the water; leave no trails at sea, not of aircraft and not of ships"). Static part: the shared template clips EVERY dotted trail and arrow line to land (landClip, land mask of daynight.js) except an item with water_ok (an outline drawn on purpose),
and an arrow drawn on the sea (area sea / water_ok) never gets a soldier / unit icon at its tip (ukA). The browser part is tools/war_trail_rig.py (every drawn trail vertex of the whole scene is on land; 103,000 vertices on Yom Kippur)."""
import re, sys
from pathlib import Path
s = (Path(__file__).resolve().parent.parent / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
assert "function landClip" in s and "landClip(offPts(pts,px))" in s and "landClip(offPts(pts,-px))" in s, "trail(): every footstep/smoke trail must be clipped to land"
assert "setLatLngs(nc?pts:landClip(pts))" in s and "it.water_ok);" in s, "lineSeg(): arrow lines are clipped to land unless water_ok"
assert "function ukA" in s and s.count("ukA(it)") >= 3, "an arrow on the sea has no unit icon"
assert "tkA=it.trail==='tank'&&!(it.area==='sea'||it.water_ok)" in s, "no tank tip on the sea"
print("ok: R52 trails and sea icons")
