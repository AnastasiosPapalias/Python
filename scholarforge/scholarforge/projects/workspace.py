"""A ScholarForge project is a folder with a known layout.

Layout
------
    <project>/
    ├── project.toml        ← name, research_goal, created_at, last_search, settings
    ├── sources/            ← raw API responses + manifests
    ├── downloads/          ← open-access files fetched during harvest
    ├── corpus/             ← documents from `scholarforge import` + processed text
    ├── reports/            ← harvest summaries, review reports, reading queues
    └── exports/            ← BibTeX, CSL-JSON, annotated markdown

Projects are the durable unit of research. Every `harvest`, `import`, and
`build` run appends to the project; the terminal report (`review-project`)
summarises the whole state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from scholarforge.projects.config import ProjectConfig, load_config, save_config

PROJECT_FILE = "project.toml"
SUBDIRS = ("sources", "downloads", "corpus", "reports", "exports")


@dataclass
class Project:
    root: Path
    config: ProjectConfig

    # ── discovery ─────────────────────────────────────────────────────────
    @classmethod
    def load(cls, path: Path) -> "Project":
        path = path.expanduser().resolve()
        if not (path / PROJECT_FILE).exists():
            raise FileNotFoundError(f"no project.toml in {path}")
        return cls(root=path, config=load_config(path / PROJECT_FILE))

    @classmethod
    def is_project(cls, path: Path) -> bool:
        try:
            return (path.expanduser().resolve() / PROJECT_FILE).exists()
        except Exception:
            return False

    # ── creation ──────────────────────────────────────────────────────────
    @classmethod
    def create(
        cls,
        root: Path,
        name: str,
        research_goal: str = "",
        project_kind: str = "exploration",  # thesis | article | book | exploration
        languages: Optional[List[str]] = None,
        research_field: str = "",
        recency: str = "any",
        trust_floor: str = "any",
    ) -> "Project":
        root = root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        for sub in SUBDIRS:
            (root / sub).mkdir(exist_ok=True)

        cfg_path = root / PROJECT_FILE
        if cfg_path.exists():
            raise FileExistsError(f"project already exists at {root}")

        cfg = ProjectConfig(
            name=name or root.name,
            research_goal=research_goal,
            project_kind=project_kind,
            research_field=research_field,
            recency=recency,
            trust_floor=trust_floor,
            languages=list(languages or ["en"]),
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        save_config(cfg_path, cfg)
        return cls(root=root, config=cfg)

    # ── paths ─────────────────────────────────────────────────────────────
    @property
    def sources_dir(self) -> Path: return self.root / "sources"
    @property
    def downloads_dir(self) -> Path: return self.root / "downloads"
    @property
    def corpus_dir(self) -> Path: return self.root / "corpus"
    @property
    def reports_dir(self) -> Path: return self.root / "reports"
    @property
    def exports_dir(self) -> Path: return self.root / "exports"

    # ── state mutation ────────────────────────────────────────────────────
    def record_search(self, raw_input: str, classification: str,
                      query_count: int) -> None:
        self.config.last_search = raw_input
        self.config.last_search_classification = classification
        self.config.last_search_at = datetime.now().isoformat(timespec="seconds")
        self.config.searches_run += 1
        save_config(self.root / PROJECT_FILE, self.config)

    def save(self) -> None:
        save_config(self.root / PROJECT_FILE, self.config)


__all__ = ["Project", "SUBDIRS", "PROJECT_FILE"]
