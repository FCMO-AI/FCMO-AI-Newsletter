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
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from tools import corpus_guard
except ImportError:  # executed as tools/newswire_bridge.py or imported from tools/
    import corpus_guard  # type: ignore

AIRLOCK_SCHEMA = "fcmo-newswire-airlock-v2"
AIRLOCK_STATE = "READY_FOR_PUBLICATION"
LOCALE_SCHEMA = "fcmo-airlocked-locale-delta-v1"
CURATED_PART_SCHEMA = "fcmo-curated-locale-part-v1"
PUBLICATION_RECEIPT_SCHEMA = "fcmo-publication-receipt-v1"
LOCALES = ("es-419", "zh-Hans")
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
EDITION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PUBLICATION_PATH = re.compile(
    r"^archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/PUBLICATION\.json$"
)
PUBLICATION_KEYS = frozenset({
    "schema", "publication_date", "published_at", "edition_id", "story_ids", "status",
})
PUBLICATION_STATUSES = frozenset({"PUBLISHED", "QUIET"})
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

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
# Newsroom-owned corpus files (contracts/README.md): written by newsroom tools after a
# release is accepted, never part of a sealed release, excluded from the content
# digest, still privacy-scanned and JSON-validated.
NEWSROOM_FILES = frozenset(corpus_guard.NEWSROOM_FILES)
DYNAMIC_PATHS = (
    re.compile(r"^developments/FCMO-[0-9A-F]{12}\.html$"),
    re.compile(r"^editions/[0-9]{4}-[0-9]{2}-[0-9]{2}\.html$"),
    PUBLICATION_PATH,
)

# Footnote: these markers mirror the upstream independent transfer gate. They are
# deliberately broad because a false negative is costlier than retaining yesterday's
# public release. The private names and internal phrases themselves must never be
# written into this public repository, so they are kept only as salted SHA-256
# digests of their normalized token sequences: text is casefolded, split into \w+
# tokens, and every 1..MARKER_MAX_TOKENS-gram whose first token is a known marker
# start is hashed and compared. Token boundaries play the role the old \b did, so a
# bare private acronym never matches inside an ordinary word.
MARKER_SALT = b"fcmo-airlock-marker-v1\0"
MARKER_MAX_TOKENS = 6
MARKER_DIGESTS = frozenset({
    "2dde373fa209104564103cc3e1eaa443", "2e6b67d98fe5eaf3ac38159046a02ee2", "3a0986cf5a96cc6396a677a190dbf22f",
    "3c32d2c65bb88e4a47d4ac96a096d44b", "412c17137f5ff86566e0ce05f31b9352", "43a7f69df71249caf92e7e492fc1f595",
    "519993b78ebe48c82ad4a60469e1f1fd", "6298e51aaa3359a2ed0197d37fd9b05f", "62bdf76bd6e784d4bcb31a18f2520bdd",
    "696c7d13c20a3fcc35072354e8688db9", "73df98bfc60f7ff1afbcb5701dd6e37e", "7c710b04348d2e7e56fbcaf8244e4084",
    "84ca0f5d38e8d8bbcf417fd459b393c7", "8a697013f4d8c35456a647a02c9a9680", "973879fec1204a5d37c25df73ff4685b",
    "a07d1406efaad825676024f91644ad34", "a71001b27b0f71ae06603484d467334b", "af420ac85d6104fa5ad744a42420c399",
    "afa60b5d8c11593886351c6bd05f5689", "db4a8f4bdd2b261b639a4c425e41aac7", "e8a8ae78527487358bc852d9be8a565f",
    "ea4d2e9d4ce7e489f29851467b514aca", "f0b5152b53f1ec919d49df2e2ab817d3", "f29c168d1e9a9ed7d1ef4b2550a20cdb",
})
MARKER_FIRST_TOKENS = frozenset({
    "0139bfaedf4e6ca272b8651edcbc9482", "0321af8e343f0b6cf7ebb391c3accb09", "03cb40b03ce1a00048122c38640b4e2f",
    "04d529ec2204b396e662af53de2c0b14", "173368b37b234c70e907fff728764c5b", "2e6b67d98fe5eaf3ac38159046a02ee2",
    "49ad460ba9ad60c3565700c5b3e0410e", "60963adfc08319d65da28f7e9e8664af", "6298e51aaa3359a2ed0197d37fd9b05f",
    "62bdf76bd6e784d4bcb31a18f2520bdd", "676f83f27b4056c97258ae33a80b6b1f", "73df98bfc60f7ff1afbcb5701dd6e37e",
    "7abe098256c49852f171e64ad818eb7c", "a07d1406efaad825676024f91644ad34", "aeb67a1777d9859237d989f536c51583",
    "dbea37f010f17838c4ba843b3d62224e", "e88c25e480474e136cf37cc9a7109065", "e8a8ae78527487358bc852d9be8a565f",
    "ea4d2e9d4ce7e489f29851467b514aca", "f29c168d1e9a9ed7d1ef4b2550a20cdb",
})
# Consumer mailbox providers, hashed the same way (single token of the domain label).
PERSONAL_MAIL_PROVIDERS = frozenset({
    "13be2cc7180c500a440c24843c8e2161", "549053c203d0d5ca31a40b37e4d528a5",
    "8f250a2b5d7a820de11e1a1ce17e55df", "a800f82bf690a800a3d60ab78fb0667a",
})
# Structural leaks that name no one: private JSON keys and source-control provenance.
STRUCTURAL_MARKERS = re.compile(
    r'"projects"\s*:|source head [0-9a-f]{7,64}|'
    r'"(?:aliases|research_implications|engineering_implications|policy_implications)"\s*:',
    re.I,
)
TOKEN = re.compile(r"\w+")
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9-]+)\.[A-Z]{2,}\b", re.I)


def _marker_digest(phrase: str) -> str:
    return hashlib.sha256(MARKER_SALT + phrase.encode("utf-8")).hexdigest()[:32]


def private_marker(text: str) -> bool:
    """True when *text* contains a private/implementation/strategic marker."""
    if STRUCTURAL_MARKERS.search(text):
        return True
    tokens = TOKEN.findall(text.casefold())
    seen: dict[str, bool] = {}
    for index, token in enumerate(tokens):
        starts = seen.get(token)
        if starts is None:
            starts = seen[token] = _marker_digest(token) in MARKER_FIRST_TOKENS
        if not starts:
            continue
        for size in range(1, MARKER_MAX_TOKENS + 1):
            if index + size > len(tokens):
                break
            if _marker_digest(" ".join(tokens[index:index + size])) in MARKER_DIGESTS:
                return True
    return False


def personal_email(text: str) -> bool:
    """True when *text* contains an address at a consumer mailbox provider."""
    return any(_marker_digest(m.group(1).casefold()) in PERSONAL_MAIL_PROVIDERS for m in EMAIL.finditer(text))


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


def _cdmx_date(value: str) -> str:
    """Return an RFC 3339 timestamp's America/Mexico_City calendar date."""
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("published_at must include an RFC 3339 offset")
    try:
        from zoneinfo import ZoneInfo

        zone: Any = ZoneInfo("America/Mexico_City")
    except Exception:  # pragma: no cover - only on a host without tzdata
        zone = timezone(timedelta(hours=-6))
    return stamp.astimezone(zone).date().isoformat()


def validate_publication_receipt(document: Any, rel: str) -> dict[str, Any]:
    """Validate the frozen receipt plus the path/time invariants JSON Schema cannot express."""
    match = PUBLICATION_PATH.fullmatch(rel)
    if match is None:
        raise ValueError(f"{rel}: publication receipt path is not allowlisted")
    if not isinstance(document, dict):
        raise ValueError(f"{rel}: publication receipt is not an object")
    missing = sorted(PUBLICATION_KEYS - set(document))
    extra = sorted(set(document) - PUBLICATION_KEYS)
    if missing:
        raise ValueError(f"{rel}: publication receipt missing fields: {missing}")
    if extra:
        raise ValueError(f"{rel}: publication receipt has undeclared fields: {extra}")
    if document.get("schema") != PUBLICATION_RECEIPT_SCHEMA:
        raise ValueError(f"{rel}: publication receipt schema mismatch")

    publication_date = document.get("publication_date")
    if not isinstance(publication_date, str):
        raise ValueError(f"{rel}: publication_date must be a date")
    try:
        date.fromisoformat(publication_date)
    except ValueError as exc:
        raise ValueError(f"{rel}: invalid publication_date") from exc
    path_date = f"{match.group('year')}-{match.group('month')}-{match.group('day')}"
    try:
        date.fromisoformat(path_date)
    except ValueError as exc:
        raise ValueError(f"{rel}: invalid publication date in path") from exc
    if path_date != publication_date:
        raise ValueError(
            f"{rel}: path date {path_date} does not match receipt publication_date {publication_date}"
        )

    published_at = document.get("published_at")
    if not isinstance(published_at, str) or RFC3339.fullmatch(published_at) is None:
        raise ValueError(f"{rel}: published_at must be an RFC 3339 date-time")
    try:
        local_date = _cdmx_date(published_at)
    except ValueError as exc:
        raise ValueError(f"{rel}: invalid published_at") from exc
    if local_date != publication_date:
        raise ValueError(
            f"{rel}: published_at has CDMX date {local_date}, expected {publication_date}"
        )

    edition_id = document.get("edition_id")
    if not isinstance(edition_id, str) or EDITION_ID.fullmatch(edition_id) is None:
        raise ValueError(f"{rel}: invalid public edition_id")
    story_ids = document.get("story_ids")
    if (
        not isinstance(story_ids, list)
        or any(not isinstance(item, str) or PUBLIC_ID.fullmatch(item) is None for item in story_ids)
        or len(story_ids) != len(set(story_ids))
    ):
        raise ValueError(f"{rel}: story_ids must be unique public FCMO ids")
    if document.get("status") not in PUBLICATION_STATUSES:
        raise ValueError(f"{rel}: invalid publication status")
    return document


def load_publication_receipt(path: Path, root: Path) -> dict[str, Any]:
    """Load one transported receipt as strict UTF-8 JSON and validate its public contract."""
    rel = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{rel}: publication receipt is not UTF-8") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{rel}: invalid publication receipt JSON: {exc}") from exc
    return validate_publication_receipt(document, rel)


def publication_receipts(root: Path) -> list[dict[str, Any]]:
    """Return every valid transported receipt, newest last; invalid receipts fail closed."""
    root = root.resolve()
    found = [
        load_publication_receipt(path, root)
        for path in sorted(root.rglob("PUBLICATION.json"))
        if PUBLICATION_PATH.fullmatch(path.relative_to(root).as_posix())
    ]
    return sorted(found, key=lambda item: (item["publication_date"], item["published_at"], item["edition_id"]))


def newest_publication_receipt(root: Path) -> dict[str, Any] | None:
    """Newest valid authority receipt in a transported release, or None for legacy releases."""
    receipts = publication_receipts(root)
    return receipts[-1] if receipts else None


def release_digest(root: Path) -> str:
    """Reproduce ARB's content-addressed release digest, excluding airlock.json and newsroom files."""
    receipt = root / "airlock.json"
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p != receipt):
        if path.relative_to(root).as_posix() in NEWSROOM_FILES:
            continue
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel + b"\0" + _sha256_file(path).encode("ascii") + b"\n")
    return digest.hexdigest()


def _allowed(rel: str) -> bool:
    return rel in EXACT_PATHS or rel in NEWSROOM_FILES or any(pattern.fullmatch(rel) for pattern in DYNAMIC_PATHS)


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


def _curated_baseline_ids(
    i18n_root: Path | None,
    locale: str,
    errors: list[str],
) -> set[str]:
    """Read only the public, already-curated locale baseline committed in Newsletter."""
    if i18n_root is None:
        return set()
    locale_dir = i18n_root.resolve() / locale
    if not locale_dir.is_dir():
        errors.append(f"{locale}: curated locale baseline directory missing")
        return set()

    ids: set[str] = set()
    # Footnote: historical packs are an intentional migration baseline, not a fallback
    # translation service. Every future/new Story still has to arrive in the Airlock
    # unless its exact public ID is already present in these committed curated parts.
    for path in sorted(locale_dir.glob("part-*.json")):
        try:
            doc = _load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid curated locale part: {exc}")
            continue
        if (
            not isinstance(doc, dict)
            or doc.get("schema") != CURATED_PART_SCHEMA
            or doc.get("locale") != locale
            or not isinstance(doc.get("records"), dict)
        ):
            errors.append(f"{path}: curated locale part contract mismatch")
            continue
        for rid, overlay in doc["records"].items():
            if not isinstance(rid, str) or not PUBLIC_ID.fullmatch(rid) or not isinstance(overlay, dict):
                errors.append(f"{path}: malformed curated locale record {rid!r}")
                continue
            if rid in ids:
                errors.append(f"{locale}: duplicate curated locale record {rid}")
            ids.add(rid)
    return ids


def verify_release(root: Path, baseline_i18n: Path | None = None) -> dict[str, Any]:
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
        if private_marker(text):
            errors.append(f"{rel}: private/implementation/strategic marker")
        if personal_email(text):
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

    public_receipts: list[dict[str, Any]] = []
    for path in sorted(root.rglob("PUBLICATION.json")):
        rel = path.relative_to(root).as_posix()
        if PUBLICATION_PATH.fullmatch(rel) is None:
            # The allowlist loop already reports the path; do not accidentally
            # bless another PUBLICATION.json location by parsing it here.
            continue
        try:
            public_receipts.append(load_publication_receipt(path, root))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    edition_ids: set[str] = set()
    for publication in public_receipts:
        extra_story_ids = set(publication["story_ids"]) - ids
        if extra_story_ids:
            errors.append(
                "publication receipt contains story ids outside the public corpus: "
                f"{sorted(extra_story_ids)}"
            )
        edition_id = publication["edition_id"]
        if edition_id in edition_ids:
            errors.append(f"publication receipt reuses edition_id: {edition_id}")
        edition_ids.add(edition_id)

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

        baseline = _curated_baseline_ids(baseline_i18n, locale, errors)
        if baseline_i18n is None:
            # Footnote: standalone verification remains deliberately self-contained.
            # Only the production bridge may rely on the separately versioned public
            # Newsletter baseline, and it must name that baseline explicitly.
            if current != ids:
                errors.append(
                    f"{rel}: native-edition coverage does not exactly match public corpus "
                    f"(corpus={len(ids)}, locale={len(current)})"
                )
        else:
            # Footnote: during migration, the authoritative public edition is the
            # union of already-curated Newsletter history and the newly airlocked
            # delta. This closes the real race without pretending historical packs
            # were authored by ARB: any genuinely new English ID absent from both
            # sources is rejected before corpus/ can be mutated.
            coverage = current | (baseline & ids)
            missing = ids - coverage
            if missing:
                errors.append(
                    f"{rel}: native-edition coverage incomplete after curated baseline + "
                    f"airlock delta (missing={len(missing)})"
                )
        locale_ids[locale] = current
    if len(locale_ids) == len(LOCALES) and locale_ids[LOCALES[0]] != locale_ids[LOCALES[1]]:
        errors.append("native-edition delta ID sets differ between es-419 and zh-Hans")

    if errors:
        raise ValueError("airlock transfer verification FAILED\n- " + "\n- ".join(errors))
    return receipt


class GuardRefused(ValueError):
    """The corpus guard refused the candidate (REGRESSION_REFUSED, exit 3)."""


def _update_ledger(stage: Path, repo: Path, now: str) -> None:
    """Freeze first publication for newly published ids and record detected merges."""
    try:
        from tools import story_layer
    except ImportError:  # executed from tools/
        import story_layer  # type: ignore
    site = repo / "site"
    ledger, tombstones, changes = story_layer.update_ledger(stage, repo, site if site.is_dir() else None, now)
    if changes:
        story_layer.write_json_atomic(stage / "first-published.json", ledger)
        story_layer.write_json_atomic(stage / "tombstones.json", tombstones)
    for line in changes:
        print(line)


def guard_candidate(release: Path, corpus: Path, max_missing_ratio: float | None = None) -> dict[str, Any] | None:
    """Run the corpus guard on a verified release before corpus/ may change.

    Returns the guard result (None when there is no published corpus yet). Raises
    GuardRefused when the candidate drops more than the allowed share of live
    stories, and ValueError when the release carries newsroom-owned files.
    """
    carried_by_upstream = sorted(name for name in NEWSROOM_FILES if (release / name).exists())
    if carried_by_upstream:
        raise ValueError(f"release carries newsroom-owned files: {carried_by_upstream}")
    if not (corpus / "data" / "developments.jsonl").is_file():
        return None
    limit = corpus_guard.default_max_missing_ratio() if max_missing_ratio is None else max_missing_ratio
    tombstones = corpus_guard.load_tombstones(corpus_guard.default_tombstones_path(corpus))
    result = corpus_guard.check(corpus, release, tombstones, limit)
    print(corpus_guard.first_line(result))
    for line in corpus_guard.alert_lines(result):
        print(line, file=sys.stderr)
    if result["exit_code"] == corpus_guard.EXIT_REFUSED:
        raise GuardRefused(corpus_guard.first_line(result))
    return result


def carry_newsroom_files(corpus: Path, stage: Path, result: dict[str, Any] | None, now: str | None = None) -> None:
    """Give the staged corpus the newsroom files of the published one.

    Tombstones, the first-publication ledger and the wire status survive the swap;
    carried.jsonl is rewritten from the guard result; the ledger freezes newly
    published ids and records detected merges.
    """
    if result is None:
        return
    now = now or corpus_guard.resolve_now()
    for name in sorted(NEWSROOM_FILES - {"carried.jsonl"}):
        if (corpus / name).is_file():
            shutil.copy2(corpus / name, stage / name)
    lines = corpus_guard.carried_lines(result, corpus, now)
    if lines:
        (stage / "carried.jsonl").write_text(
            "".join(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n" for line in lines),
            encoding="utf-8",
        )
    if (stage / "first-published.json").is_file():
        _update_ledger(stage, corpus.parent, now)


def stage_release(
    release: Path,
    corpus: Path,
    baseline_i18n: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Replace corpus/ with a verified, guarded release without leaving a mixed old/new tree."""
    release = release.resolve()
    corpus = corpus.resolve()
    receipt = verify_release(release, baseline_i18n)
    result = guard_candidate(release, corpus)
    corpus.parent.mkdir(parents=True, exist_ok=True)

    # Footnote: copy into a sibling staging directory first, verify the copy again,
    # then rename. If staging fails, the previously accepted corpus is untouched.
    stage = Path(tempfile.mkdtemp(prefix=f".{corpus.name}.stage-", dir=corpus.parent))
    backup = corpus.parent / f".{corpus.name}.previous"
    try:
        shutil.rmtree(stage)
        shutil.copytree(release, stage, symlinks=False)
        carry_newsroom_files(corpus, stage, result, now)
        verify_release(stage, baseline_i18n)
        if backup.exists():
            shutil.rmtree(backup)
        if corpus.exists():
            corpus.rename(backup)
        stage.rename(corpus)
        verify_release(corpus, baseline_i18n)
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
    verify.add_argument("--baseline-i18n", type=Path)
    stage = sub.add_parser("stage", help="verify and atomically replace corpus/")
    stage.add_argument("release", type=Path)
    stage.add_argument("corpus", type=Path)
    stage.add_argument("--baseline-i18n", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            receipt = verify_release(args.release, args.baseline_i18n)
        else:
            receipt = stage_release(args.release, args.corpus, args.baseline_i18n)
    except GuardRefused as exc:
        print(f"corpus guard refused the release; corpus/ untouched: {exc}", file=sys.stderr)
        return corpus_guard.EXIT_REFUSED
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        f"airlock transfer OK: {receipt.get('release_id')} records={receipt.get('record_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
