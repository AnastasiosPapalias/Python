"""QueryPlan — the deterministic, human-readable search strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class Query:
    text: str
    mode: str   # broad | focused | phrase | review | recency | multilingual
    reason: str = ""


@dataclass
class QueryPlan:
    """A transparent record of how we turned the user's input into queries.

    The `pretty()` output is what the CLI shows before hitting the APIs.
    """

    raw_input: str
    classification: str
    title: str = ""
    subtitle: str = ""
    salient_phrases: List[str] = field(default_factory=list)
    keyword_bundles: List[List[str]] = field(default_factory=list)
    multilingual_terms: List[str] = field(default_factory=list)
    queries: List[Query] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def as_subject_strings(self) -> List[str]:
        """Legacy glue — return a list of strings the existing harvest runner
        can consume via `parse_subjects`. Uses the highest-signal phrases and
        the first keyword bundle, then falls back to the raw input."""
        out: List[str] = []
        seen = set()
        def add(x: str) -> None:
            k = x.lower().strip()
            if k and k not in seen:
                seen.add(k)
                out.append(x.strip())
        for p in self.salient_phrases[:3]:
            add(p)
        for bundle in self.keyword_bundles[:2]:
            for kw in bundle[:3]:
                add(kw)
        if not out:
            add(self.raw_input)
        return out

    def pretty(self, width: int = 76) -> str:
        lines: List[str] = []
        sep = "─" * width

        def row(label: str, value: str) -> None:
            lines.append(f"  {label:<20} {value}")

        lines.append(sep)
        lines.append("  QUERY PLAN")
        lines.append(sep)
        row("INPUT CLASSIFICATION", self.classification)
        if self.title:
            row("TITLE", self.title)
        if self.subtitle:
            row("SUBTITLE", self.subtitle)
        if self.salient_phrases:
            row("SALIENT PHRASES", " · ".join(f'"{p}"' for p in self.salient_phrases))
        for i, bundle in enumerate(self.keyword_bundles, start=1):
            row(f"KEYWORD BUNDLE {i}", " · ".join(bundle))
        if self.multilingual_terms:
            row("MULTILINGUAL", " · ".join(self.multilingual_terms))
        lines.append("")
        lines.append("  QUERIES")
        for q in self.queries:
            tag = f"[{q.mode}]".ljust(14)
            lines.append(f"    {tag} {q.text}")
        if self.notes:
            lines.append("")
            lines.append("  NOTES")
            for n in self.notes:
                lines.append(f"    · {n}")
        lines.append(sep)
        return "\n".join(lines)


__all__ = ["Query", "QueryPlan"]
