"""Private draft rendering through the production builder; never a release input.

Readiness and provenance are preserved in storage. Only this private, authenticated
rendering view makes existing draft documents visible, with no review claim.
"""
import argparse
import json
from pathlib import Path
from tools.paper.build import PaperBuilder
from .validation import validate_doc, LOCALES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--editorial', type=Path, required=True)
    parser.add_argument('--stories', type=Path, required=True)
    parser.add_argument('--status', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    payload = json.loads(args.snapshot.read_text())
    empty = args.snapshot.parent / 'empty-editorial'; empty.mkdir(exist_ok=True)
    builder = PaperBuilder(stories_path=args.stories, status_path=args.status, editorial_path=empty, out=args.out, base=args.base)
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
