"""Turn a researcher's raw input into a `QueryPlan` of concrete queries.

Deterministic. Multiple strategies per input:
  - broad        content words joined
  - focused      title + first bundle term
  - phrase       quoted title or top salient phrase
  - review       OR'd with review/meta-analysis terms
  - recency      last three years appended (opt-in in the CLI)
  - multilingual one per non-English variant found in a lexicon

The plan is shown to the user before hitting the APIs.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from scholarforge.search.input_classifier import classify as classify_input
from scholarforge.search.title_parser import parse as parse_title
from scholarforge.search.lexicon import find_bundles, multilingual_for
from scholarforge.search.query_plan import Query, QueryPlan


REVIEW_TAIL = 'review OR "meta-analysis" OR "systematic review"'


def _dedupe(items: List[str]) -> List[str]:
    out, seen = [], set()
    for x in items:
        k = x.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(x.strip())
    return out


def expand(
    raw: str,
    *,
    include_review: bool = True,
    include_recency: bool = False,
    include_multilingual: bool = False,
    now_year: Optional[int] = None,
) -> QueryPlan:
    """Build a query plan from the user's input."""
    cls = classify_input(raw)
    parsed = parse_title(raw)
    plan = QueryPlan(
        raw_input=raw,
        classification=f"{cls.kind} ({cls.reason})",
        title=parsed.title,
        subtitle=parsed.subtitle,
        salient_phrases=list(parsed.salient_phrases),
    )

    # Bundle lookup uses phrases + title/content words.
    lookup_terms = list(parsed.salient_phrases) + [parsed.title] + list(parsed.content_words)
    bundles = find_bundles(_dedupe(lookup_terms))
    plan.keyword_bundles = bundles
    if include_multilingual:
        plan.multilingual_terms = multilingual_for(_dedupe(lookup_terms))

    # ── queries ────────────────────────────────────────────────────────────
    if cls.kind == "exact_phrase":
        plan.queries.append(Query(raw.strip().strip('"').strip("'"),
                                  "phrase", "user supplied quoted phrase"))
        plan.queries.append(Query(raw.strip().strip('"').strip("'"),
                                  "broad", "same phrase, unquoted"))
        plan.notes.append("exact_phrase inputs skip bundle expansion")
        return plan

    if cls.kind == "keyword_list":
        parts = _dedupe([p.strip() for p in raw.split(",") if p.strip()])
        plan.queries.append(Query(" ".join(parts), "broad",
                                  "all keywords together"))
        for p in parts[:3]:
            plan.queries.append(Query(f'"{p}"', "phrase", "per-keyword phrase"))
        if include_review and parts:
            plan.queries.append(Query(f"{parts[0]} {REVIEW_TAIL}", "review",
                                      "first keyword + review tail"))
        return plan

    # title_like, question_like, broad_topic — same core strategy
    # broad
    content = " ".join(parsed.content_words) or raw.strip()
    plan.queries.append(Query(content, "broad", "content words joined"))

    # focused — title + first bundle term if we have one
    if bundles and parsed.title:
        kw = bundles[0][1] if len(bundles[0]) > 1 else bundles[0][0]
        plan.queries.append(Query(f'"{parsed.title}" {kw}', "focused",
                                  "title + bundle synonym"))
    elif parsed.title:
        plan.queries.append(Query(f'"{parsed.title}"', "focused",
                                  "title as anchor"))

    # phrase — top salient phrase
    if parsed.salient_phrases:
        plan.queries.append(Query(f'"{parsed.salient_phrases[0]}"', "phrase",
                                  "top salient phrase"))

    # review variant
    if include_review:
        anchor = parsed.salient_phrases[0] if parsed.salient_phrases else content
        plan.queries.append(Query(f"{anchor} {REVIEW_TAIL}", "review",
                                  "anchor + review/meta-analysis tail"))

    # recency variant
    if include_recency:
        year_now = now_year or datetime.now().year
        span = f"{year_now - 2}..{year_now}"
        anchor = parsed.salient_phrases[0] if parsed.salient_phrases else content
        plan.queries.append(Query(f"{anchor} {span}", "recency",
                                  f"anchor + {span}"))

    # multilingual
    if include_multilingual:
        for variant in plan.multilingual_terms[:3]:
            plan.queries.append(Query(variant, "multilingual",
                                      "non-English variant from lexicon"))

    # De-duplicate queries by (text, mode)
    dedup: List[Query] = []
    seen = set()
    for q in plan.queries:
        k = (q.text.lower(), q.mode)
        if k not in seen:
            seen.add(k)
            dedup.append(q)
    plan.queries = dedup

    if not bundles:
        plan.notes.append("no domain lexicon matched — bundle expansion skipped")
    return plan


__all__ = ["expand"]
