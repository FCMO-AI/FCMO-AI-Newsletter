"""Durable two-person publication with intent-before-effect reconciliation."""
from html.parser import HTMLParser
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import threading
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .messages import PROGRESS
from .storage import NAMES, atomic, encoded, git, utc
from .validation import LOCALES
from .preview import PREFIX

class UnknownEffect(Exception): pass
class Refused(Exception): pass
class Denied(Refused):
    """A resume only the reviewer may make."""
    status = 403
class NeedsConfirm(Refused):
    """An integrity resume without confirm=true."""
    status = 400
HALT_REASONS = ('infra', 'effect', 'foreign_merge', 'merge_outside')
class Infra(Refused):
    """A transient/infrastructure failure: retried without a new human approval."""
    status = 503
class ForeignMerge(Exception):
    """Merged outside Studio with other bytes than the approved head: never published, halted for a person."""

def check_merged_head(pr, head):
    if pr.get('merged') and (pr.get('head') or {}).get('sha') != head: raise ForeignMerge()

def budget(name, default):
    # Seconds; tunable per host without code changes.
    try: return max(1, int(os.environ.get('STUDIO_' + name + '_BUDGET_S', default)))
    except ValueError: return default
GATE_BUDGET, DEPLOY_BUDGET, LIVE_BUDGET = ('GATE', 3600), ('DEPLOY', 4*3600), ('LIVE', 6*3600)
EFFECT_BUDGET = ('EFFECT', 300)  # how long an unconfirmed write is only observed before it is repeated
INFRA_RETRIES = 3
POST_MERGE = ('merged', 'deployed', 'deployed_unverified')
PROTECTION_MODES = ('github', 'studio')
def protection_mode():
    mode = os.environ.get('STUDIO_PROTECTION_MODE', 'github') or 'github'
    if mode not in PROTECTION_MODES: raise Refused('El modo de protección de publicación no es válido.')
    return mode

PUBLIC_REPO = 'FCMO-AI/FCMO-AI-Newsletter'
def publish_repo(explicit=None):
    """Where publications go. An override exists only for a rehearsal, and a rehearsal never goes live on the public repo."""
    override = os.environ.get('STUDIO_PUBLISH_REPO', '').strip(); rehearsal = os.environ.get('STUDIO_REHEARSAL') == '1'
    if override and not rehearsal: raise Refused('El repositorio de publicación sólo puede cambiarse en un ensayo.')
    repo = explicit or override or PUBLIC_REPO
    if rehearsal and repo == PUBLIC_REPO and os.environ.get('STUDIO_LIVE_ENABLED') == '1':
        raise Refused('Un ensayo no puede publicar de verdad en el repositorio público.')
    return repo

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class GitHub:
    def __init__(self, tokens, api='https://api.github.com', repo=None, live_base='https://fcmo-ai.github.io/FCMO-AI-Newsletter/'):
        self.tokens = tokens; self.api = api.rstrip('/'); self.repo = publish_repo(repo); self.live_base = live_base.rstrip('/') + '/'
        self.opener = build_opener(NoRedirect())
    def request(self, user, method, suffix, body=None):
        token = self.tokens.get(user)
        if not token: raise Refused('Falta la credencial personal para publicar.')
        req = Request(self.api + '/repos/' + self.repo + suffix, method=method,
                      data=None if body is None else json.dumps(body).encode(),
                      headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with self.opener.open(req, timeout=15) as response:
                raw = response.read(8*1024*1024)
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            if exc.code == 404 and method == 'GET': return None
            # A server error on a write may occur after committing it.
            if exc.code >= 500 or exc.code in (408, 429): raise UnknownEffect('La respuesta de publicación no está confirmada.') from None
            raise Refused('GitHub no permitió publicar. Revisa los permisos y las protecciones.') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise UnknownEffect('La respuesta de publicación no está confirmada.') from None
    def branch(self, user, branch):
        result = self.request(user, 'GET', '/git/ref/heads/' + quote(branch, safe='/'))
        return result['object']['sha'] if result else None
    def find_pr(self, user, branch):
        # all states: an acknowledged-but-lost merge still has a discoverable PR.
        rows = self.request(user, 'GET', '/pulls?' + urlencode({'state': 'all', 'head': self.repo.split('/')[0] + ':' + branch, 'per_page': 100}))
        return next((r for r in rows or [] if r['head']['ref'] == branch), None)
    def pr(self, user, number): return self.request(user, 'GET', '/pulls/' + str(number))
    def open_pr(self, user, branch, title, body):
        return self.request(user, 'POST', '/pulls', {'head': branch, 'base': 'main', 'title': title, 'body': body})
    def identity(self, user):
        token = self.tokens.get(user)
        if not token: raise Refused('Falta la credencial personal para publicar.')
        req = Request(self.api + '/user', headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        try:
            with self.opener.open(req, timeout=15) as res: return json.load(res)['login']
        except (OSError, ValueError, KeyError): raise Refused('No se pudo confirmar la credencial de publicación.') from None
    def account(self, user):
        # GitHubCLI (credentials.py) provides call(); the token client does not.
        if hasattr(self, 'call'): return self.call(user, 'GET', 'user') or {}
        token = self.tokens.get(user)
        if not token: raise Refused('Falta la credencial personal para publicar.')
        req = Request(self.api + '/user', headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        try:
            with self.opener.open(req, timeout=15) as res: return json.load(res)
        except (OSError, ValueError): raise Infra('No se pudo confirmar la cuenta de publicación.') from None
    def noreply_email(self, user):
        # The public history must carry the author's own GitHub noreply address.
        account = self.account(user); login = account.get('login')
        if not isinstance(login, str) or not login: raise Refused('No se pudo confirmar la cuenta de publicación.')
        ident = account.get('id')
        return (str(ident) + '+' if isinstance(ident, int) else '') + login + '@users.noreply.github.com'
    def preflight(self, user, reviewer):
        if not all(self.tokens.get(u) for u in (user, reviewer)):
            raise Refused('Falta la credencial personal para publicar.')
        if self.identity(user) == self.identity(reviewer):
            raise Refused('La revisión requiere dos cuentas de GitHub distintas.')
    def validate_remote(self, clone):
        expected = {'https://github.com/' + self.repo, 'https://github.com/' + self.repo + '.git'}
        if len(fetch_urls := git(clone, 'remote', 'get-url', '--all', 'origin').splitlines()) != 1 or len(push_urls := git(clone, 'remote', 'get-url', '--push', '--all', 'origin').splitlines()) != 1 or fetch_urls[0] not in expected or push_urls[0] not in expected:
            raise Refused('El destino de publicación no es el repositorio público autorizado.')
    def push_environment(self, user, helper):
        token = self.tokens.get(user)
        if not token: raise Refused('Falta la credencial personal para publicar.')
        atomic(helper, b'#!/usr/bin/env python3\nimport os,sys\nprint("x-access-token" if "Username" in sys.argv[1] else os.environ["STUDIO_PUSH_TOKEN"])\n')
        os.chmod(helper, 0o700)
        return dict(os.environ, GIT_ASKPASS=str(helper), GIT_TERMINAL_PROMPT='0', STUDIO_PUSH_TOKEN=token), ['-c', 'credential.helper=']
    def reviewed(self, user, number, head):
        rows = self.request(user, 'GET', '/pulls/' + str(number) + '/reviews?per_page=100') or []
        login = self.identity(user)
        return any(r.get('state') == 'APPROVED' and r.get('commit_id') == head and r.get('user', {}).get('login') == login for r in rows)
    def review(self, user, number, head):
        return self.request(user, 'POST', '/pulls/' + str(number) + '/reviews', {'event': 'APPROVE', 'commit_id': head, 'body': 'Leí y aprobé esta publicación en FCMO Studio.'})
    def checks(self, user, head):
        result = self.request(user, 'GET', '/commits/' + head + '/check-runs?per_page=100') or {}
        rows = [r for r in result.get('check_runs', []) if r.get('name') == 'publish-gate']
        if not rows: return 'pending'
        newest = max(rows, key=lambda r: r.get('id', 0))
        if newest.get('status') != 'completed': return 'pending'
        if newest.get('conclusion') in ('cancelled', 'timed_out', 'stale'): return 'cancelled'
        return 'green' if newest.get('conclusion') == 'success' else 'red'
    def protected(self, user):
        rules = self.request(user, 'GET', '/rules/branches/main') or []
        pulls = [r.get('parameters', {}) for r in rules if r.get('type') == 'pull_request']
        checks = [r.get('parameters', {}) for r in rules if r.get('type') == 'required_status_checks']
        good_pull = any(p.get('required_approving_review_count', 0) >= 1 and p.get('require_code_owner_review') and p.get('require_last_push_approval') and p.get('dismiss_stale_reviews_on_push') for p in pulls)
        # No "strict" (up-to-date) requirement: the confined-diff and merge-diff checks replace base equality,
        # and a ruleset that still has it is served by replaying the approved bytes on the new main.
        good_check = any(any(c.get('context') == 'publish-gate' for c in p.get('required_status_checks', [])) for p in checks)
        if not (good_pull and good_check): return False
        source_ids = {r.get('ruleset_id') for r in rules if r.get('type') in ('pull_request', 'required_status_checks')}
        if not source_ids or None in source_ids: return False
        for ident in source_ids:
            detail = self.request(user, 'GET', '/rulesets/' + str(ident)) or {}
            # GitHub hides bypass_actors without ruleset write visibility.
            # Missing metadata is not evidence of an empty exception list.
            from .protection import safe_bypass
            if detail.get('enforcement') != 'active' or not safe_bypass(detail.get('bypass_actors')): return False
        return True
    def merge(self, user, number, head):
        result = self.request(user, 'PUT', '/pulls/' + str(number) + '/merge', {'sha': head, 'merge_method': 'merge'})
        if not result.get('merged'): raise Refused('GitHub no permitió publicar. Revisa la revisión y las comprobaciones.')
        return result
    def pages(self, user, merge):
        # Deployed = a successful pages.yml run whose commit is the merge or descends from it,
        # whichever event started it. Cancelled or failed runs are simply "not yet": a later
        # run (pages.yml keeps one pending run per group) deploys the merge.
        result = self.request(user, 'GET', '/actions/workflows/pages.yml/runs?' + urlencode({'status': 'success', 'per_page': 30})) or {}
        runs = sorted((r for r in result.get('workflow_runs', []) if r.get('conclusion') == 'success' and r.get('head_sha')), key=lambda r: r.get('id', 0), reverse=True)
        for run in runs:
            if run['head_sha'] == merge: return run
        for run in runs[:10]:
            cmp = self.request(user, 'GET', '/compare/' + merge + '...' + run['head_sha']) or {}
            if cmp.get('status') in ('ahead', 'identical'): return run
        return None
    def live(self, slug, ident, kind='essay'):
        urls = []
        for loc in LOCALES:
            target = self.live_base + PREFIX[loc] + ('cartas/ediciones/' if kind == 'issue' else 'cartas/') + slug + '/'
            try:
                with self.opener.open(Request(target, headers={'Cache-Control': 'no-cache'}), timeout=15) as res:
                    content = res.read(8*1024*1024).decode('utf-8'); status = res.status
                parser = PieceHTML(ident); parser.feed(content)
                if status != 200 or not parser.found: return None
            except (OSError, ValueError): return None
            urls.append({'locale': loc, 'url': target})
        return urls
    def email_state(self, user):
        # Independent read-only branch: no main snapshot refresh or redeploy.
        from tools.email_intent import LIMIT
        try:
            doc = self.request(user, 'GET', '/contents/dispatch.json?ref=email-dispatch-state')
            if not isinstance(doc, dict) or doc.get('encoding') != 'base64': return None
            encoded_state = doc.get('content')
            if not isinstance(encoded_state, str) or len(encoded_state) > 2 * LIMIT: return None
            raw = base64.b64decode(encoded_state)
            if len(raw) > LIMIT: return None
            return json.loads(raw)
        except (Refused, UnknownEffect, OSError, TypeError, ValueError): return None

    def close_pr(self, user, number): return self.request(user, 'PATCH', '/pulls/' + str(number), {'state': 'closed'})
    def rollback(self, user):
        return self.request(user, 'POST', '/actions/workflows/pages.yml/dispatches', {'ref': 'main', 'inputs': {'operation': 'rollback'}})

class PieceHTML(HTMLParser):
    def __init__(self, ident): super().__init__(); self.ident = ident; self.found = False
    def handle_starttag(self, tag, attrs):
        if tag == 'article' and dict(attrs).get('data-piece-id') == self.ident: self.found = True

class Workspace:
    def __init__(self, store, github, check_command=None):
        self.store = store; self.github = github; self.check_command = check_command or ['python3', 'ops/publish.py', '--check']; self.production_check = check_command is None
    def prepare(self, pub):
        data = pub['payload']; clone = self.store.data / 'clone'; branch = data['branch']
        if not branch.startswith('studio/'): raise Refused('La rama de publicación no es válida.')
        # Fresh remote base, never a local draft ancestor.
        if self.production_check:
            self.github.validate_remote(clone)
        git(clone, 'fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
        base_sha = git(clone, 'rev-parse', 'refs/remotes/origin/main')
        if self.production_check:
            try:
                git(clone, 'fetch', 'origin', '+refs/tags/lkg:refs/tags/lkg')
                git(clone, 'rev-parse', '--verify', 'refs/tags/lkg^{commit}')
            except RuntimeError: raise Refused('Falta la versión LKG comprobada; no se puede publicar.') from None
        target = self.store.data / 'candidates' / pub['id']; target.parent.mkdir(exist_ok=True, mode=0o700)
        if target.exists():
            git(clone, 'worktree', 'remove', '--force', str(target)); git(clone, 'branch', '-D', branch)
        git(clone, 'worktree', 'add', '-qb', branch, str(target), 'refs/remotes/origin/main')
        is_issue = pub['kind'] == 'issue'
        rel = Path('editorial/issues') / (pub['slug'] + '.json') if is_issue else Path('editorial/pieces') / pub['slug']
        destination = target / rel
        if is_issue:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.store._worktree(pub['slug']) / rel, destination)
        else:
            source = self.store.directory(pub['slug'])
            allowed = {'piece.json', 'sources.json', 'figures.json', 'provenance.json'} | {'doc.' + loc + '.json' for loc in LOCALES}
            for file in source.rglob('*'):
                relfile = file.relative_to(source).as_posix()
                if file.is_symlink() or (file.is_file() and relfile not in allowed and not (relfile.startswith('figures/') and '/' not in relfile[8:] and file.suffix == '.webp')):
                    raise Refused('La publicación contiene un archivo no permitido.')
            if destination.exists(): shutil.rmtree(destination)
            shutil.copytree(source, destination)
        git(target, 'add', '--', str(rel))
        # Local-only placeholder: the author's own GitHub noreply address is set just before the push (needs the network).
        git(target, '-c', 'user.name=' + data['author_name'], '-c', 'user.email=noreply@users.noreply.github.com', 'commit', '-qm', 'Publish ' + data['title'])
        changed = git(target, 'diff', '--name-only', 'refs/remotes/origin/main', 'HEAD').splitlines()
        if not changed or any(path != str(rel) if is_issue else not path.startswith(str(rel) + '/') for path in changed): raise Refused('La publicación contiene cambios fuera del artículo.')
        # Do not follow a draft symlink into private state.
        if any(p.is_symlink() for p in destination.rglob('*')): raise Refused('La publicación contiene un archivo no permitido.')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_', 'GHOST_', 'DOGFOOD_'))}
        run = subprocess.run(self.check_command, cwd=target, env=env, capture_output=True, timeout=1800)
        if run.returncode:
            # Keep bounded identifiers for operator diagnosis, never document
            # excerpts, tokens, raw test traces or host paths in the audit/UI.
            import re
            output = (run.stdout + run.stderr).decode('utf-8', errors='replace')
            failures = re.findall(r'^(?:FAIL|ERROR): ([a-zA-Z0-9_]+) \(([a-zA-Z0-9_.]+)\)', output, re.M)[:100]
            gates = re.findall(r'^([A-Z_]+) FAIL', output, re.M)[:30]
            diagnostics = self.store.data / 'check-results'
            diagnostics.mkdir(exist_ok=True, mode=0o700)
            atomic(diagnostics / (pub['id'] + '.json'), encoded({'exit_code': run.returncode, 'failed_tests': failures, 'failed_gates': gates}).encode())
            raise Refused('Las comprobaciones locales fallaron. Revisa el artículo; nada se hizo público.')
        if git(target, 'status', '--porcelain', '--untracked-files=no'):
            raise Refused('Las comprobaciones modificaron la versión aprobada. Pide una nueva revisión.')
        head = git(target, 'rev-parse', 'HEAD')
        return {'head_sha': head, 'base_sha': base_sha, 'candidate': str(target), 'rel': rel.as_posix(), 'content_tree': git(target, 'rev-parse', 'HEAD:' + rel.as_posix())}
    def verify_base(self, pub):
        data = pub['payload']
        current = git(Path(data['candidate']), 'ls-remote', 'origin', 'refs/heads/main').split()
        if not current or current[0] != data.get('base_sha'):
            raise Refused('La base de publicación cambió. Pide una nueva revisión antes de publicar.')
    @staticmethod
    def piece_path(pub):
        return ('editorial/issues/' + pub['slug'] + '.json') if pub['kind'] == 'issue' else ('editorial/pieces/' + pub['slug'])
    def verify_confined(self, pub):
        """The approved bytes, and only them, differ from main. The base may have moved."""
        data = pub['payload']; target = Path(data['candidate']); rel = data.get('rel') or self.piece_path(pub)
        if git(target, 'rev-parse', 'HEAD') != data['head_sha']: raise Refused('La versión aprobada cambió antes de publicar.')
        try: git(target, 'fetch', 'origin', '+refs/heads/main:refs/remotes/origin/main')
        except RuntimeError: raise Infra('No se pudo consultar la base pública. Se reintentará.') from None
        changed = git(target, 'diff', '--name-only', git(target, 'merge-base', 'refs/remotes/origin/main', 'HEAD'), 'HEAD').splitlines()
        if not changed or any(path != rel and not path.startswith(rel + '/') for path in changed): raise Refused('La publicación contiene cambios fuera del artículo.')
        if data.get('content_tree') and git(target, 'rev-parse', 'HEAD:' + rel) != data['content_tree']: raise Refused('La versión aprobada cambió antes de publicar.')
    def recreate(self, pub):
        """Replay the approved bytes onto the current main (no new approval: the content is what was approved)."""
        data = pub['payload']; target = Path(data['candidate']); rel = data.get('rel') or self.piece_path(pub)
        old = data['head_sha']
        git(target, 'reset', '-q', '--hard', old)  # a crash after the commit but before the write must not strand it
        self.verify_confined(pub)
        git(target, 'reset', '-q', '--hard', 'refs/remotes/origin/main')
        git(target, 'rm', '-rq', '--ignore-unmatch', '--', rel)
        git(target, 'checkout', old, '--', rel)
        email = self.github.noreply_email(data['author'])
        git(target, '-c', 'user.name=' + data['author_name'], '-c', 'user.email=' + email, 'commit', '-qm', 'Publish ' + data['title'])
        new = git(target, 'rev-parse', 'HEAD')
        if git(target, 'rev-parse', 'HEAD:' + rel) != git(target, 'rev-parse', old + ':' + rel): raise Refused('La versión aprobada cambió antes de publicar.')
        return {'head_sha': new, 'base_sha': git(target, 'rev-parse', 'refs/remotes/origin/main'), 'previous_head': old, 'identity_set': True}
    def refresh(self, pub):
        """Before the first push: set the author's own noreply identity and, if main moved, replay the approved bytes onto it."""
        data = pub['payload']; target = Path(data['candidate']); changes = {}
        if not data.get('identity_set'): git(target, 'reset', '-q', '--hard', data['head_sha'])  # undo an amend whose write was lost
        self.verify_confined(pub)
        if not data.get('identity_set'):
            email = self.github.noreply_email(data['author'])
            git(target, '-c', 'user.name=' + data['author_name'], '-c', 'user.email=' + email, 'commit', '-q', '--amend', '--no-edit', '--reset-author')
            changes = {'head_sha': git(target, 'rev-parse', 'HEAD'), 'identity_set': True}; data.update(changes)
        if git(target, 'rev-parse', 'refs/remotes/origin/main') != data['base_sha']: changes.update(self.recreate(pub))
        return changes or None
    def repush(self, pub, old):
        data = pub['payload']; ref = 'refs/heads/' + data['branch']
        self.github.validate_remote(self.store.data / 'clone')
        env, options = self.github.push_environment(data['author'], self.store.data / 'askpass.py')
        run = subprocess.run(['git', '-C', data['candidate'], *options, 'push', '--force-with-lease=' + ref + ':' + old, 'origin', data['head_sha'] + ':' + ref], env=env, capture_output=True, timeout=120)
        if run.returncode: raise UnknownEffect('No se pudo confirmar el envío. Se comprobará antes de repetirlo.')
    def push(self, pub):
        data = pub['payload']; branch = data['branch']
        self.github.validate_remote(self.store.data / 'clone')
        self.github.preflight(data['author'], data['reviewer'])
        if not branch.startswith('studio/') or data['head_sha'] != git(Path(data['candidate']), 'rev-parse', 'HEAD'):
            raise Refused('La versión aprobada cambió antes de publicar.')
        self.verify_confined(pub)
        env, options = self.github.push_environment(data['author'], self.store.data / 'askpass.py')
        # Refuse to overwrite a concurrently created branch, even in dry-run.
        ref = 'refs/heads/' + branch
        run = subprocess.run(['git', '-C', data['candidate'], *options, 'push', '--force-with-lease=' + ref + ':', 'origin', data['head_sha'] + ':' + ref], env=env, capture_output=True, timeout=120)
        if run.returncode: raise UnknownEffect('No se pudo confirmar el envío. Se comprobará antes de repetirlo.')

STATES = ('approved', 'candidate', 'pushed', 'pr_open', 'reviewed', 'checks_green', 'merged', 'deployed', 'deployed_unverified', 'published')

class Publisher:
    def __init__(self, store, github, workspace, checker):
        self.store = store; self.github = github; self.workspace = workspace; self.checker = checker
        self.mutex = threading.RLock()
    def _write(self, pub, state=None, error=None):
        with self.store.mutex:
            self._write_locked(pub, state, error)
    def _write_locked(self, pub, state=None, error=None):
        if state:
            pub['state'] = state
            pub['payload'].pop('infra_retries', None); pub['payload'].pop('retry_after', None)
            entry = {'state': state, 'at': utc(), 'plain_es': PROGRESS[state][0], 'plain_en': PROGRESS[state][1]}
            if pub['payload'].get('protection_mode'): entry['protection_mode'] = pub['payload']['protection_mode']
            pub['payload'].setdefault('timeline', []).append(entry)
        if error is not None: pub['error_plain'] = error
        data = pub['payload']
        self.store.db.execute('UPDATE publications SET state=?,pr_number=?,head_sha=?,merge_sha=?,pages_run=?,live_checked_at=?,error_plain=?,payload_json=? WHERE id=?',
            (pub['state'], data.get('pr_number'), data.get('head_sha'), data.get('merge_sha'), data.get('pages_run'), data.get('live_checked_at'), pub.get('error_plain', ''), encoded(data), pub['id']))
        if state == 'published':
            piece_status = 'withdrawn' if self.store.payload(pub['slug'])['piece']['status'] == 'withdrawn' else 'published'
            self.store.db.execute('UPDATE pieces SET state=? WHERE slug=?', (piece_status, pub['slug']))
            self.store.audit(data['author'], 'live_verified', pub['slug'], {'publication_id': pub['id']})
        elif state == 'failed':
            self.store.db.execute('UPDATE pieces SET state=? WHERE slug=?', ('changes_requested', pub['slug']))
        self.store.db.commit()
    def get(self, value):
        # A committed snapshot needs only the database lock. The transition
        # lock may be held by minutes of git/build/CI work; readers must still
        # be able to observe the last committed progress while that runs.
        with self.store.mutex:
            self.store._row(value)
            row = self.store.db.execute('SELECT * FROM publications WHERE slug=? ORDER BY rowid DESC LIMIT 1', (value,)).fetchone()
            if not row: return {'state': self.store.piece(value)['state'], 'timeline': []}
            result = dict(row); result['payload'] = json.loads(result.pop('payload_json'))
            result['approved_at'] = result['payload'].get('approved_at')  # None for publications approved before this field
            return result
    def request(self, value, user):
        piece = self.store.piece(value)
        if piece['kind'] != 'issue' and piece['source_locale'] in ('en', 'es-419') and self.store.payload(value)['piece']['status'] != 'withdrawn':
            from studio.translation import prepare, TranslationError
            try: prepare(self.store, value, user)
            except TranslationError as exc: raise Refused(str(exc)) from None
        initial_rev = self.store.piece(value)['head_rev']
        checks = self.checker(value)
        with self.mutex:
            piece = self.store.piece(value)
            if piece['author'] != user or piece['state'] not in ('draft', 'changes_requested', 'amending'): raise Refused('Solo el autor puede pedir revisión del borrador.')
            if piece['head_rev'] != initial_rev: raise Refused('El artículo cambió durante las comprobaciones; vuelve a pedir revisión.')
            if not checks or any(not x['ok'] and not x.get('approval_satisfiable') for x in checks): raise Refused('Completa las comprobaciones antes de pedir revisión.')
            self.store.checkpoint(value, user, 'Para revisión')
            reviewer = 'matias' if user == 'javier' else 'javier'
            old = self.get(value)
            # Close a failed old PR before the next public candidate; ambiguous
            # close is reconciled by observing it before accepting a new review.
            if old.get('pr_number'):
                pr = self.github.pr(user, old['pr_number'])
                if pr and pr.get('state') == 'open':
                    self.github.close_pr(user, old['pr_number'])
                    observed = self.github.pr(user, old['pr_number'])
                    if not observed or observed.get('state') != 'closed': raise UnknownEffect('No se confirmó el cierre de la revisión anterior.')
            with self.store.mutex:
                current = self.store.piece(value)
                if current['head_rev'] != initial_rev or current['state'] != piece['state']:
                    raise Refused('El artículo cambió durante las comprobaciones; vuelve a pedir revisión.')
                ident = __import__('secrets').token_hex(12)
                self.store.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)', (ident, value, piece['head_rev'], user, reviewer, 'requested', utc(), ''))
                self.store.db.execute('UPDATE pieces SET state=? WHERE slug=?', ('in_review', value)); self.store.audit(user, 'request_review', value); self.store.db.commit()
            return {'state': 'in_review', 'reviewer': reviewer}
    def approve(self, value, user, note=''):
        with self.mutex, self.store.mutex:
            piece = self.store.piece(value)
            review = self.store.db.execute('SELECT * FROM reviews WHERE slug=? ORDER BY rowid DESC LIMIT 1', (value,)).fetchone()
            if piece['state'] != 'in_review' or not review or review['reviewer'] != user or piece['author'] == user:
                raise Refused('La otra persona debe revisar y aprobar la publicación.')
            if piece['head_rev'] != review['rev']: raise Refused('El artículo cambió; pide una nueva revisión.')
            ident = __import__('secrets').token_hex(12); payload = self.store.payload(value)
            stamp = utc(); payload['piece']['updated_at'] = stamp
            if 'issue' not in payload and payload['piece']['status'] != 'withdrawn':
                from studio.translation import validate_translation, TranslationError, machine_reviewed
                source = payload['piece']['source_locale']
                if payload.get('translation_error'): raise Refused(payload['translation_error'])
                states = self.store.piece(value)['locale_states']
                for loc in LOCALES:
                    if payload['piece']['locales'][loc] != 'ready':
                        if piece['author'] == 'javier' and source == 'es-419': raise Refused('Completa inglés, español y chino antes de publicar.')
                        continue
                    try: validate_translation(payload['docs'][source], payload['docs'][loc], loc)
                    except TranslationError as exc: raise Refused(str(exc)) from None
                    prior = payload['provenance'].get(loc, {})
                    if loc != source:
                        # Publication approval is not a claim of fluency in another language.
                        if not machine_reviewed(prior, payload['docs'][source], payload['docs'][loc], payload['figures']) and not (prior.get('human_reviewed') is True and prior.get('reviewer')):
                            raise Refused('La traducción requiere comprobación automática de fidelidad o revisión humana explícita del idioma.')
                        continue
                    payload['provenance'][loc] = {**prior, 'origin': prior.get('origin', 'human_authored' if loc == source else 'human_translated'),
                        'human_reviewed': True, 'reviewer': NAMES[user], 'at': stamp, 'source_locale': source}
                    states[loc] = {**states[loc], 'human_reviewed': True, 'by': user, 'at': stamp}
                self.store._put(value, payload, user, bump=False, states=states)
            if not self.store.db.execute('SELECT 1 FROM publications WHERE slug=? AND state=?', (value, 'published')).fetchone(): payload['piece']['first_published_at'] = stamp
            # Freeze timestamps before candidate check and public push.
            self.store._put(value, payload, piece['author'], bump=False)
            data = {'author': piece['author'], 'author_name': payload['piece']['authors'][0]['name'], 'reviewer': user,
                    'approved_rev': piece['head_rev'], 'approved_at': utc(), 'branch': 'studio/' + value + '-' + ident[:8], 'piece_id': payload['piece']['id'],
                    'title': piece['title'], 'created': self.store.clock(), 'timeline': [], 'urls': [],
                    'languages': payload['piece']['locales'], 'provenance': payload['provenance'], 'distribution': payload['piece'].get('distribution', {'email': False})}
            self.store.db.execute('INSERT INTO publications(id,slug,kind,state,error_plain,payload_json) VALUES(?,?,?,?,?,?)', (ident, value, piece['kind'], 'approved', '', encoded(data)))
            self.store.db.execute('UPDATE reviews SET state=?,at=?,note=? WHERE id=?', ('approved', utc(), str(note)[:10000], review['id']))
            self.store.db.execute('UPDATE pieces SET state=? WHERE slug=?', ('publishing', value)); self.store.audit(user, 'approve', value); self.store.db.commit()
            return self.get(value)
    def changes(self, value, user, note=''):
        with self.mutex, self.store.mutex:
            piece = self.store.piece(value)
            if piece['author'] == user or piece['state'] != 'in_review': raise Refused('La otra persona debe pedir cambios.')
            self.store.db.execute('UPDATE reviews SET state=?,note=? WHERE slug=? AND state=?', ('changes_requested', str(note)[:10000], value, 'requested'))
            self.store.db.execute('UPDATE pieces SET state=? WHERE slug=?', ('changes_requested', value)); self.store.db.commit()
            return {'state': 'changes_requested'}
    def _halt(self, pub, reason, message):
        """Stop visibly and record why: the reason decides who may resume."""
        data = pub['payload']; data['halted'] = True; data['unknown'] = True; data['halt_reason'] = reason
        self._write(pub, error=message)
    def _effect(self, pub, name, observe, mutate, update):
        data = pub['payload']; found = observe()
        if found:
            update(found)
            for key in ('intent', 'intent_at', 'effect_retries', 'unknown'): data.pop(key, None)
            self._write(pub, name, ''); return True
        now = self.store.clock()
        if data.get('intent'):
            since = data.setdefault('intent_at', now)
            if now - since < budget(*EFFECT_BUDGET):
                self._write(pub, error='No se confirmó la respuesta. Se está comprobando el estado antes de repetir la acción.')
                return False
            # Still nothing observed after the wait: repeat the (pinned, idempotent) write a bounded number of times, then stop visibly.
            tries = data.get('effect_retries', 0) + 1; data['effect_retries'] = tries
            if tries > INFRA_RETRIES:
                self._halt(pub, 'effect', 'La publicación se detuvo porque no se pudo confirmar un paso. Matías ya puede revisarla; el texto aprobado sigue intacto.')
                return False
            data['intent_at'] = now
        else:
            data['intent'] = name; data['intent_at'] = now; self._write(pub)
        mutate()
        found = observe()
        if not found: raise UnknownEffect('La respuesta de publicación no está confirmada.')
        update(found)
        for key in ('intent', 'intent_at', 'effect_retries', 'unknown'): data.pop(key, None)
        self._write(pub, name, ''); return True
    def _start_replay(self, pub):
        """Record the replay (old and new head) durably BEFORE the push; the branch is the witness afterwards."""
        data = pub['payload']; old = data['head_sha']
        moved = self.workspace.recreate(pub)
        data.update(moved); data['replay'] = {'old': old, 'new': moved['head_sha']}; data['intent'] = 'replay'
        self._write(pub)
    def _finish_replay(self, pub):
        """Reconcile a replay by observing the branch: new head = done, old head = push again, anything else = halt for a person."""
        data = pub['payload']; user = data['author']; replay = data['replay']; gh = self.github
        seen = gh.branch(user, data['branch'])
        if seen == replay['old']:
            self.workspace.repush(pub, replay['old']); seen = gh.branch(user, data['branch'])
            if seen != replay['new']: raise UnknownEffect('No se pudo confirmar el envío. Se comprobará antes de repetirlo.')
        if seen != replay['new']:
            # Same outcome as pr_open/checks_green when the public head moved: refused, the author asks for a new review.
            raise Refused('La versión pública cambió; pide una nueva revisión.')
        for key in ('replay', 'intent', 'unknown', 'checks_started'): data.pop(key, None)
        self._write(pub, 'pushed', '')
    def _infra(self, pub, exc):
        """Infrastructure trouble: retry with backoff while the approved content is unchanged; never ask for a new approval."""
        data = pub['payload']; n = data.get('infra_retries', 0) + 1; data['infra_retries'] = n
        if n > INFRA_RETRIES:
            self._halt(pub, 'infra', 'La publicación se detuvo por un problema técnico, no por el texto. Matías ya puede revisarla; el texto aprobado sigue intacto.')
        else:
            data['retry_after'] = self.store.clock() + 60 * 2 ** (n - 1)
            self._write(pub, error=(str(exc) or 'Problema técnico temporal.') + ' Se reintentará solo.')
    def _protection(self, pub):
        data = pub['payload']; gh = self.github; user = data['author']; reviewer = data['reviewer']
        mode = data.get('protection_mode') or protection_mode()
        if mode == 'github':
            if not gh.protected(user): raise Refused('Publicación protegida aún no activa.')
            return
        # Studio keeps the two-person rule itself: a distinct reviewer account pinned to head, a green gate, a confined diff, CODEOWNERS.
        if gh.identity(user) == gh.identity(reviewer): raise Refused('La revisión requiere dos cuentas de GitHub distintas.')
        if not gh.reviewed(reviewer, data['pr_number'], data['head_sha']): raise Refused('Falta la revisión de la otra persona sobre esta versión.')
        if gh.checks(user, data['head_sha']) != 'green': raise Refused('Las comprobaciones públicas cambiaron; revisa el artículo.')
        self.workspace.verify_confined(pub)
        if not any(gh.request(user, 'GET', '/contents/' + path + '?ref=' + data['head_sha']) for path in ('.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS')):
            raise Refused('Falta el archivo CODEOWNERS en el repositorio.')
    def _merge_diff(self, pub):
        """After the merge: the first-parent diff must stay inside the piece. None from the API = not observable, not a failure."""
        data = pub['payload']; rel = data.get('rel') or self.workspace.piece_path(pub)
        commit = self.github.request(data['author'], 'GET', '/commits/' + data['merge_sha'])
        if not isinstance(commit, dict) or not isinstance(commit.get('files'), list) or not commit['files']: data['merge_diff'] = 'unverified'; return True
        ok = all(f.get('filename') == rel or str(f.get('filename', '')).startswith(rel + '/') for f in commit['files'])
        data['merge_diff'] = 'confined' if ok else 'outside'
        return ok
    def advance(self, value):
        # One state transition per call; no HTTP handler holds a long polling loop.
        with self.mutex:
            pub = self.get(value)
            if 'payload' not in pub or pub['state'] in ('published', 'failed'): return pub
            data = pub['payload']; user = data['author']; reviewer = data['reviewer']; gh = self.github
            if data.get('halted') or (data.get('retry_after') and self.store.clock() < data['retry_after']): return pub
            try:
                if self.store.piece(value)['head_rev'] != data['approved_rev']: raise Refused('El artículo cambió después de aprobarlo.')
                state = pub['state']
                if state == 'approved':
                    data.update(self.workspace.prepare(pub)); self._write(pub, 'candidate', '')
                elif state == 'candidate':
                    if not data.get('intent') and (moved := self.workspace.refresh(pub)):
                        data.update(moved); self._write(pub)
                    self._effect(pub, 'pushed', lambda: gh.branch(user, data['branch']) == data['head_sha'], lambda: self.workspace.push(pub), lambda _: None)
                elif state == 'pushed':
                    data.setdefault('protection_mode', protection_mode())
                    body = 'Autor: ' + data['author_name'] + '\nIdiomas: ' + ', '.join(k + ': ' + v for k, v in data['languages'].items())
                    machine = [k for k, p in data['provenance'].items() if p.get('origin', '').startswith('agent_') and not p.get('human_reviewed')]
                    body += '\nTraducciones preparadas por asistente: ' + (', '.join(machine) or 'ninguna')
                    body += '\nModo de protección: ' + data['protection_mode']
                    self._effect(pub, 'pr_open', lambda: gh.find_pr(user, data['branch']), lambda: gh.open_pr(user, data['branch'], data['title'], body), lambda r: data.update(pr_number=r['number']))
                elif state == 'pr_open':
                    pr = gh.pr(user, data['pr_number'])
                    check_merged_head(pr or {}, data['head_sha'])
                    if not pr or pr['head']['sha'] != data['head_sha']: raise Refused('La versión pública cambió; pide una nueva revisión.')
                    self._effect(pub, 'reviewed', lambda: gh.reviewed(reviewer, data['pr_number'], data['head_sha']), lambda: gh.review(reviewer, data['pr_number'], data['head_sha']), lambda _: None)
                elif state == 'reviewed':
                    status = gh.checks(user, data['head_sha'])
                    started = data.setdefault('checks_started', self.store.clock())
                    if status == 'green': self._write(pub, 'checks_green', '')
                    elif status == 'red': raise Refused('Las comprobaciones públicas fallaron. Corrige el artículo y pide revisión otra vez.')
                    elif status == 'cancelled':
                        data.pop('checks_started', None); raise Infra('Las comprobaciones públicas se cancelaron.')
                    elif self.store.clock() - started >= budget(*GATE_BUDGET):
                        data.pop('checks_started', None); raise Infra('Las comprobaciones públicas tardan más de lo normal.')
                    else: self._write(pub)
                elif state == 'checks_green':
                    if data.get('replay'): self._finish_replay(pub); return self.get(value)
                    # Local candidate must equal the recorded head even after a crash between replaying and recording it.
                    git(Path(data['candidate']), 'reset', '-q', '--hard', data['head_sha'])
                    pr = gh.pr(user, data['pr_number']) or {}
                    check_merged_head(pr, data['head_sha'])
                    if not pr or pr['head']['sha'] != data['head_sha']: raise Refused('La versión pública cambió; pide una nueva revisión.')
                    if not pr.get('merged'):
                        if gh.checks(user, data['head_sha']) != 'green': raise Refused('Las comprobaciones públicas cambiaron; revisa el artículo.')
                        # The base may have moved: what must hold is that only the approved bytes differ.
                        self.workspace.verify_confined(pub)
                        self._protection(pub)
                        if pr.get('mergeable') is False or pr.get('mergeable_state') == 'behind':
                            # A conflict, or a branch behind main: replay the same bytes on the new main and take the gate again.
                            self._start_replay(pub); self._finish_replay(pub); return self.get(value)
                    def merge():
                        try: gh.merge(user, data['pr_number'], data['head_sha'])
                        except Refused as exc:
                            fresh = gh.pr(user, data['pr_number']) or {}
                            # Merged meanwhile (e.g. from the GitHub UI): not an error; the observe in _effect moves the piece on.
                            if fresh.get('merged'):
                                check_merged_head(fresh, data['head_sha']); return
                            # GitHub computes mergeability lazily after main moves: an inconclusive read (or a stale-base one)
                            # is infrastructure, retried with backoff. GitHub always sends the key (null while computing); a read without it carries no staleness signal. Only a clean, mergeable read makes this a real refusal.
                            if ('mergeable' in fresh and fresh['mergeable'] is not True) or fresh.get('mergeable_state') in ('unknown', 'behind', 'dirty'):
                                data.pop('intent', None); data.pop('intent_at', None); data.pop('effect_retries', None)
                                raise Infra('La base pública avanzó; se republicará sobre la nueva.') from None
                            raise
                    def observed_merge():
                        p = gh.pr(user, data['pr_number']) or {}
                        check_merged_head(p, data['head_sha'])
                        return p if p.get('merged') else None
                    self._effect(pub, 'merged', observed_merge, merge, lambda r: data.update(merge_sha=r['merge_commit_sha']))
                elif state == 'merged':
                    if 'merge_diff' not in data and not self._merge_diff(pub):
                        self._halt(pub, 'merge_outside', 'Lo publicado toca archivos fuera del artículo. Matías debe revisarlo antes de continuar.'); return self.get(value)
                    started = data.setdefault('deploy_started', self.store.clock())
                    run = gh.pages(user, data['merge_sha'])
                    if run: data['pages_run'] = run['id']; self._write(pub, 'deployed', '')
                    elif self.store.clock() - started >= budget(*DEPLOY_BUDGET):
                        self._write(pub, 'deployed_unverified', 'Ya está fusionado; el despliegue aún no se confirma. Se sigue comprobando.')
                    else: self._write(pub)
                elif state in ('deployed', 'deployed_unverified'):
                    now = self.store.clock(); start = data.setdefault('live_started', now)
                    late = now - start > budget(*LIVE_BUDGET)
                    if data.get('last_live_attempt') and now - data['last_live_attempt'] < (600 if late else 120): return pub
                    data['last_live_attempt'] = now; urls = gh.live(value, data['piece_id'], pub['kind'])
                    if urls:
                        data.pop('unknown', None); data['urls'] = urls; data['live_checked_at'] = utc(); self._write(pub, 'published', '')
                    elif late:
                        data['unknown'] = True; self._write(pub, 'deployed_unverified', 'No logramos confirmar que ya esté visible. Ya está fusionado y desplegado; se sigue comprobando y Matías puede revisarlo.')
                    else: self._write(pub, 'deployed_unverified', 'Desplegado pero aún no visible.')
            except ForeignMerge:
                self._halt(pub, 'foreign_merge', 'Se fusionó fuera de Studio una versión distinta de la aprobada. Matías debe revisarlo antes de continuar.')
            except UnknownEffect as exc:
                if data.get('replay'): self._infra(pub, exc)  # same backoff and cap as any infrastructure trouble
                else:
                    if data.get('intent'): data['unknown'] = True
                    self._write(pub, error=str(exc))
            except (Refused, RuntimeError, OSError, subprocess.SubprocessError, ValueError) as exc:
                if pub['state'] in POST_MERGE:
                    # Public already: never "failed", never back to changes_requested.
                    self._write(pub, error='Ya está fusionado; se sigue comprobando.')
                elif isinstance(exc, Infra) or not isinstance(exc, Refused):
                    self._infra(pub, exc if isinstance(exc, Infra) else Infra('Las comprobaciones no pudieron terminar.'))
                else: self._write(pub, 'failed', str(exc))
            return self.get(value)
    def resume(self, value, user, confirm=False):
        """Continue a halted publication. infra/effect: any editor; the approved text is kept and the next tick observes before any write.
        foreign_merge/merge_outside: only the reviewer, with confirm=true; the reviewer accepts what is public and it is audited."""
        with self.mutex:
            pub = self.get(value); data = pub.get('payload') or {}
            if not data.get('halted'): raise Refused('La publicación no está detenida.')
            reason = data.get('halt_reason')
            if reason in ('foreign_merge', 'merge_outside'):
                if user == data['author'] or user != data['reviewer']: raise Denied('Solo la otra persona puede continuar esta publicación.')
                if confirm is not True: raise NeedsConfirm('Confirma que revisaste lo publicado para continuar.')
                pr = None
                if reason == 'foreign_merge':
                    # Read GitHub before touching the row: a failed read leaves the publication halted for a retry.
                    try: pr = self.github.pr(data['author'], data['pr_number']) or {}
                    except Refused: raise
                    except Exception: raise Infra('No se pudo consultar GitHub para continuar. Inténtalo de nuevo en unos minutos.') from None
                    if not pr.get('merged') or not pr.get('merge_commit_sha'): raise Refused('No hay una fusión que continuar; pide una nueva revisión.')
                data.pop('halted', None); data.pop('halt_reason', None); data.pop('unknown', None)
                data['merge_diff'] = 'accepted_by_reviewer'
                if pr is not None:
                    for key in ('intent', 'intent_at', 'effect_retries', 'replay', 'checks_started'): data.pop(key, None)
                    data['merge_sha'] = pr['merge_commit_sha']
                    self.store.audit(user, 'publication_resume_confirmed', value, {'reason': reason})
                    self._write(pub, 'merged', '')
                else:
                    self.store.audit(user, 'publication_resume_confirmed', value, {'reason': reason})
                    self._write(pub, error='')
                return None
            # infra/effect: keep the pending intent so the next tick observes before repeating any write.
            for key in ('infra_retries', 'retry_after', 'effect_retries'): data.pop(key, None)
            if not data.get('intent'): data.pop('unknown', None)
            data.pop('halted', None); data.pop('halt_reason', None)
            self.store.audit(user, 'publication_resumed', value, {'reason': reason})
            self._write(pub, error='')
            return None
    def public_status(self, value):
        pub = self.get(value); data = pub.get('payload', {})
        from .distribution import email_status
        requested = data.get('distribution', {}).get('email') is True
        state = None
        # Approval alone cannot show email success. Wait for Studio's web proof.
        if requested and pub['state'] == 'published' and self.github is not None:
            state = self.github.email_state(data['author'])
        email = email_status(state, data.get('piece_id'), requested)
        return {'email': email, 'state': pub['state'], 'approved_at': pub.get('approved_at'), 'timeline': data.get('timeline', []), 'error_plain': pub.get('error_plain', ''), 'uncertain': bool(data.get('unknown')), 'urls': data.get('urls', []),
                'halted': bool(data.get('halted')), 'halt_reason': data.get('halt_reason') if data.get('halted') else None, 'author': data.get('author')}
