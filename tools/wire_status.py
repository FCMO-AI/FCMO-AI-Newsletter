#!/usr/bin/env python3
"""Wire liveness for the FCMO newsroom (contracts/README.md, "Wire status").

The newswire bridge writes ``corpus/wire-status.json`` on every run. That file,
not ``corpus/airlock.json.generated_at``, is the only liveness input. Readers
(refresh preflight, freshness checks, health, the page banner) classify it at
their own ``now`` with the decision table below; the bridge uses the same table
for the ``state`` it writes.

Subcommands::

    classify  read wire-status.json at --now; print the state; exit 0 for FRESH
              and QUIET, 1 for DELAYED:* and TRANSPORT_DOWN (publication freshness)
    write     (bridge) build this run's wire-status.json and decide whether it is
              committed (state change, release change, drill/guard change, or the
              heartbeat interval)
    guard     (bridge) run tools/corpus_guard.py through its CLI contract and say
              whether the verified candidate may be staged
    health    compose health-state.json from the separate signal results

Time source everywhere: ``--now`` > ``FCMO_NOW`` > the real UTC clock. Every
field this tool writes is a code, a public id/date, a count or a UTC timestamp;
no log text, path or credential ever reaches a public file.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from tools import newswire_bridge
except ImportError:  # executed as tools/wire_status.py
    import newswire_bridge  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = ROOT / "contracts" / "thresholds.json"
UTC = timezone.utc
WIRE_SCHEMA = "fcmo-wire-status-v1"
HEALTH_SCHEMA = "fcmo-health-state-v1"
NEWSROOM_FILES = ("wire-status.json", "tombstones.json", "carried.jsonl", "first-published.json")

DEFAULT_THRESHOLDS: dict[str, Any] = {
    "wire": {
        "transport_down_after_h": 30,
        "future_skew_tolerance_min": 15,
        "transport_fail_grace_h": 6,
        "fresh_new_story_max_h": 24,
        "quiet_max_h": 96,
        "commit_every_h": 5,
    },
    "editorial": {"newest_event_max_age_h": 36, "reader_stale_banner_after_h": 36},
    "corpus_guard": {"max_missing_ratio": 0.2},
}

BRIDGE_STATES = (
    "FRESH", "QUIET", "DELAYED:ARB_MAIN_RED", "DELAYED:CHECKPOINT_STALE",
    "DELAYED:STORY_SUPPLY", "DELAYED:TRANSPORT_FAIL", "DELAYED:SNAPSHOT_REFUSED",
)
TRIGGERS = ("schedule", "workflow_dispatch", "workflow_run", "push", "watchdog", "local")
DRILLS = (None, "force_checkpoint", "regressing_snapshot")
WARNINGS = ("ARB_MAIN_RED", "CORPUS_CARRY_FORWARD", "SNAPSHOT_REFUSED", "TRANSPORT_FAIL")
GUARD_VERDICTS = ("OK", "CARRY_FORWARD", "REGRESSION_REFUSED", "NOT_RUN")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*(:[A-Z0-9_]+)?$")
ID_RE = re.compile(r"^FCMO-[0-9A-F]{12}$")
RELEASE_RE = re.compile(r"^newswire-[0-9a-f]{24}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "schema", "run_at", "run_id", "trigger", "drill", "transport", "transport_error",
    "last_transport_ok_at", "source_mode", "arb_main", "arb_main_failures", "checkpoint_at",
    "release_id", "corpus_digest", "record_count", "release_changed", "last_release_change_at",
    "last_new_story_at", "newest_event_at", "guard", "state", "warnings", "previous_state",
    "state_since",
)
PUBLICATION_FIELDS = (
    "publication_authority", "last_authoritative_publication_date",
    "last_authoritative_publication_at", "last_authoritative_edition_id",
    "last_authoritative_publication_status",
)
ALLOWED = frozenset(REQUIRED + PUBLICATION_FIELDS)


# ---------------------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------------------
def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value or "").strip()
        if not raw:
            raise ValueError("empty timestamp")
        if len(raw) == 10:
            raw += "T00:00:00"
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def fmt_utc(value: Any) -> str:
    """Contract form ``YYYY-MM-DDTHH:MM:SSZ``; fractions are truncated, never rounded."""
    return parse_utc(value).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_now(flag: str | None = None) -> datetime:
    if flag:
        return parse_utc(flag)
    if os.environ.get("FCMO_NOW"):
        return parse_utc(os.environ["FCMO_NOW"])
    return utc_now()


def hours_between(earlier: Any, later: Any) -> float:
    return (parse_utc(later) - parse_utc(earlier)).total_seconds() / 3600.0


def cdmx_date(value: Any) -> str:
    """America/Mexico_City calendar date (UTC-6 all year since 2022)."""
    try:
        from zoneinfo import ZoneInfo

        zone: Any = ZoneInfo("America/Mexico_City")
    except Exception:  # pragma: no cover - only without tzdata
        zone = timezone(timedelta(hours=-6))
    return parse_utc(value).astimezone(zone).date().isoformat()


def load_thresholds(path: Path | None = None) -> dict[str, Any]:
    path = path or THRESHOLDS
    merged = json.loads(json.dumps(DEFAULT_THRESHOLDS))
    if path.is_file():
        doc = json.loads(path.read_text(encoding="utf-8"))
        for section, values in doc.items():
            if isinstance(values, dict):
                merged.setdefault(section, {}).update(values)
    return merged


def read_json(path: Path | None) -> Any:
    if path is None or not Path(path).is_file():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, doc: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def emit_outputs(path: Path | None, values: dict[str, Any]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            text = "" if value is None else str(value)
            if "\n" in text:
                raise ValueError(f"output {key} must be one line")
            handle.write(f"{key}={text}\n")


# ---------------------------------------------------------------------------------------
# Validation (the subset of wire-status.schema.json a reader relies on)
# ---------------------------------------------------------------------------------------
def _is_utc(value: Any) -> bool:
    if not isinstance(value, str) or not UTC_RE.match(value):
        return False
    try:
        parse_utc(value)
    except ValueError:
        return False
    return True


def wire_errors(doc: Any) -> list[str]:
    """Structural errors of a wire-status document; empty when it is usable."""
    if not isinstance(doc, dict):
        return ["not an object"]
    errors = [f"missing {key}" for key in REQUIRED if key not in doc]
    errors += [f"unknown {key}" for key in doc if key not in ALLOWED]
    if errors:
        return errors

    def check(ok: bool, message: str) -> None:
        if not ok:
            errors.append(message)

    check(doc["schema"] == WIRE_SCHEMA, "schema")
    for key in ("run_at", "state_since"):
        check(_is_utc(doc[key]), key)
    for key in ("last_transport_ok_at", "checkpoint_at", "last_release_change_at", "last_new_story_at", "newest_event_at"):
        check(doc[key] is None or _is_utc(doc[key]), key)
    check(doc["run_id"] is None or (isinstance(doc["run_id"], str) and re.fullmatch(r"[0-9]{1,20}", doc["run_id"]) is not None), "run_id")
    check(doc["trigger"] in TRIGGERS, "trigger")
    check(doc["drill"] in DRILLS, "drill")
    check(doc["transport"] in ("OK", "FAIL"), "transport")
    check(doc["source_mode"] in ("MAIN", "CHECKPOINT", "NONE"), "source_mode")
    check(doc["arb_main"] in ("GREEN", "RED", "UNKNOWN"), "arb_main")
    failures = doc["arb_main_failures"]
    check(isinstance(failures, list) and len(set(map(str, failures))) == len(failures)
          and all(isinstance(c, str) and CODE_RE.match(c) and len(c) <= 64 for c in failures), "arb_main_failures")
    check(doc["release_id"] is None or (isinstance(doc["release_id"], str) and RELEASE_RE.match(doc["release_id"]) is not None), "release_id")
    check(doc["corpus_digest"] is None or (isinstance(doc["corpus_digest"], str) and DIGEST_RE.match(doc["corpus_digest"]) is not None), "corpus_digest")
    check(doc["record_count"] is None or (isinstance(doc["record_count"], int) and not isinstance(doc["record_count"], bool) and doc["record_count"] >= 0), "record_count")
    check(isinstance(doc["release_changed"], bool), "release_changed")
    check(doc["state"] in BRIDGE_STATES, "state")
    check(doc["previous_state"] is None or doc["previous_state"] in BRIDGE_STATES, "previous_state")
    check(isinstance(doc["warnings"], list) and all(w in WARNINGS for w in doc["warnings"])
          and len(set(doc["warnings"])) == len(doc["warnings"]), "warnings")
    authority = doc.get("publication_authority")
    check(authority in (None, "AUTHORITATIVE", "UNKNOWN"), "publication_authority")
    present_publication = [key for key in PUBLICATION_FIELDS[1:] if key in doc]
    if authority == "AUTHORITATIVE":
        check(len(present_publication) == len(PUBLICATION_FIELDS) - 1, "authoritative publication fields")
        check(
            isinstance(doc.get("last_authoritative_publication_date"), str)
            and re.fullmatch(r"\d{4}-\d{2}-\d{2}", doc["last_authoritative_publication_date"]) is not None,
            "last_authoritative_publication_date",
        )
        check(_is_utc(doc.get("last_authoritative_publication_at")), "last_authoritative_publication_at")
        check(
            isinstance(doc.get("last_authoritative_edition_id"), str)
            and newswire_bridge.EDITION_ID.fullmatch(doc["last_authoritative_edition_id"]) is not None,
            "last_authoritative_edition_id",
        )
        check(doc.get("last_authoritative_publication_status") in ("PUBLISHED", "QUIET"),
              "last_authoritative_publication_status")
    elif authority == "UNKNOWN":
        check(not present_publication, "UNKNOWN publication authority cannot carry publication fields")
    elif present_publication:
        errors.append("publication fields require publication_authority")
    if authority == "AUTHORITATIVE" and _is_utc(doc.get("last_authoritative_publication_at")):
        try:
            actual_date = date.fromisoformat(doc["last_authoritative_publication_date"]).isoformat()
        except (TypeError, ValueError):
            errors.append("last_authoritative_publication_date")
        else:
            check(cdmx_date(doc["last_authoritative_publication_at"]) == actual_date,
                  "authoritative publication CDMX date mismatch")
    guard = doc["guard"]
    if not isinstance(guard, dict) or set(guard) != {"verdict", "missing", "withdrawn", "added", "ratio"}:
        errors.append("guard")
    else:
        check(guard["verdict"] in GUARD_VERDICTS, "guard.verdict")
        for key in ("missing", "withdrawn"):
            check(isinstance(guard[key], list) and all(isinstance(i, str) and ID_RE.match(i) for i in guard[key]), f"guard.{key}")
        check(isinstance(guard["added"], int) and not isinstance(guard["added"], bool) and guard["added"] >= 0, "guard.added")
        check(isinstance(guard["ratio"], (int, float)) and not isinstance(guard["ratio"], bool) and 0 <= guard["ratio"] <= 1, "guard.ratio")
    if errors:
        return errors
    # Conditional rules (schema allOf).
    if doc["transport"] == "OK":
        check(doc["transport_error"] is None, "transport_error must be null when OK")
        check(doc["arb_main"] in ("GREEN", "RED"), "arb_main must be known when OK")
        check(doc["last_transport_ok_at"] is not None, "last_transport_ok_at required when OK")
    else:
        check(isinstance(doc["transport_error"], str) and CODE_RE.match(doc["transport_error"]) is not None
              and len(doc["transport_error"]) <= 64, "transport_error code required when FAIL")
    if doc["source_mode"] in ("MAIN", "CHECKPOINT"):
        check(doc["release_id"] is not None and doc["corpus_digest"] is not None and doc["record_count"] is not None,
              "content identity required for MAIN/CHECKPOINT")
    if doc["source_mode"] == "CHECKPOINT":
        check(doc["checkpoint_at"] is not None, "checkpoint_at required for CHECKPOINT")
    if doc["arb_main"] == "RED":
        check(len(failures) >= 1, "RED needs failure codes")
    else:
        check(len(failures) == 0, "failure codes only when RED")
    return errors


# ---------------------------------------------------------------------------------------
# State machine (README decision table; first match wins)
# ---------------------------------------------------------------------------------------
def classify(wire: Any, now: Any, thresholds: dict[str, Any] | None = None) -> tuple[str, str | None]:
    t = (thresholds or load_thresholds())["wire"]
    now_dt = parse_utc(now)
    if not isinstance(wire, dict):
        return "TRANSPORT_DOWN", "WIRE_STATUS_MISSING"
    if wire_errors(wire):
        return "TRANSPORT_DOWN", "WIRE_STATUS_INVALID"
    run_age_h = hours_between(wire["run_at"], now_dt)
    if run_age_h < -t["future_skew_tolerance_min"] / 60.0:
        return "TRANSPORT_DOWN", "CLOCK_SKEW"
    if run_age_h > t["transport_down_after_h"]:
        return "TRANSPORT_DOWN", "WIRE_STALE"
    if wire["transport"] == "FAIL":
        last_ok = wire.get("last_transport_ok_at")
        if last_ok is None or hours_between(last_ok, now_dt) > t["transport_fail_grace_h"]:
            return "DELAYED:TRANSPORT_FAIL", "TRANSPORT_FAIL"
    new_story = wire.get("last_new_story_at")
    new_age_h = hours_between(new_story, now_dt) if new_story else float("inf")
    # A transported daily receipt is the sole publication authority. Once one
    # exists, do not let generated_at, a changed release, an edition HTML file or
    # last_new_story_at promote the edition state. The existing 24 h threshold is
    # retained as the default pending an operator decision on a daily cutoff.
    if wire.get("publication_authority") == "AUTHORITATIVE":
        publication_age_h = hours_between(wire["last_authoritative_publication_at"], now_dt)
        if publication_age_h < -t["future_skew_tolerance_min"] / 60.0:
            return "TRANSPORT_DOWN", "WIRE_STATUS_INVALID"
        if wire["arb_main"] == "RED":
            return "DELAYED:ARB_MAIN_RED", "ARB_MAIN_RED"
        if wire["source_mode"] != "MAIN":
            return "DELAYED:CHECKPOINT_STALE", "CHECKPOINT_STALE"
        if wire["guard"]["verdict"] == "REGRESSION_REFUSED":
            return "DELAYED:SNAPSHOT_REFUSED", "SNAPSHOT_REFUSED"
        if publication_age_h <= t["fresh_new_story_max_h"]:
            if wire["last_authoritative_publication_status"] == "PUBLISHED":
                return "FRESH", None
            return "QUIET", None
        return "DELAYED:STORY_SUPPLY", "STORY_SUPPLY"
    # Receipt-less releases retain the pre-R1 ordering and thresholds exactly.
    if wire["source_mode"] == "MAIN" and new_age_h <= t["fresh_new_story_max_h"]:
        return "FRESH", None
    if wire["arb_main"] == "RED":
        return "DELAYED:ARB_MAIN_RED", "ARB_MAIN_RED"
    if wire["source_mode"] != "MAIN":
        return "DELAYED:CHECKPOINT_STALE", "CHECKPOINT_STALE"
    if wire["guard"]["verdict"] == "REGRESSION_REFUSED":
        return "DELAYED:SNAPSHOT_REFUSED", "SNAPSHOT_REFUSED"
    if new_age_h <= t["quiet_max_h"]:
        return "QUIET", None
    return "DELAYED:STORY_SUPPLY", "STORY_SUPPLY"


def edition_fields(state: str, reason: str | None) -> tuple[str, str | None]:
    """Map a wire state to newsroom-status ``(edition_state, edition_reason)``."""
    if state.startswith("DELAYED:"):
        return "DELAYED", state.split(":", 1)[1]
    if state == "TRANSPORT_DOWN":
        return "TRANSPORT_DOWN", reason
    return state, None


def freshness_exit(state: str) -> int:
    return 0 if state in ("FRESH", "QUIET") else 1


def load_wire(path: Path | None) -> Any:
    """The wire document, or None when missing; an unreadable file is returned as a
    non-dict sentinel so that classification reports WIRE_STATUS_INVALID."""
    if path is None or not Path(path).is_file():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"__unreadable__": True}


def classify_path(path: Path | None, now: Any, thresholds: dict[str, Any] | None = None) -> tuple[str, str | None, Any]:
    wire = load_wire(path)
    state, reason = classify(wire, now, thresholds)
    return state, reason, wire if isinstance(wire, dict) and not wire_errors(wire) else None


# ---------------------------------------------------------------------------------------
# Bridge writer
# ---------------------------------------------------------------------------------------
def newest_event_at(records: Path | None) -> str | None:
    if records is None or not Path(records).is_file():
        return None
    newest: datetime | None = None
    for line in Path(records).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            value = row.get("event_at") if isinstance(row, dict) else None
            stamp = parse_utc(value) if value else None
        except (ValueError, TypeError, json.JSONDecodeError):
            continue
        if stamp and (newest is None or stamp > newest):
            newest = stamp
    return fmt_utc(newest) if newest else None


def guard_block(report: Any) -> dict[str, Any]:
    """wire-status ``guard`` from a corpus-guard report (or NOT_RUN)."""
    if not isinstance(report, dict) or report.get("verdict") not in ("OK", "CARRY_FORWARD", "REGRESSION_REFUSED"):
        return {"verdict": "NOT_RUN", "missing": [], "withdrawn": [], "added": 0, "ratio": 0.0}
    withdrawn = []
    for item in report.get("withdrawn") or []:
        rid = item.get("id") if isinstance(item, dict) else item
        if isinstance(rid, str) and ID_RE.match(rid):
            withdrawn.append(rid)
    added = report.get("added") or []
    return {
        "verdict": report["verdict"],
        "missing": sorted({i for i in report.get("missing") or [] if isinstance(i, str) and ID_RE.match(i)}),
        "withdrawn": sorted(set(withdrawn)),
        "added": len(added) if isinstance(added, list) else int(added or 0),
        "ratio": float(report.get("ratio") or 0.0),
    }


def build_wire_status(
    previous: dict[str, Any] | None,
    *,
    run_at: Any,
    run_id: str | None,
    trigger: str,
    drill: str | None,
    transport: str,
    transport_error: str | None,
    source_mode: str | None,
    arb_failures: list[str],
    checkpoint_at: str | None,
    airlock: dict[str, Any] | None,
    newest_event: str | None,
    guard: dict[str, Any],
    release_changed: bool,
    publication_receipt: dict[str, Any] | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose this run's wire-status (README "What the bridge writes")."""
    thresholds = thresholds or load_thresholds()
    run_at_s = fmt_utc(run_at)
    prev = previous if isinstance(previous, dict) and not wire_errors(previous) else None
    doc: dict[str, Any] = {
        "schema": WIRE_SCHEMA,
        "run_at": run_at_s,
        "run_id": run_id if run_id and re.fullmatch(r"[0-9]{1,20}", run_id) else None,
        "trigger": trigger if trigger in TRIGGERS else "local",
        "drill": drill or None,
        "transport": transport,
    }
    if transport == "OK":
        failures = sorted({c for c in arb_failures if c})
        bad = [c for c in failures if not CODE_RE.match(c) or len(c) > 64]
        if bad:
            raise ValueError(f"arb failure codes are not public-safe codes: {bad}")
        airlock = airlock or {}
        release_id = airlock.get("release_id")
        prior_change = prev.get("last_release_change_at") if prev else None
        prior_new = prev.get("last_new_story_at") if prev else None
        bootstrap = fmt_utc(airlock["generated_at"]) if airlock.get("generated_at") else run_at_s
        last_change = run_at_s if release_changed else (prior_change or bootstrap)
        if release_changed and guard.get("added", 0) > 0:
            last_new = run_at_s
        else:
            last_new = prior_new or (prior_change or bootstrap)
        if parse_utc(last_new) > parse_utc(last_change):
            last_new = last_change
        doc.update({
            "transport_error": None,
            "last_transport_ok_at": run_at_s,
            "source_mode": source_mode or "NONE",
            "arb_main": "RED" if failures else "GREEN",
            "arb_main_failures": failures,
            "checkpoint_at": fmt_utc(checkpoint_at) if source_mode == "CHECKPOINT" and checkpoint_at else None,
            "release_id": release_id,
            "corpus_digest": airlock.get("corpus_digest"),
            "record_count": airlock.get("record_count"),
            "release_changed": bool(release_changed),
            "last_release_change_at": last_change,
            "last_new_story_at": last_new,
            "newest_event_at": newest_event,
            "guard": guard,
        })
        if publication_receipt is None:
            doc["publication_authority"] = "UNKNOWN"
        else:
            # This is a projection, never an inference. The strict bridge parser
            # validated path/date/time/schema/privacy before this call.
            publication_at = fmt_utc(publication_receipt["published_at"])
            skew_h = -hours_between(publication_at, run_at_s)
            tolerance_h = thresholds["wire"]["future_skew_tolerance_min"] / 60.0
            if skew_h > tolerance_h:
                raise ValueError("authoritative publication receipt is in the future")
            doc.update({
                "publication_authority": "AUTHORITATIVE",
                "last_authoritative_publication_date": publication_receipt["publication_date"],
                "last_authoritative_publication_at": publication_at,
                "last_authoritative_edition_id": publication_receipt["edition_id"],
                "last_authoritative_publication_status": publication_receipt["status"],
            })
        if doc["source_mode"] == "CHECKPOINT" and doc["checkpoint_at"] is None:
            doc["checkpoint_at"] = last_change
    else:
        code = transport_error or "TRANSPORT_FAIL"
        if not CODE_RE.match(code) or len(code) > 64:
            code = "TRANSPORT_FAIL"
        carried = prev or {}
        doc.update({
            "transport_error": code,
            "last_transport_ok_at": carried.get("last_transport_ok_at"),
            "source_mode": carried.get("source_mode", "NONE"),
            "arb_main": carried.get("arb_main", "UNKNOWN"),
            "arb_main_failures": list(carried.get("arb_main_failures", [])),
            "checkpoint_at": carried.get("checkpoint_at"),
            "release_id": carried.get("release_id"),
            "corpus_digest": carried.get("corpus_digest"),
            "record_count": carried.get("record_count"),
            "release_changed": False,
            "last_release_change_at": carried.get("last_release_change_at"),
            "last_new_story_at": carried.get("last_new_story_at"),
            "newest_event_at": carried.get("newest_event_at"),
            "guard": carried.get("guard", guard_block(None)),
        })
        authority = carried.get("publication_authority", "UNKNOWN")
        doc["publication_authority"] = authority
        if authority == "AUTHORITATIVE":
            for key in PUBLICATION_FIELDS[1:]:
                doc[key] = carried[key]
    warnings = []
    if doc["arb_main"] == "RED":
        warnings.append("ARB_MAIN_RED")
    if doc["guard"]["verdict"] == "CARRY_FORWARD":
        warnings.append("CORPUS_CARRY_FORWARD")
    if doc["guard"]["verdict"] == "REGRESSION_REFUSED":
        warnings.append("SNAPSHOT_REFUSED")
    if transport != "OK":
        warnings.append("TRANSPORT_FAIL")
    doc["warnings"] = warnings
    doc["state"] = "DELAYED:TRANSPORT_FAIL"  # placeholder for validation below
    doc["previous_state"] = prev.get("state") if prev else None
    doc["state_since"] = run_at_s
    doc = {key: doc[key] for key in REQUIRED + PUBLICATION_FIELDS if key in doc}
    state, _ = classify(doc, run_at_s, thresholds)
    if state == "TRANSPORT_DOWN":  # the bridge can never observe this; only a reader can
        raise ValueError(f"wire-status would not validate: {wire_errors(doc)}")
    doc["state"] = state
    if prev and prev.get("state") == state:
        doc["state_since"] = prev["state_since"]
    errors = wire_errors(doc)
    if errors:
        raise ValueError(f"wire-status would not validate: {errors}")
    return doc


def commit_decision(previous: Any, new: dict[str, Any], thresholds: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Commit when the state or release changes, or the committed file is getting old."""
    every = (thresholds or load_thresholds())["wire"]["commit_every_h"]
    if not isinstance(previous, dict) or wire_errors(previous):
        return True, "FIRST_WRITE"
    if new["state"] != previous["state"]:
        return True, "STATE_CHANGED"
    if new["release_changed"] or new["release_id"] != previous["release_id"]:
        return True, "RELEASE_CHANGED"
    if new["drill"] != previous["drill"] or new["transport"] != previous["transport"]:
        return True, "RUN_KIND_CHANGED"
    if new["guard"]["verdict"] != previous["guard"]["verdict"] or new["arb_main_failures"] != previous["arb_main_failures"]:
        return True, "UPSTREAM_CHANGED"
    if any(new.get(key) != previous.get(key) for key in PUBLICATION_FIELDS):
        return True, "PUBLICATION_CHANGED"
    if hours_between(previous["run_at"], new["run_at"]) >= every:
        return True, "HEARTBEAT_DUE"
    return False, "UNCHANGED"


# ---------------------------------------------------------------------------------------
# Guard (tools/corpus_guard.py through its CLI contract only)
# ---------------------------------------------------------------------------------------
GUARD_LINE = re.compile(r"^(OK|CARRY_FORWARD|REGRESSION_REFUSED) missing=(\S+) withdrawn=(\S+) added=(\d+) published=(\d+) candidate=(\d+) ratio=([0-9.]+)$")


def guard_script() -> str:
    return os.environ.get("FCMO_CORPUS_GUARD") or str(ROOT / "tools" / "corpus_guard.py")


def release_identity(corpus: Path) -> tuple[str | None, str | None]:
    doc = read_json(Path(corpus) / "airlock.json")
    if not isinstance(doc, dict):
        return None, None
    return doc.get("release_id"), doc.get("corpus_digest")


def regressing_candidate(candidate: Path, target: Path, drop_ratio: float) -> Path:
    """Drill input: a copy of the candidate that drops more than the refusal ratio."""
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(candidate, target, symlinks=False)
    records = target / "data" / "developments.jsonl"
    lines = [line for line in records.read_text(encoding="utf-8").splitlines() if line.strip()]
    keep = max(0, int(len(lines) * (1.0 - drop_ratio)) - 1)
    rng = random.Random(0)
    kept = sorted(rng.sample(range(len(lines)), keep)) if lines else []
    records.write_text("".join(lines[i] + "\n" for i in kept), encoding="utf-8")
    return target


def run_guard(mode: str, published: Path, candidate: Path, report: Path, out: Path | None, now: str) -> tuple[int, dict[str, Any] | None, str]:
    argv = [sys.executable, guard_script(), mode, "--published", str(published), "--candidate", str(candidate),
            "--report", str(report), "--now", now]
    if mode == "apply":
        argv += ["--out", str(out)]
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    first = (proc.stdout or "").splitlines()[0] if (proc.stdout or "").strip() else ""
    match = GUARD_LINE.match(first.strip())
    doc = read_json(report) if report.is_file() else None
    if proc.returncode not in (0, 3) or not match:
        return 2, None, "GUARD_ERROR"
    verdict = match.group(1)
    if (verdict == "REGRESSION_REFUSED") != (proc.returncode == 3):
        return 2, None, "GUARD_ERROR"
    if not isinstance(doc, dict) or doc.get("verdict") != verdict:
        doc = {"verdict": verdict, "ratio": float(match.group(7)),
               "missing": [] if match.group(2) == "-" else match.group(2).split(","),
               "withdrawn": [] if match.group(3) == "-" else match.group(3).split(","),
               "added": int(match.group(4))}
    return proc.returncode, doc, first.strip()


def cmd_guard(args: argparse.Namespace) -> int:
    now = fmt_utc(resolve_now(args.now))
    thresholds = load_thresholds()
    published, candidate = Path(args.published), Path(args.candidate)
    report = Path(args.report)
    out = Path(args.out)
    changed = release_identity(published) != release_identity(candidate) or not (published / "airlock.json").is_file()
    drill = args.drill or None
    work = Path(tempfile.mkdtemp(prefix="fcmo-guard-"))
    try:
        if drill == "regressing_snapshot":
            ratio = float(thresholds["corpus_guard"]["max_missing_ratio"])
            candidate = regressing_candidate(candidate, work / "regressing", min(0.9, ratio + 0.15))
            mode = "check"
        else:
            mode = "apply" if changed else "check"
        if out.exists():
            shutil.rmtree(out)
        code, doc, line = run_guard(mode, published, candidate, report, out, now)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if code == 2 or doc is None:
        print("GUARD_ERROR stage=false", flush=True)
        emit_outputs(args.github_output, {"stage": "false", "verdict": "NOT_RUN", "changed": str(changed).lower()})
        return 2
    verdict = doc["verdict"]
    stage = changed and drill != "regressing_snapshot" and code == 0 and mode == "apply" and out.is_dir()
    write_json(report, doc)
    print(f"{line}", flush=True)
    print(f"stage={'true' if stage else 'false'} changed={'true' if changed else 'false'} drill={drill or '-'}", flush=True)
    for alert in doc.get("alerts") or []:
        if isinstance(alert, str) and CODE_RE.match(alert):
            print(f"ALERT {alert}", file=sys.stderr)
    emit_outputs(args.github_output, {"stage": str(stage).lower(), "verdict": verdict, "changed": str(changed).lower()})
    return 0


# ---------------------------------------------------------------------------------------
# Signals and health state
# ---------------------------------------------------------------------------------------
def signal(status: str, code: str, required: bool, detail: str, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    out = {"status": status, "code": code, "required": required, "since": None, "detail": detail[:300]}
    if metrics:
        out["metrics"] = metrics
    return out


def wire_signals(state: str, reason: str | None, wire: dict[str, Any] | None, now: Any) -> dict[str, dict[str, Any]]:
    """``transport`` and ``upstream`` signals from a classified wire state."""
    age = round(hours_between(wire["run_at"], now), 1) if wire else None
    if state == "TRANSPORT_DOWN":
        transport = signal("RED", "TRANSPORT_DOWN", True, f"Wire status unusable or stale ({reason}).", {"wire_age_h": age})
        upstream = signal("UNKNOWN", "UNKNOWN", True, "Upstream cannot be judged while the transport is down.")
    elif state == "DELAYED:TRANSPORT_FAIL":
        transport = signal("RED", "TRANSPORT_FAIL", True, f"Bridge runs are failing ({wire.get('transport_error') if wire else '-'}).", {"wire_age_h": age})
        upstream = signal("UNKNOWN", "UNKNOWN", True, "Upstream cannot be judged while the transport is failing.")
    else:
        transport = signal("GREEN", "OK", True, f"Last bridge run {age}h ago.", {"wire_age_h": age})
        if state in ("FRESH", "QUIET"):
            upstream = signal("GREEN", state, True, "Upstream main is green." if state == "FRESH" else "Upstream green; no new stories (quiet).")
        else:
            code = state.split(":", 1)[1]
            detail = {
                "ARB_MAIN_RED": "Upstream main is red; serving the last sealed checkpoint.",
                "CHECKPOINT_STALE": "Serving a fallback checkpoint.",
                "SNAPSHOT_REFUSED": "The corpus guard refused a regressing snapshot.",
                "STORY_SUPPLY": "Upstream green but no new stories beyond the quiet limit.",
            }.get(code, code)
            metrics = {"checkpoint_age_h": round(hours_between(wire["checkpoint_at"], now), 1)} if wire and wire.get("checkpoint_at") else None
            upstream = signal("RED", code, True, detail, metrics)
    return {"transport": transport, "upstream": upstream}


def build_health(
    signals: dict[str, dict[str, Any]],
    *,
    checked_at: Any,
    run_id: str | None,
    edition_state: str,
    release_id: str | None,
    previous: Any = None,
    wire: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checked = fmt_utc(checked_at)
    prev_signals = previous.get("signals", {}) if isinstance(previous, dict) else {}
    prev_alerts = {a.get("key"): a for a in previous.get("open_alerts", [])} if isinstance(previous, dict) else {}
    defaults = {
        "serving": signal("UNKNOWN", "UNKNOWN", True, "Serving was not measured."),
        "transport": signal("UNKNOWN", "UNKNOWN", True, "Transport was not measured."),
        "upstream": signal("UNKNOWN", "UNKNOWN", True, "Upstream was not measured."),
        "editorial": signal("UNKNOWN", "UNKNOWN", True, "Editorial freshness was not measured."),
        "translation": signal("UNKNOWN", "UNKNOWN", False, "Translation backlog was not measured."),
        "community": signal("UNKNOWN", "NOT_CONFIGURED", False, "Membership site not configured yet."),
        "watchdog": signal("UNKNOWN", "NOT_CONFIGURED", False, "Host watchdog not installed yet."),
    }
    out: dict[str, dict[str, Any]] = {}
    for key, default in defaults.items():
        sig = dict(signals.get(key) or default)
        sig["required"] = default["required"]
        if sig["status"] == "UNKNOWN" and sig["code"] not in ("UNKNOWN", "NOT_CONFIGURED"):
            sig["code"] = "UNKNOWN"
        prior = prev_signals.get(key) if isinstance(prev_signals, dict) else None
        if isinstance(prior, dict) and prior.get("status") == sig["status"] and prior.get("since"):
            sig["since"] = prior["since"]  # same status as the last check: keep its start
        elif key == "upstream" and wire and wire.get("state") == edition_state and wire.get("state_since"):
            sig["since"] = wire["state_since"]  # the bridge knows when this state began
        else:
            sig["since"] = checked  # first observation of this status
        out[key] = sig
    required = [k for k in ("serving", "transport", "upstream", "editorial")]
    red = [k for k in required if out[k]["status"] != "GREEN"]
    overall = "RED" if red else "GREEN"
    alerts = []
    if red:
        code = edition_state.split(":", 1)[0] if edition_state not in ("FRESH", "QUIET") else out[red[0]]["code"]
        alerts.append({"key": "overall", "code": code})
    for key in required + ["translation", "community", "watchdog"]:
        if out[key]["status"] == "RED":
            alerts.append({"key": key, "code": out[key]["code"]})
    for alert in alerts:
        prior = prev_alerts.get(alert["key"])
        if isinstance(prior, dict) and prior.get("since"):
            alert["since"] = prior["since"]
        else:
            since = out.get(alert["key"], {}).get("since") if alert["key"] != "overall" else None
            alert["since"] = since or checked
    return {
        "schema": HEALTH_SCHEMA,
        "checked_at": checked,
        "run_id": run_id if run_id and re.fullmatch(r"[0-9]{1,20}", run_id) else None,
        "overall": overall,
        "edition_state": edition_state,
        "release_id": release_id,
        "signals": out,
        "open_alerts": alerts,
    }


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def cmd_classify(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    state, reason, wire = classify_path(args.wire_status, now)
    age = f"{hours_between(wire['run_at'], now):.1f}" if wire else "-"
    print(f"{state} reason={reason or '-'} run_at={wire['run_at'] if wire else '-'} age_h={age}")
    emit_outputs(args.github_output, {"wire_state": state, "reason": reason or ""})
    return freshness_exit(state)


def _read_codes(path: Path | None) -> list[str]:
    if not path or not Path(path).is_file():
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_write(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    previous = load_wire(args.previous)
    previous = previous if isinstance(previous, dict) and not wire_errors(previous) else None
    guard = guard_block(read_json(args.guard_report)) if args.guard_report else guard_block(None)
    publication_receipt = None
    if args.transport == "OK":
        publication_root = args.publication_root
        if publication_root is None and args.airlock:
            publication_root = args.airlock.parent
        if publication_root is not None:
            publication_receipt = newswire_bridge.newest_publication_receipt(publication_root)
    doc = build_wire_status(
        previous,
        run_at=now,
        run_id=args.run_id or None,
        trigger=args.trigger,
        drill=args.drill or None,
        transport=args.transport,
        transport_error=args.transport_error or None,
        source_mode=args.source_mode or None,
        arb_failures=_read_codes(args.arb_failures) + [c for c in (args.arb_failure or []) if c],
        checkpoint_at=args.checkpoint_at or None,
        airlock=read_json(args.airlock) if args.airlock else None,
        newest_event=newest_event_at(args.records) if args.records else None,
        guard=guard,
        release_changed=args.release_changed == "true",
        publication_receipt=publication_receipt,
    )
    commit, why = commit_decision(previous, doc)
    write_json(args.out, doc)
    print(f"{doc['state']} commit={'true' if commit else 'false'} reason={why} transport={doc['transport']}")
    emit_outputs(args.github_output, {"commit": str(commit).lower(), "state": doc["state"], "commit_reason": why})
    return 0


def sealed_view(corpus: Path, out: Path) -> Path:
    """Copy of ``corpus`` without the newsroom-owned files (the exact sealed bytes)."""
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(corpus, out, symlinks=False, ignore=lambda folder, names: [
        n for n in names if Path(folder) == Path(corpus) and n in NEWSROOM_FILES])
    return out


def cmd_sealed_view(args: argparse.Namespace) -> int:
    view = sealed_view(Path(args.corpus), Path(args.out))
    print(f"SEALED VIEW {view} excluded={','.join(NEWSROOM_FILES)}")
    return 0


def stage_corpus(release: Path, corpus: Path, guarded: Path | None) -> None:
    """Swap the sealed release into ``corpus`` and keep the newsroom-owned files.

    The sealed release does not carry wire-status.json, tombstones.json or
    first-published.json, so they survive the swap; carried.jsonl comes from the
    corpus guard's output (absent when nothing is carried).
    """
    keep = {name: (corpus / name).read_bytes() for name in NEWSROOM_FILES if name != "carried.jsonl" and (corpus / name).is_file()}
    subprocess.run([sys.executable, str(ROOT / "tools" / "newswire_bridge_partial_locales.py"), "stage", str(release), str(corpus)], check=True)
    for name, data in keep.items():
        (corpus / name).write_bytes(data)
    carried = guarded / "carried.jsonl" if guarded else None
    if carried and carried.is_file():
        shutil.copyfile(carried, corpus / "carried.jsonl")
    elif (corpus / "carried.jsonl").exists():
        (corpus / "carried.jsonl").unlink()


def cmd_stage(args: argparse.Namespace) -> int:
    stage_corpus(Path(args.release), Path(args.corpus), Path(args.guarded) if args.guarded else None)
    kept = [n for n in NEWSROOM_FILES if (Path(args.corpus) / n).is_file()]
    print(f"STAGED corpus newsroom_files={','.join(kept) or '-'}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    now = resolve_now(args.now)
    state, reason, wire = classify_path(args.wire_status, now)
    signals = wire_signals(state, reason, wire, now)
    for item in args.signal or []:
        name, _, path = item.partition("=")
        try:
            doc = read_json(Path(path)) if path else None
        except (OSError, ValueError):
            doc = None
        if isinstance(doc, dict) and doc.get("status") in ("GREEN", "RED", "UNKNOWN") and isinstance(doc.get("code"), str):
            signals[name] = signal(doc["status"], doc["code"], False, str(doc.get("detail") or ""), doc.get("metrics"))
        else:
            signals[name] = signal("UNKNOWN", "UNKNOWN", False, f"No {name} result was reported.")
    health = build_health(
        signals,
        checked_at=now,
        run_id=args.run_id or None,
        edition_state=state,
        release_id=wire.get("release_id") if wire else None,
        previous=read_json(args.previous) if args.previous else None,
        wire=wire,
    )
    write_json(args.out, health)
    red = [k for k, v in health["signals"].items() if v["required"] and v["status"] != "GREEN"]
    print(f"HEALTH {health['overall']} edition={state} red={','.join(red) or '-'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("classify", help="classify wire-status.json at --now")
    p.add_argument("--wire-status", type=Path, default=Path("corpus/wire-status.json"))
    p.add_argument("--now")
    p.add_argument("--github-output", type=Path)
    p.set_defaults(func=cmd_classify)

    p = sub.add_parser("write", help="(bridge) write this run's wire-status.json")
    p.add_argument("--previous", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--now")
    p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    p.add_argument("--trigger", default="local")
    p.add_argument("--drill", default="")
    p.add_argument("--transport", choices=("OK", "FAIL"), required=True)
    p.add_argument("--transport-error", default="")
    p.add_argument("--source-mode", choices=("MAIN", "CHECKPOINT", "NONE", ""), default="")
    p.add_argument("--arb-failures", type=Path, help="file with one failure code per line")
    p.add_argument("--arb-failure", action="append", help="one failure code (repeatable)")
    p.add_argument("--checkpoint-at", default="")
    p.add_argument("--airlock", type=Path)
    p.add_argument(
        "--publication-root",
        type=Path,
        help="verified transported release root; defaults to the parent of --airlock",
    )
    p.add_argument("--records", type=Path)
    p.add_argument("--guard-report", type=Path)
    p.add_argument("--release-changed", choices=("true", "false"), default="false")
    p.add_argument("--github-output", type=Path)
    p.set_defaults(func=cmd_write)

    p = sub.add_parser("guard", help="(bridge) run the corpus guard through its CLI contract")
    p.add_argument("--published", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--drill", default="")
    p.add_argument("--now")
    p.add_argument("--github-output", type=Path)
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("stage", help="(bridge) swap the sealed release into corpus/, keeping newsroom files")
    p.add_argument("--release", type=Path, required=True)
    p.add_argument("--corpus", type=Path, default=Path("corpus"))
    p.add_argument("--guarded", type=Path, help="corpus guard --out directory (carried.jsonl)")
    p.set_defaults(func=cmd_stage)

    p = sub.add_parser("sealed-view", help="(bridge) copy a corpus without the newsroom-owned files")
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=cmd_sealed_view)

    p = sub.add_parser("health", help="compose health-state.json")
    p.add_argument("--wire-status", type=Path, default=Path("corpus/wire-status.json"))
    p.add_argument("--signal", action="append", help="name=path of a signal JSON (serving, editorial, translation)")
    p.add_argument("--previous", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--now")
    p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    p.set_defaults(func=cmd_health)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"wire status FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
