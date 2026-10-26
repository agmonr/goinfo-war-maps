#!/usr/bin/env python3
"""R47 (the owner 10-26): every card title links to its passage in the source (all wars). Checks the data: each card has `source_url`, https, host allow-list (Wikipedia he/en/ar, idf.il), never a .ru/.cn host, a pinned revision
(oldid) or a PDF page, and the scene log entry of the card carries the same href; the template renders the link (rel noopener, new tab). Cards without a link are LISTED as gaps (YK strict: 0 gaps; the others reported).
   python3 tools/test_war_source_links.py [events.json ...]"""
import glob, json, os, re, sys, urllib.parse
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ALLOW = ("he.wikipedia.org", "en.wikipedia.org", "ar.wikipedia.org", "www.idf.il", "idf.il", "palmach.org.il", "www.palmach.org.il")
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
t = open('war/templates/battle-map.html', encoding='utf-8').read(); fail = 0
if "class=\"tml\" href=\"'+esc(e.source_url)" not in t or "class=\"tml\" href=\"'+esc(L2[i].href)" not in t or 'rel="noopener"' not in t: print('FAIL template does not render the source link'); fail += 1
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8')); ev = d['events']; bad = []; gaps = []
    if f not in explicit and not (d.get('whole') or '1967-04-07' in f): continue     # the retired per-day Six-Day files are not published; the whole page's links are checked from its built events.json
    for c in ev:
        u = c.get('source_url')
        if not u: gaps.append(c['id']); continue
        h = urllib.parse.urlparse(u)
        if h.scheme != 'https' or h.netloc not in ALLOW or re.search(r'\.(ru|cn)$', h.netloc) or not ('oldid=' in u or '.pdf' in u or 'itemId=' in u or c.get('source_cur')): bad.append(c['id'])
    logs = (d.get('scene') or {}).get('log', [])
    nolog = [c['id'] for c in ev if c.get('source_url') and logs and not any((l.get('q') == c['quote'] or l.get('n') == c['title']) and l.get('href') == c['source_url'] for l in logs)]
    cur = sum(1 for c in ev if c.get('source_cur'))
    print(f"{f}: {len(ev) - len(gaps)}/{len(ev)} cards link to the source ({cur} of them to the CURRENT article text, re-pinned by supporting sentence)", ('gaps: ' + ', '.join(gaps[:12]) + (' ...' if len(gaps) > 12 else '')) if gaps else 'ok', ('BAD ' + ', '.join(bad)) if bad else '', ('LOG-MISSING ' + ', '.join(nolog[:5])) if nolog else '')
    if f in explicit: fail += len(gaps) + len(bad) + len(nolog)
sys.exit(1 if fail else 0)
