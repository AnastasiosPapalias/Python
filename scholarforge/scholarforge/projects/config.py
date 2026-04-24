"""project.toml load/save.

Minimal stdlib-only implementation. Reads via `tomllib` on 3.11+ with a
hand-rolled fallback for 3.8-3.10. Writes via a small serializer (we only
emit a fixed schema so we don't need a full TOML writer).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List

try:
    import tomllib  # Python 3.11+
    _HAS_TOMLLIB = True
except Exception:
    _HAS_TOMLLIB = False


@dataclass
class ProjectConfig:
    name: str = ""
    research_goal: str = ""
    project_kind: str = "exploration"   # thesis | article | book | exploration
    research_field: str = ""            # humanities | social | life | physical | cs | interdisciplinary
    recency: str = "any"                # 5y | 10y | any
    trust_floor: str = "any"            # peer_reviewed | peer_or_preprint | any
    languages: List[str] = field(default_factory=lambda: ["en"])
    created_at: str = ""
    last_search: str = ""
    last_search_classification: str = ""
    last_search_at: str = ""
    searches_run: int = 0
    imports_run: int = 0
    builds_run: int = 0
    exports_run: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────────────────────────────────────

def load_config(path: Path) -> ProjectConfig:
    text = Path(path).read_text(encoding="utf-8")
    data = _parse_toml(text)
    return _dict_to_config(data)


def _parse_toml(text: str) -> Dict[str, Any]:
    if _HAS_TOMLLIB:
        return tomllib.loads(text)
    return _simple_toml_loads(text)


def _dict_to_config(data: Dict[str, Any]) -> ProjectConfig:
    p = data.get("project") if isinstance(data.get("project"), dict) else data
    return ProjectConfig(
        name=str(p.get("name", "")),
        research_goal=str(p.get("research_goal", "")),
        project_kind=str(p.get("project_kind", "exploration")),
        research_field=str(p.get("research_field", "")),
        recency=str(p.get("recency", "any")),
        trust_floor=str(p.get("trust_floor", "any")),
        languages=list(p.get("languages") or ["en"]),
        created_at=str(p.get("created_at", "")),
        last_search=str(p.get("last_search", "")),
        last_search_classification=str(p.get("last_search_classification", "")),
        last_search_at=str(p.get("last_search_at", "")),
        searches_run=int(p.get("searches_run", 0) or 0),
        imports_run=int(p.get("imports_run", 0) or 0),
        builds_run=int(p.get("builds_run", 0) or 0),
        exports_run=int(p.get("exports_run", 0) or 0),
    )


# Very small TOML subset — only what we emit ourselves.
_TOML_LINE = re.compile(r"^\s*([A-Za-z_][\w\-]*)\s*=\s*(.+?)\s*$")


def _simple_toml_loads(text: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"project": {}}
    section = "project"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            out.setdefault(section, {})
            continue
        m = _TOML_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        out[section][key] = _parse_toml_value(value)
    return out


def _parse_toml_value(v: str) -> Any:
    v = v.strip()
    if v.startswith('"') and v.endswith('"'):
        return bytes(v[1:-1], "utf-8").decode("unicode_escape")
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        items = []
        # split on top-level commas
        buf = ""
        in_str = False
        for ch in inner:
            if ch == '"':
                in_str = not in_str
                buf += ch
            elif ch == "," and not in_str:
                items.append(_parse_toml_value(buf.strip()))
                buf = ""
            else:
                buf += ch
        if buf.strip():
            items.append(_parse_toml_value(buf.strip()))
        return items
    if v in ("true", "false"):
        return v == "true"
    try:
        if "." not in v:
            return int(v)
        return float(v)
    except ValueError:
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Writer
# ─────────────────────────────────────────────────────────────────────────────

def save_config(path: Path, cfg: ProjectConfig) -> None:
    lines = [
        "# ScholarForge project configuration",
        "# Edit by hand if you like — this is just TOML.",
        "",
        "[project]",
    ]
    for k, v in asdict(cfg).items():
        lines.append(f"{k} = {_emit_toml_value(v)}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _emit_toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_emit_toml_value(x) for x in v) + "]"
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


__all__ = ["ProjectConfig", "load_config", "save_config"]
