"""Adversarial publication proofs against an HTTP mock, with real local git trees."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from studio.translation import FakeProvider
from studio.server.storage import Store, git
from studio.server.publishing import GitHub, Workspace, Publisher, Refused, PieceHTML
from tests.harness.mock_github import MockGitHub as TwoPersonMockGitHub
from tests.test_studio_storage import DOC, ROOT

class MockGitHub(TwoPersonMockGitHub):
    """The author-only GitHub contract; all automatic merge guards remain."""
    def dispatch(self, actor, method, path, query, body):
        if method == 'PUT' and path.endswith('/merge') and actor:
            pr = self.prs[int(path.split('/')[-2])]
            if self.merge_refused or not self.protection or body['sha'] != pr['head']['sha']:
                return 403, {}
            if self.check != 'success': return 403, {}
            pr.update(merged=True, state='closed', merge_commit_sha='f' * 40)
            return 200, {'merged': True, 'sha': pr['merge_commit_sha']}
        return super().dispatch(actor, method, path, query, body)

class MockWorkspace(Workspace):
    def push(self, pub):
        data = pub['payload']; target = Path(data['candidate'])
        paths = git(target, 'diff', '--name-only', 'refs/remotes/origin/main', 'HEAD').splitlines()
        self.github.request(data['author'], 'POST', '/git/refs', {'ref': 'refs/heads/' + data['branch'], 'sha': data['head_sha'], 'paths': paths})

class Publish(unittest.TestCase):
    def setUp(self):
        provider = patch('studio.translation.configured_provider', return_value=FakeProvider())
        provider.start(); self.addCleanup(provider.stop)
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit'); self.data = Path(self.tmp.name)
        self.store = Store(self.data / 'data'); self.slug = self.store.create('javier', 'essay', 'Private essay', 'en')['slug']
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        self.remote = self.data / 'remote'; self.remote.mkdir(); git(self.remote, 'init', '-q', '-b', 'main')
        (self.remote / 'base.txt').write_text('Public base')
        git(self.remote, 'add', '.'); git(self.remote, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '-qm', 'Base')
        git(self.store.data / 'clone', 'remote', 'set-url', 'origin', str(self.remote))
        self.mock = MockGitHub().__enter__(); self.github = GitHub({'javier': 'fixture-javier', 'matias': 'fixture-matias'}, self.mock.url, live_base=self.mock.url + '/live/')
        self.mock.refs['main'] = git(self.remote, 'rev-parse', 'HEAD')
        self.workspace = MockWorkspace(self.store, self.github, ['python3', '-c', 'raise SystemExit(0)'])
        self.publisher = Publisher(self.store, self.github, self.workspace, lambda value: [{'ok': True}])
        self.mock.live_id = self.store.payload(self.slug)['piece']['id']
    def tearDown(self):
        self.mock.__exit__(); self.store.close(); self.tmp.cleanup()
    def requested(self): self.publisher.request(self.slug, 'javier')
    def approved(self): return self.publisher.request(self.slug, 'javier')
    def test_author_publishes_without_second_account(self):
        self.github.tokens.pop('matias')
        self.github.preflight('javier')
        self.publisher.request(self.slug, 'javier')
        pub = self.run_to('published')
        self.assertEqual(len(pub['payload']['urls']), 3)
        self.assertEqual(self.mock.count('POST', '/reviews'), 0)
        self.assertFalse(any(r['actor'] == 'matias' for r in self.mock.requests))
        self.assertNotIn('reviewed', [r['state'] for r in pub['payload']['timeline']])
    def test_author_request_red_gate_blocks(self):
        self.mock.check = 'failure'
        self.publisher.request(self.slug, 'javier')
        self.run_to('failed')
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_change_after_publish_is_rejected(self):
        self.publisher.request(self.slug, 'javier')
        self.store.db.execute('UPDATE pieces SET head_rev=head_rev+1 WHERE slug=?', (self.slug,))
        self.store.db.commit()
        self.publisher.advance(self.slug)
        self.assertEqual(self.publisher.get(self.slug)['state'], 'failed')
        self.assertIn('después de pulsar Publicar', self.publisher.get(self.slug)['error_plain'])
        self.assertEqual(self.mock.requests, [])
    def test_local_red_gate_blocks_author_before_any_public_effect(self):
        self.publisher.checker = lambda _: [{'ok': False, 'id': 'privacy'}]
        with self.assertRaises(Refused): self.publisher.request(self.slug, 'javier')
        self.assertEqual(self.mock.requests, [])
        self.assertEqual(self.store.piece(self.slug)['state'], 'draft')
    def test_repeated_author_request_is_idempotent(self):
        first = self.publisher.request(self.slug, 'javier')
        second = self.publisher.request(self.slug, 'javier')
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM publications').fetchone()[0], 1)
        self.run_to('published')
        self.assertEqual(self.mock.count('PUT', '/merge'), 1)
    def test_legacy_reviewed_publication_continues_without_reviewer_credential(self):
        self.publisher.request(self.slug, 'javier'); self.run_to('pr_open')
        pub = self.publisher.get(self.slug)
        pub['payload']['reviewer'] = 'matias'
        self.publisher._write(pub, 'reviewed')
        self.github.tokens.pop('matias')
        self.run_to('published')
        self.assertEqual(self.mock.count('POST', '/reviews'), 0)
    def run_to(self, target):
        for _ in range(15):
            pub = self.publisher.get(self.slug)
            if pub['state'] == target: return pub
            self.publisher.advance(self.slug)
        self.fail(str(self.publisher.public_status(self.slug)))
    def test_only_author_can_start_publication(self):
        self.assertIsNone(self.store.piece(self.slug)['published_rev'])
        with self.assertRaises(Refused): self.publisher.request(self.slug, 'matias')
        self.assertEqual(self.mock.requests, [])
        self.requested()
        self.assertEqual(self.publisher.get(self.slug)['state'], 'approved')
        self.assertEqual(self.mock.requests, [])
    def test_full_flow_tokens_tree_and_live_identity(self):
        # This sentinel on the draft branch must never reach the public candidate.
        work = self.store._worktree(self.slug); (work / 'private.txt').write_text('Draft-only')
        git(work, 'add', 'private.txt'); git(work, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '-qm', 'Private sentinel')
        self.approved(); pub = self.run_to('published')
        self.assertEqual(len(pub['payload']['urls']), 3)
        self.assertEqual(self.store.piece(self.slug)['published_rev'], pub['payload']['approved_rev'])
        pushes = self.mock.pushes; self.assertEqual(len(pushes), 1)
        self.assertEqual(pushes[0]['actor'], 'javier')
        self.assertTrue(all(p.startswith('editorial/pieces/' + self.slug + '/') for p in pushes[0]['paths']))
        self.assertTrue(pushes[0]['ref'].startswith('refs/heads/studio/'))
        self.assertFalse(any('draft/' in str(r['body']) for r in self.mock.requests))
        pr = [r for r in self.mock.requests if r['method'] == 'POST' and r['path'].endswith('/pulls')][0]
        self.assertEqual(pr['actor'], 'javier'); self.assertEqual(self.mock.count('POST', '/reviews'), 0)
    def test_red_check_never_merges(self):
        self.mock.check = 'failure'; self.approved(); self.run_to('failed')
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)
        self.assertEqual(self.store.piece(self.slug)['state'], 'changes_requested')
    def test_ruleset_precondition_refuses_merge(self):
        self.mock.protection = False; self.approved(); pub = self.run_to('failed')
        self.assertIn('protegida', pub['error_plain']); self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_hidden_bypass_metadata_refuses_merge(self):
        original = self.github.request
        def request(user, method, path, body=None):
            result = original(user, method, path, body)
            if method == 'GET' and path.startswith('/rulesets/'):
                result.pop('bypass_actors', None)
            return result
        self.github.request = request
        self.approved(); pub = self.run_to('failed')
        self.assertIn('protegida', pub['error_plain'])
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_ruleset_refusal_never_uses_another_token(self):
        self.mock.merge_refused = True; self.approved(); pub = self.run_to('failed')
        self.assertIn('GitHub no permitió', pub['error_plain'])
        attempts = [r for r in self.mock.requests if r['method'] == 'PUT' and r['path'].endswith('/merge')]
        self.assertEqual([r['actor'] for r in attempts], ['javier'])
    def test_local_failure_does_not_make_text_public(self):
        self.workspace.check_command = ['python3', '-c', 'import sys; print("FAIL: test_check (fixture.Check.test_check)", file=sys.stderr); print("Private draft text and fixture-secret"); raise SystemExit(1)']
        self.approved(); pub = self.run_to('failed')
        self.assertEqual(self.mock.pushes, []); self.assertEqual(self.mock.prs, {})
        receipt = self.store.data / 'check-results' / (pub['id'] + '.json')
        self.assertEqual(json.loads(receipt.read_text()), {'exit_code': 1, 'failed_tests': [['test_check', 'fixture.Check.test_check']], 'failed_gates': []})
        self.assertNotIn('Private draft', receipt.read_text())
        self.assertNotIn('fixture-secret', receipt.read_text())
        self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
    def test_live_mismatch_is_deployed_unverified(self):
        self.mock.live_id = 'different'; self.approved(); pub = self.run_to('deployed_unverified')
        self.assertNotEqual(self.store.piece(self.slug)['state'], 'published')
        self.assertEqual(pub['payload']['urls'], [])
    def test_lost_responses_reconcile_after_restart_at_each_effect(self):
        self.approved()
        prefix = '/repos/FCMO-AI/FCMO-AI-Newsletter'
        for before, after, method, path in [
            ('candidate', 'pushed', 'POST', '/git/refs'), ('pushed', 'pr_open', 'POST', '/pulls'),
            ('checks_green', 'merged', 'PUT', '/pulls/1/merge')]:
            self.run_to(before); self.mock.drop_after = (method, prefix + path)
            self.publisher.advance(self.slug)
            self.assertEqual(self.publisher.get(self.slug)['state'], before)
            # Reopen DB: no process memory survives; reconcile positive remote state.
            self.store.close(); self.store = Store(self.data / 'data'); self.workspace.store = self.store
            self.publisher = Publisher(self.store, self.github, self.workspace, lambda value: [{'ok': True}])
            self.publisher.advance(self.slug)
            self.assertEqual(self.publisher.get(self.slug)['state'], after)
            self.assertEqual(self.mock.count(method, path), 1)
        self.run_to('published')
    def test_missing_ack_and_no_remote_evidence_does_not_retry(self):
        self.approved(); self.run_to('pushed')
        self.mock.fail_before = ('POST', '/repos/FCMO-AI/FCMO-AI-Newsletter/pulls')
        self.publisher.advance(self.slug); self.mock.fail_before = None
        self.publisher.advance(self.slug)
        self.assertEqual(self.mock.count('POST', '/pulls'), 1)
        self.assertEqual(self.publisher.get(self.slug)['state'], 'pushed')
        self.assertIn('No se confirmó', self.publisher.get(self.slug)['error_plain'])
    def test_restart_at_every_persisted_state(self):
        self.approved()
        for _ in range(10):
            self.store.close(); self.store = Store(self.data / 'data'); self.workspace.store = self.store
            self.publisher = Publisher(self.store, self.github, self.workspace, lambda value: [{'ok': True}])
            self.publisher.advance(self.slug)
            if self.publisher.get(self.slug)['state'] == 'published': break
        self.assertEqual(self.publisher.get(self.slug)['state'], 'published')
    def test_agents_off_correction_and_withdrawal(self):
        jobs = self.store.data / 'jobs'; os.chmod(jobs, 0o500)
        try:
            self.approved(); self.run_to('published')
            self.store.amend(self.slug, 'javier', 'substantive', {'en': 'A corrected claim'})
            self.publisher.request(self.slug, 'javier'); self.run_to('published')
            self.store.amend(self.slug, 'javier', 'withdraw', {'en': 'This essay is withdrawn'}, 'EDITORIAL')
            self.publisher.request(self.slug, 'javier'); self.run_to('published')
            self.assertEqual(self.store.piece(self.slug)['state'], 'withdrawn')
            self.assertEqual(list((jobs / 'queued').iterdir()), [])
        finally: os.chmod(jobs, 0o700)
    def test_unknown_file_and_symlink_are_rejected_before_push(self):
        source = self.store.directory(self.slug)
        (source / 'private.txt').write_text('Unpublished internal note')
        self.approved(); self.run_to('failed')
        self.assertEqual(self.mock.pushes, [])
    def test_candidate_check_does_not_block_writing_another_piece(self):
        import threading
        entered, release, saved = threading.Event(), threading.Event(), threading.Event()
        original = self.workspace.prepare
        def waiting(pub):
            entered.set(); release.wait(5); return original(pub)
        self.workspace.prepare = waiting; self.approved()
        worker = threading.Thread(target=lambda: self.publisher.advance(self.slug)); worker.start()
        self.assertTrue(entered.wait(2))
        def writing():
            second = self.store.create('matias', 'essay', 'Another essay', 'en')['slug']
            self.store.save(second, 'en', 'matias', 0, DOC, {}); saved.set()
        writer = threading.Thread(target=writing); writer.start()
        try: self.assertTrue(saved.wait(2), 'Publication work blocked another author autosave')
        finally: release.set(); worker.join(10); writer.join(10)
    def test_script_or_other_attribute_is_not_live_proof(self):
        parser = PieceHTML('id'); parser.feed('<script>data-piece-id="id"</script><div data-piece-id="id"></div>')
        self.assertFalse(parser.found)
