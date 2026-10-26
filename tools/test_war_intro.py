#!/usr/bin/env python3
"""R48 (the owner 10-26): every war page opens on a still map with an opening screen: war name, dates, the casualties of BOTH sides from a cited source (link allow-list), "אין נתון בערך" where the source gives none - never invented. Checks the data: D.intro with
title, dates, two sides with >= 1 line each, a https source link on the allow-list; the template carries the overlay (button + tap + key, intro_start event, deep link skip). The browser part is tools/war_intro_rig.py.  YK strict, others listed."""
import glob, json, os, sys, urllib.parse
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ALLOW = ("he.wikipedia.org", "en.wikipedia.org", "ar.wikipedia.org", "www.idf.il", "idf.il")
explicit = [x for x in sys.argv[1:] if not x.startswith('--')] or [x for x in ['war/data/1973-10-06-events.json'] if os.path.exists(x)]
t = open('war/templates/battle-map.html', encoding='utf-8').read(); fail = 0
for need in ("function introInit", "id=\"iGo\"", "evw('intro_start'", "EVERY load, deep links included", "var INTROON=", "if(!INTROON)sndToast(true)", "localStorage.setItem('apr67snd','on')", "toggleAnim(true);introInit();"):
    if need not in t: print('FAIL template misses', need); fail += 1
for f in dict.fromkeys(sorted(glob.glob('war/data/*-events.json')) + explicit):
    d = json.load(open(f, encoding='utf-8')); I = d.get('intro')
    if not I and f not in explicit: continue
    bad = []
    if not I: bad.append('no intro')
    else:
        if not I.get('title') or not I.get('dates'): bad.append('title/dates')
        if len(I.get('sides', [])) < 2 or any(not s.get('lines') for s in I['sides']): bad.append('sides')
        u = urllib.parse.urlparse((I.get('src') or {}).get('u', ''))
        if u.scheme != 'https' or u.netloc not in ALLOW: bad.append('source link')
    print(f"{f}: opening screen " + ('FAIL ' + ', '.join(bad) if bad else 'ok: ' + I['title'] + ' | ' + I['dates']))
    if bad and f in explicit: fail += 1
sys.exit(1 if fail else 0)
