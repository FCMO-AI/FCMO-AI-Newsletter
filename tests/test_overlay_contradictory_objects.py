from __future__ import annotations

import unittest

from tools import validate_localizations as vl


class OverlayContradictoryEvidenceObjectsTests(unittest.TestCase):
    """Airlock 2026-10-30 sent contradictory_evidence as {description, source_ids} objects (FCMO-6EAE0A44CEEB)."""

    def test_objects_are_flattened_to_text_like_the_canonical_record(self):
        row = {"contradictory_evidence": [{"description": " Uno. ", "source_ids": ["S1"]}, "Dos.", {"description": ""}]}
        self.assertEqual(vl.normalize_record(row)["contradictory_evidence"], ["Uno.", "Dos."])
        self.assertIsInstance(row["contradictory_evidence"][0], dict, "input must not be mutated")

    def test_string_lists_are_untouched(self):
        row = {"contradictory_evidence": ["Uno."]}
        self.assertIs(vl.normalize_record(row), row)


if __name__ == "__main__":
    unittest.main()
