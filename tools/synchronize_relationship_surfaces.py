#!/usr/bin/env python3
"""Synchronize the two public relationship surfaces from one canonical sequence.

`relationships.json` is the canonical in-memory projection produced by corpus
ingestion. The line-oriented companion is a transport/query convenience only and
must never become a second authority with its own stale ordering or objects.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_relationships(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError("relationships.json must be an array of JSON objects")
    return value


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        for row in rows
    ).encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def synchronize(site: Path) -> int:
    source = site / "data" / "relationships.json"
    target = site / "data" / "relationships.jsonl"
    if not source.is_file():
        raise ValueError(f"missing canonical relationship surface: {source}")
    rows = read_relationships(source)

    # Footnote: both public encodings now come from the exact same ordered Python
    # list. This prevents a frozen JSONL artifact from surviving while the JSON
    # array advances with a new Airlock corpus, which previously produced a late
    # readiness failure despite the newsroom itself having built successfully.
    atomic_write(target, jsonl_bytes(rows))

    roundtrip = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if roundtrip != rows:
        raise ValueError("relationship JSONL roundtrip differs from canonical JSON")
    print(f"relationship surfaces synchronized; rows={len(rows)}")
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    args = parser.parse_args(argv)
    try:
        synchronize(args.site.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"relationship surface synchronization FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
