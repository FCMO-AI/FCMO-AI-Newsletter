"""Private host preparation; never install a unit or change Tailscale in tests."""
import importlib.util
from pathlib import Path
import shlex
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import threading
from studio.server.auth import Auth
from studio.server.http import Application, Server
from studio.server.storage import Store

ROOT = Path(__file__).resolve().parents[1]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class QuotedEnvironment(unittest.TestCase):
    def test_install_accepts_shell_quoted_personal_directories(self):
        installer = load('studio/host-ops/service_install.py', 'studio_installer_l40')
        with tempfile.TemporaryDirectory(prefix='studio host ') as tmp:
            home = Path(tmp)
            credential_root = home / 'personal credentials'
            environment = home / '.config/fcmo-studio/studio.env'
            environment.parent.mkdir(parents=True)
            values = {'STUDIO_BIND': '127.0.0.1', 'STUDIO_PORT': '8490'}
            for user in ('javier', 'matias'):
                directory = credential_root / user
                directory.mkdir(parents=True, mode=0o700)
                values['STUDIO_GH_CONFIG_' + user.upper()] = str(directory)
            environment.write_text(''.join(k + '=' + shlex.quote(v) + '\n' for k, v in values.items()))
            environment.chmod(0o600)
            def command(*args, **kwargs):
                return subprocess.CompletedProcess(args, 0, 'active\n' if 'is-active' in args else '', '')
            with patch.object(Path, 'home', return_value=home), \
                    patch.object(installer.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='fcmo-agent')), \
                    patch.object(installer, 'CREDENTIAL_ROOT', credential_root), \
                    patch.object(installer, 'command', side_effect=command), patch('sys.argv', ['install']):
                installer.main()
            self.assertEqual((home / '.config/systemd/user/fcmo-studio.service').read_bytes(), installer.SOURCE.read_bytes())


class SingleURLHost(unittest.TestCase):
    def setUp(self):
        self.host = load('ops/studio/host.py', 'studio_host_l40')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / 'data'
        self.store = Store(self.data)
        self.addCleanup(self.store.close)
        auth = Auth(self.store, 'host-fixture-key-' + 'x' * 40)
        for user in ('javier', 'matias'):
            auth.add_user(user, 'host-fixture-password')
        self.env = self.root / 'studio.env'
        self.values = {'STUDIO_REPO': str(ROOT), 'STUDIO_DATA': str(self.data),
                       'STUDIO_BIND': '127.0.0.1', 'STUDIO_PORT': '8490',
                       'STUDIO_ORIGIN': self.host.ORIGIN, 'STUDIO_SESSION_KEY': 'host-fixture-key-' + 'x' * 40}
        self.write_env()

    def write_env(self):
        self.env.write_text(''.join(k + '=' + shlex.quote(v) + '\n' for k, v in self.values.items()))
        self.env.chmod(0o600)

    def test_preflight_requires_both_local_logins_before_installing(self):
        self.assertEqual(self.host.preflight(self.env)['STUDIO_PORT'], '8490')
        self.store.db.execute("DELETE FROM users WHERE key='matias'")
        self.store.db.commit()
        with self.assertRaisesRegex(ValueError, 'Matías'):
            self.host.preflight(self.env)

    def test_preflight_refuses_wrong_origin_port_private_location_and_bundle(self):
        for key, wrong in (('STUDIO_ORIGIN', 'https://example.invalid'), ('STUDIO_PORT', '8471'),
                           ('STUDIO_BIND', '0.0.0.0'), ('STUDIO_DATA', str(ROOT / 'studio-data'))):
            with self.subTest(key=key):
                original = self.values[key]
                self.values[key] = wrong
                self.write_env()
                with self.assertRaises(ValueError): self.host.preflight(self.env)
                self.values[key] = original
        self.write_env()
        with patch.object(self.host, 'bundle_ready', return_value=False), self.assertRaisesRegex(ValueError, 'interfaz'):
            self.host.preflight(self.env)
        self.env.chmod(0o644)
        with self.assertRaisesRegex(ValueError, '0600'): self.host.preflight(self.env)

    def test_probe_reads_real_loopback_chrome_assets_and_auth_boundary(self):
        app = Application(self.store, self.host.ORIGIN, self.values['STUDIO_SESSION_KEY'], ROOT)
        server = Server(('127.0.0.1', 0), app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.host.probe(server.server_port, ROOT)
            app.web_ready = False
            with self.assertRaisesRegex(ValueError, 'interfaz'): self.host.probe(server.server_port, ROOT)
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__': unittest.main()
