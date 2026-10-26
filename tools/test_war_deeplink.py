#!/usr/bin/env python3
"""Static check of the war deep-link code in the shared template (the owner 2026-10-25): the hash carries t (battle minute) / z / c / a, an invalid part never throws, a hash without "=" stays the old #<area> form,
the hash is written with replaceState only, and the copy button + share_link event exist. Behaviour: tools/war_deeplink_rig.py (browser)."""
from pathlib import Path
s = (Path(__file__).resolve().parent.parent / "war" / "templates" / "battle-map.html").read_text(encoding="utf-8")
for need in ("function dlParse()", "function dlApply(o)", "function wireDeepLink()", "history.replaceState(null,'','#'+dlHash())", "evw('share_link'", "העתק קישור לנקודה זו",
             "indexOf('=')<0?(location.hash||'').slice(1):''", "isFinite(+c[0])", "wireDeepLink();"):
    assert need in s, need
assert "history.pushState" not in s.split("function dlParse()")[1].split("function wireAnim")[0], "deep links must not add history entries"
print("ok: war deep links")
