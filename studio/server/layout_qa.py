"""Deterministic authenticated preview screenshots; no model or assist worker."""
import json
from pathlib import Path
import os
import secrets
import subprocess
import threading
from .auth import COOKIE

def run(app, value, user):
    from .http import Server
    out = app.store.data / 'layout-qa' / value / str(app.store.piece(value)['head_rev'])
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    app.preview.build(value)
    token = secrets.token_urlsafe(32); csrf = secrets.token_urlsafe(32)
    digest = app.auth.digest(token)
    with app.store.mutex:
        now = app.store.clock()
        app.store.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)', (digest, user, now, now, 'layout-qa', csrf)); app.store.db.commit()
    server = Server(('127.0.0.1', 0), app)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # Closing the temporary HTTP server must not stop the application's worker.
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_', 'GITHUB_', 'STUDIO_', 'DOGFOOD_'))}
    env['LAYOUT_QA_COOKIE'] = COOKIE + '=' + token
    try:
        result = subprocess.run(['node', str(app.repo / 'studio/web/layout-qa.mjs'),
                                 'http://127.0.0.1:' + str(server.server_port), value, str(out)],
                                env=env, capture_output=True, text=True, timeout=180)
        if result.returncode == 2: return {'status': 'unavailable', 'plain_es': 'Instala el navegador de revisión visual en el servidor.', 'plain_en': 'Install the visual review browser on the server.'}
        if result.returncode not in (0, 1): raise ValueError('La revisión visual no pudo terminar.')
        report = json.loads(result.stdout)
        return {'status': 'done', 'ok': result.returncode == 0, 'frames': report['frames'], 'checks': report['checks']}
    finally:
        server.shutdown()
        # Bypass Server.server_close, which owns the primary worker shutdown.
        from http.server import ThreadingHTTPServer
        ThreadingHTTPServer.server_close(server)
        app.auth.logout(token)
