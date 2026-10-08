"""Actions-only protection, credential isolation and reversible host activation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ops.studio.protect_main import desired, assert_autonomous_compatible
from studio.server.credentials import GitHubCLI
from studio.server.publishing import Refused
from tests import test_studio_auth as auth_fixture

ROOT = Path(__file__).resolve().parents[1]


class Protection(unittest.TestCase):
    def test_conflicting_existing_rules_are_detected_before_apply(self):
        def responses(method, path, **kwargs):
            if path.startswith('/rules/branches/main'):
                return [{'type': 'pull_request', 'ruleset_id': 8}]
            if path == '/rulesets/8': return {'bypass_actors': []}
            return None
        with patch('ops.studio.protect_main.api', side_effect=responses) as api:
            with self.assertRaisesRegex(ValueError, 'blocks autonomous'): assert_autonomous_compatible(7)
            self.assertTrue(all(call.args[0] == 'GET' for call in api.call_args_list))
        def compatible(method, path, **kwargs):
            if path.startswith('/rules/branches/main'):
                return [{'type': 'pull_request', 'ruleset_id': 8}]
            if path == '/rulesets/8': return desired()
            return None
        with patch('ops.studio.protect_main.api', side_effect=compatible): assert_autonomous_compatible(7)

    def test_dry_run_is_offline_and_has_only_actions_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, PATH='/usr/bin:/bin', GH_CONFIG_DIR=tmp)
            plan = json.loads(subprocess.check_output(['sh', str(ROOT / 'ops/studio/protect-main.sh'), '--dry-run'], env=env))
        self.assertEqual(plan['bypass_actors'], [{'actor_type': 'Integration', 'actor_id': 15368, 'bypass_mode': 'always'}])
        self.assertEqual(plan['conditions']['ref_name']['include'], ['refs/heads/main'])
        pull = next(r['parameters'] for r in plan['rules'] if r['type'] == 'pull_request')
        self.assertEqual(pull['required_approving_review_count'], 1)
        self.assertTrue(pull['require_code_owner_review'])
        owners = (ROOT / '.github/CODEOWNERS').read_text()
        self.assertNotIn('REPLACE_WITH_', owners)
        for path in ('/editorial/', '/studio/', '/ops/studio/', '/.github/workflows/', '/.github/CODEOWNERS'):
            self.assertIn(path + ' @javo-27 @Magyarmex', owners)

    def test_effective_protection_accepts_actions_and_refuses_every_other_bypass(self):
        from studio.server.publishing import GitHub
        github = GitHub({})
        plan = desired()
        rules = [{**r, 'ruleset_id': 7} for r in plan['rules']]
        for actors, accepted in ((plan['bypass_actors'], True), ([], True), (None, False),
                                 ([{'actor_type': 'RepositoryRole', 'actor_id': 5, 'bypass_mode': 'always'}], False),
                                 ([{**plan['bypass_actors'][0], 'actor_id': 1234}], False),
                                 (plan['bypass_actors'] + [{'actor_type': 'User', 'actor_id': 123}], False)):
            with self.subTest(actors=actors), patch.object(github, 'request', side_effect=lambda u, m, p: rules if p == '/rules/branches/main' else {'enforcement': 'active', 'bypass_actors': actors}):
                self.assertEqual(github.protected('javier'), accepted)


class Credentials(unittest.TestCase):
    def test_missing_accounts_are_named_and_never_use_an_ambient_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'GH_CONFIG_DIR': tmp, 'GH_TOKEN': 'fixture', 'GITHUB_TOKEN': 'fixture'}):
            github = GitHubCLI({u: str(Path(tmp) / u) for u in ('javier', 'matias')})
            with patch('studio.server.credentials.subprocess.run') as run:
                statuses = github.credential_status()
                self.assertEqual([s['plain_es'] for s in statuses], ['Javier debe iniciar sesión en GitHub.', 'Matías debe iniciar sesión en GitHub.'])
                with self.assertRaisesRegex(Refused, 'Javier'): github.identity('javier')
                run.assert_not_called()
            for u in ('javier', 'matias'):
                env = github.environment(u)
                self.assertEqual(env['GH_CONFIG_DIR'], str(Path(tmp) / u))
                self.assertNotIn('GH_TOKEN', env); self.assertNotIn('GITHUB_TOKEN', env)


class ReadinessHTTP(unittest.TestCase):
    setUp = auth_fixture.AuthHTTP.setUp
    tearDown = auth_fixture.AuthHTTP.tearDown
    request = auth_fixture.AuthHTTP.request
    login = auth_fixture.AuthHTTP.login
    def test_readiness_requires_session_and_does_not_block_writing(self):
        self.assertEqual(self.request('GET', '/api/publication-readiness')[0], 401)
        self.login()
        with tempfile.TemporaryDirectory() as tmp:
            self.app.github = GitHubCLI({u: str(Path(tmp) / u) for u in ('javier', 'matias')})
            status, body, _ = self.request('GET', '/api/publication-readiness')
            self.assertEqual(status, 200)
            self.assertFalse(any(c['ready'] for c in body['credentials']))
            self.assertEqual(self.request('POST', '/api/pieces', {'kind': 'essay', 'title': 'Private writing', 'source_locale': 'en'})[0], 200)


class HostService(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('service_install', ROOT / 'studio/host-ops/service_install.py')
        self.module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.module)
        # Unit tests simulate the host account; they never install on the runner.
        user = patch.object(self.module.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='fcmo-agent'))
        user.start()
        self.addCleanup(user.stop)

    def test_other_accounts_are_refused_before_commands_or_filesystem_changes(self):
        for name in ('runner', 'root'):
            with self.subTest(user=name), tempfile.TemporaryDirectory() as tmp, \
                    patch.object(self.module.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name=name)), \
                    patch.object(Path, 'home', return_value=Path(tmp)), \
                    patch('sys.argv', ['install']), patch.object(self.module, 'command') as command:
                with self.assertRaisesRegex(ValueError, 'Run as fcmo-agent, without sudo'):
                    self.module.main()
                command.assert_not_called()
                self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_install_and_rollback_restore_unit_and_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp); target = home / '.config/systemd/user/fcmo-studio.service'
            target.parent.mkdir(parents=True); target.write_bytes(b'previous unit')
            environment = home / '.config/fcmo-studio/studio.env'
            environment.parent.mkdir(); environment.write_text('STUDIO_BIND=127.0.0.1\nSTUDIO_PORT=8490\n'); environment.chmod(0o600)
            calls = []
            def command(*args, **kwargs):
                calls.append(args)
                output = 'enabled\n' if 'is-enabled' in args else 'active\n' if 'is-active' in args else ''
                return subprocess.CompletedProcess(args, 0, output, '')
            with patch.object(Path, 'home', return_value=home), patch.object(self.module, 'command', side_effect=command), patch.object(self.module, 'validate_credentials'), patch('sys.argv', ['install']):
                self.module.main()
                self.assertEqual(target.read_bytes(), self.module.SOURCE.read_bytes())
                self.assertIn(('systemctl', '--user', 'enable', '--now', 'fcmo-studio.service'), calls)
                with patch('sys.argv', ['rollback', '--rollback']): self.module.main()
            self.assertEqual(target.read_bytes(), b'previous unit')
            self.assertIn(('systemctl', '--user', 'start', 'fcmo-studio.service'), calls)

    def test_no_user_manager_has_no_installation_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(Path, 'home', return_value=Path(tmp)), patch('sys.argv', ['install']), patch.object(self.module, 'command', side_effect=subprocess.CalledProcessError(1, 'systemctl')):
            with self.assertRaises(subprocess.CalledProcessError): self.module.main()
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == '__main__': unittest.main()
