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
        if loc == 'en':
            doc['title'] = 'One test'; doc['dek'] = 'One decision with evidence'
            doc['blocks'][0]['content'][0]['v'] = 'OpenAI released GPT-6.1 with 42 artificial intelligence trials. FCMO-P-123456789abc remains unconfirmed.'
            doc['blocks'][0]['content'][1]['c'][0]['v'] = 'evidence'
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

    def test_numeric_signs_percentages_and_scientific_exponents_remain_intact(self):
        source = copy.deepcopy(DOC)
        original = 'OpenAI midió -42%, +3.5 y 1e-3.'
        source['blocks'][0]['content'][0]['v'] = original
        for text in (original.replace('-42', '42'), original.replace('42%', '42'),
                     original.replace('+3.5', '3.5'), original.replace('1e-3', '1 y 3')):
            target = copy.deepcopy(source); target['locale'] = 'en'
            target['blocks'][0]['content'][0]['v'] = text
            with self.subTest(text=text), self.assertRaises(TranslationError):
                validate_translation(source, target, 'en')

    def test_protected_names_cannot_be_reused_as_substrings_of_different_entities(self):
        source = copy.deepcopy(DOC); original = 'OpenAI probó o3 bajo FCMO-P-123456789abc.'
        source['blocks'][0]['content'][0]['v'] = original
        for text in (original.replace('OpenAI', 'OtherOpenAI'), original.replace('o3', 'o3-mini'),
                     original.replace('FCMO-P-123456789abc', 'FCMO-P-123456789abcX')):
            target = copy.deepcopy(source); target['locale'] = 'zh-Hans'
            target['blocks'][0]['content'][0]['v'] = text
            with self.subTest(text=text), self.assertRaises(TranslationError): validate_translation(source, target, 'zh-Hans')
        target['blocks'][0]['content'][0]['v'] = 'OpenAI已测o3，在FCMO-P-123456789abc下。'
        validate_translation(source, target, 'zh-Hans')
        source['blocks'][0]['content'][0]['v'] = 'OpenAI probó inteligencia artificial.'
        target['blocks'][0]['content'][0]['v'] = 'OpenAI人工智能。'
        validate_translation(source, target, 'zh-Hans')

    def test_codex_subscription_command_and_output_are_injected(self):
        from studio.translation import CodexCLITranslator, make_request
        translator = CodexCLITranslator(timeout=37)
        request = make_request(DOC); response = FakeProvider().generate(request)
        def run(command, **kwargs):
            if command == ['codex', 'login', 'status']:
                return SimpleNamespace(returncode=0, stdout='', stderr='Logged in using ChatGPT')
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

    def test_visible_figure_labels_are_bound_to_machine_review(self):
        from studio.translation import machine_reviewed
        slug = self.source()
        doc = copy.deepcopy(DOC)
        doc['blocks'].append({'id': 'b-22345678', 'type': 'figure', 'attrs': {'fig': 'fig-one'}})
        self.store.save(slug, 'es-419', 'javier', self.store.piece(slug)['head_rev'], doc, {})
        figure = {'file': 'figures/fig-one.webp', 'width': 1, 'height': 1, 'credit': 'FCMO', 'licence': 'CC BY 4.0',
                  'alt': {'es-419': '42 pruebas'}, 'caption': {'es-419': 'OpenAI presenta 42 pruebas'}}
        self.store.resource(slug, 'figures', 'javier', {'fig-one': figure})
        translate(self.store, slug, 'javier', self.store.piece(slug)['head_rev'], FakeProvider())
        payload = self.store.payload(slug); row = payload['provenance']['zh-Hans']
        self.assertTrue(machine_reviewed(row, doc, payload['docs']['zh-Hans'], payload['figures']))
        changed = copy.deepcopy(payload['figures']); changed['fig-one']['caption']['zh-Hans'] = 'OpenAI presenta 43 pruebas'
        self.assertFalse(machine_reviewed(row, doc, payload['docs']['zh-Hans'], changed))
        from tools.email_piece_dispatch import locale_reviewed
        publication = {**payload['piece'], 'docs': payload['docs'], 'provenance': payload['provenance'], 'figures': changed}
        self.assertFalse(locale_reviewed(publication, 'zh-Hans'))
        # The actual public loader/gate must accept the bound figure, then reject
        # a caption altered after approval, even when the document is unchanged.
        import shutil
        image = self.store.directory(slug) / 'figures/fig-one.webp'; image.parent.mkdir(exist_ok=True)
        shutil.copyfile(Path(__file__).parent / 'fixtures/editorial/pieces/fixture-essay/figures/fig-cover.webp', image)
        publisher = Publisher(self.store, None, None, lambda _: [{'ok': True}])
        publisher.request(slug, 'javier'); publisher.approve(slug, 'matias')
        root = Path(self.tmp.name) / 'bound-public'
        directory = root / 'editorial/pieces' / slug
        shutil.copytree(self.store.directory(slug), directory)
        piece_id = self.store.payload(slug)['piece']['id']
        for prefix in ('', 'es', 'zh'):
            route = root / prefix / 'cartas' / slug / 'index.html'; route.parent.mkdir(parents=True)
            route.write_text('<article class="essay" data-piece-id="' + piece_id + '">')
        from tools.gates import piece_valid
        piece_valid.check(root)
        from tools.paper.essays import load_editorial, render_piece
        pieces, _ = load_editorial(root / 'editorial')
        self.assertIn('figcaption', render_piece(pieces[0], 'zh-Hans', base='/')[2])
        (directory / 'figures.json').write_text(json.dumps(changed))
        from tools.gates.common import GateFailure
        with self.assertRaises(GateFailure): piece_valid.check(root)

    def test_editing_target_figure_labels_clears_review_and_rechecks_fidelity(self):
        from studio.translation import prepare
        slug = self.source(); doc = copy.deepcopy(DOC)
        doc['blocks'].append({'id': 'b-22345678', 'type': 'figure', 'attrs': {'fig': 'fig-one'}})
        self.store.save(slug, 'es-419', 'javier', self.store.piece(slug)['head_rev'], doc, {})
        figure = {'file': 'figures/fig-one.webp', 'width': 1, 'height': 1, 'credit': 'FCMO', 'licence': 'CC BY 4.0',
                  'alt': {'es-419': '42 pruebas'}, 'caption': {'es-419': 'OpenAI presenta 42 pruebas'}}
        self.store.resource(slug, 'figures', 'javier', {'fig-one': figure})
        translate(self.store, slug, 'javier', self.store.piece(slug)['head_rev'], FakeProvider())
        figures = self.store.resource(slug, 'figures'); figures['fig-one']['caption']['zh-Hans'] = 'OpenAI presenta 43 pruebas'
        self.store.resource(slug, 'figures', 'javier', figures)
        self.assertEqual(self.store.piece(slug)['locales']['zh-Hans']['review_state'], 'MACHINE_TRANSLATED')
        with self.assertRaises(TranslationError): prepare(self.store, slug, 'javier', FakeProvider())

    def test_publication_approval_cannot_substitute_for_explicit_target_review(self):
        from studio.server.publishing import Refused
        slug = self.source(); translate(self.store, slug, 'javier', 1, FakeProvider())
        payload = self.store.payload(slug)
        row = payload['provenance']['zh-Hans']
        row.update(origin='human_translated'); row.pop('fidelity'); row.pop('review_state')
        self.store._put(slug, payload, 'javier')
        publisher = Publisher(self.store, None, None, lambda value: checks(self.store, SimpleNamespace(privacy=lambda _: True), value))
        with self.assertRaises(Refused): publisher.request(slug, 'javier')

    def test_lowercase_model_alias_cannot_change_with_the_same_numeric_tokens(self):
        source = copy.deepcopy(DOC); source['locale'] = 'en'
        source['blocks'][0]['content'][0]['v'] = 'OpenAI tested o3 with 42 results and uncertainty.'
        target = copy.deepcopy(source); target['locale'] = 'es-419'
        target['blocks'][0]['content'][0]['v'] = 'OpenAI tested x3 with 42 results and uncertainty.'
        with self.assertRaises(TranslationError): validate_translation(source, target, 'es-419')

    def test_cached_api_auth_is_refused_before_any_model_call(self):
        from studio.translation import CodexCLITranslator, make_request
        request = make_request(DOC); response = FakeProvider().generate(request)
        def run(command, **kwargs):
            if command == ['codex', 'login', 'status']:
                return SimpleNamespace(returncode=0, stdout='', stderr='Logged in using an API key.')
            Path(command[command.index('--output-last-message') + 1]).write_text(json.dumps(response))
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        with patch('studio.translation.subprocess.run', side_effect=run) as execute:
            with self.assertRaisesRegex(TranslationError, 'suscripción'):
                CodexCLITranslator().generate(request)
            self.assertEqual(execute.call_count, 1)


if __name__ == '__main__': unittest.main()
