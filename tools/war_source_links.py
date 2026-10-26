"""R47 helper (the owner 10-26: "the title of every event must be a link that leads to the event in the source we rely on, in all wars"): every card gets `source_url` = the pinned revision of the source article (oldid permalink) + a TEXT FRAGMENT
(#:~:text=<first words of its quote>) so the browser scrolls to and highlights the passage; an IDF PDF card gets <pdf>#page=N. Cards with a source URL already (src.u) keep it and get the fragment. A card whose quote is not in the
source's own articles (searched in the war's pinned articles: file['source']['articles']) gets NO url - it is listed as a gap (never a guessed link). apply(ev) also writes `href` on the matching scene.log entries (same title).
Article texts are fetched once (raw wikitext of the pinned revision, markup stripped) into the cache dir (env WAR_SRC_CACHE, default """
import json, os, re, sys, unicodedata, urllib.parse, urllib.request
CACHE = os.environ.get("WAR_SRC_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "war-src"))
ALLOW = ("he.wikipedia.org", "en.wikipedia.org", "ar.wikipedia.org", "www.idf.il", "idf.il", "palmach.org.il", "www.palmach.org.il")
def norm(s):
    return "".join(c for c in s if unicodedata.category(c) not in ("Cf", "Zs", "Cc") and not c.isspace() and not "֑" <= c <= "ׇ" and c not in "־-–—\"'״׳.,;:()[]«»")
def plain(w):
    w = re.sub(r"<ref[^>/]*/>", "", w); w = re.sub(r"<ref[^>]*>.*?</ref>", "", w, flags=re.S); w = re.sub(r"<!--.*?-->", "", w, flags=re.S)
    for _ in range(6): w = re.sub(r"\{\{[^{}]*\}\}", "", w)
    w = re.sub(r"\[\[(?:קובץ|File|Image|תמונה|ملف):[^\]]*\]\]", "", w)
    w = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", w); w = re.sub(r"\[\[([^\]]*)\]\]", r"\1", w)
    w = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", w); w = re.sub(r"'{2,}", "", w); w = re.sub(r"<[^>]+>", "", w)
    return w.replace("&nbsp;", " ")
def fetch(title, rev, lang="he"):
    os.makedirs(CACHE, exist_ok=True); f = os.path.join(CACHE, f"{lang}_{rev}.txt")
    if os.path.exists(f): return open(f, encoding="utf-8").read()
    u = f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(title)}&oldid={rev}&action=raw"
    try:
        t = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "goinfo-research/1.0"}), timeout=40).read().decode("utf-8")
    except Exception:
        return ""
    t = norm(plain(t)); open(f, "w", encoding="utf-8").write(t); return t
def frag(quote):
    q = re.sub(r"^\s*\[\.\.\.\]\s*", "", quote.strip()); q = q.split("[...]")[0].strip(); words = q.split()[:8]
    t = " ".join(words).strip(" «»\"״,.;:")
    return "#:~:text=" + urllib.parse.quote(t, safe="").replace("-", "%2D")
def permalink(title, rev, lang="he"):
    return f"https://{lang}.wikipedia.org/w/index.php?title={urllib.parse.quote(title)}&oldid={rev}"
def locate(quote, arts):
    seg = norm(re.sub(r"^\s*\[\.\.\.\]\s*", "", quote).split("[...]")[0])[:40]
    if len(seg) < 12: return None
    for title, a in arts.items():
        lang = a.get("lang", "he")
        if seg in fetch(title, a["revid"], lang): return permalink(title, a["revid"], lang)
    return None
def apply(ev):
    arts = {t: a for t, a in (ev.get("source", {}).get("articles") or {}).items() if a.get("revid")}
    main = ev.get("source", {})
    if main.get("title") and main.get("revid") and main["title"] not in arts: arts[main["title"]] = {"revid": main["revid"]}
    n = gaps = 0; byt = {}; byq = {}
    for c in ev["events"]:
        s = c.get("src") or {}; u = s.get("u")
        if u and "wikipedia.org" in u: url = u.split("#")[0] + frag(c["quote"])
        elif u and u.endswith(".pdf"): url = u + (f"#page={s['p']}" if s.get("p") else "")
        elif u: url = u
        else:
            base = locate(c["quote"], arts); url = (base + frag(c["quote"])) if base else None
        if url: c["source_url"] = url; byt[c["title"]] = url; byq[c["quote"]] = url; n += 1
        else: gaps += 1
    for l in (ev.get("scene") or {}).get("log", []):
        if l.get("q") in byq: l["href"] = byq[l["q"]]
        elif l.get("n") in byt: l["href"] = byt[l["n"]]
    ev["source_links"] = {"with_link": n, "gaps": gaps, "total": len(ev["events"])}
    return n


def main(argv):
    """--write FILE...      rewrite each events file with source_url/href (static data files, e.g. April)
       --map OUT STAGE_EVENTS  write {card id: url} for a page whose cards are assembled at build time (Six-Day whole page); extra articles from war/data/1967-*-events.json + 1967-casualties.json are searched too"""
    import glob
    if argv and argv[0] == "--write":
        for f in argv[1:]:
            d = json.load(open(f, encoding="utf-8")); apply(d)
            for k in ("source_links",): d.pop(k, None)
            json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(f, "links added")
    elif argv and argv[0] == "--map":
        out, stage = argv[1], argv[2]; d = json.load(open(stage, encoding="utf-8")); arts = dict(d.get("source", {}).get("articles") or {})
        for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "war", "data", "1967-06-*-events.json"))):
            for t, a in (json.load(open(f, encoding="utf-8"))["source"].get("articles") or {}).items(): arts.setdefault(t, {"revid": a["revid"]})
        cas = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "war", "data", "1967-casualties.json")
        if os.path.exists(cas):
            for a in json.load(open(cas, encoding="utf-8"))["articles"].values():
                if a.get("revid"): arts.setdefault(a["title"], {"revid": a["revid"], "lang": a["lang"]})
        d.setdefault("source", {})["articles"] = arts; apply(d)
        m = {c["id"]: c["source_url"] for c in d["events"] if c.get("source_url")}
        json.dump(m, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0); print(out, len(m), "of", len(d["events"]))
if __name__ == "__main__": main(sys.argv[1:])
