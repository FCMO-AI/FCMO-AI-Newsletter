"""Exercise the workflow's real commit/promotion step against an offline bare remote."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ("release-src", "release-overlay", "site", "READY_TO_PUBLISH.md")
STATUS = "site/data/newsroom-status.json"


def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def stamp(root, hour, digest):
    write(root, STATUS, json.dumps({"airlock_generated_at": f"2026-11-06T{hour:02}:00:00Z",
                                   "corpus_digest": digest}))


def make_transaction(tmp_path):
    # No host credentials/configuration or network: all pushes target this bare directory.
    remote, build, wire = [tmp_path / name for name in ("public.git", "builder", "wire")]
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    git(tmp_path, "clone", str(remote), str(build))
    if (ROOT / "tools/refresh_promote.py").exists():
        (build / "tools").mkdir()
        shutil.copy(ROOT / "tools/refresh_promote.py", build / "tools/refresh_promote.py")
    for name in (*GENERATED[:3], "corpus", "tools", "scaffold"):
        write(build, f"{name}/index.txt", "base\n")
    write(build, "READY_TO_PUBLISH.md", "base\n")
    write(build, ".github/workflows/daily-refresh.yml", "base\n")
    write(build, "site/obsolete.txt", "base\n")
    stamp(build, 1, "base")
    git(build, "add", "-A")
    git(build, "commit", "-m", "base")
    git(build, "push", "origin", "HEAD:main")
    git(tmp_path, "clone", str(remote), str(wire))
    for name in GENERATED[:3]:
        write(build, f"{name}/index.txt", "candidate\n")
    write(build, "READY_TO_PUBLISH.md", "candidate\n")
    (build / "site/obsolete.txt").unlink()
    stamp(build, 2, "candidate")
    return remote, build, wire


def advance(wire, changes):
    for name, content in changes.items():
        write(wire, name, content)
    git(wire, "add", "-A")
    git(wire, "commit", "-m", "concurrent remote change")
    git(wire, "push", "origin", "HEAD:main")
    return git(wire, "rev-parse", "HEAD")


def promote(build, **env):
    doc = yaml.safe_load((ROOT / ".github/workflows/daily-refresh.yml").read_text())
    step = next(s for s in doc["jobs"]["refresh"]["steps"]
                if s.get("name") == "Commit only what the autonomous newsroom produced")
    # Execute the real workflow step and its helper, copied into the base fixture.
    return subprocess.run(["bash", "-euo", "pipefail", "-c", step["run"]], cwd=build,
                          env={**os.environ, "REFRESH_PATH": "rebuild", **env},
                          text=True, capture_output=True, timeout=30)


def assert_candidate(remote, build):
    for name in (*[f"{p}/index.txt" for p in GENERATED[:3]], "READY_TO_PUBLISH.md"):
        assert git(remote, "show", f"main:{name}") == "candidate"
    assert json.loads(git(remote, "show", f"main:{STATUS}"))["corpus_digest"] == "candidate"
    assert "site/obsolete.txt" not in git(remote, "ls-tree", "-r", "--name-only", "main")
    # Blob hashes, modes and every generated path must equal the guarded snapshot.
    assert git(remote, "ls-tree", "-r", "main", "--", *GENERATED) == git(
        build, "ls-tree", "-r", "HEAD", "--", *GENERATED)
    assert git(build, "status", "--porcelain") == ""


def race_on_first_push(build, wire):
    """Move real remote main after advertisement, forcing a non-fast-forward retry."""
    hook = build / ".git/hooks/pre-push"
    marker = build / ".git/raced"
    hook.write_text(f'''#!{sys.executable}
import os
from pathlib import Path
import subprocess
marker = Path({str(marker)!r})
if not marker.exists():
    marker.write_text("once")
    env = {{k: v for k, v in os.environ.items()
           if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")}}
    subprocess.run(["git", "-C", {str(wire)!r}, "push", "origin", "HEAD:main"],
                   env=env, check=True)
''', encoding="utf-8")
    hook.chmod(0o755)


class RefreshPromoteTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.env = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        tmp = tempfile.TemporaryDirectory(prefix="refresh-promote-")
        self.addCleanup(tmp.cleanup)
        self.transaction = make_transaction(Path(tmp.name))

    def test_corpus_advance_publishes_without_losing_new_wire(self):
        remote, build, wire = self.transaction
        advance(wire, {"corpus/index.txt": "new wire\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert_candidate(remote, build)
        assert git(remote, "show", "main:corpus/index.txt") == "new wire"
        assert "publicado tras avance de corpus" in result.stdout.lower()


    def test_constructor_advance_discards(self):
        for path in ("tools/index.txt", "scaffold/index.txt", ".github/workflows/daily-refresh.yml"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                remote, build, wire = make_transaction(Path(tmp))
                head = advance(wire, {path: "new builder\n"})
                result = promote(build)
                assert result.returncode == 0, result.stdout + result.stderr
                assert git(remote, "rev-parse", "main") == head
                assert "descartado por constructor" in result.stdout.lower()


    def test_newer_remote_release_is_never_overwritten(self):
        remote, build, wire = self.transaction
        stamp(wire, 3, "newer-remote")
        head = advance(wire, {"site/index.txt": "newer release\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "descartado por release remoto más nuevo" in result.stdout.lower()


    def test_generated_conflict_publishes_complete_newer_candidate(self):
        remote, build, wire = self.transaction
        # Same lines change on both sides; rebase used to abort here. Full replacement
        # must also remove remote-only generated files and retain orthogonal changes.
        advance(wire, {"site/index.txt": "remote older release\n",
                       "site/remote-only.txt": "must disappear\n", "notes.txt": "keep\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert_candidate(remote, build)
        assert "site/remote-only.txt" not in git(remote, "ls-tree", "-r", "--name-only", "main")
        assert git(remote, "show", "main:notes.txt") == "keep"


    def test_no_advance_pushes_normally(self):
        remote, build, _wire = self.transaction
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert_candidate(remote, build)
        assert git(remote, "rev-parse", "main") == git(build, "rev-parse", "HEAD")

    def test_retry_rechecks_corpus_constructor_and_remote_release(self):
        for kind in ("corpus", "constructor", "release"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                remote, build, wire = make_transaction(Path(tmp))
                if kind == "corpus":
                    write(wire, "corpus/index.txt", "racing wire\n")
                elif kind == "constructor":
                    write(wire, "tools/index.txt", "racing builder\n")
                else:
                    stamp(wire, 3, "racing newer release")
                git(wire, "add", "-A")
                git(wire, "commit", "-m", "race during promotion")
                expected = git(wire, "rev-parse", "HEAD")
                race_on_first_push(build, wire)
                result = promote(build)
                assert result.returncode == 0, result.stdout + result.stderr
                assert "reintentando desde el main más nuevo" in result.stderr
                assert "2/5" in result.stdout
                if kind == "corpus":
                    assert_candidate(remote, build)
                    assert git(remote, "show", "main:corpus/index.txt") == "racing wire"
                else:
                    assert git(remote, "rev-parse", "main") == expected

    def test_receipt_with_same_timestamp_and_different_digest_discards(self):
        remote, build, wire = self.transaction
        stamp(wire, 2, "other corpus")
        head = advance(wire, {"site/index.txt": "ambiguous release\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "orden ambiguo" in result.stdout

    def test_same_corpus_remote_time_is_still_monotonic(self):
        remote, build, wire = self.transaction
        stamp(wire, 3, "candidate")
        head = advance(wire, {"site/index.txt": "newer same corpus\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "descartado por release remoto más nuevo" in result.stdout.lower()

    def test_equal_receipt_does_not_clobber_a_concurrent_release(self):
        remote, build, wire = self.transaction
        stamp(wire, 2, "candidate")
        head = advance(wire, {"site/index.txt": "same corpus concurrent release\n"})
        result = promote(build)
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "otro release del mismo corpus" in result.stdout

    def test_missing_receipt_blocks_instead_of_guessing(self):
        remote, build, wire = self.transaction
        head = advance(wire, {STATUS: "{}"})
        result = promote(build)
        assert result.returncode == 1, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "Promoción bloqueada" in result.stderr

    def test_outside_path_conflict_discards(self):
        remote, build, wire = self.transaction
        write(build, "notes.txt", "candidate outside scope\n")
        git(build, "add", "notes.txt")
        head = advance(wire, {"notes.txt": "remote outside scope\n"})
        result = promote(build)
        assert result.returncode == 1, result.stdout + result.stderr
        assert git(remote, "rev-parse", "main") == head
        assert "fuera de su alcance" in result.stderr

    def test_equivalent_timezone_and_same_corpus_status_update(self):
        remote, build, wire = self.transaction
        # Status-only candidates keep the airlock stamp; it is not the heartbeat.
        git(build, "restore", "--source=HEAD", "--worktree", "--", *GENERATED)
        write(build, STATUS, json.dumps({"airlock_generated_at": "2026-11-05T19:00:00-06:00",
                                        "corpus_digest": "base"}))
        advance(wire, {"corpus/wire-status.json": "fresh heartbeat\n"})
        result = promote(build, REFRESH_PATH="status")
        assert result.returncode == 0, result.stdout + result.stderr
        assert git(remote, "show", "main:site/index.txt") == "base"
        assert git(remote, "show", "main:corpus/wire-status.json") == "fresh heartbeat"
        assert git(remote, "log", "-1", "--format=%s", "main") == "status: record the newsroom edition state"

    def test_push_rejection_stops_after_five_attempts_without_moving_main(self):
        remote, build, _wire = self.transaction
        head = git(remote, "rev-parse", "main")
        hook = remote / "hooks/pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        result = promote(build)
        assert result.returncode == 1, result.stdout + result.stderr
        assert result.stdout.count("Intento de promoción del newsroom") == 5
        assert "no convergió tras 5 reintentos" in result.stderr
        assert git(remote, "rev-parse", "main") == head



if __name__ == "__main__":
    unittest.main()
