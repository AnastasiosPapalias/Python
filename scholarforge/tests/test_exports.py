"""Tests for Stage 6 — provenance-aware exports.

Covers the pure export renderers (bibtex, csljson, markdown), trust
augmentation, and the `scholarforge export` CLI verb end-to-end.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scholarforge.exports import augment_with_trust, load_records, find_project_records
from scholarforge.exports import bibtex, csljson, markdown as md_export


ROOT = Path(__file__).resolve().parents[1]
SF = [sys.executable, str(ROOT / "scholarforge.py"), "--no-banner"]


SAMPLE_RECORDS = [
    {
        "source": "openalex",
        "document_type": "journal-article",
        "title": "Neural correlates of memory consolidation",
        "authors": "Jane Doe; Sam Roe",
        "year": "2022",
        "doi": "10.1234/example.22",
        "url": "https://example.org/a",
        "journal": "Journal of Cognitive Neuroscience",
        "abstract": "We study memory consolidation via a longitudinal MRI protocol.",
        "language": "en",
        "source_id": "W1",
        "relevance_score": 42.5,
    },
    {
        "source": "arxiv",
        "document_type": "",
        "title": "A fast transformer for protein folding",
        "authors": "Alice Smith",
        "year": "2024",
        "doi": "",
        "url": "https://arxiv.org/abs/2401.00001",
        "abstract": "",
        "language": "en",
        "source_id": "2401.00001",
        "relevance_score": 30.0,
    },
    {
        "source": "ethesis",
        "document_type": "thesis",
        "title": "A systematic review of pharmacological treatments for OCD",
        "authors": "Bob Brown",
        "year": "2019",
        "doi": "",
        "url": "https://ethos.example/xyz",
        "abstract": "A systematic review of ERP and SSRI trials.",
        "source_id": "ETHOS-1",
    },
]


class AugmentTests(unittest.TestCase):
    def test_adds_trust_labels(self):
        out = augment_with_trust(SAMPLE_RECORDS)
        self.assertEqual(out[0]["trust_label"], "peer_reviewed")
        self.assertEqual(out[1]["trust_label"], "preprint")
        # Systematic-review title overrides the thesis document_type.
        self.assertEqual(out[2]["source_type"], "review")
        self.assertEqual(out[2]["trust_label"], "peer_reviewed")

    def test_preserves_existing_values(self):
        src = [{"source": "arxiv", "trust_label": "custom"}]
        out = augment_with_trust(src)
        self.assertEqual(out[0]["trust_label"], "custom")


class BibtexTests(unittest.TestCase):
    def test_render_all_records(self):
        text = bibtex.render(SAMPLE_RECORDS)
        self.assertIn("@article{", text)
        self.assertIn("@misc{", text)  # arxiv preprint
        # Trust note embedded
        self.assertIn("trust: peer_reviewed", text)
        self.assertIn("trust: preprint", text)
        # Authors joined with " and "
        self.assertIn(" and ", text)

    def test_cite_key_is_deterministic(self):
        a = bibtex.render([SAMPLE_RECORDS[0]])
        b = bibtex.render([SAMPLE_RECORDS[0]])
        self.assertEqual(a, b)

    def test_write_returns_entry_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.bib"
            n = bibtex.write(SAMPLE_RECORDS, out)
            self.assertEqual(n, 3)
            self.assertTrue(out.exists())


class CSLJSONTests(unittest.TestCase):
    def test_render_is_valid_json(self):
        text = csljson.render(SAMPLE_RECORDS)
        data = json.loads(text)
        self.assertEqual(len(data), 3)

    def test_csl_types_and_trust(self):
        items = json.loads(csljson.render(SAMPLE_RECORDS))
        types = [it["type"] for it in items]
        self.assertIn("article-journal", types)
        self.assertIn("article", types)  # preprint / review fallback
        # Every item must carry the custom provenance block.
        for it in items:
            self.assertIn("custom", it)
            self.assertIn("scholarforge", it["custom"])
            self.assertIn("trust_label", it["custom"]["scholarforge"])

    def test_author_parsing(self):
        items = json.loads(csljson.render([SAMPLE_RECORDS[0]]))
        self.assertEqual(len(items[0]["author"]), 2)
        self.assertEqual(items[0]["author"][0], {"family": "Doe", "given": "Jane"})


class MarkdownTests(unittest.TestCase):
    def test_render_groups_by_trust(self):
        text = md_export.render(SAMPLE_RECORDS)
        self.assertIn("# Bibliography", text)
        self.assertIn("peer-reviewed", text)
        self.assertIn("preprint", text)
        # Entry headers
        self.assertIn("### Neural correlates of memory consolidation", text)
        # Summary table
        self.assertIn("| Trust tier | Count |", text)

    def test_write_counts_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bib.md"
            n = md_export.write(SAMPLE_RECORDS, out)
            self.assertEqual(n, 3)


class ExportCLITests(unittest.TestCase):
    def _make_project_with_records(self, tmp: str) -> Path:
        target = Path(tmp) / "proj"
        r = subprocess.run(SF + ["new", str(target), "--name", "T"],
                           capture_output=True, timeout=15, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        # Simulate a harvest by writing metadata/filtered_records.jsonl
        meta = target / "metadata"
        meta.mkdir(exist_ok=True)
        with (meta / "filtered_records.jsonl").open("w", encoding="utf-8") as f:
            for rec in SAMPLE_RECORDS:
                f.write(json.dumps(rec) + "\n")
        return target

    def test_export_bibtex_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_project_with_records(tmp)
            r = subprocess.run(
                SF + ["export", "--project", str(target), "--format", "bibtex"],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            bib = (target / "exports" / "bibliography.bib").read_text(encoding="utf-8")
            self.assertIn("@article{", bib)

    def test_export_csljson_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_project_with_records(tmp)
            r = subprocess.run(
                SF + ["export", "--project", str(target), "--format", "csljson"],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads((target / "exports" / "bibliography.json").read_text())
            self.assertEqual(len(data), 3)

    def test_export_markdown_via_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_project_with_records(tmp)
            r = subprocess.run(
                SF + ["export", "--project", str(target), "--format", "markdown"],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            md = (target / "exports" / "bibliography.md").read_text(encoding="utf-8")
            self.assertIn("# Bibliography", md)
            self.assertIn("peer-reviewed", md)

    def test_find_project_records_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_project_with_records(tmp)
            path = find_project_records(target)
            self.assertIsNotNone(path)
            self.assertEqual(path.name, "filtered_records.jsonl")
            records = load_records(path)
            self.assertEqual(len(records), 3)

    def test_export_rejects_unknown_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = self._make_project_with_records(tmp)
            r = subprocess.run(
                SF + ["export", "--project", str(target), "--format", "xml"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
