"""Seed one disposable Studio article from the validated editorial fixture.

Run before starting the host test server, with STUDIO_DATA pointing at an isolated
test store. No credentials, GitHub calls or dev API are used.
"""
import json
import os
from pathlib import Path
import shutil
from studio.server.storage import Store


def main():
    repo = Path(__file__).resolve().parents[2]
    source = repo / 'tests/fixtures/editorial/pieces/fixture-essay'
    store = Store(Path(os.environ['STUDIO_DATA']))
    try:
        piece = store.create('javier', 'essay', 'Studio browser fixture', 'en')
        slug = piece['slug']
        for kind in ('sources', 'figures'):
            store.resource(slug, kind, 'javier', json.loads((source / (kind + '.json')).read_text()))
        shutil.copytree(source / 'figures', store.directory(slug) / 'figures', dirs_exist_ok=True)
        for loc in ('en', 'es-419', 'zh-Hans'):
            doc = json.loads((source / ('doc.' + loc + '.json')).read_text())
            store.save(slug, loc, 'javier', store.piece(slug)['head_rev'], doc, {})
            store.locale_state(slug, loc, 'javier', 'ready', True, 'Leí y entiendo el texto chino')
        print(slug)
    finally: store.close()


if __name__ == '__main__': main()
