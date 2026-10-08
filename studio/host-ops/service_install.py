"""Install a user unit with a durable receipt and restore its previous state."""
import argparse
import base64
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from studio.server.credentials import CREDENTIAL_ROOT

UNIT = 'fcmo-studio.service'
SOURCE = Path(__file__).with_name(UNIT)


def read_environment(path):
    """Read prepare_host's literal assignments without running shell content."""
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, separator, raw = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key) or key in values:
            raise ValueError('El entorno de Studio contiene una asignación inválida o repetida.')
        parts = shlex.split(raw, comments=True)
        if len(parts) > 1:
            raise ValueError('Las rutas con espacios deben ir entre comillas en el entorno de Studio.')
        values[key] = parts[0] if parts else ''
    return values


def command(*args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix('.tmp')
    with temporary.open('xb') as stream:
        os.chmod(temporary, 0o600)
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_credentials(values):
    for user in ('javier', 'matias'):
        directory = CREDENTIAL_ROOT / user
        if directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
            raise ValueError('Personal gh directories must be owner-only, owned by fcmo-agent.')
        if values.get('STUDIO_GH_CONFIG_' + user.upper()) != str(directory):
            raise ValueError('Use the agreed personal gh directory for ' + user + '.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    if pwd.getpwuid(os.getuid()).pw_name != 'fcmo-agent':
        raise ValueError('Run as fcmo-agent, without sudo.')
    home = Path.home()
    destination = home / '.config/systemd/user' / UNIT
    receipt = home / '.local/state/fcmo-studio/service-install.json'
    # Check the actual user manager before any filesystem mutation.
    command('systemctl', '--user', 'show-environment')
    if args.rollback:
        saved = json.loads(receipt.read_text())
        observed = destination.read_bytes() if destination.exists() else None
        previous = None if saved['previous'] is None else base64.b64decode(saved['previous'])
        if observed not in (base64.b64decode(saved['installed']), previous):
            raise ValueError('Unit changed since install; reconcile before rollback.')
        command('systemctl', '--user', 'disable', '--now', UNIT)
        if saved['previous'] is None: destination.unlink(missing_ok=True)
        else: write(destination, base64.b64decode(saved['previous']))
        command('systemctl', '--user', 'daemon-reload')
        if saved['enabled']: command('systemctl', '--user', 'enable', UNIT)
        if saved['active']: command('systemctl', '--user', 'start', UNIT)
        receipt.rename(receipt.with_suffix('.rolled-back.json'))
        print('Previous user service restored. Drafts and credentials retained.')
        return
    if receipt.exists(): raise ValueError('Existing installation receipt; rollback or reconcile first.')
    environment = home / '.config/fcmo-studio/studio.env'
    if environment.stat().st_uid != os.getuid() or environment.stat().st_mode & 0o077:
        raise ValueError('studio.env must be owned by fcmo-agent with mode 0600.')
    values = read_environment(environment)
    if values.get('STUDIO_BIND') != '127.0.0.1': raise ValueError('Only loopback is allowed.')
    port = int(values.get('STUDIO_PORT', '8490'))
    if not 8490 <= port <= 8499: raise ValueError('Use a port in 8490-8499.')
    occupied = command('ss', '-H', '-ltn', 'sport = :' + str(port)).stdout
    if occupied.strip(): raise ValueError('Studio port is occupied; choose another before installing.')
    command('systemd-analyze', '--user', 'verify', str(SOURCE))
    validate_credentials(values)
    previous = destination.read_bytes() if destination.exists() else None
    installed = SOURCE.read_bytes()
    saved = {'previous': None if previous is None else base64.b64encode(previous).decode(),
             'installed': base64.b64encode(installed).decode(),
             'enabled': command('systemctl', '--user', 'is-enabled', UNIT, check=False).stdout.strip() == 'enabled',
             'active': command('systemctl', '--user', 'is-active', UNIT, check=False).stdout.strip() == 'active'}
    write(receipt, json.dumps(saved).encode())
    write(destination, installed)
    command('systemctl', '--user', 'daemon-reload')
    command('systemctl', '--user', 'enable', '--now', UNIT)
    command('systemctl', '--user', 'is-active', UNIT)
    print('Studio user service enabled and active. Rollback: sh studio/host-ops/rollback.sh')


if __name__ == '__main__': main()
