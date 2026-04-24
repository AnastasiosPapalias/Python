"""Calm scholarly banner.

Replaces the 16-line ASCII-block "SCHOLAR FORGE" header with a compact
wordmark-and-tagline block, in the spirit of feynman.is / Standard Ebooks:
restrained, typographic, quiet. Five lines, one accent, one thin rule.
"""

from __future__ import annotations

import shutil

from scholarforge import __version__
from scholarforge.tui.theme import (
    ACCENT, BOLD, DIM, ITALIC, MUTED, RESET, RULE, TEXT, paint,
)

WORDMARK = "ScholarForge"
TAGLINE = "the provenance-first scholarly research workspace"
URL = "github.com/AnastasiosPapalias/scholarforge"


def _term_width(default: int = 80) -> int:
    try:
        return max(40, shutil.get_terminal_size((default, 24)).columns)
    except Exception:
        return default


def render(version: str = __version__, width: int | None = None) -> str:
    """Return the banner as a single multi-line string.

    Layout (5 lines):
        <blank>
          ScholarForge
          the provenance-first scholarly research workspace
          v3.4.0-dev · github.com/AnastasiosPapalias/scholarforge
          ──────────────────────────────────────────────
    """
    w = width if width is not None else _term_width()
    indent = "  "
    wordmark = paint(WORDMARK, BOLD, ACCENT)
    tagline = paint(TAGLINE, ITALIC, TEXT)
    meta = paint(f"v{version}  ·  {URL}", DIM)
    rule_len = min(w - 4, max(len(WORDMARK), len(TAGLINE), len(f"v{version}  ·  {URL}")))
    rule = paint("─" * rule_len, RULE)
    return "\n".join([
        "",
        f"{indent}{wordmark}",
        f"{indent}{tagline}",
        f"{indent}{meta}",
        f"{indent}{rule}",
        "",
    ])


def print_banner(version: str = __version__, width: int | None = None) -> None:
    print(render(version=version, width=width))


__all__ = ["render", "print_banner", "WORDMARK", "TAGLINE", "URL"]
