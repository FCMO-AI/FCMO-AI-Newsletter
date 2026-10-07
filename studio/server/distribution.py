"""Read the dispatcher's content-free lifetime production projection."""
import re
from tools.email_piece_state import validate
from tools.email_providers import LOCALES


def email_status(state, piece_id, requested):
    if not requested: return {'state': 'disabled', 'plain_es': 'Sin envío por correo.'}
    pending = {'state': 'pending', 'plain_es': 'Correo pendiente de programación.'}
    if not re.fullmatch(r'FCMO-P-[0-9a-f]{12}', piece_id or ''): return pending
    try:
        if state.get('provider') not in ('kit', 'brevo', 'fake', 'listmonk'): return pending
        validate(state, state['provider'])
        # Seed reservations/observations must never indicate production success.
        if any(not key.startswith('fcmo-piece:') for key in state['keys']): return pending
        rows = {row['locale']: row for row in state['records'] if row['piece_id'] == piece_id}
        if any('fcmo-piece:' + piece_id + ':' + loc not in state['keys'] or
               rows.get(loc, {}).get('state') != 'QUEUED' for loc in LOCALES): return pending
    except (AttributeError, KeyError, TypeError, ValueError): return pending
    return {'state': 'queued', 'plain_es': 'Correo programado ✓',
            'locales': {loc: {'broadcast_id': rows[loc]['broadcast_id'], 'timestamp': rows[loc]['timestamp']} for loc in LOCALES}}
