"""gh owns the host credential. Never extract, display or persist its token."""
import json
import os
from pathlib import Path
import subprocess
from .publishing import GitHub, Refused, UnknownEffect

NAMES = {'javier': 'Javier', 'matias': 'Matías'}
CREDENTIAL_ROOT = Path('/srv') / 'fcmo' / 'secrets' / 'studio'

class GitHubCLI(GitHub):
    def __init__(self, configs=None):
        super().__init__({})
        self.configs = {u: (configs or {}).get(u) or str(CREDENTIAL_ROOT / u) for u in NAMES}
    def environment(self, user):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_PUSH_TOKEN'))}
        env['GH_CONFIG_DIR'] = str(Path(self.configs[user]).expanduser())
        env['GH_PROMPT_DISABLED'] = '1'; env['GIT_TERMINAL_PROMPT'] = '0'
        return env
    def credential_status(self):
        statuses = []
        for user, name in NAMES.items():
            configured = (Path(self.configs[user]).expanduser() / 'hosts.yml').is_file()
            ok = False
            if configured:
                try:
                    run = subprocess.run(['gh', 'auth', 'status', '--hostname', 'github.com'],
                                         env=self.environment(user), capture_output=True, timeout=5)
                    ok = run.returncode == 0
                except (OSError, subprocess.SubprocessError): pass
            statuses.append({'user': user, 'ready': ok,
                             'plain_es': '' if ok else name + ' debe iniciar sesión en GitHub.',
                             'plain_en': '' if ok else name + ' needs to sign in to GitHub.'})
        return statuses
    def call(self, user, method, endpoint, body=None):
        command = ['gh', 'api', '--hostname', 'github.com', '--method', method, endpoint]
        if body is not None: command.extend(['--input', '-'])
        try:
            run = subprocess.run(command, input=None if body is None else json.dumps(body), env=self.environment(user), capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            if method == 'GET': raise Refused('Falta la credencial gh o no se pudo comprobar.') from None
            raise UnknownEffect('La respuesta de publicación no está confirmada.') from None
        if run.returncode:
            if method == 'GET' and 'HTTP 404' in run.stderr: return None
            if method != 'GET' and any(x in run.stderr for x in ('HTTP 500', 'HTTP 502', 'HTTP 503', 'HTTP 504', 'HTTP 408', 'HTTP 429')):
                raise UnknownEffect('La respuesta de publicación no está confirmada.')
            if method != 'GET' and not any('HTTP ' + str(code) in run.stderr for code in (400, 401, 403, 404, 405, 409, 422)):
                raise UnknownEffect('La respuesta de publicación no está confirmada.')
            raise Refused('GitHub rechazó la operación. Revisa la credencial gh y los permisos.')
        try: return json.loads(run.stdout) if run.stdout.strip() else {}
        except ValueError: raise UnknownEffect('La respuesta de publicación no está confirmada.') from None
    def request(self, user, method, suffix, body=None):
        return self.call(user, method, 'repos/' + self.repo + suffix, body)
    def identity(self, user):
        if not (Path(self.configs[user]).expanduser() / 'hosts.yml').is_file():
            raise Refused(NAMES[user] + ' debe iniciar sesión en GitHub.')
        result = self.call(user, 'GET', 'user')
        if not result or not result.get('login'): raise Refused('No se pudo comprobar la credencial gh.')
        return result['login']
    def preflight(self, user, reviewer):
        if self.identity(user) == self.identity(reviewer):
            raise Refused('La revisión requiere dos cuentas de GitHub distintas; configura la credencial de cada persona.')
    def push_environment(self, user, helper):
        return self.environment(user), ['-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential']
