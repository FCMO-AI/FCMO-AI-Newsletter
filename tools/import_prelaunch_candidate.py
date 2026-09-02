#!/usr/bin/env python3
"""Import the recovered FCMO AI Newsletter prelaunch artifacts safely.

This utility deliberately requires the exact QA-approved artifacts. It does not
fetch private research state, mutate `main`, or publish anything. It copies the
validated public machine bundle into `site/` and then installs the final Signal
Field v4 standalone document as `site/index.html`.

Usage:
    python tools/import_prelaunch_candidate.py \
        /path/to/FCMO-AI-Newsletter-Final-Prelaunch-Bundle.zip \
        /path/to/FCMO-AI-Newsletter-Signal-Field-v4-final.html
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

BUNDLE_NAME = "FCMO-AI-Newsletter-Final-Prelaunch-Bundle.zip"
BUNDLE_SHA256 = "93c1294eaff05eba9bad0c1c90c25af127ddbb0e8a7b4b6663b6c39b0c3881b0"
BUNDLE_FILE_COUNT = 43
V4_NAME = "FCMO-AI-Newsletter-Signal-Field-v4-final.html"
V4_SHA256 = "0bfe649a944b7a099f4109d751085359707f41f07bcd8da33fdf251eeabcc76e"

# QA/support files in the recovered archive are useful receipts, but they are not
# part of the reader/agent publication surface. The older bundle index is also
# superseded by the final Signal Field v4 artifact.
SKIP_BUNDLE_FILES = {"index.html", "manifest.json", "privacy-scan.json"}

REQUIRED_MACHINE_FILES = {
    "agent.json",
    "llms.txt",
    "llms-full.txt",
    "feed.json",
    "feed.xml",
    "data/site-manifest.json",
    "data/developments.json",
    "data/developments.jsonl",
    "data/search.json",
    "data/search.jsonl",
    "data/relationships.json",
    "data/publication-memory.json",
    "data/topics.json",
    "data/organizations.json",
    "data/media.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"prelaunch import refused: {message}")


def validate_inputs(bundle: Path, v4: Path) -> None:
    if not bundle.is_file():
        fail(f"bundle missing: {bundle}")
    if not v4.is_file():
        fail(f"Signal Field artifact missing: {v4}")
    if bundle.name != BUNDLE_NAME:
        fail(f"unexpected bundle filename: {bundle.name}")
    if v4.name != V4_NAME:
        fail(f"unexpected Signal Field filename: {v4.name}")
    if sha256(bundle) != BUNDLE_SHA256:
        fail("bundle SHA-256 does not match the recovered QA-approved artifact")
    if sha256(v4) != V4_SHA256:
        fail("Signal Field SHA-256 does not match the final QA-approved artifact")

    html = v4.read_text(encoding="utf-8")
    for marker in (
        "FCMO AI Newsletter — Signal Field Interactive",
        "--hot:#FD5204",
        "window.FCMO_AI",
        "Signal Field",
        'referrerpolicy="no-referrer"',
    ):
        if marker not in html:
            fail(f"Signal Field marker missing: {marker}")


def safe_members(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if len(infos) != BUNDLE_FILE_COUNT:
        fail(f"bundle contains {len(infos)} files, expected {BUNDLE_FILE_COUNT}")
    for info in infos:
        p = Path(info.filename)
        if info.is_dir():
            continue
        if p.is_absolute() or ".." in p.parts:
            fail(f"unsafe archive path: {info.filename}")
    names = {i.filename for i in infos if not i.is_dir()}
    missing = sorted(REQUIRED_MACHINE_FILES - names)
    if missing:
        fail("bundle is missing machine files: " + ", ".join(missing))
    briefs = [n for n in names if n.startswith("data/briefs/") and n.endswith(".json")]
    if len(briefs) != 22:
        fail(f"expected 22 per-brief dossiers, found {len(briefs)}")
    return infos


def validate_extracted(root: Path) -> None:
    for path in sorted(root.rglob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(root.rglob("*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    json.loads(line)
                except Exception as exc:
                    fail(f"invalid JSONL {path.name}:{n}: {exc}")
    ElementTree.parse(root / "feed.xml")


def install(bundle: Path, v4: Path, site: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="fcmo-prelaunch-") as tmp:
        extracted = Path(tmp)
        with zipfile.ZipFile(bundle) as zf:
            infos = safe_members(zf)
            for info in infos:
                if not info.is_dir():
                    zf.extract(info, extracted)
        validate_extracted(extracted)

        site.mkdir(parents=True, exist_ok=True)
        copied = 0
        for source in sorted(p for p in extracted.rglob("*") if p.is_file()):
            rel = source.relative_to(extracted).as_posix()
            if rel in SKIP_BUNDLE_FILES:
                continue
            target = site / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1

        shutil.copy2(v4, site / "index.html")

    # Preserve the existing static Pages marker and utility/legal pages; this tool
    # only replaces the front-page application and adds the recovered machine data.
    (site / ".nojekyll").touch(exist_ok=True)

    installed = (site / "index.html").read_text(encoding="utf-8")
    if "window.FCMO_AI" not in installed or "--hot:#FD5204" not in installed:
        fail("installed index failed final Signal Field verification")
    if not (site / "agent.json").is_file() or not (site / "data/briefs").is_dir():
        fail("installed machine surface is incomplete")

    print(
        "FCMO prelaunch candidate imported safely: "
        f"Signal Field v4 + {copied} machine/public files; no deployment performed"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    bundle = Path(sys.argv[1]).expanduser().resolve()
    v4 = Path(sys.argv[2]).expanduser().resolve()
    repo = Path(__file__).resolve().parents[1]
    site = repo / "site"
    validate_inputs(bundle, v4)
    install(bundle, v4, site)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
