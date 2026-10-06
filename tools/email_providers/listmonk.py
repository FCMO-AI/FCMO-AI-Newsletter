"""Wrap L26's existing host boundary, retaining its durable journal and recheck."""
import json
import urllib.request
from tools.email_listmonk import DeliveryError, NoRedirect, clean_origin, ListmonkClient, MailConfig
from . import SubscribeForm, LOCALES

PRIVACY_NOTICE = 'email-privacy.json'

def public_form(env,locale):
    origin = clean_origin(env.get('FCMO_EMAIL_PUBLIC_URL',''))
    return SubscribeForm(origin+'/subscribe',privacy_url=origin+'/privacy?locale='+locale)


class ListmonkProvider:
    name = 'listmonk'
    def __init__(self, env, *, service=None, client=None):
        self.env, self.service, self.client = dict(env), service, client
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
        edition.selected()
        if self.service:
            return self.service.dispatch(edition.stories,edition.status,live_verified=True,now=edition.now,locale=locale)
        payload = {k:edition.receipt[k] for k in ('source_commit','candidate_id')}
        result = self.request('/dispatch',dict(payload,locale=locale))
        if result.get('action') not in ('QUEUED','SKIP'): raise DeliveryError('invalid_gateway_outcome')
        return result
    def health(self):
        if self.service:
            self.service.client.lists(); self.service.client.campaign_template()
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
