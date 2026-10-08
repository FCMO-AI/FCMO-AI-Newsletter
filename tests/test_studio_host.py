"""Private host preparation; never install a unit or change Tailscale in tests."""
import importlib.util
from pathlib import Path
import shlex
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

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


if __name__ == '__main__': unittest.main()
