"""Native Story coverage must be checked before canonical prose is merged."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import build_newsroom_surfaces as surfaces, story_layer
from tools.paper import i18n
from tools.paper.build import PaperBuilder

ROOT = Path(__file__).resolve().parents[1]


def story_fixture():
    return {
        'id': 'FCMO-AAAAAAAAAAAA', 'research_id': 'FCMO-AAAAAAAAAAAA',
        'slug': 'coverage-test', 'url_date': '2026-10-01', 'status': 'live',
        'title': 'The source title describes a result', 'headline': 'A distinct English headline',
        'dek': 'The English dek explains the result.', 'summary': 'The source summary describes a result.',
        'why_it_matters': 'The result matters for evidence.', 'importance_rationale': 'The ranking reflects evidence.',
        'technical': {'strongest_baseline': 'The baseline is an earlier result.'},
        'evidence': {'claims': [], 'limitations': [], 'gaps': [], 'contradictory': []},
        'related': [], 'corrections': [], 'media': None, 'sources': [],
        'beat': 'research', 'desk': 'reasoning_posttraining', 'kind': 'development',
        'event_at': '2026-10-01T18:00:00Z', 'first_published_at': '2026-10-01T18:00:00Z',
        'updated_at': '2026-10-01T18:00:00Z', 'date_precision': 'minute',
        'importance': 7, 'evidence_class': 'B', 'confidence': 'supported',
        'topics': [], 'organizations': [],
        'l10n': {'es-419': {'state': 'NATIVE_ARB', 'missing': [], 'fields': {
            'title': 'El título describe un resultado', 'summary': 'El resumen describe un resultado.',
            'why_it_matters': 'El resultado importa por la evidencia.',
            'importance_rationale': 'La clasificación refleja la evidencia.',
            'technical': {'strongest_baseline': 'La referencia es un resultado anterior.'},
        }}},
    }


class StoryFieldCoverage(unittest.TestCase):
    def test_sparse_overlay_cannot_trust_a_complete_receipt(self):
        story = story_fixture()
        self.assertFalse(i18n.is_complete(story, 'es-419'))
        status = i18n.story_locale(story, 'es-419')
        self.assertEqual(status['state'], 'PENDING')
        self.assertEqual(set(status['missing_paths']), {'headline', 'dek'})

    def test_story_builder_requires_explicit_display_variants(self):
        story = story_fixture()
        row = copy.deepcopy(story['l10n']['es-419']['fields'])
        row['_provenance'] = {key: {'origin': 'arb'} for key in row}
        status = story_layer.build_l10n(story, [row], False, False)
        self.assertEqual(status['state'], 'PENDING')
        self.assertEqual(set(status['missing']), {'headline', 'dek'})

    def test_nested_prose_caption_and_correction_title_are_required(self):
        story = story_fixture()
        fields = story['l10n']['es-419']['fields']
        fields.update(headline='Un titular distinto', dek='Una entrada distinta.')
        story['evidence']['claims'] = [{'label': 'DEMONSTRATED', 'text': 'The result is demonstrated.'}]
        fields['evidence'] = {'claims': [{}]}
        story['media'] = {'caption': 'The figure explains the result.'}
        story['corrections'] = [{'title': {'en': 'The original correction title'}, 'text': {'en': 'An English correction.'}}]
        self.assertFalse(i18n.is_complete(story, 'es-419'))
        paths = i18n.story_locale(story, 'es-419')['missing_paths']
        self.assertIn('evidence.claims[0].text', paths)
        self.assertIn('media.caption', paths)
        self.assertIn('corrections[0].title', paths)
        self.assertIn('corrections[0].text', paths)

    def test_absent_taxonomy_catalog_label_is_pending(self):
        story = story_fixture()
        story['l10n']['es-419']['fields'].update(headline='Un titular distinto', dek='Una entrada distinta.')
        catalog = copy.deepcopy(i18n.load_catalogs(ROOT)['es-419'])
        del catalog['labels']['story_status']['live']
        status = i18n.story_locale(story, 'es-419', catalog=catalog)
        self.assertEqual(status['state'], 'PENDING')
        self.assertIn('labels.story_status.live', status['missing_paths'])

    def test_paper_withholds_body_on_false_complete_and_localizes_original_link(self):
        story = story_fixture()
        builder = PaperBuilder.__new__(PaperBuilder)
        builder.catalogs = i18n.load_catalogs(ROOT)
        builder.config = json.loads((ROOT / 'config/site.json').read_text())
        builder.base = '/'; builder.base_url = 'https://example.test/'; builder.status = {}
        builder.stories = [story]; builder.live = [story]; builder.og_source = None
        builder._citation_permalink = lambda _: 'https://example.test/citation.json'
        with patch.object(builder, '_write_page') as write:
            builder._story(story, builder.config['locales'][1])
        page = write.call_args.kwargs['body']
        self.assertIn('pending-panel', page)
        self.assertIn('Leer el original en inglés', page)
        self.assertNotIn('The English dek', page)
        self.assertNotIn('English original', page)

    def test_deep_body_sections_cannot_inherit_english(self):
        story = story_fixture()
        story['l10n']['es-419']['fields'].update(headline='Un titular distinto', dek='Una entrada distinta.')
        story['body'] = {'sections': [{'heading': 'The English section', 'paragraphs': ['The English paragraph.']}]}
        story['l10n']['es-419']['fields']['body'] = {'sections': [{'heading': 'La sección traducida'}]}
        status = i18n.story_locale(story, 'es-419')
        self.assertEqual(status['state'], 'PENDING')
        self.assertIn('body.sections[0].paragraphs[0]', status['missing_paths'])

    def test_normalized_relationship_kind_keeps_native_summary(self):
        story = story_fixture()
        target = 'FCMO-BBBBBBBBBBBB'
        story['related'] = [{'id': target, 'type': 'related', 'summary': 'The English relationship.'}]
        row = {'relationships': [{'target_id': target, 'type': 'compares', 'summary': 'La relación traducida.'}]}
        fields = story_layer.locale_fields(row, story, False, False)
        self.assertEqual(fields['related'][0].get('summary'), 'La relación traducida.')

    def test_complete_receipt_has_only_reader_prose_paths(self):
        from tests.test_localization_completeness import english_record, SPANISH_FULL, RID_COMPLETE
        from tools.validate_localizations import pair_status
        status = pair_status(english_record(RID_COMPLETE), SPANISH_FULL, 'es-419',
                             provenance={key: {'origin': 'arb'} for key in SPANISH_FULL})
        self.assertEqual(status['missing_paths'], [])

    def test_untranslated_correction_is_withheld_in_notice_and_ledger(self):
        story = story_fixture()
        story['status'] = 'withdrawn'
        story['corrections'] = [{'at': '2026-10-01T18:00:00Z', 'kind': 'withdrawal',
                                 'text': {'en': 'The English correction must not masquerade as translated.'}}]
        builder = PaperBuilder.__new__(PaperBuilder)
        builder.catalogs = i18n.load_catalogs(ROOT)
        builder.config = json.loads((ROOT / 'config/site.json').read_text())
        builder.base = '/'; builder.status = {}; builder.out = Path('.')
        builder.stories = [story]; builder.live = []; builder.portal_url = None
        locale = builder.config['locales'][1]
        with patch.object(builder, '_write_page') as write:
            builder._correction_notice(story, locale)
        page = write.call_args.kwargs['body']
        self.assertNotIn(story['corrections'][0]['text']['en'], page)
        self.assertIn(builder.catalogs['es-419']['strings']['l10n']['pending_notice'], page)
        with patch.object(builder, '_write_page') as write:
            builder._simple_pages(locale)
        correction = next(call.kwargs for call in write.call_args_list if call.kwargs['kind'] == 'corrections')
        self.assertNotIn(story['corrections'][0]['text']['en'], correction['body'])

    def test_native_evidence_preserves_catalog_codes_without_english_prose(self):
        story = story_fixture()
        story['evidence']['claims'] = [{'label': 'DEMONSTRATED', 'text': 'The English evidence claim.'}]
        story['l10n']['es-419']['fields']['evidence'] = {'claims': [{'text': 'La afirmación traducida.'}]}
        builder = PaperBuilder.__new__(PaperBuilder)
        locale = {'code': 'es-419'}
        evidence = builder._localized_evidence(story, locale)
        self.assertEqual(evidence['claims'][0].get('label'), 'DEMONSTRATED')
        self.assertEqual(evidence['claims'][0]['text'], 'La afirmación traducida.')
        self.assertNotIn('The English evidence claim.', json.dumps(evidence))

    def test_machine_disclosure_link_is_localized(self):
        story = story_fixture()
        story['l10n']['es-419'].update(state='MACHINE_REVIEWED')
        story['l10n']['es-419']['fields'].update(headline='Un titular distinto', dek='Una entrada distinta.')
        builder = PaperBuilder.__new__(PaperBuilder)
        builder.catalogs = i18n.load_catalogs(ROOT)
        builder.config = json.loads((ROOT / 'config/site.json').read_text())
        builder.base = '/'; builder.base_url = 'https://example.test/'; builder.status = {}
        builder.stories = [story]; builder.live = [story]; builder.og_source = None
        builder._citation_permalink = lambda _: 'https://example.test/citation.json'
        with patch.object(builder, '_write_page') as write:
            builder._story(story, builder.config['locales'][1])
        page = write.call_args.kwargs['body']
        self.assertIn('Leer el original en inglés', page)
        self.assertNotIn('>English original</a>', page)


class LegacyStoryRoutes(unittest.TestCase):
    def test_sparse_overlay_is_pending_at_builder_boundary(self):
        brief = {'id': 'FCMO-AAAAAAAAAAAA', 'title': 'The source title explains the result',
                 'summary': 'The source summary explains the result.', 'why_it_matters': 'The result matters for evidence.',
                 'technical': {'strongest_baseline': 'The baseline is an earlier result.'},
                 'primary_desk': 'reasoning_posttraining', 'evidence_class': 'B',
                 'importance_score': 7, 'event_at': '2026-10-01T18:00:00Z'}
        overlay = {'title': 'El título explica el resultado', 'summary': 'El resumen explica el resultado.',
                   'why_it_matters': 'El resultado importa por la evidencia.'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'release-src'; site = root / 'site'
            (source / 'data/briefs').mkdir(parents=True)
            (source / 'data/briefs' / (brief['id'] + '.json')).write_text(json.dumps({'brief': brief}))
            (source / 'data/media.json').write_text('[]')
            for locale in ('es-419', 'zh-Hans'):
                folder = site / 'data/i18n' / locale; folder.mkdir(parents=True)
                (folder / 'part-001.json').write_text(json.dumps({'records': {brief['id']: overlay if locale == 'es-419' else {}}}))
            self.assertEqual(surfaces.main(['--release-src', str(source), '--site', str(site), '--now', '2026-10-01T18:00:00Z']), 0)
            page = (site / 'news/es' / (brief['id'] + '.html')).read_text()
            self.assertIn('data-l10n-state="PENDING"', page)
            self.assertIn('Leer el original en inglés', page)
            self.assertNotIn(brief['technical']['strongest_baseline'], page)
            status = json.loads((site / 'data/i18n/translation-status.json').read_text())
            self.assertEqual(status['locales']['es-419']['pending'], 1)

    def test_public_receipt_accounts_for_missing_story_fields(self):
        from tests.test_localization_completeness import build_fixture, english_record, SPANISH_FULL
        from tools.mark_pending_localizations import render_pending
        story = story_fixture()
        source = english_record(story['id'])
        with tempfile.TemporaryDirectory() as tmp:
            _, site = build_fixture(Path(tmp), [source], {'es-419': {story['id']: SPANISH_FULL}})
            (site / 'data/stories.v2.json').write_text(json.dumps({'schema': 'fcmo-stories-v2', 'stories': [story]}))
            render_pending(site, {story['id']: source})
            status = json.loads((site / 'data/i18n/translation-status.json').read_text())
            self.assertEqual(status['locales']['es-419']['pending'], 1)
            self.assertEqual(status['state'], 'DEGRADED_TRANSLATION_BACKLOG')

    def test_correction_without_locale_text_is_withheld(self):
        story = story_fixture()
        story['status'] = 'withdrawn'
        story['corrections'] = [{'at': '2026-10-01T18:00:00Z', 'text': {'en': 'The original English correction.'}}]
        links = {locale: 'https://example.test/' + locale for locale in surfaces.LOCALES}
        for locale in ('es-419', 'zh-Hans'):
            with self.subTest(locale=locale):
                page = surfaces.notice_html(locale, story, links, None)
                self.assertNotIn('The original English correction.', page)
                self.assertIn(i18n.load_catalogs(ROOT)[locale]['strings']['l10n']['pending_notice'], page)

    def test_calendar_event_date_is_not_shifted_to_the_previous_day(self):
        brief = {'id': 'FCMO-AAAAAAAAAAAA', 'title': 'Título', 'summary': 'Resumen.'}
        story = {'story_type': 'STANDARD', 'published_at': '2026-10-01T18:00:00Z',
                 'event_at': '2026-10-01T00:00:00Z'}
        links = {locale: 'https://example.test/' + locale for locale in surfaces.LOCALES}
        for locale, expected in (('es-419', 'Ocurrió el 1 de octubre de 2026'),
                                 ('zh-Hans', '发生于 2026年10月1日')):
            with self.subTest(locale=locale):
                self.assertIn(expected, surfaces.article_html(locale, brief, story, links))

    def test_original_explainer_caption_uses_native_catalog(self):
        brief = {'id': 'FCMO-AAAAAAAAAAAA', 'title': 'Título', 'summary': 'Resumen.'}
        story = {'story_type': 'STANDARD', 'published_at': '2026-10-01T18:00:00Z',
                 'event_at': '2026-10-01T18:00:00Z',
                 'media': {'mode': 'fcmo_explainer', 'credit': 'FCMO AI Research Desk',
                           'license': 'FCMO original editorial graphic', 'image_url': 'figure.svg'}}
        links = {locale: 'https://example.test/' + locale for locale in surfaces.LOCALES}
        for locale in ('es-419', 'zh-Hans'):
            with self.subTest(locale=locale):
                page = surfaces.article_html(locale, brief, story, links)
                caption = page.split('<figcaption>', 1)[1].split('</figcaption>', 1)[0]
                self.assertNotIn('FCMO original editorial graphic', caption)
                self.assertIn(i18n.load_catalogs(ROOT)[locale]['strings']['story']['explainer_credit'], caption)

    def test_shell_status_taxonomy_and_dates_use_native_catalogs(self):
        brief = {'id': 'FCMO-AAAAAAAAAAAA', 'title': 'Título de la noticia', 'summary': 'Resumen de la noticia.',
                 'primary_desk': 'reasoning_posttraining'}
        story = {'story_type': 'STANDARD', 'headline': brief['title'], 'dek': brief['summary'],
                 'published_at': '2026-10-01T18:00:00Z', 'event_at': '2026-10-01T18:00:00Z'}
        links = {locale: 'https://example.test/' + locale for locale in surfaces.LOCALES}
        for locale in ('es-419', 'zh-Hans'):
            catalog = i18n.load_catalogs(ROOT)[locale]
            with self.subTest(locale=locale):
                page = surfaces.article_html(locale, brief, story, links)
                self.assertIn(catalog['labels']['story_type']['STANDARD'], page)
                self.assertIn(catalog['labels']['desk']['reasoning_posttraining'], page)
                self.assertNotIn('Published ', page)
                self.assertNotIn('Research event ', page)
                self.assertNotIn('>STANDARD', page)
                self.assertNotIn('T18:00:00Z</', page)
                index = surfaces.index_html(locale, [(story, links[locale])])
                self.assertNotIn('Published ', index)
                self.assertIn(catalog['labels']['story_type']['STANDARD'], index)


if __name__ == '__main__':
    unittest.main()
