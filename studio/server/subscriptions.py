"""Private, aggregate provider observation; no subscriber data enters publication."""
from tools.email_providers import LOCALES, create_provider

COUNTS = ('pending', 'confirmed', 'suppressed')
STATES = {'inactive': 'pending', 'unconfirmed': 'pending', 'pending': 'pending',
          'active': 'confirmed', 'enabled': 'confirmed', 'confirmed': 'confirmed',
          'cancelled': 'suppressed', 'unsubscribed': 'suppressed', 'disabled': 'suppressed',
          'bounced': 'suppressed', 'complained': 'suppressed', 'blocklisted': 'suppressed'}

def status(provider=None, env=None):
    unread = {'state': 'unread', 'plain_es': 'No se pudo leer el estado de las suscripciones.',
              'locales': {loc: {key: '?' for key in COUNTS} for loc in LOCALES}}
    try:
        if provider is None:
            import os
            config = dict(os.environ if env is None else env)
            config.setdefault('FCMO_EMAIL_PROVIDER', 'kit')
            provider = create_provider(config)
        counts = {loc: {key: 0 for key in COUNTS} for loc in LOCALES}
        unknown_locale = 0
        observer = getattr(provider, 'observe_subscribers', provider.list_subscribers)
        for row in observer():
            state = STATES.get(row.get('state', row.get('status')))
            if state is None: return unread
            locales = row.get('locales', [])
            if not isinstance(locales, list) or any(loc not in LOCALES for loc in locales): return unread
            if not locales: unknown_locale += 1
            for loc in set(locales): counts[loc][state] += 1
        return {'state': 'read', 'provider': provider.name, 'locales': counts, 'unknown_locale': unknown_locale,
                'plain_es': 'Estado leído del proveedor. Confirmados pueden recibir correo; pendientes y bajas quedan excluidos.'}
    except Exception:
        # Never expose provider errors, addresses or authentication details.
        return unread
