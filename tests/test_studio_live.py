"""Production wiring and real git transport; GitHub control plane stays offline."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from studio.server.publishing import GitHub, Workspace, Refused
from studio.server.storage import git
from tests.test_studio_integration import StudioIntegration

ROOT = Path(__file__).resolve().parents[1]

class LiveContract(unittest.TestCase):
    def test_deploy_and_recovery_build_editorial_and_validate_pr(self):
        pages = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertIn("'editorial/**'", pages)
        self.assertIn('--editorial editorial', pages)
        self.assertIn('--editorial lkg-source/editorial', pages)
        workflow = (ROOT / '.github/workflows/release-validate.yml').read_text()
        self.assertIn('publish-gate:', workflow)
        self.assertIn("'editorial/**'", workflow)
        self.assertIn('fetch-depth: 0', workflow)
        self.assertIn('ops/publish.py --check', workflow)
    def test_real_entry_and_launcher_exist(self):
        self.assertTrue((ROOT / 'ops/publish.py').is_file())
        self.assertTrue((ROOT / 'studio/host-ops/start.sh').is_file())
    def test_missing_credential_refuses_without_transport(self):
        with self.assertRaisesRegex(Refused, 'credencial'):
            GitHub({}).preflight('javier', 'matias')
    def test_failed_local_check_never_pushes(self):
        # Existing adversarial suite covers the durable state transition too.
        from tests.test_studio_publish import Publish
        case = Publish('test_red_local_candidate_never_exposes_branch')
        result = unittest.TestResult(); case.run(result)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

class BareRemote(StudioIntegration):
    # Exercise the real Workspace.push (not MockWorkspace.push), with a bare remote.
    def setUp(self):
        super().setUp()
        self.bare = self.root / 'publication.git'
        subprocess.run(['git', 'clone', '--bare', '--quiet', str(self.root / 'remote'), str(self.bare)], check=True)
        git(self.bare, 'tag', 'lkg', 'main')
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
                git(remote, 'fetch', str(bare), head)
                git(remote, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'merge', '--no-ff', '-m', 'Reviewed local publication', head)
                merge = git(remote, 'rev-parse', 'HEAD')
                git(remote, 'push', str(bare), 'HEAD:refs/heads/main')
                mock.prs[number].update(merged=True, merge_commit_sha=merge)
                return {'merged': True, 'sha': merge}
            def validate_remote(self, clone):
                if git(clone, 'remote', 'get-url', '--push', 'origin') != str(bare): raise Refused('Destino de prueba cambiado.')
        gh = LocalControl(original.tokens, original.api, live_base=original.live_base)
        self.app.publisher.github = gh
        self.app.publisher.workspace = Workspace(self.store, gh)
    def test_real_http_create_edit_preview_review_and_mock_publish(self):
        # Inherited full writing journey now uses a real git push.
        # The old assertion expected the mock transport's request; bank the
        # selected files from the actual bare remote instead.
        with patch.object(self.mock, 'pushes', [{'actor': 'javier', 'paths': ['editorial/pieces/placeholder/piece.json']}]):
            # Run an independent version below, keeping inherited tests intact.
            pass
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
        run = subprocess.run(['python3', 'ops/publish.py', '--check'], cwd=checkout, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn(b'42', (checkout / 'publish/cartas' / slug / 'index.html').read_bytes())
