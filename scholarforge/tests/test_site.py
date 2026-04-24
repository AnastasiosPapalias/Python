"""Stage 9 — static site sanity checks.

Not a design review. This verifies the shipped site is well-formed enough
that a silent breakage (missing file, broken nav link, forgotten page)
surfaces in CI rather than in a reader's browser.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

PAGES = ["index.html", "features.html", "install.html",
         "cli.html", "sources.html", "pricing.html"]


class SitePresenceTests(unittest.TestCase):
    def test_site_dir_exists(self) -> None:
        self.assertTrue(SITE.is_dir(), f"missing site/ at {SITE}")

    def test_all_pages_present(self) -> None:
        missing = [p for p in PAGES if not (SITE / p).is_file()]
        self.assertEqual(missing, [], f"missing pages: {missing}")

    def test_stylesheet_present(self) -> None:
        self.assertTrue((SITE / "style.css").is_file())


class SiteMarkupTests(unittest.TestCase):
    def test_pages_link_to_stylesheet(self) -> None:
        for p in PAGES:
            text = (SITE / p).read_text(encoding="utf-8")
            self.assertIn('href="style.css"', text,
                          f"{p} does not link style.css")

    def test_pages_have_viewport_meta(self) -> None:
        for p in PAGES:
            text = (SITE / p).read_text(encoding="utf-8")
            self.assertIn('name="viewport"', text,
                          f"{p} missing viewport meta")

    def test_nav_links_resolve(self) -> None:
        """Every internal nav href on every page must point to a real file."""
        href_re = re.compile(r'href="([^"#:]+\.html)"')
        errors = []
        for p in PAGES:
            text = (SITE / p).read_text(encoding="utf-8")
            for match in href_re.finditer(text):
                target = match.group(1)
                if not (SITE / target).is_file():
                    errors.append(f"{p} → {target}")
        self.assertEqual(errors, [], f"broken internal links: {errors}")

    def test_index_mentions_core_verbs(self) -> None:
        text = (SITE / "index.html").read_text(encoding="utf-8")
        for verb in ("scholarforge new", "scholarforge search",
                     "scholarforge export"):
            self.assertIn(verb, text, f"index.html missing '{verb}'")

    def test_cli_lists_all_verbs(self) -> None:
        text = (SITE / "cli.html").read_text(encoding="utf-8")
        for verb in ("new", "search", "import", "build",
                     "export", "review-project", "config", "premium"):
            self.assertRegex(text, rf"<h2[^>]*>\s*{verb}\b",
                             f"cli.html missing verb section '{verb}'")

    def test_pricing_covers_freemium_and_premium(self) -> None:
        text = (SITE / "pricing.html").read_text(encoding="utf-8")
        self.assertIn("Freemium", text)
        self.assertIn("Premium", text)

    def test_sources_page_covers_all_twenty(self) -> None:
        text = (SITE / "sources.html").read_text(encoding="utf-8")
        # 20 source names — sanity-check a sample we must not drop.
        for src in ("OpenAlex", "Crossref", "Semantic Scholar",
                    "OA.mg", "CORE", "DOAJ", "Paperity",
                    "arXiv", "SSRN",
                    "PubMed", "PMC Full-Text", "Europe PMC",
                    "Zenodo", "Figshare", "HAL", "OpenAIRE",
                    "Google Books", "Internet Archive", "Open Library",
                    "EThOS"):
            self.assertIn(src, text, f"sources.html missing '{src}'")


if __name__ == "__main__":
    unittest.main()
