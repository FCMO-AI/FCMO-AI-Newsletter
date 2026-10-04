"""Curated editions are private drafts; references never edit upstream briefs."""
import re
from .storage import encoded, utc
from .validation import LOCALES, closed, text

SLOTS = ('lead', 'essays', 'briefs', 'notes')

def validate_issue(issue):
    closed(issue, ('schema', 'id', 'date', 'title', 'note', 'slots'))
    if issue['schema'] != 'fcmo-issue-v1' or not isinstance(issue['id'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}', issue['id']):
        raise ValueError('La edición no es válida.')
    from datetime import date
    date.fromisoformat(issue['date'])
    if not issue['id'].startswith(issue['date'] + '-'): raise ValueError('La fecha no coincide con la edición.')
    for field in ('title', 'note'):
        closed(issue[field], LOCALES)
        for val in issue[field].values(): text(val)
    if not isinstance(issue['slots'], list): raise ValueError('Los espacios de la edición no son válidos.')
    seen = set()
    for item in issue['slots']:
        closed(item, ('slot', 'ref'))
        if item['slot'] not in SLOTS or not isinstance(item['ref'], str) or not re.fullmatch(r'FCMO-(?:P-[0-9a-f]{12}|[0-9A-F]{12})', item['ref']):
            raise ValueError('Elige una publicación de la biblioteca.')
        if item['ref'] in seen: raise ValueError('Hay publicaciones repetidas en la edición.')
        seen.add(item['ref'])
    return issue

def create(store, user, issue):
    if user != 'matias': raise ValueError('Matías ensambla las ediciones.')
    validate_issue(issue)
    with store.mutex:
        if store.db.execute('SELECT 1 FROM pieces WHERE slug=?', (issue['id'],)).fetchone(): raise ValueError('La edición ya existe.')
        # The same journal/history/locks apply, but only the issue file is exported.
        temporary = store.create(user, 'note', issue['title']['en'], 'en'); value = issue['id']
        payload = store.payload(temporary['slug']); payload['piece']['slug'] = value; payload['piece']['id'] = value; payload['issue'] = issue
        import shutil
        work = store._worktree(temporary['slug'])
        from .storage import git
        git(store.data / 'clone', 'worktree', 'remove', '--force', str(work))
        git(store.data / 'clone', 'branch', '-D', 'draft/' + temporary['slug'])
        store.db.execute('UPDATE pieces SET slug=?,kind=?,payload_json=? WHERE slug=?', (value, 'issue', encoded(payload), temporary['slug']))
        store.db.commit(); store._mirror(value)
        return get(store, value)

def get(store, value):
    result = store.piece(value)
    if result['kind'] != 'issue': raise KeyError('La edición no existe.')
    return {'rev': result['head_rev'], 'state': result['state'], 'author': result['author'], 'locale_states': result['locale_states'], 'issue': store.payload(value)['issue']}

def save(store, value, user, base_rev, issue):
    validate_issue(issue)
    if value != issue['id']: raise ValueError('La edición no coincide.')
    from .storage import Conflict
    with store.mutex:
        store._editable(value)
        if store.piece(value)['author'] != user: raise ValueError('Solo el autor puede ensamblar la edición.')
        if store.piece(value)['head_rev'] != base_rev: raise Conflict(get(store, value))
        payload = store.payload(value); payload['issue'] = issue
        states = {loc: {'state': 'drafting', 'human_reviewed': False} for loc in LOCALES}
        rev = store._put(value, payload, user, states=states)
        return {'rev': rev}

def checks(store, preview, value):
    issue = get(store, value)['issue']; result = []
    def add(ident, ok, es, en):
        result.append({'id': ident, 'ok': bool(ok), 'plain_es': es, 'plain_en': en, 'goto': {'loc': 'en'}})
    valid = True
    try: validate_issue(issue)
    except ValueError: valid = False
    add('issue', valid, 'Completa la fecha, los títulos y los espacios de la edición.', 'Complete the date, titles and edition slots.')
    add('lead', sum(x['slot'] == 'lead' for x in issue['slots']) == 1, 'Elige una sola publicación principal.', 'Choose exactly one lead publication.')
    states = store.piece(value)['locale_states']
    for loc in LOCALES:
        add('locale-' + loc, states[loc]['state'] in ('ready', 'later') and (states[loc]['state'] == 'later' or issue['title'][loc].strip()),
            'Completa cada idioma o elige publicar después.', 'Complete each language or choose publish later.')
    library = store.data / 'clone/site/data/stories.v2.json'
    import json
    stories = json.loads(library.read_text())['stories'] if library.is_file() else []
    published = {p['meta']['id']: p['meta'] for p in store.list() if p['state'] == 'published' and p['kind'] != 'issue'}
    for item in issue['slots']:
        if item['ref'].startswith('FCMO-P-'):
            ref = published.get(item['ref'])
            ok = ref and all(ref['locales'][loc] == 'ready' for loc in LOCALES if states[loc]['state'] == 'ready')
        else: ok = any(s['id'] == item['ref'] and s.get('status') == 'live' for s in stories)
        add('ref-' + item['ref'], ok, 'Elige una publicación publicada y disponible en los idiomas de la edición.', 'Choose a published item available in the edition languages.')
    ok = True
    try: preview.privacy(value)
    except Exception: ok = False
    add('privacy', ok, 'La vista previa debe superar las comprobaciones de privacidad.', 'The preview must pass the privacy checks.')
    return result
