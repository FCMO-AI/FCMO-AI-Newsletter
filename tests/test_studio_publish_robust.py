"""Publication survives a moving main, slow/cancelled Pages and infrastructure trouble.

Every case drives the real Publisher + Workspace against the offline GitHub double and real
local git trees; time is a controlled clock so budgets of hours run in milliseconds.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from studio.translation import FakeProvider
from studio.server.storage import Store, git
from studio.server.publishing import GitHub, Workspace, Publisher, Refused
from tests.harness.mock_github import MockGitHub
from tests.test_studio_storage import DOC, ROOT

PREFIX = '/repos/FCMO-AI/FCMO-AI-Newsletter'

class World(MockGitHub):
    """The measured GitHub: Pages runs, compare, commit file lists, CODEOWNERS and mergeability are scriptable."""
    def __init__(self):
        super().__init__()
        self.runs = None; self.descends = {}; self.merge_files = None; self.codeowners = True
        self.unprotected_merge = False; self.conflict_once = False; self.account_id = {'javier': 111, 'matias': 222}
    def dispatch(self, actor, method, path, query, body):
        route = path.removeprefix(PREFIX)
        if path == '/user' and actor: return 200, {'login': actor, 'id': self.account_id[actor]}
        if route.startswith('/compare/'):
            pair = tuple(route.removeprefix('/compare/').split('...'))
            return 200, {'status': self.descends.get(pair, 'diverged')}
        if route.startswith('/contents/'):
            return (200, {'type': 'file'}) if self.codeowners else (404, {})
        if route == '/actions/workflows/pages.yml/runs' and self.runs is not None:
            rows = [r for r in self.runs() if query.get('status') != ['success'] or r['conclusion'] == 'success']
            return 200, {'workflow_runs': rows}
        if route.startswith('/commits/') and not route.endswith('/check-runs'):
            files = self.merge_files if self.merge_files is not None else [{'filename': self.piece_rel + '/piece.json'}]
            return 200, {'sha': route.rsplit('/', 1)[1], 'files': files}
        if route.startswith('/pulls/') and route.endswith('/merge') and self.unprotected_merge:
            number = int(route.split('/')[2]); pr = self.prs[number]
            if body['sha'] != pr['head']['sha']: return 409, {}
            pr['merged'] = True; pr['state'] = 'closed'; pr['merge_commit_sha'] = 'f' * 40
            return 200, {'merged': True, 'sha': 'f' * 40}
        status, value = super().dispatch(actor, method, path, query, body)
        if status == 200 and isinstance(value, dict) and route.startswith('/pulls/') and route.count('/') == 2 and self.conflict_once:
            value['mergeable'] = False
        return status, value

class Robust(unittest.TestCase):
    def setUp(self):
        provider = patch('studio.translation.configured_provider', return_value=FakeProvider())
        provider.start(); self.addCleanup(provider.stop)
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit'); self.data = Path(self.tmp.name)
        self.now = 1_000_000.0
        self.store = Store(self.data / 'data', clock=lambda: self.now)
        self.slug = self.store.create('javier', 'essay', 'Private essay', 'en')['slug']
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        self.remote = self.data / 'remote'; self.remote.mkdir(); git(self.remote, 'init', '-q', '-b', 'main')
        (self.remote / 'base.txt').write_text('Public base')
        git(self.remote, 'add', '.'); git(self.remote, '-c', 'user.name=Bot', '-c', 'user.email=bot@example.invalid', 'commit', '-qm', 'Base')
        git(self.store.data / 'clone', 'remote', 'set-url', 'origin', str(self.remote))
        self.mock = World().__enter__(); self.mock.piece_rel = 'editorial/pieces/' + self.slug
        self.github = GitHub({'javier': 'fixture-javier', 'matias': 'fixture-matias'}, self.mock.url, live_base=self.mock.url + '/live/')
        self.mock.refs['main'] = git(self.remote, 'rev-parse', 'HEAD')
        mock = self.mock
        class MockWorkspace(Workspace):
            def push(self, pub):
                data = pub['payload']; paths = git(Path(data['candidate']), 'diff', '--name-only', 'refs/remotes/origin/main', 'HEAD').splitlines()
                self.github.request(data['author'], 'POST', '/git/refs', {'ref': 'refs/heads/' + data['branch'], 'sha': data['head_sha'], 'paths': paths})
            def repush(self, pub, old):
                data = pub['payload']; mock.refs[data['branch']] = data['head_sha']; mock.prs[data['pr_number']]['head']['sha'] = data['head_sha']; mock.conflict_once = False
        self.workspace = MockWorkspace(self.store, self.github, ['python3', '-c', 'raise SystemExit(0)'])
        self.publisher = Publisher(self.store, self.github, self.workspace, lambda value: [{'ok': True}])
        self.mock.live_id = self.store.payload(self.slug)['piece']['id']
        self.commits = 0
    def tearDown(self):
        self.mock.__exit__(); self.store.close(); self.tmp.cleanup()
    def move_main(self):
        self.commits += 1
        (self.remote / 'bot.txt').write_text('bot commit %d' % self.commits)
        git(self.remote, 'add', '.'); git(self.remote, '-c', 'user.name=Bot', '-c', 'user.email=bot@example.invalid', 'commit', '-qm', 'bot %d' % self.commits)
        self.mock.refs['main'] = git(self.remote, 'rev-parse', 'HEAD')
    def approved(self):
        self.publisher.request(self.slug, 'javier'); return self.publisher.approve(self.slug, 'matias')
    def pub(self): return self.publisher.get(self.slug)
    def states(self, ticks, step=120, before=None):
        seen = []
        for _ in range(ticks):
            if before: before()
            self.publisher.advance(self.slug); seen.append(self.pub()['state'])
            if seen[-1] in ('published', 'failed'): break
            self.now += step
        return seen
    def run_to(self, target, ticks=400, step=120, before=None):
        seen = self.states(ticks, step, before)
        self.assertEqual(self.pub()['state'], target, (seen[-5:], self.pub().get('error_plain')))
        return self.pub()
    def tick_until(self, state, ticks=40):
        for _ in range(ticks):
            if self.pub()['state'] == state: return
            self.publisher.advance(self.slug)
        self.fail('never reached ' + state)

    def test_main_moves_every_step_still_publishes(self):
        self.approved(); first_base = None
        def churn():
            nonlocal first_base
            self.move_main()
        pub = self.run_to('published', before=churn)
        self.assertEqual(self.mock.count('POST', '/reviews'), 1, 'no second human approval')
        data = pub['payload']
        # The candidate was replayed on the newest main before the push and carries only the approved bytes.
        self.assertNotEqual(data['base_sha'], '')
        self.assertTrue(all(p.startswith('editorial/pieces/' + self.slug + '/') for p in self.mock.pushes[0]['paths']))
        self.assertEqual(self.store.piece(self.slug)['published_rev'], data['approved_rev'])

    def test_candidate_is_replayed_on_moved_base_without_new_approval(self):
        self.approved(); self.tick_until('candidate'); old = self.pub()['payload']
        self.move_main(); self.move_main()
        self.tick_until('pushed'); new = self.pub()['payload']
        self.assertNotEqual(old['head_sha'], new['head_sha'])
        self.assertEqual(new['base_sha'], self.mock.refs['main'])
        self.assertEqual(git(Path(new['candidate']), 'rev-parse', new['head_sha'] + '^'), self.mock.refs['main'])
        self.assertEqual(git(Path(new['candidate']), 'rev-parse', 'HEAD:' + new['rel']), old['content_tree'])
        self.assertEqual(self.mock.refs[new['branch']], new['head_sha'])

    def test_conflict_replays_same_bytes_and_publishes(self):
        self.approved(); self.tick_until('checks_green'); tree = self.pub()['payload']['content_tree']
        self.move_main(); self.mock.conflict_once = True
        pub = self.run_to('published')
        self.assertEqual(self.mock.count('POST', '/reviews'), 2, 'reviewer APPROVE republished on the new sha, automatically')
        self.assertEqual(git(Path(pub['payload']['candidate']), 'rev-parse', 'HEAD:' + pub['payload']['rel']), tree)
        self.assertEqual(self.store.piece(self.slug)['published_rev'], pub['payload']['approved_rev'])

    def test_pages_run_cancelled_later_run_deploys_publishes(self):
        merge = 'f' * 40; later = 'a' * 40
        self.mock.descends[(merge, later)] = 'ahead'
        self.mock.runs = lambda: [{'id': 9, 'head_sha': later, 'event': 'schedule', 'status': 'completed', 'conclusion': 'success'},
                                  {'id': 8, 'head_sha': merge, 'event': 'push', 'status': 'completed', 'conclusion': 'cancelled'}]
        self.approved(); pub = self.run_to('published')
        self.assertEqual(pub['payload']['pages_run'], 9)

    def test_cancelled_only_run_is_not_a_failure(self):
        merge = 'f' * 40
        self.mock.runs = lambda: [{'id': 8, 'head_sha': merge, 'event': 'push', 'status': 'completed', 'conclusion': 'cancelled'}]
        self.approved(); seen = self.states(40, step=300)
        self.assertNotIn('failed', seen); self.assertEqual(self.pub()['state'], 'merged')
        self.assertNotEqual(self.store.piece(self.slug)['state'], 'changes_requested')

    def test_unrelated_success_run_does_not_deploy(self):
        self.mock.runs = lambda: [{'id': 9, 'head_sha': 'b' * 40, 'event': 'push', 'status': 'completed', 'conclusion': 'success'}]
        self.approved(); self.states(40, step=300)
        self.assertEqual(self.pub()['state'], 'merged')

    def test_deploy_70min_publishes(self):
        # Gate takes 40 min (> the old 30 min clock origin bug), Pages 70 min after the merge.
        start = self.now; self.mock.check = 'pending'; merged_at = []
        def runs():
            at = merged_at[0] if merged_at else None
            ready = at is not None and self.now - at >= 70 * 60
            return [{'id': 8, 'head_sha': 'f' * 40, 'event': 'push', 'status': 'completed', 'conclusion': 'success'}] if ready else []
        self.mock.runs = runs; self.approved()
        def clock_effects():
            if self.now - start >= 40 * 60: self.mock.check = 'success'
            if self.pub()['state'] == 'merged' and not merged_at: merged_at.append(self.now)
        pub = self.run_to('published', step=300, before=clock_effects)
        self.assertGreaterEqual(self.now - merged_at[0], 70 * 60)
        self.assertNotIn('failed', [t['state'] for t in pub['payload']['timeline']])

    def test_post_merge_never_failed(self):
        self.mock.runs = lambda: []; self.mock.live_status = 404
        self.approved(); self.tick_until('merged')
        # Pages "fails" loudly: GitHub refusing the call after the merge must not undo anything.
        with patch.object(self.github, 'pages', side_effect=Refused('El despliegue falló.')):
            seen = self.states(10)
        self.assertNotIn('failed', seen)
        self.now += 5 * 3600; seen = self.states(5, step=600)
        self.assertEqual(self.pub()['state'], 'deployed_unverified')
        self.now += 7 * 3600; seen = self.states(4, step=700)
        pub = self.pub()
        self.assertEqual(pub['state'], 'deployed_unverified'); self.assertTrue(pub['payload'].get('unknown'))
        self.assertIn('Matías', pub['error_plain'])
        self.assertEqual(self.store.piece(self.slug)['state'], 'publishing')
        self.mock.live_status = 200; self.now += 700; self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['state'], 'published')
        self.assertFalse(self.pub()['payload'].get('unknown'))

    def test_infra_retry_no_reapproval(self):
        self.mock.check = 'cancelled'; self.approved(); self.tick_until('reviewed')
        self.publisher.advance(self.slug); first = self.pub()
        self.assertEqual(first['state'], 'reviewed'); self.assertEqual(first['payload']['infra_retries'], 1)
        self.assertIn('reintentará', first['error_plain'])
        self.publisher.advance(self.slug)  # backoff: not yet due, nothing happens
        self.assertEqual(self.pub()['payload']['infra_retries'], 1)
        self.mock.check = 'success'; self.now += 61
        pub = self.run_to('published')
        self.assertEqual(self.mock.count('POST', '/reviews'), 1)
        self.assertEqual(self.mock.count('POST', '/pulls'), 1)
        self.assertNotIn('failed', [t['state'] for t in pub['payload']['timeline']])

    def test_infra_exhausted_halts_but_keeps_approval(self):
        self.mock.check = 'cancelled'; self.approved(); self.tick_until('reviewed')
        for _ in range(8):
            self.publisher.advance(self.slug); self.now += 600
        pub = self.pub()
        self.assertEqual(pub['state'], 'reviewed'); self.assertTrue(pub['payload']['halted'])
        self.assertEqual(self.store.piece(self.slug)['state'], 'publishing')
        self.assertIn('no por el texto', pub['error_plain'])

    def test_gate_slow_beyond_budget_is_infrastructure(self):
        self.mock.check = 'pending'; self.approved(); self.tick_until('reviewed')
        self.publisher.advance(self.slug); self.now += 61 * 60; self.publisher.advance(self.slug)
        pub = self.pub(); self.assertEqual(pub['state'], 'reviewed'); self.assertEqual(pub['payload']['infra_retries'], 1)

    def test_content_red_returns_changes(self):
        self.mock.check = 'failure'; self.approved(); self.run_to('failed')
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)
        self.assertEqual(self.store.piece(self.slug)['state'], 'changes_requested')

    def test_commit_uses_author_github_noreply(self):
        self.approved(); self.tick_until('pushed')
        data = self.pub()['payload']
        self.assertEqual(self.mock.refs[data['branch']], data['head_sha'])
        self.assertEqual(git(Path(data['candidate']), 'log', '-1', '--format=%ae'), '111+javier@users.noreply.github.com')
        self.assertNotIn('openai', git(Path(data['candidate']), 'log', '-1', '--format=%ae %an %cn %ce'))

    # --- STUDIO_PROTECTION_MODE=studio -------------------------------------------------
    def studio_mode(self):
        self.mock.protection = False; self.mock.unprotected_merge = True
        patcher = patch.dict(os.environ, {'STUDIO_PROTECTION_MODE': 'studio'}); patcher.start(); self.addCleanup(patcher.stop)
    def test_default_mode_is_github_and_fail_safe(self):
        self.mock.protection = False; self.approved(); pub = self.run_to('failed')
        self.assertIn('protegida', pub['error_plain']); self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_studio_mode_publishes_and_records_mode(self):
        self.studio_mode(); self.approved(); pub = self.run_to('published')
        self.assertEqual(pub['payload']['protection_mode'], 'studio')
        self.assertIn('Modo de protección: studio', [r for r in self.mock.requests if r['method'] == 'POST' and r['path'].endswith('/pulls')][0]['body']['body'])
        self.assertTrue(all(t.get('protection_mode') == 'studio' for t in pub['payload']['timeline'] if t['state'] not in ('approved', 'candidate', 'pushed')))
    def test_studio_mode_requires_distinct_approve_and_green_gate(self):
        # (a) the APPROVE disappears (dismissed): no merge.
        self.studio_mode(); self.approved(); self.tick_until('checks_green'); self.mock.reviews.clear()
        self.publisher.advance(self.slug); pub = self.pub()
        self.assertEqual(pub['state'], 'failed'); self.assertIn('revisión de la otra persona', pub['error_plain']); self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_studio_mode_gate_must_still_be_green(self):
        self.studio_mode(); self.approved(); self.tick_until('checks_green'); self.mock.check = 'pending'
        self.publisher.advance(self.slug); self.assertEqual(self.pub()['state'], 'failed'); self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_studio_mode_same_account_is_refused(self):
        self.studio_mode(); self.approved(); self.tick_until('checks_green')
        with patch.object(self.github, 'identity', return_value='one-person'):
            self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['state'], 'failed'); self.assertIn('dos cuentas', self.pub()['error_plain'])
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_studio_mode_requires_codeowners(self):
        self.studio_mode(); self.mock.codeowners = False; self.approved(); pub = self.run_to('failed')
        self.assertIn('CODEOWNERS', pub['error_plain']); self.assertEqual(self.mock.count('PUT', '/merge'), 0)
    def test_unknown_mode_fails_closed(self):
        with patch.dict(os.environ, {'STUDIO_PROTECTION_MODE': 'off'}):
            self.approved(); pub = self.run_to('failed')
        self.assertEqual(self.mock.count('PUT', '/merge'), 0)

    # --- the diff of the merge stays inside the piece ------------------------------------
    def test_merge_diff_outside_piece_refused(self):
        # Before the push: a candidate carrying anything but the approved bytes is refused.
        self.approved(); self.tick_until('candidate'); pub = self.pub(); data = pub['payload']; target = Path(data['candidate'])
        (target / 'intruder.txt').write_text('x'); git(target, 'add', 'intruder.txt')
        git(target, '-c', 'user.name=T', '-c', 'user.email=t@example.invalid', 'commit', '-qm', 'tamper')
        data['head_sha'] = git(target, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(Refused, 'fuera del artículo'): self.workspace.verify_confined(pub)
        # Tampering with the approved bytes themselves is refused too.
        git(target, 'reset', '-q', '--hard', 'HEAD~1'); (target / data['rel'] / 'piece.json').write_text('{}')
        git(target, '-c', 'user.name=T', '-c', 'user.email=t@example.invalid', 'commit', '-qam', 'edit'); data['head_sha'] = git(target, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(Refused, 'cambió'): self.workspace.verify_confined(pub)
    def test_merge_diff_outside_piece_after_merge_halts_without_failing(self):
        self.mock.merge_files = [{'filename': 'editorial/pieces/' + self.slug + '/piece.json'}, {'filename': '.github/workflows/pages.yml'}]
        self.approved(); self.tick_until('merged'); self.publisher.advance(self.slug)
        pub = self.pub()
        self.assertEqual(pub['state'], 'merged'); self.assertEqual(pub['payload']['merge_diff'], 'outside'); self.assertTrue(pub['payload']['halted'])
        self.assertEqual(self.store.piece(self.slug)['state'], 'publishing')
        before = self.mock.count('GET', '/runs'); self.publisher.advance(self.slug); self.assertEqual(self.mock.count('GET', '/runs'), before)


class RehearsalGuard(unittest.TestCase):
    def build(self, **env):
        with patch.dict(os.environ, env, clear=False):
            for key in ('STUDIO_PUBLISH_REPO', 'STUDIO_REHEARSAL', 'STUDIO_LIVE_ENABLED'):
                if key not in env: os.environ.pop(key, None)
            return GitHub({})
    def test_default_is_public_repo(self):
        self.assertEqual(self.build().repo, 'FCMO-AI/FCMO-AI-Newsletter')
    def test_override_needs_rehearsal(self):
        with self.assertRaises(Refused): self.build(STUDIO_PUBLISH_REPO='example/rehearsal')
        self.assertEqual(self.build(STUDIO_PUBLISH_REPO='example/rehearsal', STUDIO_REHEARSAL='1', STUDIO_LIVE_ENABLED='1').repo, 'example/rehearsal')
    def test_live_rehearsal_on_public_repo_is_refused(self):
        with self.assertRaises(Refused): self.build(STUDIO_REHEARSAL='1', STUDIO_LIVE_ENABLED='1')
        with self.assertRaises(Refused): self.build(STUDIO_REHEARSAL='1', STUDIO_LIVE_ENABLED='1', STUDIO_PUBLISH_REPO='FCMO-AI/FCMO-AI-Newsletter')
        self.assertEqual(self.build(STUDIO_REHEARSAL='1').repo, 'FCMO-AI/FCMO-AI-Newsletter')

if __name__ == '__main__': unittest.main()
