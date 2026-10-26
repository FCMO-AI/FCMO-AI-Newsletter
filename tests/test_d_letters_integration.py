"""D letters use published, locale-ready records through the real paper builder."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.paper.build import PaperBuilder

ROOT = Path(__file__).resolve().parents[1]


class LettersIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name) / 'paper'
        with patch('tools.paper.community.fetch_cartas', return_value=[{
            'title': 'Public Ghost letter', 'url': 'https://example.org/letter/',
            'published_at': '2026-10-02T12:00:00Z', 'authors': [{'name': 'Public author'}],
        }]):
            cls.builder = PaperBuilder(
                stories_path=ROOT / 'contracts/fixtures/stories.v2.json',
                status_path=ROOT / 'contracts/fixtures/newsroom-status.fresh.json',
                editorial_path=ROOT / 'tests/fixtures/editorial', out=cls.out, base='/paper/')
        cls.builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_letters_index_and_front_share_published_localized_records(self):
        for code, prefix, title in [('en', '', 'A durable public record'),
                                    ('es-419', 'es/', 'Un registro público duradero')]:
            with self.subTest(locale=code):
                front = (self.out / prefix / 'index.html').read_text()
                index = (self.out / prefix / 'letters/index.html').read_text()
                destination = f'/paper/{prefix}cartas/fixture-essay/'
                image = '/paper/editorial/pieces/fixture-essay/figures/fig-cover.webp'
                self.assertIn('class="d-letters-shelf"', front)
                self.assertIn('class="d-letter-index"', index)
                self.assertIn(title, front)
                self.assertIn(title, index)
                self.assertIn(f'href="{destination}"', front)
                self.assertIn(f'href="{destination}"', index)
                self.assertTrue((self.out / destination.removeprefix('/paper/') / 'index.html').is_file())
                self.assertIn(f'src="{image}"', front)
                self.assertTrue((self.out / image.removeprefix('/paper/')).is_file())
                self.assertIn('/paper/assets/css/d/d-letters.css', front)
                self.assertNotIn('fixture-withdrawn', index)
                self.assertNotIn('http-equiv="refresh"', index)
        en = (self.out / 'letters/index.html').read_text()
        self.assertLess(en.index('Public Ghost letter'), en.index('A durable public record'))
        self.assertIn('https://example.org/letter/', en)
        routes = json.loads((self.out / 'data/routes.json').read_text())
        self.assertEqual({row['path'] for row in routes if row['kind'] == 'letters'},
                         {'letters/', 'es/letters/', 'zh/letters/'})

    def test_unavailable_native_editions_never_leak_source_titles(self):
        for prefix in ('es/', 'zh/'):
            for suffix in ('', 'letters/'):
                page = (self.out / prefix / suffix / 'index.html').read_text()
                self.assertNotIn('Public Ghost letter', page)
                if prefix == 'zh/':
                    self.assertNotIn('A durable public record', page)
                    self.assertNotIn('持久的公共记录', page)
                    self.assertNotIn('d-letter-card', page)

    def test_an_empty_news_corpus_still_shows_real_letters(self):
        builder = copy.copy(self.builder)
        builder.live = []
        pages = []
        builder._write_page = lambda **page: pages.append(page)
        builder._front(builder.config['locales'][0])
        self.assertIn('class="d-letters-shelf"', pages[0]['body'])
        self.assertIn('Public Ghost letter', pages[0]['body'])
