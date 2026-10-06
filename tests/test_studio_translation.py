"""L28a: translation integrity, human authority and distribution (offline)."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from studio.server.storage import Store, Conflict
from studio.server.publishing import Publisher, Refused
from studio.server.checks import checks
from tools.gates import piece_valid
from tools.gates.common import GateFailure
from tests.harness.validate import Validator

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {'schema': 'fcmo-essay-doc-v1', 'locale': 'es-419', 'title': 'Una idea de Javier',
          'dek': 'FCMO AI el 2026-10-05', 'blocks': [
              {'id': 'b-12345678', 'type': 'p', 'content': [
                  {'t': 'text', 'v': 'Javier propone 42 ideas.'},
                  {'t': 'fn', 'id': 'fn-12345678'},
                  {'t': 'link', 'href': 'https://example.org/ref', 'c': [{'t': 'text', 'v': 'fuente'}]},
                  {'t': 'cite', 'key': 'src-one', 'locator': 'p. 4'}]},
              {'id': 'b-abcdef12', 'type': 'blockquote', 'content': [{'t': 'text', 'v': '«Una voz propia»'}]}],
          'footnotes': {'fn-12345678': [{'t': 'text', 'v': 'Nota 7.'}]}}

class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.store = Store(Path(self.temp.name) / 'data')
    def tearDown(self):
        self.store.close(); self.temp.cleanup()
    def source(self):
        self.slug = self.store.create('javier', 'essay', SOURCE['title'], 'es-419')['slug']
        self.store.save(self.slug, 'es-419', 'javier', 0, SOURCE, {})
        return self.slug
    def translate(self, provider=None):
        from studio.translation import translate, FakeProvider
        return translate(self.store, self.slug, 'javier', self.store.piece(self.slug)['head_rev'], provider or FakeProvider())
    def test_spanish_source_is_authorized_without_environment_flag(self):
        with patch.dict('os.environ', {}, clear=True): self.source()
    def test_fake_parity_and_provenance_then_human_edit(self):
        self.source(); self.translate()
        payload = self.store.payload(self.slug)
        for loc in ('en', 'zh-Hans'):
            doc = payload['docs'][loc]
            self.assertEqual([b['id'] for b in doc['blocks']], [b['id'] for b in SOURCE['blocks']])
            self.assertEqual(set(doc['footnotes']), set(SOURCE['footnotes']))
            self.assertEqual(payload['provenance'][loc]['origin'], 'agent_draft')
            self.assertEqual(payload['provenance'][loc]['model'], 'fake')
            self.assertFalse(payload['provenance'][loc]['human_reviewed'])
        doc = copy.deepcopy(payload['docs']['en']); doc['title'] += ' edited'
        self.store.save(self.slug, 'en', 'javier', self.store.piece(self.slug)['head_rev'], doc, {})
        row = self.store.payload(self.slug)['provenance']['en']
        self.assertEqual(row['origin'], 'agent_draft_human_edited'); self.assertEqual(row['model'], 'fake')
        self.assertFalse(row['human_reviewed'])
    def test_dropped_footnote_blocks_atomic_result_with_spanish_reason(self):
        from studio.translation import FakeProvider, TranslationError
        self.source(); before = self.store.payload(self.slug)
        with self.assertRaisesRegex(TranslationError, 'nota'):
            self.translate(FakeProvider(drop_footnote=True))
        self.assertEqual(self.store.payload(self.slug)['docs'], before['docs'])
        self.assertIn('nota', self.store.piece(self.slug)['translation_error'])
    def test_structural_adversaries_including_title_date_quote_and_note_link(self):
        from studio.translation import validate_translation, TranslationError
        mutations = [
            lambda d: d['blocks'][0]['content'].pop(1),
            lambda d: d['blocks'][0]['content'][2].update(href='https://example.org/other'),
            lambda d: d.update(dek='FCMO AI el 2026-10-06'),
            lambda d: d['blocks'][0]['content'][0].update(v='Javier propone 43 ideas.'),
            lambda d: d['blocks'][1]['content'][0].update(v='Otra voz'),
            lambda d: d['blocks'][0].update(content=[]),
            lambda d: d['blocks'][0]['content'][3].update(key='new-source'),
            lambda d: d.update(title='Una idea de FCMO Group'),
            lambda d: d.update(title='Una idea de Pedro'),
        ]
        for mutate in mutations:
            target = copy.deepcopy(SOURCE); target['locale'] = 'en'; mutate(target)
            with self.subTest(mutate=mutate), self.assertRaises(TranslationError):
                validate_translation(SOURCE, target, 'en')
        source = copy.deepcopy(SOURCE)
        source['footnotes']['fn-12345678'].append({'t': 'link', 'href': 'https://example.org/note', 'c': [{'t': 'text', 'v': 'nota'}]})
        target = copy.deepcopy(source); target['locale'] = 'en'; target['footnotes']['fn-12345678'][-1]['href'] += '/changed'
        with self.assertRaises(TranslationError): validate_translation(source, target, 'en')
    def test_changed_revision_during_translation_is_not_overwritten(self):
        from studio.translation import FakeProvider
        self.source()
        class RacingProvider(FakeProvider):
            def generate(inner, request):
                doc = copy.deepcopy(SOURCE); doc['title'] += ' nuevo'
                self.store.save(self.slug, 'es-419', 'javier', self.store.piece(self.slug)['head_rev'], doc, {})
                return super().generate(request)
        with self.assertRaises(Conflict): self.translate(RacingProvider())
    def test_review_is_required_and_matias_approval_reviews_translations(self):
        self.source(); self.translate()
        self.store.locale_state(self.slug, 'es-419', 'javier', 'ready', True)
        preview = SimpleNamespace(privacy=lambda value: True)
        publisher = Publisher(self.store, None, None, lambda value: checks(self.store, preview, value))
        results = publisher.checker(self.slug)
        self.assertTrue(any(not r['ok'] and r['id'].startswith('review-') for r in results))
        publisher.request(self.slug, 'javier')
        with self.assertRaises(Refused): publisher.approve(self.slug, 'javier')
        publisher.approve(self.slug, 'matias')
        for loc in ('en', 'es-419', 'zh-Hans'):
            row = self.store.payload(self.slug)['provenance'][loc]
            self.assertTrue(row['human_reviewed']); self.assertEqual(row['reviewer'], 'Matías')
        self.assertEqual(self.store.payload(self.slug)['provenance']['en']['origin'], 'agent_draft')
    def test_email_intent_written_and_closed_schema(self):
        self.source()
        self.assertTrue(self.store.payload(self.slug)['piece']['distribution']['email'])
        self.store.distribution(self.slug, 'javier', self.store.piece(self.slug)['head_rev'], False)
        saved = json.loads((self.store.directory(self.slug) / 'piece.json').read_text())
        self.assertEqual(saved['distribution'], {'email': False})
        schema = json.loads((ROOT / 'contracts/piece.v1.schema.json').read_text())
        self.assertEqual(Validator(schema).errors(saved), [])
        for distribution in ({'email': 'yes'}, {'email': True, 'extra': True}):
            self.assertTrue(Validator(schema).errors({**saved, 'distribution': distribution}))
    def test_claude_cli_headless_contract_timeout_no_execution(self):
        from studio.translation import ClaudeCLIProvider, make_request, FakeProvider, TranslationError
        provider = ClaudeCLIProvider(timeout=37)
        request = make_request(SOURCE)
        response = FakeProvider().generate(request)
        with patch('studio.translation.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(response))) as run:
            self.assertEqual(provider.generate(request), response)
        args, kwargs = run.call_args
        self.assertEqual(args[0][:5], ['claude', '-p', '--model', 'sonnet', '--output-format'])
        self.assertEqual(kwargs['timeout'], 37)
        self.assertFalse(kwargs.get('shell', False))
        self.assertEqual(json.loads(kwargs['input']), request)
        self.assertNotIn('GH_TOKEN_JAVIER', kwargs['env'])
        with patch('studio.translation.subprocess.run', return_value=SimpleNamespace(returncode=0, stdout='```json\n{}\n```')):
            with self.assertRaises(TranslationError): provider.generate(request)
    def test_piece_gate_requires_review_and_validates_distribution(self):
        root = Path(self.temp.name) / 'out'
        shutil.copytree(ROOT / 'tests/fixtures/editorial', root / 'editorial')
        for piece in (root / 'editorial/pieces').iterdir():
            for loc, prefix in (('en', ''), ('es-419', 'es'), ('zh-Hans', 'zh')):
                route = root / prefix / 'cartas' / piece.name / 'index.html'; route.parent.mkdir(parents=True)
                ident = json.loads((piece / 'piece.json').read_text())['id']
                route.write_text(f'<article class="essay" data-piece-id="{ident}">')
        path = root / 'editorial/pieces/fixture-essay/piece.json'
        piece = json.loads(path.read_text()); piece['distribution'] = {'email': True}; path.write_text(json.dumps(piece))
        piece_valid.check(root)
        for bad in ({'email': 'true'}, {'email': True, 'unknown': 1}):
            piece['distribution'] = bad; path.write_text(json.dumps(piece))
            with self.assertRaises(GateFailure): piece_valid.check(root)
        piece['distribution'] = {'email': True}; path.write_text(json.dumps(piece))
        provenance_path = path.with_name('provenance.json'); provenance = json.loads(provenance_path.read_text())
        provenance['zh-Hans'].update(origin='agent_draft', human_reviewed=False, reviewer='', model='fake')
        provenance_path.write_text(json.dumps(provenance))
        with self.assertRaises(GateFailure): piece_valid.check(root)
        provenance['zh-Hans'].update(human_reviewed=True, reviewer='Matías')
        provenance_path.write_text(json.dumps(provenance)); piece_valid.check(root)

if __name__ == '__main__': unittest.main()
