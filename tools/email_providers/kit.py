"""Kit v4 adapter against explicitly assumed, offline-tested public API shapes.

Only GETs are retried. A create schedules a broadcast and may have succeeded
when its response is lost: reconcile by marker, then block if still unknown.
The workflow uploads a write-ahead intent before entering this adapter.
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
from tools.email_render import render_daily_email
from . import LOCALES, SUFFIX, SubscribeForm, public_notice

PRIVACY_NOTICE = 'email-privacy-kit.json'

def public_form(env,locale):
    if env.get('FCMO_EMAIL_ENABLED') != 'true' or env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true':
        raise ValueError('email_signup_inactive')
    form = env.get('KIT_FORM_'+SUFFIX[locale],'')
    if not re.fullmatch(r'[1-9][0-9]*',form): raise ValueError('missing_or_invalid_kit_form')
    return SubscribeForm('https://app.kit.com/forms/'+form+'/subscriptions', 'email_address', True,
                         public_notice(env.get('FCMO_EMAIL_PRIVACY_URL','')))


class KitProvider:
    name = 'kit'
    requires_intent = True
    def __init__(self, env, *, base_url='https://api.kit.com/v4', intent=None, sleep=time.sleep):
        parts = urllib.parse.urlsplit(base_url)
        if base_url != 'https://api.kit.com/v4' and not (parts.scheme=='http' and parts.hostname=='127.0.0.1' and parts.path=='/v4'):
            raise ValueError('invalid_kit_api_origin')
        self.env, self.base_url, self.sleep = dict(env), base_url, sleep
        self.api_key = env.get('KIT_API_KEY','')
        if not self.api_key: raise ValueError('missing_kit_api_key')
        sender = env.get('FCMO_EMAIL_FROM','')
        if sender and not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',sender): raise ValueError('invalid_kit_sender_address')
        self.intent = Path(intent or env.get('FCMO_EMAIL_INTENT','email-intent.json'))
        self.filter_mode = env.get('KIT_FILTER_MODE') or 'form'
        if self.filter_mode not in ('form', 'tag'): raise ValueError('invalid_kit_filter_mode')
        self.memberships = {}
        for locale in LOCALES:
            identity = env.get('KIT_'+self.filter_mode.upper()+'_'+SUFFIX[locale],'')
            if not re.fullmatch(r'[1-9][0-9]*',identity): raise ValueError('invalid_kit_locale_'+self.filter_mode)
            self.memberships[locale] = int(identity)
        if len(set(self.memberships.values())) != 3: raise ValueError('kit_locale_memberships_must_differ')

    def subscriber_filter(self, locale):
        return {'all':[{'type':self.filter_mode,'ids':[self.memberships[locale]]}]}

    def membership_path(self, identity):
        return self.filter_mode+'s/'+str(identity)+'/subscribers'

    def subscribe_form(self, locale): return public_form(self.env,locale)

    def request(self, method, path, payload=None):
        raw = None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
        req = urllib.request.Request(self.base_url+'/'+path,data=raw,method=method,
            headers={'X-Kit-Api-Key':self.api_key,'Content-Type':'application/json','Accept':'application/json'})
        for attempt in range(3 if method=='GET' else 1):
            try:
                with urllib.request.build_opener(NoRedirect).open(req,timeout=25) as response:
                    body = response.read(8_000_001)
                if len(body)>8_000_000: raise DeliveryError('kit_response_too_large')
                doc = json.loads(body)
                if not isinstance(doc,dict): raise DeliveryError('invalid_kit_response')
                return doc
            except urllib.error.HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if method=='GET' and retryable and attempt<2:
                    self.sleep(2**attempt); continue
                raise DeliveryError('kit_request_failed_or_outcome_unknown') from None
            except (urllib.error.URLError,OSError,ValueError):
                if method=='GET' and attempt<2:
                    self.sleep(2**attempt); continue
                raise DeliveryError('kit_request_failed_or_outcome_unknown') from None
        raise DeliveryError('kit_retry_exhausted')

    def pages(self, path, field):
        cursor, seen = None, set()
        for _ in range(10000):
            separator = '&' if '?' in path else '?'
            suffix = separator+urllib.parse.urlencode({'per_page':100, **({'after':cursor} if cursor else {})})
            doc = self.request('GET',path+suffix)
            rows, page = doc.get(field), doc.get('pagination')
            if not isinstance(rows,list) or not isinstance(page,dict) or type(page.get('has_next_page')) is not bool:
                raise DeliveryError('invalid_kit_pagination')
            yield from rows
            if not page['has_next_page']: return
            cursor = page.get('end_cursor')
            if not isinstance(cursor,str) or not cursor or cursor in seen: raise DeliveryError('invalid_kit_cursor')
            seen.add(cursor)
        raise DeliveryError('kit_page_limit')

    def find(self, key):
        rows = [v for v in self.pages('broadcasts','broadcasts') if v.get('description')==key]
        if len(rows)>1: raise DeliveryError('duplicate_kit_broadcast_requires_reconcile')
        return rows[0] if rows else None

    def observed(self, broadcast, locale, key):
        if (not isinstance(broadcast.get('id'),int) or not broadcast.get('send_at') or broadcast.get('public') is not False
            or broadcast.get('description')!=key or broadcast.get('subscriber_filter')!=self.subscriber_filter(locale)):
            raise DeliveryError('kit_broadcast_requires_reconcile')
        return {'action':'SKIP','reason':'broadcast_already_scheduled','id':broadcast['id']}

    def send_edition(self, edition, locale, idempotency_key):
        if idempotency_key != edition.key(locale): raise ValueError('invalid_edition_key')
        chosen = edition.selected()
        self.validate_send()
        self.validate_seed(edition)
        # Locks protect direct/local callers; Actions also serializes the workflow.
        if not self.intent.is_file(): raise DeliveryError('missing_persisted_email_intent')
        with self.intent.open('r+') as journal:
            fcntl.flock(journal,fcntl.LOCK_EX)
            state = json.load(journal)
            if idempotency_key not in state.get('keys',[]): raise DeliveryError('missing_persisted_email_intent')
            existing = self.find(idempotency_key)
            if existing: return self.observed(existing,locale,idempotency_key)
            if idempotency_key in state.get('previous',[]) or idempotency_key in state.get('attempted',[]):
                raise DeliveryError('unknown_kit_create_requires_reconcile')
            mail = render_daily_email(chosen,edition.status['edition_date'],locale=locale,
                postal_address=self.env['FCMO_EMAIL_POSTAL_ADDRESS'],
                site_url=self.env.get('FCMO_SITE_URL','https://fcmo-ai.github.io/FCMO-AI-Newsletter'),
                preferences_url='{{ unsubscribe_url }}',unsubscribe_url='{{ unsubscribe_url }}')
            state.setdefault('attempted',[]).append(idempotency_key)
            journal.seek(0); json.dump(state,journal); journal.truncate(); journal.flush(); os.fsync(journal.fileno())
            payload = {'subject':mail.subject,'content':mail.html,'description':idempotency_key,
                'public':False, 'email_address':self.env['FCMO_EMAIL_FROM'],
                'subscriber_filter':self.subscriber_filter(locale),
                'send_at':edition.now.isoformat().replace('+00:00','Z')}
            try:
                result = self.request('POST','broadcasts',payload)
                self.observed(result.get('broadcast',{}),locale,idempotency_key)
            except DeliveryError:
                existing = self.find(idempotency_key)
                if existing: return self.observed(existing,locale,idempotency_key)
                raise DeliveryError('unknown_kit_create_requires_reconcile') from None
            # Re-read, rather than declaring provider state from the POST alone.
            existing = self.find(idempotency_key)
            if not existing: raise DeliveryError('unconfirmed_kit_create_requires_reconcile')
            self.observed(existing,locale,idempotency_key)
            return {'action':'QUEUED','id':existing['id']}

    def validate_send(self):
        if self.env.get('FCMO_EMAIL_COMPLIANCE_READY')!='true' or not all(self.env.get(k,'').strip() for k in ('FCMO_EMAIL_FROM','FCMO_EMAIL_POSTAL_ADDRESS')):
            raise ValueError('email_compliance_configuration_incomplete')

    def validate_seed(self, edition):
        if edition.namespace != 'fcmo-diario-test': return
        expected = self.env.get('KIT_TEST_SUBSCRIBER_ID','')
        if not re.fullmatch(r'[1-9][0-9]*',expected): raise ValueError('test_subscriber_id_required')
        for identity in self.memberships.values():
            rows = list(self.pages(self.membership_path(identity)+'?status=active','subscribers'))
            if len(rows)!=1 or rows[0].get('id')!=int(expected) or rows[0].get('state')!='active':
                raise DeliveryError('seed_memberships_must_contain_only_the_confirmed_test_subscriber')

    def health(self):
        self.validate_send()
        field = self.filter_mode+'s'
        identities = {v['id'] for v in self.pages(field,field)}
        if not set(self.memberships.values()).issubset(identities): raise DeliveryError('missing_kit_locale_'+self.filter_mode)
        return {'status':'ok','provider':self.name}

    def list_subscribers(self):
        # Query every state explicitly; default active-only exports lose suppressions.
        rows = {}
        for state in ('active','inactive','bounced','complained','cancelled'):
            for subscriber in self.pages('subscribers?'+urllib.parse.urlencode({'status':state}),'subscribers'):
                if not isinstance(subscriber.get('id'),int) or 'email_address' not in subscriber or 'state' not in subscriber:
                    raise DeliveryError('invalid_kit_subscriber')
                rows[subscriber['id']] = dict(subscriber,locales=[])
        for locale, identity in self.memberships.items():
            # Both membership endpoints must preserve pending/suppressed states.
            for subscriber in self.pages(self.membership_path(identity),'subscribers'):
                if subscriber.get('id') in rows: rows[subscriber['id']]['locales'].append(locale)
        yield from rows.values()

Adapter = KitProvider
