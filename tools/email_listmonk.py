#!/usr/bin/env python3
"""Listmonk delivery boundary: durable campaigns, explicit consent, no translation.

The service owns the only campaign writer. SQLite plus an OS lock spans restarts
and overlapping requests. An unacknowledged create/start is reconciled against
Listmonk; absence of acknowledgement never grants permission to send again.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import hmac
import json
import re
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tools.email_dispatch import eligibility
from tools.email_render import localized_story, render_daily_email

LOCALES = ('en', 'es-419', 'zh-Hans')
MAX_RESPONSE = 8_000_000
TEMPLATE_NAME = 'FCMO Diario raw HTML'
TEMPLATE_BODY = '{{ template "content" . }}'


class DeliveryError(RuntimeError):
    pass


def clean_origin(value: str) -> str:
    p = urllib.parse.urlsplit(value)
    if (not p.hostname or p.username or p.password or p.query or p.fragment
            or p.path not in ('', '/') or
            (p.scheme != 'https' and not (p.scheme == 'http' and p.hostname in ('127.0.0.1', 'localhost', '::1')))):
        raise ValueError('email URL must be a clean HTTPS or loopback origin')
    return value.rstrip('/')


@dataclass(frozen=True)
class MailConfig:
    listmonk_url: str
    username: str
    api_key: str
    public_url: str
    from_email: str
    postal_address: str
    site_url: str
    consent_key: str

    def __post_init__(self):
        clean_origin(self.listmonk_url)
        clean_origin(self.public_url)
        if not all((self.username, self.api_key, self.from_email, self.postal_address.strip())):
            raise ValueError('incomplete email configuration')
        if len(self.consent_key) < 32 or '\n' in self.from_email or '\r' in self.from_email:
            raise ValueError('invalid email configuration')

    @classmethod
    def from_env(cls, env):
        return cls(env.get('LISTMONK_URL', 'http://127.0.0.1:9000'), env['LISTMONK_API_USER'],
                   env['LISTMONK_API_KEY'], env['FCMO_EMAIL_PUBLIC_URL'], env['FCMO_EMAIL_FROM'],
                   env['FCMO_EMAIL_POSTAL_ADDRESS'],
                   env.get('FCMO_SITE_URL', 'https://fcmo-ai.github.io/FCMO-AI-Newsletter'),
                   env['FCMO_EMAIL_CONSENT_KEY'])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ListmonkClient:
    def __init__(self, config: MailConfig, timeout: float = 25):
        self.config, self.timeout = config, timeout

    def request(self, method, path, payload=None, *, public=False):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if not public:
            credentials = (self.config.username + ':' + self.config.api_key).encode()
            headers['Authorization'] = 'Basic ' + base64.b64encode(credentials).decode()
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        req = urllib.request.Request(self.config.listmonk_url.rstrip('/')+'/api/'+path,
                                     data=body, headers=headers, method=method)
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE+1)
            if len(raw) > MAX_RESPONSE: raise DeliveryError('provider_response_too_large')
            doc = json.loads(raw)
            if not isinstance(doc, dict) or 'data' not in doc:
                raise DeliveryError('invalid_provider_response')
            return doc['data']
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            # Bodies/URLs may contain credentials or subscriber data; never log.
            raise DeliveryError('unknown_provider_outcome') from exc

    def lists(self):
        result = self.request('GET', 'lists?per_page=all')
        selected = {}
        for locale in LOCALES:
            matches = [v for v in result['results'] if v['name'] == 'diario-'+locale]
            if len(matches) != 1 or matches[0]['optin'] != 'double' or matches[0]['type'] != 'public':
                raise DeliveryError('missing_or_unsafe_locale_list')
            selected[locale] = matches[0]
        return selected

    def find_campaign(self, name):
        data = self.request('GET', 'campaigns?'+urllib.parse.urlencode({'query':name, 'per_page':'all'}))
        matches = [v for v in data['results'] if v['name'] == name]
        if len(matches) > 1: raise DeliveryError('duplicate_campaign_requires_reconcile')
        return matches[0] if matches else None

    def campaign_template(self):
        matches = [v for v in self.request('GET','templates') if v['name']==TEMPLATE_NAME]
        if len(matches)!=1 or matches[0]['type']!='campaign' or matches[0]['body'].strip()!=TEMPLATE_BODY:
            raise DeliveryError('missing_or_modified_email_template')
        return matches[0]['id']


def literal(value: str) -> str:
    # Go text-template syntax must remain inert in subject/plain-text inputs.
    return value.replace('{{', '{\u200b{').replace('}}', '}\u200b}')


class DiarioService:
    def __init__(self, config: MailConfig, state: Path, *, client=None):
        self.config = config
        self.client = client or ListmonkClient(config)
        state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state = state
        self.thread_lock = threading.RLock()
        with closing(sqlite3.connect(state)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS dispatch (name TEXT PRIMARY KEY, phase TEXT NOT NULL, campaign_id INTEGER, digest TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS consent (email_hash TEXT, ip_hash TEXT, locale TEXT, at INTEGER, version TEXT, accepted INTEGER)')
        state.chmod(0o600)

    def dispatch(self, stories, status, *, live_verified: bool, now: datetime, locale=None):
        requested_locale = locale
        decision = eligibility(stories, status, live_verified=live_verified, now=now)
        if decision.action == 'SKIP': return {'action':'SKIP', 'reason':decision.reason}
        chosen = [v['story'] for v in decision.items]
        # Require the same canonical IDs in all three editions. A missing native
        # field must stop the entire operation before the first campaign begins.
        for locale in LOCALES:
            if any(localized_story(v, locale) is None for v in chosen):
                raise ValueError('selected edition lacks complete native '+locale)
        lists = self.client.lists()
        template_id = self.client.campaign_template()
        rendered = {locale:render_daily_email(chosen, status['edition_date'], locale=locale,
                    site_url=self.config.site_url, postal_address=self.config.postal_address,
                    preferences_url='{{ UnsubscribeURL }}?manage=true',
                    unsubscribe_url='{{ UnsubscribeURL }}') for locale in LOCALES}
        if requested_locale is not None:
            if requested_locale not in LOCALES: raise ValueError('unsupported_email_locale')
            rendered = {requested_locale: rendered[requested_locale]}
        queued = []
        with self.thread_lock, self.state.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with closing(sqlite3.connect(self.state)) as db, db:
                for locale, mail in rendered.items():
                    name = 'diario-'+status['edition_date']+'-'+locale
                    payload = {'name':name, 'subject':literal(mail.subject), 'type':'regular',
                               'content_type':'html', 'body':mail.html, 'altbody':literal(mail.text).replace('{\u200b{ UnsubscribeURL }\u200b}', '{{ UnsubscribeURL }}'),
                               'from_email':self.config.from_email, 'lists':[lists[locale]['id']],
                               'tags':['fcmo-diario', name], 'template_id':template_id}
                    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                    saved = db.execute('SELECT phase,campaign_id,digest FROM dispatch WHERE name=?', (name,)).fetchone()
                    campaign = self.client.find_campaign(name)
                    if campaign is None:
                        if saved: raise DeliveryError('missing_campaign_requires_reconcile')
                        db.execute('INSERT INTO dispatch VALUES (?,?,?,?)', (name,'creating',None,digest)); db.commit()
                        campaign = self.client.request('POST', 'campaigns', payload)
                        db.execute('UPDATE dispatch SET phase=?,campaign_id=? WHERE name=?', ('draft',campaign['id'],name)); db.commit()
                    elif saved and saved[1] is not None and saved[1] != campaign['id']:
                        raise DeliveryError('campaign_identity_requires_reconcile')
                    # A started, completed or scheduled campaign is never sent again.
                    if campaign['status'] in ('running','finished','scheduled'):
                        db.execute('INSERT OR REPLACE INTO dispatch VALUES (?,?,?,?)', (name,campaign['status'],campaign['id'], saved[2] if saved else digest)); db.commit()
                        continue
                    if campaign['status'] != 'draft' or campaign.get('started_at') or campaign.get('sent',0):
                        raise DeliveryError('campaign_state_requires_reconcile')
                    if saved and saved[2] != digest: raise DeliveryError('edition_content_changed_requires_reconcile')
                    # An existing draft must be exactly the candidate we intend.
                    for key in ('body','subject','from_email','content_type'):
                        if campaign.get(key) != payload[key]: raise DeliveryError('draft_content_requires_reconcile')
                    if campaign.get('template_id') != template_id: raise DeliveryError('draft_template_requires_reconcile')
                    target_ids = [v['id'] if isinstance(v,dict) else v for v in campaign['lists']]
                    if target_ids != payload['lists']: raise DeliveryError('draft_lists_requires_reconcile')
                    if saved and saved[0] == 'starting': raise DeliveryError('unknown_start_requires_reconcile')
                    db.execute('INSERT OR REPLACE INTO dispatch VALUES (?,?,?,?)', (name,'starting',campaign['id'],digest)); db.commit()
                    self.client.request('PUT', f"campaigns/{campaign['id']}/status", {'status':'running'})
                    observed = self.client.request('GET', f"campaigns/{campaign['id']}")
                    if observed['status'] not in ('running','finished'): raise DeliveryError('unconfirmed_start_requires_reconcile')
                    db.execute('UPDATE dispatch SET phase=? WHERE name=?', (observed['status'],name)); db.commit()
                    queued.append(locale)
        return {'action':'QUEUED' if queued else 'SKIP', 'reason':'campaigns_started' if queued else 'already_dispatched', 'locales':queued, 'edition':status['edition_date']}

    def subscribe(self, email, locale, consent, ip, now):
        if locale not in LOCALES or consent is not True or not isinstance(email,str) or not re.fullmatch(r'[^\s@<>]{1,64}@[^\s@<>]{1,190}\.[^\s@<>]{2,63}',email):
            raise ValueError('invalid_signup_or_missing_consent')
        email = email.strip().lower()
        def hashed(value): return hmac.new(self.config.consent_key.encode(),value.encode(),hashlib.sha256).hexdigest()
        email_hash, ip_hash, at = hashed(email), hashed(ip), int(now.timestamp())
        with self.thread_lock, closing(sqlite3.connect(self.state)) as db, db:
            # Keep raw contact data in Listmonk alone. 30-day unconfirmed consent
            # receipts/rate keys; opt-in confirmation lives in Listmonk metadata.
            db.execute('DELETE FROM consent WHERE at < ?', (at-30*86400,))
            n = db.execute('SELECT COUNT(*) FROM consent WHERE email_hash=? AND at>?', (email_hash,at-3600)).fetchone()[0]
            ips = db.execute('SELECT COUNT(*) FROM consent WHERE ip_hash=? AND at>?', (ip_hash,at-3600)).fetchone()[0]
            if n >= 2 or ips >= 5: raise DeliveryError('signup_rate_limited')
            db.execute('INSERT INTO consent VALUES (?,?,?,?,?,?)', (email_hash,ip_hash,locale,at,'email-consent-v1',0)); db.commit()
            selected = self.client.lists()[locale]
            response = self.client.request('POST', 'public/subscription',
                        {'email':email, 'name':'', 'list_uuids':[selected['uuid']]}, public=True)
            if response.get('has_optin') is not True: raise DeliveryError('double_optin_not_confirmed')
            db.execute('UPDATE consent SET accepted=1 WHERE email_hash=? AND at=?', (email_hash,at))
        return {'action':'CONFIRMATION_PENDING'}
