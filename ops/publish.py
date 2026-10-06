#!/usr/bin/env python3
"""Validate locally or request the reviewed main Pages workflow.

Checks and dry runs never deploy or push. Pages remains the sole deployment
writer, with browser and public-origin proof.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import json
import shutil
import tempfile

REPOSITORY = 'FCMO-AI/FCMO-AI-Newsletter'

ROOT = Path(__file__).resolve().parents[1]

def git(repository: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(repository), *args], check=True,
                          text=True, capture_output=True).stdout.strip()


def local_bare(repository: str | Path) -> Path:
    path = Path(repository).expanduser().resolve()
    if not path.is_dir() or git(path, 'rev-parse', '--is-bare-repository') != 'true':
        raise ValueError('expected a local bare repository directory; URLs are refused')
    return path


def step(root: Path, *args: str) -> None:
    env = {k:v for k,v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_', 'GHOST_'))}
    # Local evidence must not depend on live Ghost content or a publisher key.
    for key in ('GHOST_CONTENT_URL', 'GHOST_CONTENT_API_KEY', 'GHOST_PORTAL_URL'):
        env.pop(key, None)
    result = subprocess.run([sys.executable, *map(str, args)], cwd=root, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f'publication blocked: {args[0]} (exit {result.returncode})')


def build_and_check(root: Path, out: Path, sha: str) -> dict:
    # Keep the established six-gate overlay boundary even though Pages serves paper.
    step(root, 'tools/verify_release.py')
    common = ['tools/paper/build.py', '--stories', 'site/data/stories.v2.json',
              '--status', 'site/data/newsroom-status.json', '--editorial', 'editorial', '--out', str(out),
              '--base', '/FCMO-AI-Newsletter/']
    step(root, *common)
    shutil.copyfile(root / 'i18n/glossary.yml', out / 'data/glossary.json')
    # Reject unsafe prose/assets before starting the slower browser stages.
    step(root, 'tools/gates/run_all.py', str(out))
    og = out.parent / 'og'
    step(root, 'tools/paper/og_image.py', '--stories', 'site/data/stories.v2.json', '--out', str(og))
    step(root, *common, '--og-source', str(og))
    shutil.copyfile(root / 'i18n/glossary.yml', out / 'data/glossary.json')
    step(root, 'tools/gates/run_all.py', str(out))
    step(root, 'tools/validate_agent_hygiene.py', '--site', str(out))
    step(root, 'tests/oraculos/verificar_paper.py', str(out))
    identity = out / 'deployment-identity.json'
    step(root, 'tools/build_deployment_identity.py', '--site', str(out),
         '--output', str(identity), '--source-commit', sha)
    return json.loads(identity.read_text(encoding='utf-8'))


def snapshot_check(repository: Path, ref: str, mode: str) -> dict:
    # Resolve once, then use only that commit; concurrent updates cannot change bytes.
    sha = git(repository, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}')
    with tempfile.TemporaryDirectory(prefix='fcmo-publish-') as temporary:
        base = Path(temporary)
        source = base / 'source'
        subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', '--no-checkout',
                        '--', str(repository), str(source)], check=True)
        git(source, 'checkout', '--quiet', '--detach', sha)
        identity = build_and_check(source, base / 'candidate', sha)
    return {'schema': 'fcmo-protected-publish-check-v1', 'mode': mode,
            'source_commit': sha, 'checks': 'PASS', 'deployment': 'not-requested',
            'identity': identity}


def dry_run(repository: str | Path, ref: str = 'refs/heads/main') -> dict:
    return snapshot_check(local_bare(repository), ref, 'dry-run')


def dispatch(operation: str) -> None:
    if operation not in {'deploy', 'rollback'}:
        raise ValueError('operation must be deploy or rollback')
    subprocess.run(['gh', 'workflow', 'run', 'pages.yml', '--repo', REPOSITORY,
                    '--ref', 'main', '--field', f'operation={operation}'], check=True)
    print('Solicitud enviada a Pages en main. La publicación se confirma sólo después de live-verify.')




def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--check', action='store_true')
    modes.add_argument('--dry-run', action='store_true')
    modes.add_argument('--publish', action='store_true')
    modes.add_argument('--rollback', action='store_true')
    parser.add_argument('--local-bare', type=Path)
    parser.add_argument('--ref', default='refs/heads/main')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--out', type=Path, default=ROOT / 'publish')
    parser.add_argument('--fixture-build', action='store_true', help='Test-fixture build only; never sufficient for publication')
    args = parser.parse_args(argv)
    if not args.check:
        try:
            if args.fixture_build or args.out != ROOT / 'publish': raise ValueError('candidate overrides require --check')
            if args.publish or args.rollback:
                if args.local_bare or args.receipt or args.ref != 'refs/heads/main': raise ValueError('dispatch accepts only reviewed main')
                dispatch('rollback' if args.rollback else 'deploy')
                return 0
            if not args.local_bare: raise ValueError('--dry-run requires --local-bare')
            payload = json.dumps(dry_run(args.local_bare, args.ref), ensure_ascii=False, indent=2) + '\n'
            if args.receipt: args.receipt.write_text(payload, encoding='utf-8')
            print(payload, end='')
            return 0
        except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError):
            print('Publicación rechazada: comprobaciones incompletas.', file=sys.stderr)
            return 2
    if args.local_bare or args.receipt or args.ref != 'refs/heads/main': parser.error('--check uses the local candidate')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GH_TOKEN', 'GITHUB_TOKEN', 'STUDIO_', 'GHOST_'))}
    env['GHOST_CONTENT_URL'] = ''; env['GHOST_CONTENT_API_KEY'] = ''
    commands = []
    if not args.fixture_build:
        commands += [[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], [sys.executable, 'tools/verify_release.py']]
    commands += [
        ['git', 'rev-parse', '--verify', 'refs/tags/lkg^{commit}'],
        [sys.executable, 'tools/paper/build.py', '--stories', 'site/data/stories.v2.json', '--status', 'site/data/newsroom-status.json', '--editorial', 'editorial', '--out', str(args.out), '--base', '/FCMO-AI-Newsletter/'],
        [sys.executable, 'tools/validate_agent_hygiene.py', '--site', str(args.out)],
        [sys.executable, 'tools/gates/run_all.py', str(args.out)],
    ]
    if not args.fixture_build:
        commands += [[sys.executable, 'tests/oraculos/verificar_paper.py', str(args.out)]]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, timeout=1800)
        if result.returncode:
            print('Publicación rechazada: LKG, construcción o comprobaciones incompletas.', file=sys.stderr)
            return 2
    print(('Construcción de fixture únicamente. ' if args.fixture_build else 'Suite, integridad y navegador completos. ') + 'Comprobaciones locales completas. Pages aún debe verificar navegador, despliegue y origen público.')
    return 0

if __name__ == '__main__': raise SystemExit(main())
