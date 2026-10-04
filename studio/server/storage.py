"""Private SQLite journal + atomic draft files + real local git checkpoints.

SQLite owns autosave bytes and revisions. Files are mirrors rebuilt on startup,
so a power loss between the transaction and rename cannot lose an acknowledged save.
"""
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import threading
import time
from .validation import LOCALES, locale, slug, validate_doc, validate_sources, validate_figures, plain_text

NAMES = {'javier': 'Javier', 'matias': 'Matías'}

def utc(): return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
def encoded(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name('.' + path.name + '-' + secrets.token_hex(6))
    try:
        with open(temp, 'xb') as f:
            os.chmod(temp, 0o600); f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)

def git(path, *args, env=None):
    run = subprocess.run(['git', '-C', str(path), *args], env=env, capture_output=True, timeout=120)
    if run.returncode: raise RuntimeError('No se pudo guardar la versión local.')
    return run.stdout.decode().strip()

class Conflict(Exception):
    def __init__(self, current): self.current = current
class Locked(Exception):
    def __init__(self, owner): self.owner = owner

class Store:
    def __init__(self, data, clock=time.time):
        self.data = Path(data).resolve(); self.clock = clock
        self.data.mkdir(parents=True, exist_ok=True, mode=0o700); os.chmod(self.data, 0o700)
        self.mutex = threading.RLock()
        self.db = sqlite3.connect(self.data / 'studio.sqlite', check_same_thread=False)
        os.chmod(self.data / 'studio.sqlite', 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL'); self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users(key TEXT PRIMARY KEY, name TEXT, pw_scrypt TEXT, gh_login TEXT, ui_lang TEXT, failures INTEGER DEFAULT 0, locked_until REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(id_hash TEXT PRIMARY KEY, user TEXT, created REAL, last_seen REAL, ua TEXT, csrf TEXT);
        CREATE TABLE IF NOT EXISTS pieces(slug TEXT PRIMARY KEY, kind TEXT, author TEXT, state TEXT, locale_states_json TEXT, cursor_json TEXT, lock_user TEXT, lock_at REAL, head_rev INTEGER, payload_json TEXT, saved_at REAL, saved_by TEXT);
        CREATE TABLE IF NOT EXISTS locks(slug TEXT, locale TEXT, user TEXT, at REAL, PRIMARY KEY(slug,locale));
        CREATE TABLE IF NOT EXISTS checkpoints(slug TEXT, rev INTEGER, git_sha TEXT, at TEXT, user TEXT, name TEXT, payload_json TEXT, PRIMARY KEY(slug,rev));
        CREATE TABLE IF NOT EXISTS comments(id TEXT PRIMARY KEY, slug TEXT, locale TEXT, block_id TEXT, user TEXT, at TEXT, body TEXT, resolved_at TEXT);
        CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, slug TEXT, rev INTEGER, author TEXT, reviewer TEXT, state TEXT, at TEXT, note TEXT);
        CREATE TABLE IF NOT EXISTS publications(id TEXT PRIMARY KEY, slug TEXT, kind TEXT, state TEXT, pr_number INTEGER, head_sha TEXT, merge_sha TEXT, pages_run INTEGER, live_checked_at TEXT, error_plain TEXT, payload_json TEXT);
        CREATE TABLE IF NOT EXISTS audit(at TEXT, user TEXT, action TEXT, slug TEXT, detail_json TEXT);
        CREATE TABLE IF NOT EXISTS issues(id TEXT PRIMARY KEY, author TEXT, state TEXT, rev INTEGER, payload_json TEXT);
        ''')
        self.db.commit()
        for part in ('worktrees', 'uploads-tmp', 'jobs/queued', 'jobs/done'):
            (self.data / part).mkdir(parents=True, exist_ok=True, mode=0o700)
        clone = self.data / 'clone'
        if not clone.exists():
            clone.mkdir(mode=0o700); git(clone, 'init', '-q', '-b', 'main')
            git(clone, '-c', 'user.name=Studio', '-c', 'user.email=noreply@openai.com', 'commit', '--allow-empty', '-qm', 'Private Studio store')
        git(clone, 'config', 'push.default', 'nothing')
        git(clone, 'config', '--replace-all', 'remote.origin.push', 'refs/heads/studio/*:refs/heads/studio/*')
        for piece in self.list():
            self._worktree(piece['slug']); self._mirror(piece['slug'])
    def close(self):
        with self.mutex: self.db.close()
    def audit(self, user, action, piece='', details=None):
        # Callers supply only identifiers/status; never document bodies or credentials.
        self.db.execute('INSERT INTO audit VALUES(?,?,?,?,?)', (utc(), user, action, piece, encoded(details or {})))
    def _row(self, value):
        slug(value)
        row = self.db.execute('SELECT * FROM pieces WHERE slug=?', (value,)).fetchone()
        if row is None: raise KeyError('La publicación no existe.')
        return row
    def payload(self, value):
        with self.mutex: return json.loads(self._row(value)['payload_json'])
    def _worktree(self, value):
        target = self.data / 'worktrees' / slug(value)
        if not target.exists():
            clone = self.data / 'clone'; branch = 'draft/' + value
            exists = subprocess.run(['git', '-C', str(clone), 'show-ref', '--verify', '--quiet', 'refs/heads/' + branch]).returncode == 0
            git(clone, 'worktree', 'prune')
            if exists: git(clone, 'worktree', 'add', '-q', str(target), branch)
            else: git(clone, 'worktree', 'add', '-qb', branch, str(target), 'HEAD')
        return target
    def directory(self, value): return self._worktree(value) / 'editorial' / 'pieces' / value
    def _mirror(self, value):
        payload = self.payload(value); directory = self.directory(value)
        if 'issue' in payload:
            atomic(self._worktree(value) / 'editorial/issues' / (value + '.json'), (encoded(payload['issue']) + '\n').encode())
            return
        for key in ('piece', 'sources', 'figures', 'provenance'):
            atomic(directory / (key + '.json'), (encoded(payload[key]) + '\n').encode())
        for loc, doc in payload['docs'].items():
            atomic(directory / ('doc.' + loc + '.json'), (encoded(doc) + '\n').encode())
    def _put(self, value, payload, user, bump=True, cursor=None, states=None, state=None):
        row = self._row(value); rev = row['head_rev'] + int(bump)
        self.db.execute('UPDATE pieces SET payload_json=?, head_rev=?, saved_at=?, saved_by=?, cursor_json=?, locale_states_json=?, state=? WHERE slug=?',
                        (encoded(payload), rev, self.clock(), user, encoded(cursor) if cursor is not None else row['cursor_json'],
                         encoded(states) if states is not None else row['locale_states_json'], state or row['state'], value))
        self.audit(user, 'save' if bump else 'state', value, {'rev': rev})
        self.db.commit(); self._mirror(value)
        return rev
    def create(self, user, kind, title, source_locale):
        if user not in NAMES or kind not in ('essay', 'letter', 'note') or not isinstance(title, str): raise ValueError('Completa los datos de la publicación.')
        locale(source_locale)
        # English stays canonical until the operator adopts Q2.
        if source_locale != 'en' and os.environ.get('STUDIO_ALLOW_NON_EN_SOURCE') != '1':
            raise ValueError('El idioma original aún debe ser inglés; falta la decisión editorial.')
        with self.mutex:
            value = (re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')[:60] or 'ensayo') + '-' + secrets.token_hex(4)
            stamp = utc()
            piece = {'schema': 'fcmo-piece-v1', 'id': 'FCMO-P-' + secrets.token_hex(6), 'kind': kind, 'slug': value,
                     'authors': [{'key': user, 'name': NAMES[user]}], 'brand': 'fcmo' if user == 'javier' else 'fcmo-ai',
                     'source_locale': source_locale, 'status': 'published', 'first_published_at': stamp, 'updated_at': stamp,
                     'locales': {loc: 'pending' for loc in LOCALES}, 'hero': None, 'tags': [], 'corrections': [], 'withdrawal': None}
            doc = {'schema': 'fcmo-essay-doc-v1', 'locale': source_locale, 'title': title, 'dek': '', 'blocks': [], 'footnotes': {}}
            payload = {'piece': piece, 'docs': {source_locale: doc}, 'sources': [], 'figures': {}, 'provenance': {}, 'block_provenance': {}, 'source_hashes': {}}
            states = {loc: {'state': 'drafting' if loc == source_locale else 'empty', 'human_reviewed': False} for loc in LOCALES}
            self.db.execute('INSERT INTO pieces VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                            (value, kind, user, 'draft', encoded(states), '{}', None, None, 0, encoded(payload), self.clock(), user))
            self.audit(user, 'create', value); self.db.commit(); self._mirror(value)
            return self.piece(value)
    def piece(self, value):
        with self.mutex:
            row = dict(self._row(value)); payload = json.loads(row.pop('payload_json'))
            row['locale_states'] = json.loads(row.pop('locale_states_json')); row['cursor'] = json.loads(row.pop('cursor_json'))
            row['source_locale'] = payload['piece']['source_locale']
            row['locales'] = {loc: {**state, 'reviewed': state['human_reviewed'], 'origin': payload['provenance'].get(loc, {}).get('origin'), 'words': len(plain_text(payload['docs'].get(loc, {'blocks': []})).split())} for loc, state in row['locale_states'].items()}
            row['words'] = row['locales'][row['source_locale']]['words']
            row['updated_at'] = datetime.fromtimestamp(row['saved_at'], timezone.utc).isoformat()
            row['meta'] = payload['piece']; row['title'] = payload.get('issue', {}).get('title', {}).get('en') or payload['docs'][payload['piece']['source_locale']]['title']
            row['lock'] = {r['locale']: {'user': r['user'], 'at': r['at']} for r in self.db.execute('SELECT * FROM locks WHERE slug=?', (value,))}
            row['comments_count'] = self.db.execute('SELECT count(*) FROM comments WHERE slug=? AND resolved_at IS NULL', (value,)).fetchone()[0]
            return row
    def list(self, state=None):
        with self.mutex:
            rows = self.db.execute('SELECT slug FROM pieces ORDER BY saved_at DESC').fetchall()
            return [p for r in rows if (p := self.piece(r[0])) and (state is None or p['state'] == state)]
    def doc(self, value, loc):
        locale(loc)
        with self.mutex:
            row = self._row(value); payload = json.loads(row['payload_json'])
            doc = payload['docs'].get(loc, {'schema': 'fcmo-essay-doc-v1', 'locale': loc, 'title': '', 'dek': '', 'blocks': [], 'footnotes': {}})
            source = payload['docs'][payload['piece']['source_locale']]
            hashes = {b['id']: hashlib.sha256(encoded(b).encode()).hexdigest() for b in source['blocks']}
            saved = payload.get('source_hashes', {}).get(loc, {})
            return {'rev': row['head_rev'], 'doc': doc, 'by': row['saved_by'], 'at': row['saved_at'],
                    'block_provenance': payload.get('block_provenance', {}).get(loc, {}), 'source_hashes': saved,
                    'source_changed': [key for key, digest in saved.items() if hashes.get(key) != digest]}
    def _editable(self, value):
        if self._row(value)['state'] not in ('draft', 'changes_requested', 'amending'):
            raise ValueError('Pide cambios antes de modificar una publicación en revisión.')
    def _lock_guard(self, value, loc, user):
        row = self.db.execute('SELECT * FROM locks WHERE slug=? AND locale=?', (value, loc)).fetchone()
        if row and row['user'] != user and self.clock() - row['at'] < 600: raise Locked(row['user'])
    def save(self, value, loc, user, base_rev, doc, cursor):
        validate_doc(doc, loc)
        if not isinstance(cursor, dict): raise ValueError('La posición no es válida.')
        with self.mutex:
            self._editable(value); self._lock_guard(value, loc, user)
            if type(base_rev) is not int or base_rev != self._row(value)['head_rev']: raise Conflict(self.doc(value, loc))
            payload = self.payload(value); states = self.piece(value)['locale_states']; cursors = self.piece(value)['cursor']
            source = payload['piece']['source_locale']; old = payload['docs'].get(loc)
            payload['docs'][loc] = copy.deepcopy(doc); cursors[loc] = cursor
            if old != doc:
                states[loc] = {'state': 'drafting', 'human_reviewed': False}
                payload['piece']['locales'][loc] = 'pending'
                prior = payload['provenance'].get(loc, {})
                if prior.get('origin', '').startswith('agent_'):
                    prior['origin'] = 'agent_draft_human_edited'; prior['human_reviewed'] = False
                else: payload['provenance'].pop(loc, None)
                payload.setdefault('block_provenance', {})[loc] = {b['id']: 'agent_draft_human_edited' if prior.get('origin', '').startswith('agent_') else 'human_authored' for b in doc['blocks']}
                if loc != source:
                    payload.setdefault('source_hashes', {})[loc] = {b['id']: hashlib.sha256(encoded(b).encode()).hexdigest() for b in payload['docs'][source]['blocks']}
                if loc == source:
                    for target in LOCALES:
                        if target != source and states[target]['state'] == 'ready':
                            states[target] = {'state': 'drafting', 'human_reviewed': False, 'source_changed': True}
                            payload['piece']['locales'][target] = 'pending'
                            if target in payload['provenance']: payload['provenance'][target]['human_reviewed'] = False
            self.db.execute('INSERT OR REPLACE INTO locks VALUES(?,?,?,?)', (value, loc, user, self.clock()))
            rev = self._put(value, payload, user, cursor=cursors, states=states)
            return {'rev': rev}
    def lock(self, value, loc, user, takeover=False):
        locale(loc)
        with self.mutex:
            self._row(value)
            if not takeover: self._lock_guard(value, loc, user)
            self.db.execute('INSERT OR REPLACE INTO locks VALUES(?,?,?,?)', (value, loc, user, self.clock()))
            self.audit(user, 'lock', value, {'locale': loc, 'takeover': bool(takeover)}); self.db.commit()
            return self.piece(value)['lock'][loc]
    def unlock(self, value, loc, user):
        with self.mutex:
            self._lock_guard(value, loc, user); self.checkpoint(value, user)
            self.db.execute('DELETE FROM locks WHERE slug=? AND locale=? AND user=?', (value, locale(loc), user)); self.db.commit()
    def resource(self, value, kind, user=None, data=None):
        if kind not in ('sources', 'figures'): raise ValueError('El recurso no existe.')
        with self.mutex:
            payload = self.payload(value)
            if data is not None:
                self._editable(value)
                (validate_sources if kind == 'sources' else validate_figures)(data)
                payload[kind] = data; self._put(value, payload, user)
            return payload[kind]
    def locale_state(self, value, loc, user, state, reviewed=False, confirmation=''):
        locale(loc)
        if state not in ('ready', 'later', 'drafting') or type(reviewed) is not bool: raise ValueError('El estado del idioma no es válido.')
        if loc == 'zh-Hans' and reviewed and confirmation != 'Leí y entiendo el texto chino': raise ValueError('Confirma que leíste y entiendes el texto chino.')
        with self.mutex:
            self._editable(value); self._lock_guard(value, loc, user)
            payload = self.payload(value); states = self.piece(value)['locale_states']
            if state == 'ready' and not (payload['issue']['title'][loc].strip() if 'issue' in payload else (loc in payload['docs'] and payload['docs'][loc]['title'].strip())): raise ValueError('Completa el idioma antes de marcarlo listo.')
            stamp = utc(); states[loc] = {'state': state, 'human_reviewed': reviewed if state == 'ready' else False, 'by': user, 'at': stamp}
            source = payload['piece']['source_locale']
            if state == 'ready':
                prior = payload['provenance'].get(loc, {})
                payload['provenance'][loc] = {'origin': prior.get('origin', 'human_authored' if loc == source else 'human_translated'),
                    'human_reviewed': reviewed, 'reviewer': NAMES[user] if reviewed else '', 'at': stamp, 'source_locale': source}
                if prior.get('model'): payload['provenance'][loc]['model'] = prior['model']
            payload['piece']['locales'][loc] = 'ready' if state == 'ready' else 'pending'
            self._put(value, payload, user, states=states)
            return states[loc]
    def checkpoint(self, value, user, name=None):
        with self.mutex:
            row = self._row(value); rev = row['head_rev']
            existing = self.db.execute('SELECT * FROM checkpoints WHERE slug=? AND rev=?', (value, rev)).fetchone()
            if existing:
                if name:
                    self.db.execute('UPDATE checkpoints SET name=? WHERE slug=? AND rev=?', (str(name)[:200], value, rev)); self.db.commit()
                return {'rev': rev, 'git_sha': existing['git_sha']}
            self._mirror(value); worktree = self._worktree(value)
            git(worktree, 'add', '--', ('editorial/issues/' + value + '.json') if 'issue' in self.payload(value) else ('editorial/pieces/' + value))
            env = dict(os.environ, GIT_AUTHOR_NAME=NAMES[user], GIT_AUTHOR_EMAIL='noreply@openai.com', GIT_COMMITTER_NAME='Studio', GIT_COMMITTER_EMAIL='noreply@openai.com')
            git(worktree, 'commit', '--allow-empty', '-qm', 'Writing checkpoint', env=env)
            sha = git(worktree, 'rev-parse', 'HEAD')
            self.db.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?)', (value, rev, sha, utc(), user, str(name)[:200] if name else None, row['payload_json']))
            self.audit(user, 'checkpoint', value, {'rev': rev}); self.db.commit()
            return {'rev': rev, 'git_sha': sha}
    def idle_checkpoints(self, now=None):
        with self.mutex:
            now = self.clock() if now is None else now
            for row in self.db.execute('SELECT slug,head_rev,saved_at,saved_by FROM pieces').fetchall():
                if now - row['saved_at'] >= 60 and not self.db.execute('SELECT 1 FROM checkpoints WHERE slug=? AND rev=?', (row['slug'], row['head_rev'])).fetchone():
                    self.checkpoint(row['slug'], row['saved_by'])
    def versions(self, value):
        with self.mutex:
            self._row(value)
            return [dict(r) for r in self.db.execute('SELECT rev,git_sha,at,user,name FROM checkpoints WHERE slug=? ORDER BY rev DESC', (value,))]
    def restore(self, value, rev, user):
        with self.mutex:
            self._editable(value)
            for loc in LOCALES: self._lock_guard(value, loc, user)
            old = self.db.execute('SELECT payload_json FROM checkpoints WHERE slug=? AND rev=?', (value, int(rev))).fetchone()
            if not old: raise KeyError('La versión no existe.')
            self.checkpoint(value, user, 'Antes de restaurar')
            payload = json.loads(old[0]); states = self.piece(value)['locale_states']
            for loc in LOCALES:
                states[loc] = {'state': 'drafting' if loc in payload['docs'] else 'empty', 'human_reviewed': False}
                payload['piece']['locales'][loc] = 'pending'
                if loc in payload['provenance']: payload['provenance'][loc]['human_reviewed'] = False
            new = self._put(value, payload, user, states=states); self.checkpoint(value, user, 'Restaurada')
            return {'rev': new}
    def diff(self, value, left, right, loc):
        locale(loc)
        def words(rev):
            if rev == 'current': return (self.payload(value)['docs'][loc]['title'] + ' ' + self.payload(value)['docs'][loc]['dek'] + ' ' + plain_text(self.payload(value)['docs'][loc])).split()
            if rev == 'published':
                versions = self.db.execute("SELECT payload_json FROM publications WHERE slug=? AND state='published' ORDER BY rowid DESC LIMIT 1", (value,)).fetchone()
                if not versions: raise KeyError('No hay una versión publicada.')
                rev = json.loads(versions[0])['approved_rev']
            row = self.db.execute('SELECT payload_json FROM checkpoints WHERE slug=? AND rev=?', (value, int(rev))).fetchone()
            if not row: raise KeyError('La versión no existe.')
            document = json.loads(row[0])['docs'][loc]
            return (document['title'] + ' ' + document['dek'] + ' ' + plain_text(document)).split()
        with self.mutex: return list(difflib.ndiff(words(left), words(right)))
    def comment(self, value, loc, block_id, user, body):
        locale(loc)
        if not isinstance(body, str) or not body.strip() or len(body) > 10000: raise ValueError('Escribe un comentario.')
        with self.mutex:
            if block_id not in {b['id'] for b in self.doc(value, loc)['doc']['blocks']}: raise ValueError('El párrafo no existe.')
            key = secrets.token_hex(12)
            self.db.execute('INSERT INTO comments VALUES(?,?,?,?,?,?,?,NULL)', (key, value, loc, block_id, user, utc(), body))
            self.db.commit(); return {'id': key}
    def comments(self, value):
        with self.mutex:
            self._row(value); return [dict(r) for r in self.db.execute('SELECT * FROM comments WHERE slug=? ORDER BY at', (value,))]
    def resolve(self, key, user):
        with self.mutex:
            row = self.db.execute('SELECT * FROM comments WHERE id=?', (key,)).fetchone()
            if not row: raise KeyError('El comentario no existe.')
            self.db.execute('UPDATE comments SET resolved_at=? WHERE id=?', (utc(), key)); self.audit(user, 'resolve', row['slug']); self.db.commit()
    def amend(self, value, user, kind, notes, reason=None):
        with self.mutex:
            row = self._row(value)
            if row['author'] != user or row['state'] not in ('published', 'withdrawn'): raise ValueError('Solo el autor puede corregir una publicación publicada.')
            payload = self.payload(value); piece = payload['piece']
            ready = [loc for loc in LOCALES if piece['locales'][loc] == 'ready']
            if kind != 'typo' and (not isinstance(notes, dict) or any(not isinstance(notes.get(loc), str) or not notes[loc].strip() for loc in ready)):
                raise ValueError('Escribe una nota en cada idioma publicado.')
            if kind == 'withdraw':
                if reason not in ('UPSTREAM_RETRACTION', 'UNVERIFIED_RELEASE', 'DUPLICATE', 'FACTUAL_ERROR', 'RIGHTS', 'PRIVACY', 'LEGAL', 'EDITORIAL'):
                    raise ValueError('El motivo de retiro no es válido.')
                piece['status'] = 'withdrawn'; piece['withdrawal'] = {'at': utc(), 'reason_code': reason, 'note': notes}
            elif kind in ('clarification', 'substantive'): piece['corrections'].append({'at': utc(), 'type': kind, 'note': notes})
            elif kind != 'typo': raise ValueError('El tipo de corrección no es válido.')
            piece['updated_at'] = utc(); self._put(value, payload, user, state='amending')
            return self.piece(value)
