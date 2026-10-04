#!/usr/bin/env python3
"""Refresh preflight, reader-facing newsroom status and the downstream newsroom ACK.

Liveness comes only from ``corpus/wire-status.json`` (contracts/README.md,
"Wire status"); ``corpus/airlock.json.generated_at`` is content metadata, never a
heartbeat. The preflight classifies the wire at ``now`` and picks one path:

* ``rebuild`` when the sealed content or the builder changed. A builder change
  rebuilds even when the upstream is stale; that is a warning, not a block.
* ``status`` otherwise: only ``site/data/newsroom-status.json`` is refreshed, so a
  quiet day or a delayed upstream is reported honestly without a rebuild.

Exit codes: 0 classified (including transport outages), 2 unusable
input. Native-language backlog is reported explicitly and never makes a fully
validated English Story layer false.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from tools import wire_status
    from tools.publication_freshness import publication_status
    from tools.paper.freshness import corpus_freshness
except ImportError:  # executed as tools/newsroom_receipt.py
    import wire_status  # type: ignore[no-redef]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tools.publication_freshness import publication_status
    from tools.paper.freshness import corpus_freshness

AIRLOCK_SCHEMA = "fcmo-newswire-airlock-v2"
STATUS_SCHEMA = "fcmo-newsroom-status-v2"

# Files whose semantics can change the durable newsroom product. A content-identical
# Airlock still requires a rebuild when this builder identity changes.
BUILDER_INPUTS = (
    ".github/workflows/daily-refresh.yml",
    "scaffold/release-index.html",
    "scaffold/agent.json",
    "tools/ingest_corpus.py",
    "tools/synchronize_relationship_surfaces.py",
    "tools/sync_airlocked_locales.py",
    "tools/reconcile_locale_overlays.py",
    "tools/refresh_locale_identity.py",
    "tools/validate_localizations_partial.py",
    "tools/public_research_desk.py",
    "tools/visual_desk.py",
    "tools/build_newsroom_surfaces.py",
    "tools/mark_pending_localizations.py",
    "tools/editorial_freshness.py",
    "tools/promote_story_front_page.py",
    "tools/build_editorial_frontends.py",
    "tools/finalize_editorial_frontends.py",
    "tools/newsroom_receipt.py",
    "tools/wire_status.py",
    "tools/edition_banner.py",
    "tools/build_final_release.py",
    "tools/build_ready_receipt.py",
    "tools/verify_release.py",
)


def _local_tool_imports(path: Path, root: Path) -> set[str]:
    """Resolve direct in-repo Python tool dependencies without executing code."""
    if path.suffix != ".py":
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
            if node.module == "tools":
                modules.extend(f"tools.{alias.name}" for alias in node.names)
        for module in modules:
            if not module.startswith("tools."):
                continue
            rel = Path(*module.split(".")).with_suffix(".py")
            candidate = root / rel
            if candidate.is_file():
                out.add(rel.as_posix())
    return out


def builder_input_paths(root: Path) -> tuple[str, ...]:
    """Return the seed inputs plus their transitive local Python dependencies."""
    pending = list(BUILDER_INPUTS)
    seen: set[str] = set()
    while pending:
        rel = pending.pop()
        if rel in seen:
            continue
        path = root / rel
        if not path.is_file():
            raise ValueError(f"builder identity input missing: {rel}")
        seen.add(rel)
        pending.extend(sorted(_local_tool_imports(path, root) - seen))
    return tuple(sorted(seen))


def builder_digest(root: Path) -> str:
    h = hashlib.sha256()
    for rel in builder_input_paths(root):
        path = root / rel
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def require_airlock(corpus: Path) -> dict[str, Any]:
    """The sealed receipt must be present and well formed. Its age is not checked:
    liveness is the wire status, and an unchanged release is not an outage."""
    if not (corpus / "index.html").is_file() or not (corpus / "developments").is_dir():
        raise ValueError("sanitized corpus is absent or incomplete")
    receipt_path = corpus / "airlock.json"
    if not receipt_path.is_file():
        raise ValueError("airlock receipt is absent")
    receipt = load(receipt_path)
    if receipt.get("schema") != AIRLOCK_SCHEMA or receipt.get("state") != "READY_FOR_PUBLICATION":
        raise ValueError("airlock receipt schema/state mismatch")
    if not receipt.get("release_id") or not receipt.get("corpus_digest"):
        raise ValueError("airlock receipt lacks content identity")
    return receipt


def count_json_files(path: Path, pattern: str) -> int:
    return sum(1 for _ in path.glob(pattern)) if path.is_dir() else 0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def delta_state(previous: dict[str, Any], receipt: dict[str, Any], current_builder: str) -> tuple[str, str]:
    same_content = (
        previous.get("release_id") == receipt["release_id"]
        and previous.get("corpus_digest") == receipt["corpus_digest"]
    )
    same_builder = previous.get("builder_digest") == current_builder
    same = same_content and same_builder
    state = "NO_PUBLIC_DELTA" if same else "PUBLIC_DELTA_PENDING"
    reason = "UNCHANGED" if same else (
        "CONTENT_AND_BUILDER_CHANGED" if not same_content and not same_builder
        else "CONTENT_CHANGED" if not same_content
        else "BUILDER_CHANGED"
    )
    return state, reason


def translation_counts(status: dict[str, Any], story_count: int) -> dict[str, dict[str, int]]:
    """Per-locale (story, locale) pair counts. A pair counts as complete only when
    every required prose field passes the localization gate; everything else is
    pending or failed, never silently treated as native prose."""
    detailed = status.get("translation") if isinstance(status.get("translation"), dict) else {}
    present = status.get("translation_counts") if isinstance(status.get("translation_counts"), dict) else {}
    out: dict[str, dict[str, int]] = {}
    for locale in ("es-419", "zh-Hans"):
        row = detailed.get(locale)
        if isinstance(row, dict) and all(isinstance(row.get(key), int) for key in ("complete", "pending", "failed")):
            counts = {key: max(0, int(row[key])) for key in ("complete", "pending", "failed")}
            if sum(counts.values()) == story_count:
                states = row.get("state_counts")
                if isinstance(states, dict) and set(states) == {"NATIVE_ARB", "MACHINE_REVIEWED", "PENDING", "FAILED"}:
                    counts["state_counts"] = states
                out[locale] = counts
                continue
        complete = max(0, min(int(present.get(locale) or 0), story_count))
        out[locale] = {"complete": complete, "pending": story_count - complete, "failed": 0}
    return out


def edition_status(
    wire_path: Path,
    now: datetime,
    receipt: dict[str, Any],
    base: dict[str, Any],
    story_count: int,
) -> dict[str, Any]:
    """The newsroom-status v2 fields (contracts/newsroom-status.v2.schema.json)."""
    state, reason, wire = wire_status.classify_path(wire_path, now)
    edition_state, edition_reason = wire_status.edition_fields(state, reason)
    fallback_edition = base.get("last_edition_at") or receipt.get("generated_at") or now
    last_edition_at = wire_status.fmt_utc((wire or {}).get("last_release_change_at") or fallback_edition)
    quiet_since = None
    if edition_state == "QUIET":
        quiet_since = wire_status.fmt_utc((wire or {}).get("last_new_story_at") or last_edition_at)
    alerts: list[str] = []
    if edition_state == "TRANSPORT_DOWN":
        alerts.append("TRANSPORT_DOWN")
    elif edition_reason:
        alerts.append(edition_reason)
    if wire and wire["guard"]["verdict"] == "CARRY_FORWARD":
        alerts.append("CORPUS_CARRY_FORWARD")
    stamp = wire_status.fmt_utc(now)
    return {
        "status_updated_at": stamp,
        "edition_state": edition_state,
        "edition_reason": edition_reason,
        "wire_state": state,
        "wire_run_at": wire["run_at"] if wire else None,
        "edition_date": wire_status.cdmx_date(stamp),
        "last_edition_at": last_edition_at,
        "quiet_since": quiet_since,
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "live_story_count": story_count,
        "translation": translation_counts(base, story_count),
        "drill": wire.get("drill") if wire else None,
        "alerts": alerts,
    }


def github_output(path: Path | None, values: dict[str, Any]) -> None:
    wire_status.emit_outputs(path, values)


def preflight(args: argparse.Namespace) -> int:
    now = wire_status.resolve_now(getattr(args, "now", None))
    receipt = require_airlock(args.corpus)
    previous = load(args.status) if args.status.is_file() else {}
    current_builder = builder_digest(Path.cwd())
    state, reason = delta_state(previous, receipt, current_builder)
    wire_state, wire_reason, wire = wire_status.classify_path(args.wire_status, now)
    edition_state, edition_reason = wire_status.edition_fields(wire_state, wire_reason)
    path = "status" if state == "NO_PUBLIC_DELTA" else "rebuild"
    warning = ""
    if path == "rebuild" and edition_state not in ("FRESH", "QUIET"):
        # P10: a builder or content change always rebuilds; a stale upstream only warns.
        warning = f"REBUILD_WITH_{edition_state}"
        print(f"WARNING {warning} reason={reason} wire={wire_state}", file=sys.stderr)
    print(wire_state)
    print(json.dumps({
        "path": path,
        "state": state,
        "reason": reason,
        "wire_state": wire_state,
        "wire_reason": wire_reason,
        "edition_state": edition_state,
        "wire_run_at": wire["run_at"] if wire else None,
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "builder_digest": current_builder,
        "record_count": receipt.get("record_count"),
        "warning": warning or None,
    }, sort_keys=True))
    github_output(args.github_output, {
        "path": path,
        "state": state,
        "reason": reason,
        "wire_state": wire_state,
        "edition_state": edition_state,
        "edition_reason": edition_reason or "",
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "builder_digest": current_builder,
        "warning": warning,
    })
    # Construction from an accepted corpus is safe during an outage. The
    # independent wire/editorial health checks retain their failing exit codes.
    return 0


def attach_publication_status(fields: dict, site: Path) -> None:
    path = site / "data" / "stories.v2.json"
    payload = load(path) if path.is_file() else {"stories": []}
    live = [story for story in payload["stories"] if story.get("status") == "live"]
    fields["publication_status"] = publication_status(
        corpus_freshness(live, fields["status_updated_at"]), fields, stories=payload["stories"])


def material(doc: dict[str, Any]) -> dict[str, Any]:
    fields = {k: v for k, v in doc.items() if k != "status_updated_at"}
    if isinstance(fields.get("publication_status"), dict):
        fields["publication_status"] = {k: v for k, v in fields["publication_status"].items()
                                        if k not in ("checked_at", "newest_age_hours")}
    return fields


def status(args: argparse.Namespace) -> int:
    """Quiet/delayed path: refresh only the reader-facing status fields. The file
    is rewritten when anything but its timestamp changed, or when the timestamp
    is older than the wire heartbeat interval, so an idle newsroom does not
    redeploy on every hourly cycle."""
    now = wire_status.resolve_now(getattr(args, "now", None))
    receipt = require_airlock(args.corpus)
    if not args.status.is_file():
        raise ValueError("newsroom status is absent; a rebuild must create it first")
    current = load(args.status)
    story_count = int(current.get("story_layer_count") or current.get("live_story_count") or receipt.get("record_count") or 0)
    fields = edition_status(args.wire_status, now, receipt, current, story_count)
    attach_publication_status(fields, args.site)
    updated = dict(current)
    updated.update(fields)
    updated["schema"] = STATUS_SCHEMA
    every = wire_status.load_thresholds()["wire"]["commit_every_h"]
    last = current.get("status_updated_at")
    due = not last or wire_status.hours_between(last, now) >= every
    changed = material({k: current.get(k) for k in fields}) != material(fields)
    write = due or changed
    if write:
        args.status.write_text(json.dumps(updated, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"STATUS {fields['edition_state']} wire={fields['wire_state']} written={'true' if write else 'false'} "
          f"reason={'CHANGED' if changed else 'HEARTBEAT_DUE' if due else 'UNCHANGED'}")
    return 0


def finalize(args: argparse.Namespace) -> int:
    now = wire_status.resolve_now(getattr(args, "now", None))
    receipt = require_airlock(args.corpus)
    previous = load(args.status) if args.status.is_file() else {}
    current_builder = builder_digest(Path.cwd())
    same = (
        previous.get("release_id") == receipt["release_id"]
        and previous.get("corpus_digest") == receipt["corpus_digest"]
        and previous.get("builder_digest") == current_builder
    )

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

    translation_path = args.site / "data" / "i18n" / "translation-status.json"
    if not translation_path.is_file():
        raise ValueError("field-level translation status is absent")
    translation_doc = load(translation_path)
    if translation_doc.get("schema") != "fcmo-translation-status-v2":
        raise ValueError("field-level translation status schema mismatch")
    if translation_doc.get("canonical_story_count") != canonical_count:
        raise ValueError("field-level translation status story count mismatch")
    per_locale: dict[str, dict[str, int]] = {}
    incomplete: set[str] = set()
    for locale in ("es-419", "zh-Hans"):
        row = (translation_doc.get("locales") or {}).get(locale)
        if not isinstance(row, dict):
            raise ValueError(f"{locale}: field-level translation counts are absent")
        counts = {key: row.get(key) for key in ("complete", "pending", "failed")}
        if not all(isinstance(value, int) and value >= 0 for value in counts.values()):
            raise ValueError(f"{locale}: invalid field-level translation counts")
        if sum(counts.values()) != canonical_count:
            raise ValueError(f"{locale}: field-level translation counts do not cover the Story layer")
        states = row.get("state_counts") or {}
        if set(states) != {"NATIVE_ARB", "MACHINE_REVIEWED", "PENDING", "FAILED"} or \
                any(not isinstance(value, int) or value < 0 for value in states.values()) or \
                sum(states.values()) != canonical_count or \
                states["NATIVE_ARB"] + states["MACHINE_REVIEWED"] != counts["complete"] or \
                states["PENDING"] != counts["pending"] or states["FAILED"] != counts["failed"]:
            raise ValueError(f"{locale}: translation state counts disagree with detail")
        pending_ids = set(row.get("pending_ids") or [])
        failed_ids = set((row.get("failed_ids") or {}).keys())
        if len(pending_ids) != counts["pending"] or len(failed_ids) != counts["failed"]:
            raise ValueError(f"{locale}: field-level translation IDs disagree with their counts")
        if not (pending_ids | failed_ids) <= canonical_ids:
            raise ValueError(f"{locale}: field-level translation status contains non-canonical IDs")
        incomplete |= pending_ids | failed_ids
        per_locale[locale] = {**counts, "state_counts": states}
    declared_incomplete = set(translation_doc.get("pending_translation_ids") or [])
    if declared_incomplete != incomplete or translation_doc.get("pending_translation_count") != len(incomplete):
        raise ValueError("field-level translation backlog summary disagrees with the locale detail")
    translation_state = "COMPLETE" if not incomplete else "DEGRADED_TRANSLATION_BACKLOG"
    if translation_doc.get("state") != translation_state:
        raise ValueError("field-level translation state disagrees with its backlog")
    state = "NO_PUBLIC_DELTA_READY" if same else "PUBLIC_DELTA_READY"
    stamp = wire_status.fmt_utc(now)
    status_doc = {
        "schema": STATUS_SCHEMA,
        "state": state,
        "release_id": receipt["release_id"],
        "corpus_digest": receipt["corpus_digest"],
        "builder_digest": current_builder,
        "airlock_generated_at": receipt["generated_at"],
        "airlock_record_count": receipt.get("record_count"),
        "canonical_story_count": canonical_count,
        "story_layer_count": len(stories),
        "stories_sha256": sha256_file(stories_path),
        "media_count": len(media),
        "media_sha256": sha256_file(media_path),
        "translation": per_locale,
        "translation_counts": {locale: counts["complete"] for locale, counts in per_locale.items()},
        "translation_state": translation_state,
        "pending_translation_count": len(incomplete),
        "pending_translation_ids": sorted(incomplete),
        "finalized_at": stamp,
        "ack": "INGESTED_VALIDATED_AND_READY_FOR_DEPLOY",
        "previous_release_id": previous.get("release_id"),
        "deployment_proof": "post-deploy live oracle required",
    }
    status_doc.update(edition_status(args.wire_status, now, receipt, status_doc, len(stories)))
    attach_publication_status(status_doc, args.site)
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status_doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"newsroom ACK {state}: {receipt['release_id']} stories={canonical_count} "
        f"translations={translation_state} pending={len(incomplete)} edition={status_doc['edition_state']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("preflight", "status", "finalize"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--wire-status", type=Path, default=None,
                        help="wire status to classify (default: <corpus>/wire-status.json)")
    parser.add_argument("--release-src", type=Path, default=Path("release-src"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--status", type=Path, default=Path("site/data/newsroom-status.json"))
    parser.add_argument("--now", help="ISO 8601 time (else FCMO_NOW, else the real clock)")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    if args.wire_status is None:
        args.wire_status = args.corpus / "wire-status.json"
    try:
        handler = {"preflight": preflight, "status": status, "finalize": finalize}[args.mode]
        return handler(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"newsroom receipt FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
