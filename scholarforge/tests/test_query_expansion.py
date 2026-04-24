"""Tests for Stage 3 — title-to-query expansion pipeline."""

import unittest

from scholarforge.search.input_classifier import classify
from scholarforge.search.title_parser import parse, salient_phrases
from scholarforge.search.query_expansion import expand


class InputClassifierTests(unittest.TestCase):
    def test_title_with_colon(self):
        c = classify("The neuroplastic brain: current breakthroughs and emerging frontiers")
        self.assertEqual(c.kind, "title_like")

    def test_question(self):
        c = classify("How does neuroplasticity change after stroke?")
        self.assertEqual(c.kind, "question_like")

    def test_keyword_list(self):
        c = classify("OCD, ERP therapy, exposure response prevention")
        self.assertEqual(c.kind, "keyword_list")

    def test_quoted_phrase(self):
        c = classify('"mysteries of Samothrace"')
        self.assertEqual(c.kind, "exact_phrase")

    def test_short_topic(self):
        c = classify("truffle hunting")
        self.assertEqual(c.kind, "broad_topic")

    def test_greek_question(self):
        c = classify("Πώς λειτουργεί η νευροπλαστικότητα;")
        self.assertEqual(c.kind, "question_like")


class TitleParserTests(unittest.TestCase):
    def test_splits_on_colon(self):
        p = parse("The neuroplastic brain: current breakthroughs and emerging frontiers")
        self.assertEqual(p.title, "The neuroplastic brain")
        self.assertIn("breakthroughs", p.subtitle)

    def test_content_words_strip_stopwords(self):
        p = parse("The mysteries of Samothrace")
        self.assertIn("mysteries", p.content_words)
        self.assertIn("samothrace", p.content_words)
        self.assertNotIn("the", p.content_words)
        self.assertNotIn("of", p.content_words)

    def test_salient_phrases_nonempty_for_title(self):
        phrases = salient_phrases("Ritual symbolism in the mysteries of Samothrace")
        self.assertTrue(len(phrases) >= 1)
        joined = " ".join(phrases).lower()
        self.assertTrue("mysteries" in joined or "samothrace" in joined
                        or "ritual symbolism" in joined)


class QueryExpansionTests(unittest.TestCase):
    def test_neuroplasticity_title_hits_lexicon(self):
        plan = expand(
            "The neuroplastic brain: current breakthroughs and emerging frontiers",
            include_multilingual=True,
        )
        self.assertEqual(plan.title, "The neuroplastic brain")
        self.assertTrue(plan.keyword_bundles,
                        "neuroscience lexicon should match 'neuroplastic brain'")
        modes = {q.mode for q in plan.queries}
        self.assertIn("broad", modes)
        self.assertIn("review", modes)
        # Multilingual term should exist
        all_ml = " ".join(plan.multilingual_terms)
        self.assertTrue(plan.multilingual_terms,
                        "multilingual terms expected for neuroplasticity")

    def test_keyword_list_produces_per_keyword_phrases(self):
        plan = expand("OCD, ERP therapy, exposure response prevention")
        self.assertEqual(plan.classification.split()[0], "keyword_list")
        phrase_qs = [q for q in plan.queries if q.mode == "phrase"]
        self.assertGreaterEqual(len(phrase_qs), 1)

    def test_exact_phrase_skips_bundles(self):
        plan = expand('"mysteries of Samothrace"')
        modes = [q.mode for q in plan.queries]
        self.assertIn("phrase", modes)
        self.assertIn("exact_phrase inputs skip bundle expansion", plan.notes)

    def test_samothrace_title_hits_classics_lexicon(self):
        plan = expand("Ritual symbolism in the mysteries of Samothrace")
        # Expect at least one bundle
        self.assertTrue(plan.keyword_bundles)
        flat = [kw.lower() for bundle in plan.keyword_bundles for kw in bundle]
        self.assertTrue(
            any("kabe" in k or "samothra" in k or "myster" in k for k in flat)
        )

    def test_recency_adds_year_range(self):
        plan = expand(
            "neuroplasticity",
            include_recency=True,
            now_year=2026,
        )
        recency_qs = [q for q in plan.queries if q.mode == "recency"]
        self.assertTrue(recency_qs)
        self.assertIn("2024..2026", recency_qs[0].text)

    def test_as_subject_strings_gives_legacy_glue(self):
        plan = expand("The neuroplastic brain: current breakthroughs")
        subs = plan.as_subject_strings()
        self.assertTrue(subs)
        self.assertIsInstance(subs[0], str)

    def test_pretty_print_contains_classification(self):
        plan = expand("neuroplasticity")
        self.assertIn("QUERY PLAN", plan.pretty())
        self.assertIn("INPUT CLASSIFICATION", plan.pretty())


if __name__ == "__main__":
    unittest.main()
