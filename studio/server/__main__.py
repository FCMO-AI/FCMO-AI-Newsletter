"""Environment-configured entrypoint; credentials never pass on command lines."""
import argparse
import getpass
import fcntl
import os
from pathlib import Path
import sys
import threading
from .auth import Auth
from .http import Application, Server
from .storage import Store

def main():
    parser = argparse.ArgumentParser(description='FCMO Studio')
    parser.add_argument('--add-user', choices=('javier', 'matias'))
    args = parser.parse_args()
    if os.environ.get('STUDIO_BIND', '127.0.0.1') != '127.0.0.1':
        print('Studio solo puede escuchar en 127.0.0.1.', file=sys.stderr); return 2
    data = os.environ.get('STUDIO_DATA'); origin = os.environ.get('STUDIO_ORIGIN'); key = os.environ.get('STUDIO_SESSION_KEY')
    if not data or not origin or not key or len(key) < 32:
        print('Configura los datos, el origen y la clave de sesión de Studio.', file=sys.stderr); return 2
    store = Store(Path(data))
    try:
        if args.add_user:
            password = getpass.getpass('Contraseña: ')
            if password != getpass.getpass('Repetir contraseña: '): raise ValueError('Las contraseñas no coinciden.')
            Auth(store, key).add_user(args.add_user, password); return 0
        repo = Path(os.environ.get('STUDIO_REPO', Path(__file__).resolve().parents[2]))
        app = Application(store, origin, key, repo, live=os.environ.get('STUDIO_LIVE_ENABLED') == '1',
                          tokens={u: os.environ.get('GH_TOKEN_' + u.upper(), '') for u in ('javier', 'matias')})
        lockfile = open(store.data / '.server-lock', 'a')
        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        server = Server(('127.0.0.1', int(os.environ.get('STUDIO_PORT', '8447'))), app)
        threading.Thread(target=app.worker, daemon=True).start()
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()
        return 0
    except (ValueError, OSError):
        print('No se pudo iniciar Studio. Revisa la configuración local.', file=sys.stderr); return 2
    finally: store.close()

if __name__ == '__main__': raise SystemExit(main())
