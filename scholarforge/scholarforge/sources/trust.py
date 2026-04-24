"""Source-type classification and trust labelling.

Freemium differentiator: every record we surface gets a **source_type** (what
kind of artefact it is) and a **trust_label** (how much epistemic weight a
scholar should put on it). Both are deterministic functions of metadata we
already collect — no AI, no network calls.

Source types
------------
- journal_article   peer-reviewed article in a journal
- review            review / meta-analysis / systematic review
- preprint          preprint / working paper (not yet peer-reviewed)
- thesis            doctoral or master's thesis / dissertation
- book              monograph, edited volume, or book chapter
- report            technical report, white paper, policy brief
- dataset           dataset, code, supplementary material
- repository_item   generic item from an institutional repository
- unknown

Trust labels
------------
- peer_reviewed       journal article / book / review with strong provenance
- preprint            preprint — use with caution, unreviewed
- grey_literature     thesis, report, institutional repository item
- dataset             data/code — cite as evidence, not as claim
- uncertain           insufficient metadata to judge
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Source type classification
# ---------------------------------------------------------------------------

_REVIEW_PATTERNS = re.compile(
    r"\b(systematic review|meta-analysis|meta analysis|scoping review|"
    r"narrative review|umbrella review|literature review|state of the art)\b",
    re.IGNORECASE,
)

_THESIS_PATTERNS = re.compile(
    r"\b(ph\.?d\.? thesis|doctoral (dissertation|thesis)|master'?s thesis|"
    r"dissertation|habilitation|diploma thesis)\b",
    re.IGNORECASE,
)

_BOOK_PATTERNS = re.compile(
    r"\b(book chapter|monograph|edited volume|handbook|encyclopedia)\b",
    re.IGNORECASE,
)

_REPORT_PATTERNS = re.compile(
    r"\b(technical report|white paper|policy brief|working paper|"
    r"discussion paper|occasional paper)\b",
    re.IGNORECASE,
)


# Per-source default artefact type. Serves as fallback when metadata is thin.
_SOURCE_DEFAULTS = {
    "arxiv": "preprint",
    "ssrn": "preprint",
    "openalex": "journal_article",
    "crossref": "journal_article",
    "semantic_scholar": "journal_article",
    "doaj": "journal_article",
    "paperity": "journal_article",
    "oamg": "journal_article",
    "core": "journal_article",
    "pubmed": "journal_article",
    "pmc_fulltext": "journal_article",
    "europe_pmc": "journal_article",
    "google_books": "book",
    "internet_archive": "book",
    "open_library": "book",
    "ethesis": "thesis",
    "zenodo": "repository_item",
    "figshare": "repository_item",
    "hal": "repository_item",
    "openaire": "repository_item",
}


@dataclass(frozen=True)
class Classification:
    source_type: str
    trust_label: str
    reason: str


def classify(
    source: str,
    document_type: str = "",
    title: str = "",
    abstract: str = "",
    journal: str = "",
    year: str = "",
) -> Classification:
    """Return (source_type, trust_label) for a record.

    Pure function. Order of precedence:
      1. explicit document_type from the API (most trustworthy)
      2. title/abstract regex for reviews / theses / reports / books
      3. per-source default
      4. unknown + uncertain
    """
    dt = (document_type or "").strip().lower()
    title_s = title or ""
    abstract_s = abstract or ""
    haystack = f"{title_s} {abstract_s}"

    # 1) Explicit document_type mapping
    if dt:
        if dt in {"journal-article", "journal article", "article"}:
            st = "journal_article"
        elif dt in {"book", "book-chapter", "book-part", "monograph", "edited-book"}:
            st = "book"
        elif dt in {"thesis", "dissertation"}:
            st = "thesis"
        elif dt in {"preprint", "posted-content"}:
            st = "preprint"
        elif dt in {"dataset"}:
            st = "dataset"
        elif dt in {"report", "working-paper", "white-paper"}:
            st = "report"
        elif dt in {"review", "review-article"}:
            st = "review"
        else:
            st = ""
    else:
        st = ""

    # 2) Title/abstract overrides for things most APIs miss
    if _REVIEW_PATTERNS.search(haystack):
        st = "review"
    elif not st and _THESIS_PATTERNS.search(haystack):
        st = "thesis"
    elif not st and _BOOK_PATTERNS.search(haystack):
        st = "book"
    elif not st and _REPORT_PATTERNS.search(haystack):
        st = "report"

    # 3) Per-source default
    if not st:
        st = _SOURCE_DEFAULTS.get((source or "").lower(), "unknown")

    # 4) Trust label
    if st in {"journal_article", "review", "book"}:
        trust = "peer_reviewed"
    elif st == "preprint":
        trust = "preprint"
    elif st in {"thesis", "report", "repository_item"}:
        trust = "grey_literature"
    elif st == "dataset":
        trust = "dataset"
    else:
        trust = "uncertain"

    reason = _reason(source, dt, haystack, st)
    return Classification(source_type=st, trust_label=trust, reason=reason)


def _reason(source: str, dt: str, haystack: str, st: str) -> str:
    if dt:
        return f"document_type='{dt}'"
    if st == "review" and _REVIEW_PATTERNS.search(haystack):
        return "title/abstract matched review pattern"
    if st == "thesis" and _THESIS_PATTERNS.search(haystack):
        return "title/abstract matched thesis pattern"
    if st == "book" and _BOOK_PATTERNS.search(haystack):
        return "title/abstract matched book pattern"
    if st == "report" and _REPORT_PATTERNS.search(haystack):
        return "title/abstract matched report pattern"
    if source:
        return f"source default for {source}"
    return "no signal available"


def source_type(source: str, document_type: str = "", title: str = "",
                abstract: str = "") -> str:
    return classify(source, document_type, title, abstract).source_type


def trust_label(source: str, document_type: str = "", title: str = "",
                abstract: str = "") -> str:
    return classify(source, document_type, title, abstract).trust_label


__all__ = [
    "Classification", "classify", "source_type", "trust_label",
]
