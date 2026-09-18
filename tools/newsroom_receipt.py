#!/usr/bin/env python3
"""Validate the upstream Airlock heartbeat and write the downstream newsroom ACK.

A fresh heartbeat with an unchanged content-addressed release is a healthy quiet
cycle. Missing/stale input is an operational failure. Native-language backlog is
reported explicitly but does not make a fully validated English Story layer false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

AIRLOCK_SCHEMA = "fcmo-newswire-airlock-v2"
STATUS_SCHEMA = "fcmo-newsroom-status-v2"


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def require_airlock(corpus: Path, max_age_hours: int) -> dict[str, Any]:
    if not (corpus / "index.html").is_file() or not (corpus / "developments").is_dir():
        raise ValueError("sanitized corpus is absent or incomplete")
    receipt_path = corpus / "airlock.json"
    if not receipt_path.is_file():
        raise ValueError("airlock heartbeat receipt is absent")
    receipt = load(receipt_path)
    if receipt.get("schema") != AIRLOCK_SCHEMA or receipt.get("state") != "READY_FOR_PUBLICATION":
        raise ValueError("airlock receipt schema/state mismatch")
    if not receipt.get("release_id") or not receipt.get("corpus_digest"):
        raise ValueError("airlock receipt lacks content identity")
    generated = utc(str(receipt.get("generated_at") or ""))
    age = datetime.now(timezone.utc) - generated
    if age > timedelta(hours=max_age_hours):
        raise ValueError(f"airlock heartbeat is stale: {age.total_seconds()/3600:.1f}h > {max_age_hours}h")
    if age < timedelta(minutes=-15):
        raise ValueError("airlock heartbeat is implausibly in the future")
    return receipt


def count_json_files(path: Path, pattern: str) -> int:
    return sum(1 for _ in path.glob(pattern)) if path.is_dir() else 0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(args: argparse.Namespace) -> int:
    receipt = require_airlock(args.corpus, args.max_age_hours)
    previous = load(args.status) if args.status.is_file() else {}
    same = previous.get("release_id") == receipt["release_id"] and previous.get("corpus_digest") == receipt["corpus_digest"]
    state = "NO_PUBLIC_DELTA" if same else "PUBLIC_DELTA_PENDING"
    print(json.dumps({
        "state": state,
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "airlock_generated_at": receipt["generated_at"],
        "record_count": receipt.get("record_count"),
    }, sort_keys=True))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"state={state}\n")
            handle.write(f"release_id={receipt['release_id']}\n")
            handle.write(f"corpus_digest={receipt['corpus_digest']}\n")
    return 0


def finalize(args: argparse.Namespace) -> int:
    receipt = require_airlock(args.corpus, args.max_age_hours)
    previous = load(args.status) if args.status.is_file() else {}
    same = previous.get("release_id") == receipt["release_id"] and previous.get("corpus_digest") == receipt["corpus_digest"]

    stories_path = args.site / "data" / "stories.json"
    stories = json.loads(stories_path.read_text(encoding="utf-8")) if stories_path.is_file() else []
    if not isinstance(stories, list):
        raise ValueError("site/data/stories.json must be an array")
    media_path = args.release_src / "data" / "media.json"
    media = json.loads(media_path.read_text(encoding="utf-8")) if media_path.is_file() else []
    if not isinstance(media, list):
        raise ValueError("release-src/data/media.json must be an array")

    locale_ids: dict[str, set[str]] = {}
    for locale in ("es-419", "zh-Hans"):
        ids: set[str] = set()
        for path in sorted((args.site / "data" / "i18n" / locale).glob("part-*.json")):
            rows = load(path).get("records") or {}
            if not isinstance(rows, dict):
                raise ValueError(f"{locale}: malformed i18n part {path.name}")
            ids.update(rows)
        locale_ids[locale] = ids

    canonical_count = count_json_files(args.release_src / "data" / "briefs", "FCMO-*.json")
    canonical_ids = {str(s.get("research_id") or "") for s in stories}
    if len(stories) != canonical_count:
        raise ValueError(f"story layer count mismatch: canonical={canonical_count} stories={len(stories)}")
    if len(media) != canonical_count:
        raise ValueError(f"media count mismatch: canonical={canonical_count} media={len(media)}")
    for locale, ids in locale_ids.items():
        extra = ids - canonical_ids
        if extra:
            raise ValueError(f"{locale}: locale IDs outside canonical Story layer: {sorted(extra)}")
    if locale_ids["es-419"] != locale_ids["zh-Hans"]:
        raise ValueError("ES/ZH native locale ID sets differ")

    pending = canonical_ids - locale_ids["es-419"]
    translation_state = "COMPLETE" if not pending else "DEGRADED_TRANSLATION_BACKLOG"
    state = "NO_PUBLIC_DELTA_READY" if same else "PUBLIC_DELTA_READY"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status = {
        "schema": STATUS_SCHEMA,
        "state": state,
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "airlock_generated_at": receipt["generated_at"],
        "airlock_record_count": receipt.get("record_count"),
        "canonical_story_count": canonical_count,
        "story_layer_count": len(stories),
        "stories_sha256": sha256_file(stories_path),
        "media_count": len(media),
        "media_sha256": sha256_file(media_path),
        "translation_counts": {locale: len(ids) for locale, ids in locale_ids.items()},
        "translation_state": translation_state,
        "pending_translation_count": len(pending),
        "pending_translation_ids": sorted(pending),
        "finalized_at": now,
        "ack": "INGESTED_VALIDATED_AND_READY_FOR_DEPLOY",
        "previous_release_id": previous.get("release_id"),
        "deployment_proof": "post-deploy live oracle required",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"newsroom ACK {state}: {receipt['release_id']} stories={canonical_count} "
        f"translations={translation_state} pending={len(pending)}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "finalize"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--release-src", type=Path, default=Path("release-src"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--status", type=Path, default=Path("site/data/newsroom-status.json"))
    parser.add_argument("--max-age-hours", type=int, default=36)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    try:
        return preflight(args) if args.mode == "preflight" else finalize(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"newsroom receipt FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
