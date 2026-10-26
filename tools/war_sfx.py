#!/usr/bin/env python3
"""Sound cues for a war scene authored without hand-placed cues (the owner 2026-10-23: "Yom Kippur had no sound").
The Six-Day day files place their cues by hand (SFX); the Kadesh and Yom Kippur scenes had `sfx: []`, so only the movement loops could ever play - and those need the
visitor to start sound. auto(items) derives the cue track from the scene items, the same vocabulary the Six-Day track uses (engine: sfx() in battle-map.html):
  boom item, big >= 2 : 'boom'   (air strike / ship hit, the engine does NOT treat it as ground fire)
  boom item, otherwise: 'cannon' (ground fire: the daynight layer reads 'cannon' at an impact's time as a ground fight)
  fly item            : 'jet' at the first leg + 0.3 s
  arrow item, missile : 'missile' at t0 (Styx/Gabriel/Sagger/rockets, the owner 10-26 "no sound" at a sea battle: arrows had no cue)
  arrow item, other   : 'cannon' at t0 (an attack launched)
  shell item          : 'cannon' at t0 and every `period` to t1 (at most 8): the muzzle burst
  loss item           : 'boom' at t (the wreck begins to burn); lvl 2 (very heavy): boom + boom + crash
Returns [[t, kind], ...] sorted; merge into scene["sfx"]. cover(scene) adds a cue for every cue-able item that has none within 1.5 s (for scenes whose cues were placed by hand)."""
import re
MISSILE = re.compile(r"טיל|טילי|רקטות|סאגר|גבריאל|סטיקס")
CUE_TYPES = ("boom", "fly", "arrow", "shell", "loss", "surrender")


def start_of(it):
    if it["type"] in ("boom", "loss", "surrender"): return it.get("t")
    if it["type"] == "fly": return it["legs"][0]["t0"]
    return it.get("t0")


def auto(items):
    cues = []
    for it in items:
        if it["type"] == "boom":
            cues.append([round(it["t"], 2), "boom" if it.get("big", 0) >= 2 else "cannon"])
        elif it["type"] == "fly":
            cues.append([round(it["legs"][0]["t0"] + 0.3, 2), "jet"])
            if it.get("down"):   # a shot-down aircraft: a falling whistle at the hit, the crash at the end of the fall
                cues.append([round(it["down"]["t"], 2), "fall"]); cues.append([round(it["down"]["t"] + it["down"]["dur"], 2), "crash"])
        elif it["type"] == "arrow":
            cues.append([round(it["t0"], 2), "missile" if MISSILE.search(it.get("label") or "") else "cannon"])
        elif it["type"] == "shell":
            t, per = it["t0"], max(0.5, it.get("period") or 1.2)
            for _ in range(8):
                if t > it["t1"]: break
                cues.append([round(t, 2), "cannon"]); t += per
        elif it["type"] == "loss":
            cues.append([round(it["t"], 2), "boom"])
            if it.get("lvl") == 2: cues += [[round(it["t"] + 0.5, 2), "boom"], [round(it["t"] + 1.0, 2), "crash"]]     # very heavy (supreme effort): a heavier sound
        elif it["type"] == "surrender":
            cues.append([round(it["t"], 2), "flag"])      # a soft rising two-tone: a flag goes up
    return sorted(cues)


def cover(scene, tol=1.5):
    """Add the auto cue of every cue-able item that has no cue within `tol` seconds (hand-placed tracks). Returns the number added."""
    have = sorted(c[0] for c in scene.get("sfx", []))
    import bisect
    add = []
    for c in auto([it for it in scene["items"] if it["type"] in CUE_TYPES]):
        i = bisect.bisect_left(have, c[0] - tol)
        if i >= len(have) or have[i] > c[0] + tol: add.append(c)
    scene["sfx"] = sorted(scene.get("sfx", []) + add)
    return len(add)
