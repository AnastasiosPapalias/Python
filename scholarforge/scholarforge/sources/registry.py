"""Registry of all 20 academic sources.

Stage 2 wraps the legacy `search_*` functions behind the `SourceAdapter`
protocol. Stage-later migrations can replace individual entries with proper
per-source modules without touching callers.
"""

from __future__ import annotations

from typing import Dict, List

from scholarforge import _legacy as L
from scholarforge.sources.base import SourceAdapter

# Grouping mirrors the README. Used by the source-picker UI and for
# per-type recall balancing in the harvest runner.
METADATA_BACKBONE = "metadata"
OA_SEARCH = "oa_search"
PREPRINT = "preprint"
BIOMED = "biomed"
REPOSITORY = "repository"
BOOKS = "books"
THESES = "theses"


ALL_SOURCES: List[SourceAdapter] = [
    # Metadata & citation backbone
    SourceAdapter("openalex",         "OpenAlex",          METADATA_BACKBONE, L.search_openalex,        25),
    SourceAdapter("crossref",         "Crossref",          METADATA_BACKBONE, L.search_crossref,        25),
    SourceAdapter("semantic_scholar", "Semantic Scholar",  METADATA_BACKBONE, L.search_semantic_scholar, 20),
    # OA-first search engines
    SourceAdapter("oamg",             "OA.mg",             OA_SEARCH,         L.search_oamg,            20),
    SourceAdapter("core",             "CORE",              OA_SEARCH,         L.search_core,            20),
    SourceAdapter("doaj",             "DOAJ",              OA_SEARCH,         L.search_doaj,            20),
    SourceAdapter("paperity",         "Paperity",          OA_SEARCH,         L.search_paperity,        20),
    # Preprints & disciplinary repositories
    SourceAdapter("arxiv",            "arXiv",             PREPRINT,          L.search_arxiv,           20),
    SourceAdapter("ssrn",             "SSRN",              PREPRINT,          L.search_ssrn,            20),
    # Biomedical full-text
    SourceAdapter("pubmed",           "PubMed",            BIOMED,            L.search_pubmed,          20),
    SourceAdapter("pmc_fulltext",     "PMC Full-Text",     BIOMED,            L.search_pmc_fulltext,    20),
    SourceAdapter("europe_pmc",       "Europe PMC",        BIOMED,            L.search_europe_pmc,      20),
    # Open repositories
    SourceAdapter("zenodo",           "Zenodo",            REPOSITORY,        L.search_zenodo,          20),
    SourceAdapter("figshare",         "Figshare",          REPOSITORY,        L.search_figshare,        20),
    SourceAdapter("hal",              "HAL",               REPOSITORY,        L.search_hal,             20),
    SourceAdapter("openaire",         "OpenAIRE",          REPOSITORY,        L.search_openaire,        20),
    # Books & general
    SourceAdapter("google_books",     "Google Books",      BOOKS,             L.search_google_books,    20),
    SourceAdapter("internet_archive", "Internet Archive",  BOOKS,             L.search_internet_archive, 20),
    SourceAdapter("open_library",     "Open Library",      BOOKS,             L.search_open_library,    20),
    # Theses
    SourceAdapter("ethesis",          "EThOS / DART-Europe", THESES,          L.search_ethesis,         15),
]


BY_NAME: Dict[str, SourceAdapter] = {s.name: s for s in ALL_SOURCES}


def get(name: str) -> SourceAdapter:
    return BY_NAME[name]


def by_type(source_type: str) -> List[SourceAdapter]:
    return [s for s in ALL_SOURCES if s.source_type == source_type]


__all__ = [
    "ALL_SOURCES", "BY_NAME", "get", "by_type",
    "METADATA_BACKBONE", "OA_SEARCH", "PREPRINT", "BIOMED",
    "REPOSITORY", "BOOKS", "THESES",
]
