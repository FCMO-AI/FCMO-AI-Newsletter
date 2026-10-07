"""Production wiring and real git transport; GitHub control plane stays offline."""
import json
from pathlib import Path
import subprocess
import unittest
from studio.server.publishing import GitHub, Workspace, Refused
from studio.server.storage import git
from tests import test_studio_integration as integration

ROOT = Path(__file__).resolve().parents[1]

class LiveContract(unittest.TestCase):
    def test_deploy_and_recovery_build_editorial_and_validate_pr(self):
        pages = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn("'editorial/**'", pages)
        self.assertIn('--editorial editorial', pages)
        self.assertIn('--editorial lkg-source/editorial', pages)
        workflow = (ROOT / '.github/workflows/release-validate.yml').read_text()
        self.assertIn('publish-gate:', workflow)
        self.assertNotIn('    paths:', workflow, 'Required check must run for every protected-main PR')
        self.assertIn('fetch-depth: 0', workflow)
        self.assertIn('ops/publish.py --check', workflow)
    def test_recovery_runs_both_pre_studio_and_editorial_lkg_renderers(self):
        import tempfile, os, sys
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        start = workflow.index('          if test -f lkg-source/tools/paper/build.py; then')
        stop = workflow.index('            mkdir -p rollback-publish/data', start)
        shell = workflow[start:stop] + '\nfi\n'
        for editorial in (False, True):
            with self.subTest(editorial=editorial), tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp:
                root = Path(tmp); builder = root / 'lkg-source/tools/paper'
                builder.mkdir(parents=True); (builder / 'build.py').touch()
                if editorial: (builder / 'essays.py').touch()
                binary = root / 'bin'; binary.mkdir()
                python = binary / 'python'
                python.write_text('#!' + sys.executable + '\n' + "import sys,pathlib\nif '--editorial' in sys.argv and not pathlib.Path('lkg-source/tools/paper/essays.py').exists(): raise SystemExit(2)\nwith open('calls', 'a') as f: f.write(' '.join(sys.argv[1:])+'\\n')\n")
                python.chmod(0o700)
                env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ['PATH'], RUNNER_TEMP=str(root), BASE_PATH='/FCMO-AI-Newsletter/')
                result = subprocess.run(['bash', '-e', '-c', shell], cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual('--editorial' in (root / 'calls').read_text(), editorial)
    def test_real_entry_and_launcher_exist(self):
        self.assertTrue((ROOT / 'ops/publish.py').is_file())
        self.assertTrue((ROOT / 'studio/host-ops/start.sh').is_file())
    def test_missing_credential_refuses_without_transport(self):
        with self.assertRaisesRegex(Refused, 'credencial'):
            GitHub({}).preflight('javier', 'matias')
    def test_failed_local_check_never_pushes(self):
        # Existing adversarial suite covers the durable state transition too.
        from tests.test_studio_publish import Publish
        case = Publish('test_local_failure_does_not_make_text_public')
        result = unittest.TestResult(); case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

class BareRemote(integration.StudioIntegration):
    test_source_fields_and_schema_agree_with_editor = None
    test_private_preview_and_strict_publication_checks_are_separate = None
    test_stale_browser_bundle_is_refused_without_blocking_private_api = None
    # Exercise the real Workspace.push (not MockWorkspace.push), with a bare remote.
    def setUp(self):
        super().setUp()
        self.bare = self.root / 'publication.git'
        subprocess.run(['git', 'clone', '--bare', '--quiet', str(self.root / 'remote'), str(self.bare)], check=True)
        git(self.bare, 'tag', '-f', 'lkg', 'main')
        clone = self.store.data / 'clone'
        git(clone, 'remote', 'set-url', 'origin', str(self.bare))
        original = self.app.publisher.github
        mock = self.mock; bare = self.bare; remote = self.root / 'remote'
        class LocalControl(GitHub):
            def branch(self, user, branch):
                run = subprocess.run(['git', '--git-dir', str(bare), 'rev-parse', '--verify', 'refs/heads/' + branch], capture_output=True, text=True)
                if run.returncode: return None
                sha = run.stdout.strip(); mock.refs[branch] = sha
                return sha
            def merge(self, user, number, head):
                super().merge(user, number, head)
                git(remote, 'fetch', str(bare), head)
                git(remote, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'merge', '--no-ff', '-m', 'Reviewed local publication', head)
                merge = git(remote, 'rev-parse', 'HEAD')
                git(remote, 'push', str(bare), 'HEAD:refs/heads/main')
                mock.prs[number].update(merged=True, merge_commit_sha=merge)
                return {'merged': True, 'sha': merge}
            def pages(self, user, merge):
                self.asserted_merge = merge
                return {'id': 8}
            def validate_remote(self, clone):
                if git(clone, 'remote', 'get-url', '--push', 'origin') != str(bare): raise Refused('Destino de prueba cambiado.')
        gh = LocalControl(original.tokens, original.api, live_base=original.live_base)
        self.app.github = gh
        self.app.publisher.github = gh
        from studio.server.snapshot import refresh
        refresh(self.store, gh)
        self.app.publisher.workspace = Workspace(self.store, gh, ['python3', 'ops/publish.py', '--check', '--fixture-build'])
        self.app.publisher.workspace.production_check = True
        from studio.server import issues
        from studio.server.checks import checks
        self.app.publisher.checker = lambda slug: issues.checks(self.store, self.app.preview, slug) if self.store.piece(slug)['kind'] == 'issue' else checks(self.store, self.app.preview, slug)
    def test_real_http_create_edit_preview_review_and_mock_publish(self):
        import copy
        from tests.test_studio_storage import DOC
        _, piece, _ = self.request('POST', '/api/pieces', {'kind': 'essay', 'title': 'Bare remote essay', 'source_locale': 'en'}, 'javier')
        slug = piece['slug']; base = '/api/pieces/' + slug
        for loc in ('en', 'es-419', 'zh-Hans'):
            doc = copy.deepcopy(DOC); doc['locale'] = loc
            if loc != 'en':
                doc['title'] = 'Ensayo publicado' if loc == 'es-419' else '发表的随笔'
                doc['dek'] = 'Una edición comprobada' if loc == 'es-419' else '经过验证的版本'
                doc['blocks'][0]['content'][0]['v'] = 'Una publicación humana con 42 ideas.' if loc == 'es-419' else '一篇人类文章包含42个想法。'
            rev = self.store.piece(slug)['head_rev']
            self.assertEqual(self.request('PUT', base + '/doc/' + loc, {'base_rev': rev, 'doc': doc, 'cursor': {}}, 'javier')[0], 200)
            self.assertEqual(self.request('POST', base + '/locale/' + loc + '/state', {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, 'javier')[0], 200)
        status, html, _ = self.request('GET', '/preview/' + slug + '/en/', user='javier')
        self.assertEqual(status, 200); self.assertIn(b'42', html)
        self.assertEqual(self.request('POST', base + '/review/request', {}, 'javier')[0], 200)
        self.assertEqual(self.request('POST', base + '/review/approve', {}, 'matias')[0], 200)
        self.mock.live_id = self.store.payload(slug)['piece']['id']
        for _ in range(14):
            self.app.tick(); publication = self.app.publisher.get(slug)
            if publication['state'] in ('published', 'failed'): break
        self.assertEqual(publication['state'], 'published', publication)
        head = git(self.bare, 'rev-parse', 'main')
        self.assertEqual(head, publication['payload']['merge_sha'])
        self.assertIn(slug, git(self.bare, 'show', 'main:editorial/pieces/' + slug + '/piece.json'))
        checkout = self.root / 'published-checkout'
        subprocess.run(['git', 'clone', '--quiet', str(self.bare), str(checkout)], check=True)
        run = subprocess.run(['python3', 'ops/publish.py', '--check', '--fixture-build'], cwd=checkout, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(b'42', (checkout / 'publish/cartas' / slug / 'index.html').read_bytes())

        # Assemble an actual curated edition from the committed essay, edit it,
        # preview privately, obtain the other person's review, and publish it.
        issue = {'schema': 'fcmo-issue-v1', 'id': '2026-10-05-bare-edition', 'date': '2026-10-05',
                 'title': {'en': 'Test edition', 'es-419': 'Edición de prueba', 'zh-Hans': '测试版本'},
                 'note': {'en': 'Read our essay.', 'es-419': 'Lee nuestro ensayo.', 'zh-Hans': '阅读我们的随笔。'},
                 'slots': [{'slot': 'principal', 'ref': self.store.payload(slug)['piece']['id']}]}
        status, draft, _ = self.request('POST', '/api/issues', issue, 'matias')
        self.assertEqual(status, 200, draft)
        issue['note']['en'] = 'A reviewed edition.'
        self.assertEqual(self.request('PUT', '/api/issues/' + issue['id'], {'base_rev': draft['rev'], 'issue': issue}, 'matias')[0], 200)
        for loc in ('en', 'es-419', 'zh-Hans'):
            self.assertEqual(self.request('POST', '/api/issues/' + issue['id'] + '/locale/' + loc + '/state',
                                         {'state': 'ready', 'reviewed': True, 'confirmation': 'Leí y entiendo el texto chino'}, 'matias')[0], 200)
        status, html, _ = self.request('GET', '/preview/' + issue['id'] + '/en/', user='matias')
        self.assertEqual(status, 200, html); self.assertIn(b'A reviewed edition.', html)
        _, issue_checks, _ = self.request('GET', '/api/issues/' + issue['id'] + '/checks', user='matias')
        self.assertTrue(all(c['ok'] for c in issue_checks), issue_checks)
        status, result, _ = self.request('POST', '/api/issues/' + issue['id'] + '/review/request', {}, 'matias')
        self.assertEqual(status, 200, result)
        self.assertEqual(self.request('POST', '/api/issues/' + issue['id'] + '/review/approve', {}, 'javier')[0], 200)
        self.mock.live_id = issue['id']
        for _ in range(14):
            self.app.tick(); publication = self.app.publisher.get(issue['id'])
            if publication['state'] in ('published', 'failed'): break
        self.assertEqual(publication['state'], 'published', publication)
        git(checkout, 'fetch', 'origin', 'main'); git(checkout, 'checkout', '--detach', 'FETCH_HEAD')
        run = subprocess.run(['python3', 'ops/publish.py', '--check', '--fixture-build'], cwd=checkout, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(json.loads(git(self.bare, 'show', 'main:editorial/issues/' + issue['id'] + '.json')), issue)
        for prefix in ('', 'es/', 'zh/'):
            page = checkout / 'publish' / prefix / 'cartas/ediciones' / issue['id'] / 'index.html'
            self.assertTrue(page.is_file()); self.assertIn(issue['id'].encode(), page.read_bytes())

class CredentialsAndBase(unittest.TestCase):
    def test_cli_keeps_tokens_out_of_arguments_and_disables_fallback(self):
        import os
        from unittest.mock import patch
        from studio.server.credentials import GitHubCLI
        with patch.dict(os.environ, {'GH_TOKEN': 'fixture-do-not-use', 'GITHUB_TOKEN': 'fixture-other'}):
            gh = GitHubCLI({'javier': 'fixture-config'})
            env, options = gh.push_environment('javier', Path('unused'))
            self.assertNotIn('GH_TOKEN', env); self.assertNotIn('GITHUB_TOKEN', env)
            self.assertEqual(env['GH_CONFIG_DIR'], 'fixture-config')
            self.assertIn('credential.helper=!gh auth git-credential', options)
    def test_cli_same_github_identity_cannot_review_itself(self):
        from unittest.mock import patch
        from studio.server.credentials import GitHubCLI
        gh = GitHubCLI()
        with patch.object(gh, 'identity', return_value='same-login'):
            with self.assertRaisesRegex(Refused, 'distintas'): gh.preflight('javier', 'matias')
    def test_dry_run_records_review_but_worker_has_no_external_effect(self):
        import tempfile, os
        from unittest.mock import patch, Mock
        from studio.server.storage import Store
        from studio.server.http import Application
        from tests.test_studio_storage import DOC
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp, patch.dict(os.environ, {'STUDIO_DRY_RUN': '1'}):
            store = Store(Path(tmp))
            try:
                app = Application(store, 'https://studio.invalid', 'fixture-session-' + 'x'*32, ROOT)
                slug = store.create('javier', 'essay', 'Dry run', 'en')['slug']
                store.save(slug, 'en', 'javier', 0, DOC, {})
                app.publisher.checker = lambda value: [{'ok': True}]
                app.publisher.request(slug, 'javier')
                session = {'user': 'matias'}
                result = app.api('POST', '/api/pieces/' + slug + '/review/approve', {}, {}, session)
                self.assertEqual(result['state'], 'approved')
                app.publisher.advance = Mock()
                app.live_enabled = True; app.tick()
                app.publisher.advance.assert_not_called()
            finally: store.close()
    def test_tampered_immutable_snapshot_is_refused(self):
        import tempfile
        from studio.server.storage import Store
        from studio.server.snapshot import refresh
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp:
            root = Path(tmp); store = Store(root / 'data')
            try:
                clone = store.data / 'clone'
                git(clone, 'remote', 'set-url', 'origin', str(clone))
                class LocalFixture(GitHub):
                    def validate_remote(self, path): pass
                snapshot = refresh(store, LocalFixture({}))
                (snapshot / 'unexpected-file').write_text('fixture')
                with self.assertRaisesRegex(Refused, 'copia'): refresh(store, LocalFixture({}))
            finally: store.close()
    def test_cli_transport_loss_on_write_stays_unknown(self):
        from unittest.mock import patch
        from studio.server.credentials import GitHubCLI
        from studio.server.publishing import UnknownEffect
        run = subprocess.CompletedProcess([], 1, '', 'connection closed')
        with patch('studio.server.credentials.subprocess.run', return_value=run):
            with self.assertRaises(UnknownEffect): GitHubCLI().request('javier', 'POST', '/pulls', {})
    def test_stale_base_refuses_real_push(self):
        import tempfile
        from studio.server.storage import Store
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as tmp:
            root = Path(tmp); store = Store(root / 'data')
            try:
                source = root / 'source'; source.mkdir(); git(source, 'init', '-q', '-b', 'main')
                git(source, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '--allow-empty', '-qm', 'Base')
                old = git(source, 'rev-parse', 'HEAD')
                remote = root / 'remote.git'
                subprocess.run(['git', 'clone', '--quiet', '--bare', str(source), str(remote)], check=True)
                git(source, 'remote', 'add', 'origin', str(remote))
                pub = {'payload': {'candidate': str(source), 'base_sha': old}}
                Workspace(store, GitHub({})).verify_base(pub)
                git(source, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '--allow-empty', '-qm', 'New base')
                git(source, 'push', 'origin', 'HEAD:refs/heads/main')
                with self.assertRaisesRegex(Refused, 'base'): Workspace(store, GitHub({})).verify_base(pub)
            finally: store.close()
