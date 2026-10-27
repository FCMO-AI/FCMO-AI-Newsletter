"""The privacy check says what is wrong: an unfinished piece is not a privacy finding."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from studio.server.checks import checks
from studio.server.preview import Preview
from studio.server.storage import Store
from tests.test_studio_storage import ROOT


def doc(loc):
    t = lambda v: {'t': 'text', 'v': v}
    return {'schema': 'fcmo-essay-doc-v1', 'locale': loc, 'title': 'Apagar lo que nadie usa', 'dek': 'Un caso inventado', 'footnotes': {},
            'blocks': [{'id': 'b-00000001', 'type': 'p', 'content': [t('Una empresa ficticia usa Amazon Web Services; 37 % sobra y se apaga a las 22:00.')]},
                       {'id': 'b-00000002', 'type': 'blockquote', 'content': [t('«Nadie se atreve a apagar nada»')]},
                       {'id': 'b-00000003', 'type': 'ul', 'items': [[t('uno')], [t('dos')], [t('tres')]]}]}


class PrivacyCheckTests(unittest.TestCase):
    def test_tracked_source_tree_passes_machine_path_gate(self):
        # Studio's privacy checks also run during host publication, where the
        # gate sees committed files that were untracked during a box run.
        from tools.gates.no_machine_paths import check_repo
        check_repo(ROOT)

    def privacy(self, source_ready):
        (ROOT / '_audit').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp:
            store = Store(Path(tmp) / 'data')
            try:
                slug = store.create('javier', 'essay', 'Apagar', 'es-419')['slug']
                for loc in ('es-419', 'en', 'zh-Hans'):
                    store.save(slug, loc, 'javier', store.piece(slug)['head_rev'], doc(loc), {})
                    if source_ready or loc != 'es-419':
                        store.locale_state(slug, loc, 'javier', 'ready', True, 'Leí y entiendo el texto chino')
                rows = checks(store, Preview(store, ROOT), slug)
            finally: store.close()
        return next(r for r in rows if r['id'] == 'privacy')

    def test_unfinished_source_is_explained_not_called_privacy(self):
        row = self.privacy(False)
        self.assertFalse(row['ok'])
        self.assertIn('es-419', row['plain_es']); self.assertIn('No es un problema de privacidad', row['plain_es'])
        self.assertIn('not a privacy problem', row['plain_en'])

    def test_complete_invented_piece_with_company_and_quote_passes(self):
        self.assertTrue(self.privacy(True)['ok'])

    def test_real_gate_finding_names_what_to_remove(self):
        from tools.gates.common import GateFailure
        def privacy(_):
            raise GateFailure('PERSONAL_MAILBOX', ['es/cartas/x/index.html: personal consumer mailbox detected'])
        locales = {l: {'state': 'ready'} for l in ('en', 'es-419', 'zh-Hans')}
        d = {l: doc(l) for l in locales}
        payload = {'piece': {'source_locale': 'es-419'}, 'docs': d, 'sources': [], 'figures': {}, 'provenance': {l: {'origin': 'human'} for l in d}}
        store = SimpleNamespace(payload=lambda v: payload, piece=lambda v: {'author': 'x', 'locale_states': locales})
        row = next(r for r in checks(store, SimpleNamespace(privacy=privacy), 'x') if r['id'] == 'privacy')
        self.assertFalse(row['ok']); self.assertIn('PERSONAL_MAILBOX', row['plain_es']); self.assertIn('Quítalo', row['plain_es'])

    def stub(self, privacy, cite=None):
        locales = {l: {'state': 'ready'} for l in ('en', 'es-419', 'zh-Hans')}
        d = {l: doc(l) for l in locales}
        if cite is not None:
            for x in d.values(): x['blocks'].append({'id': 'b-quote001', 'type': 'blockquote', 'attrs': {'cite': cite}, 'content': [{'t': 'text', 'v': 'x'}]})
        payload = {'piece': {'source_locale': 'es-419'}, 'docs': d, 'sources': [{'key': 'src-one'}], 'figures': {}, 'provenance': {l: {'origin': 'human'} for l in d}}
        store = SimpleNamespace(payload=lambda v: payload, piece=lambda v: {'author': 'x', 'locale_states': locales})
        return checks(store, SimpleNamespace(privacy=privacy), 'x')

    def test_quotation_source_must_be_a_source_key(self):
        rows = self.stub(lambda _: True, cite='Pedro, 2020')
        bad = [r for r in rows if r['id'].startswith('quote-source-') and not r['ok']]
        self.assertEqual(len(bad), 3)
        self.assertIn('La cita usa como fuente "Pedro, 2020", que no está en las fuentes del artículo. Escribe la atribución dentro de la cita o elige una de sus fuentes.', bad[0]['plain_es'])
        self.assertEqual(bad[0]['goto']['block_id'], 'b-quote001')
        self.assertTrue(all(r['ok'] for r in self.stub(lambda _: True, cite='src-one') if r['id'].startswith('quote-source-')))

    def test_builder_reason_reaches_the_privacy_check(self):
        from studio.server.preview import RendererUnavailable, builder_reason
        def privacy(_):
            error = RendererUnavailable('x')
            error.reason = builder_reason('ValueError: /private/path/piece: numeric or URL token mismatch in en\n')
            raise error
        row = next(r for r in self.stub(privacy) if r['id'] == 'privacy')
        self.assertFalse(row['ok'])
        self.assertIn('una cifra o un enlace de en no coincide con el original', row['plain_es'])
        self.assertNotIn('/private', row['plain_es'] + row['plain_en'])

    def test_unknown_builder_text_is_not_leaked(self):
        from studio.server.preview import builder_reason
        self.assertIsNone(builder_reason('ValueError: /p/secret-title: something with piece text\n'))


if __name__ == '__main__':
    unittest.main()
