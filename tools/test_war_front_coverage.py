#!/usr/bin/env python3
"""A front never goes empty inside the war (the owner 2026-10-25: "on 13 October no forces at all on the Egyptian front"). For every whole-war scene (a "whole" block with days), every land area
that has ground-unit symbols at all must have at least one alive from the day of its first symbol to the last day of the war; a symbol is alive from its start to its "u" (end of its day/chapter)
or, with no "u", to the end of the animation. Lists every empty day x area. Exit 1 when any.
    python3 tools/test_war_front_coverage.py [events.json ...]      (default: every war/data/*-events.json with a "whole" block)"""
import json, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "war" / "data"


def check(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    w = d.get("whole")
    if not w:
        return None
    sc = d["scene"]
    dur = sc["dur"]
    days = w["days"] if isinstance(w["days"], list) else []
    n = len(days) or 1
    DAYLEN = None
    # day windows in animation seconds: from the chapter/day starts the generator wrote (T0 of each day) when present, else equal slices
    starts = [x["T0"] for x in days if isinstance(x, dict) and "T0" in x] or [dur * i / n for i in range(n)]
    ends = starts[1:] + [dur]
    items = [i for i in sc["items"] if i["type"] == "walk" and i.get("trail") in ("tank", "foot")]
    bad = []
    for area in sorted({i.get("area") for i in items} - {None, "all", "sea"}):
        its = [i for i in items if i.get("area") == area]
        first = min(i["legs"][0]["t0"] for i in its)
        for k, (a, b) in enumerate(zip(starts, ends)):
            if b <= first:
                continue
            alive = [i for i in its if i["legs"][0]["t0"] <= b and (i.get("u") is None or i["u"] >= a)]
            if not alive:
                bad.append((area, k + 1))
    return bad, len(days)


def main(argv):
    files = argv or sorted(str(p) for p in DATA.glob("*-events.json"))
    rc = 0
    for f in files:
        r = check(f)
        if r is None:
            continue
        bad, n = r
        print(f"{Path(f).name}: {n} days, {len(bad)} empty day x area" + (": " + ", ".join(f"{a} day {d}" for a, d in bad[:12]) if bad else ""))
        rc |= 1 if bad else 0
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
