"""Scholarly TUI theme — restrained palette, thin glyphs, predictable semantics.

Stage 5 replaces the hacker-demo palette (bright cyan + magenta + blue,
heavy ASCII block art) with a calm scholarly look inspired by paper / ink /
amber highlight. Colors are addressed by *role* (text, muted, accent, rule,
success, warn, error) rather than raw names, so future palettes can swap in
without touching call sites.
"""

from __future__ import annotations

import os
import sys


def supports_color() -> bool:
    """Return True if stdout appears to accept ANSI escapes."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOR = supports_color()


def _code(seq: str) -> str:
    return seq if _COLOR else ""


RESET  = _code("\033[0m")
BOLD   = _code("\033[1m")
DIM    = _code("\033[2m")
ITALIC = _code("\033[3m")

# Roles — use these, not raw colors.
TEXT    = _code("\033[37m")     # default foreground (soft white)
MUTED   = _code("\033[2m\033[37m")
RULE    = _code("\033[2m")      # dim, for thin lines and separators
ACCENT  = _code("\033[34m")     # ink-blue, the one bold hue
HILITE  = _code("\033[33m")     # amber — used sparingly for attention
SUCCESS = _code("\033[32m")
WARN    = _code("\033[33m")
ERROR   = _code("\033[31m")


def paint(text: str, *codes: str) -> str:
    if not codes or not _COLOR:
        return text
    return "".join(codes) + text + RESET


# Glyphs — thin unicode, not heavy blocks.
GLYPHS = {
    "rule_h":   "─",
    "rule_v":   "│",
    "bullet":   "·",
    "arrow":    "›",
    "section":  "§",
    "check":    "✓",
    "cross":    "✗",
    "dot":      "•",
    "ellipsis": "…",
}


__all__ = [
    "supports_color", "paint",
    "RESET", "BOLD", "DIM", "ITALIC",
    "TEXT", "MUTED", "RULE", "ACCENT", "HILITE",
    "SUCCESS", "WARN", "ERROR",
    "GLYPHS",
]
