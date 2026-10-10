"""One-language authoring, source binding and honest machine review, offline."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from studio.server.storage import Store
from studio.server.checks import checks
from studio.server.publishing import Publisher
from studio.translation import FakeProvider, TranslationError, translate, validate_translation


DOC = {'schema': 'fcmo-essay-doc-v1', 'locale': 'es-419',
       'title': 'Una prueba', 'dek': 'Una decisión con evidencia',
       'blocks': [{'id': 'b-12345678', 'type': 'p', 'content': [
           {'t': 'text', 'v': 'OpenAI publicó GPT-6.1 con 42 pruebas. FCMO-P-123456789abc sigue sin confirmar.'},
           {'t': 'link', 'href': 'https://example.org/evidence', 'c': [{'t': 'text', 'v': 'evidencia'}]}]}],
       'footnotes': {}}


class SingleSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / 'data'); self.addCleanup(self.store.close)

    def source(self, loc='es-419'):
        doc = copy.deepcopy(DOC); doc['locale'] = loc
        slug = self.store.create('javier', 'essay', doc['title'], loc)['slug']
        self.store.save(slug, loc, 'javier', 0, doc, {})
        return slug

    def test_english_source_generates_spanish_and_chinese(self):
        slug = self.source('en')
        result = translate(self.store, slug, 'javier', 1, FakeProvider())
        self.assertEqual(result['locales'], ['es-419', 'zh-Hans'])
        for loc in result['locales']:
            self.assertEqual(self.store.piece(slug)['locales'][loc]['review_state'], 'MACHINE_REVIEWED')

    def test_spanish_only_request_prepares_editions_and_approval_does_not_invent_chinese_review(self):
        slug = self.source()
        preview = SimpleNamespace(privacy=lambda value: True)
        publisher = Publisher(self.store, None, None, lambda value: checks(self.store, preview, value))
        with patch('studio.translation.configured_provider', return_value=FakeProvider()):
            publisher.request(slug, 'javier')
        publisher.approve(slug, 'matias')
        payload = self.store.payload(slug)
        for loc in ('en', 'zh-Hans'):
            self.assertFalse(payload['provenance'][loc]['human_reviewed'])
            self.assertEqual(payload['provenance'][loc]['review_state'], 'MACHINE_REVIEWED')
            validate_translation(payload['docs']['es-419'], payload['docs'][loc], loc)
        self.assertTrue(payload['provenance']['es-419']['human_reviewed'])
        # Exercise the exact public, provider-free piece validator and reader disclosure.
        from tools.gates import piece_valid
        from tools.paper.essays import load_editorial, render_piece
        root = Path(self.tmp.name) / 'public'; directory = root / 'editorial/pieces' / slug
        import shutil
        shutil.copytree(self.store.directory(slug), directory)
        for loc, prefix in (('en', ''), ('es-419', 'es'), ('zh-Hans', 'zh')):
            route = root / prefix / 'cartas' / slug / 'index.html'; route.parent.mkdir(parents=True)
            route.write_text('<article class="essay" data-piece-id="' + payload['piece']['id'] + '">')
        piece_valid.check(root)
        pieces, _ = load_editorial(root / 'editorial')
        self.assertIn('mt-disclosure', render_piece(pieces[0], 'zh-Hans', base='/')[2])
        edited = json.loads((directory / 'doc.zh-Hans.json').read_text()); edited['title'] += ' drift'
        (directory / 'doc.zh-Hans.json').write_text(json.dumps(edited))
        from tools.gates.common import GateFailure
        with self.assertRaises(GateFailure): piece_valid.check(root)

    def test_source_title_change_invalidates_every_translation_even_draft_and_regenerates(self):
        from studio.translation import prepare
        slug = self.source(); translate(self.store, slug, 'javier', 1, FakeProvider())
        self.store.locale_state(slug, 'en', 'javier', 'drafting')
        source = copy.deepcopy(DOC); source['title'] = 'Otra decisión'
        self.store.save(slug, 'es-419', 'javier', self.store.piece(slug)['head_rev'], source, {})
        for loc in ('en', 'zh-Hans'):
            self.assertTrue(self.store.piece(slug)['locales'][loc]['source_changed'])
        prepare(self.store, slug, 'javier', provider=FakeProvider())
        self.assertEqual(self.store.doc(slug, 'en')['doc']['title'], source['title'])
        self.assertFalse(self.store.piece(slug)['locales']['en'].get('source_changed', False))

    def test_english_models_ids_and_reasonable_length_are_protected(self):
        source = copy.deepcopy(DOC); source['locale'] = 'en'
        source['blocks'][0]['content'][0]['v'] = 'OpenAI and Jane Doe tested GPT-6.1 in 42 trials under FCMO-P-123456789abc.'
        for text in ('OtherAI and Jane Doe tested GPT-6.1 in 42 trials under FCMO-P-123456789abc.',
                     'OpenAI and Jane Doe tested XYZ-6.1 in 42 trials under FCMO-P-123456789abc.',
                     'OpenAI and Jane Doe tested GPT-6.1 in 42 trials under FCMO-P-123456789abd.',
                     source['blocks'][0]['content'][0]['v'] + ' invented explanation' * 500):
            target = copy.deepcopy(source); target['locale'] = 'zh-Hans'; target['blocks'][0]['content'][0]['v'] = text
            with self.subTest(text=text[:70]), self.assertRaises(TranslationError): validate_translation(source, target, 'zh-Hans')

    def test_codex_subscription_command_and_output_are_injected(self):
        from studio.translation import CodexCLITranslator, make_request
        translator = CodexCLITranslator(timeout=37)
        request = make_request(DOC); response = FakeProvider().generate(request)
        def run(command, **kwargs):
            self.assertEqual(command[:2], ['codex', 'exec'])
            self.assertIn('gpt-6.1-sol', command)
            self.assertIn('--ephemeral', command); self.assertIn('read-only', command)
            self.assertNotIn('OPENAI_API_KEY', kwargs['env']); self.assertNotIn('GH_TOKEN', kwargs['env'])
            Path(command[command.index('--output-last-message') + 1]).write_text(json.dumps(response))
            return SimpleNamespace(returncode=0, stdout='ignored events')
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only', 'GH_TOKEN': 'test-only'}), patch('studio.translation.subprocess.run', side_effect=run):
            self.assertEqual(translator.generate(request), response)

    def test_correction_note_is_written_once_and_translated_before_amend(self):
        slug = self.source(); translate(self.store, slug, 'javier', 1, FakeProvider())
        self.store.db.execute("UPDATE pieces SET state='published' WHERE slug=?", (slug,)); self.store.db.commit()
        note = 'OpenAI cambió 42 pruebas.'
        with patch('studio.translation.configured_provider', return_value=FakeProvider()):
            self.store.amend(slug, 'javier', 'clarification', {'es-419': note})
        correction = self.store.payload(slug)['piece']['corrections'][-1]
        self.assertEqual(set(correction['note']), {'en', 'es-419', 'zh-Hans'})
        self.assertEqual(correction['note']['es-419'], note)

    def test_figure_labels_are_translated_with_the_piece(self):
        slug = self.source()
        figure = {'file': 'figures/fig-one.webp', 'width': 1, 'height': 1, 'credit': 'FCMO', 'licence': 'CC BY 4.0',
                  'alt': {'es-419': '42 pruebas'}, 'caption': {'es-419': 'OpenAI presenta 42 pruebas'}}
        self.store.resource(slug, 'figures', 'javier', {'fig-one': figure})
        translate(self.store, slug, 'javier', self.store.piece(slug)['head_rev'], FakeProvider())
        figure = self.store.payload(slug)['figures']['fig-one']
        for field in ('alt', 'caption'):
            self.assertEqual(set(figure[field]), {'en', 'es-419', 'zh-Hans'})
            for text in figure[field].values(): self.assertIn('42', text)

    def test_machine_checked_editions_reach_dry_run_email_in_all_locales_once(self):
        from datetime import datetime, timezone
        from tools.email_piece_dispatch import PieceEdition, dispatch_piece
        from tools.email_providers.fake import FakeProvider as MailFixture
        slug = self.source(); translate(self.store, slug, 'javier', 1, FakeProvider())
        self.store.locale_state(slug, 'es-419', 'javier', 'ready', True)
        payload = self.store.payload(slug)
        piece = {**payload['piece'], **{key: payload[key] for key in ('docs', 'sources', 'figures', 'provenance')}}
        edition = PieceEdition(piece, {'site_url': 'https://example.org/paper'}, datetime.now(timezone.utc))
        provider = MailFixture({})
        outcome = dispatch_piece(provider, edition, enabled=True, live_verified=True)
        self.assertEqual({loc: result['action'] for loc, result in outcome['locales'].items()},
                         {'en': 'QUEUED', 'es-419': 'QUEUED', 'zh-Hans': 'QUEUED'})
        dispatch_piece(provider, edition, enabled=True, live_verified=True)
        self.assertEqual(len(provider.sent), 3)

    def test_source_figure_edit_invalidates_and_regenerates_labels(self):
        from studio.translation import prepare
        slug = self.source()
        figure = {'file': 'figures/fig-one.webp', 'width': 1, 'height': 1, 'credit': 'FCMO', 'licence': 'CC BY 4.0',
                  'alt': {'es-419': '42 pruebas'}, 'caption': {'es-419': 'OpenAI presenta 42 pruebas'}}
        self.store.resource(slug, 'figures', 'javier', {'fig-one': figure})
        translate(self.store, slug, 'javier', self.store.piece(slug)['head_rev'], FakeProvider())
        figures = self.store.resource(slug, 'figures')
        figures['fig-one']['caption']['es-419'] = 'OpenAI presenta 42 pruebas nuevas'
        self.store.resource(slug, 'figures', 'javier', figures)
        self.assertTrue(self.store.piece(slug)['locales']['zh-Hans']['source_changed'])
        prepare(self.store, slug, 'javier', FakeProvider())
        self.assertIn('nuevas', self.store.resource(slug, 'figures')['fig-one']['caption']['zh-Hans'])


if __name__ == '__main__': unittest.main()
