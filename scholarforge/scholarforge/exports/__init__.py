"""Provenance-aware exports for ScholarForge.

Freemium deliverable: given a harvested record set, produce the three formats
that scholars and writers actually use — BibTeX for LaTeX, CSL-JSON for
Zotero/Pandoc, annotated Markdown for reading-ready bibliographies. Every
exported record carries a **trust label** derived from `sources.trust`, so
downstream readers see the provenance, not just the citation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from scholarforge.sources.trust import classify


def load_records(path: Path) -> List[Dict[str, Any]]:
    """Read a JSONL file of harvest records into a list of dicts."""
    path = Path(path)
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def find_project_records(project_root: Path) -> Optional[Path]:
    """Return the best records file inside a project root, or None.

    Priority: `metadata/filtered_records.jsonl` → any `metadata/*.jsonl` →
    any `sources/*.jsonl`. Freshest by mtime wins among siblings.
    """
    root = Path(project_root)
    preferred = root / "metadata" / "filtered_records.jsonl"
    if preferred.exists():
        return preferred
    candidates: List[Path] = []
    for subdir in ("metadata", "sources"):
        d = root / subdir
        if d.is_dir():
            candidates.extend(d.glob("*.jsonl"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def augment_with_trust(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return records with source_type / trust_label / trust_reason filled in.

    Non-destructive: never overwrites an existing non-empty value.
    """
    out: List[Dict[str, Any]] = []
    for r in records:
        r = dict(r)
        if not r.get("source_type") or not r.get("trust_label"):
            c = classify(
                source=r.get("source", ""),
                document_type=r.get("document_type", ""),
                title=r.get("title", ""),
                abstract=r.get("abstract", ""),
            )
            if not r.get("source_type"):
                r["source_type"] = c.source_type
            if not r.get("trust_label"):
                r["trust_label"] = c.trust_label
            if not r.get("trust_reason"):
                r["trust_reason"] = c.reason
        else:
            r.setdefault("trust_reason", "pre-classified")
        out.append(r)
    return out


__all__ = [
    "load_records", "find_project_records", "augment_with_trust",
]
