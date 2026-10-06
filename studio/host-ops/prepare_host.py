"""Create a private first-install environment; never overwrite existing secrets."""
import argparse
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from studio.server.credentials import CREDENTIAL_ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True, help='Architect-selected private HTTPS origin, no path')
    args = parser.parse_args()
    origin = urlsplit(args.origin)
    if origin.scheme != 'https' or not origin.hostname or origin.username or origin.password or origin.path or origin.query or origin.fragment:
        raise ValueError('Use a private HTTPS origin without a path or credentials.')
    target = Path.home() / '.config/fcmo-studio/studio.env'
    if target.exists(): raise ValueError('Environment exists; inspect it privately instead of overwriting.')
    for user in ('javier', 'matias'):
        directory = CREDENTIAL_ROOT / user
        if directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
            raise ValueError('Architect must provision owner-only personal gh directories first.')
    port = next((p for p in range(8490, 8500) if not subprocess.check_output(
        ['ss', '-H', '-ltn', 'sport = :' + str(p)], text=True).strip()), None)
    if port is None: raise ValueError('No free Studio port in 8490-8499.')
    private = Path.home() / '.local/share/fcmo-studio'
    for directory in (target.parent, private, private / 'data', private / 'backups'):
        directory.mkdir(parents=True, exist_ok=True, mode=0o700); directory.chmod(0o700)
    values = {
        'STUDIO_REPO': str(Path(__file__).resolve().parents[2]),
        'STUDIO_DATA': str(private / 'data'), 'STUDIO_BACKUPS': str(private / 'backups'),
        'STUDIO_ORIGIN': args.origin, 'STUDIO_SESSION_KEY': secrets.token_urlsafe(48),
        'STUDIO_BIND': '127.0.0.1', 'STUDIO_PORT': str(port),
        'STUDIO_LIVE_ENABLED': '0', 'STUDIO_DRY_RUN': '1', 'STUDIO_ALLOW_NON_EN_SOURCE': '0',
        'STUDIO_GH_CONFIG_JAVIER': str(CREDENTIAL_ROOT / 'javier'),
        'STUDIO_GH_CONFIG_MATIAS': str(CREDENTIAL_ROOT / 'matias'),
        'PLAYWRIGHT_MODULE': str(private / 'browser/node_modules/playwright'),
        'NODE_PATH': str(private / 'browser/node_modules'),
        'AXE_CORE_PATH': str(private / 'browser/node_modules/axe-core/axe.min.js'),
    }
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(''.join(k + '=' + shlex.quote(v) + '\n' for k, v in values.items()))
        stream.flush(); os.fsync(stream.fileno())
    print('Private environment created; loopback port ' + str(port) + '. Publication disabled until acceptance.')


if __name__ == '__main__': main()
