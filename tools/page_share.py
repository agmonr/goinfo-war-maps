"""The share control the generated pages carry, written once.

Four generators build the ~930 pages under /hafkaot/, /city/, /city-news/ and
/nadlan/, and each of them owns exactly one page shell. This module is the
markup those four shells share, so the control is defined in one file rather
than copied into four - and so a change to its wording, its glyph or its
placement is one edit rather than four that drift.

The behaviour lives in src/share.js and the appearance in src/style.css, both
also one file for the whole site. A shell therefore needs two things: {share_top} where the
control belongs under the masthead and {share_bottom} where it belongs above
the footer. The <script> tag rides along inside the top block rather than
asking each shell for a third placeholder in its <head>: it is deferred and
src/share.js binds one delegated listener, so where in the document it sits
makes no difference to when it works, and one insertion point per position is
one fewer thing for four shells to get wrong.

The block is deliberately static markup with no per-page values in it. The
page's address is read at click time from its own <link rel="canonical">,
which every one of these generators already writes, so nothing here has to be
told which page it is standing on.
"""

# defer, so the parser is never blocked for a control that cannot be used
# before the page exists. src/share.js binds one delegated listener, so it
# does not care whether it runs before or after the buttons are parsed.
SCRIPT = '<script src="/src/share.js" defer></script>'

# Public: tools/mast_inject.py puts the same chain in the masthead, so the
# gesture is one glyph site-wide rather than two that drift.
# The same chain glyph the desktop window's share button uses (src/desktop.js
# CHROME), so the same gesture looks the same wherever the reader meets it.
GLYPH = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.8 1.7"/>'
    ' <path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.8-1.7"/></svg>'
)

_LABEL = "שיתוף הדף"
_TITLE = "העתקת הקישור לדף הזה"


def bar(pos):
    """The control, for pos "top" (under the masthead) or "bottom" (above the
    footer). data-pos is what src/style.css uses to space the two differently;
    both carry the same class, because src/share.js treats them identically."""
    if pos not in ("top", "bottom"):
        raise ValueError(f"share bar position must be top or bottom, not {pos!r}")
    return (
        '<div class="gi-share-bar" data-pos="' + pos + '">'
        '<button class="gi-share" type="button" title="' + _TITLE + '"'
        ' aria-label="' + _TITLE + '">'
        + GLYPH + '<span class="gi-share-label">' + _LABEL + '</span>'
        '<span class="gi-share-done" aria-hidden="true">הקישור הועתק</span>'
        '</button></div>'
    )


# The script ships with the top block - see the module note.
TOP = SCRIPT + bar("top")
BOTTOM = bar("bottom")
