"""R49/R50 helper (the owner 10-26: "נבלם = a battle in which the force is hit until it cannot move, i.e. destroyed"; "בולמת = the defender holds the attacker in place, BOTH sides take heavy losses"; "מאמץ עליון / בכל הכוח / במחיר כבד = very heavy casualties").
apply(ev, specs) for specs {card, fam: 'stopped'|'hold', side: the attacking/stopped side ('il'|'ar'), at: [lat,lon] (None -> the card's first place), lvl: 1|2, wrecks: 3, label, dlabel}:
  stopped: every attacker arrow/fill-walk standing within R of the place when the card's act runs ends right there (item "u" = stop time + 3: it does not move on) and its burning wreck marker (item 'loss', kind tank, no number)
           stays where it stood; extra wrecks are placed round the place so at least `wrecks` markers show; the other side fires at the place meanwhile (shell arcs + impact bursts for 8 scene-seconds).
  supreme: only the very-heavy (lvl 2) loss marker(s), no unit removed (the fight is drawn by the card's own items).
  hold:    the same for the attacker (stops dead + wrecks) AND wrecks on the defender's side (thinned units), fire both ways. lvl 2 (supreme effort / "at a heavy price") draws double wrecks and a heavier sound.
Bookkeeping for the test (tools/test_war_stopped.py): ev["stopped"][card] = {fam, side, at, lvl}."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_war_event_shown as es, test_war_heavy_losses as hl, war_landcheck as lc, war_pushout as po
R = 0.30
def pos_at(it, T):
    if it["type"] == "arrow":
        return lc.along(it["path"], lc.ease((T - it["t0"]) / max(1e-6, it["t1"] - it["t0"])))
    for lg in it.get("legs", []):
        if lg["t0"] <= T <= lg["t1"]: return lc.along(lg["path"], lc.ease((T - lg["t0"]) / max(1e-6, lg["t1"] - lg["t0"])))
    last = it["legs"][-1]["path"][-1] if it.get("legs") else None
    return last
def _loss(at, t, side, lvl, label, area="golan"):
    return {"type": "loss", "at": [round(at[0], 4), round(at[1], 4)], "t": round(t, 2), "side": "iaf" if side == "il" else "ar", "kind": "tank", **({"lvl": 2} if lvl == 2 else {}), "label": label, "area": area}
def _units(items, side, place, T):
    out = []
    for i, it in enumerate(items):
        if it["type"] not in ("arrow", "walk") or hl.side(it) != side: continue
        lab = it.get("label") or ""
        if lab.startswith("מסוק") or "טיל" in lab or lab.startswith("נסיגה"): continue
        a, b = es.span(it)
        if b > 5000 and not it.get("fill"): continue          # a permanent formation symbol (division / brigade) stays: only the markers show what was lost
        if not (a - 2 <= T <= b + 8): continue
        p = pos_at(it, min(T, b))
        if p and math.hypot(p[0] - place[0], p[1] - place[1]) <= R: out.append((i, p))
    return out
def apply(ev, specs, area="golan"):
    sc = ev["scene"]; items = sc["items"]; cards = {c["id"]: c for c in ev["events"]}; n = 0
    for sp in specs:
        c = cards.get(sp["card"]); a = po.act_of(sc, c)
        if not a: continue
        pl = sp.get("at") or next(((ev["places"][g["place"]]["lat"], ev["places"][g["place"]]["lon"]) for g in c.get("geometry", []) if g.get("place") in ev["places"]), None)
        if not pl: continue
        AR = sp.get("area", area); T = a["s"] + sp.get("after", 8.0); side = sp["side"]; other = "il" if side == "ar" else "ar"; lvl = sp.get("lvl", 1)
        lab = sp.get("label") or ("כוח נבלם ומושמד: הטנקים נעצרו ובערו (סכמטי, מיקום משוער)" if sp["fam"] == "stopped" else "כוח תוקף נבלם: אבדות כבדות (סכמטי, מיקום משוער)")
        got = _units(items, side, pl, T) if sp["fam"] != "supreme" else []
        for k, (i, p) in enumerate(got):
            items[i]["u"] = round(min(items[i].get("u", 1e9), T + 3), 2)
            if k < 4: items.append(_loss(p, T + 1.0 + 0.4 * k, side, lvl, lab, AR))
        # forces the card needs but the data lacks near the place: a schematic attacking arrow / holding defender, so the fight is a fight (R35)
        if sp["fam"] == "supreme":      # a card that only says the price was very heavy (k9): the fight is drawn already; add the very-heavy loss marker(s) of the side that paid
            for k in range(sp.get("wrecks", 1)):
                ang = 1.3 + 2.1 * k; items.append(_loss([pl[0] + 0.03 * math.cos(ang), pl[1] + 0.04 * math.sin(ang)], T + 1.0 + 0.4 * k, side, 2, lab, AR))
            ev.setdefault("stopped", {})[sp["card"]] = {"fam": "supreme", "side": side, "at": [round(pl[0], 4), round(pl[1], 4)], "lvl": 2, "T": round(T, 2)}; n += 1
            continue
        if not got and sp["fam"] in ("hold", "stopped"):
            src = [pl[0] + (0.12 if side == "ar" else -0.12), pl[1] + (0.22 if side == "ar" else -0.22)]
            items.append({"type": "arrow", "path": [src, [round(x, 4) for x in pl]], "t0": round(T - 9, 2), "t1": round(T - 1, 2), "label": ("התקפה סורית (סכמטי)" if side == "ar" else "התקפה ישראלית (סכמטי)"), "color": "#b3261e" if side == "ar" else "#1d5ea8", "side": side, "area": AR, "hold": 2400, "trail": "tank", "u": round(T + 3, 2)})
        if sp["fam"] == "hold" and not _units(items, other, pl, T):
            items.append({"type": "walk", "label": "כוח מגן (סכמטי)", "cls": "iaf" if other == "il" else "syr", "sym": "▣", "area": AR, "trail": "tank", "lead": 0, "hold": 1, "u": round(T + 40, 2),
                          "legs": [{"t0": round(T - 9, 2), "t1": round(T - 8.5, 2), "path": [[round(pl[0] + (0.05 if other == "il" else -0.05), 4), round(pl[1] - 0.06, 4)]] * 2}]})
        if sp.get("air"):      # Skyhawk-type strike runs: from the base to the place and back, bombs on the column (a source-named air strike)
            for k in range(sp.get("air")):
                t0 = T - 6 + 2.2 * k; o = (k - 1) * 0.02
                items.append({"type": "fly", "side": "iaf", "label": f"{sp.get('air_label', 'סקייהוק ישראלי')} {k + 1} (סכמטי)", "area": AR, "off": None, "legs": [
                    {"t0": round(t0, 2), "t1": round(t0 + 4.0, 2), "path": [sp.get("air_from", [32.66, 35.18]), [round(pl[0] + o, 4), round(pl[1] - 0.01, 4)]]}, {"t0": round(t0 + 4.6, 2), "t1": round(t0 + 8.6, 2), "path": [[round(pl[0] + o, 4), round(pl[1] - 0.01, 4)], sp.get("air_from", [32.66, 35.18])]}]})
                items.append({"type": "boom", "at": [round(pl[0] + o * 2, 4), round(pl[1] + 0.01 * k, 4)], "t": round(t0 + 4.0, 2), "area": AR, "big": 1})
        have = min(len(got), 4)
        for k in range(have, sp.get("wrecks", 3)):
            ang = 2.4 * k + 0.7; items.append(_loss([pl[0] + 0.045 * math.cos(ang), pl[1] + 0.06 * math.sin(ang)], T + 1.0 + 0.4 * k, side, lvl, lab, AR))
        if sp["fam"] == "hold":
            for k in range(sp.get("dwrecks", 2)):
                ang = 3.9 + 2.2 * k; items.append(_loss([pl[0] + 0.06 * math.cos(ang), pl[1] + 0.045 * math.sin(ang)], T + 1.6 + 0.4 * k, other, lvl, sp.get("dlabel") or "כוח מגן ספג אבדות כבדות (סכמטי, מיקום משוער)", AR))
        # fire both ways (hold) or by the other side (stopped): arcs ending on the place, with impact bursts
        for sd in ((side, other) if sp["fam"] == "hold" else (other,)):
            src = [pl[0] + (0.07 if sd == "il" else -0.07), pl[1] + (-0.1 if sd == "il" else 0.1)]
            dst = [pl[0] + (-0.01 if sd == "il" else 0.01), pl[1]]
            items.append({"type": "shell", "from": src, "to": dst, "t0": round(T - 3, 2), "t1": round(T + 5, 2), "period": 1.2, "lift": .03, "area": AR, "side": "iaf" if sd == "il" else "ar"})
            items.append({"type": "boom", "at": [round(dst[0], 4), round(dst[1], 4)], "t": round(T - 1, 2), "area": AR, "big": 1})
        ev.setdefault("stopped", {})[sp["card"]] = {"fam": sp["fam"], "side": side, "at": [round(pl[0], 4), round(pl[1], 4)], "lvl": lvl, "T": round(T, 2)}; n += 1
    return n
