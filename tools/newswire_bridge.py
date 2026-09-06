#!/usr/bin/env python3
"""Independent verifier/stager for the ARB -> FCMO AI Newsletter airlock.

This module deliberately knows only the *public transfer contract*. It never reads
private ARB state. The transport workflow may copy an already-built `_public_release`
from an ephemeral private checkout, destroy that checkout, and then hand this tool the
public candidate. The candidate is accepted only if its content identity, path
allowlist, locale deltas, UTF-8/JSON structure, and privacy scans all agree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

AIRLOCK_SCHEMA = "fcmo-newswire-airlock-v2"
AIRLOCK_STATE = "READY_FOR_PUBLICATION"
LOCALE_SCHEMA = "fcmo-airlocked-locale-delta-v1"
LOCALES = ("es-419", "zh-Hans")
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")

EXACT_PATHS = {
    ".nojekyll",
    "about.html",
    "airlock.json",
    "archive.html",
    "build-manifest.json",
    "corrections.html",
    "data/corrections.json",
    "data/developments.jsonl",
    "data/locales/es-419/records.json",
    "data/locales/zh-Hans/records.json",
    "data/relationships.jsonl",
    "data/search.json",
    "disclaimer.html",
    "feed.json",
    "feed.xml",
    "feeds.html",
    "index.html",
    "license.html",
    "organizations.html",
    "privacy.html",
    "search.html",
    "topics.html",
}
DYNAMIC_PATHS = (
    re.compile(r"^developments/FCMO-[0-9A-F]{12}\.html$"),
    re.compile(r"^editions/[0-9]{4}-[0-9]{2}-[0-9]{2}\.html$"),
)

# Footnote: these markers mirror the upstream independent transfer gate. They are
# deliberately broad because a false negative is costlier than retaining yesterday's
# public release. Innocent substring collisions are avoided for bare ARB via \b.
FORBIDDEN = re.compile(
    r"AI-Research-Breakthroughs|\bARB\b|\bBLM\b|Hermes[-–]Jarvis|NOVA TANKS|NOVASTAR|"
    r"EXOMNEME|\bCMPCT\b|\bMF2\b|magyarmex\.github@gmail\.com|project_relevance|"
    r'"projects"\s*:|source head [0-9a-f]{7,64}|'
    r"\bARB-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9A-F]{8}\b|PUBLICATION\.json|"
    r"repository schema is the CMS|research agents create structured canonical records|"
    r"canonical repository|repository receipt|canonical query projection|canonical research records|"
    r"run ledger|source watermark|candidate test|possible hypothesis|scale[- ]transfer warning|"
    r'"(?:aliases|research_implications|engineering_implications|policy_implications)"\s*:',
    re.I,
)
PERSONAL_EMAIL = re.compile(
    r"\b[A-Z0-9._%+-]+@(?:gmail|outlook|hotmail|protonmail)\.[A-Z]{2,}\b", re.I
)
RUNNER_PATH = re.compile(r"/(?:home/runner/work|github/workspace|mnt/data)/", re.I)
SECRET_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_digest(root: Path) -> str:
    """Reproduce ARB's content-addressed release digest, excluding airlock.json."""
    receipt = root / "airlock.json"
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p != receipt):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel + b"\0" + _sha256_file(path).encode("ascii") + b"\n")
    return digest.hexdigest()


def _allowed(rel: str) -> bool:
    return rel in EXACT_PATHS or any(pattern.fullmatch(rel) for pattern in DYNAMIC_PATHS)


def _canonical_ids(path: Path, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"data/developments.jsonl: unreadable UTF-8: {exc}")
        return ids
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"data/developments.jsonl:{number}: invalid JSONL: {exc}")
            continue
        rid = row.get("id") if isinstance(row, dict) else None
        if not isinstance(rid, str) or not PUBLIC_ID.fullmatch(rid):
            errors.append(f"data/developments.jsonl:{number}: invalid public record id {rid!r}")
            continue
        if rid in ids:
            errors.append(f"data/developments.jsonl:{number}: duplicate public record id {rid}")
        ids.add(rid)
    return ids


def verify_release(root: Path) -> dict[str, Any]:
    """Fail closed unless *root* is exactly one valid public airlock payload."""
    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        raise ValueError(f"airlock release is not a directory: {root}")

    # Footnote: required roots are checked before content parsing so an empty or
    # half-copied directory cannot be mistaken for a quiet-news release.
    for rel in ("index.html", ".nojekyll", "airlock.json", "data/developments.jsonl"):
        if not (root / rel).is_file():
            errors.append(f"{rel}: required transfer file missing")

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f"{rel}: symlink forbidden")
            continue
        if path.is_dir():
            continue
        if not _allowed(rel):
            errors.append(f"{rel}: path not allowlisted")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel}: non-UTF8/binary transfer file forbidden")
            continue
        if FORBIDDEN.search(text):
            errors.append(f"{rel}: private/implementation/strategic marker")
        if PERSONAL_EMAIL.search(text):
            errors.append(f"{rel}: personal email")
        if RUNNER_PATH.search(text):
            errors.append(f"{rel}: private runner path")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel}: secret-like material")
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
        elif path.suffix == ".jsonl" and rel != "data/developments.jsonl":
            for number, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{rel}:{number}: invalid JSONL: {exc}")

    ids = _canonical_ids(root / "data/developments.jsonl", errors) if (root / "data/developments.jsonl").is_file() else set()

    receipt: dict[str, Any] = {}
    receipt_path = root / "airlock.json"
    if receipt_path.is_file():
        try:
            value = _load_json(receipt_path)
            if not isinstance(value, dict):
                raise ValueError("receipt is not an object")
            receipt = value
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"airlock.json: invalid receipt: {exc}")
        else:
            if receipt.get("schema") != AIRLOCK_SCHEMA:
                errors.append("airlock.json: schema mismatch")
            if receipt.get("state") != AIRLOCK_STATE:
                errors.append("airlock.json: state is not READY_FOR_PUBLICATION")
            if receipt.get("record_count") != len(ids):
                errors.append(
                    f"airlock.json: record_count={receipt.get('record_count')!r} but corpus has {len(ids)}"
                )
            if receipt.get("contract") != {
                "public_only": True,
                "raw_private_source_forbidden": True,
                "semantic_declassification": True,
            }:
                errors.append("airlock.json: public/declassification contract mismatch")
            actual_digest = release_digest(root)
            if receipt.get("corpus_digest") != actual_digest:
                errors.append("airlock.json: corpus digest does not match transferred bytes")
            expected_release_id = f"newswire-{actual_digest[:24]}"
            if receipt.get("release_id") != expected_release_id:
                errors.append("airlock.json: release_id does not match content digest")

    locale_ids: dict[str, set[str]] = {}
    for locale in LOCALES:
        rel = f"data/locales/{locale}/records.json"
        path = root / rel
        if not path.is_file():
            errors.append(f"{rel}: required native-edition delta missing")
            continue
        try:
            doc = _load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{rel}: invalid locale delta: {exc}")
            continue
        if not isinstance(doc, dict) or doc.get("schema") != LOCALE_SCHEMA or doc.get("locale") != locale:
            errors.append(f"{rel}: locale contract mismatch")
            continue
        rows = doc.get("records")
        if not isinstance(rows, dict):
            errors.append(f"{rel}: records object missing")
            continue
        current: set[str] = set()
        for rid, overlay in rows.items():
            if not isinstance(rid, str) or not PUBLIC_ID.fullmatch(rid) or not isinstance(overlay, dict):
                errors.append(f"{rel}: malformed locale record {rid!r}")
                continue
            current.add(rid)
        if not current.issubset(ids):
            errors.append(f"{rel}: locale delta contains IDs outside the public corpus: {sorted(current - ids)}")
        locale_ids[locale] = current
    if len(locale_ids) == len(LOCALES) and locale_ids[LOCALES[0]] != locale_ids[LOCALES[1]]:
        errors.append("native-edition delta ID sets differ between es-419 and zh-Hans")

    if errors:
        raise ValueError("airlock transfer verification FAILED\n- " + "\n- ".join(errors))
    return receipt


def stage_release(release: Path, corpus: Path) -> dict[str, Any]:
    """Replace corpus/ with a verified release without leaving a mixed old/new tree."""
    release = release.resolve()
    corpus = corpus.resolve()
    receipt = verify_release(release)
    corpus.parent.mkdir(parents=True, exist_ok=True)

    # Footnote: copy into a sibling staging directory first, verify the copy again,
    # then rename. If staging fails, the previously accepted corpus is untouched.
    stage = Path(tempfile.mkdtemp(prefix=f".{corpus.name}.stage-", dir=corpus.parent))
    backup = corpus.parent / f".{corpus.name}.previous"
    try:
        shutil.rmtree(stage)
        shutil.copytree(release, stage, symlinks=False)
        verify_release(stage)
        if backup.exists():
            shutil.rmtree(backup)
        if corpus.exists():
            corpus.rename(backup)
        stage.rename(corpus)
        verify_release(corpus)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if not corpus.exists() and backup.exists():
            backup.rename(corpus)
        raise
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="verify one sanitized airlock release")
    verify.add_argument("release", type=Path)
    stage = sub.add_parser("stage", help="verify and atomically replace corpus/")
    stage.add_argument("release", type=Path)
    stage.add_argument("corpus", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = verify_release(args.release) if args.command == "verify" else stage_release(args.release, args.corpus)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=os.sys.stderr)
        return 1
    print(
        f"airlock transfer OK: {receipt.get('release_id')} records={receipt.get('record_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
