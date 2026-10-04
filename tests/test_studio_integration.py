"""Real loopback API, production renderer and local candidate, only GitHub mocked."""
import copy
from http.client import HTTPConnection
import json
from pathlib import Path
import subprocess
import shutil
import tempfile
import threading
import unittest
from studio.server.http import Application, Server
from studio.server.storage import Store, git
from studio.server.publishing import GitHub, Publisher
from tests.harness.mock_github import MockGitHub
from tests.test_studio_publish import MockWorkspace
from tests.test_studio_storage import ROOT, DOC


class StudioIntegration(unittest.TestCase):
    def setUp(self):
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit')
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'data')
        self.mock = MockGitHub().__enter__()
        gh = GitHub({'javier': 'fixture-javier', 'matias': 'fixture-matias'}, self.mock.url, live_base=self.mock.url + '/live/')
        # The candidate uses the actual production build + fourteen gates, never a green stub.
        remote = self.root / 'remote'
        subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(remote)], check=True)
        git(remote, 'checkout', '-qb', 'main')
        # Exercise current working source during red/green development as well as commits.
        for relative in git(ROOT, 'ls-files').splitlines():
            source = ROOT / relative
            if source.is_file():
                target = remote / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        git(remote, 'add', '.')
        git(remote, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '--allow-empty', '-qm', 'Integration fixture source')
        git(self.store.data / 'clone', 'remote', 'set-url', 'origin', str(remote))
        gate_script = self.root / 'candidate_check.py'
        gate_script.write_text("""from pathlib import Path
import subprocess
for command in (["python3", "tools/paper/build.py", "--stories", "site/data/stories.v2.json", "--status", "site/data/newsroom-status.json", "--out", "publish", "--base", "/FCMO-AI-Newsletter/"], ["python3", "tools/gates/run_all.py", "publish"]):
    run = subprocess.run(command, capture_output=True)
    with open(""" + repr(str(ROOT / '_audit/studio-int/candidate.log')) + """, 'ab') as log: log.write(run.stdout + run.stderr)
    if run.returncode: raise SystemExit(run.returncode)
""")
        workspace = MockWorkspace(self.store, gh, ['python3', str(gate_script)])
        self.app = Application(self.store, 'http://studio.invalid', 'integration-session-' + 'x'*32, ROOT, live=True)
        self.app.publisher = Publisher(self.store, gh, workspace, lambda slug: __import__('studio.server.checks', fromlist=['checks']).checks(self.store, self.app.preview, slug))
        for user in ('javier', 'matias'):
            self.app.auth.add_user(user, 'integration-fixture-password')
        self.server = Server(('127.0.0.1', 0), self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.sessions = {}
        for user in ('javier', 'matias'):
            status, data, headers = self.request('POST', '/api/login', {'user': user, 'password': 'integration-fixture-password'})
            self.assertEqual(status, 200)
            self.sessions[user] = (headers['Set-Cookie'].split(';')[0], data['csrf'])

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.mock.__exit__(); self.store.close(); self.tmp.cleanup()

    def request(self, method, path, body=None, user=None):
        headers = {'Origin': self.app.origin}
        if user:
            headers['Cookie'], headers['X-CSRF-Token'] = self.sessions[user]
        if body is not None:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(body)
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=180)
        try:
            conn.request(method, path, body=body, headers=headers)
            res = conn.getresponse(); raw = res.read(); hs = dict(res.getheaders())
            return res.status, json.loads(raw) if hs.get('Content-Type', '').startswith('application/json') else raw, hs
        finally:
            conn.close()

    def test_real_http_create_edit_preview_review_and_mock_publish(self):
        status, me, _ = self.request('GET', '/api/me', user='javier')
        self.assertEqual(me['other'], 'Matías')
        status, piece, _ = self.request('POST', '/api/pieces', {'kind': 'essay', 'title': 'Integrated essay', 'source_locale': 'en'}, 'javier')
        self.assertEqual(status, 200)
        slug = piece['slug']; base = '/api/pieces/' + slug
        self.assertEqual(piece['source_locale'], 'en')
        self.assertEqual(piece['words'], 0)
        doc = copy.deepcopy(DOC)
        status, saved, _ = self.request('PUT', base + '/doc/en', {'base_rev': 0, 'doc': doc, 'cursor': {'anchor': 2, 'head': 2}}, 'javier')
        self.assertEqual(status, 200)
        status, html, _ = self.request('GET', '/preview/' + slug + '/en/', user='javier')
        self.assertEqual(status, 200, html)
        self.assertIn(doc['blocks'][0]['content'][0]['v'].encode(), html)
        self.assertEqual(self.store.piece(slug)['locale_states']['en']['state'], 'drafting')
        self.assertEqual(self.request('GET', '/preview/' + slug + '/en/')[0], 401)
        # Readiness is a deliberate human action; preview must not manufacture it.
        for loc in ('en', 'es-419', 'zh-Hans'):
            if loc != 'en':
                status, current, _ = self.request('GET', base + '/doc/' + loc, user='javier')
                translated = copy.deepcopy(doc); translated['locale'] = loc
                translated['title'] = 'Una prueba integrada' if loc == 'es-419' else '集成测试'
                translated['dek'] = 'Un texto de prueba' if loc == 'es-419' else '测试文本'
                translated['blocks'][0]['content'][0]['v'] = 'Una publicación humana comprobada con 42 ideas.' if loc == 'es-419' else '经过验证的人类出版内容与42个想法。'
                self.assertEqual(self.request('PUT', base + '/doc/' + loc, {'base_rev': current['rev'], 'doc': translated, 'cursor': {}}, 'javier')[0], 200)
            self.assertEqual(self.request('POST', base + '/locale/' + loc + '/state', {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, 'javier')[0], 200)
        status, checks, _ = self.request('GET', base + '/checks', user='javier')
        self.assertTrue(all(c['ok'] for c in checks), checks)
        self.assertEqual(self.request('POST', base + '/review/request', {}, 'javier')[0], 200)
        self.assertEqual(self.mock.requests, [])
        self.assertEqual(self.request('POST', base + '/review/approve', {}, 'javier')[0], 409)
        self.assertEqual(self.request('POST', base + '/review/approve', {}, 'matias')[0], 200)
        self.mock.live_id = self.store.payload(slug)['piece']['id']
        for _ in range(12):
            self.app.tick()
            status, publication, _ = self.request('GET', base + '/publication', user='javier')
            if publication['state'] in ('published', 'failed'): break
        self.assertEqual(publication['state'], 'published', publication)
        self.assertEqual(len(publication['urls']), 3)
        self.assertTrue(publication['timeline'])
        self.assertEqual(self.mock.pushes[0]['actor'], 'javier')
        self.assertTrue(all(p.startswith('editorial/pieces/' + slug + '/') for p in self.mock.pushes[0]['paths']))
        self.assertTrue((self.root / 'data/candidates' / self.app.publisher.get(slug)['id'] / 'publish/cartas' / slug / 'index.html').is_file())

    def test_source_fields_and_schema_agree_with_editor(self):
        from studio.server.validation import validate_doc
        from tests.harness.validate import Validator
        schema = json.loads((ROOT / 'contracts/essay-doc.v1.schema.json').read_text())
        sample = copy.deepcopy(DOC)
        sample['blocks'] = [{'id': 'b-12345678', 'type': 'ul', 'items': [[{'t': 'text', 'v': 'A list item'}]]}]
        validate_doc(sample, 'en')
        self.assertEqual(Validator(schema).errors(sample), [])
        _, piece, _ = self.request('POST', '/api/pieces', {'kind': 'essay', 'title': 'Resources', 'source_locale': 'en'}, 'javier')
        self.assertEqual(self.request('GET', '/api/pieces/' + piece['slug'] + '/sources', user='javier')[1], [])
        self.assertEqual(self.request('GET', '/api/pieces/' + piece['slug'] + '/figures', user='javier')[1], {})

    def test_private_preview_and_strict_publication_checks_are_separate(self):
        _, piece, _ = self.request('POST', '/api/pieces', {'kind': 'essay', 'title': 'Private writing', 'source_locale': 'en'}, 'javier')
        slug = piece['slug']
        self.request('PUT', '/api/pieces/' + slug + '/doc/en', {'base_rev': 0, 'doc': DOC, 'cursor': {}}, 'javier')
        self.assertEqual(self.request('GET', '/preview/' + slug + '/en/', user='javier')[0], 200)
        self.assertEqual(self.request('POST', '/api/pieces/' + slug + '/review/request', {}, 'javier')[0], 409)
        self.assertEqual(self.mock.requests, [])

    def test_stale_browser_bundle_is_refused_without_blocking_private_api(self):
        # The host may only serve a bundle matching the current editor source.
        source = self.root / 'ui-repo'
        shutil.copytree(ROOT / 'studio/web', source / 'studio/web', ignore=shutil.ignore_patterns('node_modules'))
        app = Application(self.store, 'http://studio.invalid', 'integration-session-' + 'x'*32, source, preview=self.app.preview)
        server = Server(('127.0.0.1', 0), app)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            conn = HTTPConnection('127.0.0.1', server.server_port)
            conn.request('GET', '/'); response = conn.getresponse(); response.read()
            self.assertEqual(response.status, 503)
            conn.close()
        finally: server.shutdown(); server.server_close(); thread.join()
