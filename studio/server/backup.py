"""Private bundle + SQLite backup, integrity manifest, retention and restore drill."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import threading
from urllib.request import urlopen, Request
from .storage import Store, atomic, encoded, git

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def backup(data, backups):
    data = Path(data).resolve(); backups = Path(backups).resolve()
    if backups == data or backups.is_relative_to(data): raise ValueError('El respaldo debe estar fuera de los datos activos.')
    backups.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(backups, 0o700)
    target = backups / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(3))
    target.mkdir(mode=0o700)
    try:
        source = sqlite3.connect(data / 'studio.sqlite'); dest = sqlite3.connect(target / 'studio.sqlite')
        try: source.backup(dest)
        finally: source.close(); dest.close()
        os.chmod(target / 'studio.sqlite', 0o600)
        git(data / 'clone', 'bundle', 'create', str(target / 'drafts.bundle'), '--all')
        # Figures are immutable uploaded blobs; autosave JSON is recovered from DB.
        figures = target / 'figures'; figures.mkdir(mode=0o700)
        for work in (data / 'worktrees').iterdir():
            images = work / 'editorial/pieces' / work.name / 'figures'
            if images.is_dir(): shutil.copytree(images, figures / work.name)
        files = {str(p.relative_to(target)): digest(p) for p in target.rglob('*') if p.is_file()}
        atomic(target / 'manifest.json', encoded({'schema': 'fcmo-studio-backup-v1', 'files': files}).encode())
        for p in target.rglob('*'): os.chmod(p, 0o700 if p.is_dir() else 0o600)
        retain(backups)
        return target
    except Exception:
        shutil.rmtree(target); raise

def retain(backups):
    snapshots = sorted((p for p in Path(backups).iterdir() if p.is_dir() and (p / 'manifest.json').is_file()), reverse=True)
    keep = set(snapshots[:48]); daily = {}
    for path in snapshots: daily.setdefault(path.name[:8], path)
    keep.update(list(daily.values())[:30])
    for path in snapshots:
        if path not in keep: shutil.rmtree(path)

def restore(snapshot, destination):
    snapshot = Path(snapshot).resolve(); destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()): raise ValueError('Restaura en una carpeta vacía.')
    manifest = json.loads((snapshot / 'manifest.json').read_text())
    if manifest.get('schema') != 'fcmo-studio-backup-v1': raise ValueError('El respaldo no es válido.')
    for rel, expected in manifest['files'].items():
        path = (snapshot / rel).resolve()
        if not path.is_relative_to(snapshot) or path.is_symlink() or not path.is_file() or digest(path) != expected: raise ValueError('El respaldo está incompleto o cambió.')
    destination.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(destination, 0o700)
    clone = destination / 'clone'; clone.mkdir(mode=0o700); git(clone, 'init', '-q', '-b', 'main')
    git(clone, 'fetch', '--update-head-ok', str(snapshot / 'drafts.bundle'), 'refs/heads/*:refs/heads/*')
    shutil.copyfile(snapshot / 'studio.sqlite', destination / 'studio.sqlite'); os.chmod(destination / 'studio.sqlite', 0o600)
    store = Store(destination)
    try:
        for piece in store.list():
            source = snapshot / 'figures' / piece['slug']
            if source.is_dir(): shutil.copytree(source, store.directory(piece['slug']) / 'figures', dirs_exist_ok=True)
        # Candidate paths are local placement, never publication identity.
        for row in store.db.execute("SELECT * FROM publications WHERE state NOT IN ('published','failed')").fetchall():
            payload = json.loads(row['payload_json'])
            if payload.get('candidate'):
                target = destination / 'candidates' / row['id']; target.parent.mkdir(exist_ok=True, mode=0o700)
                git(clone, 'worktree', 'add', '-q', str(target), payload['branch'])
                payload['candidate'] = str(target)
                store.db.execute('UPDATE publications SET payload_json=? WHERE id=?', (encoded(payload), row['id']))
        store.db.commit()
        return [{'slug': p['slug'], 'checkpoints': len(store.versions(p['slug']))} for p in store.list()]
    finally: store.close()

def drill(data, backups, destination):
    snapshot = backup(data, backups); expected_store = Store(data)
    try: expected = [{'slug': p['slug'], 'checkpoints': len(expected_store.versions(p['slug']))} for p in expected_store.list()]
    finally: expected_store.close()
    observed = restore(snapshot, destination)
    if observed != expected: raise ValueError('El simulacro no recuperó todas las publicaciones y versiones.')
    from .http import Application, Server
    root = Path(__file__).resolve().parents[2]; store = Store(destination)
    app = Application(store, 'http://127.0.0.1', 'drill-session-key-' + secrets.token_hex(32), root)
    server = Server(('127.0.0.1', 0), app); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    token = secrets.token_urlsafe(32); csrf = secrets.token_urlsafe(32)
    identity = store.db.execute('SELECT key FROM users ORDER BY key LIMIT 1').fetchone()
    try:
        base = 'http://127.0.0.1:' + str(server.server_port)
        with urlopen(base + '/healthz', timeout=5) as response:
            if json.load(response) != {'ok': True}: raise ValueError('El servicio restaurado no respondió.')
        if observed and not identity: raise ValueError('Provisiona las cuentas antes del simulacro de recuperación.')
        if identity:
            store.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)', (app.auth.digest(token), identity[0], store.clock(), store.clock(), 'restore-drill', csrf)); store.db.commit()
            def read(path):
                with urlopen(Request(base + path, headers={'Cookie': '__Host-studio=' + token}), timeout=5) as response: return json.load(response)
            listed = read('/api/pieces')
            actual = [{'slug': p['slug'], 'checkpoints': len(read('/api/pieces/' + p['slug'] + '/versions'))} for p in listed]
            if actual != expected: raise ValueError('El servicio no listó las publicaciones y versiones restauradas.')
    finally:
        store.db.execute('DELETE FROM sessions WHERE id_hash=?', (app.auth.digest(token),)); store.db.commit()
        server.shutdown(); server.server_close(); thread.join(); store.close()
    return observed

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--drill'); parser.add_argument('--restore'); parser.add_argument('--destination'); args = parser.parse_args()
    data = os.environ.get('STUDIO_DATA'); backups = os.environ.get('STUDIO_BACKUPS')
    if args.restore:
        if not args.destination: parser.error('Falta --destination')
        result = restore(args.restore, args.destination)
    else:
        if not data or not backups: parser.error('Configura STUDIO_DATA y STUDIO_BACKUPS')
        result = drill(data, backups, args.drill) if args.drill else {'snapshot': backup(data, backups).name}
    print(json.dumps(result, ensure_ascii=False))
if __name__ == '__main__': main()
