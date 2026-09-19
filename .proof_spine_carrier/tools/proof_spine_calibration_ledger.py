#!/usr/bin/env python3
"""Calibrate Proof Spine gate observations against later project-local adjudication.

The ledger is observational. It does not execute, approve, cancel, merge, publish,
or block any action. It exists to measure whether prior Spine gate decisions aligned
with later project-local truth without inflating evidence by retry count.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

KIND = "FCMO_PROOF_SPINE_CALIBRATION_CASE"
AUTHORITY = "EVIDENCE_ONLY"
PROJECT_LOCAL = "PROJECT_LOCAL"
DECISIONS = {"OPEN", "CLOSED"}
ACTUAL = {"SHOULD_ALLOW", "SHOULD_BLOCK", "UNKNOWN"}
CLASSIFICATIONS = {"TRUE_POSITIVE", "TRUE_NEGATIVE", "FALSE_BLOCK", "MISS", "UNSCORABLE"}


class CalibrationError(ValueError):
    """Raised when calibration input cannot support an honest score."""


def parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CalibrationError(f"{label} must be a non-empty timezone-aware timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise CalibrationError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CalibrationError(f"{label} must be non-empty text")
    return value.strip()


def validate_case(case: Any) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise CalibrationError("calibration case must be an object")
    if case.get("schema_version") != 1 or case.get("kind") != KIND or case.get("authority") != AUTHORITY:
        raise CalibrationError("calibration case schema/kind/authority mismatch")

    _text(case.get("case_id"), "case_id")
    _text(case.get("episode_id"), "episode_id")

    project = case.get("project")
    if not isinstance(project, dict):
        raise CalibrationError("project must be an object")
    _text(project.get("id"), "project.id")
    repository = _text(project.get("repository"), "project.repository")
    if repository.count("/") != 1:
        raise CalibrationError("project.repository must use owner/repository form")

    gate = case.get("gate")
    if not isinstance(gate, dict):
        raise CalibrationError("gate must be an object")
    _text(gate.get("id"), "gate.id")
    if gate.get("decision") not in DECISIONS:
        raise CalibrationError(f"gate.decision must be one of {sorted(DECISIONS)}")
    _text(gate.get("reason"), "gate.reason")
    gate_time = parse_time(gate.get("observed_at"), "gate.observed_at")

    action = case.get("action")
    if not isinstance(action, dict):
        raise CalibrationError("action must be an object")
    occurred = action.get("occurred")
    if not isinstance(occurred, bool):
        raise CalibrationError("action.occurred must be boolean")
    if occurred:
        _text(action.get("kind"), "action.kind")
        action_time = parse_time(action.get("observed_at"), "action.observed_at")
        if action_time <= gate_time:
            raise CalibrationError("observed action must occur after the gate observation")

    adjudication = case.get("adjudication")
    if not isinstance(adjudication, dict):
        raise CalibrationError("adjudication must be an object")
    if adjudication.get("source_authority") != PROJECT_LOCAL:
        # Footnote: Spine must never score itself by declaring that its own block was
        # correct. The later truth label must come from project-local authority/evidence.
        raise CalibrationError("adjudication.source_authority must equal PROJECT_LOCAL")
    if adjudication.get("state") not in ACTUAL:
        raise CalibrationError(f"adjudication.state must be one of {sorted(ACTUAL)}")
    _text(adjudication.get("basis"), "adjudication.basis")

    refs = case.get("evidence_refs", [])
    if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.strip() for x in refs):
        raise CalibrationError("evidence_refs must be a non-empty list of strings")

    # Footnote: episode identity is reviewed input, not inferred from timestamps or SHA.
    # This lets one unresolved causal defect survive many retries without manufacturing
    # statistically independent wins. Reviewers should split episodes only when the
    # underlying obligation is resolved/replaced and a new causal condition begins.
    return case


def classify(case: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    gate = case["gate"]
    action = case["action"]
    actual = case["adjudication"]["state"]

    if not action["occurred"] or actual == "UNKNOWN":
        label = "UNSCORABLE"
    elif gate["decision"] == "CLOSED" and actual == "SHOULD_BLOCK":
        label = "TRUE_POSITIVE"
    elif gate["decision"] == "OPEN" and actual == "SHOULD_ALLOW":
        label = "TRUE_NEGATIVE"
    elif gate["decision"] == "CLOSED" and actual == "SHOULD_ALLOW":
        label = "FALSE_BLOCK"
    else:
        label = "MISS"

    lead = None
    if action["occurred"]:
        lead = (parse_time(action["observed_at"], "action.observed_at") -
                parse_time(gate["observed_at"], "gate.observed_at")).total_seconds()

    return {
        "case_id": case["case_id"],
        "episode_id": case["episode_id"],
        "project": case["project"],
        "gate_id": gate["id"],
        "classification": label,
        "lead_time_seconds": lead,
        "gate_decision": gate["decision"],
        "gate_reason": gate["reason"],
        "actual": actual,
        "action_occurred": action["occurred"],
    }


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": numerator, "denominator": denominator,
            "rate": (numerator / denominator) if denominator else None}


def calibrate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(cases, list) or not cases:
        raise CalibrationError("calibration input must be a non-empty list")

    events = [classify(case) for case in cases]
    seen_case_ids: set[str] = set()
    for event in events:
        if event["case_id"] in seen_case_ids:
            raise CalibrationError(f"duplicate case_id: {event['case_id']}")
        seen_case_ids.add(event["case_id"])

    # Footnote: headline calibration uses the first scored action in each causal episode.
    # Later retries remain visible as event evidence but cannot inflate sensitivity or
    # specificity merely because an unresolved defect persisted across many schedules.
    first_by_episode: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    source_by_case = {case["case_id"]: case for case in cases}
    for event in events:
        key = (event["project"]["repository"].casefold(), event["project"]["id"],
               event["gate_id"], event["episode_id"])
        if event["classification"] == "UNSCORABLE":
            continue
        current = first_by_episode.get(key)
        if current is None:
            first_by_episode[key] = event
            continue
        a = source_by_case[event["case_id"]]["action"]["observed_at"]
        b = source_by_case[current["case_id"]]["action"]["observed_at"]
        if parse_time(a, "action.observed_at") < parse_time(b, "action.observed_at"):
            first_by_episode[key] = event

    episodes = list(first_by_episode.values())
    counts = {label: sum(1 for e in episodes if e["classification"] == label)
              for label in sorted(CLASSIFICATIONS - {"UNSCORABLE"})}
    tp, tn, fp, fn = counts["TRUE_POSITIVE"], counts["TRUE_NEGATIVE"], counts["FALSE_BLOCK"], counts["MISS"]
    event_counts = {label: sum(1 for e in events if e["classification"] == label)
                    for label in sorted(CLASSIFICATIONS)}
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_REPORT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "case_count": len(events),
        "scored_episode_count": len(episodes),
        "event_counts": event_counts,
        "episode_counts": counts,
        "sensitivity": _rate(tp, tp + fn),
        "specificity": _rate(tn, tn + fp),
        "false_block_rate": _rate(fp, fp + tn),
        "miss_rate": _rate(fn, tp + fn),
        "episodes": episodes,
        "events": events,
        "claim_boundary": "Rates are defined only over causally deduplicated, project-locally adjudicated episodes. A zero denominator remains null; repeated retries of one unresolved defect do not create independent evidence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="JSON array of calibration case objects")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    report = calibrate(cases)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
