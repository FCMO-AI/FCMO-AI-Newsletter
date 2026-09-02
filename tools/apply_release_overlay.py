#!/usr/bin/env python3
"""Apply the frozen FCMO AI Newsletter release overlay to a publication tree.

The release payload is split into base64 text parts because the repository
integration surface used during prelaunch cannot upload a binary archive
atomically. This script reconstructs the exact audited tarball, verifies it,
and extracts it over a target directory. It does not deploy anything.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "release-overlay" / "v4.1"
MANIFEST = OVERLAY / "manifest.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"release overlay refused: {message}")


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "publish"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parts = sorted((OVERLAY / "parts").glob("part-*.b64"))
    if len(parts) != manifest["parts"]:
        fail(f"expected {manifest['parts']} payload parts, found {len(parts)}")

    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    if sha256(encoded.encode("ascii")) != manifest["base64_sha256"]:
        fail("base64 payload hash mismatch")
    payload = base64.b64decode(encoded, validate=True)
    if sha256(payload) != manifest["archive_sha256"]:
        fail("archive hash mismatch")

    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as tf:
        members = tf.getmembers()
        for member in members:
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or member.issym() or member.islnk():
                fail(f"unsafe archive member: {member.name}")
        tf.extractall(target, members=members, filter="data")

    index = target / "index.html"
    if not index.is_file():
        fail("index.html missing after extraction")
    if sha256(index.read_bytes()) != manifest["index_sha256"]:
        fail("index.html hash mismatch after extraction")
    files = sum(1 for p in target.rglob("*") if p.is_file())
    if files < manifest["minimum_files_after_overlay"]:
        fail(f"publication tree unexpectedly small: {files} files")

    print(
        f"FCMO AI Newsletter {manifest['release']} overlay verified and applied: "
        f"{files} files in {target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
