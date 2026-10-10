"""The host battery measures authenticated rendering before choosing its budget."""
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from studio.server import Application, Server, Store
from tests.test_studio_storage import ROOT, DOC


class JourneyTiming(unittest.TestCase):
    def test_budget_tracks_the_measured_cold_start_and_rejects_unread_values(self):
        from tests.harness.studio_host_journey import preview_timeout_ms
        self.assertEqual(preview_timeout_ms(50), 105000)
        self.assertEqual(preview_timeout_ms(2.1), 9200)
        self.assertGreater(preview_timeout_ms(75), preview_timeout_ms(50))
        for value in (None, 0, -1, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError): preview_timeout_ms(value)

    def test_probe_measures_real_authenticated_preview_without_credential_receipt(self):
        from tests.harness.studio_host_journey import measure_preview
        with TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'data')
            self.addCleanup(store.close)
            slug = store.create('javier', 'essay', 'Timing fixture', 'en')['slug']
            store.save(slug, 'en', 'javier', 0, DOC, {})
            app = Application(store, 'http://studio.invalid', 'timing-fixture-key-' + 'x' * 32, ROOT)
            app.auth.add_user('javier', 'timing-fixture-password')
            server = Server(('127.0.0.1', 0), app)
            app.origin = f'http://127.0.0.1:{server.server_port}'
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                result = measure_preview(f'http://127.0.0.1:{server.server_port}', slug, 'javier', 'timing-fixture-password')
                self.assertGreater(result['cold_preview_seconds'], 0)
                self.assertGreater(result['preview_timeout_ms'], result['cold_preview_seconds'] * 1000)
                self.assertEqual(set(result), {'cold_preview_seconds', 'preview_timeout_ms'})
                self.assertEqual(len(app.preview.cache), 1)
            finally:
                server.shutdown(); server.server_close(); thread.join()
