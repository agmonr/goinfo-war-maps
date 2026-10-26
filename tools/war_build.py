#!/usr/bin/env python3
"""/war/ - history pages by year: the hub, a page per year, and one page per battle (text + static image + the interactive map).

  python3 tools/war_build.py --stage DIR [--images DIR] [--site https://goinfo.co.il]

HELD (the owner + coordinator, freeze 2026-10-18): every page carries <meta name="robots" content="noindex, nofollow">; nothing here writes a
sitemap, nothing links to /war/ from an indexed page, no robots.txt Disallow (a Disallow would hide the noindex tag from Google - ops advice).
Links between the generated pages are RELATIVE, so the same stage works at /war/ and at a preview prefix; the canonical is absolute.

One battle = two files in war/data/: <date>.json (our own Hebrew text: title, lead, summary, timeline of 17 entries with a place
precision each, places, aftermath, still_t, still_alt) and <date>-events.json (the structured events the map reads, derived from the
Hebrew Wikipedia article under CC BY-SA 4.0). To add a battle: add the two files, run tools/war_image.py (static image of the key
moment, 1200x630, used as og:image and inline), run this script. The map page is war/templates/battle-map.html (one template for every battle).
"""
import argparse, html, json, re, shutil, sys, urllib.parse
from war_place_side import side as _place_side


def _tl_attr(e):
    """timeline row on a day page: pressing it seeks the map (iframe) to that minute of the day; rows with no clock time (start 0) are not clickable"""
    return f' data-min="{e["start"]}" tabindex="0" title="לחיצה: קפיצה לרגע הזה במפה"' if e.get('start') else ''


def add_place_sides(ev, il_now=()):
    """side of every place at the START of this day: pre-war ownership, except places the previous days' control circles show as entered by the IDF (those are ours from the next morning)"""
    for k, q in (ev.get('places') or {}).items():
        q['side'] = 'il' if k in il_now else _place_side(k)


def _icons_on(ev, stem=None):
    """the owner 10-19 GO: the icons package (kinds, side rings, units stay, labels, smoke ...) is on for every scene page"""
    if not ev.get('scene'):
        ev['icons'] = True      # April: the older engine; same flag, read as D.icons
    if ev.get('scene'):
        ev['scene']['icons'] = True
        ctl = ev['scene'].get('control')
        if ctl:                       # no hand-drawn line/label ships: the 1949 polygon is dropped, the circles keep a plain name
            ctl.pop('base', None)
            ctl['label'] = 'עיגול שליטה: מקום שהערך מזכיר שכוחות צה"ל נכנסו אליו (סכמטי)'
            for g in ctl.get('grow', []):
                g['label'] = g['label'].replace('קו חזית משוער: ', 'שליטה ישראלית (משוער): ')
        from war_act_minutes import MINUTES
        for a in ev['scene'].get('acts', []):
            m = MINUTES.get((stem or '')[:10], {}).get(a.get('s'))
            if m is not None:
                a['min'] = m


def _il_taken(data, stem):
    """place ids entered by the IDF on earlier days: the control circles of the previous day's scene (they are cumulative)"""
    import datetime
    try:
        d = datetime.date.fromisoformat(stem[:10]) - datetime.timedelta(days=1)
        pj = data / f'{d.isoformat()}-events.json'
        if pj.is_file():
            sc = (json.loads(pj.read_text(encoding='utf-8')).get('scene') or {})
            return {g['id'] for g in (sc.get('control') or {}).get('grow', [])}
    except Exception:
        pass
    return set()

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import mast_inject  # noqa: E402

HUB_NAME = "מלחמות ואירועים צבאיים לפי שנה"          # placeholder wording until the owner answers (coordinator 2026-10-18)
PREC = {"exact": ("מקום מדויק", "ex"), "approximate": ("אזור משוער", "ap"), "none": ("מקום לא צוין במקור", "no"), "schematic": ("סכמטי", "sc")}

def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)

STYLE = """<style>
 .war-ctx{font-weight:600;color:var(--muted)} .war-fig{margin:14px 0}.war-fig img{width:100%;height:auto;border-radius:12px;border:1px solid var(--border)}
 .war-fig figcaption{font-size:13px;color:var(--muted)} .war-tl{list-style:none;padding:0;margin:12px 0}.war-tl li{border-inline-start:4px solid var(--border);padding:6px 12px;margin-bottom:10px}
 .war-tl time{display:block;font-weight:700;color:var(--accent,#1d5ea8);font-size:14px}.war-tl small{display:block;color:var(--muted);font-size:12.5px;margin-top:2px}
 .badge{display:inline-block;font-size:11.5px;border:1px solid var(--border);border-radius:6px;padding:0 6px;margin-inline-end:4px}
 .badge.ex{color:#1a6b3c;border-color:#1a6b3c}.badge.ap{color:#8a5a00;border-color:#8a5a00}.badge.no{color:#b3261e;border-color:#b3261e}.badge.sc{color:#555}
 .war-app{height:100dvh;min-height:420px;background:#e8e4dc}html body>section.war-app{zoom:1!important;inline-size:100%!important}.war-app iframe{display:block;width:100%;height:100%;border:0}.war-up{display:inline-block;margin:8px 0}
 .war-nav{display:flex;flex-wrap:wrap;gap:8px 16px;justify-content:space-between;align-items:center;border:1px solid var(--border);border-radius:12px;padding:8px 12px;margin:10px 0;font-size:14px}.war-nav a{text-decoration:none}.war-nav .war-nav-mid{flex:1;text-align:center}
 .war-day{border:1px solid var(--border);border-radius:12px;padding:12px 14px;margin:12px 0}.war-day h3{margin:0 0 4px}.war-day .war-links{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0;font-size:14px}.war-day details{margin-top:8px}.war-day li{margin:4px 0}
 .war-cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));list-style:none;padding:0}.war-cards a{display:block;border:1px solid var(--border);border-radius:12px;padding:12px;text-decoration:none}
 .war-chips{display:none;gap:8px;flex-wrap:wrap;margin:10px 0}.chips-on .war-chips{display:flex}.war-chip{font:inherit;border:1px solid var(--border);background:var(--surface,#fff);border-radius:999px;padding:8px 16px;min-height:44px;cursor:pointer}.war-chip[aria-pressed=true]{background:var(--accent,#1d5ea8);color:#fff}
 .war-tl li[hidden],.war-areabox[hidden]{display:none}.badge.ar{background:#eef3fb;color:#1d3f73}
 .cas-sec{margin-top:4px;color:var(--muted)}.cas-note{background:var(--surface-2,#f6f3ec);border-inline-start:4px solid #8a5a00;padding:8px 12px;border-radius:8px;font-size:14px}
 .cas-tab td,.cas-tab th{vertical-align:top;text-align:start}.cas-line{margin-bottom:6px}.cas-w{font-weight:600}.cas-none{color:var(--muted)}.badge.lg{background:#f1ede4;color:#444}
 .cas-card{border:1px solid var(--border);border-radius:10px;padding:6px 12px;margin:8px 0}.cas-card summary{cursor:pointer;font-weight:600;min-height:32px}.cas-card q{font-size:13.5px}.cas-card h4{margin:10px 0 2px}
 .cas-clock{color:var(--muted);font-weight:400}.war-cas [hidden],.cas-tab tr[hidden]{display:none}
 .held{background:#fff3cd;color:#5c4400;border:1px solid #e8cf7a;border-radius:10px;padding:6px 12px;font-size:14px;margin-bottom:12px}
</style>"""

SHELL = """<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, nofollow">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
{ogimg}<link rel="stylesheet" href="/src/style.css">
{style}
<script type="module" src="/src/mast.js" data-mast="auto"></script>
<script type="application/ld+json">{jsonld}</script>
</head>
<body class="hafkaot-page">
{preapp}{masthead}
<main class="wrap">
<nav aria-label="מסלול ניווט" class="acc-hint">{crumbs}</nav>
{body}
</main>
</body>
</html>
"""

def crumbs(pairs):
    return " ← ".join(f'<a href="{esc(h)}">{esc(l)}</a>' if h else f"<span>{esc(l)}</span>" for l, h in pairs)

def page(title, desc, canonical, heading, crumb_pairs, body, jsonld, ogimg="", preapp=""):
    masthead = mast_inject.block(heading, canonical, prefix="/", share_title=title)
    og = f'<meta property="og:image" content="{esc(ogimg)}">\n<meta name="twitter:card" content="summary_large_image">\n' if ogimg else ""
    return SHELL.format(title=esc(title), desc=esc(desc), canonical=esc(canonical), ogimg=og, style=STYLE, masthead=masthead, preapp=preapp,
                        crumbs=crumbs(crumb_pairs), body=body, jsonld=json.dumps(jsonld, ensure_ascii=False))

def ld_breadcrumb(items):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}

def wiki_urls(title, revid, lang="he"):
    q = urllib.parse.quote(title.replace(" ", "_"))
    h = f"https://{lang}.wikipedia.org"
    return (f"{h}/wiki/{q}", f"{h}/w/index.php?title={q}&oldid={revid}", f"{h}/w/index.php?title={q}&action=history")

def article_items(src):
    """one <li> per source article with its revision permalink and author history (CC BY-SA attribution per article)"""
    out = []
    for title, info in src["articles"].items():
        page_u, rev_u, hist_u = wiki_urls(title, info["revid"])
        out.append(f'<li><a href="{esc(page_u)}" rel="noopener">{esc(title)}</a> (<a href="{esc(rev_u)}" rel="noopener">גרסה {info["revid"]}</a>, <a href="{esc(hist_u)}" rel="noopener">כותבי הערך</a>)</li>')
    return "".join(out)


LANG = {"he": "עברית", "en": "אנגלית", "ar": "ערבית", "de": "גרמנית"}
WHAT = {"k": "הרוגים", "w": "פצועים", "g": "נפגעים / אחר"}
CAS_NOTE = ("<strong>הנתונים חלקיים.</strong> המספרים כאן הם רק אלה שמופיעים במקורות המצוינים (ערכים בוויקיפדיה בעברית, באנגלית ובערבית), בלי השלמות שלנו. "
            "„לא צוין” פירושו שהמקורות לא נותנים מספר, לא שאין נפגעים. הנתונים על ישראל לפי המקורות בעברית, והנתונים על הצד השני לפי המקורות באנגלית ובערבית (מספר שרק שפה אחרת נותנת על ישראל מופיע כהערה קטנה, לא כנתון שלנו). כשמקורות חלוקים מוצגים שני המספרים וטווח; טענה שמיוחסת למישהו מוצגת בנפרד. "
            "אין כאן שמות של נפגעים. אין מונה רץ, כי לצד אחד של היום כמעט אין נתונים.")

def _num(v):
    t = v.replace("~", "").replace(",", "").strip()
    return int(t) if t.isdigit() else None

def _v(v):
    """a figure for display: '~' becomes כ-, pure numbers stay left-to-right so ranges do not flip in RTL text"""
    t = str(v).replace("~", "כ-")
    return esc(t) if any("\u0590" <= c <= "\u05ff" for c in t) else f'<bdi dir="ltr">{esc(t)}</bdi>'

def _lang_badge(cas, art):
    return f'<span class="badge lg">{LANG[cas["articles"][art]["lang"]]}</span>'

def _dedupe(cas, figs):
    """two articles of the same language giving the same figure show once (the quotes of both stay on the card)"""
    out, seen = [], set()
    for f in figs:
        k = (f["what"], f["scope"], f["val"], cas["articles"][f["art"]]["lang"])
        if k not in seen:
            seen.add(k); out.append(f)
    return out

def _cell_core(cas, figs):
    """one side of one event: lines per what/scope, a range when sources disagree, attributed claims on their own line"""
    if not figs:
        return '<span class="cas-none">לא צוין</span>'
    figs = _dedupe(cas, figs)
    out, seen = [], []
    for f in figs:
        key = (f["what"], f["scope"])
        if key not in seen:
            seen.append(key)
    for what, scope in seen:
        group = [f for f in figs if f["what"] == what and f["scope"] == scope]
        claims = [f for f in group if "טענה" in f["qual"]]
        plain = [f for f in group if f not in claims]
        for part, is_claim in ((plain, False), (claims, True)):
            if not part:
                continue
            nums = [_num(f["val"]) for f in part]
            rng = ""
            if len(part) > 1 and all(n is not None for n in nums) and len(set(nums)) > 1:
                rng = f'<strong><bdi dir="ltr">{min(nums):,}–{max(nums):,}</bdi></strong> <small>(מקורות חלוקים)</small> '
            vals = " · ".join(f'{_v(f["val"])} {_lang_badge(cas, f["art"])}' for f in part)
            lab = esc(WHAT[what]) + (" - טענה מיוחסת" if is_claim else "") + (f' <small>({esc(scope)})</small>' if scope else "")
            out.append(f'<div class="cas-line"><span class="cas-w">{lab}:</span> {rng}{vals}</div>')
    return "".join(out)

def _cell(cas, figs, side):
    """the owner 10-18: OUR (Israeli) casualties come from the Hebrew articles, the other side's from en/ar. Israeli figures that only
    en/ar give are never shown as our figure - a small footnote line; Arab-side Hebrew figures are footnoted when en/ar have figures
    for the event, and shown as the figure only when they are the sole source."""
    prim = ("he",) if side == "il" else ("en", "ar", "de")
    lang = lambda f: cas["articles"][f["art"]]["lang"]
    main = [f for f in figs if lang(f) in prim]
    sec = [f for f in figs if lang(f) not in prim]
    if side == "ar" and not main:
        main, sec = sec, []
    if not main and not sec:
        return '<span class="cas-none">לא צוין</span>'
    out = _cell_core(cas, main) if main else '<span class="cas-none">לא צוין</span>'
    if sec:
        out += '<div class="cas-sec"><small>' + ("מקורות בשפות אחרות, לא הנתון שלנו: " if side == "il" else "בעברית: ") + _cell_core(cas, sec).replace('<div class="cas-line">', '<span class="cas-line">').replace("</div>", "</span> ") + "</small></div>"
    return out

def _srcline(cas, f, side=""):
    a = cas["articles"][f["art"]]
    qd = ' dir="ltr" lang="%s"' % a["lang"] if a["lang"] != "he" else ""
    if a.get("kind") == "web":
        return (f'<li><span class="cas-w">{esc(WHAT[f["what"]])}: {_v(f["val"])}</span> <small>({esc(f["qual"])}{" · " + esc(f["scope"]) if f["scope"] else ""})</small> '
                f'{_lang_badge(cas, f["art"])} <q{qd}>{esc(f["quote"])}</q> '
                f'<small>(<a href="{esc(a["url"])}" rel="noopener">{esc(a["title"])}</a> · {esc(a["type"])} · נשלף {esc(a["retrieved"])})</small></li>')
    page_u, rev_u, hist_u = wiki_urls(a["title"], a["revid"], a["lang"])
    return (f'<li><span class="cas-w">{esc(WHAT[f["what"]])}: {_v(f["val"])}</span> <small>({esc(f["qual"])}{" · " + esc(f["scope"]) if f["scope"] else ""})</small> '
            f'{_lang_badge(cas, f["art"])}{" <small>(לא הנתון שלנו)</small>" if side == "il" and a["lang"] != "he" else ""} <q{qd}>{esc(f["quote"])}</q> '
            f'<small>(<a href="{esc(page_u)}" rel="noopener">{esc(a["title"])}</a>, <a href="{esc(rev_u)}" rel="noopener">גרסה {a["revid"]}</a>)</small></li>')


def _text_side(cas, figs, side):
    """plain-text twin of _cell for the animation (same primary-language rule, same ranges, same labels); returns (main, footnote)"""
    prim = ("he",) if side == "il" else ("en", "ar", "de")
    lang = lambda f: cas["articles"][f["art"]]["lang"]
    short = {"he": "עב", "en": "אנ", "ar": "ער", "de": "גר"}
    main = [f for f in figs if lang(f) in prim]; sec = [f for f in figs if lang(f) not in prim]
    if side == "ar" and not main:
        main, sec = sec, []
    def render(fl):
        fl = _dedupe(cas, fl)
        parts, seen = [], []
        for f in fl:
            if (f["what"], f["scope"]) not in seen:
                seen.append((f["what"], f["scope"]))
        for what, scope in seen:
            grp = [f for f in fl if f["what"] == what and f["scope"] == scope]
            for part, claim in (([f for f in grp if "טענה" not in f["qual"]], False), ([f for f in grp if "טענה" in f["qual"]], True)):
                if not part:
                    continue
                nums = [_num(f["val"]) for f in part]
                rng = f'{min(nums):,}–{max(nums):,} (מקורות חלוקים): ' if len(part) > 1 and all(n is not None for n in nums) and len(set(nums)) > 1 else ""
                vals = " · ".join(f'{f["val"].replace("~", "כ-")} ({short[lang(f)]})' for f in part)
                parts.append(f'{WHAT[what]}{" - טענה מיוחסת" if claim else ""}{" (" + scope + ")" if scope else ""}: {rng}{vals}')
        return "; ".join(parts)
    return (render(main) if main else "לא צוין", render(sec) if sec else "")

def casualties_anim(cas, key, places):
    out = []
    for e in cas["data"][key]:
        il, ilsec = _text_side(cas, e["il"], "il"); ar, arsec = _text_side(cas, e["ar"], "ar")
        pl = places.get(e.get("at") or "")
        out.append({"id": e["id"], "t": e["t"], "area": e.get("area"), "clock": e["clock"], "name": e["name"], "il": il, "ilsec": ilsec, "ar": ar, "arsec": arsec, "oth": _text_side(cas, e["oth"], "ar")[0] if e.get("oth") else "",
                    "at": [pl["lat"], pl["lon"]] if pl else None, "at_name": pl["name"] if pl else ""})
    return out

def _oth_row(cas, e):
    """optional third party (e.g. the American crew of the Liberty): a labelled line under the event name, never in the Israeli or the Arab column"""
    return f'<br><small class="cas-oth">צד שלישי (לא צד בלחימה): {_cell_core(cas, e["oth"])}</small>' if e.get("oth") else ""

def casualties_html(cas, events, multi=False, names=None):
    """summary table + a card (details) per event + the sober note. events: list of dicts from war/data/1967-casualties.json"""
    rows, cards = [], []
    for e in events:
        a = f' data-a="{e["area"]}"' if multi else ""
        rows.append(f'<tr{a}><th scope="row"><small class="cas-clock"><bdi>{esc(e["clock"])}</bdi></small><br>{esc(e["name"])}{_oth_row(cas, e)}</th><td>{_cell(cas, e["il"], "il")}</td><td>{_cell(cas, e["ar"], "ar")}</td></tr>')
        figs = e["il"] + e["ar"]
        body = ""
        for side, fl in (("ישראל", e["il"]), ("צד ערב", e["ar"])):
            body += f'<h4>{side}</h4>' + ("<ul>" + "".join(_srcline(cas, f, "il" if side == "ישראל" else "ar") for f in fl) + "</ul>" if fl else '<p class="cas-none">לא צוין</p>')
        if e.get("oth"):
            body += '<h4>צד שלישי (לא צד בלחימה)</h4><ul>' + "".join(_srcline(cas, f, "ar") for f in e["oth"]) + "</ul>"
        cards.append(f'<details class="cas-card" id="cas-{e["id"]}"{a}><summary><bdi>{esc(e["clock"])}</bdi> · {esc(e["name"])}</summary>{body}</details>')
    return (f'<div class="war-cas"><p class="cas-note">{CAS_NOTE}</p>'
            f'<div class="matrix-wrap"><table class="matrix prose cas-tab"><caption>הרוגים ופצועים לפי אירוע</caption><thead><tr><th>אירוע</th><th>ישראל</th><th>צד ערב</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<h3>הציטוטים והמקורות לכל מספר</h3>{"".join(cards)}</div>')

def war_totals_html(cas):
    rows = []
    for w in cas["data"]["war"]:
        s_ = "ar" if w["who"] != "ישראל" else "il"
        rows.append(f'<tr><th scope="row">{esc(w["who"])}</th><td>{_cell(cas, w["k"], s_)}</td><td>{_cell(cas, w["w"], s_)}</td><td>{_cell(cas, w.get("g", []), s_)}</td></tr>')
    srcs = "".join(_srcline(cas, f) for w in cas["data"]["war"] for f in w["k"] + w["w"] + w.get("g", []))
    return (f'<h3>לכל המלחמה (לא רק יום אחד)</h3><p class="cas-note">המספרים האלה הם סיכום של שישה ימי לחימה. הם מובאים להקשר בלבד ואינם שייכים ליום המוצג כאן.</p>'
            f'<div class="matrix-wrap"><table class="matrix prose cas-tab"><caption>סיכום לכל המלחמה</caption><thead><tr><th>צד</th><th>הרוגים</th><th>פצועים</th><th>נפגעים בלי פירוט, שבויים</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<p class="cas-note">הנתונים חלקיים: לסוריה ולעיראק אין מקור מעבר לערכים בוויקיפדיה שצוינו כאן, ולירדן ולמצרים המקורות חלוקים. מספרים של מקורות שונים אינם מסוכמים.</p><details class="cas-card"><summary>הציטוטים והמקורות</summary><ul>{srcs}</ul></details>')

def cas_credit(cas, events):
    """CC BY-SA credit for the en/ar (and extra he) articles the casualty figures come from"""
    used = []
    for e in events:
        for f in e["il"] + e["ar"] + e.get("oth", []):
            if f["art"] not in used:
                used.append(f["art"])
    for w in cas["data"]["war"]:
        for f in w["k"] + w["w"] + w.get("g", []):
            if f["art"] not in used:
                used.append(f["art"])
    li = []
    for k in used:
        a = cas["articles"][k]
        if a.get("kind") == "web":
            continue
        page_u, rev_u, hist_u = wiki_urls(a["title"], a["revid"], a["lang"])
        li.append(f'<li>{LANG[a["lang"]]}: <a href="{esc(page_u)}" rel="noopener">{esc(a["title"])}</a> (<a href="{esc(rev_u)}" rel="noopener">גרסה {a["revid"]}</a>, <a href="{esc(hist_u)}" rel="noopener">כותבי הערך</a>)</li>')
    return "".join(li)

def cas_credit_web(cas, events):
    """sources that are NOT Wikipedia (the owner 2026-10-19: for the other side's figures): named, typed, linked, with the retrieval date; no CC BY-SA claim is made for them"""
    used = []
    for e in events:
        for f in e["il"] + e["ar"] + e.get("oth", []):
            if f["art"] not in used:
                used.append(f["art"])
    for w in cas["data"]["war"]:
        for f in w["k"] + w["w"] + w.get("g", []):
            if f["art"] not in used:
                used.append(f["art"])
    li = [f'<li>{LANG[a["lang"]]}: <a href="{esc(a["url"])}" rel="noopener">{esc(a["title"])}</a> ({esc(a["type"])}; נשלף {esc(a["retrieved"])}; ציטוט קצר בלבד)</li>' for a in (cas["articles"][k] for k in used) if a.get("kind") == "web"]
    return ('<p>מקורות נוספים לנתוני הצד השני, שאינם ויקיפדיה (ציטוט קצר ומקור מצוין בכל שורה; אין לגביהם טענה לרישיון חופשי):</p><ul>' + "".join(li) + "</ul>") if li else ""

def credit_html(b, ev, cas=None, ckey=None):
    src = ev["source"]
    if src.get("articles"):
        head = f'העובדות לקוחות מהערכים הבאים בוויקיפדיה העברית, כל אחד בגרסה המצוינת, ברישיון <a href="{esc(src["license_url"])}" rel="noopener">{esc(src["license"])}</a>:<ul>{article_items(src)}</ul>'
    else:
        head = (f'הטקסט והעובדות לקוחים מהערך <a href="{esc(src["url"])}" rel="noopener">„{esc(src["title"])}”</a> בוויקיפדיה העברית (<a href="{esc(src["permalink"])}" rel="noopener">גרסה {src["revid"]}</a>, '
                f'<a href="{esc(src["authors_url"])}" rel="noopener">כותבי הערך</a>), ברישיון <a href="{esc(src["license_url"])}" rel="noopener">{esc(src["license"])}</a>. ')
    notes = "".join(f"<br>{esc(n)}" for n in b.get("credit_notes", []))
    if cas:
        notes += f'<br>נתוני הרוגים ופצועים (מספרים וציטוטים קצרים בלבד) לקוחים גם מהערכים הבאים בוויקיפדיה, ברישיון {esc(src["license"])}:<ul>{cas_credit(cas, cas["data"][ckey])}</ul>{cas_credit_web(cas, cas["data"][ckey])}'
    return (head + f'הסיכום, הציטוטים והקובץ הנגזר <a href="events.json">events.json</a> נכתבו מחדש ונגזרו מהם ומופצים באותו רישיון, {esc(src["license"])}. נעשו שינויים: חלוקה לאירועים וקיצור. '
            f'<br>קואורדינטות הישובים והערים: ויקיפדיה העברית (נקודת היישוב/העיר). אזורים משוערים וקווים סכמטיים שרטטנו אנחנו ואינם נתון מהמקור. מפת רקע: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">תורמי OpenStreetMap</a>.{notes}')

SRC_BAR_RE = re.compile(r'<span>מקור: <a href="[^"]*" rel="noopener">ויקיפדיה העברית</a> · CC BY-SA 4.0</span>')

def src_bar(ev):
    """the footer source line of a war page: the page's OWN main article (the template carries the April 1967 article's link, which was wrong on every other war page)"""
    s = ev["source"]
    return f'<span>מקור: <a href="{esc(s["permalink"])}" rel="noopener">ויקיפדיה העברית: {esc(s["title"])}</a> · {esc(s["license"])}</span>'

def map_page(template, b, url, events_url, mode, credit=""):
    if b.get("src_bar"):
        assert SRC_BAR_RE.search(template), "template footer changed"
        template = SRC_BAR_RE.sub(lambda m: b["src_bar"], template, count=1)
    return (template.replace("__DATE__", str(b.get("date") or "")).replace("__EVENTS_URL__", events_url).replace("__CANONICAL__", url).replace("__TITLE__", esc(b["title"]))
            .replace("__DESC__", esc(b["description"])).replace("__MODE__", mode).replace("__CREDIT__", credit).replace("__H1__", esc(b["h1"])).replace("__CTX__", esc(b["context"])))

def app_section(src):
    return (f'<section class="war-app" aria-label="המפה והאנימציה"><iframe id="war-map" src="{src}" title="מפה ואנימציה" allow="fullscreen autoplay"></iframe></section>')

JUMP_JS = """<script>(function(){var fr=document.getElementById('war-map');function go(ev){var li=ev.target.closest&&ev.target.closest('.war-tl li[data-min]');if(!li||(ev.target.closest&&ev.target.closest('a'))||(ev.type==='keydown'&&ev.key!=='Enter'))return;if(fr&&fr.contentWindow){try{fr.contentWindow.postMessage({warSeekMin:+li.dataset.min},'*')}catch(x){}var t=document.getElementById('war-top');if(t)t.scrollIntoView({behavior:'smooth'})}}document.addEventListener('click',go);document.addEventListener('keydown',go)})();</script><script>addEventListener('message',function(e){if(e.data&&e.data.warScroll==='text'){var t=document.getElementById('war-text');if(t)t.scrollIntoView({behavior:'smooth'})}
if(e.data&&e.data.warCas){var c=document.getElementById('cas-'+String(e.data.warCas).replace(/[^a-z0-9]/g,''));if(c){if(c.hidden)return;c.open=true;c.scrollIntoView({behavior:'smooth',block:'center'})}}});</script>"""

AREA_JS = """<script>
(function(){var A=%s,chips=[].slice.call(document.querySelectorAll('.war-chip')),items=[].slice.call(document.querySelectorAll('.war-tl li,.war-cas [data-a]')),boxes=[].slice.call(document.querySelectorAll('.war-areabox')),fig=document.getElementById('war-still'),fr=document.getElementById('war-map'),cur='all';
function set(id,fromMap){if(A.indexOf(id)<0)id='all';cur=id;chips.forEach(function(c){c.setAttribute('aria-pressed',String(c.dataset.a===id))});
 items.forEach(function(li){li.hidden=!(id==='all'||li.dataset.a===id)});boxes.forEach(function(b){b.hidden=b.dataset.a!==id});
 if(fig){fig.src='still-'+id+'.jpg'}
 if(!fromMap&&fr&&fr.contentWindow){try{fr.contentWindow.postMessage({warArea:id},'*')}catch(e){}}}
chips.forEach(function(c){c.addEventListener('click',function(){history.replaceState(null,'',c.dataset.a==='all'?location.pathname:'#'+c.dataset.a);set(c.dataset.a)})});
addEventListener('message',function(e){if(e.data&&e.data.warArea){history.replaceState(null,'',e.data.warArea==='all'?location.pathname:'#'+e.data.warArea);set(e.data.warArea,true)}});
addEventListener('hashchange',function(){set(location.hash.slice(1))});
var h=location.hash.slice(1);if(h)set(h);else set('all');
if(fr){fr.addEventListener('load',function(){if(cur!=='all')set(cur)});if(!fr.src&&fr.dataset.src)fr.src=fr.dataset.src+(h&&A.indexOf(h)>=0?'#'+h:'')}
document.documentElement.classList.add('chips-on')})();
</script>"""

def nav_html(b):
    """prev / overview / next strip for the days of one war (b["_nav"] = (prev, next), set in main); the overview is the year page"""
    pv, nx = b.get("_nav", (None, None))
    a = lambda x, lab: f'<a href="../{esc(x["slug"])}/" rel="{"prev" if lab == "prev" else "next"}">{("→ היום הקודם: " if lab == "prev" else "היום הבא: ") + esc(x.get("short_day") or x["h1"])}{" ←" if lab != "prev" else ""}</a>'
    return ('<nav class="war-nav" aria-label="ימי המלחמה">' + (a(pv, "prev") if pv else "<span></span>") + '<a class="war-nav-mid" href="../">סקירת המלחמה: כל הימים</a>'
            + (a(nx, "next") if nx else "<span></span>") + '</nav>')

def multi_battle_page(b, ev, site, have_images, cas=None):
    y, slug = b["year"], b["slug"]
    url = f"{site}/war/{y}/{slug}/"
    img = f"{url}og.jpg" if have_images else ""
    src = ev["source"]
    ids = ["all"] + [t["id"] for t in b["areas"]]
    chips = '<button class="war-chip" type="button" data-a="all" aria-pressed="true">הכל</button>' + "".join(f'<button class="war-chip" type="button" data-a="{t["id"]}" aria-pressed="false">{esc(t["name"])}</button>' for t in b["areas"])
    names = {t["id"]: t["name"] for t in b["areas"]}
    rows = "".join(f'<li data-a="{e["area"]}"{_tl_attr(e)}><time>{esc(e["clock"])}</time><span class="badge ar">{esc(names[e["area"]])}</span> {esc(e["text"])}<small><span class="badge {PREC[e["place_precision"]][1]}">{PREC[e["place_precision"]][0]}</span>{esc(e["place"])}</small></li>' for e in b["timeline"])
    boxes = "".join(f'<div class="war-areabox" data-a="{t["id"]}" hidden><h3>{esc(t["name"])}</h3><p>{esc(t["intro"])}</p><p class="war-ctx">{esc(t["note"])}</p></div>' for t in b["areas"])
    places = "".join(f'<tr><td>{esc(p["name"])}</td><td><span class="badge {PREC[p["precision"]][1]}">{PREC[p["precision"]][0]}</span></td><td>{esc(p["basis"])}</td></tr>' for p in b["places"])
    fig = (f'<figure class="war-fig"><img id="war-still" src="still-all.jpg" alt="{esc(b["still_alt"])}" width="1200" height="630" loading="eager"><figcaption>תמונה סכמטית של הזירה שנבחרה. הנקודות המדויקות הן יישובים וערים; אזורים וחיצים סכמטיים. <a href="map/">פתיחה במסך מלא</a></figcaption></figure>') if have_images else ""
    sources = article_items(src)
    CASSEC_M = (f'<h2 id="casualties">הרוגים ופצועים</h2>' + casualties_html(cas, cas["data"][b.get("cas_key", "jun")], True) + war_totals_html(cas)) if cas else ""
    CASCR = (f'<p>נתוני ההרוגים והפצועים לקוחים גם מהערכים הבאים, ברישיון {esc(src["license"])} (מספרים וציטוטים קצרים; נעשו שינויים: תרגום וקיצור):</p><ul>{cas_credit(cas, cas["data"][b.get("cas_key", "jun")])}</ul>{cas_credit_web(cas, cas["data"][b.get("cas_key", "jun")])}') if cas else ""
    body = f"""<article id="war-text">
<p class="war-ctx">{esc(b["context"])}</p>
{nav_html(b)}
<p>{esc(b["lead"])}</p>
{"".join(f"<p>{esc(p)}</p>" for p in b["summary"])}
<h2 id="map">התמקדות לפי אזור</h2>
<div class="war-chips" role="group" aria-label="התמקדות באזור">{chips}</div>
{boxes}
{fig}
<p><a class="war-up" href="#war-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false">↑ חזרה למפה והאנימציה</a> · <a href="map/">פתיחה במסך מלא</a> · <a href="events.json">הנתונים של המפה (events.json)</a></p>
<h2 id="timeline">ציר הזמן של היום</h2>
<p>כל האירועים לפי שעה. הכפתורים למעלה מסננים לפי אזור (והמפה מתמקדת באזור).</p>
<ol class="war-tl">{rows}</ol>
{CASSEC_M}<h2 id="places">מה מדויק ומה סכמטי</h2>
<div class="matrix-wrap"><table class="matrix"><caption>מקומות ומידת הדיוק במפה</caption><thead><tr><th>סוג</th><th>דיוק</th><th>על מה זה מבוסס</th></tr></thead><tbody>{places}</tbody></table></div>
<h2 id="after">אחרי {esc(b.get("day_he", "היום הראשון"))}</h2>
<ul>{"".join(f"<li>{esc(a)}</li>" for a in b["aftermath"])}</ul>
<h2 id="source">מקורות ורישיון</h2>
<p>העובדות לקוחות מהערכים הבאים בוויקיפדיה העברית, כל אחד בגרסה המצוינת (קישור לגרסה ולכותבי הערך), ברישיון <a href="{esc(src["license_url"])}" rel="noopener">{esc(src["license"])}</a>:</p>
<ul>{sources}</ul>
{CASCR}
<p>הסיכום, ציר הזמן והמפה כאן נכתבו מחדש ונגזרו מהם, ומופצים באותו רישיון, {esc(src["license"])}. מפת רקע: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">תורמי OpenStreetMap</a>.</p>
{nav_html(b)}
</article>
{AREA_JS % json.dumps(ids)}{JUMP_JS}"""
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": b["title"], "description": b["description"], "inLanguage": "he", "datePublished": b["date"], "mainEntityOfPage": url,
         "image": [img] if img else [], "license": src["license_url"], "author": {"@type": "Organization", "name": "GoInfo", "url": site + "/"},
         "publisher": {"@type": "Organization", "name": "GoInfo", "url": site + "/"}, "isBasedOn": src["permalink"], "about": {"@id": url + "#event"}},
        {"@type": "Event", "@id": url + "#event", "name": b["h1"], "startDate": b["date"], "endDate": b["date"], "description": b["lead"],
         "eventStatus": "https://schema.org/EventScheduled", "location": [{"@type": "Place", "name": t["name"], "address": {"@type": "PostalAddress", "addressCountry": "IL"}} for t in b["areas"]]},
        ld_breadcrumb([("GoInfo", site + "/"), (HUB_NAME, site + "/war/"), (str(y), f"{site}/war/{y}/"), (b["h1"], url)])]}
    pairs = [("GoInfo", "/"), (HUB_NAME, "../../"), (str(y), "../"), (b["h1"], None)]
    return page(b["title"], b["description"], url, b["h1"], pairs, body, jsonld, img, app_section("map/"))

def battle_page(b, ev, site, have_images, cas=None):
    y, slug = b["year"], b["slug"]
    url = f"{site}/war/{y}/{slug}/"
    img = f"{url}og.jpg" if have_images else ""
    rows = "".join(
        f'<li><time>{esc(t["clock"])}</time>{esc(t["text"])}<small><span class="badge {PREC[t["place_precision"]][1]}">{PREC[t["place_precision"]][0]}</span>{esc(t["place"])}</small></li>'
        for t in b["timeline"])
    places = "".join(f'<tr><td>{esc(p["name"])}</td><td><span class="badge {PREC[p["precision"]][1]}">{PREC[p["precision"]][0]}</span></td><td>{esc(p["basis"])}</td></tr>' for p in b["places"])
    src = ev["source"]
    fig = (f'<figure class="war-fig"><img src="still.jpg" alt="{esc(b["still_alt"])}" width="1200" height="630" loading="eager">'
           f'<figcaption>תמונה סכמטית של הרגע של 15:25. הבסיסים, מסלולי הטיסה ומיקום הסוללות אינם מדויקים. <a href="map/">פתיחה במסך מלא</a></figcaption></figure>') if have_images else ""
    CASSEC_B = (f'<h2 id="casualties">הרוגים ופצועים</h2>' + casualties_html(cas, cas["data"]["apr"])) if cas else ""
    body = f"""<article id="war-text">
<p class="war-ctx">{esc(b["context"])}</p>
{nav_html(b)}
<p>{esc(b["lead"])}</p>
{fig}
{"".join(f"<p>{esc(p)}</p>" for p in b["summary"])}
<h2 id="timeline">ציר הזמן של היום</h2>
<ol class="war-tl">{rows}</ol>
{CASSEC_B}<h2 id="places">מקומות ומידת הדיוק</h2>
<div class="matrix-wrap"><table class="matrix"><caption>מה מדויק ומה סכמטי במפה</caption><thead><tr><th>מקום</th><th>דיוק</th><th>על מה זה מבוסס</th></tr></thead><tbody>{places}</tbody></table></div>
<h2 id="after">אחרי הקרב</h2>
<ul>{"".join(f"<li>{esc(a)}</li>" for a in b["aftermath"])}</ul>
<h2 id="map">המפה והאנימציה</h2>
<p>האנימציה בראש העמוד מציגה את כל היום ברצף, עם ציטוט מהערך לכל שלב, סאונד אופציונלי ושליטה במהירות ובכיוון. היא סכמטית: אין בה בסיסים, מסלולים או מספרי מטוסים שהמקור לא מציין.</p>
<p><a class="war-up" href="#war-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false">↑ חזרה למפה והאנימציה</a> · <a href="map/">פתיחה במסך מלא</a> · <a href="events.json">הנתונים של המפה (events.json)</a></p>
<h2 id="source">מקור ורישיון</h2>
<p>העובדות לקוחות מהערך <a href="{esc(src["url"])}" rel="noopener">„{esc(src["title"])}”</a> בוויקיפדיה העברית (<a href="{esc(src["permalink"])}" rel="noopener">גרסה {src["revid"]}</a>, <a href="{esc(src["authors_url"])}" rel="noopener">כותבי הערך</a>) ברישיון <a href="{esc(src["license_url"])}" rel="noopener">{esc(src["license"])}</a>. הסיכום, ציר הזמן והמפה כאן נכתבו מחדש ונגזרו ממנו, ומופצים באותו רישיון, {esc(src["license"])}. מפת רקע: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">תורמי OpenStreetMap</a>.</p>
{nav_html(b)}
</article>
{JUMP_JS}"""
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": b["title"], "description": b["description"], "inLanguage": "he", "datePublished": b["date"],
         "mainEntityOfPage": url, "image": [img] if img else [], "license": src["license_url"],
         "author": {"@type": "Organization", "name": "GoInfo", "url": site + "/"}, "publisher": {"@type": "Organization", "name": "GoInfo", "url": site + "/"},
         "isBasedOn": src["permalink"], "about": {"@id": url + "#event"}},
        {"@type": "Event", "@id": url + "#event", "name": b["h1"], "startDate": b["date"], "endDate": b["date"], "description": b["lead"],
         "eventStatus": "https://schema.org/EventScheduled", "location": {"@type": "Place", "name": "דרום רמת הגולן, גדות והאון", "address": {"@type": "PostalAddress", "addressCountry": "IL"}}},
        ld_breadcrumb([("GoInfo", site + "/"), (HUB_NAME, site + "/war/"), (str(y), f"{site}/war/{y}/"), (b["h1"], url)])]}
    pairs = [("GoInfo", "/"), (HUB_NAME, "../../"), (str(y), "../"), (b["h1"], None)]
    return page(b["title"], b["description"], url, b["h1"], pairs, body, jsonld, img, app_section("map/"))

def year_page(y, items, site):
    url = f"{site}/war/{y}/"
    cards = "".join(f'<li><a href="{esc(b["slug"])}/"><strong>{esc(b["h1"])}</strong><br><span class="war-ctx">{esc(b["context"])}</span><br>{esc(b["description"])}</a></li>' for b in items)
    body = f"<article><p>היסטוריה צבאית של שנת {y}: קרבות ואירועים עם ציר זמן, מפה ואנימציה סכמטית.</p><ul class=\"war-cards\">{cards}</ul></article>"
    jsonld = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": f"מלחמות ואירועים צבאיים ב-{y}", "url": url,
              "hasPart": [{"@type": "Article", "name": b["h1"], "url": f'{url}{b["slug"]}/'} for b in items]},
              ld_breadcrumb([("GoInfo", site + "/"), (HUB_NAME, site + "/war/"), (str(y), url)])]}
    return page(f"אירועים צבאיים ב-{y}", f"קרבות ואירועים צבאיים משנת {y}: ציר זמן, מפה ואנימציה.", url, f"אירועים צבאיים ב-{y}",
                [("GoInfo", "/"), (HUB_NAME, "../"), (str(y), None)], body, jsonld)

MONTH = {4: "אפריל", 6: "יוני"}

def _day_cas_items(cas, key):
    """one line per casualty event of a day, as the pinned articles give it (text twin of the table; no sums)"""
    out = []
    for e in cas["data"].get(key, []):
        il, ilsec = _text_side(cas, e["il"], "il"); ar, arsec = _text_side(cas, e["ar"], "ar")
        oth = _text_side(cas, e["oth"], "ar")[0] if e.get("oth") else ""
        line = f'<strong>{esc(e["name"])}</strong> <small>(<bdi>{esc(e["clock"])}</bdi>)</small>: ישראל: {esc(il)}'
        if ilsec:
            line += f' <small>[בשפות אחרות, לא הנתון שלנו: {esc(ilsec)}]</small>'
        line += f'; צד ערב: {esc(ar)}'
        if arsec:
            line += f' <small>[בעברית: {esc(arsec)}]</small>'
        if oth:
            line += f'; צד שלישי (לא צד בלחימה): {esc(oth)}'
        out.append(f'<li><a href="{esc(e.get("_slug", ""))}#cas-{esc(e["id"])}">{line}</a></li>')
    return out

OVERVIEW_NOTE = ('הנתונים מוצגים לפי אירוע, כפי שכל ערך נותן אותם (טווחים, טענות מיוחסות, הבדלים בין מקורות ו"לא צוין" כשאין מספר). אין כאן מספר יומי כולל שלנו: '
                 'הערכים נותנים מספרים רק לחלק מהאירועים, בהיקפים שונים (קרב, חזית, כל המלחמה), ושקלול שלהם היה יוצר מספר שאף מקור אינו נותן. הנתונים חלקיים.')

def overview_page(y, items, site, cas):
    """the 1967 war in one page: every day with its summary, both links, and the casualty figures the pinned articles give for it"""
    url = f"{site}/war/{y}/"
    def day(b):
        sl = b["slug"]
        key = b.get("cas_key") or ("apr" if sl == "7-april" else "jun")
        lines = _day_cas_items(cas, key) if cas else []
        lines = [l.replace('href="#', f'href="{esc(sl)}/#').replace('href=""', f'href="{esc(sl)}/"') for l in lines]
        cas_block = (f'<details><summary>הרוגים ופצועים שמסרו הערכים לאותו יום ({len(lines)} אירועים)</summary><ul>{"".join(lines)}</ul></details>' if lines
                     else '<p class="war-ctx">הערכים לא נותנים נתוני הרוגים ופצועים לאירועי היום הזה.</p>')
        return (f'<section class="war-day" id="d-{esc(sl)}"><h3><a href="{esc(sl)}/">{esc(b["h1"])}</a></h3><p>{esc(b["description"])}</p>'
                f'<div class="war-links"><a href="{esc(sl)}/">עמוד הטקסט והציר</a><a href="{esc(sl)}/map/">המפה והאנימציה במסך מלא</a></div>{cas_block}</section>')
    pre = [b for b in items if not b.get("multi") and not b.get("six")]
    six = [b for b in items if b.get("six")]
    body = (f'<article><p>מלחמת ששת הימים (5–10 ביוני 1967), כל המלחמה על מפה אחת: ציר זמן אחד שבו השמש צובעת את פס ההתקדמות, אנימציה של מהלך הימים והנתונים שמסרו הערכים בוויקיפדיה על הרוגים ופצועים. '
            f'לפני המלחמה: יום הקרבות של 7 באפריל 1967.</p><p class="cas-note">{OVERVIEW_NOTE}</p>'
            + (f'<h2>לפני המלחמה</h2>' + "".join(day(b) for b in pre) if pre else "")
            + ('<h2>ששת הימים: כל המלחמה</h2>' + "".join(
                f'<section class="war-day" id="d-six-days"><h3><a href="{esc(b["slug"])}/">{esc(b["h1"])}</a></h3><p>{esc(b["description"])}</p>'
                f'<div class="war-links"><a href="{esc(b["slug"])}/">המפה והאנימציה במסך מלא</a></div></section>' for b in six) if six else "")
            + (f'<h2 id="war-totals">נתונים לכל המלחמה</h2>' + war_totals_html(cas) if cas else "") + '</article>')
    jsonld = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": f"מלחמות ואירועים צבאיים ב-{y}", "url": url,
              "hasPart": [{"@type": "Article", "name": b["h1"], "url": f'{url}{b["slug"]}/'} for b in items]},
              ld_breadcrumb([("GoInfo", site + "/"), (HUB_NAME, site + "/war/"), (str(y), url)])]}
    return page(f"אירועים צבאיים ב-{y}", f"מלחמת ששת הימים כולה על מפה אחת, ויום הקרבות של 7 באפריל: מפה, ציר זמן והנתונים שמסרו הערכים על הרוגים ופצועים.", url, f"אירועים צבאיים ב-{y}",
                [("GoInfo", "/"), (HUB_NAME, "../"), (str(y), None)], body, jsonld)

def hub_page(years, site):
    url = f"{site}/war/"
    cards = "".join(f'<li><a href="{y}/"><strong>{y}</strong><br>{len(items)} {"עמוד" if len(items) == 1 else "עמודים"}: ' + ", ".join(esc(b["h1"]) for b in items) + "</a></li>" for y, items in sorted(years.items()))
    body = f"<article><p>קרבות ואירועים צבאיים לפי שנה, עם ציר זמן, מפה ואנימציה סכמטית. כל עמוד מבוסס על מקור ציבורי ומסמן במפורש מה מדויק ומה סכמטי.</p><ul class=\"war-cards\">{cards}</ul></article>"
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": HUB_NAME, "url": url}
    return page(HUB_NAME, "קרבות ואירועים צבאיים לפי שנה: ציר זמן, מפה ואנימציה סכמטית, עם מקורות ורישיון.", url, HUB_NAME, [("GoInfo", "/"), (HUB_NAME, None)], body, jsonld)

def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

# the owner 10-22 ("deploy six-days, remove the old pages, keep the single April day"): the six per-day June 1967 pages are RETIRED - no longer built or published
# (their data files and generators stay in git); tools/war_whole_build.py builds the whole war as ONE page in their place. The Worker 301s the old URLs.
RETIRED_DAYS = {"1967-06-05", "1967-06-06", "1967-06-07", "1967-06-08", "1967-06-09", "1967-06-10"}
SIX_DAYS_URL = "six-days/map/"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--images"); ap.add_argument("--site", default="https://goinfo.co.il")
    a = ap.parse_args()
    stage = Path(a.stage) / "war"
    data = ROOT / "war" / "data"
    template = (ROOT / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
    cas = json.loads((data / "1967-casualties.json").read_text(encoding="utf-8")) if (data / "1967-casualties.json").is_file() else None
    years = {}
    allb = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(data.glob("????-??-??.json"))]
    for i, b in enumerate(allb):
        d_ = b["date"].split("-"); b["short_day"] = f"{int(d_[2])} ב{MONTH.get(int(d_[1]), d_[1])}"
        series = [x for x in allb if x.get("multi")] if b.get("multi") else []
        j = series.index(b) if b in series else -1
        b["_nav"] = (series[j - 1] if j > 0 else None, series[j + 1] if 0 <= j < len(series) - 1 else None)
    for f in sorted(data.glob("????-??-??.json")):
        if f.stem[0:10] in RETIRED_DAYS:
            continue
        b = next(x for x in allb if x["date"] == f.stem[0:10])
        years.setdefault(b["year"], []).append(b)
        out = stage / str(b["year"]) / b["slug"]
        imgs = Path(a.images) / f.stem if a.images else None
        url = f'{a.site}/war/{b["year"]}/{b["slug"]}/'
        if b.get("multi"):
            ev = json.loads((data / f"{f.stem}-events.json").read_text(encoding="utf-8"))
            add_place_sides(ev, _il_taken(data, f.stem)); _icons_on(ev, f.stem)
            ids = ["all"] + [t["id"] for t in b["areas"]]
            have = bool(imgs and (imgs / "og.jpg").is_file() and all((imgs / f"still-{i}.jpg").is_file() for i in ids))
            if have:
                out.mkdir(parents=True, exist_ok=True)
                shutil.copy(imgs / "og.jpg", out / "og.jpg")
                for i in ids:
                    shutil.copy(imgs / f"still-{i}.jpg", out / f"still-{i}.jpg")
            write(out / "index.html", multi_battle_page(b, ev, a.site, have, cas))
            if cas:
                ev["casualties"] = casualties_anim(cas, b.get("cas_key", "jun"), ev["places"])
            write(out / "events.json", json.dumps(ev, ensure_ascii=False, indent=1))
            shutil.copy(Path(__file__).resolve().parent.parent / "war" / "daynight.js", out / "daynight.js")
            shutil.copy(Path(__file__).resolve().parent.parent / "war" / "land-mask.json", out / "land-mask.json")      # Natural Earth 10 m land (public domain), keeps unit icons off the sea      # the held day/night mockup script (loaded only with ?daynight=1)
            write(out / "map" / "index.html", map_page(template, b, url, "../events.json", "anim" if ev.get("scene") else "static", credit_html(b, ev, cas, b.get("cas_key", "jun"))))
            print(f"battle {b['year']}/{b['slug']}: {len(b['areas'])} areas, {len(b['timeline'])} timeline entries, images={'yes' if have else 'NO (run tools/war_image.py)'}")
            continue
        ev = json.loads((data / (f.stem + "-events.json")).read_text(encoding="utf-8"))
        add_place_sides(ev, _il_taken(data, f.stem)); _icons_on(ev, f.stem)
        have = bool(imgs and (imgs / "og.jpg").is_file() and (imgs / "still.jpg").is_file())
        if have:
            out.mkdir(parents=True, exist_ok=True)
            for n in ("og.jpg", "still.jpg"):
                shutil.copy(imgs / n, out / n)
        write(out / "index.html", battle_page(b, ev, a.site, have, cas))
        if cas:
            ev["casualties"] = casualties_anim(cas, "apr", ev["places"])
        write(out / "events.json", json.dumps(ev, ensure_ascii=False, indent=1))
        write(out / "map" / "index.html", map_page(template, b, url, "../events.json", "anim", credit_html(b, ev)))
        print(f"battle {b['year']}/{b['slug']}: {len(b['timeline'])} timeline entries, images={'yes' if have else 'NO (run tools/war_image.py)'}")
    import war_whole_build
    war_whole_build.build(a.stage)
    years.setdefault(1967, []).append({"h1": "ששת הימים: כל המלחמה", "slug": SIX_DAYS_URL.rstrip("/"), "six": True, "year": 1967,
                                       "description": "כל מלחמת ששת הימים, 5-10 ביוני 1967, על ציר זמן אחד: מפה ואנימציה סכמטית."})
    for y, items in years.items():
        write(stage / str(y) / "index.html", overview_page(y, items, a.site, cas) if y == 1967 else year_page(y, items, a.site))
    write(stage / "index.html", hub_page(years, a.site))
    (stage / "sound").mkdir(parents=True, exist_ok=True)      # movement-sound loops (CC0, war/sound/SOURCES.md): fetched by war/daynight.js only after sound is turned on
    for f in ("tank.mp3", "jet.mp3", "march.mp3"):
        shutil.copy(Path(__file__).resolve().parent.parent / "war" / "sound" / f, stage / "sound" / f)
    # Rule 13 (the owner 10-25): every war page is measured, whichever generator wrote it - the hub, the overview, the year pages and the text pages come from page(), not from the map template.
    import ga_inject
    n = 0
    for p in stage.rglob("*.html"):
        t = p.read_text(encoding="utf-8")
        t2 = ga_inject.host_fallback(ga_inject.ensure(t))
        if t2 != t:
            p.write_text(t2, encoding="utf-8"); n += 1
    print(f"measurement block added to {n} war page(s); every page now carries gtag + ga-guard + host-fallback + eventlog")
    print(f"wrote hub + {len(years)} year page(s) into {stage}")

if __name__ == "__main__":
    main()
