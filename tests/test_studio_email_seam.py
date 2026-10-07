"""L29: actual approved Studio bytes -> paper -> unified dispatch -> Studio status.

Only local git and synthetic provider/Contents boundaries are used.
"""
import base64
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from studio.server.storage import Store, git
from studio.server.publishing import Publisher, Workspace, GitHub
from studio.server.checks import checks
from studio.translation import translate, FakeProvider
from tools.paper.build import PaperBuilder
from tools.email_piece_dispatch import collect
from tools.email_piece_state import StateStore
from tools.email_providers import create_provider
from tools.email_dispatch import main
from tests.test_studio_translation import SOURCE
from tests.harness.mock_github import MockGitHub

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ('en', 'es-419', 'zh-Hans')


class StudioEmailSeamTests(unittest.TestCase):
    def test_approved_piece_reaches_dispatch_and_readonly_studio_feedback_once(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'_audit') as tmp:
            root = Path(tmp); store = Store(root/'studio')
            self.addCleanup(store.close)
            slug = store.create('javier', 'essay', SOURCE['title'], 'es-419')['slug']
            store.save(slug, 'es-419', 'javier', 0, SOURCE, {})
            store.resource(slug, 'sources', 'javier', [{'key':'src-one', 'title':'Fuente', 'author':'Javier', 'publisher':'FCMO', 'date':'2026-10-05', 'url':'https://example.org/ref', 'accessed':'2026-10-05'}])
            translate(store, slug, 'javier', store.piece(slug)['head_rev'], FakeProvider())
            store.locale_state(slug, 'es-419', 'javier', 'ready', True)
            gh = GitHub({'javier':'synthetic-key', 'matias':'synthetic-other'})
            publisher = Publisher(store, gh, None, lambda value: checks(store, SimpleNamespace(privacy=lambda _:True), value))
            publisher.request(slug, 'javier'); approved = publisher.approve(slug, 'matias')
            self.assertEqual(approved['payload']['distribution'], {'email':True})
            self.assertTrue(all(store.payload(slug)['provenance'][loc]['human_reviewed'] is True for loc in LOCALES))
            remote = root/'remote'; remote.mkdir(); git(remote, 'init', '-q', '-b', 'main')
            (remote/'base.txt').write_text('Synthetic public base')
            git(remote, 'add', '.'); git(remote, '-c','user.name=Codex','-c','user.email=noreply@openai.com','commit','-qm','Base')
            git(store.data/'clone', 'remote','set-url','origin', str(remote))
            prepared = Workspace(store, gh, ['python3','-c','raise SystemExit(0)']).prepare(approved)
            candidate = Path(prepared['candidate']); commit = prepared['head_sha']
            out = root/'paper'
            PaperBuilder(stories_path=ROOT/'site/data/stories.v2.json', status_path=ROOT/'site/data/newsroom-status.json', editorial_path=candidate/'editorial', out=out, base='/FCMO-AI-Newsletter/').build()
            identity = {'source_commit':commit, 'candidate_id':'b'*64}
            (out/'deployment-identity.json').write_text(json.dumps(identity))
            base = 'https://example.org/FCMO-AI-Newsletter'
            def fetch(url, nonce): return (out/url.removeprefix(base+'/')).read_bytes()
            def read_git(*args):
                import subprocess
                return subprocess.check_output(['git','-C',str(candidate),*args])
            bundle = collect(base,commit,fetch=fetch,git=read_git,verify=lambda *a,**kw:(identity,b'{}',b'{}'))
            self.assertEqual(len(bundle['pieces']),1)
            self.assertEqual(bundle['pieces'][0]['distribution'],{'email':True})
            env = {'FCMO_EMAIL_ENABLED':'true','FCMO_EMAIL_PROVIDER':'fake','GH_TOKEN':'synthetic-key','GITHUB_REPOSITORY':'fixture/paper'}
            state_file = None; version = 0; calls = []
            def contents(method, path, payload=None):
                nonlocal state_file, version
                calls.append((method,path))
                if path.startswith('git/ref/heads/'): return {'object':{'sha':commit}}
                if method=='GET': return state_file
                self.assertEqual(payload['branch'],'email-dispatch-state')
                self.assertEqual(payload.get('sha'),state_file['sha'] if state_file else None)
                version += 1
                state_file = {'encoding':'base64','content':payload['content'],'sha':str(version)}
                return {'content':{'sha':str(version)}}
            state_store = StateStore(env,source_commit=commit,request=contents)
            provider = create_provider(env)
            original_send = provider.send_edition
            def send(edition,locale,key):
                persisted,_ = state_store.read()
                self.assertIn(key,persisted['keys'])
                self.assertEqual(edition.piece['provenance'][locale]['reviewer'],'Matías')
                return original_send(edition,locale,key)
            provider.send_edition = send
            paths = {n:root/(n+'.json') for n in ('bundle','intent','state')}
            paths['bundle'].write_text(json.dumps(bundle))
            args = [a for n,p in paths.items() for a in ('--'+n,str(p))]
            with patch.dict(os.environ,env,clear=True), patch('tools.email_piece_state.StateStore',return_value=state_store), patch('tools.email_piece_dispatch.collect',return_value=bundle), patch('tools.email_piece_dispatch.create_provider',return_value=provider):
                self.assertEqual(main(['--pieces','--claim',*args]),0)
                self.assertEqual(main(['--pieces','--send',*args]),0)
                self.assertEqual(main(['--pieces','--claim',*args]),0)
                self.assertEqual(main(['--pieces','--send',*args]),0)
            self.assertEqual(len(provider.sent),3)
            state,_ = state_store.read()
            self.assertTrue(all(r['state']=='QUEUED' for r in state['records']))
            approved['payload']['merge_sha'] = commit
            publisher._write(approved,'published')
            with MockGitHub() as mock:
                publisher.github = GitHub({'javier':'fixture-javier'},mock.url)
                original = mock.dispatch
                def api(actor,method,path,query,body):
                    if path.endswith('/contents/dispatch.json'):
                        self.assertEqual(method,'GET'); self.assertEqual(query,{'ref':['email-dispatch-state']})
                        return 200, state_file
                    return original(actor,method,path,query,body)
                mock.dispatch = api
                status = publisher.public_status(slug)
                self.assertEqual(status['email']['state'],'queued')
                self.assertEqual(status['email']['plain_es'],'Correo programado ✓')
                self.assertEqual(len(mock.requests),1)
                self.assertEqual(mock.requests[0]['method'],'GET')
                mock.dispatch = original  # Missing branch/read failure remains pending.
                self.assertEqual(publisher.public_status(slug)['email']['state'],'pending')
                publisher._write(approved,'deployed_unverified')
                before = len(mock.requests)
                self.assertEqual(publisher.public_status(slug)['email']['state'],'pending')
                self.assertEqual(len(mock.requests),before)
            self.assertTrue(all('main' not in path for _,path in calls))

    def test_partial_seed_malformed_and_unknown_records_cannot_show_success(self):
        from studio.server.distribution import email_status
        ident = 'FCMO-P-0123456789ab'
        keys = ['fcmo-piece:'+ident+':'+loc for loc in LOCALES]
        records = [{'piece_id':ident,'locale':loc,'state':'QUEUED','broadcast_id':i+1,'timestamp':'2026-10-06T00:00:00Z'} for i,loc in enumerate(LOCALES)]
        state = {'schema':'fcmo-piece-email-state-v1','provider':'fake','keys':keys,'records':records}
        self.assertEqual(email_status(state,ident,True)['state'],'queued')
        for change in ('partial','seed','unknown','invalid','wrong_piece'):
            bad = copy.deepcopy(state)
            if change=='partial': bad['records'].pop()
            if change=='seed': bad['keys'] = [key.replace('fcmo-piece:', 'fcmo-piece-test:') for key in keys]
            if change=='unknown': bad['records'][0].update(state='BLOCKED_RECONCILE',broadcast_id=None)
            if change=='invalid': bad['records'][0]['broadcast_id']=True
            if change=='wrong_piece': bad['records'][0]['piece_id']='FCMO-P-abcdef012345'
            with self.subTest(change=change): self.assertEqual(email_status(bad,ident,True)['state'],'pending')
        self.assertEqual(email_status(state,ident,False)['state'],'disabled')
