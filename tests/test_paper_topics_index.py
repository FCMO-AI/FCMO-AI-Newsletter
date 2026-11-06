"""The Topics index (topic/) and the heading of topic pages come only from the build's live stories."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import tempfile
import unittest

from tools.paper.build import PaperBuilder
from tools.paper.templates import d_components as dc

ROOT = Path(__file__).resolve().parents[1]
BASE = '/FCMO-AI-Newsletter/'


class Links(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.hrefs, self.rows, self.cards = [], [], []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.hrefs.append(a['href'])
        if tag == 'li' and 'data-topic' in a:
            self.rows.append((a['data-topic'], a['data-family'], int(a['data-count']), 'd-tx-card' in a.get('class', '')))


class TopicsIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.builder = PaperBuilder(stories_path=ROOT / 'site/data/stories.v2.json', status_path=ROOT / 'site/data/newsroom-status.json',
                                   editorial_path=ROOT / 'editorial', out=cls.out, base=BASE)
        cls.builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def page(self, route):
        return (self.out / route / 'index.html').read_text(encoding='utf-8')

    def test_every_locale_has_an_index_and_the_menu_points_to_it(self):
        for locale in self.builder.config['locales']:
            prefix = locale['path_prefix']
            for route in (prefix, prefix + 'archive/', prefix + 'topic/', prefix + 'topic/robotics/'):
                self.assertIn(f'href="{BASE}{prefix}topic/"', self.page(route), route)

    def test_counts_match_the_topic_listings_and_each_family_is_present(self):
        live = self.builder.live
        truth = Counter(t for s in live for t in set(s.get('topics') or []))
        for locale in self.builder.config['locales']:
            prefix = locale['path_prefix']
            names = self.builder.catalogs[locale['code']]['labels']['topic']
            rows = Links(self.page(prefix + 'topic/')).rows
            slugs = [r[0] for r in rows]
            self.assertEqual(len(slugs), len(set(slugs)))
            self.assertEqual(set(slugs), {t for t, n in truth.items() if n >= 3 and t in names})
            self.assertEqual({r[1] for r in rows}, {'foundry', 'living', 'intelligence'})
            for slug, family, count, _card in rows:
                self.assertEqual(count, truth[slug], slug)
                self.assertEqual(family, dc._TOPIC_SIGNALS.get(slug) or dc._topic_signal_fallback(slug))
                listing = self.page(f'{prefix}topic/{slug}/')
                self.assertEqual(len(re.findall(r'<article class="archive-item"', listing)), min(count, 100))

    def test_no_broken_internal_links_on_the_index(self):
        for locale in self.builder.config['locales']:
            for href in set(Links(self.page(locale['path_prefix'] + 'topic/')).hrefs):
                if href.startswith(BASE) and not href.startswith(BASE + 'assets/'):
                    target = self.out / href[len(BASE):].split('#')[0].split('?')[0]
                    self.assertTrue((target / 'index.html').exists() or target.is_file(), href)

    def test_latest_story_and_evidence_word_are_real(self):
        page = self.page('topic/')
        self.assertIn('d-claim', page)
        self.assertRegex(page, r'datetime="20\d\d-')
        newest = max((s for s in self.builder.live if 'robotics' in (s.get('topics') or [])), key=lambda s: (s['event_at'], s['id']))
        self.assertIn(self.builder._story_href(self.builder.config['locales'][0], newest), page)

    def test_front_page_drops_the_footer_list_and_topic_pages_get_a_heading(self):
        front = self.page('')
        self.assertNotIn('<ul><li><a href="' + BASE + 'topic/robotics/', front)
        self.assertNotIn('d-front-topics"><div class="frame"><h2', front)
        self.assertIn('All topics', front)
        head = self.page('topic/robotics')
        self.assertIn('d-tx-topic-head', head)
        self.assertIn('d-tx-back', head)
        self.assertIn('<h1 class="page-title d-page-title" translate="no">Robotics</h1>', head)

    def test_topic_pages_keep_their_pagination(self):
        pages = [p for p in (self.out / 'topic').glob('*/page/2/index.html')]
        for p in pages[:3]:
            self.assertIn('archive-pager', p.read_text(encoding='utf-8'))
            self.assertIn('rel="prev"', p.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
