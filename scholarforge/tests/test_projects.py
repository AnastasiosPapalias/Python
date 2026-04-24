"""Tests for project workspace + new CLI verbs."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SF = [sys.executable, str(ROOT / "scholarforge.py"), "--no-banner"]


class ProjectWorkspaceTests(unittest.TestCase):
    def test_create_and_load(self):
        from scholarforge.projects.workspace import Project
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "my_research"
            p = Project.create(root, name="My Research",
                               research_goal="explore X",
                               project_kind="thesis",
                               languages=["en", "gr"])
            self.assertTrue((root / "project.toml").exists())
            for sub in ("sources", "downloads", "corpus", "reports", "exports"):
                self.assertTrue((root / sub).is_dir(), sub)

            p2 = Project.load(root)
            self.assertEqual(p2.config.name, "My Research")
            self.assertEqual(p2.config.project_kind, "thesis")
            self.assertIn("gr", p2.config.languages)

    def test_record_search_increments_counter(self):
        from scholarforge.projects.workspace import Project
        with tempfile.TemporaryDirectory() as tmp:
            p = Project.create(Path(tmp), name="x")
            p.record_search("neuroplasticity", "broad_topic", 3)
            p2 = Project.load(Path(tmp))
            self.assertEqual(p2.config.searches_run, 1)
            self.assertEqual(p2.config.last_search, "neuroplasticity")


class CLIVerbsTests(unittest.TestCase):
    def test_new_creates_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            result = subprocess.run(
                SF + ["new", str(target), "--name", "Proj", "--goal", "test"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "project.toml").exists())

    def test_search_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            subprocess.run(SF + ["new", str(target)], capture_output=True, timeout=15)
            result = subprocess.run(
                SF + ["search", "--project", str(target), "--dry-run",
                      "The neuroplastic brain: current breakthroughs"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("QUERY PLAN", result.stdout)
            self.assertIn("dry-run", result.stdout)

    def test_review_project_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            subprocess.run(SF + ["new", str(target), "--name", "R"],
                           capture_output=True, timeout=15)
            result = subprocess.run(
                SF + ["review-project", "--project", str(target)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROJECT REVIEW", result.stdout)

    def test_import_copies_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "proj"
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "a.txt").write_text("hello")
            (src / "b.md").write_text("# doc")
            subprocess.run(SF + ["new", str(target)],
                           capture_output=True, timeout=15)
            result = subprocess.run(
                SF + ["import", "--project", str(target), str(src)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "corpus" / "a.txt").exists())
            self.assertTrue((target / "corpus" / "b.md").exists())


if __name__ == "__main__":
    unittest.main()
