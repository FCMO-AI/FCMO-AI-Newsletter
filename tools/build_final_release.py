#!/usr/bin/env python3
"""Build the deterministic final FCMO AI Newsletter release overlay.

The source tree is archived as a byte-stable USTAR tar stream and compressed
with a fixed XZ preset.  ``--check`` performs the same build in memory and
compares it with the manifest and payload already on disk without writing.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import lzma
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO / "release-src"
DEFAULT_OVERLAY = REPO / "release-overlay" / "final"
XZ_PRESET = 9
RECALCULATED_FIELDS = (
    "parts",
    "archive_sha256",
    "base64_sha256",
    "index_sha256",
    "overlay_files",
)


@dataclass(frozen=True)
class Artifacts:
    archive: bytes
    encoded: str
    part_size: int
    file_count: int
    index_sha256: str

    @property
    def parts(self) -> list[str]:
        return [
            self.encoded[offset : offset + self.part_size]
            for offset in range(0, len(self.encoded), self.part_size)
        ]

    @property
    def hashes(self) -> dict[str, str | int]:
        return {
            "parts": len(self.parts),
            "archive_sha256": sha256(self.archive),
            "base64_sha256": sha256(self.encoded.encode("ascii")),
            "index_sha256": self.index_sha256,
            "overlay_files": self.file_count,
        }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files(source: Path) -> list[Path]:
    if not source.is_dir():
        raise ValueError(f"source tree does not exist or is not a directory: {source}")

    paths = list(source.rglob("*"))
    symlinks = [path for path in paths if path.is_symlink()]
    if symlinks:
        names = ", ".join(path.relative_to(source).as_posix() for path in symlinks)
        raise ValueError(f"source tree contains unsupported symlink(s): {names}")

    files = [path for path in paths if path.is_file()]
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def make_archive(source: Path, files: list[Path]) -> bytes:
    """Return the exact USTAR/XZ representation used by the frozen overlay."""
    tar_buffer = io.BytesIO()
    with tarfile.open(
        fileobj=tar_buffer,
        mode="w",
        format=tarfile.USTAR_FORMAT,
    ) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            data = path.read_bytes()
            member = tarfile.TarInfo(relative)
            member.size = len(data)
            member.mode = 0o644
            member.mtime = 0
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            archive.addfile(member, io.BytesIO(data))

    return lzma.compress(
        tar_buffer.getvalue(),
        format=lzma.FORMAT_XZ,
        preset=XZ_PRESET,
    )


def build_in_memory(source: Path, part_size: int) -> Artifacts:
    if part_size <= 0:
        raise ValueError("part_size_base64_chars must be positive")
    files = source_files(source)
    index = source / "index.html"
    if not index.is_file() or index.is_symlink():
        raise ValueError(f"source tree is missing a regular index.html: {index}")
    archive = make_archive(source, files)
    encoded = base64.b64encode(archive).decode("ascii")
    return Artifacts(
        archive=archive,
        encoded=encoded,
        part_size=part_size,
        file_count=len(files),
        index_sha256=sha256(index.read_bytes()),
    )


def read_manifest(path: Path) -> dict:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest is not a JSON object: {path}")
    try:
        part_size = manifest["part_size_base64_chars"]
    except KeyError as exc:
        raise ValueError("manifest is missing part_size_base64_chars") from exc
    if not isinstance(part_size, int) or isinstance(part_size, bool) or part_size <= 0:
        raise ValueError("manifest part_size_base64_chars must be a positive integer")
    return manifest


def expected_manifest(manifest: dict, artifacts: Artifacts) -> dict:
    result = dict(manifest)
    result.update(artifacts.hashes)
    return result


def disk_encoded_parts(overlay: Path) -> tuple[list[Path], str]:
    parts_dir = overlay / "parts"
    parts = sorted(parts_dir.glob("part-*.b64"))
    try:
        encoded = "".join(path.read_text(encoding="ascii").strip() for path in parts)
    except Exception as exc:
        raise ValueError(f"cannot read payload parts in {parts_dir}: {exc}") from exc
    return parts, encoded


def check(overlay: Path, manifest: dict, artifacts: Artifacts) -> None:
    mismatches: list[str] = []
    actual = artifacts.hashes
    for field in RECALCULATED_FIELDS:
        if manifest.get(field) != actual[field]:
            mismatches.append(f"{field}: manifest={manifest.get(field)!r}, rebuilt={actual[field]!r}")

    parts, disk_encoded = disk_encoded_parts(overlay)
    if len(parts) != actual["parts"]:
        mismatches.append(f"payload part count: disk={len(parts)!r}, rebuilt={actual['parts']!r}")
    if disk_encoded != artifacts.encoded:
        mismatches.append("payload parts do not match the rebuilt base64 payload")

    if mismatches:
        raise SystemExit("final release check FAILED:\n- " + "\n- ".join(mismatches))
    print(
        "final release check OK: "
        f"{actual['parts']} parts, archive {actual['archive_sha256'][:12]}..., "
        f"index {actual['index_sha256'][:12]}..."
    )


def write_overlay(overlay: Path, manifest: dict, artifacts: Artifacts) -> None:
    parts_dir = overlay / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    for path in parts_dir.glob("part-*.b64"):
        if path.is_dir() and not path.is_symlink():
            raise ValueError(f"cannot replace directory with payload part: {path}")
        path.unlink()

    for number, part in enumerate(artifacts.parts, 1):
        (parts_dir / f"part-{number:02d}.b64").write_bytes(part.encode("ascii"))

    manifest_path = overlay / "manifest.json"
    manifest_path.write_text(
        json.dumps(expected_manifest(manifest, artifacts), indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=DEFAULT_SOURCE,
        help="source tree to package (default: release-src/)",
    )
    parser.add_argument(
        "--overlay",
        type=Path,
        default=DEFAULT_OVERLAY,
        help="overlay directory to read/write (default: release-overlay/final/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild in memory and verify the manifest and payload without writing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    source = args.source.resolve()
    overlay = args.overlay.resolve()
    manifest_path = overlay / "manifest.json"
    try:
        manifest = read_manifest(manifest_path)
        artifacts = build_in_memory(source, manifest["part_size_base64_chars"])
        if args.check:
            check(overlay, manifest, artifacts)
        else:
            write_overlay(overlay, manifest, artifacts)
            print(
                f"built final release overlay: {artifacts.file_count} files, "
                f"{len(artifacts.parts)} parts, archive {sha256(artifacts.archive)}"
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"final release build FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
