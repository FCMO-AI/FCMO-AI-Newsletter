#!/usr/bin/env python3
"""Offline GitHub control plane for the Studio dogfood. Git merges, builds and served pages are real.

Two worlds share this file:
- legacy (no world.json in DOGFOOD_ROOT): eager mergeability, instant Pages, a fixed main. Unchanged.
- measured (world.json written by run.py, or by a test): the GitHub behaviour Studio meets in production,
  compressed so that a 70-minute deploy takes seconds. Every knob is a key of world.json:
    pages_run_s               one Pages deploy takes this long (70 min compressed to 7 s)
    pages_cancel_in_progress  a newer queued Pages run cancels the running one (GitHub concurrency)
    lazy_mergeable_s          after main moves, mergeable is null and mergeable_state 'unknown' this long
    behind                    a PR whose head does not contain main reports mergeable_state 'behind'
    merge_refusals            the first N merge calls are refused with HTTP 405 (transient GitHub trouble)
    gate_s                    the publish-gate check stays in progress this long; a newer head cancels it
    bot_after_merge           a tick number: the bot commits to main INSIDE the merge call, right after the merge run
                              is queued, so the merge's Pages run is replaced by the later one (no race with a harness)
    bot_after_gate            N moves of main, each injected INSIDE the call that completes a green publish-gate: main moves
                              exactly when Studio is about to merge, whatever the host's speed (a timed bot does not)
    behind (strict)           a PR whose head does not contain main reports 'behind' and its merge is refused (HTTP 405)
A bot (bot_commit, started by run.py) moves main from outside. A tree containing CONTENT_RED makes the
publish gate fail without a build; only the piece's own files are searched, never the whole tree (the
harness itself is part of the published tree). The gh process ticks the Pages queue lazily, on each call.
"""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit

# Split in source: the harness must never match itself in a tree that contains it.
CONTENT_RED = 'DOGFOOD-' + 'CONTENT-RED'
# The publication path of a piece (essay or issue), as Studio publishes it.
PIECE_PATHS = ('editorial/pieces', 'editorial/issues')
BOT_AUTHOR = ['-c', 'user.name=FCMO Dogfood Bot', '-c', 'user.email=dogfood-bot@example.invalid']


class GhError(Exception):
    """A GitHub refusal, printed on stderr the way gh prints an HTTP failure; exit 1."""
    def __init__(self, code, message): super().__init__(message); self.code = code


def git(*args):
    return subprocess.check_output(['git', *args], stderr=subprocess.DEVNULL, text=True).strip()


def ref(root, branch):
    try: return git('--git-dir', str(root / 'origin.git'), 'rev-parse', 'refs/heads/' + branch)
    except subprocess.CalledProcessError: return None


def is_ancestor(root, older, newer):
    return subprocess.run(['git', '--git-dir', str(root / 'origin.git'), 'merge-base', '--is-ancestor', older, newer]).returncode == 0


def load_state(root):
    statefile = root / 'gh.json'
    return json.loads(statefile.read_text()) if statefile.exists() else {'prs': {}, 'checked': [], 'calls': []}


def save_state(root, s):
    (root / 'gh.json').write_text(json.dumps(s))


def world_config(root):
    """None = legacy world. A world.json, even an empty one, switches the measured world on."""
    path = root / 'world.json'
    return json.loads(path.read_text()) if path.exists() else None


@contextlib.contextmanager
def locked(root):
    """One writer at a time: gh calls, the bot and the run.py harness all take the same lock."""
    with (root / 'gh.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


# ---- Pages: one concurrency group, ticked lazily ------------------------------------------------------

def enqueue_run(s, sha, now):
    """A new run replaces a queued one that has not started (GitHub: the pending run is replaced)."""
    runs = s.setdefault('pages', [])
    for run in runs:
        if run['status'] == 'queued':
            run.update(status='completed', conclusion='cancelled', completed_at=now)
    s['pages_seq'] = s.get('pages_seq', 0) + 1
    runs.append({'id': s['pages_seq'], 'head_sha': sha, 'status': 'queued', 'conclusion': None,
                 'queued_at': now, 'started_at': None, 'completed_at': None})


def tick_pages(root, s, now, world):
    """Advance the Pages queue to `now`. Deterministic for a given `now`, so tests pass explicit times."""
    duration = float(world.get('pages_run_s', 0))
    cancel = bool(world.get('pages_cancel_in_progress', True))
    changed = True
    while changed:
        changed = False
        for run in s.get('pages', []):
            if run['status'] == 'in_progress' and now >= run['started_at'] + duration:
                run.update(status='completed', conclusion='success', completed_at=run['started_at'] + duration)
                publish_served(root, s, run['head_sha'])
                changed = True
        queued = [r for r in s.get('pages', []) if r['status'] == 'queued']
        running = [r for r in s.get('pages', []) if r['status'] == 'in_progress']
        if queued and (not running or cancel):
            # cancel-in-progress: the newer run deploys; the run still going for an older commit is cancelled.
            for run in running:
                run.update(status='completed', conclusion='cancelled', completed_at=now)
            queued[0].update(status='in_progress', started_at=now)
            changed = True


def publish_served(root, s, head):
    """A successful run serves the merged build when its commit contains the merge."""
    merge = s.get('merge_sha')
    if merge and (head == merge or is_ancestor(root, merge, head)):
        (root / 'served').write_text(str(root / 'merged' / 'publish'))


# ---- main moves, mergeability, checks -----------------------------------------------------------------

def note_main_moved(s, sha, now):
    s['main_moved_at'] = now
    s.setdefault('main_moves', []).append({'sha': sha, 'at': now})


def pr_view(root, s, pr, now, world):
    """The PR as GitHub reports it: head is the live branch; mergeability is computed lazily after main moves."""
    head = ref(root, pr['head']['ref'])
    view = {**pr, 'head': {**pr['head'], 'sha': head}}
    if pr.get('merged'): return view
    main = ref(root, 'main')
    if now - s.get('main_moved_at', 0) < float(world.get('lazy_mergeable_s', 0)):
        # Right after main moves (or a refused merge) GitHub has not computed mergeability yet.
        view.update(mergeable=None, mergeable_state='unknown')
    elif world.get('behind') and not is_ancestor(root, main, head):
        view.update(mergeable=True, mergeable_state='behind')
    else:
        view.update(mergeable=True, mergeable_state='clean')
    return view


def gate_conclusion(root, s, sha):
    marked = subprocess.run(['git', '--git-dir', str(root / 'origin.git'), 'grep', '-q', CONTENT_RED, sha, '--', *PIECE_PATHS],
                            stderr=subprocess.DEVNULL).returncode == 0
    if marked: return 'failure'
    if sha not in s['checked']:
        target = root / ('check-' + sha)
        git('clone', '--quiet', str(root / 'origin.git'), str(target))
        git('-C', str(target), 'checkout', '--detach', sha)
        with (root / ('check-' + sha + '.log')).open('w') as f:
            result = subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=target, stdout=f, stderr=f)
        if result.returncode: return 'failure'
        s['checked'].append(sha)
    return 'success'


def world_check(root, s, sha, now, world):
    """publish-gate with cancel-in-progress: a new head cancels every gate still running for another head."""
    gate = s.setdefault('gate', {})
    rec = gate.get(sha)
    if rec is None:
        for other in gate.values():
            if other['status'] == 'in_progress':
                other.update(status='completed', conclusion='cancelled')
        rec = gate[sha] = {'id': len(gate) + 1, 'status': 'in_progress', 'started_at': now, 'conclusion': None}
    if rec['status'] == 'in_progress' and now >= rec['started_at'] + float(world.get('gate_s', 0)):
        rec.update(status='completed', conclusion=gate_conclusion(root, s, sha))
        done = s.get('gate_bot_done', 0)
        if rec['conclusion'] == 'success' and done < int(world.get('bot_after_gate', 0)):
            # Main moves right after the gate went green: the PR is now behind and the base must be replayed.
            s['gate_bot_done'] = done + 1
            bot_push(root, s, int(world.get('bot_gate_tick', 900)) + done, now, queue_run=True)
    return {'check_runs': [{'name': 'publish-gate', 'id': rec['id'], 'status': rec['status'], 'conclusion': rec['conclusion']}]}


def pages_runs(s):
    return {'workflow_runs': [{'id': r['id'], 'head_sha': r['head_sha'], 'event': 'push', 'status': r['status'],
                               'conclusion': r['conclusion']} for r in s.get('pages', [])]}


# ---- the bot ------------------------------------------------------------------------------------------

def bot_push(root, s, number, now, queue_run=None):
    """The bot's commit on main. The caller holds the lock and owns the state `s`."""
    clone = root / 'bot'
    if not clone.exists(): git('clone', '--quiet', str(root / 'origin.git'), str(clone))
    git('-C', str(clone), 'fetch', '--quiet', 'origin', 'main')
    git('-C', str(clone), 'reset', '--quiet', '--hard', 'origin/main')
    (clone / 'bot').mkdir(exist_ok=True)
    (clone / 'bot' / ('tick-%d.txt' % number)).write_text('tick %d\n' % number)
    git('-C', str(clone), 'add', '-A')
    subprocess.run(['git', *BOT_AUTHOR, '-C', str(clone), 'commit', '--quiet', '-m', 'Bot tick %d' % number], check=True)
    subprocess.run(['git', '-C', str(clone), 'push', '--quiet', 'origin', 'HEAD:main'], check=True, capture_output=True)
    sha = git('-C', str(clone), 'rev-parse', 'HEAD')
    note_main_moved(s, sha, now)
    if world_config(root) is not None if queue_run is None else queue_run: enqueue_run(s, sha, now)
    return sha


def bot_commit(root, number, now=None):
    """Another contributor commits to main under Studio's feet (a file outside every piece)."""
    now = time.time() if now is None else now
    with locked(root):
        s = load_state(root)
        sha = bot_push(root, s, number, now)
        save_state(root, s)
    return sha


# ---- merges -------------------------------------------------------------------------------------------

def write_world(root, knobs):
    """Replace the measured world. Under the lock, so a gh call never sees the new knobs with the old refusal count."""
    with locked(root):
        s = load_state(root); s.pop('refusals_left', None); s.pop('gate_bot_done', None); save_state(root, s)
        (root / 'world.json').write_text(json.dumps(knobs))


def world_merge(root, s, pr, sha_asked, now, world):
    head = ref(root, pr['head']['ref'])
    assert sha_asked == head and not (root / 'unprotected').exists(), 'merge precondition'
    main = ref(root, 'main')
    if world.get('behind') and not is_ancestor(root, main, head):
        # Strict policy: a head that does not contain main cannot be merged. Studio must replay the approved bytes.
        s['behind_refusals'] = s.get('behind_refusals', 0) + 1
        raise GhError(405, 'Head branch is out of date')
    left = s.get('refusals_left')
    if left is None: left = int(world.get('merge_refusals', 0))
    if left > 0:
        # GitHub refuses and starts computing mergeability again: unknown for the lazy window.
        s['refusals_left'] = left - 1; s['refusals_done'] = s.get('refusals_done', 0) + 1; s['main_moved_at'] = now
        raise GhError(405, 'Pull Request is not mergeable')
    s['refusals_left'] = 0
    if now - s.get('main_moved_at', 0) < float(world.get('lazy_mergeable_s', 0)):
        raise GhError(405, 'Pull Request is not mergeable (mergeability is being computed)')
    checkout = root / 'merged'
    git('-C', str(checkout), 'fetch', '-q', 'origin', 'main')
    git('-C', str(checkout), 'fetch', '-q', 'origin', pr['head']['ref'])
    git('-C', str(checkout), 'reset', '-q', '--hard', 'origin/main')
    git('-C', str(checkout), '-c', 'user.name=Codex', '-c', 'user.email=codex@openai.com', 'merge', '--no-ff', '-q', '-m', 'Dogfood author publication', head)
    git('-C', str(checkout), 'push', '-q', 'origin', 'HEAD:main')
    merged = git('-C', str(checkout), 'rev-parse', 'HEAD')
    with (root / ('build-' + str(pr['number']) + '.log')).open('w') as f:
        subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=checkout, stdout=f, stderr=f, check=True)
    s['merge_sha'] = merged
    # How many times main moved before this merge: the harness asserts main really moved under the piece.
    s['moves_before_merge'] = len(s.get('main_moves', []))
    note_main_moved(s, merged, now)
    enqueue_run(s, merged, now)
    if world.get('bot_after_merge'):
        # Atomic with the merge: the later commit queues a run that replaces the merge's still-queued run.
        s['later_sha'] = bot_push(root, s, int(world['bot_after_merge']), now, queue_run=True)
    pr.update(merged=True, merge_commit_sha=merged)
    return {'merged': True, 'sha': merged}


def legacy_merge(root, s, pr, body):
    assert body['sha'] == pr['head']['sha'] and not (root / 'unprotected').exists()
    checkout = root / 'merged'
    git('-C', str(checkout), 'fetch', 'origin', pr['head']['ref'])
    git('-C', str(checkout), '-c', 'user.name=Codex', '-c', 'user.email=codex@openai.com', 'merge', '--no-ff', '-m', 'Dogfood author publication', 'FETCH_HEAD')
    git('-C', str(checkout), 'push', 'origin', 'HEAD:main')
    sha = git('-C', str(checkout), 'rev-parse', 'HEAD')
    with (root / ('build-' + str(pr['number']) + '.log')).open('w') as f:
        subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=checkout, stdout=f, stderr=f, check=True)
    (root / 'served').write_text(str(checkout / 'publish'))
    pr.update(merged=True, merge_commit_sha=sha)
    return {'merged': True, 'sha': sha}


# ---- the API surface ----------------------------------------------------------------------------------

def execute(root, s, method, path, body, login, now, world):
    from ops.studio.protect_main import desired
    if path == 'user': return {'login': login}
    path = path.removeprefix('repos/FCMO-AI/FCMO-AI-Newsletter')
    parts = path.strip('/').split('/')
    if path.startswith('/git/ref/heads/'):
        sha = ref(root, path.split('/heads/')[1])
        return {'object': {'sha': sha}} if sha else None
    if path == '/rules/branches/main':
        if (root / 'unprotected').exists(): return []
        return [{**r, 'ruleset_id': 1} for r in desired()['rules']]
    if path == '/rulesets/1': return desired()
    if path == '/pulls' and method == 'GET':
        return [pr_view(root, s, p, now, world) if world is not None else p for p in s['prs'].values()]
    if path == '/pulls' and method == 'POST':
        n = str(len(s['prs']) + 1)
        p = {'number': int(n), 'head': {'ref': body['head'], 'sha': ref(root, body['head'])}, 'user': {'login': login}, 'merged': False, 'reviews': []}
        s['prs'][n] = p; return p
    if len(parts) >= 2 and parts[0] == 'pulls':
        p = s['prs'][parts[1]]
        if len(parts) == 2:
            return pr_view(root, s, p, now, world) if world is not None else p
        if parts[2] == 'reviews':
            if method == 'GET': return p['reviews']
            assert login != p['user']['login'], 'Self review'
            row = {'state': 'APPROVED', 'commit_id': body['commit_id'], 'user': {'login': login}}
            p['reviews'].append(row); return row
        if parts[2] == 'merge':
            if world is None: return legacy_merge(root, s, p, body)
            return world_merge(root, s, p, body['sha'], now, world)
    if len(parts) == 2 and parts[0] == 'commits':
        # The first-parent diff of a commit, as GitHub lists it (the merge-diff check reads it).
        names = git('--git-dir', str(root / 'origin.git'), 'diff', '--name-only', parts[1] + '^1', parts[1]).splitlines()
        return {'sha': parts[1], 'files': [{'filename': n} for n in names]}
    if len(parts) == 3 and parts[0] == 'commits' and parts[2] == 'check-runs':
        if world is not None: return world_check(root, s, parts[1], now, world)
        # A fresh build from the candidate commit supplies the check, not a green stub.
        if parts[1] not in s['checked']:
            target = root / ('check-' + parts[1])
            git('clone', '--quiet', str(root / 'origin.git'), str(target))
            git('-C', str(target), 'checkout', '--detach', parts[1])
            with (root / ('check-' + parts[1] + '.log')).open('w') as f:
                subprocess.run([sys.executable, 'ops/publish.py', '--check', '--fixture-build'], cwd=target, stdout=f, stderr=f, check=True)
            s['checked'].append(parts[1])
        return {'check_runs': [{'name': 'publish-gate', 'id': 1, 'status': 'completed', 'conclusion': 'success'}]}
    if len(parts) == 2 and parts[0] == 'compare' and '...' in parts[1]:
        # GitHub's comparison: 'ahead' when the merge is an ancestor of the run's commit, as Studio's deploy check reads it.
        base, head = parts[1].split('...', 1)
        if base == head: return {'status': 'identical'}
        return {'status': 'ahead' if is_ancestor(root, base, head) else 'diverged'}
    if path == '/actions/workflows/pages.yml/runs':
        if world is not None: return pages_runs(s)
        return {'workflow_runs': [{'id': 1, 'head_sha': ref(root, 'main'), 'event': 'push', 'status': 'completed', 'conclusion': 'success'}]}
    if path == '/actions/workflows/pages.yml/dispatches':
        assert body == {'ref': 'main', 'inputs': {'operation': 'rollback'}}
        # Match production: rollback rebuilds current LKG, does not move main.
        (root / 'served').write_text(str(root / 'lkg-build' / 'publish'))
        s['rollback'] = True; return {}
    raise ValueError('Unsupported fake API ' + method + ' ' + path)


def main():
    root = Path(os.environ['DOGFOOD_ROOT'])
    args = sys.argv[1:]
    if args == ['auth', 'status', '--hostname', 'github.com']:
        raise SystemExit(0)
    assert args and args[0] == 'api', 'Only API calls supported'
    method = args[args.index('--method') + 1]
    endpoint = next(a for a in args if a == 'user' or a.startswith('repos/'))
    body = json.load(sys.stdin) if '--input' in args else None
    login = 'fake-' + Path(os.environ['GH_CONFIG_DIR']).name
    with locked(root):
        s = load_state(root)
        now = time.time()
        world = world_config(root)
        if world is not None: tick_pages(root, s, now, world)
        s['calls'].append({'method': method, 'endpoint': endpoint, 'login': login})
        try:
            result = execute(root, s, method, urlsplit(endpoint).path, body, login, now, world)
        except GhError as exc:
            save_state(root, s)
            print('HTTP %d: %s' % (exc.code, exc), file=sys.stderr)
            raise SystemExit(1)
        save_state(root, s)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
