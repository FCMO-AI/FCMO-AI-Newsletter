#!/usr/bin/env python3
"""Print the reviewable ruleset request. This script has no apply operation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shlex

RULESET = Path(__file__).with_name('publish-ruleset.json')


def plan(repository: str) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('expected owner/repository')
    endpoint = f'repos/{repository}/rulesets'
    return {'method': 'POST', 'endpoint': endpoint,
            'body': json.loads(RULESET.read_text(encoding='utf-8')),
            'operator_command': f'gh api --method POST {shlex.quote(endpoint)} --input ops/publish-ruleset.json',
            'state': 'proposed; not applied'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='FCMO-AI/FCMO-AI-Newsletter')
    args = parser.parse_args()
    print(json.dumps(plan(args.repo), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
