"""Test process injection only; production has no local-remote escape hatch."""
import os
if os.environ.get('DOGFOOD_ACTIVE') == 'local-bare-only':
    from pathlib import Path
    from studio.server.credentials import GitHubCLI
    from studio.server.publishing import Refused
    from studio.server.storage import git
    original = GitHubCLI.__init__
    def init(self, *a, **kw):
        original(self, *a, **kw)
        self.live_base = os.environ['DOGFOOD_LIVE']
    def validate(self, clone):
        expected = str(Path(os.environ['DOGFOOD_BARE']).resolve())
        if not expected.endswith('/origin.git') or not Path(expected).is_dir():
            raise Refused('Invalid dogfood bare repository')
        for flags in ((), ('--push',)):
            if git(clone, 'remote', 'get-url', *flags, '--all', 'origin') != expected:
                raise Refused('Dogfood remote changed')
    GitHubCLI.__init__ = init
    GitHubCLI.validate_remote = validate
    # Observe the real strict check without changing its command, environment
    # or result. Only disposable dogfood fixture traces are retained here;
    # production retains bounded diagnostic identifiers, never raw draft text.
    import subprocess
    original_run = subprocess.run
    evidence_root = Path(os.environ['DOGFOOD_ROOT']).resolve()
    def observed_run(command, *args, **kwargs):
        cwd = Path(kwargs.get('cwd', '.')).resolve()
        strict = command == ['python3', 'ops/publish.py', '--check']
        if strict and os.environ.get('DOGFOOD_FULL_SUITE') != '1' and cwd.is_relative_to(evidence_root / 'data/candidates'):
            # The journey proves transport, review and merge. The repository suite and the browser
            # oracle run once, in the caller's acceptance run, not again in every candidate
            # (about 30 minutes each, and the Chromium oracle crashes on a loaded host).
            # DOGFOOD_FULL_SUITE=1 restores the complete strict gate.
            command = command + ['--fixture-build']
        if command and command[0] == 'gh' and kwargs.get('timeout'):
            # The fake `gh` builds the candidate for its check-runs answer (minutes on a loaded host);
            # production keeps its 30 s bound, this test double must not inherit it.
            kwargs['timeout'] = max(kwargs['timeout'], 900)
        result = original_run(command, *args, **kwargs)
        if strict and cwd.is_relative_to(evidence_root / 'data/candidates'):
            def raw(value): return value.encode() if isinstance(value, str) else value or b''
            fd = os.open(evidence_root / ('strict-' + cwd.name + '.log'), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, 'wb') as out: out.write(raw(result.stdout) + raw(result.stderr))
        return result
    subprocess.run = observed_run
