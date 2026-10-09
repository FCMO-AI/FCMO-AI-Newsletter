"""Refuse stale editor artifacts; a rebuild is an explicit host prerequisite."""
import hashlib
import json
import os
from pathlib import Path


def ready(repo):
    web = Path(repo) / 'studio/web'
    try:
        manifest = json.loads((web / 'dist/build-manifest.json').read_text())
        sources = [web / name for name in ('build.mjs', 'offline-build.mjs', 'package.json', 'package-lock.json')]
        sources.extend(p for p in (web / 'offline').rglob('*') if p.is_file())
        sources.extend(p for p in (web / 'src').rglob('*') if p.is_file())
        sources.append(Path(repo) / 'site-src/assets/css/essay.css')
        sources.extend((Path(repo) / 'site-src/assets/fonts').glob('*.woff2'))
        expected = {Path(os.path.relpath(p, web)).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        return manifest['schema'] == 'fcmo-studio-bundle-v1' and manifest['sources'] == expected and all(
            hashlib.sha256((web / 'dist' / name).read_bytes()).hexdigest() == manifest['artifacts'][name]
            for name in ('app.js', 'app.css', 'index.html'))
    except (OSError, ValueError, KeyError, TypeError):
        return False
