"""Subscription states and locale delivery, with private provider fixtures only."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.email_providers import SubscribeForm
from tools.paper.templates.subscribe import diario_form

ROOT = Path(__file__).resolve().parents[1]

class SubscriptionJourneyTests(unittest.TestCase):
    def test_form_has_pending_target_errors_and_language_links_in_each_locale(self):
        for loc in ('en', 'es-419', 'zh-Hans'):
            with self.subTest(loc=loc):
                form = SubscribeForm('https://app.kit.com/forms/123/subscriptions', 'email_address', True,
                                     'https://example.org/privacy', 'https://example.org/signup')
                html = diario_form(loc, '/paper/', form, page=True)
                self.assertIn('data-state="idle"', html)
                self.assertIn('role="alert"', html)
                self.assertIn('data-sub-pending', html)
                self.assertIn('data-email-confirmation="opaque"', html)
                self.assertNotIn('select name="locale"', html)
                self.assertNotIn('style=', html)
                self.assertEqual(html.count('hreflang='), 2)

    def test_opaque_confirmation_is_only_enabled_for_validated_kit_action(self):
        for action in ('https://example.org/signup', 'http://app.kit.com/forms/123/subscriptions',
                       'https://app.kit.com.evil.invalid/forms/123/subscriptions'):
            form = SubscribeForm(action, 'email_address', True, 'https://example.org/privacy')
            with self.subTest(action=action):
                self.assertNotIn('data-email-confirmation="opaque"', diario_form('en', '/paper/', form))

    def test_real_builder_emits_subscription_states_with_noindex_and_site_shell(self):
        from tools.paper.build import PaperBuilder
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'FCMO_EMAIL_ENABLED': 'false'}, clear=True):
            out = Path(tmp) / 'site'
            PaperBuilder(stories_path=ROOT / 'contracts/fixtures/stories.v2.json',
                         status_path=ROOT / 'contracts/fixtures/newsroom-status.fresh.json', out=out, base='/paper/').build()
            for prefix, lang in (('', 'en'), ('es/', 'es-419'), ('zh/', 'zh-Hans')):
                for route in ('subscribe/', 'subscribe/check-inbox/', 'subscribed/', 'unsubscribed/'):
                    page = out / prefix / route / 'index.html'
                    self.assertTrue(page.is_file(), page)
                    html = page.read_text()
                    self.assertIn('site-header', html); self.assertIn('lang="' + lang + '"', html)
                    if route != 'subscribe/': self.assertIn('name="robots" content="noindex"', html)

    def test_status_distinguishes_pending_active_suppressed_and_unread_without_addresses(self):
        from studio.server.subscriptions import status
        class Fixture:
            name = 'fake'
            def list_subscribers(self):
                return iter([{'email_address': 'fixture@example.org', 'state': state, 'locales': [loc]}
                             for state, loc in (('inactive', 'en'), ('active', 'es-419'), ('cancelled', 'zh-Hans'))])
        result = status(Fixture())
        self.assertEqual(result['locales']['en']['pending'], 1)
        self.assertEqual(result['locales']['es-419']['confirmed'], 1)
        self.assertEqual(result['locales']['zh-Hans']['suppressed'], 1)
        self.assertNotIn('fixture@example.org', json.dumps(result))
        class Broken(Fixture):
            def list_subscribers(self): raise OSError('private detail must not escape')
        unread = status(Broken())
        self.assertEqual(unread['state'], 'unread')
        self.assertEqual(unread['locales']['en']['confirmed'], '?')
        self.assertNotIn('private detail', json.dumps(unread))

    def test_kit_state_observation_reads_opt_in_and_unsubscribe_without_writes(self):
        from harness.mock_kit import MockKit
        from tools.email_providers.kit import KitProvider
        from studio.server.subscriptions import status
        env = {'KIT_API_KEY': 'synthetic-key', 'KIT_FORM_EN': '101', 'KIT_FORM_ES': '102', 'KIT_FORM_ZH': '103',
               'KIT_TAG_EN': '11', 'KIT_TAG_ES': '12', 'KIT_TAG_ZH': '13'}
        with MockKit() as server:
            en = dict(server.subscribers[0], id=1, state='inactive')
            es = dict(server.subscribers[0], id=2, state='active')
            zh = dict(server.subscribers[0], id=3, state='cancelled')
            server.subscribers = [en, es, zh]
            server.form_members = {101: [en], 102: [es], 103: [zh]}
            provider = KitProvider(env, base_url=server.url, sleep=lambda _: None)
            observed = status(provider)
            self.assertEqual(observed['locales']['en']['pending'], 1)
            self.assertEqual(observed['locales']['es-419']['confirmed'], 1)
            self.assertEqual(observed['locales']['zh-Hans']['suppressed'], 1)
            en['state'] = 'active'; es['state'] = 'cancelled'
            observed = status(provider)
            self.assertEqual(observed['locales']['en']['confirmed'], 1)
            self.assertEqual(observed['locales']['es-419']['confirmed'], 0)
            self.assertEqual(observed['locales']['es-419']['suppressed'], 1)
            self.assertTrue(all(call[0] == 'GET' for call in server.calls))
            self.assertEqual(server.broadcasts, [])

if __name__ == '__main__': unittest.main()
