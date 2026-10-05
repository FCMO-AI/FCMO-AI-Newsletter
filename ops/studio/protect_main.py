"""Apply/read back a dedicated ruleset; preserve exact prior state for rollback.

API: https://docs.github.com/en/rest/repos/rules#create-a-repository-ruleset
An administrator runs this separately from Studio's two publication accounts.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

NAME = 'FCMO Studio protected main'
REPO = 'FCMO-AI/FCMO-AI-Newsletter'

def desired():
    return {'name': NAME, 'target': 'branch', 'enforcement': 'active',
            'bypass_actors': [], 'conditions': {'ref_name': {'include': ['refs/heads/main'], 'exclude': []}},
            'rules': [{'type': 'deletion'}, {'type': 'non_fast_forward'},
                      {'type': 'pull_request', 'parameters': {
                          'required_approving_review_count': 1, 'require_code_owner_review': True,
                          'dismiss_stale_reviews_on_push': True, 'require_last_push_approval': True,
                          'required_review_thread_resolution': True, 'allowed_merge_methods': ['merge']}},
                      {'type': 'required_status_checks', 'parameters': {
                          'strict_required_status_checks_policy': True,
                          'required_status_checks': [{'context': 'publish-gate'}]}}]}

def api(method, suffix, body=None):
    args = ['gh', 'api', '--hostname', 'github.com', '--method', method, 'repos/' + REPO + suffix]
    if body is not None: args += ['--input', '-']
    run = subprocess.run(args, input=json.dumps(body) if body is not None else None,
                         capture_output=True, text=True, timeout=60)
    if run.returncode: raise RuntimeError('GitHub refused the ruleset operation; inspect permissions/state before retrying.')
    return json.loads(run.stdout) if run.stdout.strip() else None

def writable(value):
    return {k: value[k] for k in ('name', 'target', 'enforcement', 'bypass_actors', 'conditions', 'rules')}

def contains(actual, expected):
    if isinstance(expected, dict): return isinstance(actual, dict) and all(k in actual and contains(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list): return isinstance(actual, list) and len(actual) == len(expected) and all(contains(a, e) for a, e in zip(actual, expected))
    return actual == expected

def save_receipt(path, receipt):
    temp = path.with_suffix('.tmp')
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: json.dump(receipt, f); f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    parser.add_argument('--state', type=Path, default=Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'fcmo-studio/main-ruleset.json')
    args = parser.parse_args()
    if args.dry_run and not args.rollback:
        print(json.dumps(desired(), indent=2)); return
    if args.rollback:
        saved = json.loads(args.state.read_text())
        if saved['repo'] != REPO or saved['desired'] != desired(): raise ValueError('Wrong rollback receipt.')
        if args.dry_run:
            print(json.dumps(saved['previous'], indent=2)); return
        if saved['id'] is None or 'applied' not in saved: raise ValueError('Apply response was not confirmed. Reconcile the named ruleset with the saved intent before rollback; do not resend.')
        current = api('GET', '/rulesets/' + str(saved['id']))
        if writable(current) != saved['applied']: raise ValueError('Rules changed since apply; reconcile before rollback.')
        if saved['previous'] is None:
            api('DELETE', '/rulesets/' + str(saved['id']))
            rows = api('GET', '/rulesets?includes_parents=false&per_page=100')
            if any(r['id'] == saved['id'] for r in rows): raise RuntimeError('Deletion not confirmed')
        else:
            api('PUT', '/rulesets/' + str(saved['id']), saved['previous'])
            if writable(api('GET', '/rulesets/' + str(saved['id']))) != saved['previous']: raise RuntimeError('Restoration not confirmed')
        args.state.rename(args.state.with_suffix('.rolled-back.json'))
        print('Previous ruleset state restored and verified.'); return
    owners = Path(__file__).resolve().parents[2] / '.github/CODEOWNERS'
    if 'REPLACE_WITH_' in owners.read_text(): raise ValueError('Replace CODEOWNERS placeholders with both real write-access accounts first.')
    if args.state.exists(): raise ValueError('Existing apply receipt; reconcile or rollback before another apply.')
    rows = api('GET', '/rulesets?includes_parents=false&per_page=100')
    matches = [r for r in rows if r['name'] == NAME]
    if len(matches) > 1: raise ValueError('Multiple matching rulesets; reconcile first.')
    previous = writable(api('GET', '/rulesets/' + str(matches[0]['id']))) if matches else None
    # Persist intent BEFORE the external effect. A lost response is not a retry license.
    args.state.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt = {'repo': REPO, 'previous': previous, 'desired': desired(), 'id': matches[0]['id'] if matches else None}
    fd = os.open(args.state, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: json.dump(receipt, f); f.flush(); os.fsync(f.fileno())
    result = api('PUT' if matches else 'POST', '/rulesets' + ('/' + str(matches[0]['id']) if matches else ''), desired())
    receipt['id'] = result['id']
    save_receipt(args.state, receipt)
    observed = writable(api('GET', '/rulesets/' + str(result['id'])))
    if not contains(observed, desired()): raise RuntimeError('Read-back differs')
    receipt['applied'] = observed
    save_receipt(args.state, receipt)
    print('Active protections verified. Rollback receipt: ' + str(args.state))

if __name__ == '__main__': main()
