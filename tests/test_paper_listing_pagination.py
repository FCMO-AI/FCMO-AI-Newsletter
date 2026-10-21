"""Growing discovery lists retain every story within the publication budget."""
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit

from tools.gates import size_budget
from tools.paper.build import PaperBuilder
from tools.paper import sitemaps

ROOT = Path(__file__).resolve().parents[1]


class ListingParser(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.ids = []
        self.links = {}
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and attrs.get('class') == 'archive-item':
            self.ids.append(attrs['data-story-id'])
        if tag == 'a' and attrs.get('rel') in ('prev', 'next'):
            self.links[attrs['rel']] = attrs['href']


class ListingPagination(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.builder = PaperBuilder(
            stories_path=ROOT / 'contracts/fixtures/stories.v2.json',
            status_path=ROOT / 'contracts/fixtures/newsroom-status.fresh.json',
            out=self.out, base='/FCMO-AI-Newsletter/')
        template = next(s for s in self.builder.live
                        if s.get('l10n', {}).get('zh-Hans', {}).get('state') == 'NATIVE_ARB')
        self.stories = [{**template, 'id': f'FCMO-{i:012X}', 'slug': f'listing-story-{i}'}
                        for i in range(1200)]

    def render(self, kind, suffix, stories):
        for locale in self.builder.config['locales']:
            self.builder._listing(locale=locale, suffix=suffix,
                                  title=self.builder.catalogs[locale['code']]['strings']['archive']['title'],
                                  stories=stories, kind=kind)

    def test_growing_archive_passes_the_unchanged_size_gate_without_losing_stories(self):
        self.render('archive', 'archive/', self.stories)
        for prefix in ('', 'es/', 'zh/'):
            # This focused listing test supplies the homes required by SIZE_BUDGET.
            (self.out / prefix / 'index.html').write_text('<html></html>')
        size_budget.check(self.out)
        for prefix in ('', 'es/', 'zh/'):
            actual = []
            route = prefix + 'archive/'
            visited = set()
            while route:
                self.assertNotIn(route, visited, 'Pagination must not cycle')
                visited.add(route)
                parser = ListingParser((self.out / route / 'index.html').read_text())
                self.assertLessEqual(len(parser.ids), 100)
                actual.extend(parser.ids)
                previous = parser.links.get('prev')
                if len(visited) == 1:
                    self.assertIsNone(previous)
                else:
                    self.assertTrue((self.out / urlsplit(previous).path.removeprefix('/FCMO-AI-Newsletter/')).is_dir())
                route = urlsplit(parser.links['next']).path.removeprefix('/FCMO-AI-Newsletter/') if 'next' in parser.links else None
            self.assertEqual(actual, [s['id'] for s in self.stories])
            self.assertEqual(len(visited), 12)

    def test_other_growing_listings_keep_localized_routes_and_sitemap_entries(self):
        for kind, suffix in (('beat', 'beat/research/'), ('topic', 'topic/testing/'),
                             ('org', 'org/testing/'), ('edition', 'edition/' + self.stories[0]['url_date'] + '/')):
            with self.subTest(kind=kind):
                self.render(kind, suffix, self.stories[:201])
                for locale in self.builder.config['locales']:
                    prefix = locale['path_prefix']
                    for number in (1, 2, 3):
                        path = prefix + suffix + (f'page/{number}/' if number > 1 else '')
                        html = (self.out / path / 'index.html').read_text()
                        self.assertIn('lang="' + locale['html_lang'] + '"', html)
                        self.assertIn('hreflang="zh-Hans"', html)
                        self.assertTrue(any(r['path'] == path for r in self.builder.routes))
                sitemaps.write(self.builder.routes, out=self.out,
                               generated_at=self.builder.payload['generated_at'])
                self.assertIn(suffix + 'page/3/', (self.out / 'sitemap.xml').read_text())

    def test_pagination_labels_are_localized_and_a_single_link_fills_the_row(self):
        self.render('archive', 'archive/', self.stories[:250])
        english = self.builder.catalogs['en']['strings']['archive']
        for locale, prefix in (('es-419', 'es/'), ('zh-Hans', 'zh/')):
            strings = self.builder.catalogs[locale]['strings']['archive']
            self.assertNotEqual(strings['newer'], english['newer'])
            self.assertNotEqual(strings['older'], english['older'])
            page = (self.out / prefix / 'archive/page/2/index.html').read_text()
            self.assertIn(strings['newer'], page)
            self.assertIn(strings['older'], page)
            self.assertNotIn(english['newer'], page)
            self.assertNotIn(english['older'], page)
        css = (ROOT / 'site-src/assets/css/paper.css').read_text()
        self.assertIn('.edition-neighbors[data-pagination]:has(>a:only-child){grid-template-columns:minmax(0,1fr)}', css)


if __name__ == '__main__':
    unittest.main()
