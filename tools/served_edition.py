#!/usr/bin/env python3
"""Measure editorial freshness on the edition the public origin actually serves.

The production health workflow used to measure ``site/data/stories.v2.json``
from the repository checkout.  That is the edition *waiting* to be published,
not the one readers see: when every Pages deploy was cancelled for days, the
health run still reported a fresh newspaper.  This tool closes that gap.

1. Read ``deployment-identity.json`` from the public origin (or a file).  Its
   ``source_commit`` is the commit whose Story layer the live site was built
   from (``tools/build_deployment_identity.py``; ``promote-lkg`` relies on it).
2. Export that commit's ``site/data/stories.v2.json`` and run the unchanged
   editorial check (``tools/editorial_freshness.py check --stories``) on it.
   The 36 h newest-event limit now applies to what readers see.
3. Measure the deploy lag: how long ``--ref`` (main) has carried Story-layer
   commits that the served edition does not contain.  A lag above
   ``--max-lag-hours`` (default: the editorial limit) fails the check even when
   an old edition happens to contain a recent event date.

Fail closed: an unreadable identity, a malformed or unknown ``source_commit``,
or a served commit that is not on ``--ref`` yields ``UNKNOWN`` (exit 1), never
the repository's own, fresher, Story layer.

The signal keeps the editorial contract shape (``contracts/health-state.schema.json``):
codes stay ``OK``/``EVENT_STALE``/``STORY_SUPPLY``/``UNKNOWN``; the served commit
and lag are added as metrics.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from tools import editorial_freshness, wire_status
    from tools.build_deployment_identity import SCHEMA as IDENTITY_SCHEMA
except ImportError:  # executed as tools/served_edition.py
    import editorial_freshness  # type: ignore[no-redef]
    import wire_status  # type: ignore[no-redef]
    from build_deployment_identity import SCHEMA as IDENTITY_SCHEMA  # type: ignore[no-redef]

STORIES_PATH = "site/data/stories.v2.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USER_AGENT = "FCMO-Newsroom-Served-Edition/1.0"


class Unresolved(Exception):
    """The served edition cannot be identified; never fall back to the repo."""


def fetch(url: str, attempts: int = 4, pause_s: float = 5.0) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            sep = "&" if "?" in url else "?"
            request = urllib.request.Request(
                f"{url}{sep}served-edition={time.time_ns()}",
                headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(pause_s)
    raise Unresolved(f"deployment identity could not be fetched ({type(last).__name__})")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, text=True, capture_output=True)


def served_commit(identity: Any) -> str:
    if not isinstance(identity, dict) or identity.get("schema") != IDENTITY_SCHEMA:
        raise Unresolved("deployment identity has an unexpected schema")
    sha = identity.get("source_commit")
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        raise Unresolved("deployment identity has no valid source_commit")
    return sha


def load_identity(args: argparse.Namespace) -> Any:
    try:
        raw = args.identity_file.read_bytes() if args.identity_file else fetch(args.identity_url)
        return json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise Unresolved(f"deployment identity is unreadable ({type(exc).__name__})") from exc


def commit_time(repo: Path, sha: str) -> datetime:
    return datetime.fromtimestamp(int(git(repo, "show", "-s", "--format=%ct", sha).stdout.strip()), tz=timezone.utc)


def deploy_lag(repo: Path, sha: str, ref: str, now: datetime) -> dict[str, Any]:
    """Hours since ``ref`` first carried a Story-layer change the served commit lacks."""
    if git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode != 0:
        raise Unresolved("the served commit is not in this repository's history")
    if git(repo, "merge-base", "--is-ancestor", sha, ref, check=False).returncode != 0:
        raise Unresolved(f"the served commit is not on {ref}")
    log = git(repo, "log", "--reverse", "--format=%H %ct", f"{sha}..{ref}", "--", STORIES_PATH).stdout.split()
    pending = len(log) // 2
    served_at = commit_time(repo, sha)
    if not pending:
        return {"served_commit": sha, "served_commit_at": iso(served_at), "undeployed_since": None,
                "pending_story_commits": 0, "deploy_lag_h": 0.0}
    since = datetime.fromtimestamp(int(log[1]), tz=timezone.utc)
    lag = round(max(0.0, (now - since).total_seconds() / 3600.0), 1)
    return {"served_commit": sha, "served_commit_at": iso(served_at), "undeployed_since": iso(since),
            "pending_story_commits": pending, "deploy_lag_h": lag}


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_stories(repo: Path, sha: str, out: Path) -> None:
    shown = git(repo, "show", f"{sha}:{STORIES_PATH}", check=False)
    if shown.returncode != 0:
        raise Unresolved("the served commit has no v2 Story layer")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shown.stdout, encoding="utf-8")


def unknown_signal(detail: str) -> dict[str, Any]:
    return {"status": "UNKNOWN", "code": "UNKNOWN", "required": True, "since": None, "detail": detail[:300]}


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    now = wire_status.resolve_now(args.now)
    repo = args.repo
    thresholds = wire_status.load_thresholds()
    limit = float(args.max_event_age_hours or thresholds["editorial"]["newest_event_max_age_h"])
    max_lag = float(args.max_lag_hours if args.max_lag_hours is not None else limit)
    try:
        sha = served_commit(load_identity(args))
        lag = deploy_lag(repo, sha, args.ref, now)
        stories = args.work_dir / "served-stories.v2.json"
        export_stories(repo, sha, stories)
    except Unresolved as exc:
        return 1, unknown_signal(f"The edition served by the public origin could not be resolved: {exc}.")

    editorial_out = args.work_dir / "served-editorial.json"
    rc = editorial_freshness.main([
        "check", "--wire-status", str(args.wire_status), "--records", str(args.records),
        "--stories", str(stories), "--now", iso(now), "--max-event-age-hours", f"{limit:g}",
        "--signal-out", str(editorial_out),
    ])
    sig = json.loads(editorial_out.read_text(encoding="utf-8"))
    sig.setdefault("required", True)
    sig.setdefault("since", None)
    sig.setdefault("metrics", {}).update(lag)
    sig["metrics"]["deploy_lag_limit_h"] = max_lag
    if lag["deploy_lag_h"] > max_lag:
        rc = 1
        if sig.get("status") == "GREEN":
            # The schema ties GREEN to OK; an edition this far behind main is
            # not fresh for readers whatever its newest event date says.
            sig["status"], sig["code"] = "RED", "EVENT_STALE"
        sig["detail"] = (f"The public site serves an edition {lag['deploy_lag_h']}h behind main "
                         f"(limit {max_lag:g}h). " + str(sig.get("detail", "")))[:300]
    return rc, sig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--identity-url", help="public deployment-identity.json URL")
    source.add_argument("--identity-file", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--ref", default="HEAD", help="the branch whose head should be live (main)")
    parser.add_argument("--wire-status", type=Path, default=Path("corpus/wire-status.json"))
    parser.add_argument("--records", type=Path, default=Path("corpus/data/developments.jsonl"))
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--max-event-age-hours", type=float)
    parser.add_argument("--max-lag-hours", type=float)
    parser.add_argument("--now", help="ISO 8601 time (else FCMO_NOW, else the real clock)")
    parser.add_argument("--signal-out", type=Path)
    args = parser.parse_args(argv)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    rc, sig = run(args)
    if args.signal_out:
        args.signal_out.parent.mkdir(parents=True, exist_ok=True)
        args.signal_out.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
    metrics = sig.get("metrics", {})
    print(f"SERVED {sig['code']} status={sig['status']} served_commit={metrics.get('served_commit', '-')} "
          f"deploy_lag_h={metrics.get('deploy_lag_h', '-')}")
    print(sig["detail"])
    return rc


if __name__ == "__main__":
    sys.exit(main())
