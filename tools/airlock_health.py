#!/usr/bin/env python3
"""Validate the sanitized ARB handoff and expose a public-safe newsroom health receipt.

A missing corpus is no longer treated as a successful no-op. Healthy quiet days carry a
fresh `_transport-receipt.json`; missing/stale delivery is operational starvation and
must be distinguishable from `NO_PUBLIC_DELTA`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)


def recompute_release_digest(corpus: Path) -> str:
    """Recreate the upstream digest while ignoring the downstream transport heartbeat."""
    files: dict[str, str] = {}
    for path in sorted(p for p in corpus.rglob("*") if p.is_file()):
        rel = path.relative_to(corpus).as_posix()
        if rel in {"newsroom-release.json", "_transport-receipt.json"}:
            continue
        files[rel] = sha256(path)
    material = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def previous_digest(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    digest = value.get("corpus_digest_sha256") if isinstance(value, dict) else None
    return digest if isinstance(digest, str) and digest else None


def inspect(
    corpus: Path,
    *,
    now: dt.datetime,
    max_age_hours: float,
    previous_corpus_digest: str | None = None,
) -> dict[str, Any]:
    release_path = corpus / "newsroom-release.json"
    transport_path = corpus / "_transport-receipt.json"
    if not release_path.is_file() or not transport_path.is_file():
        raise ValueError("airlock starvation: newsroom-release.json or _transport-receipt.json is missing")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    transport = json.loads(transport_path.read_text(encoding="utf-8"))
    if release.get("schema_version") != 1 or transport.get("schema_version") != 1:
        raise ValueError("unsupported airlock receipt schema")
    if release.get("state") != "READY" or transport.get("state") != "DELIVERED":
        raise ValueError("airlock receipt does not assert READY -> DELIVERED")
    for key in ("release_id", "corpus_digest_sha256"):
        if not release.get(key) or transport.get(key) != release.get(key):
            raise ValueError(f"airlock receipt mismatch for {key}")
    observed_digest = recompute_release_digest(corpus)
    if observed_digest != release["corpus_digest_sha256"]:
        raise ValueError("airlock corpus digest does not match released bytes")
    delivered = parse_time(str(transport.get("delivered_at") or ""))
    age_hours = max(0.0, (now - delivered).total_seconds() / 3600.0)
    if age_hours > max_age_hours:
        raise ValueError(
            f"airlock starvation: last delivery is {age_hours:.1f}h old (limit {max_age_hours:.1f}h)"
        )
    delta = (
        "NO_PUBLIC_DELTA"
        if previous_corpus_digest and previous_corpus_digest == release["corpus_digest_sha256"]
        else "PUBLIC_DELTA"
    )
    return {
        "schema_version": 1,
        "state": "HEALTHY",
        "public_delta_state": delta,
        "release_id": release["release_id"],
        "corpus_digest_sha256": release["corpus_digest_sha256"],
        "previous_corpus_digest_sha256": previous_corpus_digest,
        "public_evidence_cutoff": release.get("public_evidence_cutoff"),
        "development_count": int(release.get("development_count") or 0),
        "delivered_at": transport["delivered_at"],
        "transport_age_hours": round(age_hours, 3),
        "semantic_boundary": release.get("semantic_boundary", "unknown"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--max-age-hours", type=float, default=30.0)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--previous",
        type=Path,
        help="previous public-safe newsroom-status.json used only to classify delta vs heartbeat",
    )
    parser.add_argument("--now", help="UTC ISO timestamp used by tests/reproducible checks")
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    try:
        status = inspect(
            args.corpus,
            now=now,
            max_age_hours=args.max_age_hours,
            previous_corpus_digest=previous_digest(args.previous),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
