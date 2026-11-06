#!/usr/bin/env python3
"""Promote an already guarded, single-commit newsroom candidate without starvation.

Run after committing the generated paths: python tools/refresh_promote.py
--build-base <parent-of-candidate>. Only origin/main is updated, by a normal
fast-forward push. Corpus advances are retained; constructor changes invalidate
the candidate. Each retry compares the frozen candidate's airlock receipt with
the fetched release. Missing/ambiguous receipts fail closed.

Reapplication uses a temporary Git index: concurrent generated changes are
replaced only when the candidate's receipt is newer. Other remote paths, HEAD
and the working tree are never rewritten. A push race rechecks all conditions,
at most five times.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

GENERATED = ("release-src", "release-overlay", "site", "READY_TO_PUBLISH.md")
CONSTRUCTOR = ("scaffold", "tools", ".github/workflows/daily-refresh.yml")
STATUS = "site/data/newsroom-status.json"


def git(*args: str, data: str | None = None, env=None) -> str:
    return subprocess.run(["git", *args], input=data, text=True, capture_output=True,
                          env=env, check=True).stdout


def changed(base: str, head: str, *paths: str) -> bool:
    return bool(git("diff", "--name-only", "-z", base, head, "--", *paths))


def generated(path: str) -> bool:
    return any(path == root or path.startswith(root + "/") for root in GENERATED)


def receipt(revision: str) -> tuple[datetime, str]:
    doc = json.loads(git("show", f"{revision}:{STATUS}"))
    stamp = datetime.fromisoformat(doc["airlock_generated_at"].replace("Z", "+00:00"))
    digest = doc["corpus_digest"]
    if stamp.tzinfo is None or not isinstance(digest, str) or not digest.strip():
        raise ValueError("receipt sin fecha con zona o sin corpus_digest")
    return stamp.astimezone(timezone.utc), digest


def reapply(remote: str, candidate: str) -> str:
    """Replace all generated paths, including deletions and remote-only files."""
    with tempfile.TemporaryDirectory(prefix="refresh-promote-") as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        git("read-tree", remote, env=env)
        paths = git("ls-files", "-z", "--", *GENERATED, env=env)
        git("update-index", "--force-remove", "-z", "--stdin", data=paths, env=env)
        entries = git("ls-tree", "-r", "-z", candidate, "--", *GENERATED)
        git("update-index", "-z", "--index-info", data=entries, env=env)
        tree = git("write-tree", env=env).strip()
    message = git("log", "-1", "--format=%B", candidate)
    return git("commit-tree", tree, "-p", remote, data=message).strip()


def promote(build_base: str) -> int:
    candidate = git("rev-parse", "HEAD").strip()
    build_base = git("rev-parse", "--verify", f"{build_base}^{{commit}}").strip()
    if git("rev-parse", f"{candidate}^@").strip() != build_base:
        raise ValueError("el candidato debe ser un solo commit sobre BUILD_BASE")
    if git("diff", "--name-only") or git("diff", "--cached", "--name-only"):
        raise ValueError("hay cambios sin commit; se exige un candidato guardado")
    paths = git("diff", "--no-renames", "--name-only", "-z", build_base, candidate).split("\0")
    if any(path and not generated(path) for path in paths):
        print("Refresh descartado por cambios fuera de las rutas generadas.")
        return 0
    candidate_time, candidate_digest = receipt(candidate)
    for attempt in range(1, 6):
        print(f"Intento de promoción del newsroom {attempt}/5", flush=True)
        git("fetch", "--quiet", "origin", "main")
        remote = git("rev-parse", "refs/remotes/origin/main").strip()
        git("merge-base", "--is-ancestor", build_base, remote)
        if changed(build_base, remote, *CONSTRUCTOR):
            print("Refresh descartado por constructor: avanzó scaffold/, tools/ o el workflow.")
            return 0
        remote_time, remote_digest = receipt(remote)
        if remote_time > candidate_time:
            print("Refresh descartado por release remoto más nuevo; se conserva main.")
            return 0
        if remote_time == candidate_time:
            if remote_digest != candidate_digest:
                print("Refresh descartado: recibos con igual fecha y distinto corpus_digest; orden ambiguo.")
                return 0
            if changed(build_base, remote, *GENERATED):
                print("Refresh descartado: otro release del mismo corpus avanzó; no se prueba que el candidato sea más nuevo.")
                return 0
        corpus_advanced = changed(build_base, remote, "corpus")
        head = candidate if remote == build_base else reapply(remote, candidate)
        # Never force: the remote's current tip must be the parent we just checked.
        pushed = subprocess.run(["git", "push", "origin", f"{head}:refs/heads/main"],
                                text=True, capture_output=True)
        if pushed.returncode == 0:
            if corpus_advanced:
                print("Refresh publicado tras avance de corpus; el siguiente disparo incorporará el corpus nuevo.")
            else:
                print("Refresh publicado; candidato promovido sobre main.")
            return 0
        print("Main avanzó o rechazó el push; reintentando desde el main más nuevo.", file=sys.stderr)
        print(pushed.stderr, file=sys.stderr, end="")
    print("La promoción no convergió tras 5 reintentos; se rechaza force-push.", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-base", default="HEAD^")
    args = parser.parse_args()
    try:
        return promote(args.build_base)
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"Promoción bloqueada: no se pudo verificar la transacción ({exc}).", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
