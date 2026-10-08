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
    def test_independent_oracle_detects_nested_and_nonidentical_english(self):
        from tests.test_localization_completeness import independent_pair_incomplete
        source = {'technical': {'claimed_result': 'An independent evaluation has not been published.'}}
        for locale in ('es-419', 'zh-Hans'):
            self.assertTrue(independent_pair_incomplete(source, source, locale))
            self.assertTrue(independent_pair_incomplete(source, {
                'technical': {'claimed_result': 'The model is a system that has not been evaluated by the team.'}
            }, locale))
            self.assertTrue(independent_pair_incomplete(source, {'technical': {}}, locale))
    def test_useful_audit_is_normalized_and_labelled_in_three_languages(self):
        row = json.loads((ROOT / 'contracts/fixtures/corpus-44/data/developments.jsonl').read_text().splitlines()[0])
        row.update(importance_tier='Useful', importance_score=3, importance_effective_score=3,
                   development_type='reproduction_or_audit')
        normalized = taxonomy.normalize_record(row)
        self.assertEqual(normalized['importance_tier'], 'Useful')
        self.assertEqual(normalized['development_type'], 'reproduction_or_audit')
        # Importance score never manufactures a tier label.
        for tier in ('Background', 'Minor', 'Useful', 'Meaningful', 'Notable', 'Major',
                     'Very major', 'Field-shifting', 'Paradigm-level', 'Alien evidence'):
            self.assertEqual(taxonomy.normalize_record(dict(row, importance_tier=tier,
                importance_score=6, importance_effective_score=6))['importance_tier'], tier)
        from tools.paper.build import PaperBuilder
        story = story_layer.story_object(normalized, {'first_published_at': '2026-10-08T12:00:00Z',
            'url_date': '2026-10-08', 'slug': 'useful-audit'}, False, None, [])
        story['topics'] = []
        story['organizations'] = []
        for loc in ('en', 'es-419', 'zh-Hans'):
            catalog = json.loads((ROOT / f'i18n/ui/{loc}.json').read_text())
            self.assertTrue(label(catalog, 'importance_tier', normalized['importance_tier']))
            self.assertTrue(label(catalog, 'development_type', normalized['development_type']))
            builder = object.__new__(PaperBuilder)
            builder.catalogs = {loc: catalog}
            rendered = builder._facts(story, {'code': loc})
            self.assertIn(f'<dd>{label(catalog, "importance_tier", "Useful")}</dd>', rendered)
            self.assertIn(f'<dd>{label(catalog, "development_type", "reproduction_or_audit")}</dd>', rendered)
            self.assertNotIn('reproduction_or_audit', rendered)

    def test_refresh_holds_nested_english_then_admits_repaired_airlock(self):
        # Real source-controlled native editions; no generated translation fixture.
        rows = [json.loads(line) for line in (ROOT / 'corpus/data/developments.jsonl').read_text().splitlines() if line]
        rid = 'FCMO-28A7A138B4E8'
        # Use an already-complete historic row for the valid second delivery.
        valid = next(r for r in rows if r['id'] == 'FCMO-FAD9D0AFD3E4')
        from tools.validate_localizations import effective_overlays_details
        packs = {loc: effective_overlays_details(loc, ROOT / 'site/data/i18n', ROOT / 'corpus')[0]
                 for loc in ('es-419', 'zh-Hans')}
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / 'corpus'
            site = Path(tmp) / 'site'
            (corpus / 'data').mkdir(parents=True)
            (corpus / 'data/relationships.jsonl').write_text('')
            incoming = copy.deepcopy(valid)
            incoming['id'] = rid
            (corpus / 'data/developments.jsonl').write_text(json.dumps(incoming) + '\n')
            for loc in packs:
                path = corpus / f'data/locales/{loc}/records.json'
                path.parent.mkdir(parents=True)
                native = copy.deepcopy(packs[loc][valid['id']])
                native['claims'][0]['text'] = incoming['claims'][0]['text']
                path.write_text(json.dumps({'schema': 'fcmo-airlocked-locale-delta-v1', 'locale': loc,
                                           'records': {rid: native}}))
            admitted, _, held = ingest_corpus.publishable_rows(corpus, [incoming], i18n_dir=site / 'data/i18n')
            self.assertEqual(admitted, [])
            self.assertIn('ENGLISH_LEAK', held[0][1])
            release = Path(tmp) / 'release-src'
            ingest_corpus.build(corpus, release, i18n_dir=site / 'data/i18n')
            self.assertFalse((release / f'data/briefs/{rid}.json').exists())
            receipt = json.loads((release / 'data/publication-admission.json').read_text())
            self.assertIn(rid, receipt['held_back'])
            inputs = story_layer.StoryInputs(corpus, None, site, site / 'data/i18n', '2026-10-08T12:00:00Z')
            self.assertEqual(story_layer.build_stories(inputs)['stories'], [])
            # Only the native delivery changes; the English source stays fixed.
            for loc in packs:
                path = corpus / f'data/locales/{loc}/records.json'
                path.write_text(json.dumps({'schema': 'fcmo-airlocked-locale-delta-v1', 'locale': loc,
                                           'records': {rid: packs[loc][valid['id']]}}))
            admitted, _, held = ingest_corpus.publishable_rows(corpus, [incoming], i18n_dir=site / 'data/i18n')
            self.assertEqual([r['id'] for r in admitted], [rid])
            self.assertEqual(held, [])
            ingest_corpus.build(corpus, release, i18n_dir=site / 'data/i18n')
            self.assertTrue((release / f'data/briefs/{rid}.json').is_file())
            self.assertIn(rid, (release / 'data/developments.json').read_text())
            inputs = story_layer.StoryInputs(corpus, None, site, site / 'data/i18n', '2026-10-09T12:00:00Z')
            self.assertEqual([s['id'] for s in story_layer.build_stories(inputs)['stories']], [rid])
            # A later narrowed delivery is pending and is held by the same rule.
            path = corpus / 'data/locales/es-419/records.json'
            path.write_text(json.dumps({'schema': 'fcmo-airlocked-locale-delta-v1', 'locale': 'es-419',
                                        'records': {rid: {'title': packs['es-419'][valid['id']]['title']}}}))
            admitted, _, held = ingest_corpus.publishable_rows(corpus, [incoming], i18n_dir=site / 'data/i18n')
            self.assertEqual(admitted, [])
            self.assertIn('es-419:PENDING', held[0][1])

    def test_refresh_runs_deploy_translation_oracle_before_commit(self):
        workflow = (ROOT / '.github/workflows/daily-refresh.yml').read_text()
        self.assertLess(workflow.index('python tests/oraculos/verificar_traduccion.py'),
                        workflow.index('git commit'))


if __name__ == '__main__':
    unittest.main()
