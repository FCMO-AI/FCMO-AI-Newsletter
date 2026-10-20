from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from ops import publish, publish_ledger, publish_ruleset

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args, data=None):
    return subprocess.run(['git', '-C', str(root), *args], input=data,
                          capture_output=True, check=True).stdout.decode().strip()


class ProtectedPublishingTests(unittest.TestCase):
    def test_local_check_timeout_allows_the_full_regression_suite_to_finish(self):
        calls = []

        def successful_command(command, **kwargs):
            calls.append(kwargs.get('timeout'))
            return subprocess.CompletedProcess(command, 0)

        with patch.object(publish, 'run_command', side_effect=successful_command):
            self.assertEqual(publish.main(['--check']), 0)
        self.assertEqual(calls, [publish.TEST_SUITE_TIMEOUT_SECONDS] + [publish.COMMAND_TIMEOUT_SECONDS] * 7)
        self.assertEqual(publish.TEST_SUITE_TIMEOUT_SECONDS, 3600)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'source'
        self.source.mkdir()
        git(self.source, 'init', '-q')
        git(self.source, 'config', 'user.name', 'Codex')
        git(self.source, 'config', 'user.email', 'noreply@openai.com')
        ledger = self.source / publish_ledger.LEDGER
        ledger.parent.mkdir(parents=True)
        ledger.write_text('{"run_id":"existing","T0":"2026-10-04T00:00:00Z"}\n')
        (self.source / 'edition.txt').write_text('known-good')
        git(self.source, 'add', '.')
        git(self.source, 'commit', '-qm', 'fixture')
        self.sha = git(self.source, 'rev-parse', 'HEAD')
        self.bare = self.base / 'remote.git'
        subprocess.run(['git', 'clone', '--bare', '-q', str(self.source), str(self.bare)], check=True)
        self.before = git(self.bare, 'show-ref')

    def test_dry_run_checks_frozen_bare_snapshot_without_moving_refs(self):
        seen = []
        def checker(root, out, sha):
            seen.append((root.joinpath('edition.txt').read_text(), sha))
            return {'source_commit': sha}
        with patch.object(publish, 'build_and_check', side_effect=checker):
            receipt = publish.dry_run(self.bare, self.sha)
        self.assertEqual(seen, [('known-good', self.sha)])
        self.assertEqual(receipt['mode'], 'dry-run')
        self.assertEqual(git(self.bare, 'show-ref'), self.before)

    def test_failed_gate_returns_no_success_receipt_and_preserves_refs(self):
        with patch.object(publish, 'build_and_check', side_effect=RuntimeError('REMOTE_SCRIPT')):
            with self.assertRaisesRegex(RuntimeError, 'REMOTE_SCRIPT'):
                publish.dry_run(self.bare, self.sha)
        self.assertEqual(git(self.bare, 'show-ref'), self.before)

    def test_actual_gate_rejects_unsafe_edition_before_browser_or_identity(self):
        from tests.test_gates import PublicationGateTests
        fixture = PublicationGateTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.put('index.html', '<html lang="en"><script src="https://example.invalid/unsafe.js"></script></html>')
        calls = []
        real_step = publish.step
        def run_step(root, *args):
            calls.append(args[0])
            if args[0] == 'tools/gates/run_all.py':
                real_step(ROOT, args[0], str(fixture.root))
        with patch.object(publish, 'step', side_effect=run_step):
            # build_and_check creates its output through the mocked builder;
            # use the complete independently constructed edition as that output.
            with self.assertRaisesRegex(RuntimeError, 'publication blocked'):
                publish.build_and_check(ROOT, fixture.root, self.sha)
        self.assertEqual(calls, ['tools/build_ready_receipt.py', 'tools/verify_release.py',
                                 'tools/paper/build.py', 'tools/gates/run_all.py'])
        self.assertNotIn('tools/paper/og_image.py', calls)
        self.assertNotIn('tests/oraculos/verificar_paper.py', calls)
        self.assertFalse((fixture.root / 'deployment-identity.json').exists())

    def test_dry_run_rejects_urls_and_nonbare_repository(self):
        for repository in ('https://example.invalid/repo.git', self.source):
            with self.assertRaises(ValueError):
                publish.dry_run(repository, self.sha)

    def test_migration_defaults_to_plan_without_writing_refs(self):
        plan = publish_ledger.migrate(self.source, self.sha, self.bare)
        self.assertEqual(plan['records'], 1)
        self.assertEqual(git(self.bare, 'show-ref'), self.before)

    def test_migration_preserves_bytes_creates_only_ledger_branch_and_is_idempotent(self):
        result = publish_ledger.migrate(self.source, self.sha, self.bare, apply=True)
        tree = git(self.bare, 'ls-tree', '-r', '--name-only', 'refs/heads/ops-ledger').splitlines()
        self.assertEqual(tree, [publish_ledger.LEDGER])
        self.assertEqual(git(self.bare, 'show', f'refs/heads/ops-ledger:{publish_ledger.LEDGER}'), '{"run_id":"existing","T0":"2026-10-04T00:00:00Z"}')
        self.assertEqual(git(self.bare, 'rev-parse', self.sha), self.sha)
        repeat = publish_ledger.migrate(self.source, self.sha, self.bare, apply=True)
        self.assertEqual(result['ledger_commit'], repeat['ledger_commit'])

    def test_migration_refuses_existing_divergent_ledger(self):
        publish_ledger.migrate(self.source, self.sha, self.bare, apply=True)
        (self.source / publish_ledger.LEDGER).write_text('{"run_id":"changed","T0":"2026-10-04T00:00:00Z"}\n')
        git(self.source, 'add', '.')
        git(self.source, 'commit', '-qm', 'changed')
        with self.assertRaisesRegex(ValueError, 'existing'):
            publish_ledger.migrate(self.source, 'HEAD', self.bare, apply=True)

    def test_ruleset_plan_requires_actions_check_codeowner_and_has_no_bypass(self):
        plan = publish_ruleset.plan('FCMO-AI/FCMO-AI-Newsletter')
        rule = plan['body']
        self.assertEqual(rule['enforcement'], 'active')
        self.assertEqual(rule['bypass_actors'], [])
        self.assertEqual(rule['conditions']['ref_name']['include'], ['refs/heads/main'])
        rules = {r['type']: r.get('parameters', {}) for r in rule['rules']}
        self.assertTrue(rules['pull_request']['require_code_owner_review'])
        self.assertEqual(rules['pull_request']['required_approving_review_count'], 1)
        self.assertTrue(rules['required_status_checks']['strict_required_status_checks_policy'])
        self.assertEqual(rules['required_status_checks']['required_status_checks'],
                         [{'context': 'publish-gate', 'integration_id': 15368}])
        self.assertNotIn('apply', plan)

    def test_dispatch_is_fixed_main_and_arguments_never_enter_a_shell(self):
        with patch.object(publish.subprocess, 'run') as run:
            publish.dispatch('deploy')
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['gh', 'workflow', 'run', 'pages.yml', '--repo',
                                  'FCMO-AI/FCMO-AI-Newsletter', '--ref', 'main',
                                  '--field', 'operation=deploy'])
        self.assertFalse(kwargs.get('shell', False))
        with self.assertRaises(ValueError):
            publish.dispatch('$(touch owned)')

    def test_required_workflow_has_no_path_skip_and_no_write_credentials(self):
        text = (ROOT / '.github/workflows/publish-gate.yml').read_text()
        publish_source = (ROOT / 'ops/publish.py').read_text()
        self.assertIn('name: publish-gate', text)
        self.assertIn('timeout-minutes: 60', text)
        self.assertIn('pull_request:', text)
        self.assertNotIn('paths:', text)
        self.assertNotIn('pull_request_target', text)
        self.assertIn('persist-credentials: false', text)
        self.assertIn('contents: read', text)
        self.assertNotIn('contents: write', text)
        self.assertNotIn('secrets.', text)
        self.assertNotIn('run: python3 -m unittest discover -s tests', text)
        self.assertIn("[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']", publish_source)
        self.assertIn('TEST_SUITE_TIMEOUT_SECONDS = 3600', publish_source)
        self.assertIn('python3 ops/publish.py --check --tests-prevalidated', text)
        self.assertIn('tools/unittest_shards.py --index ${{ matrix.shard }} --count 8', text)

    def test_publish_check_gives_only_the_suite_its_measured_budget(self):
        from unittest.mock import patch
        with patch.object(publish, 'run_command', return_value=Mock(returncode=0)) as run:
            self.assertEqual(publish.main(['--check']), 0)
        timeouts = [call.kwargs['timeout'] for call in run.call_args_list]
        self.assertEqual(timeouts, [3600, 1800, 1800, 1800, 1800, 1800, 1800, 1800])

    def test_prevalidated_check_skips_only_the_suite(self):
        with patch.object(publish, 'run_command', return_value=Mock(returncode=0)) as run:
            self.assertEqual(publish.main(['--check', '--tests-prevalidated']), 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 7)
        self.assertNotIn([publish.sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], commands)
        self.assertIn([publish.sys.executable, 'tools/verify_release.py'], commands)
        self.assertIn([publish.sys.executable, 'tools/paper/build.py', '--stories',
                       'site/data/stories.v2.json', '--status', 'site/data/newsroom-status.json',
                       '--editorial', 'editorial', '--out', str(publish.ROOT / 'publish'),
                       '--base', '/FCMO-AI-Newsletter/'], commands)

    def test_prevalidated_suite_flag_is_rejected_outside_check_mode(self):
        with self.assertRaises(SystemExit) as error:
            publish.main(['--publish', '--tests-prevalidated'])
        self.assertEqual(error.exception.code, 2)

    def test_release_integrity_waits_for_all_complete_suite_shards(self):
        import yaml
        workflow = yaml.safe_load((ROOT / '.github/workflows/release-validate.yml').read_text())
        regression = workflow['jobs']['regression']
        self.assertEqual(regression['strategy']['matrix']['shard'], list(range(8)))
        self.assertIs(regression['strategy']['fail-fast'], False)
        self.assertIn('tools/unittest_shards.py --index ${{ matrix.shard }} --count 8',
                      regression['steps'][-1]['run'])
        gate = workflow['jobs']['publish-gate']
        self.assertEqual(gate['name'], 'release-integrity')
        self.assertEqual(gate['needs'], 'regression')
        self.assertEqual(gate['steps'][-3]['run'],
                         'python ops/publish.py --check --tests-prevalidated')

    def test_required_check_name_has_a_single_owner(self):
        import yaml
        owners = [(path.name, key) for path in (ROOT / '.github/workflows').glob('*.yml')
                  for key, job in yaml.safe_load(path.read_text()).get('jobs', {}).items()
                  if job.get('name', key) == 'publish-gate']
        self.assertEqual(owners, [('publish-gate.yml', 'publish-gate')])

    def test_pages_manual_publish_cannot_run_from_unreviewed_branch(self):
        text = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn("github.ref == 'refs/heads/main'", text)
        # The full suite runs as complete parallel shards that the build needs.
        self.assertIn('python3 tools/unittest_shards.py --index ${{ matrix.shard }} --count 8', text)
        self.assertIn('needs: regression', text)
        self.assertIn('python3 tools/verify_release.py', text)


if __name__ == '__main__':
    unittest.main()
