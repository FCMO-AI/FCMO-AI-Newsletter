#!/usr/bin/env python3
"""Per-record monotonicity guard for the published corpus (contracts/README.md).

The guard decides whether a candidate snapshot may replace the published corpus.
It works per record: one missing story never blocks new stories.

    corpus_guard.py check --published P --candidate C [--tombstones T]
                          [--max-missing-ratio R] [--report OUT.json] [--now ISO8601]
    corpus_guard.py apply --published P --candidate C --out DIR [same options]
    corpus_guard.py live-ids CORPUS [--tombstones T]

Verdicts (first stdout line, alerts on stderr):

    REGRESSION_REFUSED  more than R of the live ids are missing   exit 3, nothing written
    CARRY_FORWARD       some live ids missing, within R            exit 0, missing ids carried
    OK                  nothing missing                            exit 0
    (usage)             bad arguments, unreadable/invalid input    exit 2, nothing written

A missing id without a tombstone is never dropped silently: ``apply`` keeps its
last published record in ``DIR/carried.jsonl`` until it comes back upstream or a
tombstone withdraws it. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
THRESHOLDS = REPO / "contracts" / "thresholds.json"
DEFAULT_MAX_MISSING_RATIO = 0.2
PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
RELEASE_ID = re.compile(r"^newswire-[0-9a-f]{24}$")
WITHDRAWN_STATUSES = {"withdrawn", "superseded"}
REPORT_SCHEMA = "fcmo-corpus-guard-report-v1"
TOMBSTONES_SCHEMA = "fcmo-tombstones-v1"
# Files the newsroom writes into corpus/. They are never part of a sealed release:
# excluded from the content digest and from the airlock allowlist.
NEWSROOM_FILES = ("wire-status.json", "tombstones.json", "carried.jsonl", "first-published.json")
EXIT_OK, EXIT_USAGE, EXIT_REFUSED = 0, 2, 3


class GuardInputError(ValueError):
    """Unreadable or invalid guard input (exit 2)."""


# ---------------------------------------------------------------------------------------
# Time and thresholds
# ---------------------------------------------------------------------------------------
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def resolve_now(flag: str | None = None) -> str:
    """--now, else FCMO_NOW, else the real clock; UTC truncated to seconds."""
    raw = flag or os.environ.get("FCMO_NOW")
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise GuardInputError("--now is not an ISO 8601 timestamp") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = utc_now()
    return parsed.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_max_missing_ratio(path: Path = THRESHOLDS) -> float:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["corpus_guard"]["max_missing_ratio"]
    except (OSError, ValueError, KeyError, TypeError):
        return DEFAULT_MAX_MISSING_RATIO
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else DEFAULT_MAX_MISSING_RATIO


# ---------------------------------------------------------------------------------------
# Reading corpora
# ---------------------------------------------------------------------------------------
def records_path(corpus: Path) -> Path:
    corpus = Path(corpus)
    return corpus / "data" / "developments.jsonl" if corpus.is_dir() else corpus


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise GuardInputError(f"{label}: unreadable ({type(exc).__name__})") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GuardInputError(f"{label}: line {number} is not JSON") from exc
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not PUBLIC_ID.fullmatch(row["id"]):
            raise GuardInputError(f"{label}: line {number} has no public id")
        rows.append(row)
    return rows


def read_records(corpus: Path, label: str = "corpus") -> list[dict[str, Any]]:
    path = records_path(corpus)
    if not path.is_file():
        raise GuardInputError(f"{label}: no data/developments.jsonl")
    return _read_jsonl(path, label)


def read_carried(corpus: Path) -> list[dict[str, Any]]:
    corpus = Path(corpus)
    path = corpus / "carried.jsonl" if corpus.is_dir() else None
    if path is None or not path.is_file():
        return []
    rows = _read_jsonl(path, "carried.jsonl")
    for row in rows:
        if not isinstance(row.get("record"), dict) or row["record"].get("id") != row["id"]:
            raise GuardInputError("carried.jsonl: a line has no matching record")
    return rows


def load_tombstones(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GuardInputError(f"tombstones: unreadable ({type(exc).__name__})") from exc
    if not isinstance(document, dict) or document.get("schema") != TOMBSTONES_SCHEMA or not isinstance(document.get("tombstones"), list):
        raise GuardInputError("tombstones: not a fcmo-tombstones-v1 document")
    for entry in document["tombstones"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not PUBLIC_ID.fullmatch(entry["id"]):
            raise GuardInputError("tombstones: entry without a public id")
    return document


def active_tombstones(document: dict[str, Any] | None) -> set[str]:
    if not document:
        return set()
    return {e["id"] for e in document.get("tombstones", []) if e.get("reinstated_at") is None}


def default_tombstones_path(published: Path) -> Path | None:
    candidate = Path(published) / "tombstones.json" if Path(published).is_dir() else None
    return candidate if candidate is not None and candidate.is_file() else None


def content_digest(root: Path) -> str:
    """ARB's content digest of a release tree, without airlock.json and newsroom files."""
    digest = hashlib.sha256()
    root = Path(root)
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel == "airlock.json" or rel in NEWSROOM_FILES:
            continue
        digest.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii") + b"\n")
    return digest.hexdigest()


def read_release_id(corpus: Path) -> str | None:
    corpus = Path(corpus)
    airlock = corpus / "airlock.json" if corpus.is_dir() else None
    if airlock is None or not airlock.is_file():
        return None
    try:
        value = json.loads(airlock.read_text(encoding="utf-8")).get("release_id")
    except (OSError, ValueError, AttributeError):
        return None
    return value if isinstance(value, str) and RELEASE_ID.fullmatch(value) else None


# ---------------------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------------------
def verdict(
    published: Iterable[str],
    candidate: Iterable[str],
    tombstoned: Iterable[str] = (),
    upstream_withdrawn: Iterable[str] = (),
    max_missing_ratio: float = DEFAULT_MAX_MISSING_RATIO,
) -> dict[str, Any]:
    """The guard's set algebra over id sets (README, "Set algebra")."""
    live = set(published)
    cand = set(candidate)
    tomb = set(tombstoned)
    up = set(upstream_withdrawn) & cand
    by_tombstone = live & tomb
    by_upstream = (live & up) - by_tombstone
    missing = sorted((live - cand) - by_tombstone - by_upstream)
    ratio = round(len(missing) / len(live), 4) if live else 0.0
    if ratio > max_missing_ratio:
        name, code = "REGRESSION_REFUSED", EXIT_REFUSED
    elif missing:
        name, code = "CARRY_FORWARD", EXIT_OK
    else:
        name, code = "OK", EXIT_OK
    return {
        "verdict": name,
        "exit_code": code,
        "ratio": ratio,
        "missing": missing,
        "carried": missing if name == "CARRY_FORWARD" else [],
        "withdrawn": [{"id": i, "source": "tombstone"} for i in sorted(by_tombstone)]
        + [{"id": i, "source": "upstream"} for i in sorted(by_upstream)],
        "added": sorted(cand - live - tomb - up),
        "suppressed": sorted((cand & tomb) - live),
        "alerts": {"OK": [], "CARRY_FORWARD": ["CORPUS_CARRY_FORWARD"],
                   "REGRESSION_REFUSED": ["CORPUS_REGRESSION_REFUSED"]}[name],
        "live_count": len(live),
        "candidate_count": len(cand),
    }


def live_ids(records: list[dict[str, Any]], carried: list[dict[str, Any]], tombstoned: Iterable[str] = ()) -> set[str]:
    """Published live ids: records plus carried ids, minus withdrawn statuses and tombstones."""
    already_withdrawn = {r["id"] for r in records if r.get("status") in WITHDRAWN_STATUSES}
    return ({r["id"] for r in records} | {c["id"] for c in carried}) - already_withdrawn - set(tombstoned)


def check(
    published: Path,
    candidate: Path,
    tombstones: dict[str, Any] | None = None,
    max_missing_ratio: float = DEFAULT_MAX_MISSING_RATIO,
) -> dict[str, Any]:
    """Compare two corpora; raises GuardInputError on unreadable input."""
    pub_rows = read_records(published, "published")
    pub_carried = read_carried(published)
    cand_rows = read_records(candidate, "candidate")
    already_withdrawn = {r["id"] for r in pub_rows if r.get("status") in WITHDRAWN_STATUSES}
    live = ({r["id"] for r in pub_rows} | {c["id"] for c in pub_carried}) - already_withdrawn
    result = verdict(
        live,
        (r["id"] for r in cand_rows),
        active_tombstones(tombstones),
        (r["id"] for r in cand_rows if r.get("status") in WITHDRAWN_STATUSES),
        max_missing_ratio,
    )
    result["published_release_id"] = read_release_id(published)
    result["candidate_release_id"] = read_release_id(candidate)
    result["_published_rows"] = pub_rows
    result["_published_carried"] = pub_carried
    return result


def first_line(result: dict[str, Any]) -> str:
    def ids(values: list[str]) -> str:
        return ",".join(values) if values else "-"

    return (
        f"{result['verdict']} missing={ids(result['missing'])} "
        f"withdrawn={ids([w['id'] for w in result['withdrawn']])} added={len(result['added'])} "
        f"published={result['live_count']} candidate={result['candidate_count']} ratio={result['ratio']:.4f}"
    )


def alert_lines(result: dict[str, Any]) -> list[str]:
    if result["verdict"] == "CARRY_FORWARD":
        return [f"ALERT CORPUS_CARRY_FORWARD missing={','.join(result['missing'])}"]
    if result["verdict"] == "REGRESSION_REFUSED":
        return [f"ALERT CORPUS_REGRESSION_REFUSED missing={len(result['missing'])} ratio={result['ratio']:.4f}"]
    return []


def report(result: dict[str, Any], checked_at: str, max_missing_ratio: float) -> dict[str, Any]:
    """The --report document (contracts/corpus-guard.report.schema.json): ids, counts, codes."""
    return {
        "schema": REPORT_SCHEMA,
        "verdict": result["verdict"],
        "exit_code": result["exit_code"],
        "checked_at": checked_at,
        "max_missing_ratio": max_missing_ratio,
        "ratio": result["ratio"],
        "published": {"release_id": result.get("published_release_id"), "count": result["live_count"]},
        "candidate": {"release_id": result.get("candidate_release_id"), "count": result["candidate_count"]},
        "missing": result["missing"],
        "carried": result["carried"],
        "withdrawn": result["withdrawn"],
        "added": result["added"],
        "suppressed": result["suppressed"],
        "alerts": result["alerts"],
    }


# ---------------------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------------------
def carried_lines(result: dict[str, Any], published: Path, now: str) -> list[dict[str, Any]]:
    """carried.jsonl lines for the result's carried ids (corpus-carried.schema.json)."""
    if not result["carried"]:
        return []
    by_id = {r["id"]: r for r in result["_published_rows"]}
    previous = {c["id"]: c for c in result["_published_carried"]}
    release_id = result.get("published_release_id")
    if release_id is None and Path(published).is_dir():
        release_id = f"newswire-{content_digest(Path(published))[:24]}"
    lines = []
    for rid in result["carried"]:
        before = previous.get(rid)
        record = by_id.get(rid) or (before or {}).get("record")
        last_release = (before or {}).get("last_release_id") if rid not in by_id else release_id
        last_release = last_release or release_id
        if record is None or not isinstance(last_release, str) or not RELEASE_ID.fullmatch(last_release):
            raise GuardInputError(f"cannot carry {rid}: the published release id is unknown")
        lines.append({
            "id": rid,
            "carried_since": (before or {}).get("carried_since") or now,
            "last_release_id": last_release,
            "record": record,
        })
    return lines


def _write_tree(out: Path, build) -> None:
    """Build a tree next to ``out`` and swap it in, so a failure leaves ``out`` untouched."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{out.name}.", dir=out.parent))
    old = out.parent / f".{out.name}.old-{os.getpid()}"
    try:
        build(tmp)
        if out.exists():
            out.rename(old)
        tmp.rename(out)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        if old.exists() and not out.exists():
            old.rename(out)
        raise
    shutil.rmtree(old, ignore_errors=True)


def apply(
    published: Path,
    candidate: Path,
    out: Path,
    tombstones: dict[str, Any] | None = None,
    max_missing_ratio: float = DEFAULT_MAX_MISSING_RATIO,
    now: str | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run check; on OK/CARRY_FORWARD write the candidate plus carried.jsonl to ``out``.

    The published corpus's newsroom files (tombstones, first-publication ledger,
    wire status) are kept; ``carried.jsonl`` is rewritten from the result. On
    REGRESSION_REFUSED nothing is written.
    """
    now = now or resolve_now()
    if result is None:
        result = check(published, candidate, tombstones, max_missing_ratio)
    if result["exit_code"] != EXIT_OK:
        return result
    lines = carried_lines(result, published, now)
    published, candidate = Path(published), Path(candidate)
    keep: dict[str, bytes] = {}
    if published.is_dir():
        for name in NEWSROOM_FILES:
            if name != "carried.jsonl" and (published / name).is_file():
                keep[name] = (published / name).read_bytes()
    Path(out).resolve().parent.mkdir(parents=True, exist_ok=True)
    if candidate.is_dir():
        staged = Path(tempfile.mkdtemp(prefix=".guard-candidate.", dir=Path(out).resolve().parent))
        try:
            shutil.rmtree(staged)
            shutil.copytree(candidate, staged)
        except BaseException:
            shutil.rmtree(staged, ignore_errors=True)
            raise
    else:
        staged = None
        body = candidate.read_bytes()

    def build(tmp: Path) -> None:
        if staged is not None:
            for child in staged.iterdir():
                if child.name in NEWSROOM_FILES:
                    continue
                shutil.move(str(child), tmp / child.name)
        else:
            (tmp / "data").mkdir(parents=True, exist_ok=True)
            (tmp / "data" / "developments.jsonl").write_bytes(body)
        for name, data in keep.items():
            (tmp / name).write_bytes(data)
        if lines:
            (tmp / "carried.jsonl").write_text(
                "".join(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n" for line in lines),
                encoding="utf-8",
            )

    try:
        _write_tree(Path(out), build)
    finally:
        if staged is not None:
            shutil.rmtree(staged, ignore_errors=True)
    return result


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--tombstones", type=Path)
    parser.add_argument("--max-missing-ratio", type=float)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--now")


def run(args: argparse.Namespace) -> int:
    ratio_limit = args.max_missing_ratio if args.max_missing_ratio is not None else default_max_missing_ratio()
    if not 0 <= ratio_limit <= 1:
        raise GuardInputError("--max-missing-ratio must be within [0, 1]")
    now = resolve_now(args.now)
    tomb_path = args.tombstones if args.tombstones is not None else default_tombstones_path(args.published)
    tombstones = load_tombstones(tomb_path)
    result = check(args.published, args.candidate, tombstones, ratio_limit)
    if args.command == "apply" and result["exit_code"] == EXIT_OK:
        apply(args.published, args.candidate, args.out, tombstones, ratio_limit, now, result)
    print(first_line(result))
    for line in alert_lines(result):
        print(line, file=sys.stderr)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report(result, now, ratio_limit), indent=2) + "\n", encoding="utf-8")
    return result["exit_code"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    _add_common(sub.add_parser("check", help="compare a candidate with the published corpus"))
    apply_parser = sub.add_parser("apply", help="check, then write the candidate plus carried.jsonl")
    _add_common(apply_parser)
    apply_parser.add_argument("--out", type=Path, required=True)
    ids_parser = sub.add_parser("live-ids", help="print the live ids of a corpus, one per line")
    ids_parser.add_argument("corpus", type=Path)
    ids_parser.add_argument("--tombstones", type=Path)
    ids_parser.add_argument("--publishable", action="store_true",
                            help="also drop records the story layer would quarantine")
    args = parser.parse_args(argv)
    try:
        if args.command == "live-ids":
            tomb_path = args.tombstones if args.tombstones is not None else default_tombstones_path(args.corpus)
            records = read_records(args.corpus)
            carried = read_carried(args.corpus)
            ids = live_ids(records, carried, active_tombstones(load_tombstones(tomb_path)))
            if args.publishable:
                try:
                    from tools import taxonomy  # type: ignore
                except ImportError:  # run as a script from tools/
                    import taxonomy  # type: ignore
                rows = records + [c["record"] for c in carried if c["id"] not in {r["id"] for r in records}]
                good, _ = taxonomy.normalize_rows(rows)
                ids &= {r["id"] for r in good}
            for rid in sorted(ids):
                print(rid)
            return EXIT_OK
        return run(args)
    except GuardInputError as exc:
        print(f"USAGE {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
