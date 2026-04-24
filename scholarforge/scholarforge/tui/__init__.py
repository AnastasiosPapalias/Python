"""scholarforge.tui — scholarly terminal UI primitives.

Public surface is intentionally small during the Stage-5 transition; most
interior widgets still live in `scholarforge._legacy` and will migrate in
later stages. New code should import from here, not from legacy.
"""

from scholarforge.tui import banner, theme

__all__ = ["banner", "theme"]
