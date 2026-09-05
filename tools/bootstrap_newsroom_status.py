#!/usr/bin/env python3
"""Write an explicit bootstrap status for the existing public corpus.

This is used once while the private ARB Actions runner is unavailable. It makes
no claim that a fresh airlock delivery occurred: the status is content-addressed
from the already-public Newsletter source and is replaced by newsroom_receipt.py
as soon as the real ARB → Newsletter newswire is healthy.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RELEASE = Path("release-src")
SITE = Path("site")


def digest_tree(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii") + b"\n")
    return h.hexdigest()


def main() -> int:
    stories_path = SITE / "data" / "stories.json"
    stories = json.loads(stories_path.read_text(encoding="utf-8"))
    if not isinstance(stories, list) or not stories:
        raise SystemExit("bootstrap status refused: Story layer is absent")
    digest = digest_tree(RELEASE)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status = {
        "schema": "fcmo-newsroom-status-v1",
        "state": "BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE",
        "release_id": f"bootstrap-{digest[:24]}",
        "corpus_digest": digest,
        "canonical_story_count": len(stories),
        "story_layer_count": len(stories),
        "finalized_at": now,
        "ack": "EXISTING_PUBLIC_CORPUS_REBUILT_AS_AUTONOMOUS_NEWSROOM",
        "airlock_generated_at": None,
        "airlock_record_count": None,
        "deployment_proof": "post-deploy live oracle required",
        "bootstrap_note": "No fresh private-source transfer is asserted. This status is superseded by the first valid fcmo-newswire-airlock-v2 receipt."
    }
    path = SITE / "data" / "newsroom-status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"bootstrap newsroom status {status['release_id']} stories={len(stories)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
