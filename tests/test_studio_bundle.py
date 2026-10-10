"""Offline builds remain reproducible and never certify unsupported source drift."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from studio.server.bundle import ready
from tests.test_studio_storage import ROOT


class OfflineBundle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / 'studio/web', self.root / 'studio/web', ignore=shutil.ignore_patterns('node_modules'))
        for name in ('fonts', 'css'):
            shutil.copytree(ROOT / 'site-src/assets' / name, self.root / 'site-src/assets' / name)

    def build(self):
        return subprocess.run(['node', 'build.mjs'], cwd=self.root / 'studio/web', capture_output=True, text=True)

    def test_offline_rebuild_is_deterministic_and_binds_the_changed_login(self):
        first = self.build()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertTrue(ready(self.root))
        dist = self.root / 'studio/web/dist'
        before = {p.name: p.read_bytes() for p in dist.iterdir() if p.is_file()}
        self.assertIn("normalize('NFD')", before['app.js'].decode())
        self.assertEqual(self.build().returncode, 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in dist.iterdir() if p.is_file()})

    def test_offline_build_refuses_uncompiled_editor_changes(self):
        source = self.root / 'studio/web/src/editor.js'
        source.write_text(source.read_text() + '\n// unsupported offline change\n')
        self.assertNotEqual(self.build().returncode, 0)
        self.assertFalse(ready(self.root))
