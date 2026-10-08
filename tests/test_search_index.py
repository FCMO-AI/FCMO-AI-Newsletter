from __future__ import annotations

import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.paper import essays, search_index
from tools.paper.build import PaperBuilder
from tools.paper.i18n import dek, headline
from tools.paper.routes import href, story_path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'contracts/fixtures'


class SearchForm(HTMLParser):
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'form' and 'data-search-form' in values:
            self.index = values['data-index']
            self.shards = json.loads(values['data-shards'])


class ShardPackingTests(unittest.TestCase):
    def test_utf8_exact_budget_boundary_and_cleanup_after_shrinking(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'search.json'
            # Include multibyte and escaped characters; byte size, not character count, governs.
            row = {'h': '汉"\\'}
            overhead = len(json.dumps([row], ensure_ascii=False, separators=(',', ':')).encode())
            row['h'] += 'x' * (search_index.LIMIT - overhead)
            paths = search_index.write_shards([row, {'h': 'last'}], out=out)
            self.assertEqual(len(paths), 2)
            self.assertEqual(paths[0].stat().st_size, search_index.LIMIT)
            self.assertEqual(json.loads(paths[0].read_bytes()), [row])
            self.assertEqual(json.loads(paths[1].read_bytes()), [{'h': 'last'}])
            self.assertEqual(search_index.write_shards([], out=out), [out])
            self.assertEqual(out.read_bytes(), b'[]')
            self.assertFalse(paths[1].exists())
            row['h'] += 'x'
            with self.assertRaisesRegex(ValueError, 'search row exceeds'):
                search_index.write_shards([row], out=out)
            self.assertEqual(out.read_bytes(), b'[]', 'oversized rows fail before replacing files')

    def test_comma_bytes_can_force_a_new_shard(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'search.json'
            row = {'h': 'x' * ((search_index.LIMIT - 2) // 2 - len(b'{"h":""}'))}
            paths = search_index.write_shards([row, row], out=out)
            self.assertEqual(len(paths), 2)
            self.assertTrue(all(p.stat().st_size <= search_index.LIMIT for p in paths))


class GrowingSearchIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='l42-growth-')
        cls.root = Path(cls.temp.name)
        cls.out = cls.root / 'publish'
        payload = json.loads((FIXTURES / 'stories.v2.json').read_text())
        seed = next(s for s in payload['stories'] if s['status'] == 'live')
        stories = []
        for i in range(1000):
            story = copy.deepcopy(seed)
            story.update(id=f'FCMO-{i:012X}', slug=f'growth-story-{i:04d}', url_date='2026-10-08',
                         event_at='2026-10-08T12:00:00Z', corrections=[], organizations=['Growth Lab'], topics=['growth'])
            story.update(title=f'growth-story-{i:04d}', headline=f'growth-story-{i:04d}', dek='Synthetic search coverage. ' * 20)
            for code, title, description in [('es-419', 'Historia', 'Cobertura de búsqueda. '), ('zh-Hans', '报道', '搜索覆盖。')]:
                story['l10n'][code] = {'state': 'NATIVE_ARB', 'fields': {
                    'title': f'{title}-{i:04d}', 'headline': f'{title}-{i:04d}', 'dek': description * 80,
                    'summary': description * 80}}
            stories.append(story)
        payload['stories'] = stories
        payload['published_edition_dates'] = ['2026-10-08']
        source = cls.root / 'stories.json'
        source.write_text(json.dumps(payload, ensure_ascii=False))
        cls.builder = PaperBuilder(stories_path=source, status_path=FIXTURES / 'newsroom-status.fresh.json',
                                   editorial_path=ROOT / 'tests/fixtures/editorial', out=cls.out, base='/FCMO-AI-Newsletter/')
        cls.builder.build()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def locale_rows(self, locale):
        page = self.out / locale['path_prefix'] / 'search/index.html'
        form = SearchForm()
        form.feed(page.read_text())
        paths = [self.out / url.removeprefix(self.builder.base) for url in form.shards]
        rows = [row for p in paths for row in json.loads(p.read_bytes())]
        return form, paths, rows

    def test_thousand_stories_and_essays_fit_and_are_referenced_in_every_locale(self):
        for locale in self.builder.config['locales']:
            with self.subTest(locale=locale['code']):
                form, paths, rows = self.locale_rows(locale)
                self.assertGreater(len(paths), 1)
                self.assertEqual(form.index, form.shards[0])
                self.assertEqual(paths, [paths[0]] + [paths[0].with_name(f'search-{i}.json') for i in range(2, len(paths) + 1)])
                self.assertEqual(set(paths), set(paths[0].parent.glob('search*.json')))
                self.assertTrue(all(p.stat().st_size <= search_index.LIMIT for p in paths))
                story_rows = [row for row in rows if row.get('kind') != 'essay']
                expected = {href(self.builder.base, story_path(locale, s)) for s in self.builder.live}
                self.assertEqual(len(story_rows), 1000)
                self.assertEqual({r['u'] for r in story_rows}, expected)
                self.assertTrue(all(set(r) == {'h', 'd', 'u', 'b', 'o', 't'} for r in story_rows))
                expected_essays = essays.piece_search_rows(self.builder.editorial_pieces, locale['code'], base=self.builder.base)
                self.assertEqual([r for r in rows if r.get('kind') == 'essay'], expected_essays)
                ranked = sorted(self.builder.live, key=lambda s: (s['event_at'], s['id']), reverse=True)
                self.assertEqual([r['u'] for r in story_rows], [href(self.builder.base, story_path(locale, s)) for s in ranked])
                self.assertEqual(story_rows[0]['h'], headline(ranked[0], locale['code'], self.builder.catalogs[locale['code']]))
                self.assertEqual(story_rows[0]['d'], dek(ranked[0], locale['code'], self.builder.catalogs[locale['code']]))
                print(f"L42 growth {locale['code']}: stories={len(story_rows)} essays={len(expected_essays)} shards={len(paths)} max_bytes={max(p.stat().st_size for p in paths)}")
        self.assertLessEqual(sum(p.stat().st_size for p in self.out.rglob('*.js')), 30720)

    def test_shipped_client_finds_story_only_in_last_shard(self):
        for locale in self.builder.config['locales']:
            form, paths, rows = self.locale_rows(locale)
            last = next(r for r in json.loads(paths[-1].read_bytes()) if r.get('kind') != 'essay')
            self.assertFalse(any(last['u'] == r['u'] for p in paths[:-1] for r in json.loads(p.read_bytes())))
            result = subprocess.run(['node', str(ROOT / 'tests/search_client.mjs')], input=json.dumps({
                'script': (self.out / 'assets/js/search.js').read_text(),
                'shards': {url: json.loads(path.read_bytes()) for url, path in zip(form.shards, paths)},
                'term': last['h'], 'url': last['u']}), text=True, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_published_agent_guidance_uses_the_authoritative_api(self):
        agent = json.loads((self.out / 'agent.json').read_text())
        self.assertTrue(agent['endpoints']['search'].endswith('/api/v1/search-index.json'))
        for kind in ('search', 'documents'):
            self.assertEqual(agent['query_types'][kind]['offline_source'], 'api/v1/search-index.json')
        api = json.loads((self.out / 'api/v1/search-index.json').read_text())
        self.assertEqual({r['id'] for r in api['items']}, {s['id'] for s in self.builder.live})
        self.assertTrue(all({'title', 'summary', 'url', 'evidence', 'confidence', 'importance'} <= r.keys() for r in api['items']))
        for locale in self.builder.config['locales']:
            for name in ('llms.txt', 'llms-full.txt'):
                text = (self.out / locale['path_prefix'] / name).read_text()
                self.assertIn('/api/v1/search-index.json', text)
                self.assertNotIn('data/search.json — full-text', text)
                self.assertNotIn('"offline_source": "data/search.json"', text)
