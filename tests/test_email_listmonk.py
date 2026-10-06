"""Offline failures exercise durable dispatch, consent, and provider contracts."""
import copy
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tools.email_listmonk import ListmonkClient, DiarioService, MailConfig, DeliveryError
from tools.email_render import render_daily_email
from tools.paper.templates.subscribe import subscribe_block

ROOT = Path(__file__).resolve().parents[1]


class FakeListmonk:
    def __init__(self):
        self.campaigns = []
        self.subscriptions = []
        self.lose_create = False
        self.lose_start = False
        self.lists = [{'id': n, 'uuid': f'00000000-0000-4000-8000-{n:012d}',
                       'name': f'diario-{locale}', 'type': 'public', 'optin': 'double'}
                      for n, locale in enumerate(('en', 'es-419', 'zh-Hans'), 1)]

    def request(self, method, path, payload=None, *, public=False):
        if path == 'lists?per_page=all':
            return {'results': self.lists}
        if path == 'templates':
            return [{'id':10,'name':'FCMO Diario raw HTML','type':'campaign','body':'{{ template "content" . }}'}]
        if path.startswith('campaigns?'):
            return {'results': self.campaigns, 'total': len(self.campaigns)}
        if path == 'campaigns' and method == 'POST':
            campaign = dict(payload, id=len(self.campaigns)+1, status='draft', sent=0, started_at=None)
            self.campaigns.append(campaign)
            if self.lose_create:
                self.lose_create = False
                raise DeliveryError('unknown_provider_outcome')
            return campaign
        if path.endswith('/status'):
            campaign = self.campaigns[int(path.split('/')[1])-1]
            campaign['status'] = 'running'
            campaign['started_at'] = '2026-10-05T14:00:00Z'
            if self.lose_start:
                self.lose_start = False
                raise DeliveryError('unknown_provider_outcome')
            return campaign
        if path.startswith('campaigns/'):
            return self.campaigns[int(path.split('/')[1])-1]
        if path == 'public/subscription':
            self.subscriptions.append(payload)
            return {'has_optin': True}
        raise AssertionError((method, path, payload))


class ListmonkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.provider = FakeListmonk()
        self.stories = json.loads((ROOT/'contracts/fixtures/stories.v2.json').read_text())
        for story in self.stories['stories']:
            story['first_published_at'] = '2026-10-05T12:00:00Z'
            story['l10n']['zh-Hans'] = copy.deepcopy(story['l10n']['es-419'])
            story['l10n']['zh-Hans']['fields'].update(headline='人工智能新闻', summary='研究摘要', why_it_matters='重要性')
        self.status = {'edition_state': 'FRESH', 'edition_date': '2026-10-05'}
        self.config = MailConfig('http://127.0.0.1:9000', 'test', 'token',
                                 'http://127.0.0.1:9010', 'FCMO <daily@example.org>',
                                 'Test postal address', 'https://example.org', 'x'*40)
        self.client = ListmonkClient(self.config)
        self.client.request = self.provider.request
        self.now = datetime(2026, 10, 5, 14, tzinfo=timezone.utc)
        self.service = DiarioService(self.config, Path(self.tmp.name)/'state.sqlite', client=self.client)

    def send(self, verified=True):
        return self.service.dispatch(self.stories, self.status, live_verified=verified, now=self.now)

    def test_unverified_stale_and_early_never_create_campaign(self):
        self.assertEqual(self.send(False)['action'], 'SKIP')
        self.status['edition_state'] = 'DELAYED'
        self.assertEqual(self.send()['action'], 'SKIP')
        self.assertEqual(self.provider.campaigns, [])

    def test_repeat_and_restart_do_not_duplicate_any_locale(self):
        self.assertEqual(self.send()['action'], 'QUEUED')
        self.service = DiarioService(self.config, Path(self.tmp.name)/'state.sqlite', client=self.client)
        self.assertEqual(self.send()['action'], 'SKIP')
        self.assertEqual(len(self.provider.campaigns), 3)
        self.assertEqual({c['name'] for c in self.provider.campaigns},
                         {'diario-2026-10-05-'+l for l in ('en','es-419','zh-Hans')})
        for campaign in self.provider.campaigns:
            self.assertIn('{{ UnsubscribeURL }}', campaign['body'])
            self.assertNotIn('TrackView', campaign['body'])
            self.assertEqual(campaign['type'], 'regular')

    def test_lost_create_ack_reconciles_existing_draft(self):
        self.provider.lose_create = True
        with self.assertRaises(DeliveryError): self.send()
        self.assertEqual(self.send()['action'], 'QUEUED')
        self.assertEqual(len(self.provider.campaigns), 3)

    def test_lost_start_ack_does_not_start_again(self):
        self.provider.lose_start = True
        with self.assertRaises(DeliveryError): self.send()
        self.assertEqual(self.send()['action'], 'QUEUED')
        self.assertEqual(len(self.provider.campaigns), 3)

    def test_unknown_create_with_no_provider_record_blocks_retry(self):
        def lost(method, path, payload=None, **kwargs):
            if path == 'campaigns': raise DeliveryError('unknown_provider_outcome')
            return self.provider.request(method, path, payload, **kwargs)
        self.client.request = lost
        with self.assertRaises(DeliveryError): self.send()
        self.client.request = self.provider.request
        with self.assertRaisesRegex(DeliveryError, 'reconcile'): self.send()

    def test_missing_locale_or_single_optin_fails_before_first_send(self):
        from tools.email_dispatch import eligibility
        selected = eligibility(self.stories,self.status,live_verified=True,now=self.now).items[0]['story']
        selected['l10n']['zh-Hans']['state'] = 'PENDING'
        with self.assertRaises(ValueError): self.send()
        self.assertEqual(self.provider.campaigns, [])
        selected['l10n']['zh-Hans']['state'] = 'NATIVE_ARB'
        self.provider.lists[0]['optin'] = 'single'
        with self.assertRaises(DeliveryError): self.send()
        self.assertEqual(self.provider.campaigns, [])

    def test_consent_is_required_and_no_preconfirmation_is_possible(self):
        with self.assertRaises(ValueError):
            self.service.subscribe('reader@example.org', 'es-419', False, '127.0.0.1', self.now)
        self.service.subscribe('reader@example.org', 'es-419', True, '127.0.0.1', self.now)
        self.assertEqual(self.provider.subscriptions[0]['list_uuids'], [self.provider.lists[1]['uuid']])
        self.assertNotIn('preconfirm_subscriptions', self.provider.subscriptions[0])
        self.assertNotIn('reader@example.org', (Path(self.tmp.name)/'state.sqlite').read_bytes().decode('latin1'))

    def test_signup_rate_limit_and_invalid_locale(self):
        with self.assertRaises(ValueError):
            self.service.subscribe('reader@example.org', 'xx', True, '127.0.0.1', self.now)
        for _ in range(2): self.service.subscribe('reader@example.org', 'en', True, '127.0.0.1', self.now)
        with self.assertRaises(DeliveryError):
            self.service.subscribe('reader@example.org', 'en', True, '127.0.0.1', self.now)

    def test_native_rendering_does_not_inject_go_templates(self):
        for locale, language, phrase in [('en','en','Why it matters'), ('es-419','es-MX','Por qué importa'), ('zh-Hans','zh-Hans','为什么重要')]:
            mail = render_daily_email(self.stories, '2026-10-05', locale=locale)
            self.assertIn('lang="'+language+'"', mail.html)
            self.assertIn(phrase, mail.html)
        selected = next(v for v in self.stories['stories'] if v['l10n']['es-419']['state'] in ('NATIVE_ARB','MACHINE_REVIEWED'))
        selected['l10n']['es-419']['fields']['headline'] = '{{ UnsubscribeURL }} <script>'
        mail = render_daily_email(self.stories, '2026-10-05')
        self.assertNotIn('{{ UnsubscribeURL }}', mail.html)
        self.assertNotIn('<script>', mail.html)

    def test_active_site_form_all_locales_and_no_credentials(self):
        with patch.dict('os.environ', {'FCMO_EMAIL_PUBLIC_URL':'https://mail.example.org'}, clear=True):
            for locale in ('en','es-419','zh-Hans'):
                html = subscribe_block('paper', locale, page=True)
                self.assertIn('<form', html)
                self.assertIn('https://mail.example.org/subscribe', html)
                self.assertIn('name="consent"', html)
                self.assertIn('name="locale"', html)
                self.assertIn('/privacy/', html)
                self.assertNotIn('api_key', html)

    def test_duplicate_campaigns_and_paused_campaign_fail_closed(self):
        self.send()
        self.provider.campaigns.append(dict(self.provider.campaigns[0]))
        with self.assertRaises(DeliveryError): self.send()

    def test_paused_campaign_cannot_be_restarted_implicitly(self):
        self.send()
        self.provider.campaigns[0]['status']='paused'
        with self.assertRaises(DeliveryError):self.send()

    def test_modified_template_stops_all_campaigns(self):
        original=self.client.request
        def modified(method,path,payload=None,**kwargs):
            if path=='templates':return [{'id':10,'name':'FCMO Diario raw HTML','type':'campaign','body':'{{ TrackView }}'}]
            return original(method,path,payload,**kwargs)
        self.client.request=modified
        with self.assertRaises(DeliveryError):self.send()
        self.assertEqual(self.provider.campaigns,[])

    def test_concurrent_service_instances_share_dispatch_lease(self):
        from concurrent.futures import ThreadPoolExecutor
        another=DiarioService(self.config,Path(self.tmp.name)/'state.sqlite',client=self.client)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(s.dispatch,self.stories,self.status,live_verified=True,now=self.now) for s in (self.service,another)]
            results=[future.result() for future in futures]
        self.assertEqual(sorted(r['action'] for r in results),['QUEUED','SKIP'])
        self.assertEqual(len(self.provider.campaigns),3)


if __name__ == '__main__': unittest.main()
