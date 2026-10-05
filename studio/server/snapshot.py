"""Pin the newsroom library to an immutable commit in the private Studio clone."""
from pathlib import Path
from .storage import git
from .publishing import Refused

PUBLIC_REMOTE = 'https://github.com/FCMO-AI/FCMO-AI-Newsletter'

def refresh(store, github):
    clone = store.data / 'clone'
    remotes = git(clone, 'remote').splitlines()
    if 'origin' not in remotes: git(clone, 'remote', 'add', 'origin', PUBLIC_REMOTE)
    github.validate_remote(clone)
    git(clone, 'fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
    sha = git(clone, 'rev-parse', 'refs/remotes/origin/main')
    snapshot = store.data / 'snapshots' / sha
    if not snapshot.exists():
        snapshot.parent.mkdir(mode=0o700, exist_ok=True)
        git(clone, 'worktree', 'add', '--detach', '-q', str(snapshot), sha)
    # A snapshot is never a draft ancestor or push source; no public input is edited.
    if git(snapshot, 'rev-parse', 'HEAD') != sha or git(snapshot, 'status', '--porcelain', '--untracked-files=all'):
        raise Refused('La copia de lectura cambió; no se puede usar para publicar.')
    store.public_root = snapshot
    return snapshot
