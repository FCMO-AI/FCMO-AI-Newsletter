"""Loopback fixture of assumed Kit v4 shapes, not a live API recording."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

class MockKit:
    def __init__(self):
        self.broadcasts = []
        self.calls = []
        self.failures = []
        self.lose_create = False
        self.subscribers = [{'id': 1, 'email_address': 'reader@example.org', 'state': 'active',
                             'fields': {}, 'created_at': '2026-10-05T12:00:00Z'}]
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def respond(self, code, doc):
                data = json.dumps(doc).encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            def handle_request(self):
                path = urlsplit(self.path).path
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'null')
                owner.calls.append((self.command, path, payload, self.headers.get('X-Kit-Api-Key')))
                if self.headers.get('X-Kit-Api-Key') != 'synthetic-key':
                    return self.respond(401, {'errors': ['unauthorized']})
                if owner.failures and owner.failures[0][0] == self.command:
                    _, code = owner.failures.pop(0)
                    return self.respond(code, {'errors': ['fixture failure']})
                if path == '/v4/broadcasts' and self.command == 'POST':
                    doc = dict(payload, id=len(owner.broadcasts)+1)
                    owner.broadcasts.append(doc)
                    if owner.lose_create:
                        owner.lose_create = False
                        return self.respond(503, {'errors': ['lost acknowledgement']})
                    return self.respond(201, {'broadcast': doc})
                cursor = parse_qs(urlsplit(self.path).query).get('after', [''])[0]
                if path == '/v4/broadcasts':
                    values, field = owner.broadcasts, 'broadcasts'
                elif path == '/v4/subscribers' or path.startswith(('/v4/tags/', '/v4/forms/')):
                    values, field = owner.subscribers, 'subscribers'
                elif path == '/v4/tags':
                    values, field = [{'id': n} for n in (11, 12, 13)], 'tags'
                elif path == '/v4/forms':
                    values, field = [{'id': n} for n in (101, 102, 103)], 'forms'
                else: return self.respond(404, {})
                # One record per page forces real cursor traversal.
                if field in ('tags','forms'):
                    return self.respond(200,{field:values,'pagination':{'has_next_page':False,'end_cursor':None}})
                start = int(cursor or 0)
                more = start+1 < len(values)
                return self.respond(200, {field: values[start:start+1], 'pagination': {
                    'has_next_page': more, 'end_cursor': str(start+1) if more else None}})
            do_GET = handle_request
            do_POST = handle_request
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = 'http://127.0.0.1:'+str(self.server.server_port)+'/v4'
    def __enter__(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self
    def __exit__(self, *args):
        self.server.shutdown(); self.thread.join(); self.server.server_close()
