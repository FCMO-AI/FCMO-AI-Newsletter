"""Mandatory byte identity with a full production build once A1/B land."""
import copy
import inspect
from pathlib import Path
import subprocess
import tempfile
import unittest
from studio.server.storage import Store
from studio.server.preview import Preview, RendererUnavailable, PREFIX
from tests.test_studio_storage import ROOT, DOC

class PreviewIdentity(unittest.TestCase):
    def test_preview_matches_full_build_byte_for_byte(self):
        from tools.paper.build import PaperBuilder
        if 'editorial' not in inspect.signature(PaperBuilder.__init__).parameters and not (ROOT / 'tools/paper/essays.py').is_file():
            self.skipTest('A1 production editorial renderer and B essay template are absent on this lane base; identity is not yet provable.')
        (ROOT / '_audit').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as temporary:
            root = Path(temporary); store = Store(root / 'data')
            try:
                value = store.create('javier', 'essay', 'Identity fixture', 'en')['slug']
                for loc in ('en', 'es-419', 'zh-Hans'):
                    doc = copy.deepcopy(DOC); doc['locale'] = loc
                    store.save(value, loc, 'javier', store.piece(value)['head_rev'], doc, {})
                    store.locale_state(value, loc, 'javier', 'ready', True, 'Leí y entiendo el texto chino')
                preview = Preview(store, ROOT)
                from studio.server.http import Application, Server
                from http.client import HTTPConnection
                import threading
                app = Application(store, 'https://studio.invalid', 'preview-fixture-session-' + 'a'*32, ROOT, preview=preview)
                app.auth.add_user('javier', 'preview-fixture-password-123')
                session = app.auth.login('javier', 'preview-fixture-password-123')
                server = Server(('127.0.0.1', 0), app)
                thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
                try:
                    conn = HTTPConnection('127.0.0.1', server.server_port, timeout=180)
                    conn.request('GET', '/preview/' + value + '/es-419/', headers={'Cookie': '__Host-studio=' + session['token']})
                    response = conn.getresponse(); candidate = response.read()
                    self.assertEqual(response.status, 200); conn.close()
                finally: server.shutdown(); server.server_close(); thread.join()
                out = root / 'full-build'; editorial = store.directory(value).parents[1]
                run = subprocess.run(['python3', 'tools/paper/build.py', '--stories', 'site/data/stories.v2.json', '--status', 'site/data/newsroom-status.json', '--editorial', str(editorial), '--out', str(out), '--base', preview.base], cwd=ROOT, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr.decode())
                self.assertEqual(candidate, (out / 'es/cartas' / value / 'index.html').read_bytes())
                # The Studio optimization must retain the complete production
                # tree, including taxonomy pages, assets and machine surfaces.
                optimized = preview.build(value)
                expected = {p.relative_to(out) for p in out.rglob('*') if p.is_file()}
                self.assertEqual(expected, {p.relative_to(optimized) for p in optimized.rglob('*') if p.is_file()})
                for relative in sorted(expected):
                    self.assertEqual((optimized / relative).read_bytes(), (out / relative).read_bytes(), str(relative))
            finally: store.close()
    def test_absent_renderer_fails_closed(self):
        if (ROOT / 'tools/paper/essays.py').is_file(): self.skipTest('Renderer integration is present; exercised by byte-identity test.')
        (ROOT / '_audit').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as temporary:
            store = Store(Path(temporary))
            try:
                value = store.create('javier', 'essay', 'No substitute renderer', 'en')['slug']
                with self.assertRaises(RendererUnavailable): Preview(store, ROOT).page(value, 'en')
            finally: store.close()
