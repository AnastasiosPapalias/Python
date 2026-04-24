"""Tests for Stage 7 — beginner onboarding wizard.

The wizard is pure: it reads from a given text stream and writes to another.
Tests drive it with StringIO, so there is no real TTY interaction.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scholarforge.app.onboarding import (
    WizardAnswers, run_wizard, FIELDS, KINDS, RECENCY, TRUST, LANGUAGES,
)
from scholarforge.projects.workspace import Project


ROOT = Path(__file__).resolve().parents[1]
SF = [sys.executable, str(ROOT / "scholarforge.py"), "--no-banner"]


class AnswersTests(unittest.TestCase):
    def test_defaults(self) -> None:
        a = WizardAnswers()
        self.assertEqual(a.languages, ["en"])
        self.assertEqual(a.project_kind, "exploration")
        self.assertEqual(a.trust_floor, "any")

    def test_to_project_kwargs_round_trip(self) -> None:
        a = WizardAnswers(
            name="neuro-pain", research_goal="pain neuroplasticity",
            research_field="life", project_kind="thesis",
            recency="5y", trust_floor="peer_reviewed", languages=["en", "gr"],
        )
        kw = a.to_project_kwargs()
        self.assertEqual(kw["name"], "neuro-pain")
        self.assertEqual(kw["research_field"], "life")
        self.assertEqual(kw["languages"], ["en", "gr"])
        # Must accept Project.create signature exactly.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "p"
            p = Project.create(root=root, **kw)
            self.assertEqual(p.config.research_field, "life")
            self.assertEqual(p.config.trust_floor, "peer_reviewed")
            self.assertEqual(p.config.recency, "5y")
            self.assertEqual(p.config.languages, ["en", "gr"])

    def test_summary_lines_render(self) -> None:
        a = WizardAnswers(name="x", research_goal="g", research_field="life",
                          project_kind="thesis", recency="5y",
                          trust_floor="peer_reviewed", languages=["en"])
        s = "\n".join(a.summary_lines())
        self.assertIn("Life sciences", s)
        self.assertIn("thesis", s.lower())
        self.assertIn("Peer-reviewed only", s)


def _drive(answers_lines: list[str], default_name: str = "") -> tuple[WizardAnswers | None, str]:
    stdin = io.StringIO("\n".join(answers_lines) + "\n")
    stdout = io.StringIO()
    result = run_wizard(stdin, stdout, default_name=default_name, show_welcome=False)
    return result, stdout.getvalue()


class WizardFlowTests(unittest.TestCase):
    def test_all_defaults_accepted_by_blank_lines(self) -> None:
        # 7 questions + 1 confirm.
        ans, _ = _drive([""] * 8, default_name="my-proj")
        self.assertIsNotNone(ans)
        assert ans is not None
        self.assertEqual(ans.name, "my-proj")
        self.assertEqual(ans.project_kind, "exploration")
        self.assertEqual(ans.research_field, "interdisciplinary")
        self.assertEqual(ans.trust_floor, "any")
        self.assertEqual(ans.languages, ["en"])

    def test_picks_life_science_thesis_english(self) -> None:
        # name, goal, field=3 (life), kind=1 (thesis), recency=default (5y for thesis),
        # trust=default (peer_reviewed for thesis), languages=1 (en), confirm.
        ans, out = _drive([
            "pain-study",
            "chronic pain neuroplasticity in adolescents",
            "3", "1", "", "", "1", "",
        ])
        self.assertIsNotNone(ans)
        assert ans is not None
        self.assertEqual(ans.name, "pain-study")
        self.assertEqual(ans.research_field, "life")
        self.assertEqual(ans.project_kind, "thesis")
        self.assertEqual(ans.recency, "5y")
        self.assertEqual(ans.trust_floor, "peer_reviewed")
        self.assertEqual(ans.languages, ["en"])
        self.assertIn("Here's what I'll set up", out)

    def test_other_language_branch(self) -> None:
        # defaults until language=6 (other), then custom codes, then confirm.
        ans, _ = _drive([
            "x", "", "", "", "", "",
            str(len(LANGUAGES)),  # "other"
            "en, gr, la",
            "",
        ])
        self.assertIsNotNone(ans)
        assert ans is not None
        self.assertEqual(ans.languages, ["en", "gr", "la"])

    def test_invalid_menu_choice_reprompts(self) -> None:
        # On field question, send "99" then "2" (social).
        ans, out = _drive([
            "x", "",
            "99", "2",          # field: reject 99, accept 2
            "", "", "", "", "",
        ])
        self.assertIsNotNone(ans)
        assert ans is not None
        self.assertEqual(ans.research_field, "social")
        self.assertIn("please type a number", out)

    def test_user_declines_confirmation(self) -> None:
        # All defaults, then "n" on confirm.
        ans, out = _drive([""] * 7 + ["n"])
        self.assertIsNone(ans)
        self.assertIn("Cancelled", out)


class CLIWizardIntegrationTests(unittest.TestCase):
    """`scholarforge new` end-to-end with piped stdin, exercising the CLI wiring."""

    def test_skip_wizard_uses_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            result = subprocess.run(
                SF + ["new", "--skip-wizard",
                      "--name", "fast", "--kind", "article",
                      "--field", "life", "--recency", "10y",
                      "--trust-floor", "peer_or_preprint",
                      "--languages", "en,gr",
                      str(target)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((target / "project.toml").exists())
            p = Project.load(target)
            self.assertEqual(p.config.project_kind, "article")
            self.assertEqual(p.config.research_field, "life")
            self.assertEqual(p.config.recency, "10y")
            self.assertEqual(p.config.trust_floor, "peer_or_preprint")
            self.assertEqual(p.config.languages, ["en", "gr"])

    def test_wizard_flag_forces_wizard_with_piped_stdin(self) -> None:
        # --wizard forces wizard even when stdin is a pipe (not a TTY).
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "wiz"
            # name, goal, field=3(life), kind=1(thesis), recency default(5y),
            # trust default(peer_reviewed), languages default(en), confirm.
            stdin_text = "\n".join([
                "beta-biology", "photosynthesis in low-light mosses",
                "3", "1", "", "", "1", "",
            ]) + "\n"
            result = subprocess.run(
                SF + ["new", "--wizard", str(target)],
                input=stdin_text, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            p = Project.load(target)
            self.assertEqual(p.config.name, "beta-biology")
            self.assertEqual(p.config.project_kind, "thesis")
            self.assertEqual(p.config.research_field, "life")
            self.assertEqual(p.config.trust_floor, "peer_reviewed")
            self.assertEqual(p.config.recency, "5y")
            self.assertIn("Here's what I'll set up", result.stdout)

    def test_wizard_cancelled_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "cancel"
            stdin_text = "\n".join([""] * 7 + ["n"]) + "\n"
            result = subprocess.run(
                SF + ["new", "--wizard", str(target)],
                input=stdin_text, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((target / "project.toml").exists())
            self.assertIn("Cancelled", result.stdout)


if __name__ == "__main__":
    unittest.main()
