"""Provider boundary for FCMO AI Newsletter; builds never instantiate authenticated clients."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
import re
import importlib
from urllib.parse import urlsplit

LOCALES = ('en', 'es-419', 'zh-Hans')
SUFFIX = {'en':'EN', 'es-419':'ES', 'zh-Hans':'ZH'}

@dataclass(frozen=True)
class SubscribeForm:
    action: str
    email_field: str = 'email'
    fixed_locale: bool = False
    privacy_url: str = ''

@dataclass(frozen=True)
class Edition:
    stories: dict
    status: dict
    receipt: dict
    now: datetime
    namespace: str = 'fcmo-diario'

    def key(self, locale):
        if locale not in LOCALES: raise ValueError('unsupported_email_locale')
        if self.namespace not in ('fcmo-diario','fcmo-diario-test'): raise ValueError('invalid_email_namespace')
        return self.namespace+':'+self.status['edition_date']+':'+locale

    def selected(self):
        from tools.email_dispatch import eligibility
        from tools.email_render import localized_story
        decision = eligibility(self.stories,self.status,live_verified=True,now=self.now)
        if decision.action != 'SEND': raise ValueError('edition_not_eligible')
        chosen = [v['story'] for v in decision.items]
        for locale in LOCALES:
            if any(localized_story(v,locale) is None for v in chosen):
                raise ValueError('selected edition lacks complete native '+locale)
        return chosen

class Provider(Protocol):
    name: str
    def subscribe_form(self, locale: str) -> SubscribeForm: ...
    def send_edition(self, edition: Edition, locale: str, idempotency_key: str) -> dict: ...
    def list_subscribers(self): ...
    def health(self) -> dict: ...


def public_notice(value):
    parts = urlsplit(value)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('complete_email_privacy_url_required')
    return value


def provider_module(env):
    name = env.get('FCMO_EMAIL_PROVIDER','listmonk')
    if not re.fullmatch(r'[a-z][a-z0-9_]*',name): raise ValueError('unknown_email_provider')
    try:
        return importlib.import_module(__name__+'.'+name)
    except ModuleNotFoundError as exc:
        if exc.name == __name__+'.'+name: raise ValueError('unknown_email_provider') from None
        raise


def signup_form(env, locale):
    """Public-only configuration. Keys and subscriber information never reach HTML."""
    if locale not in LOCALES: raise ValueError('unsupported_email_locale')
    if env.get('FCMO_EMAIL_ENABLED') == 'false': raise ValueError('email_disabled')
    return provider_module(env).public_form(env,locale)


def create_provider(env, **kwargs):
    return provider_module(env).Adapter(env,**kwargs)


def dispatch_edition(provider, edition, *, enabled, live_verified):
    from tools.email_dispatch import eligibility
    if not enabled: return {'action':'SKIP','reason':'disabled'}
    decision = eligibility(edition.stories,edition.status,live_verified=live_verified,now=edition.now)
    if decision.action == 'SKIP': return {'action':'SKIP','reason':decision.reason}
    edition.selected()  # All languages must be complete before the first call.
    outcomes, failed = {}, []
    from tools.email_listmonk import DeliveryError
    for locale in LOCALES:
        try: outcomes[locale] = provider.send_edition(edition,locale,edition.key(locale))
        except DeliveryError: failed.append(locale)
    if failed: raise DeliveryError('provider_outcome_requires_reconcile:'+','.join(failed))
    return {'action':'QUEUED' if any(v['action']=='QUEUED' for v in outcomes.values()) else 'SKIP',
            'edition':edition.status['edition_date'], 'locales':outcomes}


def privacy_notice_file(env):
    return provider_module(env).PRIVACY_NOTICE
