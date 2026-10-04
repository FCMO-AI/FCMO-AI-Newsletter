"""Plain-language publication checks; failures stay tied to a useful destination."""
import re
from .validation import LOCALES, validate_doc, validate_figures, validate_sources

def checks(store, preview, value):
    payload = store.payload(value); piece = store.piece(value); results = []
    def add(key, ok, es, en, loc='en', block=None):
        results.append({'id': key, 'ok': bool(ok), 'plain_es': es, 'plain_en': en, 'goto': {'loc': loc, **({'block_id': block} if block else {})}})
    source = payload['piece']['source_locale']; docs = payload['docs']; source_doc = docs[source]
    source_ids = [b['id'] for b in source_doc['blocks']]
    source_notes = set(source_doc['footnotes'])
    for loc in LOCALES:
        state = piece['locale_states'][loc]['state']; doc = docs.get(loc)
        add('language-' + loc, state in ('ready', 'later'), 'Completa este idioma o elige publicar después.', 'Complete this language or choose publish later.', loc)
        if state != 'ready': continue
        add('heading-' + loc, doc and doc['title'].strip() and doc['dek'].strip() and doc['blocks'], 'Completa el título, la introducción y el texto.', 'Complete the title, introduction and body.', loc)
        valid = True
        try: validate_doc(doc, loc)
        except (ValueError, TypeError): valid = False
        add('document-' + loc, valid, 'Revisa la estructura y las notas al pie.', 'Check the document structure and footnotes.', loc)
        if not doc: continue
        add('alignment-' + loc, [b['id'] for b in doc['blocks']] == source_ids and set(doc['footnotes']) == source_notes,
            'Conserva los mismos párrafos y notas en cada idioma.', 'Keep the same paragraphs and notes in each language.', loc)
        def tokens(document):
            import json
            serial = json.dumps(document, ensure_ascii=False)
            # Exclude structural IDs; the final PIECE_VALID gate is authoritative.
            numbers, links, cites, figures = [], [], [], []
            def walk(node):
                if isinstance(node, list):
                    for x in node: walk(x)
                elif isinstance(node, dict):
                    if node.get('t') == 'text': numbers.extend(re.findall(r'\d+(?:[.,]\d+)*', node['v']))
                    if node.get('t') == 'link': links.append(node['href'])
                    if node.get('t') == 'cite': cites.append(node['key'])
                    if node.get('type') == 'figure': figures.append(node['attrs']['fig'])
                    for v in node.values():
                        if isinstance(v, (dict, list)): walk(v)
            walk(document); return sorted(numbers), sorted(links), sorted(cites), sorted(figures)
        add('tokens-' + loc, tokens(doc) == tokens(source_doc), 'Conserva cifras, enlaces, fuentes y figuras del original.', 'Keep the original numbers, links, sources and figures.', loc)
        source_keys = {s['key'] for s in payload['sources']}
        for block in doc['blocks']:
            if block['type'] == 'figure':
                fig = payload['figures'].get(block['attrs']['fig'], {})
                path = store.directory(value) / fig.get('file', 'missing')
                ok = all(fig.get(f) for f in ('credit', 'licence')) and all(fig.get(f, {}).get(loc, '').strip() for f in ('alt', 'caption')) and path.is_file()
                add('figure-' + loc + '-' + block['id'], ok, 'Completa texto alternativo, pie, crédito y licencia de esta figura.', 'Complete the alt text, caption, credit and licence for this figure.', loc, block['id'])
        add('references-' + loc, not (set(tokens(doc)[2]) - source_keys), 'Cada cita debe tener una fuente.', 'Every citation needs a source.', loc)
        add('notes-' + loc, all(body for body in doc['footnotes'].values()), 'Completa todas las notas al pie.', 'Complete every footnote.', loc)
    valid_resources = True
    try: validate_sources(payload['sources']); validate_figures(payload['figures'])
    except ValueError: valid_resources = False
    add('resources', valid_resources, 'Revisa fuentes, figuras y derechos de uso.', 'Check sources, figures and reuse rights.')
    private_ok = True
    try: preview.privacy(value)
    except Exception: private_ok = False
    add('privacy', private_ok, 'La vista previa debe superar las comprobaciones de privacidad.', 'The preview must pass the privacy checks.')
    return results
