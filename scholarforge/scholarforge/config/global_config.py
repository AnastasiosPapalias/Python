"""scholarforge.config.global_config — user-level API key and preference store.

Priority order (highest wins):
  1. Environment variable  (e.g. SCHOLARFORGE_CORE_API_KEY)
  2. ~/.scholarforge.toml  [api_keys] section
  3. .env file in cwd or any parent directory

Supported keys
--------------
  core_api_key          — CORE API key (free at https://core.ac.uk/services/api)
  semantic_scholar_key  — Semantic Scholar API key (free at https://www.semanticscholar.org/product/api)
  elsevier_api_key      — Elsevier TDM API key (optional, paid)
  wiley_api_key         — Wiley TDM API key (optional, paid)

Usage
-----
  from scholarforge.config.global_config import get_api_keys
  keys = get_api_keys()
  core_key = keys.core_api_key  # str or ""
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Dict, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ApiKeys:
    core_api_key: str = ""
    semantic_scholar_key: str = ""
    elsevier_api_key: str = ""
    wiley_api_key: str = ""

    def as_dict(self) -> Dict[str, str]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def has_any(self) -> bool:
        return any(getattr(self, f.name) for f in fields(self))


# ─────────────────────────────────────────────────────────────────────────────
# Env var names
# ─────────────────────────────────────────────────────────────────────────────

_ENV_MAP = {
    "core_api_key":         "SCHOLARFORGE_CORE_API_KEY",
    "semantic_scholar_key": "SCHOLARFORGE_SEMANTIC_SCHOLAR_KEY",
    "elsevier_api_key":     "SCHOLARFORGE_ELSEVIER_API_KEY",
    "wiley_api_key":        "SCHOLARFORGE_WILEY_API_KEY",
}

# Also accept the bare names that users commonly set
_ENV_ALIASES = {
    "core_api_key":         ["CORE_API_KEY"],
    "semantic_scholar_key": ["SEMANTIC_SCHOLAR_API_KEY", "S2_API_KEY"],
    "elsevier_api_key":     ["ELSEVIER_API_KEY"],
    "wiley_api_key":        ["WILEY_API_KEY"],
}

# ─────────────────────────────────────────────────────────────────────────────
# .env loader (no external deps)
# ─────────────────────────────────────────────────────────────────────────────

def _find_dotenv(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from start (default: cwd) looking for a .env file."""
    here = (start or Path.cwd()).resolve()
    for directory in [here, *here.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def _load_dotenv(path: Path) -> Dict[str, str]:
    """Parse a .env file into a dict. Supports KEY=value and KEY="value"."""
    result: Dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
    except OSError:
        pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ~/.scholarforge.toml loader
# ─────────────────────────────────────────────────────────────────────────────

_TOML_KEY_LINE = re.compile(r"^\s*([A-Za-z_][\w]*)\s*=\s*\"([^\"]*)\"\s*$")


def _load_global_toml() -> Dict[str, str]:
    """Read [api_keys] section from ~/.scholarforge.toml."""
    toml_path = Path.home() / ".scholarforge.toml"
    if not toml_path.is_file():
        return {}

    result: Dict[str, str] = {}
    in_api_keys = False
    try:
        for line in toml_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                in_api_keys = stripped in ("[api_keys]", '["api_keys"]')
                continue
            if not in_api_keys:
                continue
            m = _TOML_KEY_LINE.match(line)
            if m:
                result[m.group(1)] = m.group(2)
    except OSError:
        pass
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_api_keys(dotenv_dir: Optional[Path] = None) -> ApiKeys:
    """Return API keys resolved from env vars → ~/.scholarforge.toml → .env."""
    # Layer 3: .env file (lowest priority)
    dotenv_path = _find_dotenv(dotenv_dir)
    dotenv_values = _load_dotenv(dotenv_path) if dotenv_path else {}

    # Layer 2: ~/.scholarforge.toml
    toml_values = _load_global_toml()

    keys = ApiKeys()
    for field_name in [f.name for f in fields(ApiKeys)]:
        # Layer 1: env vars (highest priority)
        primary_env = _ENV_MAP.get(field_name, "")
        value = os.environ.get(primary_env, "")
        if not value:
            for alias in _ENV_ALIASES.get(field_name, []):
                value = os.environ.get(alias, "")
                if value:
                    break
        # Layer 2: toml
        if not value:
            value = toml_values.get(field_name, "")
        # Layer 3: dotenv
        if not value:
            value = dotenv_values.get(primary_env, "")
            if not value:
                for alias in _ENV_ALIASES.get(field_name, []):
                    value = dotenv_values.get(alias, "")
                    if value:
                        break
        setattr(keys, field_name, value)

    return keys


def global_config_path() -> Path:
    return Path.home() / ".scholarforge.toml"


def write_global_config_template() -> Path:
    """Write a commented template to ~/.scholarforge.toml if it doesn't exist."""
    path = global_config_path()
    if path.exists():
        return path
    path.write_text(
        "# ScholarForge global configuration\n"
        "# This file lives at ~/.scholarforge.toml\n"
        "# All values are optional — ScholarForge works without any API keys.\n"
        "# Keys improve rate limits and result quality for authenticated sources.\n"
        "\n"
        "[api_keys]\n"
        '# core_api_key = ""          # free at https://core.ac.uk/services/api\n'
        '# semantic_scholar_key = ""  # free at https://www.semanticscholar.org/product/api\n'
        '# elsevier_api_key = ""      # optional, paid\n'
        '# wiley_api_key = ""         # optional, paid\n',
        encoding="utf-8",
    )
    return path


__all__ = ["ApiKeys", "get_api_keys", "global_config_path", "write_global_config_template"]
