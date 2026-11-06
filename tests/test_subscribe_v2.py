from __future__ import annotations

import os
import re
from collections import Counter
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
                self.assertRegex(html, r'<input\b(?=[^>]*\btype="email")(?=[^>]*\srequired(?:\s|>))[^>]*>')

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
        self.assertRegex(html, r'<a\b(?=[^>]*class="sub-error-link")(?=[^>]*href="https://example.org/signup")(?=[^>]*\shidden(?:\s|>))[^>]*>')
        self.assertNotIn('You’re subscribed', html)

    def test_form_stays_off_while_email_flag_is_false(self):
        with patch.dict(os.environ, {'FCMO_EMAIL_ENABLED': 'false', 'FCMO_EMAIL_PROVIDER': 'kit',
                                     'FCMO_EMAIL_COMPLIANCE_READY': 'true', 'FCMO_EMAIL_PRIVACY_URL': 'https://example.org/privacy'}, clear=True):
            html = subscribe_block('all', 'en', page=True)
        self.assertIn('data-subscribe-state="launch"', html); self.assertNotIn('<form', html)

    def test_pending_has_one_way_to_use_another_address(self):
        for locale in ('en', 'es-419', 'zh-Hans'):
            with self.subTest(locale=locale):
                html = self._form(locale).split('<div data-sub-pending', 1)[1]
                self.assertEqual(html.count('data-sub-retry'), 1)
                self.assertNotIn('<a ', html)

    def test_kicker_is_neutral_and_desktop_rows_do_not_use_the_column_gutter(self):
        css = (ROOT / 'site-src/assets/subscribe/subscribe.css').read_text()
        kicker = re.search(r'\.subscribe-v2 \.section-kicker\{([^}]+)', css).group(1)
        self.assertNotRegex(kicker.lower(), r'a9340e|f05a28')
        grid = re.search(r'\.sub-grid\{([^}]+)', css).group(1)
        self.assertIn('row-gap:1rem', grid)
        self.assertIn('column-gap:clamp(', grid)

    def test_intro_and_proof_share_a_column_independent_of_the_form(self):
        from html.parser import HTMLParser

        class Columns(HTMLParser):
            def __init__(self):
                super().__init__()
                self.divs = []
                self.parents = {}

            def handle_starttag(self, tag, attrs):
                if tag == 'div':
                    classes = dict(attrs).get('class', '').split()
                    for name in ('sub-copy', 'sub-proof', 'sub-ledger'):
                        if name in classes:
                            self.parents[name] = self.divs[-1]
                    self.divs.append(classes)

            def handle_endtag(self, tag):
                if tag == 'div':
                    self.divs.pop()

        for locale in ('en', 'es-419', 'zh-Hans'):
            with self.subTest(locale=locale):
                parser = Columns()
                parser.feed(self._form(locale))
                self.assertIn('sub-story', parser.parents['sub-copy'])
                self.assertIn('sub-story', parser.parents['sub-proof'])
                self.assertNotIn('sub-story', parser.parents['sub-ledger'])
                self.assertEqual(parser.divs, [])


class SubscriptionNoticeTests(unittest.TestCase):
    def test_full_notice_discloses_tracking_and_keeps_every_placeholder(self):
        notice = (ROOT / 'legal/AVISO-PRIVACIDAD-CORREO.md').read_text()
        editions = notice.split('\n---\n')
        self.assertEqual(len(editions), 3)
        for edition, pixel, clicks, images, region in zip(
                editions, ('píxel', 'pixel', '像素'), ('clics', 'clicks', '点击'),
                ('imágenes remotas', 'remote images', '远程图片'), ('EEE', 'EEA', '欧洲经济区')):
            with self.subTest(pixel=pixel):
                self.assertIn(pixel, edition)
                self.assertIn(clicks, edition)
                self.assertIn(images, edition)
                self.assertIn(region, edition)
                # Operador 10-26: responsable y domicilio los decide Javier; el aviso no propone nombre.
                self.assertNotIn('Peña Szőke', edition)
                # HEAD has eight body markers, despite the review's count of seven.
                body = edition[edition.index('## 1.'):]
                self.assertEqual(Counter(re.findall(r'\{\{\w+\}\}', body)), {
                    '{{RESPONSABLE}}': 1, '{{DOMICILIO}}': 2,
                    '{{CORREO_PRIVACIDAD}}': 4, '{{FECHA}}': 1,
                })
                self.assertEqual(len(re.findall(r'^## \d+\.', body, re.M)), 11)
        self.assertNotRegex(notice, r'no medimos|do not currently measure|目前不统计')

    def test_kit_runbook_records_domain_sender_and_activation_boundaries(self):
        guide = (ROOT / 'docs/suscripcion/LISTA-KIT-MATIAS.md').read_text()
        self.assertIn('0. **Dominio', guide)
        self.assertIn('DOMINIO_ENVIO', guide)
        self.assertIn('news.fcmo.group', guide)
        # Operador 10-26: FCMO no tiene otro dominio; no hay respaldo de envío.
        self.assertNotRegex(guide, r'DOMINIO_\w+=\S*fcmogroup')
        self.assertIn('no son de FCMO', guide)
        self.assertNotIn('hola@news.', guide)
        self.assertIn('alias', guide)
        self.assertIn('como texto', guide)
        self.assertIn('BLOQUEADO por dominio', guide)
        self.assertIn('DISEÑO PENDIENTE', guide)
        self.assertIn('nunca se activaron', guide)
        self.assertIn('COMPLIANCE_READY', guide)


if __name__ == '__main__':
    unittest.main()
