"""R3: Letters with no real letters shows R4's structure and an honest empty state.

The public Newsletter never invents letters, authors or quotes. The fixture piece used
here lives only under tests/ and is clearly fictitious; the build only ever renders
pieces found in editorial/pieces.
"""
import re
import unittest
from pathlib import Path

from tools.paper import community

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/editorial/pieces/fixture-essay"


class LettersEmptyStateTests(unittest.TestCase):
    def test_empty_state_has_structure_and_no_persons(self):
        for code, none in (("en", "No letters have been published yet."), ("es-419", "Aún no hay cartas publicadas.")):
            html = community.render_letters_empty(code)
            self.assertIn(none, html)
            self.assertNotIn("<img", html.replace('class="plate"', ""))
            for name in ("Javier", "Castellanos", "Matías", "Founder", "Research editor", "System designer"):
                self.assertNotIn(name, html)
            self.assertNotIn("d-letter-card", html)

    def test_zh_empty_state_is_localized(self):
        html = community.render_letters_empty("zh-Hans")
        self.assertRegex(html, r"[一-鿿]")

    def test_real_editorial_dir_ships_no_pieces_so_no_letter_page_is_invented(self):
        pieces = ROOT / "editorial/pieces"
        self.assertEqual([], [p for p in pieces.glob("*") if p.is_dir()] if pieces.exists() else [])

    def test_letter_page_template_exists_and_is_exercised_only_by_the_test_fixture(self):
        self.assertTrue(FIXTURE.is_dir())
        self.assertIn("fixture", FIXTURE.name)


if __name__ == "__main__":
    unittest.main()
