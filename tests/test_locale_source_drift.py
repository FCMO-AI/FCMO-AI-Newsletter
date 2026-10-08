"""Source changes invalidate only their locale; publication and ACK keep working."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import shutil

from tests.test_localization_completeness import english_record, SPANISH_FULL, write_json
from tools import refresh_locale_identity as identity, validate_localizations as vl
from tools import apply_curated_i18n as curated
from tools import newsroom_receipt, story_layer
from tools.paper import build as paper
from tools.paper.routes import story_path, output_path
from tools.reconcile_locale_overlays import prune

ROOT = Path(__file__).resolve().parents[1]
RID = 'FCMO-0C0DE0000001'


class LocaleSourceDrift(unittest.TestCase):
    def test_reconciliation_removes_changed_list_without_reassigning_its_prose(self):
        self.assertEqual(prune({'limitations': ['Second English item']},
                               {'limitations': ['Primero antiguo', 'Segundo vigente']}), {'limitations': []})

    def test_initial_migration_cannot_approve_caveat_drift_from_a_core_field_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root)
            source['limitations'][0] = 'The evaluation has now been independently reproduced.'
            root.joinpath('index.html').write_text('<script id="fcmo-data" type="application/json">'
                + json.dumps({'records': [source]}) + '</script>')
            self.refresh(root)
            rows, _, origins, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
            self.assertEqual(vl.pair_status(source, rows[RID], 'es-419', provenance=origins[RID])['state'], 'PENDING')

    def test_changed_corpus_with_unchanged_delta_carries_last_native_publication_and_fresh_ack(self):
        """Fixture runs the real source -> Story -> ACK -> static paper path."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus, site, release = root / 'corpus', root / 'site', root / 'release-src'
            shutil.copytree(ROOT / 'corpus', corpus)
            shutil.copytree(ROOT / 'site/data/i18n', site / 'data/i18n')
            shutil.copytree(ROOT / 'release-src/data', release / 'data')
            for name in ('stories.json', 'stories.v2.json'):
                shutil.copyfile(ROOT / 'site/data' / name, site / 'data' / name)
            rid = 'FCMO-9E06CC5FA8A5'
            old_native = {locale: vl.load_locale(site / 'data/i18n', locale)[0][rid]['summary']
                          for locale in vl.LOCALES}
            path = corpus / 'data/developments.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
            source = next(row for row in rows if row['id'] == rid)
            source['summary'] += ' These outcomes remain unverified after the latest correction.'
            path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            from tools import ingest_corpus
            ingest_corpus.build(corpus, release, i18n_dir=site / 'data/i18n')
            admission = json.loads((release / 'data/publication-admission.json').read_text())
            self.assertIn(rid, admission['carried_ids'])
            identity.main(['--corpus', str(corpus), '--i18n-dir', str(site / 'data/i18n')])
            inputs = story_layer.StoryInputs(corpus, None, site, site / 'data/i18n', '2026-10-07T20:00:00Z')
            doc = story_layer.build_stories(inputs)
            story = next(row for row in doc['stories'] if row['id'] == rid)
            for locale in vl.LOCALES:
                self.assertIn(story['l10n'][locale]['state'], vl.COMPLETE_STATES)
                self.assertEqual(story['l10n'][locale]['fields']['summary'], old_native[locale])
            self.assertTrue(story['carried_forward'])
            self.assertIn(rid, inputs.held_back)
            write_json(site / 'data/stories.v2.json', doc)
            write_json(site / 'data/i18n/translation-status.json', {
                'schema': 'fcmo-translation-status-v2', 'canonical_story_count': 0})
            args = type('Args', (), {'corpus': corpus, 'site': site, 'release_src': release,
                'status': site / 'data/newsroom-status.json', 'wire_status': corpus / 'wire-status.json',
                'now': '2026-10-07T20:00:00Z'})()
            self.assertEqual(newsroom_receipt.finalize(args), 0)
            ack = json.loads(args.status.read_text())
            self.assertNotIn(rid, ack['pending_translation_ids'])
            for locale in vl.LOCALES:
                counts = ack['translation'][locale]
                self.assertEqual(sum(counts[k] for k in ('complete', 'pending', 'failed')),
                                 len([s for s in doc['stories'] if s['status'] == 'live']))
            candidate = root / 'candidate'
            self.assertEqual(paper.main(['--stories', str(site / 'data/stories.v2.json'), '--status', str(args.status),
                '--out', str(candidate), '--base', '/FCMO-AI-Newsletter/']), 0)
            for code in vl.LOCALES:
                locale = next(loc for loc in json.loads((ROOT / 'config/site.json').read_text())['locales']
                              if loc['code'] == code)
                rendered = output_path(candidate, story_path(locale, story)).read_text()
                self.assertNotIn('pending-panel', rendered)
                self.assertIn(old_native[code], rendered)
            english = output_path(candidate, story_path({'path_prefix': ''}, story)).read_text()
            self.assertNotIn('These outcomes remain unverified', english)
            self.assertIn('These outcomes remain unverified', source['summary'])

    def fixture(self, root):
        source = english_record(RID)
        root.joinpath('index.html').write_text('<html><head></head><body><script id="fcmo-data" type="application/json">'
            + json.dumps({'records': [source]}) + '</script></body></html>')
        for locale in vl.LOCALES:
            ui = json.loads((ROOT / 'site/data/i18n' / locale / 'ui.json').read_text())
            ui['canonical_record_count'] = 1
            ui['canonical_source_sha256'] = identity._canonical_digest({RID: {k: source[k] for k in identity.REQUIRED_FIELDS}})
            write_json(root / 'data/i18n' / locale / 'ui.json', ui)
            write_json(root / 'data/i18n' / locale / 'part-01.json', {
                'schema': 'fcmo-curated-locale-part-v1', 'locale': locale,
                'canonical_source_sha256': ui['canonical_source_sha256'], 'records': {RID: SPANISH_FULL}})
        write_json(root / 'data/i18n/integrity-manifest.json', {'records': {RID: {
            locale: {'canonical_digest': vl.stable_digest(vl.translated_projection(source)),
                     'locale_digest': vl.stable_digest(SPANISH_FULL)} for locale in vl.LOCALES}}})
        return source

    def refresh(self, root):
        return identity.main(['--site', str(root), '--i18n-dir', str(root / 'data/i18n')])

    def test_same_shape_semantic_change_is_pending_after_repeated_metadata_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root)
            self.refresh(root)
            source['summary'] = source['summary'].replace('matches', 'fails to match')
            root.joinpath('index.html').write_text('<html><head></head><body><script id="fcmo-data" type="application/json">'
                + json.dumps({'records': [source]}) + '</script></body></html>')
            for _ in range(2):
                self.refresh(root)
                rows, strict, provenance, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
                state = vl.pair_status(source, rows[RID], 'es-419', provenance=provenance[RID])
                self.assertEqual(state['state'], 'PENDING')
                self.assertNotIn('summary', state['complete_keys'])
            # Exercise the real frozen-release assembler, not just the classifier.
            curated.apply_curated_i18n(root, hashlib.sha256(root.joinpath('index.html').read_bytes()).hexdigest())
            manifest = json.loads(root.joinpath('data/i18n/manifest.json').read_text())
            self.assertEqual(manifest['pending_translation_count'], 1)
            self.assertEqual(manifest['translation_state'], 'DEGRADED_TRANSLATION_BACKLOG')
            bundle = root.joinpath('index.html').read_text().split('id="fcmo-i18n-data" type="application/json">')[1].split('</script>')[0]
            self.assertNotIn(RID, json.loads(bundle)['packs']['es-419']['records'])

    def test_only_stale_locale_is_excluded_from_the_browser_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            self.refresh(root)
            path = root / 'data/i18n/es-419/part-01.json'
            doc = json.loads(path.read_text())
            doc['source_bindings'][RID]['summary']['source_sha256'] = '0' * 64
            write_json(path, doc)
            result = curated.validate_curated_i18n(root)
            self.assertEqual(result['pending_records'], 1)
            self.assertNotIn(RID, result['packs']['es-419']['records'])
            self.assertIn(RID, result['packs']['zh-Hans']['records'])

    def test_automated_metadata_refresh_does_not_approve_changed_locale_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root)
            self.refresh(root)
            path = root / 'data/i18n/es-419/part-01.json'
            doc = json.loads(path.read_text())
            old = copy.deepcopy(doc['source_bindings'][RID]['summary'])
            doc['records'][RID]['summary'] += ' El resultado requiere comprobación independiente.'
            write_json(path, doc)
            self.refresh(root)
            self.assertEqual(json.loads(path.read_text())['source_bindings'][RID]['summary'], old)
            rows, _, provenance, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
            self.assertEqual(vl.pair_status(source, rows[RID], 'es-419', provenance=provenance[RID])['state'], 'PENDING')
            identity.main(['--site', str(root), '--i18n-dir', str(root / 'data/i18n'), '--bind-updated-fields'])
            rows, _, provenance, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
            self.assertEqual(vl.pair_status(source, rows[RID], 'es-419', provenance=provenance[RID])['state'], 'NATIVE_ARB')

    def test_list_removal_does_not_reassociate_old_translation_by_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.fixture(root)
            source['limitations'].append('A second limitation remains unresolved.')
            native = copy.deepcopy(SPANISH_FULL)
            native['limitations'].append('Una segunda limitación sigue sin resolverse.')
            root.joinpath('index.html').write_text('<script id="fcmo-data" type="application/json">' + json.dumps({'records': [source]}) + '</script>')
            for locale in vl.LOCALES:
                path = root / 'data/i18n' / locale / 'part-01.json'
                doc = json.loads(path.read_text()); doc['records'][RID] = native; write_json(path, doc)
            write_json(root / 'data/i18n/integrity-manifest.json', {'records': {RID: {
                locale: {'canonical_digest': vl.stable_digest(vl.translated_projection(source)),
                         'locale_digest': vl.stable_digest(native)} for locale in vl.LOCALES}}})
            self.refresh(root)
            source['limitations'].pop(0)
            root.joinpath('index.html').write_text('<script id="fcmo-data" type="application/json">' + json.dumps({'records': [source]}) + '</script>')
            self.refresh(root)
            rows, _, origins, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
            state = vl.pair_status(source, rows[RID], 'es-419', provenance=origins[RID])
            self.assertEqual(state['state'], 'PENDING')
            self.assertNotIn('limitations', state['complete_keys'])
