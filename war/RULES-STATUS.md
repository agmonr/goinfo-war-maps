# War rules: status per war (2026-10-26)
Generated part: `python3 tools/war_rules_matrix.py YK=... Kadesh=... Independence=... Civil1947=... SixDay=<stage events.json>` (0 = pass; the Six-Day row is the data of the LIVE page as built from the twin stage; nothing was changed on live).

| war | cards | items | R24 sound cues (>0) | R22 play s/war day (>=150; >20-day wars >=100) | R12 on water | R11 cards not shown | R15 unlabelled movers |
|---|---|---|---|---|---|---|---|
| YK | 76 | 496 | 289 | 156 | 0 | 0 | 0 |
| Kadesh | 25 | 54 | 26 | 187 | 0 | 1 | 0 |
| Independence | 30 | 84 | 36 | 108 | 0 | 0 | 0 |
| Civil1947 | 21 | 50 | 80 | 110 | 0 | 0 | 0 |
| SixDay | 113 | 444 | 245 | 225 | 1 | 5 | 12 |

April 1967 (7 April, single-day page, live) is not a scene of the same kind: no act minutes, no `scene.items` in its data file; R11/R12/R15/R22 do not apply; R24 sound = its own track; its shot-down MiGs (6, tally in the HUD) are drawn only as a counter (see R13 below).

## Browser rigs and shared-template rules (one engine, so a pass on the twin is a pass for the template; per-war data in the notes)
| Rule | Check | YK | Six-Day (twin, not live) | Kadesh | Independence | Civil 1947 | April (live) |
|---|---|---|---|---|---|---|---|
| R18 facing/no spin | `test_war_heading.py` (static) | pass | pass | pass | pass | pass | n/a (no tanks facing rule data) |
| R27 play-through, no stall | `war_playthrough_rig.py` | pass 8x, 0 stalls | pass 8x, 0 stalls | not run | not run | not run | not run |
| R25 auto-return | `war_autoreturn_rig.py` | pass | pass | shared template, not run | shared template, not run | shared template, not run | live: not in the template yet |
| R16 rotor | `war_rotor_rig.py` | pass | no helicopters | no helicopters | no helicopters | no helicopters | no helicopters |
| R13 shot-down fall | `war_shotdown_rig.py` | pass 9/9 (7 MiG Ofira, 2 Phantoms Benha) | 3 candidates, NOT applied (live) | 2 candidates (k5, k10) not applied | none | none | tally only; 6 MiGs candidates e5/e6/e9/e10 not applied (live) |
| R12 land check | `war_landcheck.py` | pass | 1 offender (brigade 35 arrow, day 3): fix on the branch as a separate commit, not live | pass | pass | pass | pass |
| R11 every card shown | `test_war_event_shown.py` + `war_event_audit.py` | 76/76 | 113 cards: 108 (static), browser audit: 67 at place, 15 place-but-nothing-there, 31 no place | 24/25 (k15) | 30/30 | 21/21 | not covered |
| R29 measurement | `test_war_measure.py` | pass | pass | pass | pass | pass | pass |

Fails that need the owner's/the coordinator's word before the live page changes: Six-Day R11 (5 cards truly absent: d3-s1, d3-g0, d4-s5, d5-s1, d6-s0; 10 more with nothing at the place at that time), Six-Day R12 (1 arrow), Six-Day R15 (12 unlabelled movers), Six-Day/April R13 (shot-down not drawn), Kadesh k15.
