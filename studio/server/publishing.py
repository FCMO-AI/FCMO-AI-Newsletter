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

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class GitHub:
    def __init__(self, tokens, api='https://api.github.com', repo='FCMO-AI/FCMO-AI-Newsletter', live_base='https://fcmo-ai.github.io/FCMO-AI-Newsletter/'):
        self.tokens = tokens; self.api = api.rstrip('/'); self.repo = repo; self.live_base = live_base.rstrip('/') + '/'
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
        return 'green' if newest.get('conclusion') == 'success' else 'red'
    def protected(self, user):
        rules = self.request(user, 'GET', '/rules/branches/main') or []
        pulls = [r.get('parameters', {}) for r in rules if r.get('type') == 'pull_request']
        checks = [r.get('parameters', {}) for r in rules if r.get('type') == 'required_status_checks']
        good_pull = any(p.get('required_approving_review_count', 0) >= 1 and p.get('require_code_owner_review') and p.get('require_last_push_approval') and p.get('dismiss_stale_reviews_on_push') for p in pulls)
        good_check = any(p.get('strict_required_status_checks_policy') and any(c.get('context') == 'publish-gate' for c in p.get('required_status_checks', [])) for p in checks)
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
        result = self.request(user, 'GET', '/actions/workflows/pages.yml/runs?' + urlencode({'head_sha': merge, 'event': 'push', 'per_page': 100})) or {}
        runs = [r for r in result.get('workflow_runs', []) if r.get('head_sha') == merge and r.get('event') == 'push']
        if not runs: return None
        run = max(runs, key=lambda r: r.get('id', 0))
        if run.get('status') == 'completed' and run.get('conclusion') != 'success': raise Refused('El despliegue falló. La publicación aún no está confirmada.')
        return run if run.get('conclusion') == 'success' else None
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
        git(target, '-c', 'user.name=' + data['author_name'], '-c', 'user.email=noreply@openai.com', 'commit', '-qm', 'Publish ' + data['title'])
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
        return {'head_sha': head, 'base_sha': base_sha, 'candidate': str(target)}
    def verify_base(self, pub):
        data = pub['payload']
        current = git(Path(data['candidate']), 'ls-remote', 'origin', 'refs/heads/main').split()
        if not current or current[0] != data.get('base_sha'):
            raise Refused('La base de publicación cambió. Pide una nueva revisión antes de publicar.')
    def push(self, pub):
        data = pub['payload']; branch = data['branch']
        self.github.validate_remote(self.store.data / 'clone')
        self.github.preflight(data['author'], data['reviewer'])
        if not branch.startswith('studio/') or data['head_sha'] != git(Path(data['candidate']), 'rev-parse', 'HEAD'):
            raise Refused('La versión aprobada cambió antes de publicar.')
        self.verify_base(pub)
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
            pub['payload'].setdefault('timeline', []).append({'state': state, 'at': utc(), 'plain_es': PROGRESS[state][0], 'plain_en': PROGRESS[state][1]})
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
            result = dict(row); result['payload'] = json.loads(result.pop('payload_json')); return result
    def request(self, value, user):
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
                from studio.translation import validate_translation, TranslationError
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
                    payload['provenance'][loc] = {**prior, 'origin': prior.get('origin', 'human_authored' if loc == source else 'human_translated'),
                        'human_reviewed': True, 'reviewer': NAMES[user], 'at': stamp, 'source_locale': source}
                    states[loc] = {**states[loc], 'human_reviewed': True, 'by': user, 'at': stamp}
                self.store._put(value, payload, user, bump=False, states=states)
            if not self.store.db.execute('SELECT 1 FROM publications WHERE slug=? AND state=?', (value, 'published')).fetchone(): payload['piece']['first_published_at'] = stamp
            # Freeze timestamps before candidate check and public push.
            self.store._put(value, payload, piece['author'], bump=False)
            data = {'author': piece['author'], 'author_name': payload['piece']['authors'][0]['name'], 'reviewer': user,
                    'approved_rev': piece['head_rev'], 'branch': 'studio/' + value + '-' + ident[:8], 'piece_id': payload['piece']['id'],
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
    def _effect(self, pub, name, observe, mutate, update):
        data = pub['payload']; found = observe()
        if found:
            update(found); data.pop('intent', None); data.pop('unknown', None); self._write(pub, name, ''); return True
        if data.get('intent'):
            self._write(pub, error='No se confirmó la respuesta. Se está comprobando el estado antes de repetir la acción.')
            return False
        data['intent'] = name; self._write(pub)
        mutate()
        found = observe()
        if not found: raise UnknownEffect('La respuesta de publicación no está confirmada.')
        update(found); data.pop('intent', None); data.pop('unknown', None); self._write(pub, name, ''); return True
    def advance(self, value):
        # One state transition per call; no HTTP handler holds a long polling loop.
        with self.mutex:
            pub = self.get(value)
            if 'payload' not in pub or pub['state'] in ('published', 'failed'): return pub
            data = pub['payload']; user = data['author']; reviewer = data['reviewer']; gh = self.github
            try:
                if self.store.piece(value)['head_rev'] != data['approved_rev']: raise Refused('El artículo cambió después de aprobarlo.')
                state = pub['state']
                if state == 'approved':
                    data.update(self.workspace.prepare(pub)); self._write(pub, 'candidate', '')
                elif state == 'candidate':
                    self._effect(pub, 'pushed', lambda: gh.branch(user, data['branch']) == data['head_sha'], lambda: self.workspace.push(pub), lambda _: None)
                elif state == 'pushed':
                    body = 'Autor: ' + data['author_name'] + '\nIdiomas: ' + ', '.join(k + ': ' + v for k, v in data['languages'].items())
                    machine = [k for k, p in data['provenance'].items() if p.get('origin', '').startswith('agent_') and not p.get('human_reviewed')]
                    body += '\nTraducciones preparadas por asistente: ' + (', '.join(machine) or 'ninguna')
                    self._effect(pub, 'pr_open', lambda: gh.find_pr(user, data['branch']), lambda: gh.open_pr(user, data['branch'], data['title'], body), lambda r: data.update(pr_number=r['number']))
                elif state == 'pr_open':
                    pr = gh.pr(user, data['pr_number'])
                    if not pr or pr['head']['sha'] != data['head_sha']: raise Refused('La versión pública cambió; pide una nueva revisión.')
                    self._effect(pub, 'reviewed', lambda: gh.reviewed(reviewer, data['pr_number'], data['head_sha']), lambda: gh.review(reviewer, data['pr_number'], data['head_sha']), lambda _: None)
                elif state == 'reviewed':
                    status = gh.checks(user, data['head_sha'])
                    if status == 'green': self._write(pub, 'checks_green', '')
                    elif status == 'red': raise Refused('Las comprobaciones públicas fallaron. Corrige el artículo y pide revisión otra vez.')
                    elif self.store.clock() - data.get('checks_started', data['created']) >= 1800: raise Refused('Las comprobaciones públicas no terminaron en 30 minutos.')
                    else: data.setdefault('checks_started', self.store.clock()); self._write(pub)
                elif state == 'checks_green':
                    pr = gh.pr(user, data['pr_number'])
                    if not pr or pr['head']['sha'] != data['head_sha']: raise Refused('La versión pública cambió; pide una nueva revisión.')
                    if not pr.get('merged'):
                        if gh.branch(user, 'main') != data['base_sha']: raise Refused('La base de publicación cambió. Pide una nueva revisión antes de publicar.')
                        if gh.checks(user, data['head_sha']) != 'green': raise Refused('Las comprobaciones públicas cambiaron; revisa el artículo.')
                        if not gh.protected(user): raise Refused('Publicación protegida aún no activa.')
                    self._effect(pub, 'merged', lambda: (p if (p := gh.pr(user, data['pr_number'])) and p.get('merged') else None), lambda: gh.merge(user, data['pr_number'], data['head_sha']), lambda r: data.update(merge_sha=r['merge_commit_sha']))
                elif state == 'merged':
                    run = gh.pages(user, data['merge_sha'])
                    if run: data['pages_run'] = run['id']; self._write(pub, 'deployed', '')
                    elif self.store.clock() - data.get('deploy_started', data['created']) >= 1800: raise Refused('El despliegue no terminó en 30 minutos; comprueba su estado.')
                    else: data.setdefault('deploy_started', self.store.clock()); self._write(pub)
                elif state in ('deployed', 'deployed_unverified'):
                    now = self.store.clock(); start = data.setdefault('live_started', now)
                    if data.get('last_live_attempt') and now - data['last_live_attempt'] < 120: return pub
                    if now - start > 1800:
                        self._write(pub, error='Desplegado pero aún no visible. Revisa el sitio antes de confirmar la publicación.'); return pub
                    data['last_live_attempt'] = now; urls = gh.live(value, data['piece_id'], pub['kind'])
                    if urls:
                        data['urls'] = urls; data['live_checked_at'] = utc(); self._write(pub, 'published', '')
                    else: self._write(pub, 'deployed_unverified', 'Desplegado pero aún no visible.')
            except UnknownEffect as exc:
                if data.get('intent'): data['unknown'] = True
                self._write(pub, error=str(exc))
            except (Refused, RuntimeError, OSError, subprocess.SubprocessError, ValueError) as exc:
                self._write(pub, 'failed', str(exc) if isinstance(exc, Refused) else 'Las comprobaciones locales no pudieron terminar. Nada se publicó.')
            return self.get(value)
    def public_status(self, value):
        pub = self.get(value); data = pub.get('payload', {})
        from .distribution import email_status
        requested = data.get('distribution', {}).get('email') is True
        state = None
        # Approval alone cannot show email success. Wait for Studio's web proof.
        if requested and pub['state'] == 'published' and self.github is not None:
            state = self.github.email_state(data['author'])
        email = email_status(state, data.get('piece_id'), requested)
        return {'email': email, 'state': pub['state'], 'timeline': data.get('timeline', []), 'error_plain': pub.get('error_plain', ''), 'uncertain': bool(data.get('unknown')), 'urls': data.get('urls', [])}
