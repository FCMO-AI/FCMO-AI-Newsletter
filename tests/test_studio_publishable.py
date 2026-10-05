"""Regressions found while exercising Studio's previously absent writer paths."""
import copy
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from studio.server.http import Application
from studio.server.storage import Store, Conflict
from studio.server import assist
from tests.test_studio_storage import ROOT, DOC
from ops.studio import protect_main

class Publishable(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / 'data')
        self.app = Application(self.store, 'https://studio.invalid', 'fixture-key-' + 'x'*40, ROOT)
        self.app.auth.add_user('javier', 'fixture-long-password')
        self.slug = self.store.create('javier', 'essay', 'A real draft', 'en')['slug']
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
    def tearDown(self): self.store.close(); self.tmp.cleanup()
    def job(self, kind='translate', loc='es-419'):
        heartbeat = self.store.data / 'jobs/worker-heartbeat'; heartbeat.touch()
        return self.app.api('POST', '/api/pieces/' + self.slug + '/assist', {}, {'kind': kind, 'loc': loc}, {'user': 'javier'})['job_id']
    def test_progress_read_does_not_wait_for_long_publication_transition(self):
        held = threading.Event(); release = threading.Event()
        publisher = self.app.publisher
        def transition():
            with publisher.mutex:
                held.set(); release.wait(5)
        worker = threading.Thread(target=transition)
        worker.start(); self.assertTrue(held.wait(2))
        result = []; completed = threading.Event()
        def poll():
            result.append(publisher.public_status(self.slug)); completed.set()
        reader = threading.Thread(target=poll); reader.start()
        try:
            self.assertTrue(completed.wait(1), 'HTTP progress blocked behind candidate checks')
            self.assertEqual(result[0]['state'], 'draft')
        finally:
            release.set(); worker.join(5); reader.join(5)
    def test_first_start_initializes_url_after_store_installs_push_refspec(self):
        from studio.server.snapshot import refresh, PUBLIC_REMOTE
        from studio.server.storage import git
        from studio.server.publishing import GitHub, Refused
        class StopBeforeNetwork(GitHub):
            def validate_remote(inner, clone):
                super().validate_remote(clone)
                raise Refused('fixture stops before fetch')
        with self.assertRaisesRegex(Refused, 'fixture stops'):
            refresh(self.store, StopBeforeNetwork({}))
        self.assertEqual(git(self.store.data / 'clone', 'remote', 'get-url', 'origin'), PUBLIC_REMOTE)
    def test_start_does_not_overwrite_an_existing_wrong_remote(self):
        from studio.server.snapshot import refresh
        from studio.server.storage import git
        from studio.server.publishing import GitHub, Refused
        clone = self.store.data / 'clone'
        git(clone, 'config', 'remote.origin.url', 'https://example.invalid/wrong')
        with self.assertRaises(Refused): refresh(self.store, GitHub({}))
        self.assertEqual(git(clone, 'remote', 'get-url', 'origin'), 'https://example.invalid/wrong')
    def test_translation_job_contains_original_instead_of_empty_target(self):
        ident = self.job()
        envelope = json.loads((self.store.data / 'jobs/queued' / (ident + '.json')).read_text())
        self.assertEqual(envelope['doc'], DOC)
        self.assertEqual(envelope['locale'], 'es-419')
        self.assertNotIn('token', envelope)
    def test_multiple_suggestions_and_human_edits_preserve_provenance_and_revision(self):
        ident = self.job(loc='en')
        payload = {'model': 'fixture-model', 'suggestions': [{'block_id': DOC['blocks'][0]['id'], 'text': 'An assistant suggestion with 42 ideas.'}]}
        (self.store.data / 'jobs/done' / (ident + '.json')).write_text(json.dumps(payload))
        result = assist.accept(self.store, ident, 'javier', [DOC['blocks'][0]['id']], 1, {DOC['blocks'][0]['id']: 'Edited assistant prose with 42 ideas.'})
        self.assertEqual(result['rev'], 2)
        self.assertEqual(self.store.payload(self.slug)['provenance']['en']['origin'], 'agent_draft_human_edited')
        self.assertFalse(self.store.payload(self.slug)['provenance']['en']['human_reviewed'])
        self.assertEqual(json.loads((self.store.data / 'jobs/queued' / (ident + '.json')).read_text())['rev'], 2)
        self.store.save(self.slug, 'en', 'javier', 2, DOC, {})
        with self.assertRaises(Conflict): assist.accept(self.store, ident, 'javier', [DOC['blocks'][0]['id']], 3)
    def test_title_suggestion_does_not_require_a_fake_document_block(self):
        ident = self.job('dek', 'en')
        (self.store.data / 'jobs/done' / (ident + '.json')).write_text(json.dumps({'model': 'fixture', 'suggestions': [{'block_id': 'title', 'text': 'Suggested title'}, {'block_id': 'dek', 'text': 'Suggested introduction'}]}))
        assist.accept(self.store, ident, 'javier', ['title'], 1)
        assist.accept(self.store, ident, 'javier', ['dek'], 2)
        self.assertEqual(self.store.doc(self.slug, 'en')['doc']['title'], 'Suggested title')
        self.assertEqual(self.store.doc(self.slug, 'en')['doc']['dek'], 'Suggested introduction')
    def test_layout_review_does_not_need_worker_or_leave_session_or_stop_app(self):
        from studio.server.layout_qa import run
        with patch.object(self.app.preview, 'build'), patch('studio.server.layout_qa.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps({'frames': ['en-390-light.png'], 'checks': [{'ok': True}]}), '')):
            result = run(self.app, self.slug, 'javier')
        self.assertEqual(result['status'], 'done')
        self.assertFalse(self.app.stop.is_set())
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
    def test_ruleset_dry_run_prints_json_without_gh(self):
        result = subprocess.run(['sh', str(ROOT / 'ops/studio/protect-main.sh'), '--dry-run'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), protect_main.desired())
    def test_apply_readback_and_rollback_preserve_previous_rules(self):
        receipt = Path(self.tmp.name) / 'rules.json'
        previous = copy.deepcopy(protect_main.desired()); previous['enforcement'] = 'disabled'
        state = {'value': previous, 'calls': []}
        def api(method, path, body=None):
            state['calls'].append((method, path))
            if path.startswith('/rulesets?'): return [{'id': 7, 'name': protect_main.NAME}]
            if method == 'PUT': state['value'] = copy.deepcopy(body); return {'id': 7, **body}
            return {'id': 7, **state['value']}
        original = Path.read_text
        def read(path, *args, **kw):
            return '/editorial/ @javier-real @matias-real\n' if path.name == 'CODEOWNERS' else original(path, *args, **kw)
        with patch.object(protect_main, 'api', side_effect=api), patch.object(Path, 'read_text', read):
            with patch.object(sys, 'argv', ['protect', '--state', str(receipt)]): protect_main.main()
            self.assertEqual(state['value'], protect_main.desired())
            with patch.object(sys, 'argv', ['protect', '--rollback', '--state', str(receipt)]): protect_main.main()
            self.assertEqual(state['value'], previous)
            self.assertFalse(receipt.exists())
    def test_placeholder_codeowners_fail_before_any_external_effect(self):
        original = Path.read_text
        def read(path, *args, **kw):
            return '/editorial/ @REPLACE_WITH_JAVIER @REPLACE_WITH_MATIAS' if path.name == 'CODEOWNERS' else original(path, *args, **kw)
        with patch.object(Path, 'read_text', read), patch.object(protect_main, 'api') as api, patch.object(sys, 'argv', ['protect', '--state', str(Path(self.tmp.name) / 'rules.json')]):
            with self.assertRaisesRegex(ValueError, 'placeholders'): protect_main.main()
            api.assert_not_called()
