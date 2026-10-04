#!/usr/bin/env python3
"""Plan or seed ops-ledger in a LOCAL bare clone. Never push or alter main."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ops.publish import git, local_bare

LEDGER = 'ops/publication-desk/LEDGER.jsonl'
REF = 'refs/heads/ops-ledger'


def raw(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(['git', '-C', str(repo), *args], input=data,
                          check=True, capture_output=True).stdout



def validate_ledger(data: bytes) -> list[dict]:
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError('ledger must contain object records')
    ids = [row.get('run_id') for row in rows]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError('ledger must contain unique nonempty run_id values')
    times = []
    for row in rows:
        timestamp = datetime.fromisoformat(row['T0'].replace('Z', '+00:00'))
        if timestamp.tzinfo is None:
            raise ValueError('ledger activation timestamp must include timezone')
        times.append(timestamp.astimezone(timezone.utc))
    if times != sorted(times):
        raise ValueError('ledger activations must be chronological in UTC')
    return rows

def migrate(source: Path, source_ref: str, destination: str | Path, *, apply: bool = False) -> dict:
    source = Path(source).resolve()
    destination = local_bare(destination)
    sha = git(source, 'rev-parse', '--verify', '--end-of-options', f'{source_ref}^{{commit}}')
    data = raw(source, 'show', f'{sha}:{LEDGER}')
    rows = validate_ledger(data)
    existing = subprocess.run(['git', '-C', str(destination), 'rev-parse', '--verify', REF],
                              capture_output=True, text=True)
    if existing.returncode == 0:
        previous = existing.stdout.strip()
        if git(destination, 'ls-tree', '-r', '--name-only', REF) != LEDGER or raw(destination, 'show', f'{REF}:{LEDGER}') != data:
            raise ValueError('existing ops-ledger differs; refuse to overwrite or lose appended records')
    else:
        previous = None
    plan = {'schema': 'fcmo-ledger-migration-v1', 'source_commit': sha,
            'destination_ref': REF, 'records': len(rows),
            'ledger_sha256': hashlib.sha256(data).hexdigest(), 'mode': 'apply-local' if apply else 'plan'}
    if not apply:
        return plan
    if previous:
        plan['ledger_commit'] = previous
        return plan
    # Build an orphan tree containing only the ledger. No worktree/checkout mutation.
    blob = raw(destination, 'hash-object', '-w', '--stdin', data=data).decode().strip()
    desk = raw(destination, 'mktree', data=f'100644 blob {blob}\tLEDGER.jsonl\n'.encode()).decode().strip()
    ops = raw(destination, 'mktree', data=f'040000 tree {desk}\tpublication-desk\n'.encode()).decode().strip()
    tree = raw(destination, 'mktree', data=f'040000 tree {ops}\tops\n'.encode()).decode().strip()
    commit = raw(destination, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com',
                 'commit-tree', tree, data=b'ops: migrate public desk ledger to isolated branch\n').decode().strip()
    # Compare-and-swap: concurrent creation fails instead of replacing another writer.
    raw(destination, 'update-ref', REF, commit, '0' * 40)
    plan['ledger_commit'] = commit
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source-ref', required=True, help='commit captured BEFORE main stops tracking the ledger')
    parser.add_argument('--local-bare', type=Path, required=True)
    parser.add_argument('--apply-local', action='store_true', help='write ops-ledger only in this local bare clone')
    args = parser.parse_args()
    try:
        print(json.dumps(migrate(args.source, args.source_ref, args.local_bare,
                                 apply=args.apply_local), indent=2))
        return 0
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f'LEDGER MIGRATION REFUSED: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
