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

    def test_active_spanish_has_two_choices_and_real_fallback(self):
        html = subscribe_block('letter', 'es-419', ghost_url='https://comunidad.example')
        self.assertIn('data-subscribe-state="active"', html)
        self.assertEqual(html.count('class="subscribe-choice '), 2)
        self.assertIn('https://comunidad.example/#/portal/signup', html)
        self.assertIn('data-ghost-portal="signup"', html)
        self.assertNotIn('<form', html)
        self.assertIn('Cambia tus preferencias', html)
        config = subscription_config()
        for product in config['products'].values():
            self.assertIn(product['name'], html)

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

    def test_letter_preview_uses_brand_and_ghost_account(self):
        letter = render_letter_email('Una idea', 'Hola <amiga>\n\nProbemos algo.',
                                     ghost_url='https://comunidad.example', postal_address='Dirección de prueba')
        self.assertIn(LETTER_NAME, letter.subject)
        self.assertIn('fCMO', letter.html)
        self.assertIn('&lt;amiga&gt;', letter.html)
        self.assertNotIn('Hola <amiga>', letter.html)
        self.assertIn('https://comunidad.example/#/portal/account', letter.html)
        self.assertIn('Dirección de prueba', letter.text)


if __name__ == '__main__':
    unittest.main()
