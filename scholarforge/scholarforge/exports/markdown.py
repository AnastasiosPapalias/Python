"""Annotated Markdown bibliography with trust badges.

Each record renders as a short entry:

    ### Title of the paper
    *Authors* · Year · Journal
    trust: peer_reviewed  ·  source: openalex  ·  [DOI](…)
    > abstract first 240 chars…

The entries are grouped by trust tier so the reader sees peer-reviewed work
first, preprints next, grey literature below that. A small summary table at
the top gives the record counts per tier.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from scholarforge.exports import augment_with_trust


_TRUST_ORDER = ["peer_reviewed", "preprint", "grey_literature", "dataset", "uncertain"]
_TRUST_BADGES = {
    "peer_reviewed":  "★★★ peer-reviewed",
    "preprint":       "★★   preprint",
    "grey_literature":"★★   grey literature",
    "dataset":        "·    dataset / code",
    "uncertain":      "?    uncertain",
}


def _clip(text: str, n: int) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _render_entry(r: Dict[str, Any]) -> str:
    title = r.get("title", "Untitled").strip()
    authors = r.get("authors", "").strip()
    year = str(r.get("year", "") or "").strip()[:4]
    journal = r.get("journal", "").strip()
    doi = r.get("doi", "").strip()
    url = (r.get("open_access_url") or r.get("url") or r.get("pdf_url") or "").strip()
    abstract = _clip(r.get("abstract", ""), 320)

    header = f"### {title}"
    meta_bits = []
    if authors: meta_bits.append(f"*{authors}*")
    if year:    meta_bits.append(year)
    if journal: meta_bits.append(journal)
    meta = " · ".join(meta_bits)

    trust = r.get("trust_label", "uncertain")
    source = r.get("source", "")
    badge = _TRUST_BADGES.get(trust, trust)
    prov_bits = [f"`{badge}`"]
    if source:
        prov_bits.append(f"source: **{source}**")
    if doi:
        prov_bits.append(f"[DOI](https://doi.org/{doi})")
    elif url:
        prov_bits.append(f"[link]({url})")
    reason = r.get("trust_reason", "")
    if reason:
        prov_bits.append(f"_reason: {reason}_")
    provenance = "  ·  ".join(prov_bits)

    parts = [header]
    if meta:
        parts.append(meta)
    parts.append(provenance)
    if abstract:
        parts.append(f"> {abstract}")
    return "\n".join(parts)


def _summary_table(records: List[Dict[str, Any]]) -> str:
    counts: Dict[str, int] = {}
    for r in records:
        counts[r.get("trust_label", "uncertain")] = counts.get(r.get("trust_label", "uncertain"), 0) + 1
    rows = ["| Trust tier | Count |", "|---|---|"]
    for tier in _TRUST_ORDER:
        if tier in counts:
            rows.append(f"| {_TRUST_BADGES[tier]} | {counts[tier]} |")
    return "\n".join(rows)


def render(records: Iterable[Dict[str, Any]], title: str = "Bibliography") -> str:
    enriched = augment_with_trust(records)
    grouped: Dict[str, List[Dict[str, Any]]] = {t: [] for t in _TRUST_ORDER}
    for r in enriched:
        tier = r.get("trust_label", "uncertain")
        grouped.setdefault(tier, []).append(r)

    out: List[str] = [f"# {title}", "", f"_Total records: {len(enriched)}_", ""]
    out.append(_summary_table(enriched))
    out.append("")

    for tier in _TRUST_ORDER:
        items = grouped.get(tier, [])
        if not items:
            continue
        out.append(f"## {_TRUST_BADGES[tier]}  ({len(items)})")
        out.append("")
        for r in items:
            out.append(_render_entry(r))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def write(records: Iterable[Dict[str, Any]], path, title: str = "Bibliography") -> int:
    text = render(records, title=title)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text.count("\n### ")


__all__ = ["render", "write"]
