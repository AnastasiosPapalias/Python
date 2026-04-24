"""Parse a publication-like title into structured parts + salient phrases.

Deterministic — no AI, no external resources beyond the stdlib.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple


# Compact multi-language stopword list. Covers the user's working languages.
_STOPWORDS = {
    # English
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or",
    "but", "is", "are", "was", "were", "be", "been", "being", "it", "its",
    "this", "that", "these", "those", "with", "without", "from", "by",
    "about", "into", "between", "among", "as", "than", "then", "also",
    "such", "some", "any", "all", "no", "not", "very", "more", "most",
    "study", "studies", "paper", "article", "research", "review",
    "analysis", "current", "recent", "new", "emerging", "toward",
    "towards", "frontier", "frontiers", "breakthrough", "breakthroughs",
    "contemporary",
    # Greek
    "ο", "η", "το", "οι", "τα", "του", "της", "των", "τον", "την",
    "μια", "ένα", "έναν", "και", "ή", "στον", "στην", "στο", "στα",
    "για", "με", "χωρίς", "από", "προς", "είναι", "ήταν",
    # Common other
    "de", "la", "le", "et", "du", "des", "un", "une", "y", "o",
}


@dataclass(frozen=True)
class ParsedTitle:
    title: str
    subtitle: str = ""
    content_words: Tuple[str, ...] = field(default_factory=tuple)
    salient_phrases: Tuple[str, ...] = field(default_factory=tuple)


def _split_title_subtitle(raw: str) -> Tuple[str, str]:
    """Split on the first ':', em-dash, or en-dash (with spaces)."""
    s = (raw or "").strip().strip('"').strip("'")
    # Prefer colon with surrounding space if present.
    for sep in [":", " \u2014 ", " \u2013 ", " - "]:
        if sep in s:
            left, right = s.split(sep, 1)
            return left.strip(), right.strip()
    return s, ""


def _tokens(text: str) -> List[str]:
    return [t for t in re.split(r"[^\w]+", text.lower(), flags=re.UNICODE) if t]


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def content_words(text: str) -> List[str]:
    """Tokens with stopwords + short/numeric tokens + 1-char tokens removed."""
    out = []
    for t in _tokens(text):
        if len(t) < 3:
            continue
        if t.isdigit():
            continue
        if t in _STOPWORDS:
            continue
        if _strip_accents(t) in _STOPWORDS:
            continue
        out.append(t)
    return out


def _ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def salient_phrases(raw: str, max_phrases: int = 6) -> List[str]:
    """Extract multi-word phrases that look meaningful.

    Algorithm:
      1. Split original text into sentences/clauses on punctuation.
      2. Within each clause, find runs of consecutive content words.
      3. Keep 2- and 3-grams from those runs.
      4. De-duplicate, prefer longer phrases, cap at `max_phrases`.
    """
    s = (raw or "").strip()
    if not s:
        return []

    clauses = re.split(r"[.!?;:,\u2014\u2013]+", s)

    phrases: List[str] = []
    seen = set()
    for clause in clauses:
        words = re.findall(r"[\w]+", clause, flags=re.UNICODE)
        run: List[str] = []
        for w in words + [""]:  # sentinel flushes the run
            lw = w.lower()
            is_content = (
                len(w) >= 3 and not w.isdigit()
                and lw not in _STOPWORDS
                and _strip_accents(lw) not in _STOPWORDS
            )
            if is_content:
                run.append(w)
            else:
                if len(run) >= 2:
                    for n in (3, 2):
                        for ng in _ngrams(run, n):
                            key = ng.lower()
                            if key not in seen:
                                seen.add(key)
                                phrases.append(ng)
                run = []

    # Score: longer phrases first, then by content-word frequency.
    counter = Counter(content_words(raw))
    def score(p: str) -> Tuple[int, int]:
        toks = p.split()
        return (len(toks), sum(counter.get(t.lower(), 0) for t in toks))
    phrases.sort(key=score, reverse=True)
    return phrases[:max_phrases]


def parse(raw: str) -> ParsedTitle:
    title, subtitle = _split_title_subtitle(raw)
    full = (title + " " + subtitle).strip()
    return ParsedTitle(
        title=title,
        subtitle=subtitle,
        content_words=tuple(content_words(full)),
        salient_phrases=tuple(salient_phrases(raw)),
    )


__all__ = ["ParsedTitle", "parse", "content_words", "salient_phrases"]
