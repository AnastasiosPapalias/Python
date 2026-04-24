"""`scholarforge review-project` — a terminal report of project state."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List

from scholarforge.projects.workspace import Project


def build_report(project: Project) -> str:
    cfg = project.config
    lines: List[str] = []
    w = 76
    sep = "─" * w
    lines.append(sep)
    lines.append(f"  PROJECT REVIEW — {cfg.name}")
    lines.append(sep)
    lines.append(f"  Kind:            {cfg.project_kind}")
    if cfg.research_goal:
        lines.append(f"  Research goal:   {cfg.research_goal}")
    lines.append(f"  Languages:       {', '.join(cfg.languages) or '—'}")
    lines.append(f"  Created:         {cfg.created_at or '—'}")
    lines.append(f"  Last search:     {cfg.last_search or '—'}")
    if cfg.last_search_at:
        lines.append(f"  Last search at:  {cfg.last_search_at}")
    lines.append(f"  Searches run:    {cfg.searches_run}")
    lines.append(f"  Imports run:     {cfg.imports_run}")
    lines.append(f"  Builds run:      {cfg.builds_run}")
    lines.append("")

    counts = _corpus_counts(project)
    lines.append("  CORPUS")
    lines.append(f"    downloads/ files : {counts['downloads']}")
    lines.append(f"    corpus/    files : {counts['corpus']}")
    lines.append(f"    exports/   files : {counts['exports']}")
    lines.append(f"    reports/   files : {counts['reports']}")
    lines.append("")

    ext = _extensions(project)
    if ext:
        lines.append("  FILE TYPES")
        for name, n in ext.most_common(8):
            lines.append(f"    {name:<12} {n}")
    lines.append(sep)
    return "\n".join(lines)


def _corpus_counts(project: Project) -> Dict[str, int]:
    return {
        "downloads": _count_files(project.downloads_dir),
        "corpus":    _count_files(project.corpus_dir),
        "exports":   _count_files(project.exports_dir),
        "reports":   _count_files(project.reports_dir),
    }


def _count_files(p: Path) -> int:
    if not p.exists():
        return 0
    return sum(1 for _ in p.rglob("*") if _.is_file())


def _extensions(project: Project) -> Counter:
    c: Counter = Counter()
    for base in (project.downloads_dir, project.corpus_dir):
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.is_file():
                c[f.suffix.lower() or "(no ext)"] += 1
    return c


__all__ = ["build_report"]
