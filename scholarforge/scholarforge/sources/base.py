"""Source protocol and shared record type.

A `Source` is anything that can take a query and return a list of
`HarvestRecord`s. The protocol is deliberately narrow so new adapters can be
written (or ported from the legacy `search_*` functions) without touching the
harvest runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Protocol, runtime_checkable

# Re-export the canonical record type from the legacy module. Stage 6 will
# migrate this into `scholarforge.provenance.record` with trust fields.
from scholarforge._legacy import HarvestRecord  # noqa: F401

SearchFn = Callable[[str, str, List[str], int], List[HarvestRecord]]


@runtime_checkable
class Source(Protocol):
    """Any object with these attributes is a valid Source."""

    name: str          # stable identifier, e.g. "openalex"
    label: str         # human-readable name, e.g. "OpenAlex"
    source_type: str   # one of: metadata | oa_search | preprint | biomed |
                       #          repository | books | theses
    default_max: int   # default page size / max results per query
    search: SearchFn


@dataclass(frozen=True)
class SourceAdapter:
    """Concrete Source built from a legacy `search_*` function."""

    name: str
    label: str
    source_type: str
    search: SearchFn
    default_max: int = 20

    def __call__(self, query: str, query_mode: str, subjects: List[str],
                 max_results: int = 0) -> List[HarvestRecord]:
        return self.search(query, query_mode, subjects, max_results or self.default_max)


__all__ = ["Source", "SourceAdapter", "SearchFn", "HarvestRecord"]
