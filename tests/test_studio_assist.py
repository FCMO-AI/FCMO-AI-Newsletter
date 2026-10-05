import json
from pathlib import Path
import secrets
import tempfile
import unittest
from studio.server.assist import accept
from studio.server.storage import Store, Conflict
from tests.test_studio_storage import ROOT, DOC

class AssistProvenance(unittest.TestCase):
    def test_accept_and_edit_never_marks_assistant_as_human_reviewed(self):
        # A clean candidate/CI checkout has no ignored _audit directory yet.
        # This private fixture must be runnable without another test creating it.
        with tempfile.TemporaryDirectory(prefix='studio-assist-') as temporary:
            store = Store(Path(temporary))
            try:
                value = store.create('javier', 'essay', 'Optional assistant', 'en')['slug']
                store.save(value, 'en', 'javier', 0, DOC, {})
                ident = secrets.token_hex(12)
                (store.data / 'jobs/queued' / (ident + '.json')).write_text(json.dumps({'author': 'javier', 'slug': value, 'locale': 'en', 'rev': 1}))
                (store.data / 'jobs/done' / (ident + '.json')).write_text(json.dumps({'model': 'fixture-model', 'suggestions': [{'block_id': 'b-12345678', 'text': 'An assistant suggestion 42'}]}))
                accept(store, ident, 'javier', ['b-12345678'], 1)
                store.locale_state(value, 'en', 'javier', 'ready', False)
                provenance = store.payload(value)['provenance']['en']
                self.assertEqual(provenance['origin'], 'agent_draft'); self.assertFalse(provenance['human_reviewed'])
                doc = store.doc(value, 'en')['doc']; doc['title'] = 'Human edit'
                store.save(value, 'en', 'javier', store.piece(value)['head_rev'], doc, {})
                store.locale_state(value, 'en', 'javier', 'ready', False)
                self.assertEqual(store.payload(value)['provenance']['en']['origin'], 'agent_draft_human_edited')
                self.assertFalse(store.payload(value)['provenance']['en']['human_reviewed'])
                with self.assertRaises(Conflict): accept(store, ident, 'javier', ['b-12345678'], 1)
            finally: store.close()
