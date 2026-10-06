"""Brevo v3 hosted-DOI/list-campaign adapter, with offline-assumed API shapes.

Campaign creation and sendNow are separate mutations. Neither is retried.
Only a re-read campaign in queued/sent/inProcess state confirms scheduling.
A previous intent or an uncertain draft requires operator reconciliation.
"""
import fcntl
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from tools.email_listmonk import DeliveryError, NoRedirect
from . import LOCALES, SubscribeForm, public_notice

PRIVACY_NOTICE = 'email-privacy-brevo.json'
DAILY_CAP = 300


def configuration(env, name):
    try:
        doc = json.loads(env.get(name) or '{}')
    except (ValueError, TypeError):
        raise ValueError('invalid_brevo_configuration') from None
    if not isinstance(doc, dict): raise ValueError('invalid_brevo_configuration')
    return doc


def public_form(env, locale):
    if env.get('FCMO_EMAIL_ENABLED') != 'true' or env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true':
        raise ValueError('email_signup_inactive')
    config = configuration(env, 'FCMO_EMAIL_PUBLIC_CONFIG')
    forms = config.get('forms', {})
    if not isinstance(forms, dict): raise ValueError('invalid_brevo_public_form')
    action = forms.get(locale, '')
    if not isinstance(action, str): raise ValueError('invalid_brevo_public_form')
    parts = urllib.parse.urlsplit(action)
    # Public opaque hosted form token is expected; API credentials are never public.
    if (parts.scheme != 'https' or not parts.hostname or not parts.hostname.endswith('.sibforms.com')
        or parts.username or parts.password or parts.port not in (None, 443)
        or parts.query or parts.fragment or not re.fullmatch(r'/serve/[A-Za-z0-9_-]+', parts.path)):
        raise ValueError('invalid_brevo_public_form')
    return SubscribeForm(action, 'EMAIL', True, public_notice(env.get('FCMO_EMAIL_PRIVACY_URL', '')))


class BrevoProvider:
    name = 'brevo'
    requires_intent = True

    def __init__(self, env, *, base_url='https://api.brevo.com/v3', intent=None, sleep=time.sleep):
        parts = urllib.parse.urlsplit(base_url)
        if base_url != 'https://api.brevo.com/v3' and not (
            parts.scheme == 'http' and parts.hostname == '127.0.0.1' and parts.path == '/v3'
            and not parts.username and not parts.password and not parts.query and not parts.fragment):
            raise ValueError('invalid_brevo_api_origin')
        self.env, self.base_url, self.sleep = dict(env), base_url, sleep
        config = configuration(env, 'FCMO_EMAIL_PROVIDER_CONFIG')
        self.api_key = config.get('api_key')
        if not isinstance(self.api_key, str) or not self.api_key.strip(): raise ValueError('missing_brevo_api_key')
        self.lists = config.get('list_ids')
        if (not isinstance(self.lists, dict) or set(self.lists) != set(LOCALES)
            or any(type(v) is not int or v < 1 for v in self.lists.values())
            or len(set(self.lists.values())) != 3):
            raise ValueError('invalid_brevo_locale_lists')
        self.intent = Path(intent or env.get('FCMO_EMAIL_INTENT', 'email-intent.json'))

    def subscribe_form(self, locale): return public_form(self.env, locale)

    def request(self, method, path, payload=None):
        raw = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        req = urllib.request.Request(self.base_url+'/'+path, data=raw, method=method,
            headers={'api-key': self.api_key, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        for attempt in range(3 if method == 'GET' else 1):
            try:
                with urllib.request.build_opener(NoRedirect).open(req, timeout=25) as response:
                    body = response.read(8_000_001)
                    if response.status == 204 and method == 'POST': return {}
                if len(body) > 8_000_000: raise DeliveryError('brevo_response_too_large')
                doc = json.loads(body)
                if not isinstance(doc, dict): raise DeliveryError('invalid_brevo_response')
                return doc
            except urllib.error.HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if method == 'GET' and retryable and attempt < 2:
                    self.sleep(2**attempt); continue
                raise DeliveryError('brevo_request_failed_or_outcome_unknown') from None
            except (urllib.error.URLError, OSError, ValueError):
                if method == 'GET' and attempt < 2:
                    self.sleep(2**attempt); continue
                raise DeliveryError('brevo_request_failed_or_outcome_unknown') from None
        raise DeliveryError('brevo_retry_exhausted')

    def pages(self, path, field):
        offset, total, seen = 0, None, set()
        for _ in range(10000):
            doc = self.request('GET', path+'?'+urllib.parse.urlencode({'limit': 100, 'offset': offset}))
            rows, count = doc.get(field), doc.get('count')
            if (not isinstance(rows, list) or type(count) is not int or count < 0
                or (total is not None and total != count) or offset+len(rows) > count):
                raise DeliveryError('invalid_brevo_pagination')
            total = count
            for row in rows:
                if not isinstance(row, dict) or type(row.get('id')) is not int or row['id'] in seen:
                    raise DeliveryError('invalid_brevo_paginated_record')
                seen.add(row['id']); yield row
            offset += len(rows)
            if offset == total: return
            if not rows: raise DeliveryError('incomplete_brevo_pagination')
        raise DeliveryError('brevo_page_limit')

    def find(self, key):
        rows = [v for v in self.pages('emailCampaigns', 'campaigns') if v.get('name') == key]
        if len(rows) > 1: raise DeliveryError('duplicate_brevo_campaign_requires_reconcile')
        if not rows: return None
        return self.request('GET', 'emailCampaigns/'+str(rows[0]['id']))

    def validate_campaign(self, campaign, locale, key):
        # API GET uses recipients.lists; POST uses recipients.listIds.
        recipients = campaign.get('recipients')
        if (not isinstance(recipients, dict) or recipients.get('lists') != [self.lists[locale]]
            or any(v for k, v in recipients.items() if k != 'lists')):
            raise DeliveryError('brevo_campaign_requires_reconcile')
        if (type(campaign.get('id')) is not int or campaign.get('name') != key or campaign.get('tag') != key):
            raise DeliveryError('brevo_campaign_requires_reconcile')

    def observed(self, campaign, locale, key):
        self.validate_campaign(campaign, locale, key)
        if campaign.get('status') not in ('queued', 'sent', 'inProcess'):
            raise DeliveryError('brevo_send_requires_reconcile')
        return {'action': 'SKIP', 'reason': 'campaign_already_queued', 'id': campaign['id']}

    def validate_send(self):
        sender = self.env.get('FCMO_EMAIL_FROM', '')
        if (self.env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true'
            or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', sender)
            or not self.env.get('FCMO_EMAIL_POSTAL_ADDRESS', '').strip()):
            raise ValueError('email_compliance_configuration_incomplete')

    def send_edition(self, edition, locale, idempotency_key):
        if idempotency_key != edition.key(locale): raise ValueError('invalid_edition_key')
        edition.validate_locale(locale)
        self.validate_send()
        # No implicit production-list fallback for the existing Kit seed mode.
        if edition.namespace != 'fcmo-diario': raise ValueError('brevo_seed_mode_not_configured')
        if not self.intent.is_file(): raise DeliveryError('missing_persisted_email_intent')
        with self.intent.open('r+') as journal:
            fcntl.flock(journal, fcntl.LOCK_EX)
            state = json.load(journal)
            if idempotency_key not in state.get('keys', []): raise DeliveryError('missing_persisted_email_intent')
            existing = self.find(idempotency_key)
            if existing: return self.observed(existing, locale, idempotency_key)
            if idempotency_key in state.get('previous', []) or idempotency_key in state.get('attempted', []):
                raise DeliveryError('unknown_brevo_create_requires_reconcile')
            mail = edition.render(locale,
                postal_address=self.env['FCMO_EMAIL_POSTAL_ADDRESS'],
                site_url=self.env.get('FCMO_SITE_URL', 'https://fcmo-ai.github.io/FCMO-AI-Newsletter'),
                preferences_url='{{ unsubscribe }}', unsubscribe_url='{{ unsubscribe }}')
            state.setdefault('attempted', []).append(idempotency_key)
            journal.seek(0); json.dump(state, journal); journal.truncate(); journal.flush(); os.fsync(journal.fileno())
            payload = {'name': idempotency_key, 'tag': idempotency_key, 'type': 'classic',
                'sender': {'email': self.env['FCMO_EMAIL_FROM'], 'name': 'FCMO AI Newsletter'},
                'subject': mail.subject, 'htmlContent': mail.html,
                'recipients': {'listIds': [self.lists[locale]]}, 'inlineImageActivation': False}
            try:
                result = self.request('POST', 'emailCampaigns', payload)
            except DeliveryError:
                existing = self.find(idempotency_key)
                if existing: return self.observed(existing, locale, idempotency_key)
                raise DeliveryError('unknown_brevo_create_requires_reconcile') from None
            existing = self.find(idempotency_key)
            if not existing or existing.get('id') != result.get('id'):
                raise DeliveryError('unconfirmed_brevo_create_requires_reconcile')
            self.validate_campaign(existing, locale, idempotency_key)
            if existing.get('status') != 'draft': raise DeliveryError('unexpected_brevo_create_state')
            # The durable attempted key already guards BOTH mutations, including
            # a crash after creating the draft but before this single sendNow.
            try:
                self.request('POST', 'emailCampaigns/'+str(existing['id'])+'/sendNow', {})
            except DeliveryError:
                existing = self.find(idempotency_key)
                if existing: return self.observed(existing, locale, idempotency_key)
                raise DeliveryError('unknown_brevo_send_requires_reconcile') from None
            existing = self.find(idempotency_key)
            if not existing: raise DeliveryError('unconfirmed_brevo_send_requires_reconcile')
            self.observed(existing, locale, idempotency_key)
            return {'action': 'QUEUED', 'id': existing['id']}

    def health(self):
        self.validate_send()
        estimate = 0
        for identity in self.lists.values():
            row = self.request('GET', 'contacts/lists/'+str(identity))
            count = row.get('totalSubscribers')
            if row.get('id') != identity or type(count) is not int or count < 0:
                raise DeliveryError('invalid_brevo_locale_list')
            estimate += count
        warnings = ['brevo_daily_cap_exceeded'] if estimate > DAILY_CAP else []
        return {'status': 'warning' if warnings else 'ok', 'provider': self.name,
                'warnings': warnings, 'estimated_daily_emails': estimate, 'daily_cap': DAILY_CAP}

    def list_subscribers(self):
        # Do not request only list/active contacts: suppressed and pending records
        # outside the production lists are essential to a safe migration.
        for row in self.pages('contacts', 'contacts'):
            if (not isinstance(row.get('email'), str) or type(row.get('emailBlacklisted')) is not bool
                or not isinstance(row.get('listIds'), list)
                or any(type(v) is not int for v in row['listIds'])):
                raise DeliveryError('invalid_brevo_contact')
            yield dict(row, locales=[locale for locale, identity in self.lists.items() if identity in row['listIds']])


Adapter = BrevoProvider
