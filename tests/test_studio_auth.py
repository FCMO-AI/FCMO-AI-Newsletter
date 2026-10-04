"""Real HTTP auth boundaries; no identity-header trust or credential disclosure."""
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from studio.server import Store, Application, Server
from studio.server.auth import Auth, COOKIE
from tests.test_studio_storage import ROOT, DOC

class AuthHTTP(unittest.TestCase):
    def setUp(self):
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit'); self.store = Store(Path(self.tmp.name))
        self.app = Application(self.store, 'https://studio.invalid:8447', 'fixture-session-key-' + 'a'*32, ROOT)
        self.app.auth.add_user('javier', 'fixture-passphrase-1234')
        self.app.auth.add_user('matias', 'fixture-passphrase-5678')
        self.server = Server(('127.0.0.1', 0), self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.cookie = None; self.csrf = None
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.store.close(); self.tmp.cleanup()
    def request(self, method, path, body=None, headers=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        defaults = {'Origin': self.app.origin, 'Content-Type': 'application/json'}
        if self.cookie: defaults['Cookie'] = self.cookie
        if self.csrf: defaults['X-CSRF-Token'] = self.csrf
        defaults.update(headers or {})
        conn.request(method, path, json.dumps(body).encode() if body is not None else None, defaults)
        response = conn.getresponse(); status = response.status; received = dict(response.getheaders()); raw = response.read(); conn.close()
        return status, json.loads(raw), received
    def login(self):
        status, data, headers = self.request('POST', '/api/login', {'user': 'javier', 'password': 'fixture-passphrase-1234'})
        self.assertEqual(status, 200); self.cookie = headers['Set-Cookie'].split(';')[0]; self.csrf = data['csrf']
        return headers
    def test_all_private_routes_require_session(self):
        for method, path in [('GET', '/api/pieces'), ('GET', '/api/me'), ('GET', '/preview/fixture/en/'), ('PUT', '/api/pieces/fixture/doc/en'), ('POST', '/api/site/rollback'), ('GET', '/api/library/briefs'), ('GET', '/api/jobs/abc'), ('GET', '/FCMO-AI-Newsletter/assets/style.css')]:
            with self.subTest(path=path): self.assertEqual(self.request(method, path, headers={'Tailscale-User-Login': 'javier'})[0], 401)
        self.assertEqual(self.request('GET', '/healthz')[1], {'ok': True})
    def test_cookie_csp_and_csrf_origin(self):
        headers = self.login(); cookie = headers['Set-Cookie']
        for value in ('__Host-studio=', 'Secure', 'HttpOnly', 'SameSite=Strict', 'Path=/'): self.assertIn(value, cookie)
        self.assertIn("connect-src 'self'", headers['Content-Security-Policy'])
        data = {'title': 'HTTP piece', 'kind': 'essay', 'source_locale': 'en'}
        self.assertEqual(self.request('POST', '/api/pieces', data, {'Origin': 'https://evil.invalid'})[0], 403)
        self.assertEqual(self.request('POST', '/api/pieces', data, {'X-CSRF-Token': ''})[0], 403)
        self.assertEqual(self.request('POST', '/api/pieces', data)[0], 200)
    def test_five_failures_lock_user_for_fifteen_minutes(self):
        for _ in range(5): self.assertEqual(self.request('POST', '/api/login', {'user': 'javier', 'password': 'wrong-password-long'})[0], 401)
        self.assertEqual(self.request('POST', '/api/login', {'user': 'javier', 'password': 'fixture-passphrase-1234'})[0], 401)
        now = self.store.clock(); self.store.clock = lambda: now + 901
        self.assertEqual(self.request('POST', '/api/login', {'user': 'javier', 'password': 'fixture-passphrase-1234'})[0], 200)
    def test_http_revision_conflict_and_closed_schema(self):
        self.login(); value = self.request('POST', '/api/pieces', {'title': 'HTTP piece', 'kind': 'essay', 'source_locale': 'en'})[1]['slug']
        path = '/api/pieces/' + value + '/doc/en'
        self.assertEqual(self.request('PUT', path, {'base_rev': 0, 'doc': DOC, 'cursor': {'anchor': 42}})[0], 200)
        status, data, _ = self.request('PUT', path, {'base_rev': 0, 'doc': DOC, 'cursor': {}})
        self.assertEqual(status, 409); self.assertEqual(data['rev'], 1); self.assertEqual(data['doc'], DOC)
        bad = dict(DOC, raw_html='<script>x</script>')
        self.assertEqual(self.request('PUT', path, {'base_rev': 1, 'doc': bad})[0], 400)
        self.assertEqual(self.request('GET', path)[1]['rev'], 1)
    def test_assist_off_leaves_no_jobs_and_no_network(self):
        self.login(); value = self.request('POST', '/api/pieces', {'title': 'No agents', 'kind': 'essay', 'source_locale': 'en'})[1]['slug']
        self.assertEqual(self.request('POST', '/api/pieces/' + value + '/assist', {'kind': 'translate', 'loc': 'es-419'})[1], {'status': 'no_worker'})
        self.assertEqual(list((self.store.data / 'jobs/queued').iterdir()), [])
    def test_logout_and_expiry(self):
        self.login(); self.assertEqual(self.request('POST', '/api/logout', {})[0], 200)
        self.assertEqual(self.request('GET', '/api/me')[0], 401)
        self.login(); now = self.store.clock(); self.store.clock = lambda: now + 30*86400 + 1
        self.assertEqual(self.request('GET', '/api/me')[0], 401)
    def test_refuses_non_loopback_before_opening_data(self):
        path = Path(self.tmp.name) / 'must-not-exist'
        env = dict(os.environ, STUDIO_DATA=str(path), STUDIO_BIND='0.0.0.0')
        run = subprocess.run(['python3', '-m', 'studio.server'], cwd=ROOT, env=env, capture_output=True)
        self.assertNotEqual(run.returncode, 0); self.assertFalse(path.exists())
        with self.assertRaises(ValueError): Server(('0.0.0.0', 0), self.app)
