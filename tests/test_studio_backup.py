from pathlib import Path
import tempfile
import unittest
from studio.server.backup import backup, restore, drill
from studio.server.auth import Auth, verify_password
from studio.server.storage import Store
from tests.test_studio_storage import DOC, ROOT

class Backup(unittest.TestCase):
    def test_round_trip_includes_autosave_beyond_last_commit_and_accounts(self):
        (ROOT / '_audit').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as temporary:
            root = Path(temporary); store = Store(root / 'data')
            auth = Auth(store, 'backup-fixture-session-key-' + 'a'*32)
            auth.add_user('javier', 'backup-fixture-password-123'); auth.add_user('matias', 'backup-fixture-password-456')
            value = store.create('javier', 'essay', 'Backup fixture', 'en')['slug']
            store.save(value, 'en', 'javier', 0, DOC, {}); store.checkpoint(value, 'javier')
            changed = dict(DOC, title='Uncommitted last sentence'); store.save(value, 'en', 'javier', 1, changed, {'anchor': 10})
            snapshot = backup(root / 'data', root / 'backups')
            observed = restore(snapshot, root / 'restore')
            recovered = Store(root / 'restore')
            try:
                self.assertTrue(verify_password('backup-fixture-password-123', recovered.db.execute("SELECT pw_scrypt FROM users WHERE key='javier'").fetchone()[0]))
                self.assertEqual(observed, [{'slug': value, 'checkpoints': 1}])
                self.assertEqual(recovered.doc(value, 'en')['doc'], changed)
                self.assertEqual(recovered.piece(value)['cursor']['en'], {'anchor': 10})
                self.assertEqual((snapshot.stat().st_mode & 0o777), 0o700)
            finally: recovered.close(); store.close()
            self.assertEqual(drill(root / 'data', root / 'backups', root / 'drill'), observed)
    def test_corrupt_snapshot_is_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as temporary:
            root = Path(temporary); store = Store(root / 'data'); store.close()
            snapshot = backup(root / 'data', root / 'backups'); (snapshot / 'studio.sqlite').write_bytes(b'corrupt')
            with self.assertRaises(ValueError): restore(snapshot, root / 'restore')
