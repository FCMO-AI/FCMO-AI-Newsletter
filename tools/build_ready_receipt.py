#!/usr/bin/env python3
"""Generate or verify the measured static-paper release receipt.

The receipt is derived from the A3 static-site generator's final route manifest
and the two source artifacts embedded in that candidate. ``--check`` preserves
the historical CLI contract: it measures without rewriting and fails on any
value or narrative drift.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
STORIES_PATH = SITE / "data" / "stories.v2.json"
STATUS_PATH = SITE / "data" / "newsroom-status.json"
CONFIG_PATH = REPO / "config" / "site.json"
RECEIPT_PATH = REPO / "READY_TO_PUBLISH.md"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_string(mapping: dict, key: str, source: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{source}.{key} must be a non-empty string")
    return value


def read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def measure_candidate(candidate: Path, stories_source: Path, status_source: Path) -> dict[str, str]:
    """Measure a completed A3 tree and prove its embedded inputs are exact."""
    routes_path = candidate / "data" / "routes.json"
    embedded_stories = candidate / "data" / "stories.v2.json"
    embedded_status = candidate / "data" / "newsroom-status.json"
    try:
        routes = json.loads(routes_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read candidate data/routes.json: {exc}") from exc
    if not isinstance(routes, list) or any(not isinstance(route, dict) for route in routes):
        raise ValueError("candidate data/routes.json must be an array of objects")
    if not routes:
        raise ValueError("candidate data/routes.json must not be empty")

    stories_bytes = stories_source.read_bytes()
    status_bytes = status_source.read_bytes()
    if embedded_stories.read_bytes() != stories_bytes:
        raise ValueError("candidate data/stories.v2.json is not a byte-for-byte source copy")
    if embedded_status.read_bytes() != status_bytes:
        raise ValueError("candidate data/newsroom-status.json is not a byte-for-byte source copy")

    stories = read_object(embedded_stories, "embedded stories")
    status = read_object(embedded_status, "embedded newsroom status")
    story_rows = stories.get("stories")
    if not isinstance(story_rows, list) or any(not isinstance(story, dict) for story in story_rows):
        raise ValueError("embedded stories.stories must be an array of objects")
    live_stories = [story for story in story_rows if story.get("status") == "live"]
    route_kinds = Counter(str(route.get("kind") or "unknown") for route in routes)
    route_locales = Counter(str(route.get("locale") or "unknown") for route in routes)
    public_files = sum(1 for path in candidate.rglob("*") if path.is_file())
    media_root = candidate / "assets" / "story-media"
    media_files = sum(1 for path in media_root.rglob("*") if path.is_file()) if media_root.is_dir() else 0

    return {
        "receipt_schema": "fcmo-paper-receipt-v1",
        "stories_schema": require_string(stories, "schema", "embedded stories"),
        "status_schema": require_string(status, "schema", "embedded newsroom status"),
        "release": require_string(stories, "release_id", "embedded stories"),
        "generated_at": require_string(stories, "generated_at", "embedded stories"),
        "edition_date": require_string(status, "edition_date", "embedded newsroom status"),
        "edition_state": require_string(status, "edition_state", "embedded newsroom status"),
        "route_manifest_sha256": sha256(routes_path.read_bytes()),
        "stories_sha256": sha256(stories_bytes),
        "status_sha256": sha256(status_bytes),
        "candidate_sha256": tree_digest(candidate),
        "route_count": str(len(routes)),
        "story_route_count": str(route_kinds.get("story", 0)),
        "live_story_count": str(len(live_stories)),
        "public_files": str(public_files),
        "media_files": str(media_files),
        "route_locales": ", ".join(f"{key}={route_locales[key]}" for key in sorted(route_locales)),
        "route_kinds": ", ".join(f"{key}={route_kinds[key]}" for key in sorted(route_kinds)),
    }


def measured_values() -> dict[str, str]:
    config = read_object(CONFIG_PATH, "site config")
    base = require_string(config, "base_path", "site config")
    with tempfile.TemporaryDirectory(prefix="fcmo-paper-receipt-") as temporary:
        candidate = Path(temporary) / "publish"
        subprocess.run(
            [
                sys.executable,
                "tools/paper/build.py",
                "--stories", str(STORIES_PATH),
                "--status", str(STATUS_PATH),
                "--out", str(candidate),
                "--base", base,
            ],
            cwd=REPO,
            check=True,
        )
        return measure_candidate(candidate, STORIES_PATH, STATUS_PATH)


def render_receipt(values: dict[str, str]) -> str:
    return f"""# FCMO AI Newsletter — static-paper release receipt

Release: **{values['release']}**

Status: **the deterministic A3 publication candidate is assembled and measurable.** Deployment still requires the A4 integrity gates, browser oracle, and post-deploy live verification.

## Release identity

- Receipt schema: `{values['receipt_schema']}`
- Story schema: `{values['stories_schema']}`
- Newsroom-status schema: `{values['status_schema']}`
- Story layer generated at: `{values['generated_at']}`
- Edition: `{values['edition_date']}` (`{values['edition_state']}`)

## Final route/data manifest

- `data/routes.json`: {values['route_count']} routes; SHA-256 `{values['route_manifest_sha256']}`
- Route locales: {values['route_locales']}
- Route kinds: {values['route_kinds']}
- Story routes: {values['story_route_count']} for {values['live_story_count']} live canonical stories
- Embedded `data/stories.v2.json`: byte-identical to the Story layer; SHA-256 `{values['stories_sha256']}`
- Embedded `data/newsroom-status.json`: byte-identical to newsroom status; SHA-256 `{values['status_sha256']}`
- Candidate tree: {values['public_files']} files, including {values['media_files']} local story-media files; SHA-256 `{values['candidate_sha256']}`

## Verification boundary

This receipt is generated from `tools/paper/build.py` and measures its final `data/routes.json` plus the embedded source artifacts. It does not describe or mount the retired `release-overlay` frontend. GitHub Pages separately generates OG cards, runs all A4 gates, runs the browser oracle, deploys the candidate, verifies the live site, and only then advances the durable `lkg` tag.
"""


def receipt_values(text: str) -> dict[str, str]:
    patterns = {
        "release": r"^Release: \*\*(?P<value>.+)\*\*$",
        "receipt_schema": r"^- Receipt schema: `(?P<value>[^`]+)`$",
        "stories_schema": r"^- Story schema: `(?P<value>[^`]+)`$",
        "status_schema": r"^- Newsroom-status schema: `(?P<value>[^`]+)`$",
        "generated_at": r"^- Story layer generated at: `(?P<value>[^`]+)`$",
        "edition_date": r"^- Edition: `(?P<value>[^`]+)` \(`[^`]+`\)$",
        "edition_state": r"^- Edition: `[^`]+` \(`(?P<value>[^`]+)`\)$",
        "route_count": r"^- `data/routes\.json`: (?P<value>\d+) routes; SHA-256 `[0-9a-f]+`$",
        "route_manifest_sha256": r"^- `data/routes\.json`: \d+ routes; SHA-256 `(?P<value>[0-9a-f]+)`$",
        "route_locales": r"^- Route locales: (?P<value>.+)$",
        "route_kinds": r"^- Route kinds: (?P<value>.+)$",
        "story_route_count": r"^- Story routes: (?P<value>\d+) for \d+ live canonical stories$",
        "live_story_count": r"^- Story routes: \d+ for (?P<value>\d+) live canonical stories$",
        "stories_sha256": r"^- Embedded `data/stories\.v2\.json`: byte-identical to the Story layer; SHA-256 `(?P<value>[0-9a-f]+)`$",
        "status_sha256": r"^- Embedded `data/newsroom-status\.json`: byte-identical to newsroom status; SHA-256 `(?P<value>[0-9a-f]+)`$",
        "public_files": r"^- Candidate tree: (?P<value>\d+) files, including \d+ local story-media files; SHA-256 `[0-9a-f]+`$",
        "media_files": r"^- Candidate tree: \d+ files, including (?P<value>\d+) local story-media files; SHA-256 `[0-9a-f]+`$",
        "candidate_sha256": r"^- Candidate tree: \d+ files, including \d+ local story-media files; SHA-256 `(?P<value>[0-9a-f]+)`$",
    }
    values: dict[str, str] = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"receipt has {len(matches)} readable value(s) for {field}, expected one")
        values[field] = matches[0]
    return values


def check_receipt(expected: dict[str, str]) -> None:
    try:
        actual_text = RECEIPT_PATH.read_text(encoding="utf-8")
        actual = receipt_values(actual_text)
    except Exception as exc:
        raise SystemExit(f"ready receipt check FAILED: {exc}") from exc
    differences = [
        f"{field}: receipt={actual.get(field)!r}, assembled={value!r}"
        for field, value in expected.items()
        if actual.get(field) != value
    ]
    if differences:
        raise SystemExit("ready receipt check FAILED:\n- " + "\n- ".join(differences))
    if actual_text != render_receipt(expected):
        raise SystemExit(
            "ready receipt check FAILED: receipt narrative/structure drift; regenerate with tools/build_ready_receipt.py"
        )
    print(
        "ready receipt check OK: "
        f"{expected['route_count']} routes; candidate {expected['candidate_sha256'][:12]}..."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare measured receipt values without rewriting it")
    args = parser.parse_args(argv)
    try:
        values = measured_values()
        if args.check:
            check_receipt(values)
        else:
            RECEIPT_PATH.write_text(render_receipt(values), encoding="utf-8", newline="\n")
            print(
                "ready receipt generated: "
                f"{values['route_count']} routes; candidate {values['candidate_sha256'][:12]}..."
            )
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ready receipt build FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
