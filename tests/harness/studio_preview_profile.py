"""Measure fresh isolated previews; optional reference is read from local Git.

python3 -m tests.harness.studio_preview_profile --baseline-ref 25c64214
No live store, model, remote Git operation or service is used.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import time

from studio.server.preview import Preview
from studio.server.storage import Store
from tests.test_studio_storage import ROOT, DOC


def measure(factory, warm=False):
    with tempfile.TemporaryDirectory(prefix='studio-preview-timing-') as tmp:
        store = Store(Path(tmp) / 'data')
        try:
            slug = store.create('javier', 'essay', 'Timing fixture', 'en')['slug']
            for loc in ('en', 'es-419', 'zh-Hans'):
                doc = copy.deepcopy(DOC); doc['locale'] = loc
                store.save(slug, loc, 'javier', store.piece(slug)['head_rev'], doc, {})
                store.locale_state(slug, loc, 'javier', 'ready', True, 'Leí y entiendo el texto chino')
            preview = factory(store, ROOT)
            warming = None
            if warm:
                start = time.perf_counter(); preview.warm(); warming = time.perf_counter() - start
            start = time.perf_counter(); body = preview.page(slug, 'en'); cold = time.perf_counter() - start
            start = time.perf_counter(); preview.page(slug, 'en'); cached = time.perf_counter() - start
            return {'warm_seconds': warming, 'first_preview_seconds': cold,
                    'cached_preview_seconds': cached, 'html_bytes': len(body)}
        finally: store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-ref')
    args = parser.parse_args()
    if args.baseline_ref:
        source = subprocess.check_output(['git', 'show', args.baseline_ref + ':studio/server/preview.py'], cwd=ROOT)
        scope = {'__name__': 'studio.server.reference_preview', '__package__': 'studio.server'}
        exec(compile(source, '<reference-preview>', 'exec'), scope)
        print(json.dumps({'reference': args.baseline_ref, **measure(scope['Preview'])}), flush=True)
    print(json.dumps({'renderer': 'studio', **measure(Preview)}), flush=True)
    print(json.dumps({'renderer': 'studio-warmed', **measure(Preview, warm=True)}), flush=True)


if __name__ == '__main__': main()
