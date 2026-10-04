"""Build a private snapshot with the production builder; never approximate HTML."""
import os
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from .storage import atomic, encoded
from .validation import LOCALES, locale

PREFIX = {'en': '', 'es-419': 'es/', 'zh-Hans': 'zh/'}

class RendererUnavailable(RuntimeError): pass

class Preview:
    def __init__(self, store, repo, base='/FCMO-AI-Newsletter/'):
        self.store = store; self.repo = Path(repo).resolve(); self.base = '/' + base.strip('/') + '/'
        self.mutex = threading.RLock(); self.cache = {}
    def build(self, value):
        with self.mutex:
            with self.store.mutex:
                rev = self.store.piece(value)['head_rev']; payload = self.store.payload(value)
                key = (value, rev, hashlib.sha256(encoded(payload).encode()).hexdigest())
                if key in self.cache: return self.cache[key]
                root = self.store.data / 'previews'; root.mkdir(exist_ok=True, mode=0o700)
                workspace = Path(tempfile.mkdtemp(dir=root)); editorial = workspace / 'editorial'; directory = editorial / 'pieces' / value
                payload = self.store.payload(value)
                self.store._mirror(value)
                if 'issue' in payload:
                    editorial.mkdir(exist_ok=True)
                    source = self.store._worktree(value) / 'editorial'
                    shutil.copytree(source / 'issues', editorial / 'issues')
                    if (self.store.data / 'clone/editorial/pieces').is_dir(): shutil.copytree(self.store.data / 'clone/editorial/pieces', editorial / 'pieces')
                else:
                    shutil.copytree(self.store.directory(value), directory)
            output = workspace / 'publish'
            env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN_', 'GHOST_', 'STUDIO_SESSION_'))}
            env['GHOST_CONTENT_URL'] = ''; env['GHOST_CONTENT_API_KEY'] = ''
            command = ['python3', str(self.repo / 'tools/paper/build.py'), '--stories', str(self.repo / 'site/data/stories.v2.json'),
                       '--status', str(self.repo / 'site/data/newsroom-status.json'), '--editorial', str(editorial), '--out', str(output), '--base', self.base]
            run = subprocess.run(command, cwd=self.repo, env=env, capture_output=True, timeout=180)
            if run.returncode or any(not (output / PREFIX[loc] / ('cartas/ediciones' if 'issue' in payload else 'cartas') / value / 'index.html').is_file() for loc in LOCALES):
                shutil.rmtree(workspace)
                raise RendererUnavailable('La vista previa espera la integración del formato de ensayos con el sitio.')
            self.cache[key] = output
            older = [k for k in self.cache if k[0] == value and k != key]
            for old in older[:-1]:
                previous = self.cache.pop(old)
                shutil.rmtree(previous.parent)
            return output
    def page(self, value, loc):
        locale(loc); output = self.build(value)
        return (output / PREFIX[loc] / ('cartas/ediciones' if 'issue' in self.store.payload(value) else 'cartas') / value / 'index.html').read_bytes()
    def privacy(self, value):
        out = self.build(value)
        from tools.gates import personal_mailbox, internal_id, no_machine_paths, remote_script
        for module in (personal_mailbox, internal_id, no_machine_paths, remote_script): module.check(out)
        return True
