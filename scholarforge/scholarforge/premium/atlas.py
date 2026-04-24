"""Premium seam — citation / co-citation atlas.

Builds a directed graph of harvested records keyed by DOI / OpenAlex id,
with edges drawn from each record's reference list. The free stub exposes
the public surface so integrators can write code against it today; the
paid build replaces `_build_graph` with the real harvester.

Public surface is intentionally small: one dataclass (`AtlasResult`), one
factory (`build`). Anything exported here is part of the premium contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import require


@dataclass
class AtlasResult:
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
    source_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "generated_at": self.generated_at,
            "source_count": self.source_count,
        }


def build(
    records: Iterable[Dict[str, Any]],
    *,
    include_external: bool = False,
    min_degree: int = 1,
    output: Optional[Path] = None,
) -> AtlasResult:
    """Build a citation atlas from harvested records.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("atlas")
    return _build_graph(records, include_external=include_external,
                        min_degree=min_degree, output=output)


def _build_graph(records, **_) -> AtlasResult:  # pragma: no cover
    raise NotImplementedError("atlas graph builder is shipped in the paid build")


__all__ = ["AtlasResult", "build"]
