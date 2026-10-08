"""Preflight and verify the private Studio before the operator shares its URL."""
import argparse
from http.client import HTTPConnection
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from studio.server.bundle import ready as bundle_ready

ORIGIN = 'https://fcmo-hub.tail8cbe0b.ts.net:8447'
PORT = 8490
spec = importlib.util.spec_from_file_location('studio_user_installer', ROOT / 'studio/host-ops/service_install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def private(path, mode):
    stat = path.stat()
    if stat.st_uid != os.getuid() or stat.st_mode & 0o777 != mode:
        raise ValueError('Los datos privados de Studio deben ser tuyos y tener modo ' + format(mode, '04o') + '.')


def preflight(environment):
    private(environment, 0o600)
    values = installer.read_environment(environment)
    if values.get('STUDIO_BIND') != '127.0.0.1' or values.get('STUDIO_PORT') != str(PORT):
        raise ValueError('Esta activación requiere exclusivamente 127.0.0.1:8490.')
    if values.get('STUDIO_ORIGIN') != ORIGIN:
        raise ValueError('Configura el origen único de Studio: ' + ORIGIN + '.')
    repo = Path(values.get('STUDIO_REPO', '')).resolve()
    if repo != ROOT or not bundle_ready(repo):
        raise ValueError('Reconstruye la interfaz de Studio en el checkout que se va a instalar.')
    if len(values.get('STUDIO_SESSION_KEY', '')) < 32:
        raise ValueError('Configura una clave privada de sesión de al menos 32 caracteres.')
    data_value = values.get('STUDIO_DATA')
    if not data_value or not Path(data_value).is_absolute():
        raise ValueError('Configura una ruta privada absoluta para los borradores de Studio.')
    data = Path(data_value).resolve()
    if data == repo or data.is_relative_to(repo) or repo.is_relative_to(data):
        raise ValueError('Guarda los borradores privados fuera del checkout público.')
    private(data, 0o700)
    # Read-only: checking activation must not create an empty database or users.
    database = data / 'studio.sqlite'
    if not database.is_file():
        raise ValueError('Crea las cuentas locales de Javier y Matías antes de instalar Studio.')
    private(database, 0o600)
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as db:
        users = {row[0] for row in db.execute('SELECT key FROM users')}
    for user, name in (('javier', 'Javier'), ('matias', 'Matías')):
        if user not in users:
            raise ValueError('Falta crear la cuenta local de ' + name + ' antes de compartir Studio.')
    return values


def probe(port, repo):
    connection = HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        for path, status, expected in (
            ('/healthz', 200, None), ('/', 200, Path(repo) / 'studio/web/dist/index.html'),
            ('/app.js', 200, Path(repo) / 'studio/web/dist/app.js'),
            ('/app.css', 200, Path(repo) / 'studio/web/dist/app.css'), ('/api/me', 401, None),
            ('/api/pieces', 401, None),
        ):
            connection.request('GET', path)
            response = connection.getresponse()
            body = response.read()
            if response.status != status or expected and body != expected.read_bytes():
                raise ValueError('Studio aún no sirve su interfaz actual o no protege la API privada.')
            if path == '/healthz' and json.loads(body).get('ok') is not True:
                raise ValueError('Studio aún no responde correctamente en loopback.')
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Instalar y arrancar la unidad de usuario; no cambia Tailscale')
    args = parser.parse_args()
    try:
        preflight(Path.home() / '.config/fcmo-studio/studio.env')
        if args.install:
            subprocess.run([sys.executable, str(ROOT / 'studio/host-ops/service_install.py')], check=True, capture_output=True)
            deadline = time.monotonic() + 45
            while True:
                try:
                    probe(PORT, ROOT)
                    break
                except (OSError, ValueError):
                    if time.monotonic() >= deadline:
                        raise ValueError('La unidad no abrió Studio correctamente en 45 segundos. Revisa el servicio antes de añadir Tailscale.')
                    time.sleep(.5)
            print('Studio responde en 127.0.0.1:8490; interfaz actual y API privada comprobadas.')
        else:
            print('La configuración privada está lista para instalar Studio en el URL único.')
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error, subprocess.SubprocessError):
        # No environment values, passwords, DB content or subprocess output.
        print('No se activó el URL. Comprueba el entorno 0600, ambas cuentas locales, el bundle y el gestor systemd de usuario. Consulta OPERATOR-LINE.md.', file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
