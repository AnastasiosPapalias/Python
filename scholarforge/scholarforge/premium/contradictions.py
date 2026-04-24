"""Premium seam — claim-conflict detection.

Surfaces passages that stake opposing claims about the same subject, so a
researcher can spot controversies, failed replications, and hedged findings
without reading every paper end to end. Freemium exposes the contract; the
paid build ships the detector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from . import require


@dataclass
class Contradiction:
    subject: str
    claim_a: str
    claim_b: str
    source_a: str
    source_b: str
    confidence: float = 0.0
    notes: str = ""


@dataclass
class ContradictionReport:
    items: List[Contradiction] = field(default_factory=list)
    scanned_records: int = 0


def scan(
    records: Iterable[Dict[str, Any]],
    *,
    min_confidence: float = 0.4,
    subject_filter: str = "",
) -> ContradictionReport:
    """Scan harvested records for conflicting claims.

    Premium — raises PremiumNotAvailableError when not activated.
    """
    require("contradictions")
    return _run_scanner(records, min_confidence=min_confidence,
                        subject_filter=subject_filter)


def _run_scanner(records, **_) -> ContradictionReport:  # pragma: no cover
    raise NotImplementedError("contradictions scanner is shipped in the paid build")


__all__ = ["Contradiction", "ContradictionReport", "scan"]
