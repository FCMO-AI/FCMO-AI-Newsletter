"""Deterministic in-memory provider; never selected implicitly."""
from . import SubscribeForm

PRIVACY_NOTICE = 'email-privacy.json'

def public_form(env,locale):
    return SubscribeForm("https://example.org/subscribe",privacy_url="https://example.org/privacy")

class FakeProvider:
    name = 'fake'
    def __init__(self, env): self.env, self.sent = dict(env), {}
    def subscribe_form(self,locale): return public_form(self.env,locale)
    def send_edition(self,edition,locale,idempotency_key):
        if idempotency_key!=edition.key(locale): raise ValueError('invalid_edition_key')
        edition.selected()
        if idempotency_key in self.sent: return {'action':'SKIP'}
        self.sent[idempotency_key] = locale
        return {'action':'QUEUED'}
    def list_subscribers(self): return iter(())
    def health(self): return {'status':'ok','provider':self.name}

Adapter = FakeProvider
