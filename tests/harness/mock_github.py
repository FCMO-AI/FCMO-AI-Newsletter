"""Offline GitHub/Pages double with observed state and lost-response injection.

Only loopback sockets are used. Tokens are conspicuously fake fixture identifiers.
"""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
from urllib.parse import parse_qs, urlsplit

class MockGitHub:
    def __init__(self):
        self.requests = []; self.refs = {}; self.prs = {}; self.reviews = {}; self.pushes = []
        self.check = 'success'; self.protection = True; self.merge_refused = False; self.live_id = None; self.live_status = 200
        self.drop_after = None; self.fail_before = None; self.pages_ready = True
    def __enter__(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def run(self):
                parsed = urlsplit(self.path); path = parsed.path; query = parse_qs(parsed.query)
                token = self.headers.get('Authorization', '').removeprefix('Bearer ')
                actor = {'fixture-javier': 'javier', 'fixture-matias': 'matias'}.get(token)
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'{}')
                owner.requests.append({'method': self.command, 'path': path, 'actor': actor, 'body': body})
                status, value = owner.dispatch(actor, self.command, path, query, body)
                if owner.drop_after == (self.command, path):
                    owner.drop_after = None; self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR); self.connection.close(); return
                data = value if isinstance(value, bytes) else json.dumps(value).encode()
                self.send_response(status); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
            do_GET = run; do_POST = run; do_PUT = run; do_PATCH = run
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)
        return self
    def __exit__(self, *args):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
    def count(self, method, path): return sum(r['method'] == method and r['path'].endswith(path) for r in self.requests)
    def dispatch(self, actor, method, path, query, body):
        if path.startswith('/live/'):
            return self.live_status, ('<!doctype html><article data-piece-id="' + (self.live_id or 'wrong') + '">Visible</article>').encode()
        if not actor: return 401, {'message': 'fixture credential required'}
        if self.fail_before == (method, path): return 503, {}
        if path == '/user': return 200, {'login': actor}
        prefix = '/repos/FCMO-AI/FCMO-AI-Newsletter'; route = path.removeprefix(prefix)
        if route.startswith('/git/ref/heads/'):
            branch = route.removeprefix('/git/ref/heads/')
            return (200, {'object': {'sha': self.refs[branch]}}) if branch in self.refs else (404, {})
        if route == '/git/refs' and method == 'POST':
            branch = body['ref'].removeprefix('refs/heads/')
            if not branch.startswith('studio/'): return 403, {}
            self.refs[branch] = body['sha']; self.pushes.append({'actor': actor, **body}); return 201, {'object': {'sha': body['sha']}}
        if route == '/rules/branches/main':
            if not self.protection: return 200, []
            return 200, [{'type': 'pull_request', 'ruleset_id': 7, 'parameters': {'required_approving_review_count': 1, 'require_code_owner_review': True, 'require_last_push_approval': True, 'dismiss_stale_reviews_on_push': True}},
                         {'type': 'required_status_checks', 'ruleset_id': 7, 'parameters': {'strict_required_status_checks_policy': True, 'required_status_checks': [{'context': 'publish-gate'}]}}]
        if route == '/rulesets/7': return 200, {'enforcement': 'active', 'bypass_actors': []}
        if route == '/pulls':
            if method == 'GET': return 200, [copy.deepcopy(p) for p in self.prs.values() if p['head']['ref'] == query['head'][0].split(':', 1)[1]]
            number = len(self.prs) + 1; branch = body['head']
            if branch not in self.refs: return 422, {}
            self.prs[number] = {'number': number, 'user': {'login': actor}, 'head': {'ref': branch, 'sha': self.refs[branch]}, 'state': 'open', 'merged': False, 'merge_commit_sha': None}
            return 201, copy.deepcopy(self.prs[number])
        if route.startswith('/pulls/'):
            bits = route.strip('/').split('/'); number = int(bits[1]); pr = self.prs[number]
            if len(bits) == 2:
                if method == 'PATCH': pr['state'] = body['state']
                return 200, copy.deepcopy(pr)
            if bits[2] == 'reviews':
                if method == 'GET': return 200, copy.deepcopy(self.reviews.get(number, []))
                if actor == pr['user']['login']: return 422, {}
                row = {'state': 'APPROVED', 'user': {'login': actor}, 'commit_id': body['commit_id']}
                self.reviews.setdefault(number, []).append(row); return 200, row
            if bits[2] == 'merge':
                if self.merge_refused or not self.protection or body['sha'] != pr['head']['sha']: return 403, {}
                if not any(r['user']['login'] != pr['user']['login'] and r['commit_id'] == pr['head']['sha'] for r in self.reviews.get(number, [])): return 403, {}
                pr['merged'] = True; pr['state'] = 'closed'; pr['merge_commit_sha'] = 'f'*40
                return 200, {'merged': True, 'sha': pr['merge_commit_sha']}
        if route.startswith('/commits/') and route.endswith('/check-runs'):
            return 200, {'check_runs': [{'id': 1, 'name': 'publish-gate', 'status': 'completed' if self.check != 'pending' else 'in_progress', 'conclusion': self.check}]}
        if route == '/actions/workflows/pages.yml/runs':
            return 200, {'workflow_runs': [{'id': 8, 'head_sha': 'f'*40, 'event': 'push', 'status': 'completed', 'conclusion': 'success'}] if self.pages_ready else []}
        if route == '/actions/workflows/pages.yml/dispatches': return 204, b''
        return 404, {}
