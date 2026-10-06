"""Public synthetic fixture matching Studio's frozen essay document contract."""
import copy

LOCALES = ('en', 'es-419', 'zh-Hans')


def piece_fixture():
    piece = {'schema': 'fcmo-piece-v1', 'id': 'FCMO-P-123456789abc',
             'kind': 'essay', 'slug': 'a-careful-decision', 'brand': 'fcmo',
             'authors': [{'key': 'javier', 'name': 'Javier Castellanos Peña'}],
             'source_locale': 'es-419', 'status': 'published',
             'first_published_at': '2026-10-05T12:00:00Z',
             'locales': {locale: 'ready' for locale in LOCALES},
             'distribution': {'email': True},
             'provenance': {locale: {'origin': 'human_translated', 'human_reviewed': True,
                                    'reviewer': 'Javier'} for locale in LOCALES},
             'sources': [{'key': 'source-one', 'title': 'Primary source',
                          'url': 'https://example.org/source'}], 'figures': {}, 'docs': {}}
    for locale, title, body in [('en', 'A careful decision', 'Consider the evidence.'),
                                 ('es-419', 'Una decisión cuidadosa', 'Considera la evidencia.'),
                                 ('zh-Hans', '审慎的决定', '请考虑证据。')]:
        piece['docs'][locale] = {'schema': 'fcmo-essay-doc-v1', 'locale': locale,
                                'title': title, 'dek': body,
                                'blocks': [{'id': 'b-12345678', 'type': 'p', 'content': [
                                    {'t': 'text', 'v': body}, {'t': 'fn', 'id': 'fn-87654321'},
                                    {'t': 'cite', 'key': 'source-one', 'locator': 'p. 2'}]},
                                    {'id': 'b-23456789', 'type': 'ul', 'items': [[
                                        {'t': 'text', 'v': body, 'marks': ['strong']}]]}],
                                'footnotes': {'fn-87654321': [{'t': 'text', 'v': body},
                                    {'t': 'link', 'href': 'https://example.org/note',
                                     'c': [{'t': 'text', 'v': 'Reference'}]}]}}
    return copy.deepcopy(piece)
