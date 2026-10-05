#!/usr/bin/env python3
"""Wait for and verify the exact deployed candidate at the public origin."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "FCMO-Live-Identity-Oracle/2.0"


def validate_identity(identity: dict) -> None:
    """Reject incomplete receipts before accepting their critical-byte proof."""
    if not isinstance(identity, dict) or identity.get("schema") != "fcmo-deployment-identity-v2":
        raise ValueError("unexpected identity schema")
    critical = identity.get("critical_files")
    required = {"index.html", "es/index.html", "zh/index.html", "data/newsroom-status.json"}
    if not isinstance(critical, dict) or not required <= critical.keys():
        raise ValueError("identity lacks critical publication routes")
    if not ({"data/stories.v2.json", "data/stories.json"} & critical.keys()):
        raise ValueError("identity lacks critical Story data")
    for route, digest in critical.items():
        if (not isinstance(route, str) or route.startswith("/") or
                any(part in {"", ".", ".."} for part in route.split("/")) or
                any(char in route for char in "\\?#:") or
                not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("invalid critical route or digest")
    body = {k: v for k, v in identity.items() if k != "candidate_id"}
    candidate_id = hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(",", ":"),
                                            sort_keys=True).encode("utf-8")).hexdigest()
    if candidate_id != identity.get("candidate_id"):
        raise ValueError("deployment receipt candidate hash differs")


def fetch(url: str, nonce: str, timeout: float = 25.0) -> bytes:
    separator = "&" if "?" in url else "?"
    request = urllib.request.Request(
        url + separator + urllib.parse.urlencode({"fcmo_verify": nonce}),
        headers={"User-Agent": UA, "Cache-Control": "no-cache, no-store", "Pragma": "no-cache"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise OSError(f"HTTP {response.status} for {url}")
        return response.read()


def verify_once(base_url: str, expected: dict, nonce: str, *, get=None) -> tuple[bool, bool, str]:
    get = get or fetch
    base = base_url.rstrip("/") + "/"
    try:
        actual = json.loads(get(base + "deployment-identity.json", nonce).decode("utf-8"))
    except Exception as exc:
        return False, False, f"identity unavailable: {exc}"
    if actual.get("candidate_id") != expected.get("candidate_id"):
        return False, False, f"origin candidate={actual.get('candidate_id', '<missing>')}"
    failures = []
    for route, wanted in expected.get("critical_files", {}).items():
        try: got = hashlib.sha256(get(base + route, nonce)).hexdigest()
        except Exception as exc:
            failures.append(f"{route}: {exc}"); continue
        if got != wanted: failures.append(f"{route}: sha256 {got} != {wanted}")
    if failures: return True, False, "; ".join(failures)
    return True, True, "exact identity and critical bytes match"


def wait_for_candidate(base_url: str, expected: dict, timeout_seconds: float, poll_seconds: float, *, get=None) -> None:
    deadline = time.monotonic() + timeout_seconds
    saw_candidate = False; last = "no attempt"
    while True:
        nonce = str(time.time_ns())
        seen, valid, last = verify_once(base_url, expected, nonce, get=get)
        saw_candidate = saw_candidate or seen
        if valid: return
        if time.monotonic() >= deadline: break
        time.sleep(min(poll_seconds, max(0.0, deadline - time.monotonic())))
    state = "candidate served but invalid" if saw_candidate else "candidate never reached the origin"
    raise ValueError(f"{state} within {timeout_seconds:g}s: {last}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-identity", type=Path, required=True)
    parser.add_argument("--base-url", default="https://fcmo-ai.github.io/FCMO-AI-Newsletter/")
    parser.add_argument("--timeout-seconds", type=float, default=900)
    parser.add_argument("--poll-seconds", type=float, default=15)
    args = parser.parse_args(argv)
    try:
        expected = json.loads(args.expected_identity.read_text(encoding="utf-8"))
        validate_identity(expected)
        wait_for_candidate(args.base_url, expected, args.timeout_seconds, args.poll_seconds)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"LIVE VERIFY FAILED: {exc}") from exc
    print(f"LIVE VERIFY PASS: candidate={expected['candidate_id']} release={expected['release_id']} lead={expected['lead_id']}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
