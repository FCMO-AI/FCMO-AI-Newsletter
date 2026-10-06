"""Loopback Kit fixture incorporating the operator's 2026-10-05 live probe."""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

class MockKit:
    def __init__(self):
        self.broadcasts, self.calls, self.queries, self.failures = [], [], [], []
        self.lose_create = False
        self.tags = [{'id': n, 'name': name} for n, name in zip((11,12,13),
                     ('newsletter-en','newsletter-es-419','newsletter-zh-Hans'))]
        self.subscriber_tags = {}
        self.form_members = {}
        self.tag_listing_lags = True
        self.hidden_tag_names = set()
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
                self.end_headers(); self.wfile.write(data)
            def handle_request(self):
                path = urlsplit(self.path).path
                query = parse_qs(urlsplit(self.path).query)
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or b'null')
                owner.calls.append((self.command, path, payload, self.headers.get('X-Kit-Api-Key')))
                owner.queries.append(query)
                if self.headers.get('X-Kit-Api-Key') != 'synthetic-key':
                    return self.respond(401, {'errors': ['unauthorized']})
                if owner.failures and owner.failures[0][0] == self.command and (len(owner.failures[0])==2 or owner.failures[0][2]==path):
                    failure = owner.failures.pop(0)
                    return self.respond(failure[1], {'errors': ['fixture failure']})
                if path == '/v4/broadcasts' and self.command == 'POST':
                    filters = payload.get('subscriber_filter')
                    items = filters if isinstance(filters,list) else [filters]
                    if any(v.get('type') not in ('tag','segment') for item in items for v in item.get('all',[])):
                        return self.respond(422, {'errors': ['Only `segment` or `tag` filters allowed']})
                    if not isinstance(filters,list): return self.respond(422, {'errors':['subscriber_filter must be a list']})
                    doc = dict(payload, id=len(owner.broadcasts)+1)
                    owner.broadcasts.append(doc)
                    if owner.lose_create:
                        owner.lose_create = False
                        return self.respond(503, {'errors': ['lost acknowledgement']})
                    return self.respond(201, {'broadcast': doc})
                if path == '/v4/tags' and self.command == 'POST':
                    existing = next((v for v in owner.tags if v['name'] == payload['name']), None)
                    if existing: return self.respond(200, {'tag':existing})
                    tag = {'id':max([v['id'] for v in owner.tags]+[10])+1, 'name':payload['name']}
                    owner.tags.append(tag)
                    return self.respond(201, {'tag':tag})
                match = re.fullmatch(r'/v4/tags/(\d+)/subscribers/(\d+)',path)
                if match and self.command == 'POST':
                    tag, subscriber = map(int,match.groups())
                    assigned = owner.subscriber_tags.setdefault(subscriber,set())
                    code = 200 if tag in assigned else 201
                    assigned.add(tag)
                    return self.respond(code, {'subscriber':next(v for v in owner.subscribers if v['id']==subscriber)})
                match = re.fullmatch(r'/v4/subscribers/(\d+)/tags',path)
                if match:
                    values, field = [v for v in owner.tags if v['id'] in owner.subscriber_tags.get(int(match[1]),set())], 'tags'
                elif path == '/v4/broadcasts': values, field = owner.broadcasts, 'broadcasts'
                elif path == '/v4/subscribers': values, field = owner.subscribers, 'subscribers'
                elif path.startswith('/v4/forms/'):
                    form = int(path.split('/')[3])
                    values, field = owner.form_members.get(form,owner.subscribers), 'subscribers'
                elif path.startswith('/v4/tags/'):
                    tag = int(path.split('/')[3])
                    values = [] if owner.tag_listing_lags else [v for v in owner.subscribers if tag in owner.subscriber_tags.get(v['id'],set())]
                    field = 'subscribers'
                elif path == '/v4/tags': values, field = [v for v in owner.tags if v['name'] not in owner.hidden_tag_names], 'tags'
                elif path == '/v4/forms':
                    values, field = [{'id': n} for n in (101,102,103,10007761,10007787,10007798)], 'forms'
                else: return self.respond(404, {})
                if field=='subscribers' and 'status' in query:
                    values = [v for v in values if v['state']==query['status'][0]]
                # One record per page forces real cursor traversal on every endpoint.
                start = int(query.get('after',['0'])[0]); more = start+1 < len(values)
                return self.respond(200, {field: values[start:start+1], 'pagination': {
                    'has_next_page': more, 'end_cursor': str(start+1) if more else None}})
            do_GET = handle_request
            do_POST = handle_request
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.url = 'http://127.0.0.1:'+str(self.server.server_port)+'/v4'
    def __enter__(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start(); return self
    def __exit__(self, *args):
        self.server.shutdown(); self.thread.join(); self.server.server_close()
