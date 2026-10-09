"""Private draft rendering through the production builder; never a release input.

Readiness and provenance are preserved in storage. Only this private, authenticated
rendering view makes existing draft documents visible, with no review claim.
"""
import argparse
from collections import Counter
import importlib
import json
from pathlib import Path
from tools.paper.build import PaperBuilder, esc
from tools.paper.routes import href, slugify
from .validation import validate_doc, LOCALES

def warm():
    # Templates are Python modules, not a separate Jinja compiler. Importing
    # them warms Python's compiled bytecode cache for subsequent renderer runs.
    importlib.import_module('tools.paper.templates.essay')


class StudioPaperBuilder(PaperBuilder):
    """Same full production build, with corpus membership indexed once.

    Counts are per story (duplicates in one story still count once), and first
    encounter order is retained for the production sort's equal-key ties.
    The index belongs to this immutable build, never to another snapshot.
    """
    def _topic_links(self, locale, *, exclude_topic='', exclude_org='', limit=5):
        if not hasattr(self, '_studio_neighbors'):
            counts = {field: Counter(value for story in self.live for value in set(story.get(field) or []))
                      for field in ('topics', 'organizations')}
            rows = {}
            for story in self.live:
                for field, route in (('topics', 'topic'), ('organizations', 'org')):
                    for value in story.get(field, []):
                        count = counts[field][value]
                        if field == 'topics' and count < 3: continue
                        rows.setdefault((value, route), (count, value, slugify(value), route))
            self._studio_neighbors = tuple(rows.values())
            self._studio_neighbor_html = {}
        key = (locale['code'], locale['path_prefix'], exclude_topic, exclude_org, limit)
        if key not in self._studio_neighbor_html:
            selected = []
            for count, value, slug, route in self._studio_neighbors:
                exclude = exclude_topic if route == 'topic' else exclude_org
                if value == exclude or slug == exclude: continue
                selected.append((count, value, href(self.base, locale['path_prefix'] + route + '/' + slug + '/')))
            selected.sort(key=lambda row: (-row[0], row[1].casefold()))
            links = ''.join(f'<li><a href="{esc(url)}" translate="no">{esc(value)}</a><span>{count}</span></li>'
                            for count, value, url in selected[:limit])
            title = esc(self.catalogs[locale['code']]['strings']['front']['see_all'])
            self._studio_neighbor_html[key] = f'<nav class="taxonomy-neighbors"><h2>{title}</h2><ul>{links}</ul></nav>' if links else ''
        return self._studio_neighbor_html[key]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--warm', action='store_true')
    parser.add_argument('--snapshot', type=Path)
    for name in ('editorial', 'stories', 'status', 'out'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--base')
    args = parser.parse_args()
    warm()
    if args.warm: return
    if any(getattr(args, name) is None for name in ('editorial', 'stories', 'status', 'out', 'base')):
        parser.error('Configura editorial, stories, status, out y base para construir la vista previa.')
    if not args.snapshot:
        StudioPaperBuilder(stories_path=args.stories, status_path=args.status, editorial_path=args.editorial,
                           out=args.out, base=args.base).build()
        return
    payload = json.loads(args.snapshot.read_text())
    empty = args.snapshot.parent / 'empty-editorial'; empty.mkdir(exist_ok=True)
    builder = StudioPaperBuilder(stories_path=args.stories, status_path=args.status, editorial_path=empty, out=args.out, base=args.base)
    piece = payload['piece']
    for loc, doc in payload['docs'].items():
        validate_doc(doc, loc)
        # Empty typing surfaces still have a production paragraph/title shape.
        if not doc['blocks']: doc['blocks'] = [{'id': 'b-00000000', 'type': 'p', 'content': []}]
        if not doc['title']: doc['title'] = {'en': 'Untitled draft', 'es-419': 'Borrador sin título', 'zh-Hans': '未命名草稿'}[loc]
    piece.update(docs=payload['docs'], sources=payload['sources'], figures=payload['figures'], provenance=payload['provenance'], directory=args.editorial / 'pieces' / piece['slug'])
    piece['locales'] = {loc: 'ready' if loc in piece['docs'] else 'pending' for loc in LOCALES}
    builder.editorial_path = args.editorial
    builder.editorial_pieces = [piece]
    builder.build()


if __name__ == '__main__': main()
