#!/usr/bin/env python3
"""Offline GitHub control plane. Git merges/builds/served pages are real."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

root = Path(os.environ['DOGFOOD_ROOT'])
def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL, text=True).strip()
def ref(branch):
    try: return git('--git-dir', str(root / 'origin.git'), 'rev-parse', 'refs/heads/' + branch)
    except subprocess.CalledProcessError: return None

def execute(s, method, path, body, login):
    from ops.studio.protect_main import desired
    if path == 'user': return {'login': login}
    path = path.removeprefix('repos/FCMO-AI/FCMO-AI-Newsletter')
    parts = path.strip('/').split('/')
    if path.startswith('/git/ref/heads/'): return {'object': {'sha': ref(path.split('/heads/')[1])}} if ref(path.split('/heads/')[1]) else None
    if path == '/rules/branches/main':
        if (root / 'unprotected').exists(): return []
        return [{**r, 'ruleset_id': 1} for r in desired()['rules']]
    if path == '/rulesets/1': return desired()
    if path == '/pulls' and method == 'GET': return list(s['prs'].values())
    if path == '/pulls' and method == 'POST':
        n = str(len(s['prs']) + 1)
        p = {'number': int(n), 'head': {'ref': body['head'], 'sha': ref(body['head'])}, 'user': {'login': login}, 'merged': False, 'reviews': []}
        s['prs'][n] = p; return p
    if len(parts) >= 2 and parts[0] == 'pulls':
        p = s['prs'][parts[1]]
        if len(parts) == 2: return p
        if parts[2] == 'reviews':
            if method == 'GET': return p['reviews']
            assert login != p['user']['login'], 'Self review'
            row = {'state': 'APPROVED', 'commit_id': body['commit_id'], 'user': {'login': login}}
            p['reviews'].append(row); return row
        if parts[2] == 'merge':
            assert body['sha'] == p['head']['sha'] and p['reviews'] and not (root / 'unprotected').exists()
            checkout = root / 'merged'
            git('-C', str(checkout), 'fetch', 'origin', p['head']['ref'])
            git('-C', str(checkout), '-c', 'user.name=Codex', '-c', 'user.email=codex@openai.com', 'merge', '--no-ff', '-m', 'Dogfood reviewed publication', 'FETCH_HEAD')
            git('-C', str(checkout), 'push', 'origin', 'HEAD:main')
            sha = git('-C', str(checkout), 'rev-parse', 'HEAD')
            log = root / ('build-' + parts[1] + '.log')
            with log.open('w') as f:
                subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=checkout, stdout=f, stderr=f, check=True)
            (root / 'served').write_text(str(checkout / 'publish'))
            p.update(merged=True, merge_commit_sha=sha)
            return {'merged': True, 'sha': sha}
    if len(parts) == 3 and parts[0] == 'commits' and parts[2] == 'check-runs':
        # A fresh build from the candidate commit supplies the check, not a green stub.
        if parts[1] not in s['checked']:
            target = root / ('check-' + parts[1])
            git('clone', '--quiet', str(root / 'origin.git'), str(target))
            git('-C', str(target), 'checkout', '--detach', parts[1])
            with (root / ('check-' + parts[1] + '.log')).open('w') as f:
                subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=target, stdout=f, stderr=f, check=True)
            s['checked'].append(parts[1])
        return {'check_runs': [{'name': 'publish-gate', 'id': 1, 'status': 'completed', 'conclusion': 'success'}]}
    if path == '/actions/workflows/pages.yml/runs':
        return {'workflow_runs': [{'id': 1, 'head_sha': ref('main'), 'event': 'push', 'status': 'completed', 'conclusion': 'success'}]}
    if path == '/actions/workflows/pages.yml/dispatches':
        assert body == {'ref': 'main', 'inputs': {'operation': 'rollback'}}
        # Match production: rollback rebuilds current LKG, does not move main.
        (root / 'served').write_text(str(root / 'lkg-build' / 'publish'))
        s['rollback'] = True; return {}
    raise ValueError('Unsupported fake API ' + method + ' ' + path)

args = sys.argv[1:]
assert args and args[0] == 'api', 'Only API calls supported'
method = args[args.index('--method') + 1]
endpoint = next(a for a in args if a == 'user' or a.startswith('repos/'))
body = json.load(sys.stdin) if '--input' in args else None
login = 'fake-' + Path(os.environ['GH_CONFIG_DIR']).name
with (root / 'gh.lock').open('w') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    statefile = root / 'gh.json'
    s = json.loads(statefile.read_text()) if statefile.exists() else {'prs': {}, 'checked': [], 'calls': []}
    s['calls'].append({'method': method, 'endpoint': endpoint, 'login': login})
    result = execute(s, method, urlsplit(endpoint).path, body, login)
    statefile.write_text(json.dumps(s))
    print(json.dumps(result))
