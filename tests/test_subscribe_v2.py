from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.paper.templates.subscribe import ghost_signup_url, subscribe_block, subscription_config
from tools.email_render import PAPER_NAME, LETTER_NAME, render_letter_email

ROOT = Path(__file__).resolve().parents[1]


class SubscribeBlockTests(unittest.TestCase):
    def test_launch_state_every_locale(self):
        for locale, label, prefix in [('en', 'Subscriptions are coming soon', ''),
                                      ('es-419', 'Las suscripciones llegarán pronto', 'es/'),
                                      ('zh-Hans', '订阅即将开放', 'zh/')]:
            with self.subTest(locale=locale), patch.dict(os.environ, {}, clear=True):
                html = subscribe_block('all', locale)
                self.assertIn(label, html)
                self.assertIn('data-subscribe-state="launch"', html)
                self.assertIn('/FCMO-AI-Newsletter/' + prefix + 'feed.xml', html)
                self.assertIn('/FCMO-AI-Newsletter/' + prefix + 'feed.json', html)
                self.assertNotIn('<form', html)
                self.assertNotIn('data-ghost-portal', html)

    def test_active_spanish_has_one_subscription_text_and_real_fallback(self):
        # CONTRACT-CHANGES.md #3: one publication, one subscription text, no product list or product names.
        html = subscribe_block('letter', 'es-419', ghost_url='https://comunidad.example')
        self.assertIn('data-subscribe-state="active"', html)
        self.assertEqual(html.count('Una sola publicación. Síguela a tu manera.'), 1)
        self.assertNotIn('subscribe-choice', html)
        self.assertIn('https://comunidad.example/#/portal/signup', html)
        self.assertIn('data-ghost-portal="signup"', html)
        self.assertNotIn('<form', html)
        self.assertIn('Cambia tus preferencias', html)
        config = subscription_config()
        for product in config['products'].values():
            self.assertNotIn(product['name'], html)

    def test_unapproved_locales_keep_feeds_when_ghost_is_ready(self):
        for locale in ('en', 'zh-Hans'):
            with self.subTest(locale=locale):
                html = subscribe_block('paper', locale, ghost_url='https://comunidad.example')
                self.assertIn('data-subscribe-state="launch"', html)
                self.assertNotIn('data-ghost-portal', html)

    def test_bad_ghost_urls_fail_closed(self):
        for value in ('http://remote.example', 'https://user:pass@example.com',
                      'https://example.com/?key=secret', 'https://example.com/ghost/api/admin/',
                      'javascript:alert(1)'):
            with self.subTest(value=value):
                self.assertIsNone(ghost_signup_url(value))
                self.assertIn('data-subscribe-state="launch"', subscribe_block('all', 'es-419', ghost_url=value))

    def test_configured_names_feed_email_renderer(self):
        self.assertEqual(PAPER_NAME, subscription_config()['products']['paper']['name'])
        self.assertEqual(subscription_config()['ghost']['membership'], 'one_site')
        # CONTRACT-CHANGES.md #4: Ghost offers one publication, not two optional newsletters.
        self.assertEqual(subscription_config()['ghost']['newsletter_choice'], 'one_publication')

    def test_letter_preview_uses_brand_and_ghost_account(self):
        letter = render_letter_email('Una idea', 'Hola <amiga>\n\nProbemos algo.',
                                     ghost_url='https://comunidad.example', postal_address='Dirección de prueba')
        self.assertIn(LETTER_NAME, letter.subject)
        self.assertIn('FCMO AI', letter.html)
        self.assertNotIn('fCMO', letter.html)
        self.assertIn('&lt;amiga&gt;', letter.html)
        self.assertNotIn('Hola <amiga>', letter.html)
        self.assertIn('https://comunidad.example/#/portal/account', letter.html)
        self.assertIn('Dirección de prueba', letter.text)

class SubscribeFormTests(unittest.TestCase):
    """The native form behind the email flag: one explicit consent, one language per page, honest states."""
    def _form(self, locale):
        from tools.email_providers import SubscribeForm
        from tools.paper.templates.subscribe import diario_form
        return diario_form(locale, '/', SubscribeForm('https://app.kit.com/forms/123/subscriptions', 'email_address', True,
                                                      'https://example.org/privacy', 'https://example.org/signup'), True)

    def test_every_locale_has_required_unchecked_consent_linking_the_notice(self):
        import re
        for locale, prefix in (('en', ''), ('es-419', 'es/'), ('zh-Hans', 'zh/')):
            with self.subTest(locale=locale):
                html = self._form(locale)
                box = re.search(r'<input type="checkbox" name="consent"[^>]*>', html).group(0)
                self.assertIn('required', box); self.assertNotIn('checked', box)
                self.assertIn('href="/' + prefix + 'privacy/"', html)
                self.assertIn('type="email"', html); self.assertIn('required', html)

    def test_language_switch_marks_current_and_links_the_other_two(self):
        for locale in ('en', 'es-419', 'zh-Hans'):
            with self.subTest(locale=locale):
                html = self._form(locale)
                self.assertEqual(html.count('aria-current="true"'), 1)
                self.assertEqual(html.count('class="sub-lang" href='), 2)

    def test_states_and_hosted_fallback_exist_without_claiming_confirmation(self):
        html = self._form('en')
        for marker in ('role="alert"', 'data-sub-pending', 'data-sub-retry', 'sub-error-link', 'data-busy="Sending'):
            self.assertIn(marker, html)
        self.assertNotIn('You’re subscribed', html)

    def test_form_stays_off_while_email_flag_is_false(self):
        with patch.dict(os.environ, {'FCMO_EMAIL_ENABLED': 'false', 'FCMO_EMAIL_PROVIDER': 'kit',
                                     'FCMO_EMAIL_COMPLIANCE_READY': 'true', 'FCMO_EMAIL_PRIVACY_URL': 'https://example.org/privacy'}, clear=True):
            html = subscribe_block('all', 'en', page=True)
        self.assertIn('data-subscribe-state="launch"', html); self.assertNotIn('<form', html)


if __name__ == '__main__':
    unittest.main()
