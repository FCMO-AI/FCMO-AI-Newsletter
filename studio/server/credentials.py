"""gh owns the host credential. Never extract, display or persist its token."""
import json
import os
from pathlib import Path
import subprocess
from .publishing import GitHub, Refused, UnknownEffect

class GitHubCLI(GitHub):
    def __init__(self, configs=None):
        super().__init__({})
        self.configs = configs or {}
    def environment(self, user):
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_PUSH_TOKEN'))}
        if self.configs.get(user): env['GH_CONFIG_DIR'] = str(Path(self.configs[user]).expanduser())
        env['GH_PROMPT_DISABLED'] = '1'; env['GIT_TERMINAL_PROMPT'] = '0'
        return env
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
        result = self.call(user, 'GET', 'user')
        if not result or not result.get('login'): raise Refused('No se pudo comprobar la credencial gh.')
        return result['login']
    def preflight(self, user, reviewer):
        if self.identity(user) == self.identity(reviewer):
            raise Refused('La revisión requiere dos cuentas de GitHub distintas; configura la credencial de cada persona.')
    def push_environment(self, user, helper):
        return self.environment(user), ['-c', 'credential.helper=', '-c', 'credential.helper=!gh auth git-credential']
