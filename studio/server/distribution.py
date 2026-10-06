"""Read-only L28b hook; only confirmed dispatch for this deployment is shown."""
import json
from pathlib import Path
import re


def email_status(root, piece_id, merge_sha, requested):
    if not requested: return {'state': 'disabled', 'plain_es': 'Sin envío por correo.'}
    pending = {'state': 'pending', 'plain_es': 'Correo pendiente del despliegue verificado.'}
    if not re.fullmatch(r'FCMO-P-[0-9a-f]{12}', piece_id or '') or not re.fullmatch(r'[0-9a-f]{40}', merge_sha or ''): return pending
    path = Path(root) / 'ops/email-dispatch/pieces' / (piece_id + '.json')
    try:
        if path.stat().st_size > 16384: return pending
        row = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError): return pending
    if not isinstance(row, dict): return pending
    if row.get('schema') == 'fcmo-piece-email-dispatch-v1' and row.get('piece_id') == piece_id and row.get('merge_sha') == merge_sha and row.get('state') == 'sent' and isinstance(row.get('sent_at'), str) and row['sent_at'].strip() and isinstance(row.get('dispatch_id'), str) and row['dispatch_id'].strip():
        return {'state': 'sent', 'plain_es': 'Enviado por correo ✓', 'sent_at': row['sent_at']}
    return pending
