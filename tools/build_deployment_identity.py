#!/usr/bin/env python3
"""Create the immutable identity receipt for one exact Pages candidate.

The receipt is uploaded as a workflow artifact, not served by the site itself.
Post-deploy verification uses it to prove that production is serving the exact
build manifest and critical bytes emitted by the build that Pages promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(site: Path, source_commit: str) -> dict:
    manifest_path = site / "build-manifest.json"
    status_path = site / "data" / "newsroom-status.json"
    stories_path = site / "data" / "stories.json"
    for path in (manifest_path, status_path, stories_path):
        if not path.is_file():
            raise ValueError(f"deployment identity missing required file: {path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))
    stories = json.loads(stories_path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("files"), dict) or not manifest.get("files"):
        raise ValueError("build manifest has no files map")
    if not isinstance(status, dict) or not status.get("release_id") or not status.get("corpus_digest"):
        raise ValueError("newsroom status lacks release/corpus identity")
    if not isinstance(stories, list) or not stories:
        raise ValueError("Story layer is empty")

    recorded = manifest["files"]
    for rel, path in (
        ("data/newsroom-status.json", status_path),
        ("data/stories.json", stories_path),
    ):
        digest = sha256(path)
        if recorded.get(rel) != digest:
            raise ValueError(f"build manifest does not bind exact {rel} bytes")

    return {
        "schema": "fcmo-deployment-identity-v1",
        "source_commit": source_commit,
        "release_id": status["release_id"],
        "corpus_digest": status["corpus_digest"],
        "story_count": len(stories),
        "build_manifest_sha256": sha256(manifest_path),
        "newsroom_status_sha256": sha256(status_path),
        "stories_sha256": sha256(stories_path),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site", type=Path, default=Path("publish"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", ""))
    args = p.parse_args(argv)
    try:
        receipt = build(args.site, args.source_commit)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"deployment identity FAILED: {exc}") from exc
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"deployment identity OK: release={receipt['release_id']} "
        f"stories={receipt['story_count']} manifest={receipt['build_manifest_sha256'][:12]}..."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
