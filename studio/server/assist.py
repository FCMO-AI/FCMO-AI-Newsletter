"""Optional private suggestions: acceptance never invents human review."""
import copy
import json
import re
from .storage import atomic, encoded, utc
from .validation import locale

def envelope(store, ident, user):
    if not re.fullmatch('[0-9a-f]{24}', ident): raise KeyError('La sugerencia no existe.')
    path = store.data / 'jobs/queued' / (ident + '.json')
    if not path.is_file(): raise KeyError('La sugerencia no existe.')
    job = json.loads(path.read_text())
    if job['author'] != user: raise ValueError('Solo el autor puede ver sus sugerencias.')
    return job

def accept(store, ident, user, block_ids, base_rev):
    job = envelope(store, ident, user); value = job['slug']; loc = locale(job['locale'])
    path = store.data / 'jobs/done' / (ident + '.json')
    if not path.is_file() or path.stat().st_size > 2*1024*1024: raise ValueError('La sugerencia aún no está lista.')
    done = json.loads(path.read_text())
    if not isinstance(done.get('model'), str) or len(done['model']) > 200 or not isinstance(done.get('suggestions'), list): raise ValueError('La sugerencia no es válida.')
    if not isinstance(block_ids, list) or not block_ids or any(not isinstance(k, str) for k in block_ids): raise ValueError('Elige los párrafos que quieres aceptar.')
    with store.mutex:
        from .storage import Conflict
        if store.piece(value)['head_rev'] != base_rev or job['rev'] != base_rev: raise Conflict(store.doc(value, loc))
        payload = store.payload(value); source = payload['piece']['source_locale']
        doc = copy.deepcopy(payload['docs'].get(loc, payload['docs'][source])); doc['locale'] = loc
        suggestions = {s['block_id']: s['text'] for s in done['suggestions'] if isinstance(s, dict) and isinstance(s.get('text'), str) and isinstance(s.get('block_id'), str)}
        changed = set()
        for block in doc['blocks']:
            if block['id'] not in block_ids: continue
            if block['id'] not in suggestions or block['type'] not in ('p', 'h2', 'h3', 'blockquote', 'pullquote') or any(n.get('t') != 'text' for n in block.get('content', [])):
                raise ValueError('Este párrafo necesita edición manual para conservar sus referencias.')
            block['content'] = [{'t': 'text', 'v': suggestions[block['id']]}]; changed.add(block['id'])
        if changed != set(block_ids): raise ValueError('El párrafo de la sugerencia ya no existe.')
        result = store.save(value, loc, user, base_rev, doc, store.piece(value)['cursor'].get(loc, {}))
        payload = store.payload(value)
        payload['provenance'][loc] = {'origin': 'agent_draft', 'human_reviewed': False, 'reviewer': '', 'at': utc(), 'source_locale': source, 'model': done['model']}
        blocks = payload.setdefault('block_provenance', {}).setdefault(loc, {})
        for key in changed: blocks[key] = 'agent_draft'
        store._put(value, payload, user, bump=False)
        return result
