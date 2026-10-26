# goinfo-war-maps

Interactive, sourced maps of Israel's wars - Yom Kippur 1973, Six-Day 1967 (and the 7 April 1967 air battle), Sinai/Kadesh 1956, the War of Independence 1948-49 and the 1947-48 civil phase - built from one shared map-and-animation template.
They run as pages of https://goinfo.co.il/war/ (the site serves the built pages; this repository is the code and the data behind them).

**What is in here**

| path | what |
|---|---|
| `war/templates/battle-map.html` | the one shared template (Leaflet map, animation engine, sound, controls) used by every war page |
| `war/data/*-events.json` | the scene of each war: cards (title, verbatim quote, source link), places, moving units, fire, losses, sound cues |
| `war/RULES.md`, `war/RULES-STATUS.md` | the numbered rule set every war page must satisfy, each with its machine check, and the rule x war table |
| `tools/war_data_*.py` | one generator per war: sourced cards + schematic movements -> `war/data/*.json` |
| `tools/war_build.py`, `war_one_build.py`, `war_whole_build.py` | build the pages into a stage directory |
| `tools/test_war_*.py`, `tools/war_*_rig.py` | static checks and browser rigs (Playwright) for the rules |

**Principles** (see `war/RULES.md`): every card quote is a verbatim passage of a pinned Wikipedia revision (or a cited PDF) and its title links to that passage; positions the source does not give are drawn schematically and labelled "(approximate)"; nothing is invented; both sides of a battle are drawn and fire; absence is never drawn as data.

**Build a page**

```
python3 tools/war_data_1973_yomkippur.py          # needs WAR_SRC_DIR with the cached article texts (see below)
python3 tools/war_one_build.py ./stage yomkippur
python3 -m http.server 8000 --directory stage      # open /war/1973/yomkippur/map/
python3 tools/test_war_heading.py && python3 tools/test_war_event_shown.py && python3 tools/test_war_fire.py   # rule checks
```

The generators assert every quote against a local copy of its source text (`WAR_SRC_DIR`, plain-text extracts of the pinned revisions; fetched with `tools/war_source_links.py`; the IDF PDF text is not redistributed). `WAR_SRC_CACHE` sets the cache of fetched article texts.

**Licences**: the code (`tools/`, `war/templates/`, `war/daynight.js`) is MIT - see `LICENSE`; the data below is CC BY-SA 4.0. **Data and licences**: the text of the cards is quoted/derived from Hebrew, English and Arabic Wikipedia (CC BY-SA 4.0) - see `LICENSE-DATA.md`; maps use OpenStreetMap tiles (c) OpenStreetMap contributors and a Natural Earth land mask (public domain); movement sounds are CC0 loops (`war/sound/SOURCES.md`).

**Measurement**: the pages carry the site's analytics tag only behind a guard that disables it on any host that is not goinfo.co.il, in test browsers and for the site owner; a clone of this repository served from another host does not report anything.
