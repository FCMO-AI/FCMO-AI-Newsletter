"""Deterministic complexity guards for the full publication renderer."""
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

from tools.paper.build import PaperBuilder
from tools.paper.routes import href


class CountedCorpus(list):
    def __init__(self, rows):
        super().__init__(rows)
        self.visits = 0

    def __iter__(self):
        for row in super().__iter__():
            self.visits += 1
            yield row


class NeighborParser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.urls = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.append(dict(attrs)['href'])


class TaxonomyComplexity(unittest.TestCase):
    def builder(self, rows):
        builder = PaperBuilder.__new__(PaperBuilder)
        builder.live = CountedCorpus(rows)
        builder.base = '/fixture/'
        builder.catalogs = {code: {'strings': {'front': {'see_all': title}}}
                            for code, title in (('en', 'All'), ('es-419', 'Todo'), ('zh-Hans', '全部'))}
        return builder

    def test_taxonomy_membership_is_counted_once_for_all_pages_and_locales(self):
        for size in (8, 32):
            with self.subTest(stories=size):
                builder = self.builder([{'topics': ['Common', f'Topic {i}'],
                                         'organizations': ['Shared', f'Org {i}']}
                                        for i in range(size)])
                for code, prefix in (('en', ''), ('es-419', 'es/'), ('zh-Hans', 'zh/')):
                    for i in range(6):
                        text = builder._topic_links({'code': code, 'path_prefix': prefix},
                                                    exclude_org=f'org-{i}')
                        self.assertIn(prefix + 'topic/common/', text)
                self.assertLessEqual(builder.live.visits, 4 * size,
                                     'Pages must reuse build-scoped taxonomy membership counts')

    def test_membership_duplicates_ties_exclusions_and_limits_keep_exact_order(self):
        builder = self.builder([
            {'topics': ['Alpha', 'Alpha', 'Beta', 'Rare', 'Rare', 'Rare'], 'organizations': ['Twin', 'One', 'Both']},
            {'topics': ['Alpha', 'Beta', 'Both'], 'organizations': ['twin', 'One']},
            {'topics': ['Alpha', 'Beta', 'Both'], 'organizations': ['Two']},
        ])
        locale = {'code': 'en', 'path_prefix': ''}
        expected = ['topic/alpha/', 'topic/beta/', 'org/one/', 'org/both/',
                    'org/twin/', 'org/twin/', 'org/two/']
        text = builder._topic_links(locale, limit=20)
        self.assertEqual(NeighborParser(text).urls, ['/fixture/' + path for path in expected])
        self.assertNotIn('Rare', text)
        self.assertNotIn('topic/both/', text)
        self.assertIn('>Alpha</a><span>3</span>', text)
        self.assertLess(text.index('>Twin</a>'), text.index('>twin</a>'))
        for topic in ('Alpha', 'alpha'):
            for org in ('One', 'one'):
                for limit in (0, 1, 5, 20, -1):
                    with self.subTest(topic=topic, org=org, limit=limit):
                        actual = builder._topic_links(locale, exclude_topic=topic, exclude_org=org, limit=limit)
                        remaining = [path for path in expected if path not in ('topic/alpha/', 'org/one/')]
                        self.assertEqual(NeighborParser(actual).urls,
                                         ['/fixture/' + path for path in remaining[:limit]])
        other = self.builder([{'topics': [], 'organizations': ['Separate']}])
        self.assertIn('org/separate/', other._topic_links(locale))
        self.assertNotIn('org/separate/', builder._topic_links(locale))

    def test_only_selected_taxonomy_urls_are_rendered(self):
        builder = self.builder([{'topics': [], 'organizations': [f'Org {i}' for i in range(50)]}])
        with patch('tools.paper.build.href', wraps=href) as render_url:
            text = builder._topic_links({'code': 'en', 'path_prefix': ''}, limit=5)
        self.assertEqual(len(NeighborParser(text).urls), 5)
        self.assertLessEqual(render_url.call_count, 5)


if __name__ == '__main__':
    unittest.main()
