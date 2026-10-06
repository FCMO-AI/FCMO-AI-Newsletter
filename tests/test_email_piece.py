"""L28b red-first acceptance and recovery tests; providers are loopback fixtures."""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from harness.email_piece import LOCALES, piece_fixture
from harness.mock_kit import MockKit
from harness.mock_brevo import MockBrevo
from test_email_providers import ENV, BREVO_ENV
from tools.email_listmonk import DeliveryError
from tools.email_providers import create_provider

NOW = datetime(2026, 10, 6, 14, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


class PieceRenderTests(unittest.TestCase):
    def render(self, piece=None, locale='en'):
        from tools.email_render import render_piece_email
        return render_piece_email(piece or piece_fixture(), locale=locale,
                                  site_url='https://example.org/paper',
                                  postal_address='Synthetic postal address',
                                  unsubscribe_url='{{ unsubscribe_url }}')

    def test_three_locales_all_piece_kinds_byline_and_web_link(self):
        for kind in ('letter', 'essay', 'note'):
            for locale, prefix in [('en', ''), ('es-419', 'es/'), ('zh-Hans', 'zh/')]:
                with self.subTest(kind=kind, locale=locale):
                    piece = piece_fixture(); piece['kind'] = kind
                    mail = self.render(piece, locale)
                    self.assertIn(piece['docs'][locale]['title'], mail.subject)
                    self.assertIn('Javier Castellanos Peña', mail.html)
                    self.assertIn('Javier Castellanos Peña', mail.text)
                    self.assertIn(f'https://example.org/paper/{prefix}cartas/a-careful-decision/', mail.html)
                    self.assertIn('max-width:640px', mail.html)
                    self.assertIn('{{ unsubscribe_url }}', mail.html)

    def test_endnotes_numbered_in_reference_order_with_links(self):
        piece = piece_fixture(); doc = piece['docs']['en']
        doc['footnotes'] = {'fn-12345678': [{'t': 'text', 'v': 'Second note'}], **doc['footnotes']}
        doc['blocks'][0]['content'].append({'t': 'fn', 'id': 'fn-12345678'})
        mail = self.render(piece)
        self.assertIn('href="#endnote-1">1</a>', mail.html)
        self.assertIn('id="endnote-1"', mail.html)
        self.assertIn('https://example.org/note', mail.html)
        self.assertIn('[1]', mail.text)
        self.assertLess(mail.html.index('id="endnote-1"'), mail.html.index('Second note'))
        self.assertIn('https://example.org/source', mail.text)

    def test_brand_rule_and_editorial_template_escaping(self):
        piece = piece_fixture()
        piece['docs']['en']['blocks'][0]['content'][0]['v'] = '<script>{{danger}}</script>'
        mail = self.render(piece)
        self.assertIn('&lt;script&gt;&#123;&#123;danger', mail.html)
        self.assertNotIn('<script>', mail.html)
        self.assertIn('fCMO', mail.html)
        self.assertNotIn('FCMO Group', mail.html + mail.subject + mail.text)
        piece['docs']['en']['title'] = 'FCMO Group'
        with self.assertRaises(ValueError): self.render(piece)

    def test_rejects_missing_note_unknown_node_and_unsafe_link(self):
        for change in ('missing_note', 'node', 'link'):
            piece = piece_fixture(); doc = piece['docs']['en']
            if change == 'missing_note': doc['footnotes'] = {}
            elif change == 'node': doc['blocks'][0]['type'] = 'script'
            else: doc['footnotes']['fn-87654321'][1]['href'] = 'javascript:alert(1)'
            with self.subTest(change=change), self.assertRaises(ValueError): self.render(piece)

    def test_all_closed_document_block_types_preserve_content(self):
        piece = piece_fixture(); doc = piece['docs']['en']
        for n, kind in enumerate(('h2', 'h3', 'blockquote', 'pullquote', 'ol', 'hr', 'evidence', 'figure'), 3):
            block = {'id': f'b-{n:08x}', 'type': kind}
            if kind in ('h2', 'h3', 'blockquote', 'pullquote'): block['content'] = [{'t': 'text', 'v': kind}]
            if kind == 'ol': block['items'] = [[{'t': 'text', 'v': 'ordered item'}]]
            if kind == 'evidence': block['attrs'] = {'class': 'B', 'confidence': 'Moderate', 'limits': [{'t': 'text', 'v': 'Scope matters'}]}
            if kind == 'figure': block['attrs'] = {'fig': 'cover'}
            doc['blocks'].append(block)
        piece['figures']['cover'] = {'file': 'figures/cover.webp', 'width': 640, 'height': 320,
                                    'credit': 'FCMO', 'licence': 'CC BY 4.0',
                                    'alt': {'en': 'A diagram'}, 'caption': {'en': 'Figure caption'}}
        mail = self.render(piece)
        for value in ('Scope matters', 'Figure caption', 'CC BY 4.0', 'ordered item', 'blockquote'):
            self.assertIn(value, mail.text)
        self.assertIn('https://example.org/paper/editorial/pieces/a-careful-decision/figures/cover.webp', mail.html)


class PieceDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.piece = piece_fixture()
        self.intent = self.root / 'email-intent.json'

    def edition(self, seed=False):
        from tools.email_piece_dispatch import PieceEdition
        return PieceEdition(self.piece, {}, NOW, 'fcmo-diario-test' if seed else 'fcmo-diario')

    def prepare(self, edition, previous=()):
        from tools.email_intent import prepare_keys
        prepare_keys([edition.key(locale) for locale in edition.sendable()], previous, self.intent)

    def dispatch(self, provider, edition, **kwargs):
        from tools.email_piece_dispatch import dispatch_piece
        return dispatch_piece(provider, edition, enabled=kwargs.get('enabled', True),
                              live_verified=kwargs.get('live_verified', True))

    def kit(self, server, **env):
        return create_provider(dict(ENV, **env), base_url=server.url, intent=self.intent, sleep=lambda _: None)

    def test_unreviewed_locale_is_skipped_and_rerun_creates_zero(self):
        self.piece['provenance']['zh-Hans']['human_reviewed'] = False
        edition = self.edition(); self.prepare(edition)
        with MockKit() as server:
            result = self.dispatch(self.kit(server), edition)
            self.assertEqual(result['locales']['zh-Hans']['reason'], 'human_review_required')
            self.assertEqual(len(server.broadcasts), 2)
            result = self.dispatch(self.kit(server), edition)
            self.assertEqual(len(server.broadcasts), 2)
            for locale, tag in [('en', 11), ('es-419', 12)]:
                broadcast = next(b for b in server.broadcasts if b['description'] == 'fcmo-piece:'+self.piece['id']+':'+locale)
                self.assertEqual(broadcast['subscriber_filter'], [{'all': [{'type': 'tag', 'ids': [tag]}]}])
                self.assertEqual(result['locales'][locale]['id'], broadcast['id'])
                self.assertIn(self.piece['docs'][locale]['title'], broadcast['content'])

    def test_disabled_unverified_draft_missing_flag_and_future_send_nothing(self):
        with MockKit() as server:
            provider = self.kit(server)
            self.dispatch(provider, self.edition(), enabled=False)
            self.dispatch(provider, self.edition(), live_verified=False)
            self.piece.pop('distribution'); self.dispatch(provider, self.edition())
            self.piece['distribution'] = {'email': True}; self.piece['status'] = 'draft'
            self.dispatch(provider, self.edition())
            self.piece['status'] = 'published'; self.piece['first_published_at'] = '2027-01-01T00:00:00Z'
            self.dispatch(provider, self.edition())
            self.assertEqual(server.calls, [])

    def test_seed_is_separate_never_syncs_public_forms_and_checks_isolation(self):
        edition = self.edition(seed=True); self.prepare(edition)
        with MockKit() as server:
            server.subscriber_tags[1] = {11, 12, 13}
            self.dispatch(self.kit(server, KIT_TEST_SUBSCRIBER_ID='1'), edition)
            self.assertEqual(len(server.broadcasts), 3)
            self.assertTrue(all(b['description'].startswith('fcmo-piece-test:') for b in server.broadcasts))
            self.assertFalse(any(c[0] == 'POST' and c[1] != '/v4/broadcasts' for c in server.calls))
            server.subscribers.append(dict(server.subscribers[0], id=2))
            with self.assertRaises(DeliveryError): self.dispatch(self.kit(server, KIT_TEST_SUBSCRIBER_ID='1'), edition)

    def test_lost_ack_and_restored_absent_campaign_never_repeat_post(self):
        edition = self.edition(); self.prepare(edition)
        with MockKit() as server:
            server.lose_create = True
            self.dispatch(self.kit(server), edition)
            self.dispatch(self.kit(server), edition)
            self.assertEqual(len(server.broadcasts), 3)
        prior = json.loads(self.intent.read_text()); self.prepare(edition, [prior])
        with MockKit() as server:
            result = self.dispatch(self.kit(server), edition)
            self.assertEqual(result['locales']['en']['action'], 'BLOCKED')
            self.assertFalse(any(c[0] == 'POST' and c[1] == '/v4/broadcasts' for c in server.calls))

    def test_brevo_and_fake_use_the_same_piece_contract(self):
        edition = self.edition(); self.prepare(edition)
        with MockBrevo() as server:
            provider = create_provider(BREVO_ENV, base_url=server.url, intent=self.intent, sleep=lambda _: None)
            self.dispatch(provider, edition); self.dispatch(provider, edition)
            self.assertEqual(len(server.campaigns), 3)
        provider = create_provider(dict(ENV, FCMO_EMAIL_PROVIDER='fake'))
        self.dispatch(provider, edition); self.dispatch(provider, edition)
        self.assertEqual(len(provider.sent), 3)

    def test_public_records_are_content_free_and_preserve_confirmed_state(self):
        from tools.email_piece_dispatch import record_dispatch
        edition = self.edition(); self.prepare(edition)
        with MockKit() as server:
            result = self.dispatch(self.kit(server), edition)
            records = record_dispatch([], edition, result)
            self.assertEqual(len(records), 3)
            for record in records:
                self.assertEqual(set(record), {'piece_id', 'locale', 'state', 'broadcast_id', 'timestamp'})
                self.assertEqual(record['state'], 'QUEUED')
            self.piece['provenance']['en']['human_reviewed'] = False
            result = self.dispatch(self.kit(server), edition)
            updated = record_dispatch(records, edition, result)
            self.assertEqual(next(r for r in updated if r['locale'] == 'en')['state'], 'QUEUED')
            self.assertNotIn('reader@example.org', json.dumps(updated))


class PieceWorkflowTests(unittest.TestCase):
    def test_durable_intent_is_written_and_uploaded_before_send(self):
        import yaml
        doc = yaml.safe_load((ROOT / '.github/workflows/dispatch-pieces.yml').read_text())
        steps = doc['jobs']['dispatch']['steps']
        claim = next(i for i,s in enumerate(steps) if '--claim' in s.get('run', ''))
        upload = next(i for i,s in enumerate(steps) if 'upload-artifact' in s.get('uses', ''))
        send = next(i for i,s in enumerate(steps) if '--send' in s.get('run', ''))
        self.assertLess(claim, upload); self.assertLess(upload, send)
        self.assertEqual(steps[upload]['with']['if-no-files-found'], 'error')
        self.assertEqual(doc['concurrency']['group'], 'fcmo-daily-email')
        self.assertIn('FCMO_EMAIL_ENABLED', doc['jobs']['dispatch']['if'])
