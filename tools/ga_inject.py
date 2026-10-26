#!/usr/bin/env python3
"""Every published page carries the site's Google tag (the nightly sanity check of 2026-09-20:
"Google Analytics tag not detected" on the whole education family, pedagogy, tmichot, nadlan,
deals, budget, objections - the committed and generated families whose heads never had it).

    tools/ga_inject.py <stage>

Runs in the stage before stamp_assets: a page with a <head> and no gtag loader gets the same
block index.html and city.html carry - the guard first (src/ga-guard.js keeps staging views out),
then the loader, then the config with the manager opt-out. Absolute /src/ paths, so a page at any
depth loads the same file and the stamp gives it the same ?v=. Pages that already carry the tag,
pages marked staging (index_test) and non-HTML files are left alone. Prints the count.
"""
import re
import sys
from pathlib import Path

GA_ID = "G-HMYNE9NT2K"
BLOCK = f"""  <!-- Google tag (gtag.js) -->
  <script src="/src/ga-guard.js"></script>
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>
    try {{ if (localStorage.getItem('yeelaIsManager') === 'true') window['ga-disable-{GA_ID}'] = true; }} catch (e) {{}}
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_ID}');
  </script>
"""
SKIP = re.compile(r"Google tag omitted|index_test\.html", re.I)


def main(stage):
    stage = Path(stage)
    done = skipped = 0
    for p in stage.rglob("*.html"):
        rel = p.relative_to(stage).as_posix()
        if rel.startswith(("reports/", "pro/protocols/pagefind", "pro/tenders/pagefind")) or "index_test" in rel:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            skipped += 1
            continue
        if "googletagmanager.com/gtag" in text or SKIP.search(text) or "</head>" not in text:
            continue
        p.write_text(text.replace("</head>", BLOCK + "</head>", 1), encoding="utf-8")
        done += 1
    print(f"ga_inject: the Google tag added to {done} pages ({skipped} unreadable skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
