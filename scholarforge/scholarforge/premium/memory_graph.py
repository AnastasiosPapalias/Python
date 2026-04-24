"""Premium seam — persistent cross-project research graph.

Maintains a long-lived knowledge graph across every ScholarForge project
on the machine: shared authors, recurring subjects, claims seen in
multiple places, papers that keep coming up. Freemium exposes the
contract; the paid build ships the storage + query engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import require


@dataclass
class MemoryQueryResult:
    matches: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    backend: str = ""


def ingest(
    records: Iterable[Dict[str, Any]],
    *,
    project_id: str,
    store_path: Optional[Path] = None,
) -> int:
    """Ingest harvested records into the shared memory graph.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("memory_graph.ingest")
    return _ingest(records, project_id=project_id, store_path=store_path)


def query(
    text: str,
    *,
    limit: int = 25,
    subject: str = "",
    store_path: Optional[Path] = None,
) -> MemoryQueryResult:
    """Query the shared memory graph for prior knowledge on a topic.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("memory_graph.query")
    return _query(text, limit=limit, subject=subject, store_path=store_path)


def _ingest(records, **_) -> int:  # pragma: no cover
    raise NotImplementedError("memory graph ingestion is shipped in the paid build")


def _query(text, **_) -> MemoryQueryResult:  # pragma: no cover
    raise NotImplementedError("memory graph query is shipped in the paid build")


__all__ = ["MemoryQueryResult", "ingest", "query"]
