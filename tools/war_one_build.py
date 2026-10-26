#!/usr/bin/env python3
"""One single-scene war page (a multi-day war authored as ONE scene with a "whole" block) -> STAGE/war/<year>/<slug>/{map/index.html, events.json, daynight.js, land-mask.json}.
    python3 tools/war_one_build.py STAGE kadesh      (Operation Kadesh / Sinai War 1956, LAN test page: noindex via the template, no sitemap, no link)"""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import war_build as wb
ROOT = wb.ROOT
WARS = {"kadesh": dict(year=1956, file="1956-10-29-events.json", title="מבצע קדש (מלחמת סיני): 29 באוקטובר – 5 בנובמבר 1956, על מפה אחת", h1="מבצע קדש",
                       desc="מבצע קדש (מלחמת סיני), 29 באוקטובר – 5 בנובמבר 1956, על ציר זמן אחד: מפה ואנימציה סכמטית לפי הערך בוויקיפדיה העברית.", date="1956-10-29")}

def build(stage, key):
    w = WARS[key]
    ev = json.loads((ROOT / "war" / "data" / w["file"]).read_text(encoding="utf-8"))
    b = {"date": w["date"], "title": w["title"], "h1": w["h1"], "description": w["desc"], "context": "מפה ואנימציה סכמטית.",
         "credit_notes": ["כל הציטוטים לקוחים מהגרסה המצוינת של הערך; שום פרט שאינו בערך לא נוסף. מסלולים ומיקומים סכמטיים."]}
    b["src_bar"] = wb.src_bar(ev)
    out = Path(stage) / "war" / str(w["year"]) / key
    template = (ROOT / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
    url = f"https://goinfo.co.il/war/{w['year']}/{key}/map/"
    wb.write(out / "map" / "index.html", wb.map_page(template, b, url, "../events.json", "anim", wb.credit_html(b, ev)))
    wb.write(out / "events.json", json.dumps(ev, ensure_ascii=False, indent=1))
    snd = Path(stage) / "war" / "sound"                  # the movement-sound loops daynight.js fetches (../../sound/): a stand-alone LAN stage had none
    snd.mkdir(parents=True, exist_ok=True)
    for f in ("tank.mp3", "jet.mp3", "march.mp3"):
        shutil.copy(ROOT / "war" / "sound" / f, snd / f)
    for f in ("daynight.js", "land-mask.json"):
        (out / f).write_bytes((ROOT / "war" / f).read_bytes())
    return out

if __name__ == "__main__":
    print("wrote", build(sys.argv[1], sys.argv[2]))
