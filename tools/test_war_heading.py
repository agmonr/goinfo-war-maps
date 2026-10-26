#!/usr/bin/env python3
"""A stationary war unit must not rotate (the owner 2026-10-25: "when the tanks start to attack they circle around themselves"). The shared template turns a ground unit toward its screen
movement only while it is on a leg and has moved >= 0.6 px at z10; aircraft need >= 0.3 px. Static check of the template (the rule is one expression) + the recorded-track rig is
tools/war_spin_rig.py (browser, a dev machine)."""
import re
from pathlib import Path

s = (Path(__file__).resolve().parent.parent / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
assert "moving&&d>0.6&&d<60)mv=" in s, "setTank must turn only while moving and for a real move"
assert s.count("d>0.02&&d<60)mv=") == 0, "the 0.02 px rule (stationary tanks turned on jitter) must not come back"
m = re.search(r"function setPlane.*?d>(0\.\d+)&&d<60\)mv=", s, re.S)
assert m and float(m.group(1)) >= 0.3, "aircraft heading threshold"
print("ok: heading rule")

# facing rule (the owner 2026-10-25: tanks face the enemy, or their direction of travel when moving)
assert "function faceBearing(" in s and "m._side" in s and "A.gp" in s, "stationary tanks face the nearest enemy"
assert "if(moving&&!m._rev){if(st.a===null)st.a=hd*180/Math.PI;else if(mv!==null)" in s, "moving tanks follow their travel (a retreating unit, m._rev, keeps facing the enemy: R50)"
assert "if(a==='golan')return ar?270:90;if(a==='sinai')return ar?90:270" in s, "side defaults: Golan Syrians west / Israelis east, canal Egyptians east / Israelis west"
print("ok: facing rule")
