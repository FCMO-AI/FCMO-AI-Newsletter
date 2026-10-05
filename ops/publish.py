#!/usr/bin/env python3
"""Validation only: reconstruct the immutable public input; never deploy or push.

Pages remains the sole deployment writer, with browser and public-origin proof.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', required=True)
    parser.add_argument('--out', type=Path, default=ROOT / 'publish')
    args = parser.parse_args(argv)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_', 'GHOST_'))}
    env['GHOST_CONTENT_URL'] = ''; env['GHOST_CONTENT_API_KEY'] = ''
    commands = [
        ['git', 'rev-parse', '--verify', 'refs/tags/lkg^{commit}'],
        [sys.executable, 'tools/paper/build.py', '--stories', 'site/data/stories.v2.json', '--status', 'site/data/newsroom-status.json', '--editorial', 'editorial', '--out', str(args.out), '--base', '/FCMO-AI-Newsletter/'],
        [sys.executable, 'tools/validate_agent_hygiene.py', '--site', str(args.out)],
        [sys.executable, 'tools/gates/run_all.py', str(args.out)],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, timeout=1800)
        if result.returncode:
            print('Publicación rechazada: LKG, construcción o comprobaciones incompletas.', file=sys.stderr)
            return 2
    print('Comprobaciones locales completas. Pages aún debe verificar navegador, despliegue y origen público.')
    return 0

if __name__ == '__main__': raise SystemExit(main())
