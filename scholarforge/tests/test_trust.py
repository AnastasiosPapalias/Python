"""Tests for sources.trust classifier."""

import unittest

from scholarforge.sources.trust import classify


class TrustTests(unittest.TestCase):
    def test_arxiv_default_is_preprint(self):
        c = classify("arxiv", "", "Some quantum paper", "")
        self.assertEqual(c.source_type, "preprint")
        self.assertEqual(c.trust_label, "preprint")

    def test_openalex_journal_article_is_peer_reviewed(self):
        c = classify("openalex", "journal-article", "A study", "Background...")
        self.assertEqual(c.source_type, "journal_article")
        self.assertEqual(c.trust_label, "peer_reviewed")

    def test_title_signals_review(self):
        c = classify("crossref", "", "A systematic review of X", "")
        self.assertEqual(c.source_type, "review")
        self.assertEqual(c.trust_label, "peer_reviewed")

    def test_title_signals_meta_analysis(self):
        c = classify("pubmed", "", "Meta-analysis of treatment Y", "")
        self.assertEqual(c.source_type, "review")

    def test_ethesis_default_is_thesis(self):
        c = classify("ethesis", "", "On the topology of X", "")
        self.assertEqual(c.source_type, "thesis")
        self.assertEqual(c.trust_label, "grey_literature")

    def test_zenodo_default_is_repository_item(self):
        c = classify("zenodo", "", "Dataset release", "")
        self.assertEqual(c.source_type, "repository_item")
        self.assertEqual(c.trust_label, "grey_literature")

    def test_dataset_document_type(self):
        c = classify("zenodo", "dataset", "Some data", "")
        self.assertEqual(c.source_type, "dataset")
        self.assertEqual(c.trust_label, "dataset")

    def test_book_chapter(self):
        c = classify("crossref", "book-chapter", "Chapter 3", "")
        self.assertEqual(c.source_type, "book")
        self.assertEqual(c.trust_label, "peer_reviewed")

    def test_unknown_source_unknown_type(self):
        c = classify("", "", "", "")
        self.assertEqual(c.source_type, "unknown")
        self.assertEqual(c.trust_label, "uncertain")

    def test_thesis_in_title_beats_source_default(self):
        c = classify("openalex", "", "A doctoral dissertation on X", "")
        self.assertEqual(c.source_type, "thesis")


class RegistryTests(unittest.TestCase):
    def test_all_twenty_sources_present(self):
        from scholarforge.sources.registry import ALL_SOURCES
        self.assertEqual(len(ALL_SOURCES), 20)

    def test_by_name_lookup(self):
        from scholarforge.sources.registry import get
        src = get("openalex")
        self.assertEqual(src.label, "OpenAlex")
        self.assertEqual(src.source_type, "metadata")

    def test_grouping_covers_all(self):
        from scholarforge.sources import registry as R
        groups = [R.METADATA_BACKBONE, R.OA_SEARCH, R.PREPRINT,
                  R.BIOMED, R.REPOSITORY, R.BOOKS, R.THESES]
        total = sum(len(R.by_type(g)) for g in groups)
        self.assertEqual(total, 20)


if __name__ == "__main__":
    unittest.main()
