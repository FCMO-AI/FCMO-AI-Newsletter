"""Red-first L27 acceptance: real HTTP boundary, four adapter contract, age roundtrip."""
import copy
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from harness.mock_kit import MockKit
from harness.mock_brevo import MockBrevo
from test_email_listmonk import FakeListmonk
from tools.email_listmonk import ListmonkClient, MailConfig, DiarioService, DeliveryError
from tools.email_providers import Edition, create_provider, dispatch_edition, signup_form
from tools.email_providers.kit import KitProvider
from tools.email_backup import encrypted_backup

ROOT = Path(__file__).resolve().parents[1]
ENV = {'FCMO_EMAIL_ENABLED':'true', 'FCMO_EMAIL_PROVIDER': 'kit', 'KIT_API_KEY': 'synthetic-key',
       'KIT_FORM_EN': '101', 'KIT_FORM_ES': '102', 'KIT_FORM_ZH': '103',
       'KIT_TAG_EN': '11', 'KIT_TAG_ES': '12', 'KIT_TAG_ZH': '13',
       'FCMO_EMAIL_POSTAL_ADDRESS': 'Synthetic postal address',
       'FCMO_EMAIL_PRIVACY_URL': 'https://example.org/complete-notice',
       'FCMO_EMAIL_COMPLIANCE_READY': 'true', 'FCMO_EMAIL_FROM': 'daily@example.org'}

BREVO_ENV = dict(ENV, FCMO_EMAIL_PROVIDER='brevo', FCMO_EMAIL_PROVIDER_CONFIG=json.dumps({
    'api_key': 'synthetic-key', 'list_ids': {'en': 21, 'es-419': 22, 'zh-Hans': 23}}),
    FCMO_EMAIL_PUBLIC_CONFIG=json.dumps({'forms': {l: 'https://example.sibforms.com/serve/'+l
                                                 for l in ('en', 'es-419', 'zh-Hans')}}))

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stories = json.loads((ROOT/'contracts/fixtures/stories.v2.json').read_text())
        for story in self.stories['stories']:
            story['first_published_at'] = '2026-10-05T12:00:00Z'
            story['l10n']['zh-Hans'] = copy.deepcopy(story['l10n']['es-419'])
            story['l10n']['zh-Hans']['fields'].update(headline='人工智能新闻', summary='研究摘要', why_it_matters='重要性')
        self.now = datetime(2026, 10, 5, 14, tzinfo=timezone.utc)
        self.status = {'edition_state':'FRESH', 'edition_date':'2026-10-05'}
        self.edition = Edition(self.stories, self.status, {'source_commit':'a'*40,'candidate_id':'candidate'}, self.now)
        self.intent = self.root/'intent.json'
        self.intent.write_text(json.dumps({'previous':[], 'keys':[self.edition.key(l) for l in ('en','es-419','zh-Hans')]}))
    def kit(self, server):
        return KitProvider(ENV, base_url=server.url, intent=self.intent, sleep=lambda _: None)
    def test_contract_all_four_adapters(self):
        with MockKit() as server, MockBrevo() as brevo:
            config = MailConfig('http://127.0.0.1:9000','test','key','https://mail.example.org',
                                'daily@example.org','Synthetic postal address','https://example.org','x'*40)
            client = ListmonkClient(config); remote = FakeListmonk(); original_request = remote.request
            def request(method,path,payload=None,**kwargs):
                if path.startswith('subscribers?'): return {'results':[], 'total':0}
                return original_request(method,path,payload,**kwargs)
            client.request = request
            service = DiarioService(config,self.root/'listmonk.sqlite',client=client)
            adapters = [self.kit(server), create_provider(BREVO_ENV, base_url=brevo.url, intent=self.intent, sleep=lambda _:None), create_provider(dict(ENV,FCMO_EMAIL_PROVIDER='fake')),
                        create_provider({'FCMO_EMAIL_PROVIDER':'listmonk','FCMO_EMAIL_PUBLIC_URL':'https://mail.example.org'}, service=service)]
            for provider in adapters:
                with self.subTest(provider=provider.name):
                    self.assertEqual(provider.health()['status'], 'ok')
                    self.assertTrue(provider.subscribe_form('en').action.startswith('https://'))
                    for locale in ('en','es-419','zh-Hans'):
                        outcome = provider.send_edition(self.edition, locale, self.edition.key(locale))
                        self.assertEqual(outcome['action'], 'QUEUED')
                        self.assertEqual(provider.send_edition(self.edition,locale,self.edition.key(locale))['action'],'SKIP')
                    self.assertIsInstance(list(provider.list_subscribers()), list)
            self.assertEqual(len(remote.campaigns),3)
    def test_kit_restart_paginates_and_does_not_create_again(self):
        with MockKit() as server:
            provider = self.kit(server)
            for locale, form in [('en',101),('es-419',102),('zh-Hans',103)]:
                self.assertEqual(provider.send_edition(self.edition,locale,self.edition.key(locale))['action'],'QUEUED')
                broadcast = server.broadcasts[-1]
                self.assertEqual(broadcast['subscriber_filter'], {'all':[{'type':'form','ids':[form]}]})
                self.assertFalse(broadcast['public']); self.assertTrue(broadcast['send_at'])
                self.assertIn('unsubscribe_url', broadcast['content'])
            provider = self.kit(server)
            for locale in ('en','es-419','zh-Hans'):
                self.assertEqual(provider.send_edition(self.edition,locale,self.edition.key(locale))['action'],'SKIP')
            self.assertEqual(len(server.broadcasts),3)
    def test_kit_defaults_to_forms_without_tags_or_automation(self):
        env = {k:v for k,v in ENV.items() if not k.startswith('KIT_TAG_')}
        with MockKit() as server:
            provider = KitProvider(env,base_url=server.url,intent=self.intent,sleep=lambda _:None)
            self.assertEqual(provider.health()['status'],'ok')
            provider.send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(server.broadcasts[0]['subscriber_filter'],{'all':[{'type':'form','ids':[101]}]})
            self.assertEqual(list(provider.list_subscribers())[0]['locales'],['en','es-419','zh-Hans'])
            self.assertFalse(any('/tags' in c[1] for c in server.calls))
    def test_kit_optional_tags_and_invalid_filter_are_fail_closed(self):
        with MockKit() as server:
            provider = KitProvider(dict(ENV,KIT_FILTER_MODE='tag'),base_url=server.url,intent=self.intent,sleep=lambda _:None)
            provider.health(); provider.send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(server.broadcasts[0]['subscriber_filter'],{'all':[{'type':'tag','ids':[11]}]})
        with self.assertRaises(ValueError): KitProvider(dict(ENV,KIT_FILTER_MODE='all'))
        with self.assertRaises(ValueError): KitProvider(dict(ENV,KIT_FORM_ES='101'))
    def test_master_switch_and_verification_send_nothing(self):
        with MockKit() as server:
            provider = self.kit(server)
            self.assertEqual(dispatch_edition(provider,self.edition,enabled=False,live_verified=True)['action'],'SKIP')
            self.assertEqual(dispatch_edition(provider,self.edition,enabled=True,live_verified=False)['action'],'SKIP')
            self.assertEqual(server.calls,[])
    def test_incomplete_chinese_stops_before_any_provider_call(self):
        for story in self.stories['stories']: story['l10n']['zh-Hans']['state']='PENDING'
        with MockKit() as server:
            with self.assertRaises(ValueError): dispatch_edition(self.kit(server),self.edition,enabled=True,live_verified=True)
            self.assertEqual(server.calls,[])
    def test_reads_retry_bounded_429_and_503(self):
        with MockKit() as server:
            server.failures = [('GET',429),('GET',503)]
            self.assertEqual(self.kit(server).health()['status'],'ok')
            self.assertEqual(len(server.calls),3)
            server.calls.clear(); server.failures = [('GET',503)]*5
            with self.assertRaises(DeliveryError): self.kit(server).health()
            self.assertEqual(len(server.calls),3)
    def test_mutation_unknown_is_never_blindly_retried(self):
        with MockKit() as server:
            server.failures = [('POST',503)]
            provider = self.kit(server)
            with self.assertRaises(DeliveryError): provider.send_edition(self.edition,'en',self.edition.key('en'))
            with self.assertRaises(DeliveryError): self.kit(server).send_edition(self.edition,'en',self.edition.key('en'))
            self.assertEqual(sum(call[0]=='POST' for call in server.calls),1)
    def test_lost_create_ack_reconciles_without_resend(self):
        with MockKit() as server:
            server.lose_create = True
            provider = self.kit(server)
            self.assertEqual(provider.send_edition(self.edition,'en',self.edition.key('en'))['action'],'SKIP')
            self.assertEqual(self.kit(server).send_edition(self.edition,'en',self.edition.key('en'))['action'],'SKIP')
            self.assertEqual(len(server.broadcasts),1)
    def test_prior_workflow_intent_with_absent_broadcast_blocks(self):
        self.intent.write_text(json.dumps({'previous':[self.edition.key('en')],'keys':[self.edition.key('en')]}))
        with MockKit() as server:
            with self.assertRaises(DeliveryError): self.kit(server).send_edition(self.edition,'en',self.edition.key('en'))
            self.assertFalse(any(c[0]=='POST' for c in server.calls))
    def test_age_backup_roundtrip_preserves_locale_and_suppression(self):
        identity = self.root/'identity.txt'
        keys = subprocess.run(['age-keygen','-o',str(identity)],capture_output=True,check=True)
        recipient = keys.stderr.decode().split('Public key: ')[1].strip()
        with MockKit() as server:
            server.subscribers.append(dict(server.subscribers[0],id=2,state='cancelled',email_address='unsubscribed@example.org'))
            provider = self.kit(server)
            out = self.root/'backup.json.age'
            encrypted_backup(provider,recipient,out)
            ciphertext = out.read_bytes()
            self.assertTrue(ciphertext.startswith(b'age-encryption.org/v1'))
            self.assertNotIn(b'reader@example.org',ciphertext)
            decrypted = subprocess.run(['age','-d','-i',str(identity),str(out)],capture_output=True,check=True)
            doc = json.loads(decrypted.stdout)
            self.assertEqual(len(doc['subscribers']),2)
            self.assertEqual(doc['subscribers'][1]['state'],'cancelled')
            self.assertEqual(doc['subscribers'][0]['locales'],['en','es-419','zh-Hans'])
            self.assertEqual(sorted(p.name for p in self.root.iterdir()),['backup.json.age','identity.txt','intent.json'])
    def test_static_forms_all_locales(self):
        from tools.paper.templates.subscribe import subscribe_block
        with patch.dict(os.environ,ENV,clear=True):
            for locale,form in [('en',101),('es-419',102),('zh-Hans',103)]:
                html = subscribe_block('paper',locale,page=True)
                self.assertIn(f'action="https://app.kit.com/forms/{form}/subscriptions"',html)
                self.assertIn('name="email_address"',html)
                self.assertIn('name="consent" value="yes" required',html)
                self.assertNotIn('checked',html); self.assertIn('/privacy/',html)
                self.assertNotIn('synthetic-key',html)
    def test_bad_public_configuration_is_closed(self):
        with self.assertRaises(ValueError): signup_form(dict(ENV,KIT_FORM_EN='1?api_key=secret'),'en')
        with self.assertRaises(ValueError): create_provider({'FCMO_EMAIL_PROVIDER':'unknown'})

class IntentTests(unittest.TestCase):
    def test_prior_workflow_snapshots_restore_as_blocking_intents(self):
        from tools.email_intent import prepare
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'email-intent.json'
            prepare('2026-10-05',[],out)
            first = json.loads(out.read_text())
            self.assertEqual(first['previous'],[])
            prepare('2026-10-05',[first],out)
            self.assertEqual(set(json.loads(out.read_text())['previous']),set(first['keys']))
            with self.assertRaises(ValueError): prepare('2026-10-06',[first],out)
    def test_restore_follows_signed_download_without_forwarding_token(self):
        import io
        import urllib.error
        import zipfile
        from tools.email_intent import restore
        keys = ['fcmo-diario:2026-10-05:'+l for l in ('en','es-419','zh-Hans')]
        raw = io.BytesIO()
        with zipfile.ZipFile(raw,'w') as archive: archive.writestr('email-intent.json',json.dumps({'keys':keys}))
        class Response(io.BytesIO): pass
        calls = []
        class Opener:
            def open(self,request,timeout):
                calls.append((request.full_url,dict(request.header_items())))
                if 'page=' in request.full_url:
                    return Response(json.dumps({'artifacts':[{'name':'email-intent-2026-10-05-1-1','id':1,'expired':False}]}).encode())
                if request.full_url.endswith('/zip'):
                    raise urllib.error.HTTPError(request.full_url,302,'redirect',{'Location':'https://storage.example.org/signed'},None)
                return Response(raw.getvalue())
        with patch('tools.email_intent.urllib.request.build_opener',return_value=Opener()):
            documents = restore('example/paper','synthetic-token','2026-10-05')
        self.assertEqual(documents,[{'keys':keys}])
        self.assertIn('Authorization',calls[0][1])
        self.assertNotIn('Authorization',calls[-1][1])
    def test_workflow_persists_intent_before_dispatch_and_copies_ciphertext_only(self):
        import yaml
        workflow = yaml.safe_load((ROOT/'.github/workflows/dispatch-email.yml').read_text())
        steps = workflow['jobs']['dispatch']['steps']
        upload = next(i for i,s in enumerate(steps) if 'email-intent' in s.get('with',{}).get('name',''))
        send = next(i for i,s in enumerate(steps) if s.get('run','').startswith('python tools/email_dispatch.py ') and '--check' not in s.get('run',''))
        self.assertLess(upload,send)
        self.assertEqual(steps[upload]['with']['if-no-files-found'],'error')
        backup = yaml.safe_load((ROOT/'.github/workflows/backup-email.yml').read_text())
        stored = backup['jobs']['backup']['steps'][-1]['with']
        self.assertTrue(stored['path'].endswith('.age'))
        self.assertEqual(stored['retention-days'],30)

class SeedTests(unittest.TestCase):
    setUp = ProviderTests.setUp
    def test_seed_namespace_does_not_consume_production_key(self):
        seed = Edition(self.stories,self.status,{},self.now,'fcmo-diario-test')
        self.intent.write_text(json.dumps({'previous':[], 'keys':[seed.key(l) for l in ('en','es-419','zh-Hans')]}))
        with MockKit() as server:
            provider = KitProvider(dict(ENV,KIT_TEST_SUBSCRIBER_ID='1'),base_url=server.url,intent=self.intent,sleep=lambda _:None)
            provider.send_edition(seed,'en',seed.key('en'))
            self.assertNotEqual(server.broadcasts[0]['description'],self.edition.key('en'))
            server.subscribers.append(dict(server.subscribers[0],id=2))
            with self.assertRaises(DeliveryError): provider.send_edition(seed,'es-419',seed.key('es-419'))
            self.assertEqual(len(server.broadcasts),1)

class ExportFailureTests(unittest.TestCase):
    def test_failed_export_leaves_no_artifact_or_plaintext_file(self):
        class Broken:
            name = 'fake'
            def list_subscribers(self):
                yield {'email_address':'synthetic@example.org'}
                raise DeliveryError('export_failed')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'backup.age'
            key = subprocess.run(['age-keygen'],capture_output=True,check=True)
            recipient = key.stderr.decode().split('Public key: ')[1].strip()
            with self.assertRaises(DeliveryError): encrypted_backup(Broken(),recipient,out)
            self.assertEqual(list(Path(tmp).iterdir()),[])
    def test_listmonk_export_preserves_suppression_and_confirmed_language(self):
        from tools.email_providers.listmonk import ListmonkProvider
        class Client:
            def lists(self): return {l:{'id':n} for n,l in enumerate(('en','es-419','zh-Hans'),1)}
            def request(self,method,path):
                return {'total':2,'results':[
                    {'id':1,'email':'active@example.org','status':'enabled','lists':[{'id':2,'subscription_status':'confirmed'}]},
                    {'id':2,'email':'blocked@example.org','status':'blocklisted','lists':[{'id':1,'subscription_status':'unsubscribed'}]}]}
        records = list(ListmonkProvider({},client=Client()).list_subscribers())
        self.assertEqual(records[0]['locales'],['es-419'])
        self.assertEqual(records[1]['status'],'blocklisted')
        self.assertEqual(records[1]['lists'][0]['subscription_status'],'unsubscribed')
    def test_cli_disabled_does_not_instantiate_or_contact_a_provider(self):
        from tools.email_dispatch import main
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for name,document in [('stories',{}),('status',{}),('receipt',{})]:
                path = Path(tmp)/(name+'.json'); path.write_text(json.dumps(document)); paths.append(str(path))
            with patch.dict(os.environ,{'FCMO_EMAIL_ENABLED':'false'},clear=True), patch('tools.email_providers.create_provider') as factory:
                self.assertEqual(main(['--stories',paths[0],'--status',paths[1],'--live-verify',paths[2]]),0)
                factory.assert_not_called()
