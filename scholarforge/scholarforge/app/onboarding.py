"""Stage 7 — beginner onboarding wizard.

A plain-English, numbered-menu wizard that sets research-goal-driven defaults
for a new ScholarForge project. The target user is a scholar with little or
no Linux / Python experience, so:

  * every question has a sane default shown in brackets — Enter accepts it
  * options are numbered, not typed-out keywords
  * no jargon (say "peer-reviewed journal articles", not "openalex+crossref")
  * the wizard is pure logic: it reads from any text stream, writes to any
    text stream, so tests can drive it with StringIO

The wizard never touches the filesystem. `_cmd_new` in `app/cli.py` turns the
answers into `Project.create(**answers.to_project_kwargs())`.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, TextIO


# ─────────────────────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────────────────────

FIELDS: List[tuple[str, str]] = [
    ("humanities",       "Humanities (history, classics, philosophy, literature)"),
    ("social",           "Social sciences (psychology, sociology, economics, education)"),
    ("life",             "Life sciences (biology, medicine, ecology, neuroscience)"),
    ("physical",         "Physical sciences (physics, chemistry, earth sciences)"),
    ("cs",               "Computer science / engineering"),
    ("interdisciplinary","Interdisciplinary / not sure yet"),
]

KINDS: List[tuple[str, str]] = [
    ("thesis",      "A thesis or dissertation"),
    ("article",     "A journal article or conference paper"),
    ("book",        "A book or book chapter"),
    ("exploration", "Just exploring the topic"),
]

RECENCY: List[tuple[str, str]] = [
    ("5y",  "Last 5 years"),
    ("10y", "Last 10 years"),
    ("any", "Any year"),
]

TRUST: List[tuple[str, str]] = [
    ("peer_reviewed",     "Peer-reviewed only (strictest)"),
    ("peer_or_preprint",  "Peer-reviewed + preprints"),
    ("any",               "Anything (books, theses, reports, datasets too)"),
]

LANGUAGES: List[tuple[str, str]] = [
    ("en",      "English"),
    ("en,gr",   "English + Greek"),
    ("en,fr",   "English + French"),
    ("en,de",   "English + German"),
    ("en,es",   "English + Spanish"),
    ("other",   "Something else (type codes)"),
]

# Default index per writing target → trust floor.
_TRUST_DEFAULT_BY_KIND = {
    "thesis":      "peer_reviewed",
    "article":     "peer_reviewed",
    "book":        "peer_or_preprint",
    "exploration": "any",
}


# ─────────────────────────────────────────────────────────────────────────────
# Answers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WizardAnswers:
    name: str = ""
    research_goal: str = ""
    research_field: str = "interdisciplinary"
    project_kind: str = "exploration"
    recency: str = "any"
    trust_floor: str = "any"
    languages: List[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.languages is None:
            self.languages = ["en"]

    def to_project_kwargs(self) -> Dict[str, Any]:
        """Map answers to `Project.create(**kwargs)` keyword arguments."""
        return {
            "name": self.name,
            "research_goal": self.research_goal,
            "project_kind": self.project_kind,
            "languages": list(self.languages),
            "research_field": self.research_field,
            "recency": self.recency,
            "trust_floor": self.trust_floor,
        }

    def summary_lines(self) -> List[str]:
        pretty_kind = dict(KINDS).get(self.project_kind, self.project_kind)
        pretty_field = dict(FIELDS).get(self.research_field, self.research_field)
        pretty_recency = dict(RECENCY).get(self.recency, self.recency)
        pretty_trust = dict(TRUST).get(self.trust_floor, self.trust_floor)
        return [
            f"  name           : {self.name}",
            f"  research goal  : {self.research_goal or '(none)'}",
            f"  field          : {pretty_field}",
            f"  writing target : {pretty_kind}",
            f"  recency        : {pretty_recency}",
            f"  trust floor    : {pretty_trust}",
            f"  languages      : {', '.join(self.languages)}",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Prompt helpers (pure, stream-driven)
# ─────────────────────────────────────────────────────────────────────────────

def _ask(stdin: TextIO, stdout: TextIO, prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    stdout.write(f"{prompt}{hint}: ")
    stdout.flush()
    line = stdin.readline()
    if not line:
        return default
    value = line.rstrip("\r\n").strip()
    return value or default


def _ask_menu(stdin: TextIO, stdout: TextIO, prompt: str,
              options: List[tuple[str, str]], default_key: str) -> str:
    default_idx = next((i for i, (k, _) in enumerate(options) if k == default_key), 0)
    stdout.write(f"{prompt}\n")
    for i, (_, label) in enumerate(options, start=1):
        marker = " *" if (i - 1) == default_idx else "  "
        stdout.write(f"  {i}.{marker} {label}\n")
    while True:
        raw = _ask(stdin, stdout, "choose", default=str(default_idx + 1))
        try:
            n = int(raw)
        except ValueError:
            stdout.write(f"  (please type a number 1–{len(options)})\n")
            continue
        if 1 <= n <= len(options):
            return options[n - 1][0]
        stdout.write(f"  (please type a number 1–{len(options)})\n")


def _ask_yes_no(stdin: TextIO, stdout: TextIO, prompt: str, default: bool) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        raw = _ask(stdin, stdout, f"{prompt} [{d}]").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Wizard
# ─────────────────────────────────────────────────────────────────────────────

WELCOME = (
    "\n"
    "Welcome — let's set up your research project.\n"
    "Press Enter to accept the default in [brackets].\n"
    "You can change any of this later by editing project.toml.\n"
    "\n"
)


def run_wizard(
    stdin: TextIO,
    stdout: TextIO,
    default_name: str = "",
    show_welcome: bool = True,
) -> Optional[WizardAnswers]:
    """Run the interactive wizard. Return answers, or None if the user aborts."""
    if show_welcome:
        stdout.write(WELCOME)

    # 1. Name
    name = _ask(stdin, stdout, "Project name (a short handle, no spaces)",
                default=default_name or "my-research")

    # 2. Research goal
    goal = _ask(stdin, stdout,
                "In one sentence, what are you researching?",
                default="")

    # 3. Field
    field = _ask_menu(stdin, stdout,
                      "Which field best describes this work?",
                      FIELDS, default_key="interdisciplinary")

    # 4. Writing target
    kind = _ask_menu(stdin, stdout,
                     "What will you write from this research?",
                     KINDS, default_key="exploration")

    # 5. Recency
    recency = _ask_menu(stdin, stdout,
                        "How recent should the sources be?",
                        RECENCY,
                        default_key=("5y" if kind in ("thesis", "article") else "any"))

    # 6. Trust floor — default driven by writing target
    trust_default = _TRUST_DEFAULT_BY_KIND.get(kind, "any")
    trust = _ask_menu(stdin, stdout,
                      "How strict should the trust filter be?",
                      TRUST, default_key=trust_default)

    # 7. Languages
    lang_key = _ask_menu(stdin, stdout,
                         "What languages should sources be in?",
                         LANGUAGES, default_key="en")
    if lang_key == "other":
        raw = _ask(stdin, stdout,
                   "Type language codes separated by commas (e.g. en,gr,fr)",
                   default="en")
        languages = [c.strip() for c in raw.split(",") if c.strip()] or ["en"]
    else:
        languages = [c.strip() for c in lang_key.split(",") if c.strip()]

    answers = WizardAnswers(
        name=name,
        research_goal=goal,
        research_field=field,
        project_kind=kind,
        recency=recency,
        trust_floor=trust,
        languages=languages,
    )

    stdout.write("\nHere's what I'll set up:\n")
    for line in answers.summary_lines():
        stdout.write(line + "\n")
    stdout.write("\n")

    if not _ask_yes_no(stdin, stdout, "Create the project with these settings?", default=True):
        stdout.write("Cancelled. Nothing was created.\n")
        return None

    return answers


__all__ = [
    "WizardAnswers",
    "run_wizard",
    "FIELDS", "KINDS", "RECENCY", "TRUST", "LANGUAGES",
]
