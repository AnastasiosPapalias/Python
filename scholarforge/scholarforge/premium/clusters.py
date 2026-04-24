"""Premium seam — topic clustering.

Groups harvested records into topical clusters using TF-IDF over titles +
abstracts with a lightweight hierarchical merge. The free stub exposes the
public surface; the paid build ships the clustering implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from . import require


@dataclass
class Cluster:
    id: str
    label: str
    keywords: List[str] = field(default_factory=list)
    member_ids: List[str] = field(default_factory=list)
    size: int = 0


@dataclass
class ClusterResult:
    clusters: List[Cluster] = field(default_factory=list)
    unassigned: List[str] = field(default_factory=list)


def cluster(
    records: Iterable[Dict[str, Any]],
    *,
    target_clusters: int = 8,
    min_cluster_size: int = 3,
    language: Optional[str] = None,
) -> ClusterResult:
    """Cluster harvested records into topical groups.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("clusters")
    return _run_clusterer(records, target_clusters=target_clusters,
                          min_cluster_size=min_cluster_size, language=language)


def _run_clusterer(records, **_) -> ClusterResult:  # pragma: no cover
    raise NotImplementedError("clusterer is shipped in the paid build")


__all__ = ["Cluster", "ClusterResult", "cluster"]
