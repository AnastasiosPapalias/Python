"""scholarforge.premium — premium seams (Stage 8).

Stubs and interfaces for the paid layer. Freemium code never imports from
these modules; everything routed through `scholarforge.premium` surfaces a
clean `PremiumNotAvailableError` when invoked without a valid premium
activation.

Modules
-------
atlas            — citation / co-citation graph over a project corpus
clusters         — topic clustering across harvested records
contradictions   — claim-conflict detection between records
thesis_pack      — thesis scaffold export (chapters, outline, literature matrix)
book_pack        — book scaffold export (front matter, chapters, bibliography)
memory_graph     — persistent cross-project research graph

Activation
----------
Premium is gated by an activation key read in this priority order:

    1. env var   SCHOLARFORGE_PREMIUM_KEY
    2. global    ~/.scholarforge.toml  →  [premium] license_key = "..."
    3. env var   SCHOLARFORGE_PREMIUM_UNLOCK  ("1" | "true" | "yes" — for tests)

No network check is performed. The key's *presence* toggles the seam; the
real validation happens server-side when a build is released.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class PremiumNotAvailableError(RuntimeError):
    """Raised when a premium entry point is called without activation."""

    def __init__(self, feature: str) -> None:
        super().__init__(
            f"'{feature}' is a ScholarForge Premium feature. "
            "See https://github.com/AnastasiosPapalias/Python/tree/main/scholarforge "
            "for how to activate, or run `scholarforge premium` for local status."
        )
        self.feature = feature


@dataclass(frozen=True)
class PremiumStatus:
    active: bool
    source: str  # "env" | "config" | "unlock" | "none"
    key_preview: str  # masked form of the key, or ""


def _read_toml_license() -> Optional[str]:
    """Return the [premium].license_key from ~/.scholarforge.toml, if any."""
    try:
        from scholarforge.config.global_config import global_config_path
    except Exception:
        return None
    path = global_config_path()
    if not path or not Path(path).exists():
        return None
    try:
        import tomllib  # py3.11+
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore
        except ModuleNotFoundError:
            return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return None
    block = data.get("premium") or {}
    value = block.get("license_key")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def get_status() -> PremiumStatus:
    """Inspect the environment and config for a premium activation."""
    env_key = os.environ.get("SCHOLARFORGE_PREMIUM_KEY", "").strip()
    if env_key:
        return PremiumStatus(active=True, source="env", key_preview=_mask(env_key))

    toml_key = _read_toml_license()
    if toml_key:
        return PremiumStatus(active=True, source="config", key_preview=_mask(toml_key))

    unlock = os.environ.get("SCHOLARFORGE_PREMIUM_UNLOCK", "").strip().lower()
    if unlock in {"1", "true", "yes", "on"}:
        return PremiumStatus(active=True, source="unlock", key_preview="test-unlock")

    return PremiumStatus(active=False, source="none", key_preview="")


def is_active() -> bool:
    return get_status().active


def require(feature: str) -> None:
    """Gate a premium entry point. Raises PremiumNotAvailableError if inactive."""
    if not is_active():
        raise PremiumNotAvailableError(feature)


def _mask(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


__all__ = [
    "PremiumNotAvailableError",
    "PremiumStatus",
    "get_status",
    "is_active",
    "require",
]
