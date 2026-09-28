#!/usr/bin/env python3
"""Fetch the exact live-verified Pages edition for an email dispatch.

The LKG tag moves only after Pages' public-origin verification. Requiring it to
match the live identity prevents a scheduled email from racing a deployment or
mailing an unverified candidate. The two inputs are copied from the origin only
after the candidate's critical routes have been checked against its identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools import verify_live_front_page
except ModuleNotFoundError:
    import verify_live_front_page  # type: ignore[no-redef]

STORIES_ROUTE = "data/stories.v2.json"
STATUS_ROUTE = "data/newsroom-status.json"


def collect(base_url: str, lkg_commit: str, fetch=None) -> tuple[dict, bytes, bytes]:
    get = fetch or verify_live_front_page.fetch
    if not re.fullmatch(r"[0-9a-f]{40}", lkg_commit):
        raise ValueError("invalid LKG commit")
    base = base_url.rstrip("/") + "/"
    identity = json.loads(get(base + "deployment-identity.json", "email-receipt").decode("utf-8"))
    if not isinstance(identity, dict) or identity.get("schema") != "fcmo-deployment-identity-v2":
        raise ValueError("live deployment identity is missing or invalid")
    if identity.get("source_commit") != lkg_commit:
        raise ValueError("live candidate is not the live-verified LKG")
    critical = identity.get("critical_files")
    if not isinstance(critical, dict) or not all(route in critical for route in (STORIES_ROUTE, STATUS_ROUTE)):
        raise ValueError("live identity does not bind the email inputs")
    # This independent oracle checks the whole critical route set, including
    # each locale's lead page, before any email input is accepted.
    seen, valid, detail = verify_live_front_page.verify_once(base_url, identity, "email-proof")
    if not (seen and valid):
        raise ValueError(f"live candidate verification failed: {detail}")
    stories = get(base + STORIES_ROUTE, "email-input")
    status = get(base + STATUS_ROUTE, "email-input")
    for route, raw in ((STORIES_ROUTE, stories), (STATUS_ROUTE, status)):
        if hashlib.sha256(raw).hexdigest() != critical[route]:
            raise ValueError(f"live {route} changed after verification")
    story_doc = json.loads(stories)
    status_doc = json.loads(status)
    if (not isinstance(story_doc, dict) or story_doc.get("schema") != "fcmo-stories-v2"
            or not isinstance(status_doc, dict) or status_doc.get("schema") != "fcmo-newsroom-status-v2"
            or story_doc.get("release_id") != identity.get("release_id")
            or status_doc.get("release_id") != identity.get("release_id")
            or status_doc.get("corpus_digest") != identity.get("corpus_digest")):
        raise ValueError("live email inputs disagree with the verified candidate")
    return identity, stories, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://fcmo-ai.github.io/FCMO-AI-Newsletter/")
    parser.add_argument("--lkg-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        identity, stories, status = collect(args.base_url, args.lkg_commit)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "stories.v2.json").write_bytes(stories)
        (args.out / "newsroom-status.json").write_bytes(status)
        (args.out / "live-verify.json").write_text(json.dumps({
            "status": "GREEN", "code": "OK", "candidate_id": identity["candidate_id"],
            "source_commit": identity["source_commit"],
        }, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"EMAIL LIVE RECEIPT FAILED: {exc}")
        return 1
    print(f"EMAIL LIVE RECEIPT OK candidate={identity['candidate_id'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
