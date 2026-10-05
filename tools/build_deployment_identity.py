#!/usr/bin/env python3
"""Bind one exact Pages candidate to an origin-verifiable identity receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.gates.common import canonical_story_path, live_stories
from tools.paper.front_order import front_order

SCHEMA = "fcmo-deployment-identity-v2"
IDENTITY_ROUTE = "deployment-identity.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(site: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(site.rglob("*")):
        if not path.is_file() or path.relative_to(site).as_posix() == IDENTITY_ROUTE:
            continue
        relative = path.relative_to(site).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big")); digest.update(relative)
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def critical_routes(site: Path, lead: dict | None) -> list[str]:
    routes = ["index.html", "es/index.html", "zh/index.html", "data/newsroom-status.json"]
    # L3 candidates expose public freshness separately from the legacy receipt.
    # Keep legacy LKGs rebuildable while proving these bytes on new deployments.
    if (site / "status.json").is_file():
        routes.append("status.json")
    story_data = "data/stories.v2.json" if (site / "data/stories.v2.json").is_file() else "data/stories.json"
    routes.append(story_data)
    if lead:
        for locale in ("en", "es-419", "zh-Hans"):
            route = canonical_story_path(lead, locale)
            if route: routes.append(route)
    return list(dict.fromkeys(routes))


def build(site: Path, source_commit: str) -> dict:
    if not source_commit:
        raise ValueError("source commit is empty")
    document, stories = live_stories(site)
    if not stories:
        raise ValueError("Story layer has no live stories")
    status_path = site / "data/newsroom-status.json"
    if not status_path.is_file():
        raise ValueError("deployment identity missing data/newsroom-status.json")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if not isinstance(status, dict):
        raise ValueError("newsroom status is not an object")
    release_id = status.get("release_id") or document.get("release_id")
    corpus_digest = status.get("corpus_digest")
    if not release_id or not corpus_digest:
        raise ValueError("newsroom status lacks release/corpus identity")
    # Name the lead the reader actually sees: the paper front uses this same order.
    lead = front_order(stories)[0]
    routes = critical_routes(site, lead)
    missing = [route for route in routes if not (site / route).is_file()]
    if missing:
        raise ValueError(f"deployment identity missing critical routes: {missing}")
    critical = {route: sha256(site / route) for route in routes}
    body = {
        "schema": SCHEMA,
        "source_commit": source_commit,
        "release_id": release_id,
        "corpus_digest": corpus_digest,
        "story_count": len(stories),
        "lead_id": lead.get("id"),
        "tree_sha256": tree_digest(site),
        "critical_files": critical,
    }
    body["candidate_id"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("publish"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args(argv)
    output = args.output or args.site / IDENTITY_ROUTE
    try: receipt = build(args.site, args.source_commit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"deployment identity FAILED: {exc}") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"deployment identity OK: candidate={receipt['candidate_id'][:12]} release={receipt['release_id']} stories={receipt['story_count']}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
