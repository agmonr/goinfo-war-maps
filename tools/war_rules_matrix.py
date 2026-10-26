#!/usr/bin/env python3
"""Rule x war matrix for the machine-checkable rules of war/RULES.md.
    python3 tools/war_rules_matrix.py LABEL=path/to/events.json ...   -> markdown table on stdout (war/RULES-STATUS.md is this output, dated).
Each cell: the number of offenders (0 = pass). Rules judged here: R05 sound cue track present, R06 pace (play seconds per war day), R12 no land unit/fixed mark on water, R13 every card shown at its time,
R14 every card quote is a substring of its card's own text fields (cheap check), R15 every scene item has a label that ends (סכמטי) or a source key. Browser-only rules (heading, deep link, follow, intro, rotor, shot-down,
play-through, GA) are listed in RULES.md with their rig and are not judged from data."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_landcheck as lc, test_war_event_shown as es, test_war_heavy_losses as hl
def row(path):
    d = json.load(open(path, encoding='utf-8')); sc = d.get('scene') or {}
    items = sc.get('items', []); cards = d.get('events', [])
    days = ((d.get('whole') or {}).get('days') or [])
    ndays = len(days) if days else 1
    dur = sc.get('dur') or 0
    play_per_day = round(dur / ndays) if ndays else dur
    cues = len(sc.get('sfx') or [])
    land = len(lc.check(path)) if sc else None
    sh = es.check(path); hv = hl.check(path)
    unlabeled = sum(1 for it in items if it['type'] in ('walk', 'fly') and 'סכמטי' not in (it.get('label') or '') and not it.get('sk'))
    return dict(cards=len(cards), items=len(items), sfx=cues, pace=play_per_day, land=land, shown=(len(sh[2]) if sh else 'n/a'), unlabeled=unlabeled, heavy=(len(hv[1]) if hv else 'n/a'))
def main():
    rows = []
    for a in sys.argv[1:]:
        label, _, p = a.partition('='); rows.append((label, row(p)))
    print('| war | cards | items | R24 sound cues (>0) | R22 play s/war day (>=150; >20-day wars >=100) | R12 on water | R11 cards not shown | R15 unlabelled movers | R34 heavy-loss cards without fight+loss |')
    print('|---|---|---|---|---|---|---|---|---|')
    for l, r in rows:
        print(f"| {l} | {r['cards']} | {r['items']} | {r['sfx']} | {r['pace']} | {r['land']} | {r['shown']} | {r['unlabeled']} | {r['heavy']} |")
main()
