"""Source changes invalidate only their locale; publication and ACK keep working."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tests.test_localization_completeness import english_record, SPANISH_FULL, write_json
from tools import refresh_locale_identity as identity, validate_localizations as vl
from tools import apply_curated_i18n as curated

ROOT = Path(__file__).resolve().parents[1]
RID = 'FCMO-0C0DE0000001'


class LocaleSourceDrift(unittest.TestCase):
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
            self.refresh(root)
            source['limitations'].pop(0)
            root.joinpath('index.html').write_text('<script id="fcmo-data" type="application/json">' + json.dumps({'records': [source]}) + '</script>')
            self.refresh(root)
            rows, _, origins, _ = vl.load_locale_details(root / 'data/i18n', 'es-419')
            state = vl.pair_status(source, rows[RID], 'es-419', provenance=origins[RID])
            self.assertEqual(state['state'], 'PENDING')
            self.assertNotIn('limitations', state['complete_keys'])
