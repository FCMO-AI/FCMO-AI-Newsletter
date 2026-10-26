import shutil
import tempfile
import unittest
from pathlib import Path

from tools.paper import community, essays


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/editorial/pieces/fixture-essay"


class LettersShelfTests(unittest.TestCase):
    def test_empty_shelf_is_absent(self):
        self.assertEqual("", community.render_letters_shelf([], "en"))
        self.assertEqual("", community.render_letters_index([], "en"))

    def test_ghost_shelf_handles_missing_image_and_locales_without_inventing_author(self):
        letters = [{"title": "A " + "long " * 20 + "title", "url": "/cartas/long/", "published_at": "2026-10-01T12:00:00Z", "custom_excerpt": None}]
        for locale in ("en", "es-419", "zh-Hans"):
            html = community.render_letters_shelf(letters, locale)
            self.assertIn('class="d-letter-card no-image"', html)
            self.assertIn("long", html)
            self.assertNotIn("Research editor", html)
            self.assertNotIn("<img", html)
            self.assertNotIn("By ", html)

    def test_index_localizes_and_keeps_only_present_fields(self):
        letters = [
            {"title": "Letter " + "long " * 12, "url": "/cartas/one/", "published_at": "2026-10-01T12:00:00Z", "authors": [{"name": "Javier"}], "kind": "letter"},
            {"title": "Matías essay", "url": "/cartas/two/", "published_at": "2026-09-30T12:00:00Z", "kind": "essay"},
        ]
        for locale, expected in (("en", "Letters"), ("es-419", "Cartas"), ("zh-Hans", "来信")):
            html = community.render_letters_index(letters, locale)
            self.assertIn(expected, html)
            self.assertIn('class="d-letter-row"', html)
            self.assertIn("Javier", html)
            self.assertNotIn("Research editor", html)
            self.assertEqual(2, html.count('class="d-letter-row"'))

    def test_piece_shelf_reads_localized_document_data(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "fixture-essay"
            shutil.copytree(FIXTURE, target)
            piece = essays.load_piece(target)
        shelf = community.render_letters_shelf([piece], "en")
        self.assertIn("A durable public record", shelf)
        self.assertIn("Javier", shelf)
        self.assertIn("editorial/pieces/fixture-essay/figures/fig-cover.webp", shelf)

    def test_piece_page_has_data_driven_hero_and_chinese_title(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "fixture-essay"
            shutil.copytree(FIXTURE, target)
            piece = essays.load_piece(target)
        _, _, html = essays.render_piece(piece, "en", base="/newsletter/")
        self.assertIn('class="essay-hero"', html)
        self.assertIn('/newsletter/editorial/pieces/fixture-essay/figures/fig-cover.webp', html)
        self.assertIn('data-kind="essay"', html)

    def test_missing_locale_title_is_not_replaced_with_slug(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "fixture-essay"
            shutil.copytree(FIXTURE, target)
            piece = essays.load_piece(target)
        _, _, html = essays.render_piece(piece, "zh-Hans", base="/newsletter/")
        self.assertNotIn("Fixture Essay", html)
        self.assertNotIn("fixture-essay</h1>", html)


if __name__ == "__main__":
    unittest.main()
