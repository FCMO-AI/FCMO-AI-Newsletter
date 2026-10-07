"""Red-first Brevo safety and recovery acceptance at the HTTP boundary."""
import json
import os
import unittest
from unittest.mock import patch
from harness.mock_brevo import MockBrevo
import test_email_providers as contract
from test_email_providers import BREVO_ENV
from tools.email_providers import create_provider, dispatch_edition, signup_form
from tools.email_listmonk import DeliveryError


class BrevoTests(unittest.TestCase):
    setUp = contract.ProviderTests.setUp
    def provider(self, server):
        return create_provider(BREVO_ENV,base_url=server.url,intent=self.intent,sleep=lambda _:None)
    def test_locale_campaigns_restart_idempotency_and_detail(self):
        with MockBrevo() as server:
            provider = self.provider(server)
            for locale, identity in [('en',21),('es-419',22),('zh-Hans',23)]:
                self.assertEqual(provider.send_edition(self.edition,locale,self.edition.key(locale))['action'],'QUEUED')
                campaign = server.campaigns[-1]
                self.assertEqual(campaign['name'],self.edition.key(locale))
                self.assertEqual(campaign['tag'],self.edition.key(locale))
                self.assertEqual(campaign['recipients'],{'lists':[identity]})
                self.assertIn('{{ unsubscribe }}',campaign['htmlContent'])
                self.assertFalse(campaign['inlineImageActivation'])
            for locale in ('en','es-419','zh-Hans'):
                self.assertEqual(self.provider(server).send_edition(self.edition,locale,self.edition.key(locale))['action'],'SKIP')
            self.assertEqual(sum(c[1].endswith('/sendNow') for c in server.calls),3)
    def test_lost_send_ack_reconciles_queued_but_draft_blocks_resend(self):
        for status in ('queued','draft'):
            with self.subTest(status=status), MockBrevo() as server:
                self.intent.write_text(json.dumps({'keys':[self.edition.key('en')]}))
                server.lose_send = True; server.send_status = status
                provider = self.provider(server)
                if status == 'queued':
                    self.assertEqual(provider.send_edition(self.edition,'en',self.edition.key('en'))['action'],'SKIP')
                    self.assertEqual(self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))['action'],'SKIP')
                else:
                    with self.assertRaises(DeliveryError): provider.send_edition(self.edition,'en',self.edition.key('en'))
                    with self.assertRaises(DeliveryError): self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))
                self.assertEqual(sum(c[1].endswith('/sendNow') for c in server.calls),1)
    def test_lost_create_never_sends_unconfirmed_draft_or_creates_twice(self):
        with MockBrevo() as server:
            server.lose_create = True
            with self.assertRaises(DeliveryError): self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))
            with self.assertRaises(DeliveryError): self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),1)
    def test_failed_create_and_prior_intent_never_repeat(self):
        with MockBrevo() as server:
            server.failures = [('POST',503)]
            for _ in range(2):
                with self.assertRaises(DeliveryError): self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(sum(c[0]=='POST' for c in server.calls),1)
        self.intent.write_text(json.dumps({'keys':[self.edition.key('en')],'previous':[self.edition.key('en')]}))
        with MockBrevo() as server:
            with self.assertRaises(DeliveryError): self.provider(server).send_edition(self.edition,'en',self.edition.key('en'))
            self.assertFalse(any(c[0]=='POST' for c in server.calls))
    def test_wrong_filter_and_duplicate_campaign_marker_block(self):
        with MockBrevo() as server:
            provider = self.provider(server)
            provider.send_edition(self.edition,'en',self.edition.key('en'))
            server.campaigns[0]['recipients'] = {'lists':[22]}
            with self.assertRaises(DeliveryError): provider.send_edition(self.edition,'en',self.edition.key('en'))
            server.campaigns.append(dict(server.campaigns[0],id=2))
            with self.assertRaises(DeliveryError): provider.send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(sum(c[1].endswith('/sendNow') for c in server.calls),1)
    def test_master_switch_incomplete_native_and_seed_fail_before_request(self):
        with MockBrevo() as server:
            provider = self.provider(server)
            self.assertEqual(dispatch_edition(provider,self.edition,enabled=False,live_verified=True)['action'],'SKIP')
            for story in self.stories['stories']: story['l10n']['zh-Hans']['state']='PENDING'
            with self.assertRaises(ValueError): provider.send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(server.calls,[])
    def test_daily_cap_counts_locale_memberships_not_unique_contacts(self):
        with MockBrevo() as server:
            server.counts = {21:101,22:100,23:100}
            result = self.provider(server).health()
            self.assertEqual(result['status'],'warning')
            self.assertEqual(result['warnings'],['brevo_daily_cap_exceeded'])
            self.assertEqual(result['estimated_daily_emails'],301)
            server.counts[21] = 100
            self.assertEqual(self.provider(server).health()['status'],'ok')
    def test_export_preserves_blacklist_attributes_and_locale_memberships(self):
        with MockBrevo() as server:
            server.contacts.append(dict(server.contacts[0],id=2,email='blocked@example.org',emailBlacklisted=True,listIds=[22]))
            records = list(self.provider(server).list_subscribers())
            self.assertEqual(len(records),2)
            self.assertEqual(records[1]['locales'],['es-419'])
            self.assertTrue(records[1]['emailBlacklisted'])
            self.assertEqual(records[1]['attributes'],{'DOI':True})
    def test_preflight_surfaces_health_warnings_without_provider_coupling(self):
        import contextlib
        import io
        from tools.email_dispatch import main
        paths = []
        for name, document in [('stories',self.stories),('status',self.status),('receipt',{'passed':True})]:
            path = self.root/(name+'.json'); path.write_text(json.dumps(document)); paths.append(str(path))
        class FutureProvider:
            requires_intent = True
            def health(self): return {'status':'warning','provider':'future',
                                      'warnings':['daily_cap_exceeded'],'private':'secret@example.org'}
        output = io.StringIO()
        with patch.dict(os.environ,{'FCMO_EMAIL_ENABLED':'true'},clear=True), \
             patch('tools.email_providers.create_provider',return_value=FutureProvider()), \
             contextlib.redirect_stdout(output):
            self.assertEqual(main(['--check','--stories',paths[0],'--status',paths[1],
                                   '--live-verify',paths[2],'--now','2026-10-05T14:00:00Z']),0)
        self.assertIn('WARNING daily_cap_exceeded',output.getvalue())
        self.assertNotIn('secret@example.org',output.getvalue())
    def test_encrypted_export_roundtrip_keeps_suppression(self):
        import subprocess
        from tools.email_backup import encrypted_backup
        identity = self.root/'identity.txt'
        keys = subprocess.run(['age-keygen','-o',str(identity)],capture_output=True,check=True)
        recipient = keys.stderr.decode().split('Public key: ')[1].strip()
        with MockBrevo() as server:
            server.contacts[0]['emailBlacklisted'] = True
            out = self.root/'backup.age'
            encrypted_backup(self.provider(server),recipient,out)
            self.assertNotIn(b'reader@example.org',out.read_bytes())
            raw = subprocess.run(['age','-d','-i',str(identity),str(out)],capture_output=True,check=True)
            doc = json.loads(raw.stdout)
            self.assertEqual(doc['provider'],'brevo')
            self.assertTrue(doc['subscribers'][0]['emailBlacklisted'])
            self.assertEqual(doc['subscribers'][0]['locales'],['en','es-419','zh-Hans'])
    def test_reads_retry_bounded_and_export_pagination_fails_closed(self):
        with MockBrevo() as server:
            server.failures = [('GET',429),('GET',503)]
            self.assertEqual(self.provider(server).health()['status'],'ok')
            server.calls.clear(); server.failures = [('GET',503)]*4
            with self.assertRaises(DeliveryError): self.provider(server).health()
            self.assertEqual(len(server.calls),3)
    def test_hosted_doi_forms_need_no_key_and_no_own_server(self):
        from tools.paper.templates.subscribe import subscribe_block
        env = {k:v for k,v in BREVO_ENV.items() if k!='FCMO_EMAIL_PROVIDER_CONFIG'}
        with patch.dict(os.environ,env,clear=True):
            for locale in ('en','es-419','zh-Hans'):
                html = subscribe_block('paper',locale,page=True)
                self.assertIn('action="https://example.sibforms.com/serve/'+locale+'"',html)
                self.assertIn('name="EMAIL"',html)
                self.assertIn('name="consent" value="yes" required',html)
                self.assertNotIn('checked',html); self.assertNotIn('synthetic-key',html)
        for action in ('http://example.sibforms.com/serve/en','https://evil.example/serve/en',
                       'https://example.sibforms.com/serve/en?api-key=secret'):
            bad = dict(env,FCMO_EMAIL_PUBLIC_CONFIG=json.dumps({'forms':{'en':action}}))
            with self.assertRaises(ValueError): signup_form(bad,'en')
    def test_private_config_and_test_namespace_are_closed(self):
        for config in ({}, {'api_key':'key','list_ids':{'en':21,'es-419':21,'zh-Hans':23}}):
            with self.assertRaises(ValueError): create_provider(dict(BREVO_ENV,FCMO_EMAIL_PROVIDER_CONFIG=json.dumps(config)))
        from dataclasses import replace
        with MockBrevo() as server:
            seed = replace(self.edition,namespace='fcmo-diario-test')
            with self.assertRaises(ValueError): self.provider(server).send_edition(seed,'en',seed.key('en'))
            self.assertEqual(server.calls,[])
