#!/usr/bin/env python3
"""Operator alerts as GitHub issues, opened and closed only on transitions.

Two alert sources, both stateless: the open issues in the repository are the
alert state, so a rerun or a lost event never duplicates or strands an issue.

``health``   reads a health-state.json (contracts/health-state.schema.json).
             One incident issue (key ``overall``) is open exactly while
             overall health is RED. GREEN->RED opens it, RED->RED with the
             same failing signals writes nothing, a change of failing signals
             while RED updates the issue body and adds one comment, and
             RED->GREEN comments and closes it. A missing or invalid health
             state counts as RED (``HEALTH_STATE_MISSING`` or
             ``HEALTH_STATE_INVALID``): being blind is not being green.

``workflow`` reads the recent completed runs of one workflow on a branch.
             After ``--threshold`` (2) consecutive failures it opens one issue
             (key ``workflow:<file stem>``); the next success closes it.
             Cancelled and skipped runs neither count nor reset the streak.

Usage:

    python3 tools/alert_transition.py health --health FILE --repo OWNER/NAME [--run-id N]
    python3 tools/alert_transition.py workflow --workflow-id ID --workflow-path .github/workflows/X.yml
            --repo OWNER/NAME [--workflow-name NAME] [--branch main] [--threshold 2]

Common options: ``--api-url`` (default ``$GITHUB_API_URL`` or
https://api.github.com), ``--dry-run`` (read only, print the decision). The
token comes from ``GITHUB_TOKEN`` or ``GH_TOKEN`` and is never printed.

First stdout line: ``<ACTION> key=<key> [issue=#N] [...]`` with ACTION one of
OPENED, UPDATED, UNCHANGED, CLOSED, NOOP (and ``WOULD_*`` with --dry-run).
Exit codes: 0 done, 1 GitHub API failure, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:  # executed as tools/alert_transition.py or imported as tools.alert_transition
    from status_report import HealthError, REQUIRED_SIGNALS, load_health
except ImportError:  # pragma: no cover - package import
    from tools.status_report import HealthError, REQUIRED_SIGNALS, load_health

LABEL = "operator-alert"
MARKER_RE = re.compile(r"<!-- fcmo-operator-alert key=(\S+) codes=(\S*) -->")
FAILED = {"failure", "timed_out", "startup_failure"}
IGNORED = {"cancelled", "skipped", "neutral", "action_required", "stale", None}
USER_AGENT = "fcmo-operator-alerts"


class ApiError(RuntimeError):
    pass


class GitHub:
    """Minimal GitHub REST client (stdlib only)."""

    def __init__(self, repo: str, api_url: str, token: str | None, author: str = "github-actions[bot]", timeout: float = 20.0) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("--repo must be OWNER/NAME")
        self.repo = repo
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.author = author
        self.timeout = timeout
        self.writes = 0

    def request(self, method: str, path: str, body: Any = None, query: dict[str, Any] | None = None) -> Any:
        url = f"{self.api_url}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", USER_AGENT)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        if method != "GET":
            self.writes += 1
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raise ApiError(f"GITHUB_HTTP_{exc.code} {method} {path}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ApiError(f"GITHUB_UNREACHABLE {method} {path}") from None
        return json.loads(raw) if raw else None

    # Issues ----------------------------------------------------------------------------
    def open_alert_issues(self) -> dict[str, dict[str, Any]]:
        """Open alert issues by key (oldest wins if duplicated).

        Only issues opened by the alerting identity count, so a public issue that
        copies the marker cannot silence or hijack an alert. The label is not used
        to find issues: GitHub drops labels silently for tokens without push access.
        """
        found: dict[str, dict[str, Any]] = {}
        for page in range(1, 6):
            batch = self.request(
                "GET",
                f"/repos/{self.repo}/issues",
                query={"state": "open", "creator": self.author, "per_page": 100, "page": page, "sort": "created", "direction": "asc"},
            )
            if not isinstance(batch, list):
                raise ApiError("GITHUB_BAD_PAYLOAD issues")
            for issue in batch:
                if "pull_request" in issue or (issue.get("user") or {}).get("login") != self.author:
                    continue
                match = MARKER_RE.search(issue.get("body") or "")
                if match and match.group(1) not in found:
                    found[match.group(1)] = issue
            if len(batch) < 100:
                break
        return found

    def create_issue(self, title: str, body: str) -> dict[str, Any]:
        return self.request("POST", f"/repos/{self.repo}/issues", {"title": title, "body": body, "labels": [LABEL]})

    def update_issue(self, number: int, **fields: Any) -> dict[str, Any]:
        return self.request("PATCH", f"/repos/{self.repo}/issues/{number}", fields)

    def comment(self, number: int, body: str) -> dict[str, Any]:
        return self.request("POST", f"/repos/{self.repo}/issues/{number}/comments", {"body": body})

    # Actions ---------------------------------------------------------------------------
    def workflow_runs(self, workflow_id: str, branch: str, per_page: int = 20) -> list[dict[str, Any]]:
        payload = self.request(
            "GET",
            f"/repos/{self.repo}/actions/workflows/{workflow_id}/runs",
            query={"branch": branch, "status": "completed", "per_page": per_page, "exclude_pull_requests": "true"},
        )
        runs = payload.get("workflow_runs") if isinstance(payload, dict) else None
        if not isinstance(runs, list):
            raise ApiError("GITHUB_BAD_PAYLOAD workflow_runs")
        return runs


# ---------------------------------------------------------------------------------------
# Decisions (pure)
# ---------------------------------------------------------------------------------------
def marker(key: str, codes: list[str]) -> str:
    return f"<!-- fcmo-operator-alert key={key} codes={','.join(codes)} -->"


def issue_codes(issue: dict[str, Any]) -> list[str]:
    match = MARKER_RE.search(issue.get("body") or "")
    return [c for c in match.group(2).split(",") if c] if match else []


def health_codes(doc: dict[str, Any] | None, error: str | None) -> list[str]:
    """Failing required signals as ``signal:CODE``; empty means GREEN."""
    if doc is None:
        return [f"health:{error or 'HEALTH_STATE_MISSING'}"]
    signals = doc["signals"]
    codes = [f"{name}:{signals[name]['code']}" for name in REQUIRED_SIGNALS if signals[name]["status"] != "GREEN"]
    if doc["overall"] != "GREEN" and not codes:  # impossible for a valid document; never read RED as GREEN
        codes = ["overall:RED"]
    return codes


def failure_streak(runs: list[dict[str, Any]]) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None]:
    """(consecutive failures from newest, newest counted run, newest failed run)."""
    counted = [r for r in runs if r.get("conclusion") not in IGNORED]
    counted.sort(key=lambda r: (r.get("run_started_at") or r.get("created_at") or "", r.get("id") or 0), reverse=True)
    streak = 0
    for run in counted:
        if run.get("conclusion") in FAILED:
            streak += 1
        else:
            break
    newest = counted[0] if counted else None
    newest_failed = counted[0] if counted and streak else None
    return streak, newest, newest_failed


# ---------------------------------------------------------------------------------------
# Rendering (public repository: codes and public links only)
# ---------------------------------------------------------------------------------------
def health_title(doc: dict[str, Any] | None, codes: list[str]) -> str:
    edition = doc["edition_state"] if doc else "UNKNOWN"
    return f"[alert] Newsroom health RED: {edition} ({', '.join(codes)})"[:240]


def health_body(doc: dict[str, Any] | None, codes: list[str], repo: str, run_id: str | None) -> str:
    lines = [marker("overall", codes), "", "Overall production health is **RED**.", ""]
    if doc is None:
        lines += [f"The health state could not be read (`{codes[0].split(':', 1)[1]}`). Nothing is known about production until a health run produces a valid health state.", ""]
    else:
        lines += [
            f"- Checked at: {doc['checked_at']} UTC",
            f"- Edition state: `{doc['edition_state']}`",
            f"- Serving release: `{doc.get('release_id')}`",
            "",
            "| Signal | Required | Status | Code | Since | Detail |",
            "|---|---|---|---|---|---|",
        ]
        for name, sig in doc["signals"].items():
            required = "yes" if name in REQUIRED_SIGNALS else "no"
            detail = str(sig.get("detail", "")).replace("|", "\\|")
            lines.append(f"| {name} | {required} | {sig.get('status')} | `{sig.get('code')}` | {sig.get('since') or '—'} | {detail} |")
        lines.append("")
    if run_id:
        lines.append(f"Health run: https://github.com/{repo}/actions/runs/{run_id}")
    lines += [
        "",
        "This issue was opened by the operator-alerts workflow on the GREEN→RED transition.",
        "It is updated when the failing signals change and closed automatically when health is GREEN again.",
    ]
    return "\n".join(lines)


def workflow_body(key: str, name: str, streak: int, run: dict[str, Any] | None, repo: str) -> str:
    lines = [
        marker(key, [f"FAILED_X{min(streak, 99)}"] if streak else []),
        "",
        f"The workflow **{name}** failed {streak} times in a row on the default branch.",
        "",
    ]
    if run:
        lines.append(f"Latest failed run: https://github.com/{repo}/actions/runs/{run.get('id')} ({run.get('event')}, {run.get('conclusion')}, {run.get('created_at')})")
    lines += [
        "",
        "This issue was opened by the operator-alerts workflow after consecutive failures.",
        "It closes automatically on the next successful run.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------------------
def run_health(gh: GitHub, health_path: Path, run_id: str | None, dry_run: bool) -> str:
    error: str | None = None
    try:
        doc: dict[str, Any] | None = load_health(health_path)
    except HealthError as exc:
        doc, error = None, str(exc)
    codes = health_codes(doc, error)
    run_id = run_id or (doc.get("run_id") if doc else None)
    issue = gh.open_alert_issues().get("overall")
    prefix = "WOULD_" if dry_run else ""

    if not codes:
        if not issue:
            return "NOOP key=overall state=GREEN"
        if not dry_run:
            gh.comment(issue["number"], f"Recovered: overall health is GREEN at {doc['checked_at']} UTC (edition `{doc['edition_state']}`). Closing.")
            gh.update_issue(issue["number"], state="closed", state_reason="completed")
        return f"{prefix}CLOSED key=overall issue=#{issue['number']} state=GREEN"

    title = health_title(doc, codes)
    body = health_body(doc, codes, gh.repo, run_id)
    joined = ",".join(codes)
    if not issue:
        if dry_run:
            return f"WOULD_OPENED key=overall codes={joined}"
        created = gh.create_issue(title, body)
        return f"OPENED key=overall issue=#{created.get('number')} codes={joined}"
    before = issue_codes(issue)
    if before == codes:
        return f"UNCHANGED key=overall issue=#{issue['number']} codes={joined}"
    if not dry_run:
        gh.update_issue(issue["number"], title=title, body=body)
        gh.comment(issue["number"], f"Failing signals changed: {', '.join(before) or 'none'} → {', '.join(codes)}.")
    return f"{prefix}UPDATED key=overall issue=#{issue['number']} codes={joined}"


def run_workflow(gh: GitHub, workflow_id: str, path: str, name: str | None, branch: str, threshold: int, dry_run: bool) -> str:
    stem = Path(path).stem if path else str(workflow_id)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", stem):
        raise ValueError("unsafe workflow path")
    key = f"workflow:{stem}"
    name = name or stem
    runs = gh.workflow_runs(workflow_id, branch)
    streak, newest, newest_failed = failure_streak(runs)
    issue = gh.open_alert_issues().get(key)
    prefix = "WOULD_" if dry_run else ""

    if streak >= threshold:
        if issue:
            return f"UNCHANGED key={key} issue=#{issue['number']} failures={streak}"
        if dry_run:
            return f"WOULD_OPENED key={key} failures={streak}"
        created = gh.create_issue(f"[alert] Workflow failing: {name} ({streak} consecutive failures)"[:240], workflow_body(key, name, streak, newest_failed, gh.repo))
        return f"OPENED key={key} issue=#{created.get('number')} failures={streak}"
    if issue and newest is not None and newest.get("conclusion") not in FAILED:
        if not dry_run:
            gh.comment(issue["number"], f"Recovered: run {newest.get('id')} succeeded at {newest.get('created_at')}. Closing.")
            gh.update_issue(issue["number"], state="closed", state_reason="completed")
        return f"{prefix}CLOSED key={key} issue=#{issue['number']} failures={streak}"
    if issue:
        # One failure after an unrecorded success: the old episode ended; a new one has not reached the threshold.
        if not dry_run:
            gh.comment(issue["number"], f"A later run succeeded before this failure; streak is now {streak}. Closing this episode.")
            gh.update_issue(issue["number"], state="closed", state_reason="completed")
        return f"{prefix}CLOSED key={key} issue=#{issue['number']} failures={streak}"
    return f"NOOP key={key} failures={streak}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    common.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL") or "https://api.github.com")
    common.add_argument("--dry-run", action="store_true")
    common.add_argument("--author", default="github-actions[bot]", help="Login that opens alert issues (default: the Actions bot).")
    health = sub.add_parser("health", parents=[common])
    health.add_argument("--health", required=True, type=Path)
    health.add_argument("--run-id")
    wf = sub.add_parser("workflow", parents=[common])
    wf.add_argument("--workflow-id", required=True)
    wf.add_argument("--workflow-path", default="")
    wf.add_argument("--workflow-name")
    wf.add_argument("--branch", default="main")
    wf.add_argument("--threshold", type=int, default=2)
    args = parser.parse_args(argv)

    if not args.repo:
        print("usage: --repo OWNER/NAME (or GITHUB_REPOSITORY) is required", file=sys.stderr)
        return 2
    if args.command == "health" and args.run_id and not re.fullmatch(r"[0-9]{1,20}", args.run_id):
        print("usage: --run-id must be numeric", file=sys.stderr)
        return 2
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        gh = GitHub(args.repo, args.api_url, token, author=args.author)
        if args.command == "health":
            line = run_health(gh, args.health, args.run_id, args.dry_run)
        else:
            if args.threshold < 1:
                raise ValueError("--threshold must be >= 1")
            line = run_workflow(gh, args.workflow_id, args.workflow_path, args.workflow_name, args.branch, args.threshold, args.dry_run)
    except ValueError as exc:
        print(f"usage: {exc}", file=sys.stderr)
        return 2
    except ApiError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
