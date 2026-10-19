"""Release timeouts must stop the whole browser/server process family."""
import contextlib
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from ops import publish


def running(pid):
    try:
        # A terminated orphan may briefly await the host's init reaper.
        return Path(f'/proc/{pid}/stat').read_text().split()[2] != 'Z'
    except FileNotFoundError:
        return False


class PublishProcessTests(unittest.TestCase):
    def test_publish_refuses_timeout_without_running_later_gates(self):
        errors = io.StringIO()
        with patch.object(publish, 'run_command', side_effect=subprocess.TimeoutExpired('fixture', 1)) as run:
            with contextlib.redirect_stderr(errors):
                self.assertEqual(publish.main(['--check', '--tests-prevalidated']), 2)
        self.assertEqual(run.call_count, 1)
        self.assertIn('Publicación rechazada', errors.getvalue())
        self.assertIn('tools/build_ready_receipt.py', errors.getvalue())

    def test_outer_timeout_cleans_a_nested_browser_watchdog(self):
        with tempfile.TemporaryDirectory() as temporary:
            pid_file = Path(temporary) / 'browser.pid'
            browser = ('import os,pathlib,signal,sys,time; '
                       'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
                       'pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)')
            oracle = ('import sys; from tools.release_process import run_command; '
                      'run_command([sys.executable, "-c", sys.argv[1], sys.argv[2]], timeout=60)')
            try:
                started = time.monotonic()
                with self.assertRaises(subprocess.TimeoutExpired):
                    publish.run_command([sys.executable, '-c', oracle, browser, str(pid_file)],
                                        cwd=publish.ROOT, timeout=1, capture_output=True, text=True)
                self.assertLess(time.monotonic() - started, 8, 'nested cleanup exceeded its deadline')
                pid = int(pid_file.read_text())
                self.assertFalse(running(pid), 'outer watchdog leaked the nested browser group')
            finally:
                if pid_file.exists() and running(int(pid_file.read_text())):
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)

    def test_timeout_stops_descendants_and_reports_the_command(self):
        with tempfile.TemporaryDirectory() as temporary:
            pid_file = Path(temporary) / 'child.pid'
            code = '''import pathlib, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c',
    'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)'])
pathlib.Path(sys.argv[1]).write_text(str(child.pid))
time.sleep(60)
'''
            errors = io.StringIO()
            try:
                with contextlib.redirect_stderr(errors), self.assertRaises(subprocess.TimeoutExpired):
                    publish.run_command([sys.executable, '-c', code, str(pid_file)], timeout=1)
                pid = int(pid_file.read_text())
                deadline = time.monotonic() + 2
                while running(pid) and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertFalse(running(pid), 'browser descendant survived the command timeout')
                self.assertIn('Tiempo agotado', errors.getvalue())
            finally:
                if pid_file.exists() and running(int(pid_file.read_text())):
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)

    def test_success_also_cleans_up_an_abandoned_server(self):
        with tempfile.TemporaryDirectory() as temporary:
            pid_file = Path(temporary) / 'child.pid'
            code = '''import pathlib, subprocess, sys
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
pathlib.Path(sys.argv[1]).write_text(str(child.pid))
print('GATES PASS (14/14)', flush=True)
'''
            try:
                result = publish.run_command([sys.executable, '-c', code, str(pid_file)],
                                             timeout=3, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)
                self.assertIn('GATES PASS (14/14)', result.stdout)
                pid = int(pid_file.read_text())
                deadline = time.monotonic() + 2
                while running(pid) and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertFalse(running(pid), 'server survived a successful command')
            finally:
                if pid_file.exists() and running(int(pid_file.read_text())):
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
