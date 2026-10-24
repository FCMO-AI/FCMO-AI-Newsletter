"""The background worker survives a failed tick and leaves a content-free diagnosis."""
import contextlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from studio.server.http import Application
from studio.server.storage import Store
from tests.test_studio_storage import ROOT

SECRET_SLUG = 'secret-slug-piece'
SECRET_BODY = 'body text token=abc123'


class OneTurnStop:
    """Stop event whose wait() lets `ticks` loop turns run, then ends the worker."""
    def __init__(self, ticks):
        self.left = ticks
    def wait(self, timeout):
        if self.left > 0:
            self.left -= 1
            return False
        return True


class WorkerDiagnosis(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Store(Path(tmp.name) / 'data')
        self.addCleanup(self.store.close)
        with self.store.mutex:
            self.store.db.execute("INSERT INTO publications(id, slug, kind, state) VALUES (?,?,?,?)", ('pub-1', SECRET_SLUG, 'essay', 'pr_open'))
            self.store.db.commit()
        self.app = Application(self.store, 'http://studio.invalid', 'worker-diag-key-' + 'x' * 32, ROOT)

    def run_worker(self, script, turns):
        """script: list of exceptions (or None for a clean tick) consumed one per tick."""
        calls = []
        def tick():
            calls.append(1)
            step = script[len(calls) - 1]
            if step is not None: raise step
        self.app.tick = tick
        self.app.stop = OneTurnStop(turns)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.app.worker()
        return calls, err.getvalue().splitlines()

    def test_failed_tick_logs_class_and_publication_states_only(self):
        calls, lines = self.run_worker([RuntimeError(f'{SECRET_BODY} slug {SECRET_SLUG}')], turns=1)
        self.assertEqual(lines, ['studio-worker error class=RuntimeError queued=pr_open:1'])
        joined = '\n'.join(lines)
        for leaked in (SECRET_SLUG, SECRET_BODY, 'token', 'abc123', 'pub-1'):
            self.assertNotIn(leaked, joined)

    def test_worker_keeps_ticking_after_a_failure(self):
        calls, _ = self.run_worker([ValueError('a'), None, None], turns=3)
        self.assertEqual(len(calls), 3)

    def test_same_class_is_logged_once_per_minute_and_a_new_class_is_logged(self):
        _, lines = self.run_worker([ValueError('a'), ValueError('b'), ValueError('c'), KeyError('d'), ValueError('e')], turns=5)
        self.assertEqual([line.split(' queued')[0] for line in lines], [
            'studio-worker error class=ValueError',
            'studio-worker error class=KeyError',
            'studio-worker error class=ValueError',
        ])

    def test_unreadable_store_still_yields_the_class(self):
        def tick():
            self.store.close()
            raise OSError('gone')
        self.app.tick = tick
        self.app.stop = OneTurnStop(1)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.app.worker()
        self.assertEqual(err.getvalue().splitlines(), ['studio-worker error class=OSError queued=unreadable'])


if __name__ == '__main__':
    unittest.main()
