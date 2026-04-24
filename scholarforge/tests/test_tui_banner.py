"""Tests for the Stage-5 scholarly banner.

The banner must be:
  * compact (≤ 8 lines including surrounding blanks)
  * free of ANSI escapes when stripped
  * carry wordmark + tagline + version + URL
  * not re-introduce the old hacker-demo ASCII block art
"""

from __future__ import annotations

import re

from scholarforge import __version__
from scholarforge.tui import banner


ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _strip(s: str) -> str:
    return ANSI_RE.sub("", s)


def test_banner_contains_wordmark_and_tagline():
    out = _strip(banner.render(width=80))
    assert banner.WORDMARK in out
    assert banner.TAGLINE in out
    assert banner.URL in out


def test_banner_includes_current_version():
    out = _strip(banner.render(width=80))
    assert __version__ in out


def test_banner_is_compact():
    lines = banner.render(width=80).splitlines()
    # wordmark, tagline, meta, rule + framing blanks — must be well under the
    # 16-line hacker banner we replaced.
    assert len(lines) <= 8, f"banner grew to {len(lines)} lines"


def test_banner_has_no_block_ascii_art():
    out = _strip(banner.render(width=80))
    # The legacy banner used these heavy U+2588 / U+255A drawings.
    forbidden = ["█", "╔", "╗", "╚", "╝", "╠", "╣"]
    for glyph in forbidden:
        assert glyph not in out, f"legacy block art leaked: {glyph!r}"


def test_banner_width_clamps_rule():
    narrow = _strip(banner.render(width=50))
    # The rule line is the one we clamp — it must fit inside the given width.
    rule_line = next(l for l in narrow.splitlines() if "─" in l)
    assert len(rule_line) <= 50


def test_banner_version_override():
    out = _strip(banner.render(version="9.9.9", width=80))
    assert "9.9.9" in out
