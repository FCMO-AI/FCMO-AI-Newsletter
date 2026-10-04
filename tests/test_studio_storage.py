"""Durability and schema regressions for the private Studio store."""
import copy
from pathlib import Path
import tempfile
import unittest
from studio.server.storage import Store, Conflict, Locked
from studio.server.validation import validate_doc, validate_webp

ROOT = Path(__file__).resolve().parents[1]
DOC = {'schema': 'fcmo-essay-doc-v1', 'locale': 'en', 'title': 'An essay', 'dek': 'A useful idea',
       'blocks': [{'id': 'b-12345678', 'type': 'p', 'content': [{'t': 'text', 'v': 'Hello 42'}]}], 'footnotes': {}}

class Storage(unittest.TestCase):
    def setUp(self):
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit')
        self.store = Store(Path(self.tmp.name))
        self.slug = self.store.create('javier', 'essay', 'An essay', 'en')['slug']
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def test_autosave_conflict_and_restart(self):
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {'anchor': 42})
        with self.assertRaises(Conflict):
            self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        self.store.close()
        self.store = Store(Path(self.tmp.name))
        self.assertEqual(self.store.doc(self.slug, 'en')['doc'], DOC)
        self.assertEqual(self.store.piece(self.slug)['cursor']['en'], {'anchor': 42})
    def test_restore_checkpoints_current_unsaved_work_first(self):
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        old = self.store.checkpoint(self.slug, 'javier', 'First')
        changed = copy.deepcopy(DOC); changed['title'] = 'Second'
        self.store.save(self.slug, 'en', 'javier', 1, changed, {})
        self.store.restore(self.slug, old['rev'], 'javier')
        self.assertEqual(self.store.doc(self.slug, 'en')['doc'], DOC)
        self.assertTrue(any(x['rev'] == 2 for x in self.store.versions(self.slug)))
    def test_idle_and_locale_locks(self):
        self.store.lock(self.slug, 'en', 'javier')
        with self.assertRaises(Locked): self.store.lock(self.slug, 'en', 'matias')
        self.store.lock(self.slug, 'es-419', 'matias')
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        self.store.idle_checkpoints(now=self.store.clock() + 61)
        self.assertEqual(len(self.store.versions(self.slug)), 1)
    def test_closed_nodes_and_unsafe_links(self):
        for node in [{'t': 'html', 'v': '<b>x</b>'}, {'t': 'link', 'href': 'javascript:alert(1)', 'c': []}]:
            bad = copy.deepcopy(DOC); bad['blocks'][0]['content'] = [node]
            with self.assertRaises(ValueError): validate_doc(bad, 'en')
    def test_upload_rejects_metadata_and_non_webp(self):
        for blob in [b'not an image', b'RIFF\x10\0\0\0WEBPEXIF\x04\0\0\0gps!']:
            with self.assertRaises(ValueError): validate_webp(blob)
    def test_source_change_invalidates_human_review(self):
        self.store.save(self.slug, 'en', 'javier', 0, DOC, {})
        es = copy.deepcopy(DOC); es['locale'] = 'es-419'
        self.store.save(self.slug, 'es-419', 'javier', 1, es, {})
        self.store.locale_state(self.slug, 'es-419', 'javier', 'ready', True)
        changed = copy.deepcopy(DOC); changed['blocks'][0]['content'][0]['v'] = 'New 42'
        self.store.save(self.slug, 'en', 'javier', 2, changed, {})
        state = self.store.piece(self.slug)['locale_states']['es-419']
        self.assertEqual(state['state'], 'drafting')
        self.assertFalse(state['human_reviewed'])
