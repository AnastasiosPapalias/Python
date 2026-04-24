"""Classify a researcher's raw input so we can choose the right expansion strategy.

Categories
----------
- title_like       Looks like a publication title. Often contains a colon or
                   em-dash separating title and subtitle. Usually 6-20 words,
                   mostly content words, starts with a capital, ends without
                   a question mark.
- question_like    A research question. Starts with how/why/what/when/where/
                   which/who/does/do/is/are/can/should, or ends with '?'.
- keyword_list     Comma-separated short phrases, e.g. "OCD, ERP therapy,
                   exposure response prevention".
- exact_phrase     Wrapped in quotes or a short 2-4 word span the user wants
                   matched verbatim.
- broad_topic      Everything else — short, thematic, under ~5 words.

Pure functions, no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# Question words in several languages the user often works in.
_QUESTION_WORDS = {
    # English
    "how", "why", "what", "when", "where", "which", "who", "whom", "whose",
    "does", "do", "did", "is", "are", "was", "were", "can", "could",
    "should", "would", "will", "shall",
    # Greek
    "πώς", "γιατί", "τι", "πότε", "πού", "ποιος", "ποια", "ποιο",
    "είναι", "μπορεί",
    # French / Spanish / German — light coverage
    "comment", "pourquoi", "qué", "cómo", "por qué", "warum", "wie", "was",
}


@dataclass(frozen=True)
class Classification:
    kind: str          # title_like | question_like | keyword_list | exact_phrase | broad_topic
    confidence: float  # 0.0 – 1.0
    reason: str


def classify(raw: str) -> Classification:
    """Return the best guess for what the user typed."""
    text = (raw or "").strip()
    if not text:
        return Classification("broad_topic", 0.0, "empty input")

    # exact_phrase: fully quoted
    if (text.startswith('"') and text.endswith('"')) or \
       (text.startswith("'") and text.endswith("'")):
        return Classification("exact_phrase", 0.95, "wrapped in quotes")

    # keyword_list: at least one comma + short segments
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
        short_parts = sum(1 for p in parts if len(p.split()) <= 4)
        if len(parts) >= 2 and short_parts >= len(parts) - 1:
            return Classification(
                "keyword_list", 0.9,
                f"comma-separated with {len(parts)} short segments",
            )

    # question_like: '?' or starts with an interrogative
    first_word = re.split(r"\s+", text, maxsplit=1)[0].lower().rstrip(",.;:")
    if text.endswith("?") or first_word in _QUESTION_WORDS:
        return Classification("question_like", 0.9,
                              f"starts with '{first_word}' / ends with '?'")

    # title_like: has a colon/em-dash separator OR is long, capitalised, no '?'
    has_separator = bool(re.search(r"[:\u2014\u2013]", text))
    word_count = len(text.split())
    starts_capital = text[:1].isupper()
    if has_separator and word_count >= 4:
        return Classification("title_like", 0.95,
                              "colon / em-dash separator with ≥4 words")
    if word_count >= 6 and starts_capital and not text.endswith("?"):
        return Classification("title_like", 0.7,
                              f"{word_count} words, starts capital, no '?'")

    # Fallback — short thematic input
    if word_count <= 4:
        return Classification("broad_topic", 0.8, f"{word_count} words, thematic")
    return Classification("broad_topic", 0.5, "fallback")


__all__ = ["Classification", "classify"]
