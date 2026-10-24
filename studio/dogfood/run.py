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
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from studio.dogfood import fake_gh
from studio.server.auth import Auth
from studio.server.storage import Store, git

ROOT = Path(__file__).resolve().parents[2]
BROWSER_TIMEOUT = int(os.environ.get('DOGFOOD_BROWSER_TIMEOUT', '1200'))
PASSWORD = 'dogfood-local-fixture-password'
# Items scored before the measured world is switched on (their count is unchanged).
BASE_ITEMS = 17
# The items of the setup (launcher, login, readiness): what DOGFOOD_ONLY=world still runs besides the world items.
SETUP_ITEMS = 5
# DOGFOOD_ONLY=world skips the base journey and runs the setup plus the «mundo movido» items (a cheap red check).
ONLY_CHOICES = ('world',)
# The «mundo movido» items: GitHub moving under Studio, slow and cancelled Pages, infra trouble, content red.
WORLD_ITEMS = (
    'mundo movido: main moves 3 times during publication and it still publishes',
    'mundo movido: the Pages run of the merge is cancelled while a later run deploys, published',
    'mundo movido: a 70-minute (compressed) deploy publishes',
    'mundo movido: after the merge the piece never reaches failed',
    'mundo movido: infra trouble retries without a second approval',
    'mundo movido: a content-red gate returns the piece to changes requested',
    'Javier writes es-419 with fake translation: full cycle publishes',
)
# A 70-minute deploy, compressed by 1/600: the measured deploy is seconds here.
COMPRESSED_DEPLOY_S = 7.0

class Bot(threading.Thread):
    """Moves main from outside Studio: a commit every `every` seconds, `moves` times at most."""
    def __init__(self, root, every, moves, first_tick, first_delay=None):
        super().__init__(daemon=True)
        self.root = root; self.every = every; self.moves = moves; self.first_tick = first_tick
        self.first_delay = every if first_delay is None else first_delay
        self.stop_event = threading.Event(); self.commits = []; self.error = None
    def run(self):
        try:
            for number in range(self.first_tick, self.first_tick + self.moves):
                if self.stop_event.wait(self.first_delay if number == self.first_tick else self.every): return
                self.commits.append(fake_gh.bot_commit(self.root, number))
        except BaseException as exc:
            self.error = exc

class Journey:
    def __init__(self, root, browser=False):
        self.browser = browser
        self.root = root; self.scores = []; self.sessions = {}; self.process = None
        self.ticks = 100; self.states = {}; self.completed = False
        self.only = os.environ.get('DOGFOOD_ONLY') or None
        assert self.only in (None, *ONLY_CHOICES), 'DOGFOOD_ONLY must be one of ' + str(ONLY_CHOICES)
    def score(self, name, ok=True):
        # A red item is recorded and named; it never aborts the run, so the items after it still run.
        self.scores.append({'name': name, 'ok': bool(ok)})
        print(('PASS ' if ok else 'FAIL ') + name, flush=True)
        return bool(ok)
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
        """The publication once it is in `states`, or as it stands when it failed or time ran out: the caller's score
        decides, so one red item does not hide the next. DOGFOOD_WAIT_S caps every wait (cheap red checks)."""
        cap = os.environ.get('DOGFOOD_WAIT_S')
        end = time.monotonic() + (min(timeout, float(cap)) if cap else timeout)
        while True:
            pub = self.call('GET', '/api/pieces/' + slug + '/publication')
            if pub['state'] in states or pub['state'] == 'failed' or time.monotonic() >= end: return pub
            assert self.process.poll() is None, 'Launcher stopped'
            time.sleep(.3)
    # The body of every locale. The renderer refuses a piece whose locales do not carry the same numbers.
    BODY = {'en': 'Human publication with 42 ideas.', 'es-419': 'Una publicación humana con 42 ideas.', 'zh-Hans': '一篇人类文章包含42个想法。'}
    def create(self, title, author, en_text=None):
        piece = self.call('POST', '/api/pieces', {'kind': 'essay', 'title': title, 'source_locale': 'en'}, author)
        slug = piece['slug']; base = '/api/pieces/' + slug
        titles = {'en': title, 'es-419': 'Una prueba de publicación', 'zh-Hans': '出版测试'}
        text = dict(self.BODY)
        if en_text: text['en'] = en_text
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
        # Objects are shared with the checkout and every tracked file is overlaid below: no second copy of history.
        subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(source)], check=True)
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
                   STUDIO_TRANSLATION_PROVIDER='fake',
                   STUDIO_GH_CONFIG_JAVIER=str(self.root / 'javier'), STUDIO_GH_CONFIG_MATIAS=str(self.root / 'matias'),
                   DOGFOOD_ACTIVE='local-bare-only', DOGFOOD_ROOT=str(self.root), DOGFOOD_BARE=str(self.bare),
                   DOGFOOD_LIVE='http://127.0.0.1:' + str(self.pages.server_port) + '/FCMO-AI-Newsletter/',
                   PYTHONPATH=str(ROOT / 'studio/dogfood') + os.pathsep + str(source), PATH=str(binary) + os.pathsep + env['PATH'])
        self.env = env
        self.log = (self.root / 'server.log').open('w')
        self.process = subprocess.Popen(['sh', str(source / 'studio/host-ops/start.sh')], env=env, stdout=self.log, stderr=self.log, start_new_session=True)
        self.wait_healthy()
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
    # A cold start on a loaded host gets at least 120 s before the launcher counts as dead.
    START_TIMEOUT = max(120.0, float(os.environ.get('DOGFOOD_START_TIMEOUT', '180')))
    def wait_healthy(self):
        # A cold start (bytecode, renderer warm-up, loaded host) takes well over 10 s:
        # wait on /healthz against a deadline, and fail at once if the launcher dies.
        deadline = time.monotonic() + self.START_TIMEOUT
        while time.monotonic() < deadline:
            try:
                if self.request('GET', '/healthz')[0] == 200: return
            except OSError: pass
            assert self.process.poll() is None, (self.root / 'server.log').read_text()
            time.sleep(.25)
        raise AssertionError('Server did not become healthy within %ss' % self.START_TIMEOUT)
    def run(self):
        self.setup()
        if self.only == 'world': return self.world_items()
        try: self.base_journey()
        except Exception as exc:
            # An unexpected error in the base journey is a red item, not the end of the run.
            print('BASE JOURNEY ERROR: %s: %s' % (type(exc).__name__, exc), flush=True)
            self.score('base journey ran to its end', False)
        self.world_items()
    def base_journey(self):
        published = []
        for author, reviewer in (('javier', 'matias'), ('matias', 'javier')):
            slug = self.create('Dogfood ' + author, author)
            published.append(slug)
            base = '/api/pieces/' + slug
            self.call('POST', base + '/review/approve', {}, author, status=409)
            self.score(author + ': self-approval refused before public transport', not any(slug in x for x in git(self.bare, 'for-each-ref', '--format=%(refname)').splitlines()))
            self.call('POST', base + '/review/approve', {}, reviewer)
            pub = self.wait(slug, {'published'})
            self.score(author + ': create/edit/preview/review/publish over HTTP', len(pub.get('urls', [])) == 3)
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
        # CONTRACT CHANGE (L2, approved by the merger): this item used to expect `failed` («changed main refuses
        # transport/merge»). Under the L1 contract a moved main is not a refusal: the piece replays on it and publishes.
        # What the item still protects: the concurrent change survives, and only the piece differs from it.
        pub = self.wait(slug, {'published'})
        piece = 'editorial/pieces/' + slug
        changed = git(self.bare, 'diff', '--name-only', concurrent, 'main').splitlines()
        self.score('changed main: the piece replays on it and publishes, only the piece differs',
                   pub['state'] == 'published' and subprocess.run(['git', '--git-dir', str(self.bare), 'merge-base', '--is-ancestor', concurrent, 'main']).returncode == 0
                   and bool(changed) and all(c.startswith(piece + '/') for c in changed))
        after_publish = git(self.bare, 'rev-parse', 'main')
        conn = HTTPConnection('127.0.0.1', self.pages.server_port)
        conn.request('GET', '/FCMO-AI-Newsletter/cartas/' + published[0] + '/')
        response = conn.getresponse(); assert response.status == 200; response.read(); conn.close()
        self.call('POST', '/api/site/rollback', {'confirmation': 'Volver a la última versión comprobada'}, 'matias')
        conn = HTTPConnection('127.0.0.1', self.pages.server_port)
        conn.request('GET', '/FCMO-AI-Newsletter/cartas/' + published[0] + '/')
        response = conn.getresponse(); response.read(); conn.close()
        self.score('rollback serves LKG and preserves main', response.status == 404 and git(self.bare, 'rev-parse', 'main') == after_publish and json.loads((self.root / 'gh.json').read_text())['rollback'])
        refs = git(self.bare, 'for-each-ref', '--format=%(refname)')
        self.score('no draft refs or unapproved piece in public main', 'refs/heads/draft/' not in refs and 'missing-protections' not in git(self.bare, 'ls-tree', '-r', '--name-only', 'main'))
    def set_world(self, **knobs):
        """The measured world, read by every gh call from now on. Each scenario states all its knobs."""
        fake_gh.write_world(self.root, knobs)
    def gh_state(self):
        return json.loads((self.root / 'gh.json').read_text())
    def count_reviews(self):
        return sum(1 for c in self.gh_state()['calls'] if c['method'] == 'POST' and c['endpoint'].endswith('/reviews'))
    @staticmethod
    def expected_total(browser, captures, only=None):
        """Every item the journey must score: the base items, the browser items, and the measured-world items.
        With only='world' (DOGFOOD_ONLY): the setup plus the measured-world items."""
        if only == 'world': return SETUP_ITEMS + len(WORLD_ITEMS)
        return BASE_ITEMS + len(WORLD_ITEMS) + ((8 + bool(captures)) if browser else 0)
    def timeline_states(self, slug):
        return [entry.get('state') for entry in self.call('GET', '/api/pieces/' + slug + '/publication').get('timeline', [])]
    def piece_state(self, slug):
        return self.call('GET', '/api/pieces/' + slug)['state']
    def world_items(self):
        """Publications through the measured world. Each item says what it proves in its name; one red item
        (or one that raises) is scored FAIL and the next still runs."""
        for index, item in enumerate((self.world_main_moves, self.world_pages_cancelled, self.world_slow_deploy, self.world_never_failed,
                                      self.world_infra_retry, self.world_content_red, self.world_es_javier)):
            try: item()
            except Exception as exc:
                print('ITEM ERROR: %s: %s' % (type(exc).__name__, exc), flush=True)
                self.score(WORLD_ITEMS[index], False)
    def world_main_moves(self):
        # 1. main moves three times while the piece is in publication: it still publishes, replayed on the moved main.
        # The fake reports a PR whose head lacks main as 'behind' and refuses to merge it: without replay-on-behind this is red.
        self.set_world(pages_run_s=0, gate_s=0.5, lazy_mergeable_s=1.5, behind=True)
        slug = self.create('Mundo movido: tres movimientos', 'matias')
        moves_start = len(self.gh_state().get('main_moves', []))
        bot = Bot(self.root, every=2.0, moves=3, first_tick=self.ticks + 1, first_delay=0.5); self.ticks += 3
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'javier')
        bot.start()
        pub = self.wait(slug, {'published'}, timeout=1800)
        bot.join(timeout=60)
        moved_before_merge = self.gh_state().get('moves_before_merge', 0) - moves_start
        self.score(WORLD_ITEMS[0], len(bot.commits) >= 3 and bot.error is None and moved_before_merge >= 1 and len(pub.get('urls', [])) == 3)
    def world_pages_cancelled(self):
        # 2. the merge's Pages run is replaced by a later run for a commit that moved main; the later run deploys.
        # The later commit lands inside the fake's merge call (bot_after_merge), so there is no race with this harness.
        self.ticks += 1
        self.set_world(pages_run_s=4.0, pages_cancel_in_progress=True, gate_s=0.5, bot_after_merge=self.ticks)
        slug = self.create('Mundo movido: Pages cancelado', 'javier')
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'matias')
        pub = self.wait(slug, {'published'}, timeout=1800)
        state = self.gh_state()
        merge, later = state.get('merge_sha'), state.get('later_sha')
        runs = state.get('pages', [])
        merge_run = [r for r in runs if r['head_sha'] == merge and r['conclusion'] == 'cancelled']
        later_run = [r for r in runs if r['head_sha'] == later and r['conclusion'] == 'success']
        self.states[2] = self.timeline_states(slug)
        self.score(WORLD_ITEMS[1], bool(merge_run) and bool(later_run) and later != merge and len(pub.get('urls', [])) == 3)
    def world_slow_deploy(self):
        # 3. a 70-minute deploy, compressed: the piece waits in merged, then publishes.
        self.set_world(pages_run_s=COMPRESSED_DEPLOY_S, gate_s=0.5)
        slug = self.create('Mundo movido: despliegue lento', 'matias')
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'javier')
        self.wait(slug, {'merged'}, timeout=1800)
        started = time.monotonic()
        pub = self.wait(slug, {'published'}, timeout=1800)
        deploy_s = time.monotonic() - started
        self.states[3] = self.timeline_states(slug)
        self.score(WORLD_ITEMS[2], deploy_s >= COMPRESSED_DEPLOY_S * 0.8 and len(pub.get('urls', [])) == 3)
    def world_never_failed(self):
        # 4. after the merge, neither slow nor cancelled deploys ever put the piece in failed.
        after_merge = lambda states: states[states.index('merged'):] if 'merged' in states else []
        states_2, states_3 = self.states.get(2, []), self.states.get(3, [])
        self.score(WORLD_ITEMS[3], bool(after_merge(states_2)) and 'failed' not in after_merge(states_2)
                   and bool(after_merge(states_3)) and 'failed' not in after_merge(states_3))
    def world_infra_retry(self):
        # 5. transient GitHub trouble (mergeability unknown, merge refused): retried by Studio, one approval only.
        self.set_world(merge_refusals=1, lazy_mergeable_s=3.0, pages_run_s=0, gate_s=0.5)
        slug = self.create('Mundo movido: reintento', 'javier')
        reviews_before = self.count_reviews()
        refusals_before = self.gh_state().get('refusals_done', 0)
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'matias')
        pub = self.wait(slug, {'published'}, timeout=1800)
        refused = self.gh_state().get('refusals_done', 0) - refusals_before
        self.score(WORLD_ITEMS[4], len(pub.get('urls', [])) == 3 and refused == 1 and self.count_reviews() - reviews_before == 1)
    def world_content_red(self):
        # 6. a content-red gate: the approved text is refused by the public check, the piece goes back to changes requested.
        self.set_world(pages_run_s=0, gate_s=0.5)
        slug = self.create('Mundo movido: contenido rojo', 'matias', en_text=self.red_text())
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'javier')
        pub = self.wait(slug, {'failed'}, timeout=1800)
        self.score(WORLD_ITEMS[5], self.piece_state(slug) == 'changes_requested' and 'comprobaciones' in pub.get('error_plain', ''))
    def world_es_javier(self):
        # 7. Javier writes in es-419 (the source); the fake translator prepares en and zh-Hans; the full cycle publishes.
        self.set_world(pages_run_s=0, gate_s=0.5)
        slug = self.make_es_piece('Javier escribe en español', 'javier')
        self.call('POST', '/api/pieces/' + slug + '/review/approve', {}, 'matias')
        pub = self.wait(slug, {'published'}, timeout=1800)
        self.score(WORLD_ITEMS[6], len(pub.get('urls', [])) == 3)
    @staticmethod
    def red_text():
        # The marker rides in the source text. The text keeps the numbers of the other locales: a piece whose en text lost
        # the «42» of es-419 and zh-Hans (numeric token mismatch) never renders, so its preview was a 503 and the item never ran.
        return Journey.BODY['en'][:-1] + ' and ' + fake_gh.CONTENT_RED + '.'
    def make_es_piece(self, title, author):
        """Javier's piece: es-419 is the source; the translate endpoint (STUDIO_TRANSLATION_PROVIDER=fake) prepares the rest."""
        piece = self.call('POST', '/api/pieces', {'kind': 'essay', 'title': title, 'source_locale': 'es-419'}, author)
        slug = piece['slug']; base = '/api/pieces/' + slug
        current = self.call('GET', base + '/doc/es-419', user=author)
        doc = {'schema': 'fcmo-essay-doc-v1', 'locale': 'es-419', 'title': title, 'dek': 'Una edición comprobada.',
               'blocks': [{'id': 'b-01234567', 'type': 'p', 'content': [{'t': 'text', 'v': 'Una publicación escrita en español con 42 ideas.'}], 'attrs': {}}],
               'footnotes': {}}
        self.call('PUT', base + '/doc/es-419', {'base_rev': current['rev'], 'doc': doc, 'cursor': {'anchor': 2}}, author)
        self.call('POST', base + '/locale/es-419/state', {'state': 'ready', 'reviewed': True}, author)
        self.call('POST', base + '/translate', {'base_rev': self.call('GET', base, user=author)['head_rev']}, author)
        for loc in ('en', 'zh-Hans'):
            self.call('POST', base + '/locale/' + loc + '/state', {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, author)
        self.call('POST', base + '/versions', {'name': 'Reviewed draft'}, author)
        self.call('POST', base + '/review/request', {}, author)
        return slug
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
                result = subprocess.run(['node', str(ROOT / ('tests/harness/browser/' + name + '.mjs')), self.origin + '/', *args], env=env, stdout=f, stderr=f, timeout=BROWSER_TIMEOUT)
            self.score('browser ' + name, result.returncode == 0)
        if os.environ.get('DOGFOOD_CAPTURES'):
            with (self.root / 'studio_captures.log').open('w') as f:
                result = subprocess.run(['node', str(ROOT / 'tests/harness/browser/studio_captures.mjs'), self.origin + '/', seeded, os.environ['DOGFOOD_CAPTURES']], env=env, stdout=f, stderr=f, timeout=BROWSER_TIMEOUT)
            self.score('browser studio_captures', result.returncode == 0)
        with (self.root / 'studio_actions.log').open('w') as f:
            result = subprocess.run(['node', str(ROOT / 'tests/harness/browser/studio_actions.mjs'), self.origin + '/'], env=env, stdout=f, stderr=f, timeout=BROWSER_TIMEOUT)
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
        expected = self.expected_total(self.browser, os.environ.get('DOGFOOD_CAPTURES'), self.only)
        passed = sum(s['ok'] for s in self.scores)
        self.completed = passed == expected and len(self.scores) == expected
        summary = {'passed': passed, 'total': expected, 'executed': len(self.scores), 'completed': self.completed, 'checks': self.scores}
        (self.root / 'summary.json').write_text(json.dumps(summary, indent=2))
        for failed in (s['name'] for s in self.scores if not s['ok']): print('FAIL ' + failed, flush=True)
        print(f"DOGFOOD {summary['passed']}/{summary['total']}; evidence: {self.root}", flush=True)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--keep', type=Path); parser.add_argument('--browser', action='store_true'); args = parser.parse_args()
    root = args.keep.resolve() if args.keep else Path(tempfile.mkdtemp(prefix='studio-dogfood-'))
    # A signal must unwind through the finally blocks: the temporary tree is gigabytes.
    for number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(number, lambda signum, frame: sys.exit(128 + signum))
    journey = None
    try:
        root.mkdir(parents=True, exist_ok=True)
        journey = Journey(root, args.browser)
        try: journey.run()
        except BaseException:
            journey.scores.append({'name': 'complete journey', 'ok': False})
            log = root / 'server.log'
            if log.is_file(): print('--- server.log (tail) ---\n' + '\n'.join(log.read_text(errors='replace').splitlines()[-40:]), flush=True)
            for extra in sorted([*root.glob('strict-*.log'), *root.glob('studio_*.log'), *root.glob('lkg.log'), *root.glob('build-*.log'), *root.glob('check-*.log')]):
                print('--- ' + extra.name + ' (tail) ---\n' + '\n'.join(extra.read_text(errors='replace').splitlines()[-40:]), flush=True)
            raise
        finally: journey.close()
    finally:
        if not args.keep: shutil.rmtree(root, ignore_errors=True)
    # Red items were scored and named, and the run went on; the exit status still says the run is not green.
    if journey is not None and not journey.completed: sys.exit(1)

if __name__ == '__main__': main()
