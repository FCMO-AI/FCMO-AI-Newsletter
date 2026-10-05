"""Executable reference oracles for the contracts in contracts/README.md.

These are test oracles, not production code: tools implement the contracts on
their own (tools never import from tests/), and their tests compare results
with these functions over the fixtures and over clock grids. When prose in the
README and an oracle disagree, that is a contract bug to report, not a license
to pick one.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

try:
    from .clock import hours_between, parse_utc
    from .validate import CONTRACTS, validator_for
except ImportError:  # executed as a top-level module
    from clock import hours_between, parse_utc  # type: ignore
    from validate import CONTRACTS, validator_for  # type: ignore

THRESHOLDS_PATH = CONTRACTS / "thresholds.json"
DELAYED_REASONS = ("ARB_MAIN_RED", "CHECKPOINT_STALE", "STORY_SUPPLY", "TRANSPORT_FAIL", "SNAPSHOT_REFUSED")
DOWN_REASONS = ("WIRE_STATUS_MISSING", "WIRE_STATUS_INVALID", "WIRE_STALE", "CLOCK_SKEW")


def load_thresholds(path: Path = THRESHOLDS_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------
# Wire status state machine
# ---------------------------------------------------------------------------------------
def classify_wire(wire: Any, now: str | datetime, thresholds: dict[str, Any] | None = None) -> tuple[str, str | None]:
    """Return ``(state, reason)`` for a wire-status document read at ``now``.

    ``state`` is FRESH, QUIET, TRANSPORT_DOWN or DELAYED:<REASON>. ``reason`` is
    None for FRESH/QUIET, the DELAYED reason, or the TRANSPORT_DOWN cause.
    Rules are evaluated in order; the first match wins (README, "Decision table").
    """
    t = (thresholds or load_thresholds())["wire"]
    now_dt = parse_utc(now)

    # R1 transport down: missing, invalid, stale or from the future.
    if not isinstance(wire, dict):
        return "TRANSPORT_DOWN", "WIRE_STATUS_MISSING"
    if validator_for(CONTRACTS / "wire-status.schema.json").errors(wire):
        return "TRANSPORT_DOWN", "WIRE_STATUS_INVALID"
    run_age_h = hours_between(wire["run_at"], now_dt)
    if run_age_h < -t["future_skew_tolerance_min"] / 60.0:
        return "TRANSPORT_DOWN", "CLOCK_SKEW"
    if run_age_h > t["transport_down_after_h"]:
        return "TRANSPORT_DOWN", "WIRE_STALE"

    # R2 transport failing beyond the grace period.
    if wire["transport"] == "FAIL":
        last_ok = wire.get("last_transport_ok_at")
        if last_ok is None or hours_between(last_ok, now_dt) > t["transport_fail_grace_h"]:
            return "DELAYED:TRANSPORT_FAIL", "TRANSPORT_FAIL"
        # Within grace: judge the carried-forward upstream fields of the last OK run.

    new_story = wire.get("last_new_story_at")
    new_age_h = hours_between(new_story, now_dt) if new_story else float("inf")

    # R3 fresh content from the current upstream main.
    if wire["source_mode"] == "MAIN" and new_age_h <= t["fresh_new_story_max_h"]:
        return "FRESH", None
    # R4 upstream main is red (root cause wins over its symptoms).
    if wire["arb_main"] == "RED":
        return "DELAYED:ARB_MAIN_RED", "ARB_MAIN_RED"
    # R5 serving a fallback although main is not known red (forced, unknown or no source).
    if wire["source_mode"] != "MAIN":
        return "DELAYED:CHECKPOINT_STALE", "CHECKPOINT_STALE"
    # R6 the upstream sent a regressing snapshot that the guard refused.
    if wire["guard"]["verdict"] == "REGRESSION_REFUSED":
        return "DELAYED:SNAPSHOT_REFUSED", "SNAPSHOT_REFUSED"
    # R7 a legitimate quiet period.
    if new_age_h <= t["quiet_max_h"]:
        return "QUIET", None
    # R8 green upstream but nothing new for too long.
    return "DELAYED:STORY_SUPPLY", "STORY_SUPPLY"


def edition_fields(state: str, reason: str | None) -> tuple[str, str | None]:
    """Map a wire state to newsroom-status (edition_state, edition_reason)."""
    if state.startswith("DELAYED:"):
        return "DELAYED", state.split(":", 1)[1]
    if state == "TRANSPORT_DOWN":
        return "TRANSPORT_DOWN", reason
    return state, None


def freshness_exit_code(state: str) -> int:
    """Exit code of publication-freshness style checks: green (0) only for FRESH and QUIET."""
    return 0 if state in {"FRESH", "QUIET"} else 1


# ---------------------------------------------------------------------------------------
# Corpus guard
# ---------------------------------------------------------------------------------------
def read_records(path: Path) -> list[dict[str, Any]]:
    """Records of a corpus directory (data/developments.jsonl) or of a .jsonl file."""
    path = Path(path)
    source = path / "data" / "developments.jsonl" if path.is_dir() else path
    rows: list[dict[str, Any]] = []
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_carried_ids(path: Path) -> set[str]:
    carried = Path(path) / "carried.jsonl" if Path(path).is_dir() else None
    if not carried or not carried.is_file():
        return set()
    return {json.loads(line)["id"] for line in carried.read_text(encoding="utf-8").splitlines() if line.strip()}


def read_release_id(path: Path) -> str | None:
    airlock = Path(path) / "airlock.json" if Path(path).is_dir() else None
    if airlock and airlock.is_file():
        return json.loads(airlock.read_text(encoding="utf-8")).get("release_id")
    return None


def active_tombstones(document: dict[str, Any] | None) -> set[str]:
    if not document:
        return set()
    return {entry["id"] for entry in document.get("tombstones", []) if entry.get("reinstated_at") is None}


def guard_verdict(
    published: Iterable[str],
    candidate: Iterable[str],
    tombstoned: Iterable[str] = (),
    upstream_withdrawn: Iterable[str] = (),
    max_missing_ratio: float = 0.2,
) -> dict[str, Any]:
    """Pure set algebra of ``corpus_guard check`` (README, "corpus_guard CLI").

    ``published`` is the published live id set (records + carried, minus ids that
    were already withdrawn); ``candidate`` every id in the candidate snapshot;
    ``upstream_withdrawn`` the candidate ids whose record status is withdrawn or
    superseded.
    """
    live = set(published)
    cand = set(candidate)
    tomb = set(tombstoned)
    up = set(upstream_withdrawn) & cand
    withdrawn_tomb = live & tomb
    withdrawn_up = (live & up) - withdrawn_tomb
    withdrawn = withdrawn_tomb | withdrawn_up
    missing = sorted((live - cand) - withdrawn)
    ratio = round(len(missing) / len(live), 4) if live else 0.0
    if ratio > max_missing_ratio:
        verdict, code = "REGRESSION_REFUSED", 3
    elif missing:
        verdict, code = "CARRY_FORWARD", 0
    else:
        verdict, code = "OK", 0
    added = sorted(cand - live - tomb - up)
    suppressed = sorted((cand & tomb) - live)
    alerts = {"OK": [], "CARRY_FORWARD": ["CORPUS_CARRY_FORWARD"], "REGRESSION_REFUSED": ["CORPUS_REGRESSION_REFUSED"]}[verdict]
    return {
        "verdict": verdict,
        "exit_code": code,
        "ratio": ratio,
        "missing": missing,
        "carried": missing if verdict == "CARRY_FORWARD" else [],
        "withdrawn": [{"id": i, "source": "tombstone"} for i in sorted(withdrawn_tomb)]
        + [{"id": i, "source": "upstream"} for i in sorted(withdrawn_up)],
        "added": added,
        "suppressed": suppressed,
        "alerts": alerts,
        "live_count": len(live),
        "candidate_count": len(cand),
    }


def guard_corpora(
    published_dir: Path,
    candidate_dir: Path,
    tombstones: dict[str, Any] | None = None,
    max_missing_ratio: float = 0.2,
) -> dict[str, Any]:
    """Apply guard_verdict to two corpus directories (the CLI's inputs)."""
    pub_rows = read_records(published_dir)
    already_withdrawn = {r["id"] for r in pub_rows if r.get("status") in {"withdrawn", "superseded"}}
    live = ({r["id"] for r in pub_rows} | read_carried_ids(published_dir)) - already_withdrawn
    cand_rows = read_records(candidate_dir)
    result = guard_verdict(
        live,
        (r["id"] for r in cand_rows),
        active_tombstones(tombstones),
        (r["id"] for r in cand_rows if r.get("status") in {"withdrawn", "superseded"}),
        max_missing_ratio,
    )
    result["published_release_id"] = read_release_id(published_dir)
    result["candidate_release_id"] = read_release_id(candidate_dir)
    return result


def guard_line(result: dict[str, Any]) -> str:
    """First stdout line of ``corpus_guard check`` for a guard result."""
    def ids(values: list[str]) -> str:
        return ",".join(values) if values else "-"

    return (
        f"{result['verdict']} missing={ids(result['missing'])} "
        f"withdrawn={ids([w['id'] for w in result['withdrawn']])} added={len(result['added'])} "
        f"published={result['live_count']} candidate={result['candidate_count']} ratio={result['ratio']:.4f}"
    )


def guard_report(result: dict[str, Any], checked_at: str, max_missing_ratio: float = 0.2) -> dict[str, Any]:
    """The --report document (contracts/corpus-guard.report.schema.json)."""
    return {
        "schema": "fcmo-corpus-guard-report-v1",
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
