"""CSL-JSON exporter (Citation Style Language / Zotero / Pandoc compatible).

Trust and provenance are carried in two places:
  * `note` — human-readable "trust: peer_reviewed; source: openalex; …"
  * `custom.scholarforge` — structured provenance (source, source_type,
    trust_label, trust_reason, score) so downstream tools can filter on it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from scholarforge.exports import augment_with_trust


_TYPE_MAP = {
    "journal_article":  "article-journal",
    "review":           "article-journal",
    "preprint":         "article",
    "thesis":           "thesis",
    "book":             "book",
    "report":           "report",
    "dataset":          "dataset",
    "repository_item":  "article",
    "unknown":          "article",
}


def _authors_to_csl(raw: str) -> List[Dict[str, str]]:
    if not raw:
        return []
    parts = [p.strip() for p in re.split(r"[;|]", raw) if p.strip()]
    out: List[Dict[str, str]] = []
    for p in parts:
        if "," in p:
            family, _, given = p.partition(",")
            out.append({"family": family.strip(), "given": given.strip()})
        else:
            toks = p.split()
            if len(toks) == 1:
                out.append({"family": toks[0]})
            else:
                out.append({"family": toks[-1], "given": " ".join(toks[:-1])})
    return out


def _year_to_issued(year: Any) -> Dict[str, Any]:
    s = str(year or "").strip()[:4]
    if s.isdigit():
        return {"date-parts": [[int(s)]]}
    return {}


def to_csl_item(record: Dict[str, Any]) -> Dict[str, Any]:
    st = record.get("source_type", "unknown")
    item: Dict[str, Any] = {
        "id": record.get("doi") or record.get("source_id") or record.get("url") or record.get("title", "untitled"),
        "type": _TYPE_MAP.get(st, "article"),
        "title": record.get("title", ""),
    }
    authors = _authors_to_csl(record.get("authors", ""))
    if authors:
        item["author"] = authors
    issued = _year_to_issued(record.get("year"))
    if issued:
        item["issued"] = issued
    if record.get("doi"):
        item["DOI"] = record["doi"]
    url = record.get("open_access_url") or record.get("url") or record.get("pdf_url")
    if url:
        item["URL"] = url
    if record.get("journal"):
        item["container-title"] = record["journal"]
    if record.get("abstract"):
        item["abstract"] = record["abstract"]
    if record.get("language"):
        item["language"] = record["language"]

    trust = record.get("trust_label", "uncertain")
    source = record.get("source", "")
    reason = record.get("trust_reason", "")
    note_parts = [f"trust: {trust}"]
    if source:
        note_parts.append(f"source: {source}")
    if reason:
        note_parts.append(f"reason: {reason}")
    item["note"] = "; ".join(note_parts)
    item["custom"] = {
        "scholarforge": {
            "source": source,
            "source_type": st,
            "trust_label": trust,
            "trust_reason": reason,
            "relevance_score": record.get("relevance_score"),
        }
    }
    return item


def render(records: Iterable[Dict[str, Any]]) -> str:
    enriched = augment_with_trust(records)
    items = [to_csl_item(r) for r in enriched]
    return json.dumps(items, indent=2, ensure_ascii=False) + "\n"


def write(records: Iterable[Dict[str, Any]], path) -> int:
    text = render(records)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    # Count returned = number of items written.
    try:
        return len(json.loads(text))
    except Exception:
        return 0


__all__ = ["render", "write", "to_csl_item"]
