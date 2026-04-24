"""Command-line entry point.

New in Stage 4:
  scholarforge new              — create a project workspace
  scholarforge search           — title / question / keyword search → query plan → harvest
  scholarforge import DIR       — pull documents from a folder into the project corpus
  scholarforge build            — run the forge stage over the project corpus
  scholarforge review-project   — terminal report of project state

Legacy verbs (harvest / forge / pipeline) continue to work via the legacy
monolith and print a deprecation hint.

The dispatcher is a thin custom argument parser so we don't conflict with the
legacy argparse invoked by the monolith.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import scholarforge as _pkg


NEW_VERBS = {"new", "search", "import", "build", "review-project", "review_project", "export", "config", "premium"}

# Global flags that can precede a new verb without breaking dispatch.
# These mirror the legacy top-level flags so invocations like
#   scholarforge.py --no-banner --no-color new --name foo
# still land in the new-verb handler rather than legacy argparse.
_PASSTHROUGH_FLAGS = {"--no-banner", "--no-color", "--verbose", "-v"}


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Skip leading passthrough flags to find the first positional. If it's a
    # new verb, dispatch here; otherwise hand off to the legacy CLI so flags
    # like --help / --version / --deps / --explain / --no-banner keep working.
    i = 0
    while i < len(argv) and argv[i] in _PASSTHROUGH_FLAGS:
        i += 1
    if i < len(argv) and argv[i] in NEW_VERBS:
        leading = argv[:i]
        verb = argv[i].replace("-", "_")
        rest = argv[i + 1:]
        # Apply leading flags that the new handlers care about.
        if "--no-color" in leading:
            import os
            os.environ["NO_COLOR"] = "1"
        handler = {
            "new": _cmd_new,
            "search": _cmd_search,
            "import": _cmd_import,
            "build": _cmd_build,
            "review_project": _cmd_review,
            "export": _cmd_export,
            "config": _cmd_config,
            "premium": _cmd_premium,
        }[verb]
        return handler(rest)

    # Legacy path (harvest / forge / pipeline / --help / --version / --deps /
    # --explain / interactive menu).
    from scholarforge._legacy import main as legacy_main
    return legacy_main()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _pop_option(argv: List[str], *names: str, default: Optional[str] = None) -> Optional[str]:
    """Remove `--name value` (or `-n value`) from argv and return value."""
    for n in names:
        if n in argv:
            i = argv.index(n)
            if i + 1 < len(argv):
                val = argv[i + 1]
                del argv[i:i + 2]
                return val
    return default


def _pop_flag(argv: List[str], *names: str) -> bool:
    for n in names:
        if n in argv:
            argv.remove(n)
            return True
    return False


def _resolve_project(argv: List[str]) -> "Project":
    from scholarforge.projects.workspace import Project
    path = _pop_option(argv, "--project", "-p")
    target = Path(path).expanduser().resolve() if path else Path.cwd()
    # Walk up to find a project
    for p in [target, *target.parents]:
        if Project.is_project(p):
            return Project.load(p)
    raise SystemExit(
        "error: no ScholarForge project found. Run `scholarforge new` first."
    )


# ─────────────────────────────────────────────────────────────────────────────
# new
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_new(argv: List[str]) -> int:
    from scholarforge.projects.workspace import Project

    force_wizard = _pop_flag(argv, "--wizard", "-w")
    skip_wizard = _pop_flag(argv, "--skip-wizard", "--no-wizard")

    name = _pop_option(argv, "--name", "-n")
    goal = _pop_option(argv, "--goal", "-g", default="")
    kind = _pop_option(argv, "--kind", "-k", default="exploration")
    langs = _pop_option(argv, "--languages", "-l", default="en")
    field = _pop_option(argv, "--field", default="")
    recency = _pop_option(argv, "--recency", default="any")
    trust_floor = _pop_option(argv, "--trust-floor", default="any")

    path_str = argv[0] if argv else "."
    root = Path(path_str).expanduser().resolve()

    # Wizard decision: explicit --wizard wins, --skip-wizard wins against auto.
    # Otherwise, launch the wizard when no power-user flags were supplied AND
    # stdin is a TTY (interactive). This keeps `scholarforge new` beginner-
    # friendly while preserving scriptability.
    no_flag_path = (
        name is None and not goal and kind == "exploration"
        and langs == "en" and not field
        and recency == "any" and trust_floor == "any"
    )
    want_wizard = force_wizard or (not skip_wizard and no_flag_path and sys.stdin.isatty())

    if want_wizard:
        from scholarforge.app.onboarding import run_wizard
        answers = run_wizard(sys.stdin, sys.stdout, default_name=root.name)
        if answers is None:
            return 1
        try:
            project = Project.create(root=root, **answers.to_project_kwargs())
        except FileExistsError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    else:
        if not name:
            name = root.name
        try:
            project = Project.create(
                root=root,
                name=name,
                research_goal=goal or "",
                project_kind=kind,
                languages=[s.strip() for s in langs.split(",") if s.strip()],
                research_field=field or "",
                recency=recency,
                trust_floor=trust_floor,
            )
        except FileExistsError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    print(f"created project '{project.config.name}' at {project.root}")
    for sub in ("sources", "downloads", "corpus", "reports", "exports"):
        print(f"  {sub}/")
    print(f"  project.toml")
    print()
    print("next:")
    print(f"  scholarforge search --project \"{project.root}\" \"<title or question>\"")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# search
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_search(argv: List[str]) -> int:
    from scholarforge.search.query_expansion import expand

    include_multilingual = _pop_flag(argv, "--multilingual")
    include_recency = _pop_flag(argv, "--recent")
    no_review = _pop_flag(argv, "--no-review")
    dry_run = _pop_flag(argv, "--dry-run")
    max_results = int(_pop_option(argv, "--max-results", default="25") or 25)
    min_score = float(_pop_option(argv, "--min-score", default="10") or 10)
    skip_download = _pop_flag(argv, "--no-download")

    project = _resolve_project(argv)
    raw = " ".join(argv).strip()
    if not raw:
        print("error: provide a title, question, or keyword list", file=sys.stderr)
        return 1

    plan = expand(
        raw,
        include_review=not no_review,
        include_recency=include_recency,
        include_multilingual=include_multilingual,
    )
    print(plan.pretty())

    project.record_search(raw, plan.classification, len(plan.queries))

    if dry_run:
        print("\n--dry-run: not executing harvest")
        return 0

    # Hand off to the legacy harvest runner. We pass the expanded subjects
    # string so the existing 20-source pipeline does the actual network work.
    from scholarforge._legacy import run_harvest, _print_harvest_final
    subjects = plan.as_subject_strings()
    print(f"\nrunning harvest with {len(subjects)} subject(s): {subjects}")
    result = run_harvest(
        subjects=subjects,
        output_dir=project.root,
        max_results=max_results,
        min_score=min_score,
        max_downloads=100,
        skip_download=skip_download,
        verbose=False,
    )
    _print_harvest_final(result)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# import
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_import(argv: List[str]) -> int:
    import shutil
    project = _resolve_project(argv)
    if not argv:
        print("error: specify a source directory to import", file=sys.stderr)
        return 1
    src = Path(argv[0]).expanduser().resolve()
    if not src.exists():
        print(f"error: {src} does not exist", file=sys.stderr)
        return 1

    dst = project.corpus_dir
    dst.mkdir(exist_ok=True)
    copied = 0
    if src.is_file():
        shutil.copy2(src, dst / src.name)
        copied = 1
    else:
        for f in src.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src)
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
                copied += 1

    project.config.imports_run += 1
    project.save()
    print(f"imported {copied} file(s) into {dst}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# build
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_build(argv: List[str]) -> int:
    from scholarforge._legacy import run_forge, _print_forge_final, CHUNK_SIZE_DEFAULT, CHUNK_OVERLAP_DEFAULT
    project = _resolve_project(argv)
    chunk_size = int(_pop_option(argv, "--chunk-size", default=str(CHUNK_SIZE_DEFAULT)))
    overlap = int(_pop_option(argv, "--overlap", default=str(CHUNK_OVERLAP_DEFAULT)))

    # Build runs over corpus/ and downloads/ combined — we pass corpus_dir;
    # users can re-run with --source downloads if they want that subset only.
    source = _pop_option(argv, "--source", default="all")
    if source == "corpus":
        src = project.corpus_dir
    elif source == "downloads":
        src = project.downloads_dir
    else:
        src = project.root  # scans both plus exports/, filtered by iter_files

    out = project.exports_dir / "knowledge_export"
    summary = run_forge(
        source_dir=src,
        output_dir=out,
        chunk_size=chunk_size,
        overlap=overlap,
        include_extensions=None,
        include_hidden=False,
        verbose=False,
    )
    project.config.builds_run += 1
    project.save()
    _print_forge_final(summary, out)
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# review-project
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_review(argv: List[str]) -> int:
    from scholarforge.projects.report import build_report
    project = _resolve_project(argv)
    print(build_report(project))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# export  (Stage 6 — provenance-aware exports)
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_export(argv: List[str]) -> int:
    """scholarforge export --format bibtex|csljson|markdown [--input PATH] [-o OUT]

    With `--project` (default cwd), reads the project's harvested records and
    writes the export under `exports/`. With `--input`, reads any JSONL file.
    """
    from scholarforge.exports import find_project_records, load_records

    fmt = (_pop_option(argv, "--format", "-f", default="bibtex") or "bibtex").lower()
    output = _pop_option(argv, "--output", "-o")
    input_path = _pop_option(argv, "--input", "-i")
    title = _pop_option(argv, "--title", default="Bibliography")

    if fmt not in {"bibtex", "csljson", "markdown"}:
        print(f"error: unknown format '{fmt}' (choose bibtex / csljson / markdown)",
              file=sys.stderr)
        return 2

    if input_path:
        records_path = Path(input_path).expanduser().resolve()
        if not records_path.exists():
            print(f"error: {records_path} does not exist", file=sys.stderr)
            return 1
        project = None
        default_out_dir = Path.cwd()
    else:
        project = _resolve_project(argv)
        records_path = find_project_records(project.root)
        if records_path is None:
            print("error: no harvest records found. Run `scholarforge search` first.",
                  file=sys.stderr)
            return 1
        default_out_dir = project.exports_dir

    records = load_records(records_path)
    if not records:
        print(f"error: no records in {records_path}", file=sys.stderr)
        return 1

    ext = {"bibtex": "bib", "csljson": "json", "markdown": "md"}[fmt]
    out_path = Path(output).expanduser().resolve() if output else default_out_dir / f"bibliography.{ext}"

    if fmt == "bibtex":
        from scholarforge.exports import bibtex
        count = bibtex.write(records, out_path)
    elif fmt == "csljson":
        from scholarforge.exports import csljson
        count = csljson.write(records, out_path)
    else:
        from scholarforge.exports import markdown as md_export
        count = md_export.write(records, out_path, title=title)

    print(f"wrote {count} record(s) to {out_path}")
    if project is not None:
        project.config.exports_run = getattr(project.config, "exports_run", 0) + 1
        project.save()
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# config  (global API key inspection + template creation)
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_config(argv: List[str]) -> int:
    """scholarforge config [--init]

    Without flags: show which API keys are currently loaded and where they
    came from (env var / ~/.scholarforge.toml / .env).

    With --init: create a commented ~/.scholarforge.toml template if one
    does not already exist.
    """
    from scholarforge.config.global_config import (
        get_api_keys, global_config_path, write_global_config_template,
        _ENV_MAP,
    )

    init = _pop_flag(argv, "--init")

    if init:
        path = write_global_config_template()
        if path.exists():
            print(f"config file ready at: {path}")
            print("Open it in a text editor and fill in your API keys.")
        return 0

    keys = get_api_keys()
    cfg_path = global_config_path()

    print("ScholarForge — API key configuration")
    print(f"  global config : {cfg_path} {'(exists)' if cfg_path.exists() else '(not found)'}")
    print()

    _LABELS = {
        "core_api_key":         ("CORE",             "https://core.ac.uk/services/api"),
        "semantic_scholar_key": ("Semantic Scholar",  "https://www.semanticscholar.org/product/api"),
        "elsevier_api_key":     ("Elsevier TDM",      "https://dev.elsevier.com/"),
        "wiley_api_key":        ("Wiley TDM",         "https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining"),
    }

    import os
    from scholarforge.config.global_config import _ENV_ALIASES, _load_global_toml, _find_dotenv, _load_dotenv
    toml_vals = _load_global_toml()
    dotenv_path = _find_dotenv()
    dotenv_vals = _load_dotenv(dotenv_path) if dotenv_path else {}

    any_key = False
    for field_name, (label, signup_url) in _LABELS.items():
        value = getattr(keys, field_name)
        env_name = _ENV_MAP.get(field_name, "")
        if value:
            any_key = True
            # Determine source
            if os.environ.get(env_name) or any(os.environ.get(a) for a in _ENV_ALIASES.get(field_name, [])):
                source = "environment variable"
            elif field_name in toml_vals:
                source = f"~/.scholarforge.toml"
            else:
                source = f".env ({dotenv_path})"
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"  {label:<20} {masked}  (from {source})")
        else:
            print(f"  {label:<20} not set   (sign up: {signup_url})")

    print()
    if not any_key:
        print("No API keys configured. ScholarForge works without them,")
        print("but keys improve rate limits and result quality.")
        print()
        print("To add keys, run:")
        print("  scholarforge config --init")
        print("Then edit ~/.scholarforge.toml")
    else:
        print("Keys marked 'not set' are optional — ScholarForge works without them.")

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# premium  (Stage 8 — activation status + seam listing)
# ─────────────────────────────────────────────────────────────────────────────

_PREMIUM_FEATURES = [
    ("atlas",          "Citation / co-citation graph over your corpus"),
    ("clusters",       "Topic clustering across harvested records"),
    ("contradictions", "Claim-conflict detection between sources"),
    ("thesis-pack",    "Thesis scaffold export (chapters + literature matrix)"),
    ("book-pack",      "Book scaffold export (front matter + chapters + bib)"),
    ("memory-graph",   "Persistent cross-project research graph"),
]


def _cmd_premium(argv: List[str]) -> int:
    """scholarforge premium [--status | --features]

    Show activation status and the list of premium seams. All entry points
    raise PremiumNotAvailableError when called without activation.
    """
    from scholarforge import premium as _premium

    status = _premium.get_status()
    show_features = _pop_flag(argv, "--features", "-l") or not argv

    print("ScholarForge — Premium")
    if status.active:
        src = {"env": "environment variable",
               "config": "~/.scholarforge.toml",
               "unlock": "test unlock flag"}.get(status.source, status.source)
        print(f"  status : ACTIVE ({status.key_preview}, from {src})")
    else:
        print("  status : inactive")
        print("  activate by setting SCHOLARFORGE_PREMIUM_KEY, or by adding")
        print("  a [premium] license_key = \"...\" block to ~/.scholarforge.toml")

    if show_features:
        print()
        print("Seams:")
        for name, desc in _PREMIUM_FEATURES:
            mark = "✓" if status.active else "·"
            print(f"  {mark} {name:<16} {desc}")

    return 0


__all__ = ["main"]
