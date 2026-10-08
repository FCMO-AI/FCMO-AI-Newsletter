"""Real offline journey through the launcher, HTTP, two identities and bare git."""
import argparse
import copy
from http.client import HTTPConnection
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit
from studio.server.auth import Auth
from studio.server.storage import Store, git

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = 'dogfood-local-fixture-password'

class Journey:
    def __init__(self, root, browser=False):
        self.browser = browser
        self.root = root; self.scores = []; self.sessions = {}; self.process = None
    def score(self, name, ok=True):
        self.scores.append({'name': name, 'ok': bool(ok)})
        print(('PASS ' if ok else 'FAIL ') + name, flush=True)
        if not ok: raise AssertionError(name)
    def request(self, method, path, body=None, user=None):
        headers = {'Origin': self.origin}
        if user: headers['Cookie'], headers['X-CSRF-Token'] = self.sessions[user]
        if body is not None: body = json.dumps(body); headers['Content-Type'] = 'application/json'
        conn = HTTPConnection('127.0.0.1', self.port, timeout=180)
        try:
            conn.request(method, path, body, headers)
            res = conn.getresponse(); raw = res.read(); hs = dict(res.getheaders())
            return res.status, json.loads(raw) if hs.get('Content-Type', '').startswith('application/json') else raw, hs
        finally: conn.close()
    def call(self, method, path, body=None, user='javier', status=200):
        actual, data, _ = self.request(method, path, body, user)
        assert actual == status, (path, actual, data)
        return data
    def wait(self, slug, states, timeout=1200):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            pub = self.call('GET', '/api/pieces/' + slug + '/publication')
            if pub['state'] in states: return pub
            assert pub['state'] != 'failed', pub
            assert self.process.poll() is None, 'Launcher stopped'
            time.sleep(.3)
        raise AssertionError('Publication timed out: ' + str(pub))
    def create(self, title, author):
        piece = self.call('POST', '/api/pieces', {'kind': 'essay', 'title': title, 'source_locale': 'en'}, author)
        slug = piece['slug']; base = '/api/pieces/' + slug
        titles = {'en': title, 'es-419': 'Una prueba de publicación', 'zh-Hans': '出版测试'}
        text = {'en': 'Human publication with 42 ideas.', 'es-419': 'Una publicación humana con 42 ideas.', 'zh-Hans': '一篇人类文章包含42个想法。'}
        for loc in titles:
            current = self.call('GET', base + '/doc/' + loc, user=author)
            doc = {'schema': 'fcmo-essay-doc-v1', 'locale': loc, 'title': titles[loc],
                   'dek': {'en': 'A checked edition.', 'es-419': 'Una edición comprobada.', 'zh-Hans': '经过验证的版本。'}[loc],
                   'blocks': [{'id': 'b-01234567', 'type': 'p', 'content': [{'t': 'text', 'v': text[loc]}], 'attrs': {}}], 'footnotes': {}}
            self.call('PUT', base + '/doc/' + loc, {'base_rev': current['rev'], 'doc': doc, 'cursor': {'anchor': 2}}, author)
            self.call('POST', base + '/locale/' + loc + '/state', {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, author)
            preview = self.call('GET', '/preview/' + slug + '/' + loc + '/', user=author)
            assert text[loc].encode() in preview
        # Explicit second edit, followed by reload, and a named checkpoint.
        doc = self.call('GET', base + '/doc/en', user=author)
        doc['doc']['dek'] = 'Edited and checked.'
        self.call('PUT', base + '/doc/en', {'base_rev': doc['rev'], 'doc': doc['doc'], 'cursor': {'anchor': 7}}, author)
        self.call('POST', base + '/locale/en/state', {'state': 'ready', 'reviewed': True}, author)
        assert self.call('GET', base + '/doc/en', user=author)['doc']['dek'] == 'Edited and checked.'
        for loc in titles:
            self.call('POST', base + '/locale/' + loc + '/state', {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, author)
        checks = self.call('GET', base + '/checks', user=author)
        assert all(c['ok'] for c in checks), checks
        self.call('POST', base + '/versions', {'name': 'Reviewed draft'}, author)
        self.call('POST', base + '/review/request', {}, author)
        return slug
    def setup(self):
        source = self.root / 'source'
        subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(source)], check=True)
        git(source, 'checkout', '-B', 'main')
        for rel in git(ROOT, 'ls-files').splitlines():
            file = ROOT / rel
            if file.is_file():
                dest = source / rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(file, dest)
        git(source, 'add', '.')
        git(source, '-c', 'user.name=Codex', '-c', 'user.email=codex@openai.com', 'commit', '--allow-empty', '-qm', 'Dogfood source')
        self.bare = self.root / 'origin.git'
        subprocess.run(['git', 'clone', '--quiet', '--bare', str(source), str(self.bare)], check=True)
        git(self.bare, 'tag', '-f', 'lkg', 'main')
        self.initial = git(self.bare, 'rev-parse', 'main')
        for name in ('merged', 'lkg-build'):
            subprocess.run(['git', 'clone', '--quiet', str(self.bare), str(self.root / name)], check=True)
        with (self.root / 'lkg.log').open('w') as f:
            subprocess.run(['python3', 'ops/publish.py', '--check', '--fixture-build'], cwd=self.root / 'lkg-build', stdout=f, stderr=f, check=True)
        (self.root / 'served').write_text(str(self.root / 'lkg-build/publish'))
        outer = self
        class Pages(SimpleHTTPRequestHandler):
            def log_message(self, *args): pass
            def translate_path(self, path):
                relative = urlsplit(path).path.removeprefix('/FCMO-AI-Newsletter/').lstrip('/')
                return str(Path((outer.root / 'served').read_text()) / relative)
        self.pages = ThreadingHTTPServer(('127.0.0.1', 0), Pages)
        threading.Thread(target=self.pages.serve_forever, daemon=True).start()
        self.data = self.root / 'data'; store = Store(self.data)
        try:
            git(self.data / 'clone', 'remote', 'set-url', 'origin', str(self.bare))
            auth = Auth(store, 'dogfood-session-key-' + 'x' * 40)
            for user in ('javier', 'matias'): auth.add_user(user, PASSWORD)
        finally: store.close()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); self.port = sock.getsockname()[1]
        self.origin = 'http://127.0.0.1:' + str(self.port)
        binary = self.root / 'bin'; binary.mkdir()
        for user in ('javier', 'matias'):
            config = self.root / user
            config.mkdir(mode=0o700)
        shutil.copy2(ROOT / 'studio/dogfood/fake_gh.py', binary / 'gh')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_', 'GITHUB_', 'STUDIO_', 'DOGFOOD_'))}
        env.update(STUDIO_DATA=str(self.data), STUDIO_ORIGIN=self.origin, STUDIO_SESSION_KEY='dogfood-session-key-' + 'x' * 40,
                   STUDIO_PORT=str(self.port), STUDIO_REPO=str(source), STUDIO_LIVE_ENABLED='1', STUDIO_DRY_RUN='0',
                   STUDIO_GH_CONFIG_JAVIER=str(self.root / 'javier'), STUDIO_GH_CONFIG_MATIAS=str(self.root / 'matias'),
                   DOGFOOD_ACTIVE='local-bare-only', DOGFOOD_ROOT=str(self.root), DOGFOOD_BARE=str(self.bare),
                   DOGFOOD_LIVE='http://127.0.0.1:' + str(self.pages.server_port) + '/FCMO-AI-Newsletter/',
                   PYTHONPATH=str(ROOT / 'studio/dogfood') + os.pathsep + str(source), PATH=str(binary) + os.pathsep + env['PATH'])
        self.env = env
        self.log = (self.root / 'server.log').open('w')
        self.process = subprocess.Popen(['sh', str(source / 'studio/host-ops/start.sh')], env=env, stdout=self.log, stderr=self.log, start_new_session=True)
        for _ in range(100):
            try:
                if self.request('GET', '/healthz')[0] == 200: break
            except OSError: pass
            assert self.process.poll() is None, (self.root / 'server.log').read_text()
            time.sleep(.1)
        else: raise AssertionError('Server did not start')
        self.score('launcher on alternative loopback port; health and login chrome', self.request('GET', '/')[0] == 200)
        self.score('private API refuses unauthenticated user', self.request('GET', '/api/pieces')[0] == 401)
        for user in ('javier', 'matias'):
            status, login, headers = self.request('POST', '/api/login', {'user': user, 'password': PASSWORD})
            assert status == 200, login
            self.sessions[user] = headers['Set-Cookie'].split(';')[0], login['csrf']
        self.score('two distinct authenticated sessions', self.sessions['javier'] != self.sessions['matias'])
        readiness = self.call('GET', '/api/publication-readiness')
        self.score('missing gh accounts: Studio starts and names both logins',
                   [c['plain_es'] for c in readiness['credentials']] == ['Javier debe iniciar sesión en GitHub.', 'Matías debe iniciar sesión en GitHub.'])
        piece = self.call('POST', '/api/pieces', {'kind': 'essay', 'title': 'Private before GitHub login', 'source_locale': 'en'})
        self.score('private editor remains usable without GitHub credentials',
                   self.call('GET', '/api/pieces/' + piece['slug'])['slug'] == piece['slug'])
        for user in ('javier', 'matias'):
            (self.root / user / 'hosts.yml').write_text('github.com: {}\n')
    def run(self):
        self.setup()
        published = []
        for author, reviewer in (('javier', 'matias'), ('matias', 'javier')):
            slug = self.create('Dogfood ' + author, author)
            published.append(slug)
            base = '/api/pieces/' + slug
            self.call('POST', base + '/review/approve', {}, author, status=409)
            self.score(author + ': self-approval refused before public transport', not any(slug in x for x in git(self.bare, 'for-each-ref', '--format=%(refname)').splitlines()))
            self.call('POST', base + '/review/approve', {}, reviewer)
            pub = self.wait(slug, {'published'})
            self.score(author + ': create/edit/preview/review/publish over HTTP', len(pub['urls']) == 3)
            self.score(author + ': real public build contains edited piece', b'Edited and checked.' in (self.root / 'merged/publish/cartas' / slug / 'index.html').read_bytes())
            calls = json.loads((self.root / 'gh.json').read_text())['calls']
            assert any(c['method'] == 'POST' and c['endpoint'].endswith('/pulls') and c['login'] == 'fake-' + author for c in calls)
            assert any(c['method'] == 'POST' and c['endpoint'].endswith('/reviews') and c['login'] == 'fake-' + reviewer for c in calls)
            self.score(author + ': author opens PR, other identity approves')
        if self.browser: self.browser_checks(published)
        before = git(self.bare, 'rev-parse', 'main')
        (self.root / 'unprotected').touch()
        slug = self.create('Missing protections', 'javier')
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'matias')
        pub = self.wait(slug, {'failed'})
        self.score('missing protections refuses merge', 'protegida' in pub['error_plain'] and git(self.bare, 'rev-parse', 'main') == before)
        (self.root / 'unprotected').unlink()
        slug = self.create('Changed main', 'matias')
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'javier')
        self.wait(slug, {'candidate'})
        merged = self.root / 'merged'
        git(merged, '-c', 'user.name=Codex', '-c', 'user.email=codex@openai.com', 'commit', '--allow-empty', '-qm', 'Concurrent main change')
        git(merged, 'push', 'origin', 'HEAD:main')
        concurrent = git(self.bare, 'rev-parse', 'main')
        pub = self.wait(slug, {'failed'})
        self.score('changed main refuses transport/merge', 'base' in pub['error_plain'] and git(self.bare, 'rev-parse', 'main') == concurrent)
        conn = HTTPConnection('127.0.0.1', self.pages.server_port)
        conn.request('GET', '/FCMO-AI-Newsletter/cartas/' + published[0] + '/')
        response = conn.getresponse(); assert response.status == 200; response.read(); conn.close()
        self.call('POST', '/api/site/rollback', {'confirmation': 'Volver a la última versión comprobada'}, 'matias')
        conn = HTTPConnection('127.0.0.1', self.pages.server_port)
        conn.request('GET', '/FCMO-AI-Newsletter/cartas/' + published[0] + '/')
        response = conn.getresponse(); response.read(); conn.close()
        self.score('rollback serves LKG and preserves main', response.status == 404 and git(self.bare, 'rev-parse', 'main') == concurrent and json.loads((self.root / 'gh.json').read_text())['rollback'])
        refs = git(self.bare, 'for-each-ref', '--format=%(refname)')
        self.score('no draft refs or unapproved piece in public main', 'refs/heads/draft/' not in refs and 'missing-protections' not in git(self.bare, 'ls-tree', '-r', '--name-only', 'main'))
    def browser_checks(self, published):
        env = dict(self.env, STUDIO_USER='javier', STUDIO_PASS=PASSWORD)
        seeded = subprocess.check_output(['python3', '-m', 'tests.harness.seed_studio'], cwd=self.root / 'source', env=env, text=True).strip()
        env.update(STUDIO_SLUG=seeded, STUDIO_ESSAY_SLUG=published[0], STUDIO_OTHER_SLUG=published[1], STUDIO_REVIEW_SLUG=published[0])
        for name, args in (
            ('studio_editor', []), ('studio_review', [seeded]), ('studio_translate', [seeded]), ('studio_publish', [seeded]),
            ('studio_a11y', ['--viewport', '390x844', '--viewport', '1440x900', '--json', str(self.root / 'a11y.json')]),
            ('studio_frames', ['http://127.0.0.1:' + str(self.pages.server_port) + '/FCMO-AI-Newsletter/', str(self.root / 'frames')])):
            if name == 'studio_publish':
                seeded = subprocess.check_output(['python3', '-m', 'tests.harness.seed_studio'], cwd=self.root / 'source', env=env, text=True).strip()
                env['STUDIO_SLUG'] = seeded; args = [seeded]
            with (self.root / (name + '.log')).open('w') as f:
                result = subprocess.run(['node', str(ROOT / ('tests/harness/browser/' + name + '.mjs')), self.origin + '/', *args], env=env, stdout=f, stderr=f, timeout=300)
            self.score('browser ' + name, result.returncode == 0)
        with (self.root / 'studio_actions.log').open('w') as f:
            result = subprocess.run(['node', str(ROOT / 'tests/harness/browser/studio_actions.mjs'), self.origin + '/'], env=env, stdout=f, stderr=f, timeout=300)
        self.score('browser issue/correction/withdrawal', result.returncode == 0)
        qa = self.call('POST', '/api/pieces/' + seeded + '/assist', {'kind': 'layout_qa', 'loc': 'en'})
        self.score('deterministic visual assist without worker', qa['status'] == 'done' and len(qa['frames']) == 12 and qa['ok'])
    def close(self):
        if self.process:
            # Own the entire launcher/checker process group, including a
            # checker that is still running if this journey fails early.
            try: os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL); self.process.wait()
            self.log.close()
        if hasattr(self, 'pages'): self.pages.shutdown(); self.pages.server_close()
        expected = 25 if self.browser else 17
        passed = sum(s['ok'] for s in self.scores)
        summary = {'passed': passed, 'total': expected, 'executed': len(self.scores), 'completed': passed == expected and len(self.scores) == expected, 'checks': self.scores}
        (self.root / 'summary.json').write_text(json.dumps(summary, indent=2))
        print(f"DOGFOOD {summary['passed']}/{summary['total']}; evidence: {self.root}", flush=True)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--keep', type=Path); parser.add_argument('--browser', action='store_true'); args = parser.parse_args()
    root = args.keep.resolve() if args.keep else Path(tempfile.mkdtemp(prefix='studio-dogfood-'))
    root.mkdir(parents=True, exist_ok=True)
    journey = Journey(root, args.browser)
    try: journey.run()
    except BaseException:
        journey.scores.append({'name': 'complete journey', 'ok': False})
        raise
    finally: journey.close()
    if not args.keep: shutil.rmtree(root)

if __name__ == '__main__': main()
