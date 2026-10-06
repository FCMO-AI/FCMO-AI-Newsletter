"""Kit v4 adapter using the operator's live-probed tag broadcast boundary.

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
CONFIG = json.loads((Path(__file__).resolve().parents[2]/'community/config/kit.json').read_text())

def form_id(env, locale):
    value = env.get('KIT_FORM_'+SUFFIX[locale]) or CONFIG['locales'][locale]['form_id']
    if not re.fullmatch(r'[1-9][0-9]*',value): raise ValueError('missing_or_invalid_kit_form')
    return value

def public_form(env,locale):
    if env.get('FCMO_EMAIL_ENABLED') != 'true' or env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true':
        raise ValueError('email_signup_inactive')
    form = form_id(env,locale)
    uid = env.get('KIT_FORM_UID_'+SUFFIX[locale]) or CONFIG['locales'][locale]['uid']
    if not re.fullmatch(r'[a-z0-9]+',uid): raise ValueError('invalid_kit_form_uid')
    return SubscribeForm('https://app.kit.com/forms/'+form+'/subscriptions', 'email_address', True,
                         public_notice(env.get('FCMO_EMAIL_PRIVACY_URL','')),
                         CONFIG['hosted_origin']+'/'+uid)


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
        if (env.get('KIT_FILTER_MODE') or 'tag') != 'tag':
            raise ValueError('kit_supports_only_tag_filters')
        self.forms = {locale:int(form_id(env,locale)) for locale in LOCALES}
        if len(set(self.forms.values())) != 3: raise ValueError('kit_locale_forms_must_differ')
        self.memberships = {}
        self._prepared_keys = set()
        for locale in LOCALES:
            identity = env.get('KIT_TAG_'+SUFFIX[locale])
            if identity:
                if not re.fullmatch(r'[1-9][0-9]*',identity): raise ValueError('invalid_kit_locale_tag')
                self.memberships[locale] = int(identity)
        if len(set(self.memberships.values())) != len(self.memberships):
            raise ValueError('kit_locale_memberships_must_differ')
        if env.get('FCMO_EMAIL_NAMESPACE') == 'fcmo-diario-test' and len(self.memberships)!=3:
            raise ValueError('explicit_seed_tags_required')

    def ensure_tags(self):
        if len(self.memberships)==3:
            if len(set(self.memberships.values()))!=3: raise DeliveryError('kit_locale_memberships_must_differ')
            return
        tags = list(self.pages('tags','tags'))
        for locale in LOCALES:
            if locale in self.memberships: continue
            name = CONFIG['locales'][locale]['tag_name']
            matches = [tag for tag in tags if tag.get('name')==name]
            if len(matches)>1: raise DeliveryError('duplicate_kit_locale_tag')
            if not matches:
                try:
                    self.request('POST','tags',{'name':name})
                except DeliveryError:
                    # Creation may have succeeded. Reconcile by exact name once.
                    pass
                tags = list(self.pages('tags','tags'))
                matches = [tag for tag in tags if tag.get('name')==name]
            if len(matches)!=1 or type(matches[0].get('id')) is not int or matches[0]['id']<=0:
                raise DeliveryError('unconfirmed_kit_locale_tag')
            self.memberships[locale] = matches[0]['id']
        if len(set(self.memberships.values()))!=3: raise DeliveryError('kit_locale_memberships_must_differ')

    def subscriber_filter(self, locale):
        self.ensure_tags()
        return [{'all':[{'type':'tag','ids':[self.memberships[locale]]}]}]

    def subscriber_tags(self, identity):
        tags = list(self.pages('subscribers/'+str(identity)+'/tags','tags'))
        if any(type(tag.get('id')) is not int for tag in tags): raise DeliveryError('invalid_kit_subscriber_tags')
        return {tag['id'] for tag in tags}

    def sync_subscribers(self, locale=None):
        """Idempotently mirror active form members; never read the lagging tag list."""
        self.ensure_tags()
        for language in ((locale,) if locale else LOCALES):
            tag = self.memberships[language]
            seen = set()
            for subscriber in self.pages('forms/'+str(self.forms[language])+'/subscribers?status=active','subscribers'):
                identity = subscriber.get('id')
                if type(identity) is not int or identity<=0 or subscriber.get('state')!='active':
                    raise DeliveryError('invalid_kit_active_form_subscriber')
                if identity in seen: continue
                seen.add(identity)
                try:
                    self.request('POST','tags/'+str(tag)+'/subscribers/'+str(identity),{})
                except DeliveryError:
                    # This membership POST is idempotent; confirm the effect even
                    # when its acknowledgement was lost, without a blind retry.
                    pass
                if tag not in self.subscriber_tags(identity):
                    raise DeliveryError('unconfirmed_kit_subscriber_tag')

    def prepare_edition(self, edition):
        # Sync every locale before the first broadcast in a dispatch batch.
        self._prepared_keys.clear()
        self.validate_send()
        self.validate_seed(edition)
        if edition.namespace != 'fcmo-diario-test':
            self.sync_subscribers()
            self._prepared_keys.update(edition.key(locale) for locale in LOCALES)

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
            prepared = idempotency_key in self._prepared_keys
            self._prepared_keys.discard(idempotency_key)
            existing = self.find(idempotency_key)
            if existing: return self.observed(existing,locale,idempotency_key)
            if idempotency_key in state.get('previous',[]) or idempotency_key in state.get('attempted',[]):
                raise DeliveryError('unknown_kit_create_requires_reconcile')
            if edition.namespace != 'fcmo-diario-test' and not prepared: self.sync_subscribers(locale)
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
        # The account-wide active audience is a conservative isolation oracle.
        # A lagging GET /tags/<id>/subscribers cannot prove an exclusive seed.
        if any(not self.env.get('KIT_TAG_'+SUFFIX[locale]) for locale in LOCALES):
            raise ValueError('explicit_seed_tags_required')
        self.ensure_tags()
        rows = list(self.pages('subscribers?status=active','subscribers'))
        if len(rows)!=1 or rows[0].get('id')!=int(expected) or rows[0].get('state')!='active':
            raise DeliveryError('seed_account_must_contain_only_the_confirmed_test_subscriber')
        if not set(self.memberships.values()).issubset(self.subscriber_tags(int(expected))):
            raise DeliveryError('seed_subscriber_missing_locale_tags')

    def health(self):
        self.validate_send()
        identities = {v['id'] for v in self.pages('forms','forms')}
        if not set(self.forms.values()).issubset(identities): raise DeliveryError('missing_kit_locale_form')
        if self.memberships:
            tags = {v['id'] for v in self.pages('tags','tags')}
            if not set(self.memberships.values()).issubset(tags): raise DeliveryError('missing_kit_locale_tag')
        return {'status':'ok','provider':self.name}

    def list_subscribers(self):
        self.sync_subscribers()  # Daily encrypted backup also repairs form→tag drift.
        # Query every state explicitly; default active-only exports lose suppressions.
        rows = {}
        for state in ('active','inactive','bounced','complained','cancelled'):
            for subscriber in self.pages('subscribers?'+urllib.parse.urlencode({'status':state}),'subscribers'):
                if not isinstance(subscriber.get('id'),int) or 'email_address' not in subscriber or 'state' not in subscriber:
                    raise DeliveryError('invalid_kit_subscriber')
                rows[subscriber['id']] = dict(subscriber,locales=[])
        # Preserve locale intent even for pending/suppressed form members.
        for locale, identity in self.forms.items():
            for state in ('active','inactive','bounced','complained','cancelled'):
                for subscriber in self.pages('forms/'+str(identity)+'/subscribers?status='+state,'subscribers'):
                    if subscriber.get('id') in rows and locale not in rows[subscriber['id']]['locales']:
                        rows[subscriber['id']]['locales'].append(locale)
        for identity, subscriber in rows.items():
            tags = self.subscriber_tags(identity)
            for locale, tag in self.memberships.items():
                if tag in tags and locale not in subscriber['locales']: subscriber['locales'].append(locale)
            yield subscriber

Adapter = KitProvider
