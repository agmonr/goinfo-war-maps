"""R43 helper (the owner 10-26): a report of a surrender shows a WHITE FLAG waving above the place for two simulated hours. fill(ev) adds a 'surrender' item (a) at every stronghold/position mark whose label says it surrendered
("נכנע"), at its own place and time, with the mark's quote; (b) for every card whose title/quote reports a surrender (כניעה / נכנע / נכנעו / הסגיר) and has a place but no flag in its window: at its place (the first geometry place),
at the card's act. A card with no place and no mark gets no flag (nothing to put it above; test_war_surrender lists it). Surrender words only - 'prisoners' / 'captured' are not surrenders."""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es
SURR = re.compile(r'(?<![א-ת])(?:כניעה|כניעת|הכניעה|נכנע(?:ה|ו|ים)?|הסגיר(?:ו)?|נוהל הכניעה)(?![א-ת])')
R = 0.45
def fill(ev):
    sc, places, n = ev["scene"], ev.get("places", {}), 0
    items = sc["items"]
    for it in list(items):
        if it["type"] == "mark" and it.get("at") and "נכנע" in (it.get("label") or ""):
            items.append({"type": "surrender", "at": it["at"], "t": it["t0"], "label": (it["label"].split(":")[0] + ": כניעה"), "q": it.get("q", ""), "s": it.get("s", ""), "area": it.get("area") or "all", "from_mark": 1}); n += 1
    acts = [x for x in sc["acts"] if x.get("min") is not None]
    for c in ev["events"]:
        if not SURR.search(c["title"] + " " + c["quote"]): continue
        near = min(acts, key=lambda x: abs(x["min"] - c["start_min"]), default=None)
        if not near or abs(near["min"] - c["start_min"]) > 90: continue
        w0, w1 = near["s"] - 2, near["s"] + 14
        pl = [(places[g["place"]]["lat"], places[g["place"]]["lon"], g["place"]) for g in c.get("geometry", []) if g.get("place") in places]
        have = [x for x in items if x["type"] == "surrender" and w0 <= x["t"] <= w1]
        if have and not pl: continue
        for la, lo, pid in pl:
            if any(math.hypot(x["at"][0] - la, x["at"][1] - lo) <= R for x in have): continue
            src = c.get("src") or {}
            items.append({"type": "surrender", "at": [round(la, 5), round(lo, 5)], "t": round(near["s"] + 0.3, 2), "label": f"{places[pid]['name']}: כניעה", "q": c["quote"][:200], "s": src.get("s") or "", "area": c.get("area") or "all",
                          "approx": places[pid].get("precision") != "exact", "card": c["id"]}); n += 1
    ev["surrender_flags"] = n
    return n
