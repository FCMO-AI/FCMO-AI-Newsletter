"""Content-free lifetime intents and observations on a dedicated public branch.

Only explicit JSON projection is accepted. Writes use the Contents API SHA
precondition. Credentials never enter the JSON, redirects or error messages.
"""
import base64
import json
import re
import urllib.error
import urllib.request

from tools.email_listmonk import NoRedirect, DeliveryError
from tools.email_intent import LIMIT
from tools.email_providers import LOCALES

BRANCH = 'email-dispatch-state'
SCHEMA = 'fcmo-piece-email-state-v1'


def validate(state, provider):
    if (not isinstance(state, dict) or set(state) != {'schema', 'provider', 'keys', 'records'}
        or state['schema'] != SCHEMA or state['provider'] != provider
        or not isinstance(state['keys'], list) or not isinstance(state['records'], list)):
        raise ValueError('invalid_piece_email_state_or_provider_changed')
    pattern = r'fcmo-piece(?:-test)?:FCMO-P-[0-9a-f]{12}:(en|es-419|zh-Hans)'
    if len(set(state['keys'])) != len(state['keys']) or any(not re.fullmatch(pattern, key) for key in state['keys']):
        raise ValueError('invalid_piece_state_keys')
    seen = set()
    for row in state['records']:
        if not isinstance(row, dict) or set(row) != {'piece_id', 'locale', 'state', 'broadcast_id', 'timestamp'}:
            raise ValueError('invalid_piece_public_record')
        if (not re.fullmatch(r'FCMO-P-[0-9a-f]{12}', row['piece_id']) or row['locale'] not in LOCALES
            or row['state'] not in ('PENDING', 'QUEUED', 'BLOCKED_RECONCILE', 'SKIPPED_UNREVIEWED', 'SKIPPED_NOT_READY')
            or (row['broadcast_id'] is not None and (type(row['broadcast_id']) is not int or row['broadcast_id'] <= 0))
            or (row['state'] == 'QUEUED' and row['broadcast_id'] is None)
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z', row['timestamp'])):
            raise ValueError('invalid_piece_public_record')
        key = row['piece_id'], row['locale']
        if key in seen: raise ValueError('duplicate_piece_public_record')
        seen.add(key)


class StateStore:
    def __init__(self, env, *, source_commit, request=None):
        self.repository = env.get('GITHUB_REPOSITORY', '')
        self.token = env.get('GH_TOKEN', '')
        self.provider = env.get('FCMO_EMAIL_PROVIDER', 'kit')
        if (not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', self.repository) or not self.token
            or self.provider not in ('kit', 'brevo', 'fake', 'listmonk')
            or not re.fullmatch(r'[0-9a-f]{40}', source_commit)):
            raise ValueError('piece_state_configuration_required')
        self.source_commit = source_commit
        self.test = env.get('FCMO_EMAIL_NAMESPACE') == 'fcmo-diario-test'
        self.path = 'dispatch-test.json' if self.test else 'dispatch.json'
        self.request = request or self._request

    def _request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request('https://api.github.com/repos/' + self.repository + '/' + path,
            method=method, data=body, headers={'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json', 'User-Agent': 'FCMO-Piece-Email-State'})
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
                raw = response.read(LIMIT + 1)
            if len(raw) > LIMIT: raise ValueError('piece_state_response_too_large')
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code == 404: return None
            raise DeliveryError('piece_state_write_or_read_unconfirmed') from None
        except (OSError, ValueError):
            raise DeliveryError('piece_state_write_or_read_unconfirmed') from None

    def read(self):
        branch = self.request('GET', 'git/ref/heads/' + BRANCH)
        if branch is None:
            # Only create the dedicated state branch, never change main or LKG.
            self.request('POST', 'git/refs', {'ref': 'refs/heads/' + BRANCH, 'sha': self.source_commit})
            if self.request('GET', 'git/ref/heads/' + BRANCH) is None:
                raise DeliveryError('piece_state_branch_unconfirmed')
        doc = self.request('GET', 'contents/' + self.path + '?ref=' + BRANCH)
        if doc is None:
            return {'schema': SCHEMA, 'provider': self.provider, 'keys': [], 'records': []}, None
        if doc.get('encoding') != 'base64': raise ValueError('invalid_piece_state_encoding')
        state = json.loads(base64.b64decode(doc['content']))
        validate(state, self.provider)
        expected_prefix = 'fcmo-piece-test:' if self.test else 'fcmo-piece:'
        if any(not key.startswith(expected_prefix) for key in state['keys']):
            raise ValueError('mixed_piece_seed_and_production_keys')
        return state, doc['sha']

    def write(self, state, sha):
        validate(state, self.provider)
        payload = {'message': 'Record content-free piece email state', 'branch': BRANCH,
                   'content': base64.b64encode((json.dumps(state, sort_keys=True) + '\n').encode()).decode()}
        if sha is not None: payload['sha'] = sha
        result = self.request('PUT', 'contents/' + self.path, payload)
        if not result or not result.get('content', {}).get('sha'):
            raise DeliveryError('piece_state_write_unconfirmed')
        # Read back the exact saved projection before proceeding to mail.
        observed, observed_sha = self.read()
        if observed != state or observed_sha != result['content']['sha']:
            raise DeliveryError('piece_state_readback_changed')
        return observed_sha
