"""Run a reviewed publication's preflight without any GitHub write."""
import argparse
import fcntl
import os
from pathlib import Path
import sys
from .http import Application
from .storage import Store
from .publishing import Refused, UnknownEffect, protection_mode

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slug', required=True)
    parser.add_argument('--dry-run', action='store_true', required=True)
    args = parser.parse_args(argv)
    store = None
    try:
        data_root = Path(os.environ['STUDIO_DATA'])
        lock = open(data_root / '.server-lock', 'a')
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        store = Store(data_root)
        repo = Path(os.environ.get('STUDIO_REPO', Path(__file__).resolve().parents[2]))
        tokens = {u: os.environ.get('GH_TOKEN_' + u.upper(), '') for u in ('javier', 'matias')}
        app = Application(store, os.environ['STUDIO_ORIGIN'], os.environ['STUDIO_SESSION_KEY'], repo, tokens=tokens if any(tokens.values()) else None)
        pub = app.publisher.get(args.slug)
        if pub['state'] != 'approved': raise Refused('El ensayo o la edición debe estar seleccionado por su autor antes del ensayo de publicación.')
        data = pub['payload']
        if store.piece(args.slug)['head_rev'] != data['approved_rev']: raise Refused('El texto cambió después de pulsar Publicar.')
        app.github.preflight(data['author'])
        if (data.get('protection_mode') or protection_mode()) == 'github' and not app.github.protected(data['author']): raise Refused('Publicación protegida aún no activa.')
        candidate = app.publisher.workspace.prepare(pub)
        pub['payload'].update(candidate)
        app.publisher.workspace.verify_confined(pub)
        print('Ensayo completo: credencial del autor, base, LKG y comprobaciones locales válidas. Ningún envío, PR, merge o despliegue.')
        print('Candidato: ' + candidate['head_sha'])
        return 0
    except (KeyError, OSError, RuntimeError, ValueError, Refused, UnknownEffect) as exc:
        print(str(exc) if isinstance(exc, (Refused, UnknownEffect)) else 'No se pudo completar el ensayo de publicación; revisa la configuración local.', file=sys.stderr)
        return 2
    finally:
        if store: store.close()

if __name__ == '__main__': raise SystemExit(main())
