"""The dogfood journey must never leave its multi-gigabyte temporary tree behind."""
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.test_studio_storage import ROOT

DRIVER = '''
import os, sys, time
from pathlib import Path
from studio.dogfood import run
def fake(self):
    (self.root / 'big').write_bytes(b'x' * 1024)
    mode = os.environ['MODE']
    if mode == 'fail': raise AssertionError('journey failed')
    if mode == 'wait': print('READY', flush=True); time.sleep(60)
run.Journey.run = fake
run.main()
'''


class DogfoodCleanup(unittest.TestCase):
    def start(self, mode, tmp):
        env = dict(os.environ, TMPDIR=tmp, PYTHONPATH=str(ROOT), MODE=mode)
        return subprocess.Popen([sys.executable, '-c', DRIVER], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_failed_journey_removes_its_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.start('fail', tmp); run.communicate(timeout=60)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(os.listdir(tmp), [])

    def test_passing_journey_removes_its_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.start('ok', tmp); run.communicate(timeout=60)
            self.assertEqual(run.returncode, 0)
            self.assertEqual(os.listdir(tmp), [])

    def test_sigterm_removes_its_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.start('wait', tmp)
            self.assertEqual(run.stdout.readline().strip(), 'READY')
            self.assertEqual(len(os.listdir(tmp)), 1)
            run.send_signal(signal.SIGTERM); run.communicate(timeout=60)
            self.assertEqual(os.listdir(tmp), [])


if __name__ == '__main__': unittest.main()
