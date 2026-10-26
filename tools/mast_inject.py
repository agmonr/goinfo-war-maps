"""Stub of the goinfo.co.il site masthead, so the war pages build stand-alone.

On goinfo.co.il the build runs with the site's real `tools/mast_inject.py` first on the import path (PYTHONPATH=<site>/tools), which renders the full masthead, search and footer
from the site's own registry. Here `block()` returns a minimal header: the site link, the section and the page title."""
import html
def block(section, canonical, prefix="/", share_title=""):
    return ('<header class="mast-stub" dir="rtl"><a href="https://goinfo.co.il/">goinfo.co.il</a> · <span>' + html.escape(section or "") + "</span></header>")
def demote_body_h1(body):
    return body.replace("<h1", "<h2").replace("</h1>", "</h2>")
