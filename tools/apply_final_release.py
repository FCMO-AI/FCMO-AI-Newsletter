#!/usr/bin/env python3
"""Assemble and validate the frozen FCMO AI Newsletter public release.

Copies are expected to start from the repository's `site/` tree. This script
applies the hash-verified final overlay, validates the complete public tree, and
writes an exact build manifest. It never changes repository visibility or
performs a deployment.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import sys
import tarfile
from pathlib import Path
from html.parser import HTMLParser
from xml.etree import ElementTree

REPO = Path(__file__).resolve().parents[1]
OVERLAY = REPO / "release-overlay" / "final"
MANIFEST = OVERLAY / "manifest.json"
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
SECRET_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
PERSONAL_MAILBOX = re.compile(r"\b[A-Z0-9._%+-]+@(?:gmail|outlook|hotmail|protonmail)\.[A-Z]{2,}\b", re.I)
STALE_PUBLIC_BRAND = "AI Research Breakthroughs"

class _RemoteExecParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.dependencies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "script":
            src = data.get("src", "")
            if src.startswith(("http://", "https://", "//")):
                self.dependencies.append(src)
        elif tag == "link":
            rel = {token.lower() for token in data.get("rel", "").split()}
            href = data.get("href", "")
            if "stylesheet" in rel and href.startswith(("http://", "https://", "//")):
                self.dependencies.append(href)


def remote_exec_dependencies(text: str) -> list[str]:
    parser = _RemoteExecParser()
    parser.feed(text)
    return parser.dependencies


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_corpus_count(index_text: str) -> int:
    match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', index_text, re.S)
    if not match:
        raise ValueError("index is missing embedded fcmo-data corpus")
    data = json.loads(match.group(1))
    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError("embedded fcmo-data corpus has no records array")
    return len(records)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"final release refused: {message}")


def reconstruct(manifest: dict) -> bytes:
    parts = sorted((OVERLAY / "parts").glob("part-*.b64"))
    if len(parts) != manifest["parts"]:
        fail(f"expected {manifest['parts']} payload parts, found {len(parts)}")
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    if sha256(encoded.encode("ascii")) != manifest["base64_sha256"]:
        fail("base64 payload hash mismatch")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        fail(f"invalid base64 payload: {exc}")
    if sha256(payload) != manifest["archive_sha256"]:
        fail("archive hash mismatch")
    return payload


def extract(payload: bytes, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:*") as tf:
        members = tf.getmembers()
        for member in members:
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or member.issym() or member.islnk():
                fail(f"unsafe archive member: {member.name}")
        tf.extractall(target, members=members, filter="data")


def parse_public_data(target: Path, errors: list[str]) -> None:
    for path in sorted(target.rglob("*.json")):
        if path.name == "build-manifest.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {path.relative_to(target)}: {exc}")
    for path in sorted(target.rglob("*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:
                errors.append(f"invalid JSONL {path.relative_to(target)}:{n}: {exc}")
    try:
        ElementTree.parse(target / "feed.xml")
    except Exception as exc:
        errors.append(f"invalid RSS XML: {exc}")
    try:
        ElementTree.parse(target / "sitemap.xml")
    except Exception as exc:
        errors.append(f"invalid sitemap XML: {exc}")


def validate(target: Path, manifest: dict) -> None:
    errors: list[str] = []
    required = {
        "index.html", ".nojekyll", "robots.txt", "sitemap.xml",
        "about.html", "archive.html", "search.html", "topics.html",
        "organizations.html", "corrections.html", "feeds.html", "privacy.html",
        "license.html", "disclaimer.html", "feed.json", "feed.xml",
        "agent.json", "llms.txt", "llms-full.txt",
        "data/corrections.json", "data/site-manifest.json", "data/developments.json",
        "data/developments.jsonl", "data/search.json", "data/search.jsonl",
        "data/relationships.json", "data/relationships.jsonl", "data/publication-memory.json", "data/topics.json",
        "data/organizations.json", "data/media.json",
    }
    rels = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    for rel in sorted(required - rels):
        errors.append(f"missing required public file: {rel}")

    live_corpus_count: int | None = None
    index = target / "index.html"
    if index.is_file():
        if sha256(index.read_bytes()) != manifest["index_sha256"]:
            errors.append("index.html does not match audited final hash")
        home = index.read_text(encoding="utf-8")
        for token in ("window.FCMO_AI", "window.FCMOAgent", "window.fcmo", "fcmo-agent-query-v2", "--hot:#FD5204", "Signal Field"):
            if token not in home:
                errors.append(f"index missing release contract token: {token}")
        deps = remote_exec_dependencies(home)
        if deps:
            errors.append(f"index contains remote executable/style dependencies: {deps}")
        try:
            live_corpus_count = canonical_corpus_count(home)
        except Exception as exc:
            errors.append(f"canonical corpus validation failed: {exc}")

    briefs = sorted((target / "data/briefs").glob("FCMO-*.json")) if (target / "data/briefs").is_dir() else []
    bridges = sorted((target / "developments").glob("FCMO-*.html")) if (target / "developments").is_dir() else []
    edition_json = sorted((target / "data/editions").glob("*.json")) if (target / "data/editions").is_dir() else []
    edition_html = sorted((target / "editions").glob("*.html")) if (target / "editions").is_dir() else []
    if len(briefs) != manifest["canonical_briefs"]:
        errors.append(f"expected {manifest['canonical_briefs']} brief dossiers, found {len(briefs)}")
    if len(bridges) != manifest["stable_brief_routes"]:
        errors.append(f"expected {manifest['stable_brief_routes']} stable brief routes, found {len(bridges)}")
    if len(edition_json) != manifest["edition_routes"] or len(edition_html) != manifest["edition_routes"]:
        errors.append(f"expected {manifest['edition_routes']} edition JSON/HTML routes, found {len(edition_json)}/{len(edition_html)}")
    for p in briefs:
        if not PUBLIC_ID.fullmatch(p.stem):
            errors.append(f"invalid brief identifier: {p.name}")

    try:
        relationships_json = json.loads((target / "data/relationships.json").read_text(encoding="utf-8"))
        relationships_jsonl = []
        for n, line in enumerate((target / "data/relationships.jsonl").read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                errors.append(f"relationships JSONL line {n} is not a JSON object")
            relationships_jsonl.append(row)
        if not isinstance(relationships_json, list) or any(not isinstance(row, dict) for row in relationships_json):
            errors.append("relationships.json must be an array of JSON objects")
        elif relationships_jsonl != relationships_json:
            errors.append("relationships.json and relationships.jsonl must contain the same objects in the same order")
    except Exception as exc:
        errors.append(f"relationships surface validation failed: {exc}")

    try:
        media = json.loads((target / "data/media.json").read_text(encoding="utf-8"))
        real = sum(1 for row in media if row.get("sourced") is True)
        fallback = sum(1 for row in media if row.get("sourced") is False)
        expected = manifest["story_media"]
        if live_corpus_count is not None and (len(media), real, fallback) != (
            live_corpus_count, expected["real_preferred"], expected["embedded_fallback"]
        ):
            errors.append(
                f"media policy mismatch: expected total/real/fallback="
                f"{live_corpus_count}/{expected['real_preferred']}/{expected['embedded_fallback']}, "
                f"found {len(media)}/{real}/{fallback}"
            )
    except Exception as exc:
        errors.append(f"media manifest validation failed: {exc}")

    try:
        agent = json.loads((target / "agent.json").read_text(encoding="utf-8"))
        if agent.get("schema") != "fcmo-agent-discovery-v2" or agent.get("query_contract") != "fcmo-agent-query-v2":
            errors.append("agent discovery/query contract mismatch")
        if live_corpus_count is not None and agent.get("counts", {}).get("briefs") != live_corpus_count:
            errors.append(f"agent brief count mismatch: expected {live_corpus_count}")
    except Exception as exc:
        errors.append(f"agent.json validation failed: {exc}")

    parse_public_data(target, errors)

    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        rel = path.relative_to(target).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-text public file not allowed: {rel}")
            continue
        if PERSONAL_MAILBOX.search(text):
            errors.append(f"personal mailbox address detected: {rel}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"credential-like material detected: {rel}")
        if path.suffix == ".html":
            if STALE_PUBLIC_BRAND in text:
                errors.append(f"stale pre-newsletter branding detected: {rel}")
            deps = remote_exec_dependencies(text)
            if deps:
                errors.append(f"remote executable/style dependency detected: {rel}: {deps}")

    files = sum(1 for p in target.rglob("*") if p.is_file())
    if files < manifest["minimum_files_after_overlay"]:
        errors.append(f"publication tree unexpectedly small: {files} files")

    if errors:
        print("Final publication validation FAILED:")
        for error in errors:
            print("-", error)
        raise SystemExit(1)


def write_build_manifest(target: Path, release: str) -> None:
    entries = {}
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        rel = path.relative_to(target).as_posix()
        if rel == "build-manifest.json":
            continue
        entries[rel] = sha256(path.read_bytes())
    obj = {
        "schema_version": 6,
        "product": "FCMO AI Newsletter",
        "release": release,
        "deterministic": True,
        "files": entries,
    }
    (target / "build-manifest.json").write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "publish"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload = reconstruct(manifest)
    extract(payload, target)
    validate(target, manifest)
    write_build_manifest(target, manifest["release"])
    # Validate once more after build-manifest generation to include it in scans/counts.
    validate(target, manifest)
    files = sum(1 for p in target.rglob("*") if p.is_file())
    print(f"FCMO AI Newsletter {manifest['release']} READY: {files} public files; index {manifest['index_sha256'][:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
