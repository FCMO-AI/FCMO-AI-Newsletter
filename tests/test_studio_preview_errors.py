"""A failed production build must name its bound without exposing diagnostics."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from studio.server.preview import Preview, RendererUnavailable
from studio.server.storage import Store
from tests.test_studio_storage import ROOT, DOC


class PreviewFailureReason(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / 'data')
        self.addCleanup(self.store.close)
        self.slug = self.store.create('javier', 'essay', 'A private draft', 'en')['slug']
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        self.preview = Preview(self.store, ROOT)

    def fail_build(self, stderr):
        result = subprocess.CompletedProcess([], 1, b'', stderr.encode())
        with patch('studio.server.preview.subprocess.run', return_value=result):
            with self.assertRaises(RendererUnavailable) as caught:
                self.preview.page(self.slug, 'en')
        self.assertEqual(list((self.store.data / 'previews').iterdir()), [])
        self.assertEqual(self.preview.cache, {})
        return str(caught.exception)

    def test_search_budget_failure_names_the_actual_publication_bound(self):
        message = self.fail_build('Traceback with private fixture text\nValueError: search index exceeds 153600 bytes for en: 166155\n')
        self.assertIn('índice de búsqueda de en', message)
        self.assertIn('166155 bytes', message)
        self.assertIn('153600 bytes', message)
        self.assertIn('generador de publicación', message)
        self.assertNotIn('fixture', message)
        self.assertNotIn('integración del formato', message)

    def test_other_build_failures_do_not_claim_an_absent_integration_or_leak_stderr(self):
        message = self.fail_build('A private path and password must not appear in the refusal')
        self.assertIn('renderer de producción', message)
        self.assertNotIn('integración del formato', message)
        self.assertNotIn('private path', message)
        self.assertNotIn('password', message)


if __name__ == '__main__': unittest.main()
