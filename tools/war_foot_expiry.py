"""R44 helper (the owner 10-26: "foot forces disappear when there is no update on them"): a foot unit (infantry symbol: foot-trail walk/arrow or an infantry label) is removed from the map HOURS (default 6 simulated hours) after
its LAST UPDATE. An update = its own move ends, a shell/burst/loss/flag within 0.15 deg of where it stands, a card whose place is within 0.3 deg (the card's act). Gaps longer than the timeout end the unit's life even if a
later event happens near it (that event shows its own symbols). Aircraft wrecks (3 h) and ground loss markers (chapter end) keep their own rules. apply(ev) sets item["u"]; stats(ev) returns counts for the report."""
import math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import war_landcheck as lc
INF = re.compile(r'חיילים|חי"ר|חי״ר|צנחנים|קומנדו|לוחמים|פלוגת|כוח רגלי|גל חי')
MISSILE = lc.MISSILE
HOURS = 6
def is_foot(it):
    if it["type"] not in ("walk", "arrow"): return False
    lab = it.get("label") or ""
    if it["type"] == "arrow" and MISSILE.search(lab) and not INF.search(lab): return False
    if lab.startswith("מסוק") or lab.startswith("אח") or "ספינ" in lab: return False
    return it.get("trail") == "foot" or bool(INF.search(lab))
def end_of(it): return it["legs"][-1]["t1"] if it["type"] == "walk" else it["t1"]
def pos_of(it): return (it["legs"][-1]["path"][-1] if it["type"] == "walk" else it["path"][-1])
def maps(ev):
    pts = sorted((a["s"], a["min"]) for a in ev["scene"]["acts"] if a.get("min") is not None)
    def minute_at(T):
        if T <= pts[0][0]: return pts[0][1]
        for (s0, m0), (s1, m1) in zip(pts, pts[1:]):
            if s0 <= T <= s1: return m0 + (m1 - m0) * ((T - s0) / (s1 - s0) if s1 > s0 else 0)
        return pts[-1][1]
    def t_at(m):
        if m <= pts[0][1]: return pts[0][0]
        for (s0, m0), (s1, m1) in zip(pts, pts[1:]):
            if m0 <= m <= m1: return s0 + (s1 - s0) * ((m - m0) / (m1 - m0) if m1 > m0 else 0)
        return pts[-1][0] + (m - pts[-1][1]) * 0.1
    return minute_at, t_at
def start_of(it): return it["legs"][0]["t0"] if it["type"] == "walk" else it["t0"]
def update_times(ev, it):
    p = pos_of(it); out = []; places = ev.get("places", {})
    for x in ev["scene"]["items"]:
        t = None
        if x["type"] in ("boom", "loss", "surrender"): t, q = x["t"], x.get("at")
        elif x["type"] == "shell": t, q = x["t0"], x["to"]
        elif x["type"] == "mark": t, q = x["t0"], x.get("at")
        if t is not None and q and math.hypot(q[0] - p[0], q[1] - p[1]) <= 0.15: out.append(t)
    acts = [a for a in ev["scene"]["acts"] if a.get("min") is not None]
    for c in ev["events"]:
        g = [places[g_["place"]] for g_ in c.get("geometry", []) if g_.get("place") in places]
        if any(math.hypot(q["lat"] - p[0], q["lon"] - p[1]) <= 0.3 for q in g):
            a = min(acts, key=lambda x: abs(x["min"] - c["start_min"]), default=None)
            if a and abs(a["min"] - c["start_min"]) <= 90: out.append(a["s"] + 14)     # the card's act is an update for the whole act (a unit named by a card is mentioned while it is on screen)
    return sorted(out)
def expiry(ev, it, minute_at, t_at, hours=HOURS):
    t_end = end_of(it); m = minute_at(t_end); life = hours * 60
    last = m
    for ut in update_times(ev, it):
        if ut < start_of(it): continue
        mu = minute_at(ut)
        if mu - last > life: break
        last = max(last, mu)
    return t_at(last + life), last
def apply(ev, hours=HOURS):
    minute_at, t_at = maps(ev); n = 0
    for it in ev["scene"]["items"]:
        if not is_foot(it): continue
        u, last = expiry(ev, it, minute_at, t_at, hours)
        u = max(round(u, 2), round(end_of(it) + 1.0, 2))
        if it.get("u") is None or u < it["u"]: it["u"] = u
        it["foot_expiry"] = 1; n += 1
    ev["foot_expiry"] = n
    return n
def alive_counts(ev, fracs=(0.25, 0.5, 0.9)):
    dur = ev["scene"]["dur"]; foot = [it for it in ev["scene"]["items"] if is_foot(it)]
    res = []
    for f in fracs:
        T = dur * f
        res.append(sum(1 for it in foot if (it["legs"][0]["t0"] if it["type"] == "walk" else it["t0"]) - 6 <= T and (it.get("u") is None or T <= it["u"])))
    return len(foot), res
