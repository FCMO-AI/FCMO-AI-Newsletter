"""Build a private snapshot with the production builder; never approximate HTML."""
import os
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from .storage import atomic, encoded
from .validation import LOCALES, locale

PREFIX = {'en': '', 'es-419': 'es/', 'zh-Hans': 'zh/'}

class RendererUnavailable(RuntimeError): pass

_L = r'(en|es-419|zh-Hans)'
_F = r'([A-Za-z0-9_-]{1,80})'
# Known builder refusals, said in plain words. Only these shapes cross the boundary:
# never the path in front of them, a traceback or any piece text.
_REASONS = [
    (r'numeric or URL token mismatch in ' + _L, lambda m: ('una cifra o un enlace de ' + m[0] + ' no coincide con el original', 'a number or link in ' + m[0] + ' does not match the original')),
    (r'citation references a missing source in ' + _L, lambda m: ('una cita de ' + m[0] + ' usa una fuente que no está en las fuentes del artículo', 'a citation in ' + m[0] + ' uses a source that is not in the article sources')),
    (r'footnote, citation or figure structure mismatch in ' + _L, lambda m: ('las notas, citas o figuras de ' + m[0] + ' no coinciden con el original', 'the notes, citations or figures in ' + m[0] + ' do not match the original')),
    (r'footnote id mismatch in ' + _L, lambda m: ('las notas al pie de ' + m[0] + ' no coinciden con el original', 'the footnotes in ' + m[0] + ' do not match the original')),
    (r'footnote reference/body mismatch in ' + _L, lambda m: ('hay una nota al pie sin referencia, o una referencia sin nota, en ' + m[0], 'a footnote has no reference, or a reference has no footnote, in ' + m[0])),
    (r'block id mismatch in ' + _L, lambda m: ('los párrafos de ' + m[0] + ' no coinciden con el original', 'the paragraphs in ' + m[0] + ' do not match the original')),
    (r'duplicate block id in ' + _L, lambda m: ('hay párrafos duplicados en ' + m[0], 'there are duplicate paragraphs in ' + m[0])),
    (r'ready ' + _L + r' has not been human-reviewed', lambda m: (m[0] + ' está lista pero nadie la ha revisado', m[0] + ' is marked ready but nobody has reviewed it')),
    (r'figure ' + _F + r' is missing credit or licence', lambda m: ('la figura ' + m[0] + ' no tiene crédito o licencia', 'figure ' + m[0] + ' has no credit or licence')),
    (r'figure ' + _F + r' is missing alt text or caption in ' + _L, lambda m: ('la figura ' + m[0] + ' no tiene texto alternativo o pie en ' + m[1], 'figure ' + m[0] + ' has no alt text or caption in ' + m[1])),
    (r'source locale must be ready before publication', lambda m: ('el idioma original aún no está marcado como listo', 'the original language is not marked ready yet')),
]

def builder_reason(stderr):
    """Short plain reason (es, en) for a known builder refusal, or None when unknown."""
    for line in reversed(stderr.splitlines()):
        found = re.fullmatch(r'ValueError: [^\r\n]*?: ([^\r\n:]{1,200})\r?', line)
        if not found: continue
        for pattern, say in _REASONS:
            match = re.fullmatch(pattern, found.group(1))
            if match: return say(match.groups())
    return None

class Preview:
    def __init__(self, store, repo, base='/FCMO-AI-Newsletter/'):
        self.store = store; self.repo = Path(repo).resolve(); self.base = '/' + base.strip('/') + '/'
        self.mutex = threading.RLock(); self.cache = {}
    def warm(self):
        try:
            run = subprocess.run(['python3', '-m', 'studio.server.render_preview', '--warm'], cwd=self.repo,
                                 env=self.renderer_environment(), capture_output=True, timeout=10)
        except subprocess.TimeoutExpired:
            raise RendererUnavailable('El renderer superó el límite de preparación de 10 segundos. Revisa la carga del host antes de iniciar Studio.') from None
        if run.returncode:
            raise RendererUnavailable('No se pudo preparar el renderer de producción. Revisa el generador antes de iniciar Studio.')
    @staticmethod
    def renderer_environment():
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'GHOST_', 'STUDIO_'))}
        env['GHOST_CONTENT_URL'] = ''; env['GHOST_CONTENT_API_KEY'] = ''
        return env
    def build(self, value, strict=False):
        with self.mutex:
            with self.store.mutex:
                rev = self.store.piece(value)['head_rev']; payload = self.store.payload(value)
                source_repo = getattr(self.store, 'public_root', self.repo)
                key = (value, rev, str(source_repo), hashlib.sha256(encoded(payload).encode()).hexdigest(), strict)
                if key in self.cache: return self.cache[key]
                root = self.store.data / 'previews'; root.mkdir(exist_ok=True, mode=0o700)
                workspace = Path(tempfile.mkdtemp(dir=root)); editorial = workspace / 'editorial'; directory = editorial / 'pieces' / value
                payload = self.store.payload(value)
                self.store._mirror(value)
                if 'issue' in payload:
                    editorial.mkdir(exist_ok=True)
                    source = self.store._worktree(value) / 'editorial'
                    shutil.copytree(source / 'issues', editorial / 'issues')
                    if (source_repo / 'editorial/pieces').is_dir(): shutil.copytree(source_repo / 'editorial/pieces', editorial / 'pieces')
                else:
                    shutil.copytree(self.store.directory(value), directory)
            output = workspace / 'publish'
            private = not strict and 'issue' not in payload and any(self.store.piece(value)['locale_states'][loc]['state'] in ('empty', 'drafting') for loc in LOCALES)
            if private: atomic(workspace / 'snapshot.json', encoded(payload).encode())
            env = self.renderer_environment()
            command = ['python3', '-m', 'studio.server.render_preview', '--stories', str(source_repo / 'site/data/stories.v2.json'),
                       '--status', str(source_repo / 'site/data/newsroom-status.json'), '--editorial', str(editorial), '--out', str(output), '--base', self.base]
            if private:
                command.extend(['--snapshot', str(workspace / 'snapshot.json')])
            run = subprocess.run(command, cwd=self.repo, env=env, capture_output=True, timeout=180)
            if run.returncode or any(not (output / PREFIX[loc] / ('cartas/ediciones' if 'issue' in payload else 'cartas') / value / 'index.html').is_file() for loc in LOCALES):
                shutil.rmtree(workspace)
                # Only this known numeric bound may cross the private diagnostic
                # boundary. Never return the builder's traceback or arbitrary text.
                budget = re.search(r'(?m)^ValueError: search index exceeds ([0-9]{1,10}) bytes for (en|es-419|zh-Hans): ([0-9]{1,10})\r?$', run.stderr.decode('utf-8', errors='replace'))
                if run.returncode and budget:
                    limit, loc, actual = budget.groups()
                    raise RendererUnavailable('La vista previa está bloqueada: el índice de búsqueda de ' + loc +
                                              ' ocupa ' + actual + ' bytes y supera el límite de ' + limit +
                                              ' bytes. Repara el generador de publicación antes de continuar.')
                reason = builder_reason(run.stderr.decode('utf-8', errors='replace')) if run.returncode else None
                if reason:
                    error = RendererUnavailable('No se pudo construir la vista previa: ' + reason[0] + '. Corrígelo y vuelve a intentar.')
                    error.reason = reason
                    raise error
                raise RendererUnavailable('No se pudo construir la vista previa con el renderer de producción. Revisa el generador de publicación antes de continuar.')
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
        out = self.build(value, strict=True)
        from tools.gates import personal_mailbox, internal_id, no_machine_paths, remote_script
        for module in (personal_mailbox, internal_id, no_machine_paths, remote_script): module.check(out)
        return True
