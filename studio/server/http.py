"""Authenticated loopback HTTP API; production assets are served read-only."""
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit
from . import issues, assist, bundle
from .messages import localize
from .auth import Auth, COOKIE, TTL
from .checks import checks
from .preview import Preview, RendererUnavailable
from .publishing import GitHub, Workspace, Publisher, Refused, UnknownEffect
from .storage import Store, Conflict, Locked, atomic
from studio.translation import translate, TranslationError
from .validation import locale, slug, validate_webp

PREVIEW_CSP = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; font-src 'self'; connect-src 'none'; frame-ancestors 'self'; form-action 'none'; base-uri 'none'"
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; font-src 'self'; connect-src 'self'; frame-ancestors 'self'; form-action 'self'; base-uri 'none'"

class Application:
    def __init__(self, store, origin, session_key, repo, publisher=None, preview=None, live=False, tokens=None, github=None):
        parsed = urlsplit(origin)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment: raise ValueError('El origen de Studio no es válido.')
        self.store = store; self.origin = origin; self.repo = Path(repo); self.auth = Auth(store, session_key)
        self.preview = preview or Preview(store, repo); self.live_enabled = live
        import os
        self.dry_run = os.environ.get('STUDIO_DRY_RUN') == '1'
        if github is None and tokens is None:
            from .credentials import GitHubCLI
            import os
            github = GitHubCLI({u: os.environ.get('STUDIO_GH_CONFIG_' + u.upper()) for u in ('javier', 'matias')})
        self.github = github or GitHub(tokens or {})
        self.publisher = publisher or Publisher(store, self.github, Workspace(store, self.github), lambda value: issues.checks(store, self.preview, value) if store.piece(value)['kind'] == 'issue' else checks(store, self.preview, value))
        self.dist = self.repo / 'studio/web/dist'; self.web_ready = bundle.ready(self.repo); self.preview_sessions = {}; self.stop = threading.Event()
    def tick(self):
        self.store.idle_checkpoints()
        if self.live_enabled and not self.dry_run:
            with self.store.mutex:
                queued = self.store.db.execute("SELECT slug FROM publications WHERE state NOT IN ('published','failed')").fetchall()
            for row in queued:
                pub = self.publisher.advance(row['slug'])
                if pub['state'] == 'published' and hasattr(self.store, 'public_root'):
                    from .snapshot import refresh
                    refresh(self.store, self.github)
        cutoff = self.store.clock() - 86400
        for path in (self.store.data / 'uploads-tmp').iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff: path.unlink()
    def worker(self):
        while not self.stop.wait(5):
            try: self.tick()
            except Exception: pass  # Durable state retained; never log document/token/trace.
    def api(self, method, path, query, body, session):
        user = session['user']; parts = path.strip('/').split('/')
        if path == '/api/publication-readiness' and method == 'GET':
            statuses = self.github.credential_status() if hasattr(self.github, 'credential_status') else [
                {'user': u, 'ready': bool(self.github.tokens.get(u)),
                 'plain_es': ('Javier' if u == 'javier' else 'Matías') + ' debe iniciar sesión en GitHub.',
                 'plain_en': ('Javier' if u == 'javier' else 'Matías') + ' needs to sign in to GitHub.'}
                for u in ('javier', 'matias')]
            return {'credentials': statuses, 'live_enabled': self.live_enabled, 'dry_run': self.dry_run}
        if path == '/api/me' and method == 'GET': return {'user': user, 'name': session['name'], 'ui_lang': session['ui_lang'], 'csrf': session['csrf'], 'other': 'Matías' if user == 'javier' else 'Javier', 'allow_non_en_source': __import__('os').environ.get('STUDIO_ALLOW_NON_EN_SOURCE') == '1', 'allow_es_source': True}
        if path == '/api/pieces':
            if method == 'GET': return self.store.list(query.get('state', [None])[0])
            if method == 'POST': return self.store.create(user, body.get('kind', 'essay'), body.get('title', ''), body.get('source_locale', 'es-419' if user == 'javier' else 'en'))
        if path == '/api/site/rollback' and method == 'POST':
            if body.get('confirmation') != 'Volver a la última versión comprobada': raise ValueError('Confirma que quieres volver a la última versión comprobada.')
            if not self.live_enabled: raise Refused('La publicación en vivo aún no está habilitada.')
            self.github.rollback(user)
            return {'state': 'requested', 'plain_es': 'Se pidió restaurar el despliegue anterior. El retiro revisado sigue siendo necesario; lo que un lector ya vio no se deshace.'}
        if len(parts) == 4 and parts[:2] == ['api', 'comments'] and parts[3] == 'resolve' and method == 'POST':
            self.store.resolve(parts[2], user); return {'ok': True}
        if len(parts) == 4 and parts[:2] == ['api', 'jobs'] and parts[3] == 'accept' and method == 'POST':
            return assist.accept(self.store, parts[2], user, body.get('block_ids'), body.get('base_rev'), body.get('edits'))
        if len(parts) == 3 and parts[:2] == ['api', 'jobs'] and method == 'GET':
            key = parts[2]
            if not __import__('re').fullmatch('[0-9a-f]{24}', key): raise KeyError('La sugerencia no existe.')
            # Job envelope preserves ownership even after a worker writes done bytes.
            envelope = self.store.data / 'jobs/queued' / (key + '.json')
            if not envelope.exists(): raise KeyError('La sugerencia no existe.')
            queued = json.loads(envelope.read_text())
            if queued['author'] != user: raise Refused('Solo el autor puede ver sus sugerencias.')
            done = self.store.data / 'jobs/done' / (key + '.json')
            return json.loads(done.read_text()) if done.exists() and done.stat().st_size <= 2*1024*1024 else {'status': 'queued'}
        if path == '/api/issues':
            if method == 'GET': return [issues.get(self.store, p['slug']) for p in self.store.list() if p['kind'] == 'issue']
            if method == 'POST': return issues.create(self.store, user, body.get('issue', body))
        if len(parts) >= 3 and parts[:2] == ['api', 'issues']:
            value = slug(parts[2])
            if len(parts) == 3:
                if method == 'GET': return issues.get(self.store, value)
                if method == 'PUT': return issues.save(self.store, value, user, body.get('base_rev'), body.get('issue'))
            if parts[3:] == ['checks'] and method == 'GET': return issues.checks(self.store, self.preview, value)
            return self.api(method, '/api/pieces/' + '/'.join(parts[2:]), query, body, session)
        if path == '/api/library/briefs' and method == 'GET':
            library = getattr(self.store, 'public_root', self.store.data / 'clone') / 'site/data/stories.v2.json'
            if not library.exists(): return []
            data = json.loads(library.read_text())['stories']
            date = query.get('date', [''])[0]; term = query.get('q', [''])[0].casefold(); cls = query.get('class', [''])[0]
            return [row for row in data if (not date or str(row.get('event_at', row.get('first_published_at', ''))).startswith(date)) and
                    (not term or term in json.dumps(row, ensure_ascii=False).casefold()) and (not cls or row.get('evidence_class') == cls)]
        if len(parts) < 3 or parts[:2] != ['api', 'pieces']: raise KeyError('La página no existe.')
        value = slug(parts[2]); self.store.piece(value); rest = parts[3:]
        if not rest and method == 'GET': return self.store.piece(value)
        if len(rest) == 2 and rest[0] == 'doc':
            loc = locale(rest[1])
            if method == 'GET': return self.store.doc(value, loc)
            if method == 'PUT': return self.store.save(value, loc, user, body.get('base_rev'), body.get('doc'), body.get('cursor', {}))
        if len(rest) == 2 and rest[0] == 'lock':
            if method == 'POST': return self.store.lock(value, locale(rest[1]), user, bool(body.get('takeover', False)))
            if method == 'DELETE': self.store.unlock(value, locale(rest[1]), user); return {'ok': True}
        if rest in (['sources'], ['figures']):
            if method == 'GET': return self.store.resource(value, rest[0])
            if method == 'PUT': return {'data': self.store.resource(value, rest[0], user, body), 'rev': self.store.piece(value)['head_rev']}
        if rest == ['figures', 'upload'] and method == 'POST':
            with self.store.mutex:
                self.store._editable(value); width, height = validate_webp(body); key = 'fig-' + secrets.token_hex(8)
                atomic(self.store.directory(value) / 'figures' / (key + '.webp'), body)
                return {'id': key, 'file': 'figures/' + key + '.webp', 'width': width, 'height': height}
        if len(rest) == 3 and rest[0] == 'locale' and rest[2] == 'state' and method == 'POST':
            state = self.store.locale_state(value, locale(rest[1]), user, body.get('state'), body.get('reviewed', False), body.get('confirmation', ''))
            return {**state, 'rev': self.store.piece(value)['head_rev']}
        if rest == ['translate'] and method == 'POST':
            return translate(self.store, value, user, body.get('base_rev'), replace=body.get('replace') is True)
        if rest == ['distribution'] and method == 'PUT':
            return self.store.distribution(value, user, body.get('base_rev'), body.get('email'))
        if rest == ['versions']:
            if method == 'GET': return self.store.versions(value)
            if method == 'POST': return self.store.checkpoint(value, user, body.get('name'))
        if len(rest) == 3 and rest[0] == 'versions' and rest[2] == 'restore' and method == 'POST': return self.store.restore(value, rest[1], user)
        if rest == ['diff'] and method == 'GET': return self.store.diff(value, query['from'][0], query['to'][0], query.get('loc', ['en'])[0])
        if rest == ['comments']:
            if method == 'GET': return self.store.comments(value)
            if method == 'POST': return self.store.comment(value, body.get('locale'), body.get('block_id'), user, body.get('body'))
        if rest == ['checks'] and method == 'GET': return issues.checks(self.store, self.preview, value) if self.store.piece(value)['kind'] == 'issue' else checks(self.store, self.preview, value)
        if len(rest) == 2 and rest[0] == 'review' and method == 'POST':
            if rest[1] == 'request': return self.publisher.request(value, user)
            if rest[1] == 'approve':
                if not (self.live_enabled or self.dry_run): raise Refused('La publicación en vivo aún no está habilitada.')
                return self.publisher.approve(value, user, body.get('note', '')) and self.publisher.public_status(value)
            if rest[1] == 'changes': return self.publisher.changes(value, user, body.get('note', ''))
        if rest == ['publication'] and method == 'GET': return self.publisher.public_status(value)
        if rest == ['correct'] and method == 'POST': return self.store.amend(value, user, body.get('type'), body.get('note', {}))
        if rest == ['withdraw'] and method == 'POST': return self.store.amend(value, user, 'withdraw', body.get('note', {}), body.get('reason_code'))
        if rest == ['assist'] and method == 'POST':
            if self.store.piece(value)['author'] != user: raise Refused('Solo el autor puede pedir ayuda sobre su borrador.')
            if body.get('kind') not in ('translate', 'cite_check', 'layout_qa', 'dek'): raise ValueError('La sugerencia no es válida.')
            loc = locale(body.get('loc'))
            if body['kind'] == 'layout_qa':
                from .layout_qa import run
                return run(self, value, user)
            heartbeat = self.store.data / 'jobs/worker-heartbeat'
            if not heartbeat.is_file() or self.store.clock() - heartbeat.stat().st_mtime > 10: return {'status': 'no_worker'}
            ident = secrets.token_hex(12)
            envelope = {'id': ident, 'author': user, 'kind': body['kind'], 'slug': value, 'locale': loc, 'rev': self.store.piece(value)['head_rev'], 'doc': self.store.doc(value, self.store.payload(value)['piece']['source_locale'] if body['kind'] == 'translate' else loc)['doc']}
            atomic(self.store.data / 'jobs/queued' / (ident + '.json'), json.dumps(envelope, ensure_ascii=False).encode())
            return {'job_id': ident}
        raise KeyError('La página no existe.')

class Server(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, app):
        if address[0] != '127.0.0.1': raise ValueError('Studio solo puede escuchar en 127.0.0.1.')
        self.app = app; super().__init__(address, Handler)
    def server_close(self):
        self.app.stop.set(); super().server_close()

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup(); self.connection.settimeout(15)
    def log_message(self, *args): pass
    def reply(self, status, body, mime='application/json; charset=utf-8', cookie=None, csp=CSP):
        data = body if isinstance(body, bytes) else json.dumps(localize(body, getattr(self, 'ui_lang', 'es')), ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', mime); self.send_header('Content-Length', str(len(data)))
        self.send_header('Content-Security-Policy', csp); self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff'); self.send_header('Referrer-Policy', 'no-referrer')
        if cookie: self.send_header('Set-Cookie', cookie)
        self.end_headers(); self.wfile.write(data)
    def handle_api(self):
        app = self.server.app; method = self.command; parsed = urlsplit(self.path); path = unquote(parsed.path)
        try:
            if path == '/healthz' and method == 'GET': return self.reply(200, {'ok': True})
            cookies = SimpleCookie(); cookies.load(self.headers.get('Cookie', ''))
            token = cookies[COOKIE].value if COOKIE in cookies else None
            session = app.auth.session(token)
            self.ui_lang = session['ui_lang'] if session else 'es'
            if path == '/api/login' and method == 'POST':
                if self.headers.get('Origin') != app.origin: return self.reply(403, {'error_plain': 'Abre el inicio de sesión desde Studio.'})
            elif not session:
                # The login chrome contains no draft data. Private API, preview
                # and publication assets always require the per-person session.
                candidate = (app.dist / path.lstrip('/')).resolve()
                if method == 'GET' and not path.startswith(('/api/', '/preview/', app.preview.base)) and (path == '/' or candidate.is_relative_to(app.dist.resolve()) and candidate.is_file()):
                    target = app.dist / 'index.html' if path == '/' else candidate
                    if not app.web_ready: return self.reply(503, {'error_plain': 'La interfaz necesita una reconstrucción antes de abrir Studio.'})
                    if target.is_file(): return self.reply(200, target.read_bytes(), mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
                return self.reply(401, {'error_plain': 'Inicia sesión para continuar.'})
            elif method != 'GET' and not app.auth.csrf(session, self.headers.get('X-CSRF-Token'), self.headers.get('Origin'), app.origin):
                return self.reply(403, {'error_plain': 'Recarga Studio antes de continuar.'})
            body = None
            if method != 'GET':
                count = int(self.headers.get('Content-Length', '0')); limit = 15*1024*1024 if path.endswith('/figures/upload') else 2*1024*1024
                if count < 0 or count > limit: return self.reply(413, {'error_plain': 'El archivo es demasiado grande.'})
                raw = self.rfile.read(count)
                if path.endswith('/figures/upload'):
                    if self.headers.get('Content-Type') != 'image/webp': raise ValueError('Sube una imagen WebP.')
                    body = raw
                else: body = json.loads(raw or b'{}')
            if path == '/api/login' and method == 'POST':
                login = app.auth.login(body.get('user'), body.get('password'), self.headers.get('User-Agent', ''), self.headers.get('Tailscale-User-Login', ''))
                if not login: return self.reply(401, {'error_plain': 'No se pudo iniciar sesión. Revisa tus datos o espera 15 minutos.'})
                token = login.pop('token'); return self.reply(200, login, cookie=COOKIE + '=' + token + '; Path=/; Max-Age=' + str(TTL) + '; Secure; HttpOnly; SameSite=Strict')
            if path == '/api/logout' and method == 'POST':
                app.auth.logout(token); return self.reply(200, {'ok': True}, cookie=COOKIE + '=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Strict')
            if path.startswith('/api/'):
                return self.reply(200, app.api(method, path, parse_qs(parsed.query), body, session))
            if method != 'GET': raise KeyError('La página no existe.')
            parts = path.strip('/').split('/')
            if len(parts) == 4 and parts[0] == 'figures':
                value = slug(parts[1]); key = parts[2]
                figure = app.store.resource(value, 'figures').get(key)
                if not figure or parts[3] != 'image.webp': raise KeyError('La figura no existe.')
                root = app.store.directory(value).resolve(); target = (root / figure['file']).resolve()
                if not target.is_relative_to(root) or not target.is_file(): raise KeyError('La figura no existe.')
                return self.reply(200, target.read_bytes(), 'image/webp')
            if len(parts) == 3 and parts[0] == 'preview':
                page = app.preview.page(slug(parts[1]), locale(parts[2]))
                app.preview_sessions[session['id_hash']] = slug(parts[1])
                return self.reply(200, page, 'text/html; charset=utf-8', csp=PREVIEW_CSP)
            if path.startswith(app.preview.base):
                relative = path[len(app.preview.base):]
                value = app.preview_sessions.get(session['id_hash'])
                if not value: raise KeyError('El recurso no existe.')
                root = app.preview.build(value); target = (root / relative).resolve()
            else:
                if not app.web_ready: return self.reply(503, {'error_plain': 'La interfaz necesita una reconstrucción antes de abrir Studio.'})
                root = app.dist.resolve(); target = (root / path.lstrip('/')).resolve()
                if path == '/' or not target.suffix: target = root / 'index.html'
            if not target.is_relative_to(root.resolve()) or not target.is_file(): raise KeyError('La página no existe.')
            mime = mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            return self.reply(200, target.read_bytes(), mime)
        except Conflict as exc: self.reply(409, {**exc.current, 'error_plain': 'Hay una versión más reciente. Compara las versiones antes de guardar.'})
        except Locked as exc: self.reply(409, {'error_plain': ('Javier' if exc.owner == 'javier' else 'Matías') + ' está editando.', 'by': exc.owner})
        except (Refused, UnknownEffect) as exc: self.reply(409, {'error_plain': str(exc)})
        except RendererUnavailable as exc: self.reply(503, {'error_plain': str(exc)})
        except TranslationError as exc: self.reply(400, {'error_plain': str(exc)})
        except (ValueError, TypeError, AttributeError, OverflowError): self.reply(400, {'error_plain': 'Revisa los datos enviados.'})
        except KeyError: self.reply(404, {'error_plain': 'La página no existe.'})
        except Exception: self.reply(503, {'error_plain': 'No se pudo completar la operación. Tu última versión guardada sigue disponible.'})
    do_GET = handle_api
    do_POST = handle_api
    do_PUT = handle_api
    do_DELETE = handle_api
