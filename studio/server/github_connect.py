"""Short-lived GitHub device login, scoped to the authenticated Studio user."""
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
from .publishing import Refused

LOGIN_TIMEOUT = 15 * 60
CODE = re.compile(r'^! First copy your one-time code: ([A-Z0-9]{4}-[A-Z0-9]{4})\s*$')
DEVICE_URL = 'Open this URL to continue in your web browser: https://github.com/login/device'


class ConnectionInProgress(Refused):
    pass


class GitHubConnect:
    def __init__(self, github, timeout=LOGIN_TIMEOUT):
        self.github = github
        self.timeout = timeout
        self.lock = threading.Lock()
        self.sessions = {}

    @staticmethod
    def _safe(session):
        return {key: session[key] for key in ('user', 'state', 'code', 'url') if key in session}

    def status(self, user):
        with self.lock:
            session = self.sessions.get(user)
            return self._safe(session) if session else {'user': user, 'state': 'idle'}

    def start(self, user):
        with self.lock:
            current = self.sessions.get(user)
            if current and current['state'] in ('starting', 'waiting'):
                raise ConnectionInProgress('Ya hay una conexión de GitHub en curso.')
            session = {'user': user, 'state': 'starting', 'code': '', 'url': '',
                       'process': None, 'cancel': threading.Event(), 'done': threading.Event(),
                       'instructions': threading.Event()}
            self.sessions[user] = session
        thread = threading.Thread(target=self._run, args=(session,), daemon=True)
        session['thread'] = thread
        thread.start()
        # gh prints the device instructions immediately; wait briefly so the
        # first response can show them without making the browser poll blindly.
        session['instructions'].wait(1.5)
        return self.status(user)

    def cancel(self, user):
        with self.lock:
            session = self.sessions.get(user)
            if not session or session['state'] not in ('starting', 'waiting'):
                return self._safe(session) if session else {'user': user, 'state': 'idle'}
            session['cancel'].set()
            process = session.get('process')
            if process and process.poll() is None:
                process.terminate()
            session['code'] = ''
        session['done'].wait(2)
        with self.lock:
            if session['state'] in ('starting', 'waiting'):
                session['state'] = 'cancelled'
                session['code'] = ''
            return self._safe(session)

    def _run(self, session):
        user = session['user']
        instructions = session['instructions']
        reader = None
        try:
            config = Path(self.github.configs[user]).expanduser()
            created = not config.exists()
            config.mkdir(mode=0o700, parents=True, exist_ok=True)
            if created:
                config.chmod(0o700)
            env = self.github.environment(user)
            env.pop('GH_PROMPT_DISABLED', None)
            env['BROWSER'] = 'true'
            env.pop('GH_TOKEN', None)
            env.pop('GITHUB_TOKEN', None)
            process = subprocess.Popen(
                ['gh', 'auth', 'login', '--hostname', 'github.com', '--git-protocol', 'https', '--web'],
                env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
            session['process'] = process
            process.stdin.write('\n')
            process.stdin.close()
            lines = queue.Queue()

            def collect():
                try:
                    for line in process.stdout:
                        lines.put(line.rstrip('\r\n'))
                finally:
                    lines.put(None)
            reader = threading.Thread(target=collect, daemon=True)
            reader.start()
            deadline = time.monotonic() + self.timeout
            eof = False
            while not eof and time.monotonic() < deadline and not session['cancel'].is_set():
                try:
                    line = lines.get(timeout=min(.2, max(0, deadline - time.monotonic())))
                except queue.Empty:
                    if process.poll() is not None and lines.empty(): break
                    continue
                if line is None:
                    eof = True
                    continue
                code_match = CODE.fullmatch(line)
                if code_match:
                    session['code'] = code_match.group(1)
                    session['state'] = 'waiting'
                    instructions.set()
                elif line == DEVICE_URL:
                    session['url'] = 'https://github.com/login/device'
                    instructions.set()
            if session['cancel'].is_set():
                if process.poll() is None: process.terminate()
                session['state'] = 'cancelled'
            elif time.monotonic() >= deadline and process.poll() is None:
                process.terminate()
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
                session['state'] = 'timeout'
                session['code'] = ''
            else:
                returncode = process.wait(timeout=2)
                if returncode == 0 and next((item['ready'] for item in self.github.credential_status()
                                             if item['user'] == user), False):
                    session['state'] = 'ready'
                    session['code'] = ''
                elif session['state'] != 'cancelled':
                    session['state'] = 'error'
                    session['code'] = ''
        except (OSError, subprocess.SubprocessError):
            session['state'] = 'error'
            session['code'] = ''
        finally:
            process = session.get('process')
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try: process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
                if reader is not None: reader.join(timeout=1)
                if process.stdout and (reader is None or not reader.is_alive()):
                    process.stdout.close()
            instructions.set()
            session['done'].set()
