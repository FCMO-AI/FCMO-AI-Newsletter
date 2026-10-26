"""Exercise the production builder's public core routes using committed records."""
import json
from pathlib import Path
import tempfile
import unittest
from tools.paper.build import PaperBuilder

ROOT = Path(__file__).resolve().parents[1]


class DSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='nl-d-site-')
        cls.out = Path(cls.tmp.name) / 'site'
        PaperBuilder(stories_path=ROOT/'site/data/stories.v2.json', status_path=ROOT/'site/data/newsroom-status.json',
                     editorial_path=ROOT/'tests/fixtures/editorial', out=cls.out, base='/paper/').build()
        cls.routes = json.loads((cls.out/'data/routes.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def page(self, row):
        return (self.out/row['path']/'index.html').read_text()

    def test_core_routes_link_all_d_sheets(self):
        for kind in ('landing', 'story', 'archive', 'method', 'search', 'topic', 'legal', 'status'):
            for row in [r for r in self.routes if r['kind'] == kind]:
                source = self.page(row)
                for name in ('base', 'front', 'story', 'letters', 'pages'):
                    self.assertIn(f'/paper/assets/css/d/d-{name}.css', source, row['path'])
                self.assertIn('d-nav', source)
                self.assertIn('d-footer', source)
                self.assertNotIn('SourceSerif4-normal', source)

    def test_front_evidence_map_and_numbered_rank_all_locales(self):
        for row in [r for r in self.routes if r['kind'] == 'landing']:
            source = self.page(row)
            for component in ('d-evidence-map', 'd-rank', 'd-legend', 'd-grade', 'd-stat'):
                self.assertIn(component, source, row['path'])

    def test_story_ledger_diagram_and_recorded_timeline(self):
        for row in [r for r in self.routes if r['kind'] == 'story'][:6]:
            source = self.page(row)
            for component in ('d-ledger', 'd-claims-sources', 'd-timeline'):
                self.assertIn(component, source)

    def test_archive_calendar_uses_real_editions_only(self):
        for row in [r for r in self.routes if r['kind'] == 'archive']:
            source = self.page(row)
            self.assertIn('d-calendar', source)
            self.assertIn('data-edition-date=', source)

    def test_language_switch_keeps_the_configured_mount(self):
        from html.parser import HTMLParser
        class Languages(HTMLParser):
            def __init__(self): super().__init__(); self.urls=[]
            def handle_starttag(self, tag, attrs):
                a=dict(attrs)
                if tag=='a' and a.get('hreflang'): self.urls.append(a['href'])
        row = next(r for r in self.routes if r['kind']=='landing' and r['locale']=='en')
        parser=Languages(); parser.feed(self.page(row))
        self.assertTrue(parser.urls)
        self.assertTrue(all(url.startswith('/paper/') for url in parser.urls),parser.urls)

    def test_navigation_letters_destination_exists(self):
        for locale, prefix in [('en',''),('es-419','es/'),('zh-Hans','zh/')]:
            self.assertTrue((self.out/prefix/'letters/index.html').is_file())
