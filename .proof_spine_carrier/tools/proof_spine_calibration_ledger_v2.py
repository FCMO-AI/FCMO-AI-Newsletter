#!/usr/bin/env python3
"""Calibrate Proof Spine gate decisions against later project-local adjudication.

Decision correctness and action consequence are deliberately separate. A gate can be
right or wrong even when the action never occurs; action timing is additional evidence,
not a prerequisite for scoring the decision itself.
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
RELATIONS = {"INDEPENDENT_OF_SPINE", "DERIVED_FROM_SPINE", "UNKNOWN"}
MECHANISM_ORIGINS = {"PREEXISTING_PROJECT_LOCAL", "EXTERNAL_INDEPENDENT", "SPINE_DERIVED", "UNKNOWN"}
INDEPENDENT_MECHANISM_ORIGINS = {"PREEXISTING_PROJECT_LOCAL", "EXTERNAL_INDEPENDENT"}
CLASSIFICATIONS = {"TRUE_BLOCK", "TRUE_ALLOW", "FALSE_BLOCK", "FALSE_ALLOW", "UNSCORABLE"}


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


def _subject(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise CalibrationError(f"{label} must be a non-empty object")
    # Footnote: a calibration sample must name the represented subject explicitly.
    # Repo/gate/episode labels alone are too coarse to prevent candidate-A evidence from
    # being paired with candidate-B adjudication.
    return value


def validate_case(case: Any) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise CalibrationError("calibration case must be an object")
    if case.get("schema_version") != 2 or case.get("kind") != KIND or case.get("authority") != AUTHORITY:
        raise CalibrationError("calibration case schema/kind/authority mismatch")

    _text(case.get("case_id"), "case_id")
    _text(case.get("episode_id"), "episode_id")
    subject = _subject(case.get("subject"), "subject")

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
        if _subject(action.get("subject"), "action.subject") != subject:
            raise CalibrationError("action.subject must exactly match calibration subject")

    adjudication = case.get("adjudication")
    if not isinstance(adjudication, dict):
        raise CalibrationError("adjudication must be an object")
    if adjudication.get("source_authority") != PROJECT_LOCAL:
        raise CalibrationError("adjudication.source_authority must equal PROJECT_LOCAL")
    if adjudication.get("state") not in ACTUAL:
        raise CalibrationError(f"adjudication.state must be one of {sorted(ACTUAL)}")
    if adjudication.get("relation_to_spine") not in RELATIONS:
        raise CalibrationError(f"adjudication.relation_to_spine must be one of {sorted(RELATIONS)}")
    adjudication_time = parse_time(adjudication.get("observed_at"), "adjudication.observed_at")
    if adjudication_time < gate_time:
        raise CalibrationError("adjudication must not predate the gate observation it scores")
    if _subject(adjudication.get("subject"), "adjudication.subject") != subject:
        raise CalibrationError("adjudication.subject must exactly match calibration subject")
    _text(adjudication.get("basis"), "adjudication.basis")

    mechanism = adjudication.get("mechanism")
    if not isinstance(mechanism, dict):
        raise CalibrationError("adjudication.mechanism must be an object")
    _text(mechanism.get("id"), "adjudication.mechanism.id")
    origin = mechanism.get("origin")
    if origin not in MECHANISM_ORIGINS:
        raise CalibrationError(f"adjudication.mechanism.origin must be one of {sorted(MECHANISM_ORIGINS)}")
    mechanism_time = parse_time(mechanism.get("established_at"), "adjudication.mechanism.established_at")
    mechanism_refs = mechanism.get("evidence_refs", [])
    if not isinstance(mechanism_refs, list) or not mechanism_refs or any(
        not isinstance(x, str) or not x.strip() for x in mechanism_refs
    ):
        raise CalibrationError("adjudication.mechanism.evidence_refs must be a non-empty list of strings")

    # Footnote: PROJECT_LOCAL describes authority provenance, not causal independence.
    # A validator, oracle, or review path created because Spine raised the case is useful
    # repair evidence but cannot independently calibrate the decision that caused it.
    # Pre-existing local mechanisms must be demonstrably established no later than the
    # gate observation; explicitly external independent mechanisms may be later because
    # their independence is reviewed through separate provenance rather than chronology.
    relation = adjudication["relation_to_spine"]
    if relation == "INDEPENDENT_OF_SPINE":
        if origin not in INDEPENDENT_MECHANISM_ORIGINS:
            raise CalibrationError("INDEPENDENT_OF_SPINE requires independent adjudication.mechanism.origin")
        if origin == "PREEXISTING_PROJECT_LOCAL" and mechanism_time > gate_time:
            raise CalibrationError("pre-existing project-local adjudication mechanism must not postdate the gate")
    elif relation == "DERIVED_FROM_SPINE" and origin != "SPINE_DERIVED":
        raise CalibrationError("DERIVED_FROM_SPINE requires adjudication.mechanism.origin=SPINE_DERIVED")

    refs = case.get("evidence_refs", [])
    if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.strip() for x in refs):
        raise CalibrationError("evidence_refs must be a non-empty list of strings")

    # Footnote: episode identity is reviewed input, not inferred from timestamps or SHA.
    # One obligation may persist across source revisions, while each individual case is
    # still bound to its exact subject. This prevents retries from becoming fake samples.
    return case


def classify(case: dict[str, Any]) -> dict[str, Any]:
    validate_case(case)
    gate = case["gate"]
    action = case["action"]
    adjudication = case["adjudication"]
    actual = adjudication["state"]

    # Footnote: decision correctness is scored even when no action happened. Otherwise
    # enforcement could hide every false block merely by preventing the blocked action.
    # Only local adjudication explicitly independent of Spine enters the denominator.
    if actual == "UNKNOWN" or adjudication["relation_to_spine"] != "INDEPENDENT_OF_SPINE":
        label = "UNSCORABLE"
    elif gate["decision"] == "CLOSED" and actual == "SHOULD_BLOCK":
        label = "TRUE_BLOCK"
    elif gate["decision"] == "OPEN" and actual == "SHOULD_ALLOW":
        label = "TRUE_ALLOW"
    elif gate["decision"] == "CLOSED" and actual == "SHOULD_ALLOW":
        label = "FALSE_BLOCK"
    else:
        label = "FALSE_ALLOW"

    lead = None
    if action["occurred"]:
        lead = (parse_time(action["observed_at"], "action.observed_at") -
                parse_time(gate["observed_at"], "gate.observed_at")).total_seconds()

    return {
        "case_id": case["case_id"],
        "episode_id": case["episode_id"],
        "project": case["project"],
        "subject": case["subject"],
        "gate_id": gate["id"],
        "classification": label,
        "lead_time_seconds": lead,
        "gate_decision": gate["decision"],
        "gate_reason": gate["reason"],
        "actual": actual,
        "adjudication_relation": adjudication["relation_to_spine"],
        "adjudication_mechanism_origin": adjudication["mechanism"]["origin"],
        "adjudicated_at": adjudication["observed_at"],
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

    # Footnote: headline calibration uses the earliest independently adjudicated gate
    # observation in each causal episode, not the first later action. This preserves a
    # valid sample when enforcement correctly prevents an action and avoids retry inflation.
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
        a = source_by_case[event["case_id"]]["gate"]["observed_at"]
        b = source_by_case[current["case_id"]]["gate"]["observed_at"]
        if parse_time(a, "gate.observed_at") < parse_time(b, "gate.observed_at"):
            first_by_episode[key] = event

    episodes = list(first_by_episode.values())
    scored_labels = CLASSIFICATIONS - {"UNSCORABLE"}
    counts = {label: sum(1 for e in episodes if e["classification"] == label)
              for label in sorted(scored_labels)}
    event_counts = {label: sum(1 for e in events if e["classification"] == label)
                    for label in sorted(CLASSIFICATIONS)}
    tb, ta = counts["TRUE_BLOCK"], counts["TRUE_ALLOW"]
    fb, fa = counts["FALSE_BLOCK"], counts["FALSE_ALLOW"]

    return {
        "schema_version": 2,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_REPORT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "case_count": len(events),
        "scored_episode_count": len(episodes),
        "observed_action_count": sum(1 for e in events if e["action_occurred"]),
        "event_counts": event_counts,
        "episode_counts": counts,
        "sensitivity": _rate(tb, tb + fa),
        "specificity": _rate(ta, ta + fb),
        "false_block_rate": _rate(fb, fb + ta),
        "false_allow_rate": _rate(fa, fa + tb),
        "episodes": episodes,
        "events": events,
        "claim_boundary": (
            "Decision accuracy is scored over causally deduplicated episodes only when later adjudication is project-local, bound to the same subject, and supported by an adjudication mechanism whose provenance is independently reviewable rather than Spine-derived. Action occurrence is reported separately; zero denominators remain null."
        ),
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
