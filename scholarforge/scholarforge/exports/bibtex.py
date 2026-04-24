"""BibTeX exporter with trust labels in the `note` field.

Design notes
------------
* We emit stable, reproducible cite-keys so the same harvest always renders
  the same `.bib` file (good for diff review / version control).
* `source_type` maps to a BibTeX entry type; unknowns fall back to `@misc`.
* Trust label + reason are preserved in `note = {}` so LaTeX users see
  provenance in any style that prints the note field.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

from scholarforge.exports import augment_with_trust


_TYPE_MAP = {
    "journal_article":  "article",
    "review":           "article",
    "preprint":         "misc",
    "thesis":           "phdthesis",
    "book":             "book",
    "report":           "techreport",
    "dataset":          "misc",
    "repository_item":  "misc",
    "unknown":          "misc",
}

_SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


def _slug(s: str, max_len: int = 20) -> str:
    return _SLUG_RE.sub("", (s or "").strip())[:max_len]


def _first_author_last(authors: str) -> str:
    """Best-effort last-name extraction from a free-form author string."""
    if not authors:
        return "anon"
    first = authors.split(";")[0].split(",")[0].strip()
    if "," in authors.split(";")[0]:
        # "Last, First" format
        return _slug(authors.split(";")[0].split(",")[0]) or "anon"
    # "First Last" format → take the last whitespace-separated token
    parts = first.split()
    return _slug(parts[-1] if parts else first) or "anon"


def _first_title_word(title: str) -> str:
    for w in (title or "").split():
        s = _slug(w)
        if len(s) >= 3:
            return s.lower()
    return "untitled"


def _cite_key(record: Dict[str, Any]) -> str:
    author = _first_author_last(record.get("authors", "")).lower() or "anon"
    year = str(record.get("year", "") or "nd")[:4]
    word = _first_title_word(record.get("title", ""))
    return f"{author}{year}{word}"


def _escape(value: str) -> str:
    if not value:
        return ""
    # Minimal BibTeX escaping: curly-brace and backslash; strip control chars.
    s = str(value).replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    return s.replace("\n", " ").replace("\r", " ").strip()


def _format_authors(authors: str) -> str:
    if not authors:
        return ""
    # Preserve as-is but normalise separators: BibTeX uses " and ".
    raw = [a.strip() for a in re.split(r"[;|]", authors) if a.strip()]
    if len(raw) <= 1:
        return _escape(authors.strip())
    return " and ".join(_escape(a) for a in raw)


def _emit_entry(record: Dict[str, Any]) -> str:
    entry_type = _TYPE_MAP.get(record.get("source_type", "unknown"), "misc")
    key = _cite_key(record)
    fields: List[tuple[str, str]] = []

    def add(name: str, value: str) -> None:
        if value:
            fields.append((name, _escape(value)))

    add("title", record.get("title", ""))
    authors = _format_authors(record.get("authors", ""))
    if authors:
        fields.append(("author", authors))
    add("year", str(record.get("year", "") or "")[:4])
    add("doi", record.get("doi", ""))
    url = record.get("open_access_url") or record.get("url") or record.get("pdf_url", "")
    add("url", url)
    add("journal", record.get("journal", ""))
    add("language", record.get("language", ""))

    trust = record.get("trust_label", "uncertain")
    source = record.get("source", "")
    note_parts = [f"trust: {trust}", f"source: {source}"] if source else [f"trust: {trust}"]
    reason = record.get("trust_reason", "")
    if reason:
        note_parts.append(f"reason: {reason}")
    fields.append(("note", _escape("; ".join(note_parts))))

    lines = [f"@{entry_type}{{{key},"]
    for i, (name, value) in enumerate(fields):
        sep = "," if i < len(fields) - 1 else ""
        lines.append(f"  {name} = {{{value}}}{sep}")
    lines.append("}")
    return "\n".join(lines)


def render(records: Iterable[Dict[str, Any]]) -> str:
    """Render an iterable of records into a single BibTeX string."""
    enriched = augment_with_trust(records)
    # Deduplicate cite-keys by appending -2, -3, ...
    seen: Dict[str, int] = {}
    entries: List[str] = []
    for r in enriched:
        key = _cite_key(r)
        n = seen.get(key, 0) + 1
        seen[key] = n
        if n > 1:
            r = dict(r, _key_suffix=f"-{n}")
            entry = _emit_entry(r)
            entry = entry.replace(f"@{_TYPE_MAP.get(r.get('source_type','unknown'),'misc')}{{{key},",
                                  f"@{_TYPE_MAP.get(r.get('source_type','unknown'),'misc')}{{{key}-{n},")
            entries.append(entry)
        else:
            entries.append(_emit_entry(r))
    return "\n\n".join(entries) + ("\n" if entries else "")


def write(records: Iterable[Dict[str, Any]], path) -> int:
    text = render(records)
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text.count("@") if text else 0


__all__ = ["render", "write"]
