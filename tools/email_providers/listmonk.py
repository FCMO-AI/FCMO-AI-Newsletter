"""Wrap L26's existing host boundary, retaining its durable journal and recheck."""
import json
import fcntl
import os
from pathlib import Path
import urllib.request
from tools.email_listmonk import DeliveryError, NoRedirect, clean_origin, ListmonkClient, MailConfig, literal
from . import SubscribeForm, LOCALES

PRIVACY_NOTICE = 'email-privacy.json'

def public_form(env,locale):
    origin = clean_origin(env.get('FCMO_EMAIL_PUBLIC_URL',''))
    return SubscribeForm(origin+'/subscribe',privacy_url=origin+'/privacy?locale='+locale)


class ListmonkProvider:
    name = 'listmonk'
    def __init__(self, env, *, service=None, client=None):
        self.env, self.service, self.client = dict(env), service, client
        if self.client is None and env.get('FCMO_EMAIL_PROVIDER_CONFIG'):
            private = json.loads(env['FCMO_EMAIL_PROVIDER_CONFIG'])
            if not isinstance(private, dict): raise ValueError('invalid_listmonk_private_configuration')
            self.client = ListmonkClient(MailConfig.from_env(dict(env, **private)))
    def subscribe_form(self,locale): return public_form(self.env,locale)
    def request(self,path,payload=None):
        token = self.env.get('FCMO_EMAIL_DISPATCH_TOKEN','')
        if len(token)<32: raise ValueError('missing_dispatch_capability')
        req = urllib.request.Request(clean_origin(self.env.get('FCMO_EMAIL_PUBLIC_URL',''))+path,
            data=json.dumps(payload).encode() if payload is not None else None,
            method='POST' if payload is not None else 'GET',headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=120) as response:
                return json.loads(response.read(8192))
        except (OSError,ValueError): raise DeliveryError('email_gateway_outcome_unconfirmed') from None
    def send_edition(self,edition,locale,idempotency_key):
        if idempotency_key!=edition.key(locale): raise ValueError('invalid_edition_key')
        from tools.email_piece_dispatch import PieceEdition
        if isinstance(edition, PieceEdition): return self.send_piece(edition, locale, idempotency_key)
        edition.selected()
        if self.service:
            return self.service.dispatch(edition.stories,edition.status,live_verified=True,now=edition.now,locale=locale)
        payload = {k:edition.receipt[k] for k in ('source_commit','candidate_id')}
        result = self.request('/dispatch',dict(payload,locale=locale))
        if result.get('action') not in ('QUEUED','SKIP'): raise DeliveryError('invalid_gateway_outcome')
        return result

    def send_piece(self, edition, locale, key):
        """Private API lane with the same durable L27 intent/reconciliation rule.

        L26's public gateway remains scoped to daily dispatch; piece API access
        requires private credentials and an authorized route to Listmonk.
        """
        edition.validate_locale(locale)
        if edition.namespace != 'fcmo-diario': raise ValueError('listmonk_seed_mode_not_configured')
        if self.env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true': raise ValueError('email_compliance_configuration_incomplete')
        client = self.client or (self.service.client if self.service else None)
        if client is None: raise ValueError('listmonk_piece_private_api_configuration_required')
        config = client.config
        lists = client.lists(); template = client.campaign_template()
        mail = edition.render(locale, site_url=config.site_url, postal_address=config.postal_address,
                              preferences_url='{{ UnsubscribeURL }}?manage=true', unsubscribe_url='{{ UnsubscribeURL }}')
        intent = Path(self.env.get('FCMO_EMAIL_INTENT', 'email-intent.json'))
        def observed(row):
            target = [v['id'] if isinstance(v, dict) else v for v in row.get('lists', [])]
            if (row.get('name') != key or target != [lists[locale]['id']]
                or row.get('template_id') != template or key not in row.get('tags', [])
                or type(row.get('id')) is not int
                or row.get('status') not in ('running', 'finished', 'scheduled')):
                raise DeliveryError('listmonk_piece_requires_reconcile')
            return {'action': 'SKIP', 'reason': 'campaign_already_queued', 'id': row['id']}
        if not intent.is_file(): raise DeliveryError('missing_persisted_email_intent')
        with intent.open('r+') as journal:
            fcntl.flock(journal, fcntl.LOCK_EX); state = json.load(journal)
            if key not in state.get('keys', []): raise DeliveryError('missing_persisted_email_intent')
            existing = client.find_campaign(key)
            if existing: return observed(existing)
            if key in state.get('previous', []) or key in state.get('attempted', []):
                raise DeliveryError('unknown_listmonk_piece_create_requires_reconcile')
            state.setdefault('attempted', []).append(key)
            journal.seek(0); json.dump(state, journal); journal.truncate(); journal.flush(); os.fsync(journal.fileno())
            payload = {'name': key, 'subject': literal(mail.subject), 'type': 'regular', 'content_type': 'html',
                       'body': mail.html, 'altbody': literal(mail.text).replace('{\u200b{ UnsubscribeURL }\u200b}', '{{ UnsubscribeURL }}'),
                       'from_email': config.from_email, 'lists': [lists[locale]['id']],
                       'tags': ['fcmo-piece', key], 'template_id': template}
            try:
                result = client.request('POST', 'campaigns', payload)
                existing = client.find_campaign(key)
                if not existing or existing.get('id') != result.get('id') or existing.get('status') != 'draft':
                    raise DeliveryError('unconfirmed_listmonk_piece_draft')
                target = [v['id'] if isinstance(v, dict) else v for v in existing.get('lists', [])]
                if (target != payload['lists'] or any(existing.get(k) != v for k, v in payload.items() if k != 'lists')):
                    raise DeliveryError('listmonk_piece_draft_changed')
                client.request('PUT', f'campaigns/{existing["id"]}/status', {'status': 'running'})
            except DeliveryError:
                existing = client.find_campaign(key)
                if existing: return observed(existing)
                raise DeliveryError('unknown_listmonk_piece_create_requires_reconcile') from None
            existing = client.request('GET', f'campaigns/{existing["id"]}')
            observed(existing)
            return {'action': 'QUEUED', 'id': existing['id']}
    def health(self):
        if self.service or self.client:
            client = self.client or self.service.client
            client.lists(); client.campaign_template()
            return {'status':'ok','provider':self.name}
        if self.request('/healthz').get('status')!='ok': raise DeliveryError('gateway_unhealthy')
        return {'status':'ok','provider':self.name}
    def list_subscribers(self):
        # Backup job uses private provider credentials, never the dispatch capability.
        client = self.client or (self.service.client if self.service else ListmonkClient(MailConfig.from_env(self.env)))
        lists = client.lists()
        for page in range(1,10001):
            data = client.request('GET',f'subscribers?page={page}&per_page=100')
            rows = data.get('results')
            if not isinstance(rows,list): raise DeliveryError('invalid_listmonk_export')
            for row in rows:
                memberships = {v['id']:v.get('subscription_status') for v in row.get('lists',[])}
                yield dict(row,locales=[l for l in LOCALES if memberships.get(lists[l]['id'])=='confirmed'])
            if page*100>=data['total']: return
        raise DeliveryError('listmonk_export_page_limit')

Adapter = ListmonkProvider
