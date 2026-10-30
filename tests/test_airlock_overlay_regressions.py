from __future__ import annotations

import unittest

from tools import validate_localizations as vl
from tools.gates import english_leak


class OverlayContradictoryEvidenceObjectsTests(unittest.TestCase):
    """Airlock 2026-10-30 sent contradictory_evidence as {description, source_ids} objects (FCMO-6EAE0A44CEEB)."""

    def test_objects_are_flattened_to_text_like_the_canonical_record(self):
        row = {"contradictory_evidence": [{"description": " Uno. ", "source_ids": ["S1"]}, "Dos.", {"description": ""}]}
        self.assertEqual(vl.normalize_record(row)["contradictory_evidence"], ["Uno.", "Dos."])
        self.assertIsInstance(row["contradictory_evidence"][0], dict, "input must not be mutated")

    def test_string_lists_are_untouched(self):
        row = {"contradictory_evidence": ["Uno."]}
        self.assertIs(vl.normalize_record(row), row)


class SpanishSentenceNamingAnEnglishTitleTests(unittest.TestCase):
    """FCMO-1D451D958006 (2026-10-29): a Spanish sentence quoting a paper title froze every refresh for 52 h."""

    def test_spanish_sentence_naming_an_english_title_is_not_english_prose(self):
        text = "Los autores publicaron el preprint arXiv 2610.37658v1, When Should We Intervene at Test Time?, el 27 de octubre de 2026."
        self.assertFalse(english_leak.looks_english(text))

    def test_unmarked_english_prose_still_fails(self):
        self.assertTrue(english_leak.looks_english("This is English prose that remains a release defect."))
        self.assertTrue(english_leak.looks_english("The authors posted the preprint when we asked, and it is on the site de la"))


if __name__ == "__main__":
    unittest.main()
