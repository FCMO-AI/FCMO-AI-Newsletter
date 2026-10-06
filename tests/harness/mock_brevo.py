"""Synthetic Brevo v3 boundary; deliberately not a live API recording."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs


class MockBrevo:
    def __init__(self):
        self.campaigns, self.calls, self.failures = [], [], []
        self.lose_create = self.lose_send = False
        self.send_status = 'queued'
        self.counts = {21: 1, 22: 1, 23: 1}
        self.contacts = [{'id': 1, 'email': 'reader@example.org', 'emailBlacklisted': False,
                          'listIds': [21, 22, 23], 'attributes': {'DOI': True},
                          'createdAt': '2026-10-05T12:00:00Z'}]
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def respond(self, code, doc=None):
                data = b'' if doc is None else json.dumps(doc).encode()
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers(); self.wfile.write(data)
            def handle_request(self):
                url = urlsplit(self.path); path = url.path
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'null')
                owner.calls.append((self.command, path, payload, self.headers.get('api-key')))
                if self.headers.get('api-key') != 'synthetic-key': return self.respond(401, {})
                if owner.failures and owner.failures[0][0] == self.command:
                    _, code = owner.failures.pop(0); return self.respond(code, {})
                if path == '/v3/emailCampaigns' and self.command == 'POST':
                    campaign = dict(payload, id=len(owner.campaigns)+1, status='draft')
                    campaign['recipients'] = {'lists': payload['recipients']['listIds']}
                    owner.campaigns.append(campaign)
                    if owner.lose_create:
                        owner.lose_create = False; return self.respond(503, {})
                    return self.respond(201, {'id': campaign['id']})
                if path.startswith('/v3/emailCampaigns/'):
                    campaign = next((v for v in owner.campaigns if v['id'] == int(path.split('/')[3])), None)
                    if campaign is None: return self.respond(404, {})
                    if path.endswith('/sendNow') and self.command == 'POST':
                        campaign['status'] = owner.send_status
                        if owner.lose_send:
                            owner.lose_send = False; return self.respond(503, {})
                        return self.respond(204)
                    return self.respond(200, campaign)
                if path.startswith('/v3/contacts/lists/'):
                    identity = int(path.rsplit('/', 1)[1])
                    if identity not in owner.counts: return self.respond(404, {})
                    return self.respond(200, {'id': identity, 'totalSubscribers': owner.counts[identity]})
                offset = int(parse_qs(url.query).get('offset', ['0'])[0])
                if path == '/v3/emailCampaigns':
                    # Listing intentionally omits detail; the adapter must read it.
                    rows = [{'id': v['id'], 'name': v['name']} for v in owner.campaigns]
                    return self.respond(200, {'campaigns': rows[offset:offset+1], 'count': len(rows)})
                if path == '/v3/contacts':
                    return self.respond(200, {'contacts': owner.contacts[offset:offset+1], 'count': len(owner.contacts)})
                return self.respond(404, {})
            do_GET = handle_request
            do_POST = handle_request
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port) + '/v3'
    def __enter__(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start(); return self
    def __exit__(self, *args):
        self.server.shutdown(); self.thread.join(); self.server.server_close()
