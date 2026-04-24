"""Premium seam — book scaffold export.

Renders a long-form book project from a corpus: front matter, chapter
outlines seeded by clusters, per-chapter source lists, and a consolidated
bibliography. Freemium exposes the contract; the paid build ships the
renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import require


@dataclass
class BookPackResult:
    front_matter_path: Optional[Path] = None
    chapters: List[str] = field(default_factory=list)
    bibliography_path: Optional[Path] = None
    output_dir: Optional[Path] = None


def export(
    records: Iterable[Dict[str, Any]],
    *,
    title: str,
    author: str,
    output_dir: Path,
    target_chapters: int = 10,
    style: str = "chicago",
) -> BookPackResult:
    """Render a book scaffold from harvested records.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("book_pack")
    return _render(records, title=title, author=author,
                   output_dir=output_dir, target_chapters=target_chapters,
                   style=style)


def _render(records, **_) -> BookPackResult:  # pragma: no cover
    raise NotImplementedError("book pack renderer is shipped in the paid build")


__all__ = ["BookPackResult", "export"]
