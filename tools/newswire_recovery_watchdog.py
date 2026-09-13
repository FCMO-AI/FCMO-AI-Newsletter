#!/usr/bin/env python3
"""Decide whether the autonomous daily Newsletter production cycle needs recovery."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

DEFAULT_STATUS_URL = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/newsroom-status.json"
LOCAL_ZONE = ZoneInfo("America/Mexico_City")
RECOVERY_AFTER = time(9, 0)
AIRLOCK_STATES = {"PUBLIC_DELTA_READY", "NO_PUBLIC_DELTA_READY"}
USER_AGENT = "FCMO-Newsroom-Recovery-Watchdog/1.0"


def parse_utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def recovery_decision(status: dict[str, Any] | None, now: datetime) -> tuple[bool, str]:
    local_now = now.astimezone(LOCAL_ZONE)
    # Footnote: ARB's research cycle is still landing during the early morning.
    # Recovery begins only after the normal 07:10–08:47 production window has had
    # room to succeed; before 09:00 a stale live site is not yet an incident.
    if local_now.timetz().replace(tzinfo=None) < RECOVERY_AFTER:
        return False, "BEFORE_RECOVERY_WINDOW"
    if not isinstance(status, dict):
        return True, "LIVE_STATUS_UNAVAILABLE"
    if status.get("state") not in AIRLOCK_STATES:
        return True, "NO_AIRLOCK_BACKED_RELEASE"
    generated = status.get("airlock_generated_at")
    if not isinstance(generated, str) or not generated:
        return True, "AIRLOCK_HEARTBEAT_MISSING"
    try:
        generated_local = parse_utc(generated).astimezone(LOCAL_ZONE)
    except (TypeError, ValueError):
        return True, "AIRLOCK_HEARTBEAT_INVALID"
    if generated_local.date() != local_now.date():
        return True, "DAILY_CYCLE_MISSING"
    return False, "CURRENT_DAILY_CYCLE_LIVE"


def fetch_status(url: str) -> dict[str, Any] | None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if getattr(response, "status", 200) != 200:
                return None
            value = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def write_github_output(path: Path, needed: bool, reason: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"recovery_needed={'true' if needed else 'false'}\n")
        handle.write(f"reason={reason}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-url", default=DEFAULT_STATUS_URL)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--now", help="test/debug override as ISO-8601 timestamp")
    args = parser.parse_args(argv)

    now = parse_utc(args.now) if args.now else datetime.now(timezone.utc)
    status = fetch_status(args.status_url)
    needed, reason = recovery_decision(status, now)
    if args.github_output:
        write_github_output(args.github_output, needed, reason)
    print(f"NEWSWIRE_RECOVERY_NEEDED={'true' if needed else 'false'} reason={reason}")
    # Footnote: needing recovery is an operational decision, not a validator error.
    # Exit zero so the workflow can proceed to the narrowly scoped dispatch step.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
