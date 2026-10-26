"""R48 helper (the owner 10-26): the opening screen of a war page - war name, dates and the casualties of every side, from the sources we already cite, never invented. intro(ev, title, sides_override=None) reads the INFOBOX of the war's
pinned Wikipedia article (ev['source']: title + revid; fields תאריך התחלה / תאריך סיום / צד ראשון-אבדות / צד שני-אבדות, the raw wikitext of the pinned revision, cached) and writes ev['intro'] =
{title, dates, sides:[{k, name, lines:[...]}], src:{t,u}, note}; a field the article leaves empty becomes "אין נתון בערך". The numbers are the article's words (cleaned of markup), side by side, not merged."""
import json, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_source_links as sl
HE = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
def raw(title, rev, lang="he"):
    os.makedirs(sl.CACHE, exist_ok=True); f = os.path.join(sl.CACHE, f"raw_{lang}_{rev}.txt")
    if os.path.exists(f): return open(f, encoding="utf-8").read()
    u = f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(title)}&oldid={rev}&action=raw"
    t = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "goinfo-research/1.0"}), timeout=40).read().decode("utf-8")
    open(f, "w", encoding="utf-8").write(t); return t
def field(w, key):
    m = re.search(r"\n\s*\|\s*" + re.escape(key) + r"\s*=(.*?)(?=\n\s*\|\s*[^=|\n]{1,40}=|\n\}\})", w, re.S)
    if not m: return ""
    g = re.sub(r"\{\{ש\}\}|<br\s*/?>|\n\s*\*", " · ", m.group(1))
    t = sl.plain(g); t = re.sub(r"\n+", " · ", t); t = re.sub(r"(?<=[א-ת]),(?=\S)", ", ", t); t = re.sub(r":(?=\S)", ": ", t); t = re.sub(r"\s+", " ", t).strip(" ·*:")
    return t
def short_date(t):
    t = re.sub(r"\s+[א-ת]'?\"?[א-ת]* ב[א-ת]+ תש[א-ת\"]+$", "", t)       # drop the Hebrew-calendar tail
    return re.sub(r"\s*[י-כ]['\"״]?[א-ת]?['\"״]? ב[א-ת]+ תש.*$", "", t).strip()
NUM = r"((?:כ-|מעל |כ־)?[\d][\d,.–-]*)"
KEYS = (("הרוגים", r"הרוגים"), ("פצועים", r"פצועים"), ("שבויים", r"שבויים|שבוי|שבויים"), ("נעדרים", r"נעדרים"))
def people(frags, default):
    """the people counts (killed, wounded, captured, missing) per named group of an infobox casualties field; machines (aircraft, tanks...) are in the source link, not on the opening screen"""
    groups = []; cur = None
    for f in frags:
        m = re.match(r"^([^\d:]{2,40}):\s*(.*)$", f)
        if m: cur = {"name": m.group(1).strip(" *"), "v": {}}; groups.append(cur); f = m.group(2)
        if cur is None: cur = {"name": default, "v": {}}; groups.append(cur)
        for k, pat in KEYS:
            mm = re.search(NUM + r"\s*(?:" + pat + r")", f) or (re.search(r"(שבוי אחד)", f) if k == "שבויים" else None)
            if mm and k not in cur["v"]: cur["v"][k] = ("1" if mm.group(1) == "שבוי אחד" else mm.group(1).strip())
        if re.search(r"(?:חיילים|אזרחים)", f) and not cur["v"]: cur["v"]["_raw"] = f.strip(" .")
    out = []
    for g in groups:
        if not g["v"]: continue
        if "_raw" in g["v"]: out.append((g["name"] + ": " if g["name"] != default else "") + g["v"]["_raw"]); continue
        out.append((g["name"] + " - " if g["name"] != default else "") + " · ".join(f"{k} {v}" for k, v in g["v"].items()))
    return out
def _range(a, b):
    """'6 באוקטובר 1973' + '24 באוקטובר 1973' -> '6–24 באוקטובר 1973' (same month); '29 באוקטובר 1956' + '5 בנובמבר 1956' -> '29 באוקטובר – 5 בנובמבר 1956' (same year)"""
    ma, mb = re.match(r"^(\d+) (\S+) (\d{4})$", a), re.match(r"^(\d+) (\S+) (\d{4})$", b)
    if ma and mb:
        if ma.group(2) == mb.group(2) and ma.group(3) == mb.group(3): return f"{ma.group(1)}–{mb.group(1)} {ma.group(2)} {ma.group(3)}"
        if ma.group(3) == mb.group(3): return f"{ma.group(1)} {ma.group(2)} – {mb.group(1)} {mb.group(2)} {mb.group(3)}"
    return f"{a} – {b}"
def intro(ev, title, il_name="ישראל", ar_name="הצד השני", note="", ar_override=None, il_override=None, dates=None):
    s = ev["source"]; w = raw(s["title"], s["revid"])
    a, b = short_date(field(w, "תאריך התחלה")), short_date(field(w, "תאריך סיום"))
    d = dates or (a if a == b else _range(a, b))
    il = il_override or field(w, "צד ראשון-אבדות"); ar = ar_override or field(w, "צד שני-אבדות")
    clean = lambda t: [x.strip(" ·") for x in re.split(r" · | ‑ ", t) if x.strip(" ·")]
    sides = [{"k": "il", "name": il_name, "lines": people(clean(il), il_name) or clean(il) or ["אין נתון בערך"]}, {"k": "ar", "name": ar_name, "lines": people(clean(ar), ar_name) or clean(ar) or ["אין נתון בערך"]}]
    ev["intro"] = {"title": title, "dates": d, "sides": sides, "src": {"t": "ויקיפדיה: " + s["title"] + " (תיבת המידע, הגרסה המצוינת)", "u": sl.permalink(s["title"], s["revid"])}, "note": note}
    return ev["intro"]
