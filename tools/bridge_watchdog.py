#!/usr/bin/env python3
"""Host-side bridge watchdog for when GitHub's own schedule stops firing.

Run hourly from a scheduler outside GitHub Actions. A dispatch response is only
an accepted request; the next run must still appear and finish successfully.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKFLOW = "newswire-bridge.yml"
API = "https://api.github.com"


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def decision(runs: list[dict], previous_request: str | None, now: datetime,
             *, max_gap_h: int = 6, retry_h: int = 2) -> str:
    if now.tzinfo is None:
        raise ValueError("watchdog clock must include a timezone")
    candidates = []
    for run in runs:
        if run.get("head_branch") != "main":
            continue
        try:
            candidates.append(utc(run["created_at"]))
        except (KeyError, TypeError, ValueError):
            continue
    if candidates and now - max(candidates) <= timedelta(hours=max_gap_h):
        return "RECENT_RUN"
    if previous_request:
        try:
            if now - utc(previous_request) < timedelta(hours=retry_h):
                return "AWAITING_DISPATCH"
        except ValueError:
            pass
    return "DISPATCH"


def request(method: str, url: str, token: str, body: dict | None = None):
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method=method, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "FCMO-Bridge-Watchdog/1.0",
    })
    with urllib.request.urlopen(req, timeout=20) as response:
        raw = response.read()
        if method == "POST" and response.status != 204:
            raise ValueError("dispatch was not accepted")
    return json.loads(raw) if raw else None


def run(repo: str, token: str, state_path: Path, now: datetime, *, api=request) -> str:
    if not token:
        raise ValueError("FCMO_WATCHDOG_TOKEN is not configured")
    if "/" not in repo or repo.count("/") != 1:
        raise ValueError("invalid repository name")
    base = f"{API}/repos/{repo}/actions/workflows/{WORKFLOW}"
    payload = api("GET", base + "/runs?branch=main&per_page=10", token)
    runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
    if not isinstance(runs, list):
        raise ValueError("workflow run response is invalid")
    previous = None
    if state_path.is_file():
        try:
            previous = json.loads(state_path.read_text(encoding="utf-8")).get("requested_at")
        except (OSError, ValueError, AttributeError):
            pass
    outcome = decision(runs, previous, now)
    if outcome != "DISPATCH":
        return outcome
    api("POST", base + "/dispatches", token, {"ref": "main"})
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"requested_at": now.astimezone(timezone.utc).isoformat(),
                                      "result": "accepted_not_confirmed"}) + "\n", encoding="utf-8")
    return "DISPATCH_REQUESTED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="FCMO-AI/FCMO-AI-Newsletter")
    parser.add_argument("--state", type=Path, required=True,
                        help="persistent host-local receipt path, outside the public checkout")
    parser.add_argument("--token-file", type=Path,
                        help="host-local file containing only the Actions-dispatch token")
    args = parser.parse_args(argv)
    try:
        token = (args.token_file.read_text(encoding="utf-8").strip() if args.token_file
                 else os.environ.get("FCMO_WATCHDOG_TOKEN", ""))
        outcome = run(args.repo, token, args.state,
                      datetime.now(timezone.utc))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        # Never print an HTTP response body: it could include private details.
        print(f"WATCHDOG FAILED {type(exc).__name__}", file=sys.stderr)
        return 1
    print(f"WATCHDOG {outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
