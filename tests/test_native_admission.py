"""Refresh admission must reject nested English and recover on a later delta."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools import ingest_corpus, story_layer, taxonomy
from tools.paper.i18n import label

ROOT = Path(__file__).resolve().parents[1]


class NativeAdmission(unittest.TestCase):
    def test_useful_audit_is_normalized_and_labelled_in_three_languages(self):
        row = json.loads((ROOT / 'contracts/fixtures/corpus-44/data/developments.jsonl').read_text().splitlines()[0])
        row.update(importance_tier='Useful', importance_score=3, importance_effective_score=3,
                   development_type='reproduction_or_audit')
        normalized = taxonomy.normalize_record(row)
        self.assertEqual(normalized['importance_tier'], 'Useful')
        self.assertEqual(normalized['development_type'], 'reproduction_or_audit')
        for loc in ('en', 'es-419', 'zh-Hans'):
            catalog = json.loads((ROOT / f'i18n/ui/{loc}.json').read_text())
            self.assertTrue(label(catalog, 'importance_tier', normalized['importance_tier']))
            self.assertTrue(label(catalog, 'development_type', normalized['development_type']))

    def test_refresh_holds_nested_english_then_admits_repaired_airlock(self):
        # Real source-controlled native editions; no generated translation fixture.
        rows = [json.loads(line) for line in (ROOT / 'corpus/data/developments.jsonl').read_text().splitlines() if line]
        rid = 'FCMO-28A7A138B4E8'
        row = next(r for r in rows if r['id'] == rid)
        # Use an already-complete historic row for the valid second delivery.
        valid = next(r for r in rows if r['id'] == 'FCMO-FAD9D0AFD3E4')
        from tools.validate_localizations import effective_overlays_details
        packs = {loc: effective_overlays_details(loc, ROOT / 'site/data/i18n', ROOT / 'corpus')[0]
                 for loc in ('es-419', 'zh-Hans')}
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / 'corpus'
            site = Path(tmp) / 'site'
            (corpus / 'data').mkdir(parents=True)
            incoming = copy.deepcopy(valid)
            incoming['id'] = rid
            incoming['claims'] = [{'label': 'CLAIMED', 'text': row['claims'][0]['text']}]
            (corpus / 'data/developments.jsonl').write_text(json.dumps(incoming) + '\n')
            for loc in packs:
                path = corpus / f'data/locales/{loc}/records.json'
                path.parent.mkdir(parents=True)
                native = copy.deepcopy(packs[loc][valid['id']])
                native['claims'] = [{'text': row['claims'][0]['text']}]
                path.write_text(json.dumps({'schema': 'fcmo-airlocked-locale-delta-v1', 'locale': loc,
                                           'records': {rid: native}}))
            admitted, _, held = ingest_corpus.publishable_rows(corpus, [incoming], i18n_dir=site / 'data/i18n')
            self.assertEqual(admitted, [])
            self.assertIn('ENGLISH_LEAK', held[0][1])
            inputs = story_layer.StoryInputs(corpus, None, site, site / 'data/i18n', '2026-10-08T12:00:00Z')
            self.assertEqual(story_layer.build_stories(inputs)['stories'], [])
            # A fresh valid EN + native delivery for the same identity clears the hold.
            incoming = dict(valid, id=rid)
            (corpus / 'data/developments.jsonl').write_text(json.dumps(incoming) + '\n')
            for loc in packs:
                path = corpus / f'data/locales/{loc}/records.json'
                path.write_text(json.dumps({'schema': 'fcmo-airlocked-locale-delta-v1', 'locale': loc,
                                           'records': {rid: packs[loc][valid['id']]}}))
            admitted, _, held = ingest_corpus.publishable_rows(corpus, [incoming], i18n_dir=site / 'data/i18n')
            self.assertEqual([r['id'] for r in admitted], [rid])
            self.assertEqual(held, [])
            inputs = story_layer.StoryInputs(corpus, None, site, site / 'data/i18n', '2026-10-09T12:00:00Z')
            self.assertEqual([s['id'] for s in story_layer.build_stories(inputs)['stories']], [rid])

    def test_refresh_runs_deploy_translation_oracle_before_commit(self):
        workflow = (ROOT / '.github/workflows/daily-refresh.yml').read_text()
        self.assertLess(workflow.index('python tests/oraculos/verificar_traduccion.py'),
                        workflow.index('git commit'))


if __name__ == '__main__':
    unittest.main()
