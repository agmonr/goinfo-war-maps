#!/usr/bin/env python3
"""Refuses a war stage with an unmeasured page (the owner 10-25, rule 13: every page served is measured; "make it impossible to publish a war page without it").

    tools/war_measure_check.py STAGE_DIR      STAGE_DIR holds war/ (or is the war/ directory itself)

Every .html under it must carry the Google tag, its guard (src/ga-guard.js), the inline host-fallback beside the guard (a LAN twin serves no /src/ga-guard.js: 10-26) and the event log (src/eventlog.js). Exit 1 and the list of pages when not."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ga_inject  # noqa: E402


HOST_FALLBACK = "!/(^|\\.)goinfo\\.co\\.il$/.test(location.hostname)"


def main(stage):
    root = Path(stage)
    root = root / "war" if (root / "war").is_dir() else root
    pages = sorted(root.rglob("*.html"))
    bad = [p.relative_to(root).as_posix() for p in pages if not (lambda t: ga_inject.measured(t) and HOST_FALLBACK in t)(p.read_text(encoding="utf-8"))]
    for b in bad:
        print("UNMEASURED (no gtag / ga-guard / host-fallback / eventlog):", b, file=sys.stderr)
    print(f"war_measure_check: {len(pages)} pages, {len(bad)} unmeasured")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
