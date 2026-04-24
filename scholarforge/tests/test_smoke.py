"""Smoke tests — Stage 1 must never regress these.

Works with either pytest or `python -m unittest discover tests`.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def test_package_imports(self):
        import scholarforge
        self.assertTrue(scholarforge.__version__)
        from scholarforge.app.cli import main
        self.assertTrue(callable(main))

    def test_version_flag_matches_package(self):
        import scholarforge
        result = subprocess.run(
            [sys.executable, str(ROOT / "scholarforge.py"), "--no-banner", "--version"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(scholarforge.__version__, result.stdout)

    def test_deps_flag_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scholarforge.py"), "--no-banner", "--deps"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0)

    def test_python_m_scholarforge(self):
        result = subprocess.run(
            [sys.executable, "-m", "scholarforge", "--no-banner", "--version"],
            capture_output=True, text=True, timeout=15,
            cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
