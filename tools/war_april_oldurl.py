#!/usr/bin/env python3
"""The OLD April URL https://goinfo.co.il/reports/battle-1967-04-07/ (noindex, no canonical) must keep serving the April map.
Builds its two files from a built stage:  python3 tools/war_april_oldurl.py STAGE OUT_DIR
  OUT_DIR/index.html  = STAGE/war/1967/7-april/map/index.html with: fetch('../events.json') -> 'events.json' (+ the events.json footer link),
                        the canonical line dropped, the OLD title and description kept
  OUT_DIR/events.json = STAGE/war/1967/7-april/events.json
Upload both to r2:goinfo/reports/battle-1967-04-07/ (copy only; Content-Type text/html + application/json; Cache-Control no-cache)."""
import re, shutil, sys
from pathlib import Path
OLD_TITLE = "7 באפריל 1967 על המפה - כחודשיים לפני מלחמת ששת הימים (יוני 1967)"
OLD_DESC = "קרבות 7 באפריל 1967 - כחודשיים לפני מלחמת ששת הימים (יוני 1967). מפה ואנימציה סכמטית לפי הערך בוויקיפדיה העברית."
def main():
    stage, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    src = stage / "war" / "1967" / "7-april"
    h = (src / "map" / "index.html").read_text(encoding="utf-8")
    n_fetch = h.count("../events.json"); h = h.replace("../events.json", "events.json")
    h, n_can = re.subn(r'<link rel="canonical"[^>]*>\n?', "", h)
    h, n_t = re.subn(r"<title>.*?</title>", f"<title>{OLD_TITLE}</title>", h, count=1, flags=re.S)
    h, n_d = re.subn(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + OLD_DESC + m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:(?:title|url|description)"[^>]*>\n?)', "", h)
    h = h.replace("'../#cas-'", "'/war/1967/7-april/#cas-'")   # standalone casualty links go to the day page, not to /reports/
    assert n_fetch >= 1 and n_t == 1, (n_fetch, n_t)
    (out / "index.html").write_text(h, encoding="utf-8")
    shutil.copy(src / "events.json", out / "events.json")
    print(f"old-url copy: {n_fetch} events.json refs fixed, canonical dropped {n_can}, title {n_t}, description {n_d} -> {out}")
main()
