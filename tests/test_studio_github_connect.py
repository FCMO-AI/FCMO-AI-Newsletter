import os
from pathlib import Path
import stat
import tempfile
import time
import unittest
from unittest.mock import patch

from tests import test_studio_auth as auth_fixture
from studio.server.credentials import GitHubCLI
from studio.server.http import Handler


class GitHubConnectHTTP(unittest.TestCase):
    setUp = auth_fixture.AuthHTTP.setUp
    tearDown = auth_fixture.AuthHTTP.tearDown
    request = auth_fixture.AuthHTTP.request
    login = auth_fixture.AuthHTTP.login

    def setUpFake(self, script):
        self.login()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        fake = root / 'gh'
        prefix = """import os, sys
if sys.argv[1:3] == ['auth', 'status']:
    raise SystemExit(0 if os.path.isfile(os.path.join(os.environ['GH_CONFIG_DIR'], 'hosts.yml')) else 1)
"""
        fake.write_text('#!/usr/bin/env python3\n' + prefix + script)
        fake.chmod(0o700)
        self.config = root / 'javier-config'
        self.other_config = root / 'matias-config'
        self.app.github = GitHubCLI({'javier': str(self.config), 'matias': str(self.other_config)})
        from studio.server.github_connect import GitHubConnect
        self.app.github_connect = GitHubConnect(self.app.github)
        self.old_path = os.environ.get('PATH', '')
        self.path_patch = patch.dict(os.environ, {'PATH': str(root) + os.pathsep + self.old_path,
                                                   'GH_TOKEN': 'must-not-leak',
                                                   'GITHUB_TOKEN': 'must-not-leak'})
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def wait_for(self, predicate, timeout=3):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if predicate(): return True
            time.sleep(.02)
        return predicate()

    def test_connect_returns_device_code_and_exact_url_for_own_account(self):
        self.setUpFake("""import os, sys, time
assert os.environ.get('GH_TOKEN') is None
assert os.environ.get('GITHUB_TOKEN') is None
assert os.environ.get('BROWSER') == 'true'
assert sys.stdin.read() == '\\n'
print('! First copy your one-time code: ABCD-EFGH', flush=True)
print('Open this URL to continue in your web browser: https://github.com/login/device', flush=True)
time.sleep(.15)
os.makedirs(os.environ['GH_CONFIG_DIR'], exist_ok=True)
open(os.path.join(os.environ['GH_CONFIG_DIR'], 'hosts.yml'), 'w').write('github.com: {}\\n')
""")
        status, body, _ = self.request('POST', '/api/github/connect')
        self.assertEqual(status, 200)
        self.assertEqual(body['code'], 'ABCD-EFGH')
        self.assertEqual(body['url'], 'https://github.com/login/device')
        self.assertTrue(self.wait_for(lambda: self.request('GET', '/api/github/connect')[1]['state'] == 'ready'))
        self.assertTrue(self.app.github.credential_status()[0]['ready'])
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o700)
        self.assertFalse((self.config / 'hosts.yml').read_text().startswith('ABCD-EFGH'))
        persisted = [p.read_bytes() for p in self.app.store.data.rglob('*') if p.is_file()]
        persisted += [p.read_bytes() for p in self.config.rglob('*') if p.is_file()]
        self.assertFalse(any(b'ABCD-EFGH' in content for content in persisted))

    def test_session_cannot_start_or_read_another_person_connection(self):
        self.setUpFake("import time; time.sleep(2)\n")
        status, body, _ = self.request('POST', '/api/github/connect', {'user': 'matias'})
        self.assertEqual(status, 200)
        self.assertEqual(body['user'], 'javier')
        self.assertEqual(self.request('GET', '/api/github/connect?user=matias')[1]['user'], 'javier')

    def test_timeout_and_cancel_are_visible_without_exposing_process_output(self):
        self.setUpFake("""import time
print('! First copy your one-time code: WXYZ-1234', flush=True)
print('Open this URL to continue in your web browser: https://github.com/login/device', flush=True)
time.sleep(10)
""")
        self.app.github_connect.timeout = .2
        with patch('studio.server.github_connect.LOGIN_TIMEOUT', .2):
            status, body, _ = self.request('POST', '/api/github/connect')
            self.assertEqual(status, 200)
            self.assertEqual(body['code'], 'WXYZ-1234')
            self.assertTrue(self.wait_for(lambda: self.request('GET', '/api/github/connect')[1]['state'] == 'timeout'))
        status, _, _ = self.request('POST', '/api/github/connect')
        self.assertEqual(status, 200)
        self.assertEqual(self.request('DELETE', '/api/github/connect')[0], 200)
        self.assertTrue(self.wait_for(lambda: self.request('GET', '/api/github/connect')[1]['state'] == 'cancelled'))

    def test_ready_connection_whose_credential_vanished_can_start_again(self):
        self.setUpFake("""import os, time
print('! First copy your one-time code: AGAI-N123', flush=True)
print('Open this URL to continue in your web browser: https://github.com/login/device', flush=True)
time.sleep(.1)
os.makedirs(os.environ['GH_CONFIG_DIR'], exist_ok=True)
open(os.path.join(os.environ['GH_CONFIG_DIR'], 'hosts.yml'), 'w').write('github.com: {}\\n')
""")
        self.assertEqual(self.request('POST', '/api/github/connect')[0], 200)
        self.assertTrue(self.wait_for(lambda: self.request('GET', '/api/github/connect')[1]['state'] == 'ready'))
        (self.config / 'hosts.yml').unlink()  # session closed or token revoked, Studio not restarted
        self.assertFalse(self.app.github.credential_status()[0]['ready'])
        self.assertEqual(self.request('GET', '/api/github/connect')[1]['state'], 'ready')
        status, body, _ = self.request('POST', '/api/github/connect')  # what the card's «Empezar» sends
        self.assertEqual(status, 200)
        self.assertEqual(body['code'], 'AGAI-N123')
        self.assertTrue(self.wait_for(lambda: self.app.github.credential_status()[0]['ready']))

    def test_only_one_login_per_person_and_code_is_not_logged(self):
        self.setUpFake("""import time
print('! First copy your one-time code: SECR-ET99', flush=True)
print('Open this URL to continue in your web browser: https://github.com/login/device', flush=True)
time.sleep(10)
""")
        logs = []
        with patch.object(Handler, 'log_message', lambda handler, fmt, *args: logs.append(fmt % args)):
            status, body, _ = self.request('POST', '/api/github/connect')
            self.assertEqual(status, 200)
            self.assertEqual(body['code'], 'SECR-ET99')
            self.assertEqual(self.request('POST', '/api/github/connect')[0], 409)
        self.assertFalse(any('SECR-ET99' in line for line in logs))
        persisted = [p.read_bytes() for p in self.app.store.data.rglob('*') if p.is_file()]
        self.assertFalse(any(b'SECR-ET99' in content for content in persisted))
        self.request('DELETE', '/api/github/connect')


if __name__ == '__main__': unittest.main()
