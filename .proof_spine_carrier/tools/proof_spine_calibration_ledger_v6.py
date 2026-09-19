#!/usr/bin/env python3
"""Calibration v6: source-enumerated coverage for omission-resistant rates.

v5 proves that the sampling plan existed before the gate and prevents retroactive
case enrollment from entering the accuracy denominator. v6 closes the next loophole:
a preregistered analyst could still omit an inconvenient future gate execution from
the submitted case list entirely.

v6 therefore separates:
- case correctness (v4/v5);
- prospective plan registration (v5); and
- denominator coverage (v6).

A scoreable event must belong to a source-enumerated coverage frame for its exact
plan/project/repository/gate. Every decision-receipt digest enumerated by that frame
must appear in the supplied cases. If even one enumerated receipt is missing, the
whole frame is denominator-incomplete and its cases cannot improve headline rates.

Coverage provenance remains evidence, not authority. The shared ledger does not know
what GitHub Actions, a scheduler, a deploy system, or a laboratory means.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "calibration_v5", HERE / "proof_spine_calibration_ledger_v5.py"
)
v5 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v5
assert SPEC.loader is not None
SPEC.loader.exec_module(v5)

COVERAGE_KIND = "FCMO_PROOF_SPINE_CALIBRATION_COVERAGE"
COVERAGE_AUTHORITY = "NON_NORMATIVE_EVIDENCE"
COVERAGE_SNAPSHOT_KIND = "FCMO_PROOF_SPINE_COVERAGE_SOURCE_SNAPSHOT"
COVERAGE_SNAPSHOT_AUTHORITY = "SOURCE_ENUMERATION_EVIDENCE"
COVERAGE_STATE = "EXECUTED_SOURCE_ENUMERATION"
COVERAGE_RELATION = "INDEPENDENT_OF_SPINE"
DECISION_RECEIPT_KIND = "FCMO_PROOF_SPINE_DECISION_RECEIPT"
ACTION_WITNESS_KIND = "FCMO_PROOF_SPINE_ACTION_WITNESS"
ACTION_WITNESS_AUTHORITY = "OBSERVATIONAL_ONLY"
ALLOWED_COVERAGE_ORIGINS = {
    "PREEXISTING_PROJECT_LOCAL",
    "EXTERNAL_INDEPENDENT",
    "SOURCE_NATIVE_PLATFORM",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise v5.v4.CalibrationError(f"{label} must be non-empty text")
    return value.strip()


def _strings(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        suffix = "a list" if allow_empty else "a non-empty list"
        raise v5.v4.CalibrationError(f"{label} must be {suffix}")
    if any(not isinstance(x, str) or not x.strip() for x in value):
        raise v5.v4.CalibrationError(f"{label} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise v5.v4.CalibrationError(f"{label} must not contain duplicates")
    return value


def _gate_key(plan_id: str, project_id: str, repository: str, gate_id: str) -> tuple[str, str, str, str]:
    return (plan_id, project_id, repository.casefold(), gate_id)


def _registered_gate_keys(plan: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (g["project_id"], g["repository"].casefold(), g["gate_id"])
        for g in plan["registered_gates"]
    }


def validate_decision_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise v5.v4.CalibrationError("decision receipt must be an object")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("kind") != DECISION_RECEIPT_KIND
        or receipt.get("authority") != "EVIDENCE_ONLY"
    ):
        raise v5.v4.CalibrationError("decision receipt schema/kind/authority mismatch")
    if receipt.get("mode") not in {"FCMO_PROOF_SPINE_PROJECT", "FCMO_PROOF_SPINE_FEDERATION"}:
        raise v5.v4.CalibrationError("decision receipt mode is not a universal Proof Spine mode")
    v5.v4.parse_time(receipt.get("evaluated_at"), "decision_receipt.evaluated_at")
    for key in (
        "proofspec_digest",
        "source_evidence_digest",
        "effective_evidence_digest",
        "proof_report_digest",
    ):
        value = _text(receipt.get(key), f"decision_receipt.{key}")
        if not DIGEST_RE.fullmatch(value):
            raise v5.v4.CalibrationError(f"decision_receipt.{key} must be canonical sha256")
    if not isinstance(receipt.get("context"), dict):
        raise v5.v4.CalibrationError("decision_receipt.context must be an object")
    gates = receipt.get("gate_decisions")
    if not isinstance(gates, dict) or not gates:
        raise v5.v4.CalibrationError("decision_receipt.gate_decisions must be a non-empty object")
    for gate_id, decision in gates.items():
        if not isinstance(gate_id, str) or not gate_id.strip() or not isinstance(decision, dict):
            raise v5.v4.CalibrationError("decision receipt gate entries must be named objects")
        if decision.get("state") not in {"OPEN", "CLOSED"}:
            raise v5.v4.CalibrationError("decision receipt gate state must be OPEN or CLOSED")
    return receipt


def index_decision_receipts(receipts: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(receipts, list):
        raise v5.v4.CalibrationError("decision receipts input must be a list")
    out: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        validate_decision_receipt(receipt)
        digest = v5.canonical_digest(receipt)
        if digest in out:
            raise v5.v4.CalibrationError(f"duplicate decision receipt digest: {digest}")
        out[digest] = receipt
    return out


def validate_action_witness(witness: Any) -> dict[str, Any]:
    """Validate byte identity and the minimum semantics needed for consequence claims."""
    if not isinstance(witness, dict):
        raise v5.v4.CalibrationError("action witness must be an object")
    if (
        witness.get("schema_version") != 1
        or witness.get("kind") != ACTION_WITNESS_KIND
        or witness.get("authority") != ACTION_WITNESS_AUTHORITY
    ):
        raise v5.v4.CalibrationError("action witness schema/kind/authority mismatch")

    claimed = _text(witness.get("witness_digest"), "action_witness.witness_digest")
    if not DIGEST_RE.fullmatch(claimed):
        raise v5.v4.CalibrationError("action_witness.witness_digest must be canonical sha256")
    unsigned = {key: value for key, value in witness.items() if key != "witness_digest"}
    if v5.canonical_digest(unsigned) != claimed:
        # Footnote: Action Witness computes its digest before inserting the self-hash.
        # Reconstruct that exact payload here so a copied digest cannot bless mutated
        # chronology, subject binding, or action identity.
        raise v5.v4.CalibrationError("action witness bytes disagree with witness_digest")

    proof_binding = witness.get("proof_binding")
    gate = witness.get("gate")
    action = witness.get("action")
    temporal = witness.get("temporal_relation")
    subject_binding = witness.get("subject_binding")
    if not all(isinstance(value, dict) for value in (proof_binding, gate, action, temporal, subject_binding)):
        raise v5.v4.CalibrationError(
            "action witness requires proof_binding/gate/action/temporal_relation/subject_binding objects"
        )
    if (
        proof_binding.get("mode") != "EXACT_DECISION_RECEIPT"
        or proof_binding.get("exact_executed") is not True
    ):
        raise v5.v4.CalibrationError(
            "calibration consequence evidence requires exact executed decision-receipt binding"
        )
    decision_digest = _text(
        proof_binding.get("decision_receipt_digest"),
        "action_witness.proof_binding.decision_receipt_digest",
    )
    if not DIGEST_RE.fullmatch(decision_digest):
        raise v5.v4.CalibrationError(
            "action witness decision_receipt_digest must be canonical sha256"
        )
    if gate.get("gate_state") not in {"OPEN", "CLOSED"}:
        raise v5.v4.CalibrationError("action witness gate_state must be OPEN or CLOSED")
    if temporal.get("proof_precedes_action") is not True:
        raise v5.v4.CalibrationError(
            "calibration consequence witness must establish proof before action"
        )
    lead = temporal.get("lead_seconds")
    if not isinstance(lead, (int, float)) or isinstance(lead, bool) or lead <= 0:
        raise v5.v4.CalibrationError(
            "action witness lead_seconds must be a positive number"
        )
    if witness.get("classification") not in {
        "PRE_ACTION_CLOSED",
        "PRE_ACTION_CLOSED_CORROBORATED",
        "PRE_ACTION_OPEN",
        "PRE_ACTION_OPEN_CORROBORATED",
    }:
        raise v5.v4.CalibrationError(
            "action witness classification does not establish a pre-action relation"
        )
    if subject_binding.get("state") != "EXACT":
        raise v5.v4.CalibrationError(
            "action witness direct subject binding must be EXACT"
        )
    continuity = subject_binding.get("continuity")
    if not isinstance(continuity, dict) or continuity.get("state") not in {"NOT_REQUIRED", "MATCH"}:
        raise v5.v4.CalibrationError(
            "action witness continuity must be NOT_REQUIRED or MATCH"
        )
    _text(action.get("action_kind"), "action_witness.action.action_kind")
    _text(action.get("selected_time"), "action_witness.action.selected_time")
    v5.v4.parse_time(action["selected_time"], "action_witness.action.selected_time")
    _text(gate.get("gate_id"), "action_witness.gate.gate_id")
    return witness


def index_action_witnesses(
    witnesses: Any,
) -> dict[str, list[dict[str, Any]]]:
    if witnesses is None:
        witnesses = []
    if not isinstance(witnesses, list):
        raise v5.v4.CalibrationError("action_witnesses must be a list")
    by_decision: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    for witness in witnesses:
        validate_action_witness(witness)
        digest = witness["witness_digest"]
        if digest in seen:
            raise v5.v4.CalibrationError(f"duplicate action witness digest: {digest}")
        seen.add(digest)
        decision_digest = witness["proof_binding"]["decision_receipt_digest"]
        by_decision.setdefault(decision_digest, []).append(witness)
    return by_decision


def _consequence_evidence(
    case: dict[str, Any],
    witnesses_by_decision: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    action = case["action"]
    if not action["occurred"]:
        # Footnote: non-occurrence is not prevention proof. The action may simply not
        # have been attempted, may be outside observation, or may have been stopped by
        # another mechanism. Accuracy remains scoreable independently of this surface.
        return {
            "state": "NO_ACTION_OBSERVED",
            "witness_digest": None,
            "verified_lead_time_seconds": None,
            "prevention_evidence": False,
        }

    provenance = case["gate"]["provenance"]
    if provenance["state"] != "EXECUTED":
        return {
            "state": "ACTION_OBSERVED_GATE_NOT_EXECUTED",
            "witness_digest": None,
            "verified_lead_time_seconds": None,
            "prevention_evidence": False,
        }

    decision_digest = provenance["decision_receipt_digest"]
    candidates = witnesses_by_decision.get(decision_digest, [])
    matches: list[dict[str, Any]] = []
    for witness in candidates:
        if witness["gate"]["gate_id"] != case["gate"]["id"]:
            continue
        if witness["gate"]["gate_state"] != case["gate"]["decision"]:
            continue
        if witness["action"]["action_kind"] != action.get("kind"):
            continue
        witness_action_time = v5.v4.parse_time(
            witness["action"]["selected_time"],
            "action_witness.action.selected_time",
        )
        case_action_time = v5.v4.parse_time(
            action.get("observed_at"),
            "action.observed_at",
        )
        if witness_action_time != case_action_time:
            # Footnote: timestamps are semantic instants, not serializer spellings.
            # RFC3339 Z and ISO +00:00 represent the same UTC time and must not break
            # exact consequence binding when every substantive identity already agrees.
            continue
        matches.append(witness)

    if not matches:
        return {
            "state": "ACTION_OBSERVED_WITHOUT_EXACT_WITNESS",
            "witness_digest": None,
            "verified_lead_time_seconds": None,
            "prevention_evidence": False,
        }
    if len(matches) > 1:
        # Footnote: one reported consequential action must resolve to one exact witness.
        # Picking whichever duplicate has the nicest lead time would recreate an
        # analyst-controlled consequence surface even while decision accuracy stays sound.
        raise v5.v4.CalibrationError(
            "reported action matches multiple exact action witnesses"
        )

    witness = matches[0]
    return {
        "state": "ACTION_OBSERVED_EXACT_WITNESS",
        "witness_digest": witness["witness_digest"],
        "verified_lead_time_seconds": witness["temporal_relation"]["lead_seconds"],
        "prevention_evidence": False,
    }


def _decision_receipt_reasons(
    case: dict[str, Any],
    receipts_by_digest: dict[str, dict[str, Any]],
) -> list[str]:
    provenance = case["gate"]["provenance"]
    if provenance["state"] != "EXECUTED":
        return []
    digest = provenance["decision_receipt_digest"]
    receipt = receipts_by_digest.get(digest)
    if receipt is None:
        return ["DECISION_RECEIPT_BYTES_UNAVAILABLE"]

    # Footnote: v4/v5 required digest-shaped provenance, but a syntactically valid
    # hash is not evidence that the referenced decision bytes exist. v6 re-hashes the
    # supplied universal receipt, then cross-checks the exact contract/evidence/time/
    # gate tuple before allowing it anywhere near an accuracy denominator.
    if receipt["mode"] != "FCMO_PROOF_SPINE_PROJECT":
        return ["DECISION_RECEIPT_NOT_PROJECT_SCOPED"]

    context = receipt["context"]
    project = case["project"]
    if context.get("project_id") != project["id"]:
        raise v5.v4.CalibrationError(
            "case project.id disagrees with decision receipt context"
        )
    receipt_repository = context.get("repository")
    if (
        not isinstance(receipt_repository, str)
        or receipt_repository.casefold() != project["repository"].casefold()
    ):
        raise v5.v4.CalibrationError(
            "case project.repository disagrees with decision receipt context"
        )

    missing_subject_keys = sorted(set(case["subject"]) - set(context))
    if missing_subject_keys:
        # Footnote: a partial overlap is not subject identity. A generic field such as
        # gate_scope could otherwise let a real receipt for candidate A calibrate a
        # case about candidate B. The case defines the concrete calibration subject;
        # every one of those keys must be byte-bound into the executed receipt context.
        return ["DECISION_SUBJECT_UNDERBOUND"]
    mismatched_subject_keys = [
        key for key in sorted(case["subject"])
        if case["subject"][key] != context[key]
    ]
    if mismatched_subject_keys:
        raise v5.v4.CalibrationError(
            "case subject disagrees with decision receipt context on keys: "
            + ", ".join(mismatched_subject_keys)
        )

    if receipt["proofspec_digest"] != provenance["proofspec_digest"]:
        raise v5.v4.CalibrationError("case proofspec_digest disagrees with decision receipt bytes")
    if receipt["effective_evidence_digest"] != provenance["effective_evidence_digest"]:
        raise v5.v4.CalibrationError("case effective_evidence_digest disagrees with decision receipt bytes")
    receipt_time = v5.v4.parse_time(
        receipt["evaluated_at"],
        "decision_receipt.evaluated_at",
    )
    case_gate_time = v5.v4.parse_time(
        case["gate"]["observed_at"],
        "gate.observed_at",
    )
    if receipt_time != case_gate_time:
        # Footnote: cryptographic identity belongs to the receipt bytes; semantic
        # cross-object time binding compares parsed instants. Requiring identical
        # timestamp typography would make equivalent Z/+00:00 encodings falsely diverge.
        raise v5.v4.CalibrationError("case gate time disagrees with decision receipt instant")
    decision = receipt["gate_decisions"].get(case["gate"]["id"])
    if decision is None:
        raise v5.v4.CalibrationError("case gate_id is absent from decision receipt")
    if decision.get("state") != case["gate"]["decision"]:
        raise v5.v4.CalibrationError("case gate decision disagrees with decision receipt bytes")
    return []


def validate_coverage(
    frame: Any,
    plans_by_id: dict[str, dict[str, Any]],
    registrations_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(frame, dict):
        raise v5.v4.CalibrationError("coverage frame must be an object")
    if (
        frame.get("schema_version") != 1
        or frame.get("kind") != COVERAGE_KIND
        or frame.get("authority") != COVERAGE_AUTHORITY
    ):
        raise v5.v4.CalibrationError("coverage frame schema/kind/authority mismatch")

    _text(frame.get("coverage_id"), "coverage.coverage_id")
    plan_id = _text(frame.get("plan_id"), "coverage.plan_id")
    plan = plans_by_id.get(plan_id)
    if plan is None:
        raise v5.v4.CalibrationError(f"coverage references unknown plan_id: {plan_id}")

    gate = frame.get("gate")
    if not isinstance(gate, dict):
        raise v5.v4.CalibrationError("coverage.gate must be an object")
    project_id = _text(gate.get("project_id"), "coverage.gate.project_id")
    repository = _text(gate.get("repository"), "coverage.gate.repository")
    gate_id = _text(gate.get("gate_id"), "coverage.gate.gate_id")
    if (project_id, repository.casefold(), gate_id) not in _registered_gate_keys(plan):
        raise v5.v4.CalibrationError("coverage.gate is not registered in the referenced plan")

    observed_from = v5.v4.parse_time(frame.get("observed_from"), "coverage.observed_from")
    observed_through = v5.v4.parse_time(frame.get("observed_through"), "coverage.observed_through")
    if observed_from > observed_through:
        raise v5.v4.CalibrationError("coverage.observed_from must not be after observed_through")

    registered_at = v5.v4.parse_time(
        registrations_by_id[plan_id]["committed_at"], "registration.committed_at"
    )
    if observed_from > registered_at:
        # Footnote: the plan says ALL_QUALIFYING_FUTURE_EVENTS. Allowing its first
        # coverage frame to begin later would recreate post-registration left-truncation:
        # awkward early events could vanish before enumeration even starts.
        raise v5.v4.CalibrationError(
            "coverage must begin no later than the plan Git-registration boundary"
        )

    receipts = _strings(
        frame.get("decision_receipt_digests", []),
        "coverage.decision_receipt_digests",
        allow_empty=True,
    )
    if any(not DIGEST_RE.fullmatch(x) for x in receipts):
        raise v5.v4.CalibrationError(
            "coverage.decision_receipt_digests must contain canonical sha256 digests"
        )

    enumeration = frame.get("enumeration")
    if not isinstance(enumeration, dict):
        raise v5.v4.CalibrationError("coverage.enumeration must be an object")
    if enumeration.get("state") != COVERAGE_STATE:
        raise v5.v4.CalibrationError(
            f"coverage.enumeration.state must equal {COVERAGE_STATE}"
        )
    if enumeration.get("relation_to_spine") != COVERAGE_RELATION:
        raise v5.v4.CalibrationError(
            f"coverage.enumeration.relation_to_spine must equal {COVERAGE_RELATION}"
        )
    if enumeration.get("origin") not in ALLOWED_COVERAGE_ORIGINS:
        raise v5.v4.CalibrationError(
            "coverage.enumeration.origin must be source-native or causally independent"
        )
    _text(enumeration.get("mechanism_id"), "coverage.enumeration.mechanism_id")
    _strings(enumeration.get("evidence_refs"), "coverage.enumeration.evidence_refs")
    _strings(enumeration.get("measurement_roots"), "coverage.enumeration.measurement_roots")
    snapshot_digest = _text(
        enumeration.get("source_snapshot_digest"),
        "coverage.enumeration.source_snapshot_digest",
    )
    if not DIGEST_RE.fullmatch(snapshot_digest):
        raise v5.v4.CalibrationError(
            "coverage.enumeration.source_snapshot_digest must be canonical sha256"
        )

    snapshot = enumeration.get("source_snapshot")
    if not isinstance(snapshot, dict):
        raise v5.v4.CalibrationError(
            "coverage.enumeration.source_snapshot must expose the exact enumerator bytes"
        )
    if (
        snapshot.get("schema_version") != 1
        or snapshot.get("kind") != COVERAGE_SNAPSHOT_KIND
        or snapshot.get("authority") != COVERAGE_SNAPSHOT_AUTHORITY
    ):
        raise v5.v4.CalibrationError(
            "coverage source snapshot schema/kind/authority mismatch"
        )
    if v5.canonical_digest(snapshot) != snapshot_digest:
        # Footnote: a digest without the referenced bytes is not provenance. Rehash
        # the exact source-enumerator snapshot here so an analyst cannot type an
        # impressive-looking sha256 string while silently changing the denominator.
        raise v5.v4.CalibrationError(
            "coverage source_snapshot bytes disagree with source_snapshot_digest"
        )

    snapshot_gate = snapshot.get("gate")
    snapshot_window = snapshot.get("window")
    if not isinstance(snapshot_gate, dict) or not isinstance(snapshot_window, dict):
        raise v5.v4.CalibrationError(
            "coverage source snapshot requires gate and window objects"
        )
    expected_gate = {
        "project_id": project_id,
        "repository": repository,
        "gate_id": gate_id,
    }
    if snapshot_gate != expected_gate:
        raise v5.v4.CalibrationError(
            "coverage source snapshot gate disagrees with frame gate"
        )
    if snapshot_window != {
        "observed_from": frame["observed_from"],
        "observed_through": frame["observed_through"],
    }:
        raise v5.v4.CalibrationError(
            "coverage source snapshot window disagrees with frame window"
        )
    if snapshot.get("mechanism_id") != enumeration.get("mechanism_id"):
        raise v5.v4.CalibrationError(
            "coverage source snapshot mechanism disagrees with enumeration"
        )
    if snapshot.get("origin") != enumeration.get("origin"):
        raise v5.v4.CalibrationError(
            "coverage source snapshot origin disagrees with enumeration"
        )
    if snapshot.get("relation_to_spine") != enumeration.get("relation_to_spine"):
        raise v5.v4.CalibrationError(
            "coverage source snapshot relation disagrees with enumeration"
        )
    if snapshot.get("evidence_refs") != enumeration.get("evidence_refs"):
        raise v5.v4.CalibrationError(
            "coverage source snapshot evidence_refs disagree with enumeration"
        )
    if snapshot.get("measurement_roots") != enumeration.get("measurement_roots"):
        raise v5.v4.CalibrationError(
            "coverage source snapshot measurement_roots disagree with enumeration"
        )
    snapshot_receipts = _strings(
        snapshot.get("decision_receipt_digests", []),
        "coverage.enumeration.source_snapshot.decision_receipt_digests",
        allow_empty=True,
    )
    if snapshot_receipts != receipts:
        raise v5.v4.CalibrationError(
            "coverage source snapshot receipt enumeration disagrees with frame"
        )

    source_event_count = enumeration.get("source_event_count")
    if (
        not isinstance(source_event_count, int)
        or isinstance(source_event_count, bool)
        or source_event_count < 0
    ):
        raise v5.v4.CalibrationError(
            "coverage.enumeration.source_event_count must be a non-negative integer"
        )
    if source_event_count != len(receipts):
        raise v5.v4.CalibrationError(
            "coverage enumeration count must equal decision_receipt_digests length"
        )
    snapshot_count = snapshot.get("source_event_count")
    if (
        not isinstance(snapshot_count, int)
        or isinstance(snapshot_count, bool)
        or snapshot_count != source_event_count
    ):
        raise v5.v4.CalibrationError(
            "coverage source snapshot count disagrees with frame enumeration"
        )
    enumerated_at = v5.v4.parse_time(
        enumeration.get("observed_at"), "coverage.enumeration.observed_at"
    )
    snapshot_time = v5.v4.parse_time(
        snapshot.get("observed_at"),
        "coverage.enumeration.source_snapshot.observed_at",
    )
    if snapshot_time != enumerated_at:
        raise v5.v4.CalibrationError(
            "coverage source snapshot observed_at disagrees with enumeration"
        )
    if enumerated_at < observed_through:
        raise v5.v4.CalibrationError(
            "coverage enumeration cannot predate the window it claims to enumerate"
        )

    return frame


def index_coverage(
    frames: Any,
    plans_by_id: dict[str, dict[str, Any]],
    registrations_by_id: dict[str, dict[str, Any]],
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    if not isinstance(frames, list):
        raise v5.v4.CalibrationError("coverage input must be a list")
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    ids: set[str] = set()
    for frame in frames:
        validate_coverage(frame, plans_by_id, registrations_by_id)
        coverage_id = frame["coverage_id"]
        if coverage_id in ids:
            raise v5.v4.CalibrationError(f"duplicate coverage_id: {coverage_id}")
        ids.add(coverage_id)
        gate = frame["gate"]
        key = _gate_key(
            frame["plan_id"], gate["project_id"], gate["repository"], gate["gate_id"]
        )
        if key in out:
            # Footnote: v0.3h deliberately allows one bounded frame per registered
            # gate. Multiple overlapping/stitched windows need explicit continuity
            # semantics before they can safely affect a denominator.
            raise v5.v4.CalibrationError(
                "multiple coverage frames for one plan/project/repository/gate are not yet supported"
            )
        out[key] = frame
    return out


def _case_key(case: dict[str, Any]) -> tuple[str, str, str, str]:
    return _gate_key(
        case["enrollment"]["plan_id"],
        case["project"]["id"],
        case["project"]["repository"],
        case["gate"]["id"],
    )


def _receipt_digest(case: dict[str, Any]) -> str | None:
    provenance = case.get("gate", {}).get("provenance", {})
    digest = provenance.get("decision_receipt_digest")
    return digest if isinstance(digest, str) and DIGEST_RE.fullmatch(digest) else None


def _inside(frame: dict[str, Any], case: dict[str, Any]) -> bool:
    at = v5.v4.parse_time(case["gate"]["observed_at"], "gate.observed_at")
    start = v5.v4.parse_time(frame["observed_from"], "coverage.observed_from")
    end = v5.v4.parse_time(frame["observed_through"], "coverage.observed_through")
    return start <= at <= end


def coverage_audit(
    frames_by_key: dict[tuple[str, str, str, str], dict[str, Any]],
    cases: list[dict[str, Any]],
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    audit: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for key, frame in frames_by_key.items():
        expected = set(frame["decision_receipt_digests"])
        supplied: set[str] = set()
        for case in cases:
            if _case_key(case) != key or not _inside(frame, case):
                continue
            digest = _receipt_digest(case)
            if digest is not None:
                supplied.add(digest)
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        audit[key] = {
            "coverage_id": frame["coverage_id"],
            "expected_receipt_count": len(expected),
            "supplied_receipt_count": len(supplied),
            "missing_receipt_digests": missing,
            "unexpected_receipt_digests": extra,
            "denominator_complete": not missing and not extra,
        }
    return audit


def _coverage_reasons(
    case: dict[str, Any],
    frames_by_key: dict[tuple[str, str, str, str], dict[str, Any]],
    audit: dict[tuple[str, str, str, str], dict[str, Any]],
) -> list[str]:
    key = _case_key(case)
    frame = frames_by_key.get(key)
    if frame is None:
        return ["NO_SOURCE_ENUMERATED_COVERAGE_FRAME"]
    reasons: list[str] = []
    if not _inside(frame, case):
        reasons.append("GATE_OUTSIDE_COVERAGE_WINDOW")
        return reasons

    digest = _receipt_digest(case)
    if digest is None:
        reasons.append("DECISION_RECEIPT_DIGEST_NOT_COVERABLE")
    elif digest not in set(frame["decision_receipt_digests"]):
        reasons.append("EVENT_ABSENT_FROM_COVERAGE_FRAME")

    frame_audit = audit[key]
    if not frame_audit["denominator_complete"]:
        # Footnote: one omitted source-enumerated event invalidates the denominator
        # for the whole frame. Otherwise an analyst could keep the favorable cases,
        # discard the inconvenient receipt, and still publish a flattering rate.
        reasons.append("INCOMPLETE_SOURCE_ENUMERATED_DENOMINATOR")
    return reasons


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def _withheld_rate(
    numerator: int,
    denominator: int,
    reason: str,
) -> dict[str, Any]:
    # Footnote: keep observed counts inspectable while refusing to manufacture a
    # headline rate from an incompletely enumerated registered gate set.
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": None,
        "withheld_reason": reason,
    }


def calibrate(
    plans: list[dict[str, Any]],
    registrations: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    decision_receipts: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    *,
    action_witnesses: list[dict[str, Any]] | None = None,
    git_root: Path | None = None,
) -> dict[str, Any]:
    plans_by_id = v5.index_plans(plans)
    registrations_by_id = v5.index_registrations(registrations, plans_by_id)
    if set(plans_by_id) != set(registrations_by_id):
        raise v5.v4.CalibrationError("every supplied plan must have exactly one registration")

    frames_by_key = index_coverage(coverage, plans_by_id, registrations_by_id)
    receipts_by_digest = index_decision_receipts(decision_receipts)
    witnesses_by_decision = index_action_witnesses(action_witnesses)
    registered_gate_keys = {
        _gate_key(plan_id, gate["project_id"], gate["repository"], gate["gate_id"])
        for plan_id, plan in plans_by_id.items()
        for gate in plan["registered_gates"]
    }
    missing_registered_coverage = sorted(registered_gate_keys - set(frames_by_key))

    # v5 remains the owner of plan Git verification and every v4 scoreability rule.
    # v6 only adds the denominator-completeness layer; it does not silently fork or
    # weaken prior provenance/adjudication/measurement requirements.
    base = v5.calibrate(
        plans,
        registrations,
        cases,
        git_root=git_root,
    )
    by_id = {event["case_id"]: event for event in base["events"]}
    source = {case["case_id"]: case for case in cases}
    audit = coverage_audit(frames_by_key, cases)

    events: list[dict[str, Any]] = []
    for case in cases:
        event = dict(by_id[case["case_id"]])
        reasons = list(
            dict.fromkeys(
                event["scoreability_reasons"]
                + _decision_receipt_reasons(case, receipts_by_digest)
                + _coverage_reasons(case, frames_by_key, audit)
            )
        )
        if reasons:
            event["classification"] = "UNSCORABLE"
        event["scoreability_reasons"] = reasons
        frame = frames_by_key.get(_case_key(case))
        event["coverage_id"] = frame["coverage_id"] if frame else None
        event["source_enumerated_coverage"] = frame is not None

        # Footnote: accuracy and consequence evidence are deliberately orthogonal.
        # A decision may be calibrated correctly even when no later action witness
        # exists. Conversely, a hand-authored action timestamp must not become a
        # verified lead-time/prevention claim merely because the decision was correct.
        event["reported_lead_time_seconds"] = event.get("lead_time_seconds")
        consequence = _consequence_evidence(case, witnesses_by_decision)
        event["consequence_evidence"] = consequence
        event["lead_time_seconds"] = consequence["verified_lead_time_seconds"]
        events.append(event)

    seen_decision_events: set[tuple[str, str, str, str, str]] = set()
    for case in cases:
        if case["gate"]["provenance"]["state"] != "EXECUTED":
            continue
        event_key = (*_case_key(case), case["gate"]["provenance"]["decision_receipt_digest"])
        if event_key in seen_decision_events:
            # Footnote: source enumeration identifies one executed decision receipt,
            # not an analyst-authored number of "cases". Counting the same receipt
            # twice under different case_id/episode_id values would let favorable
            # evidence inflate accuracy without any additional real decision event.
            raise v5.v4.CalibrationError(
                "duplicate executed decision receipt for the same registered gate"
            )
        seen_decision_events.add(event_key)

    first_by_episode: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for event in events:
        if event["classification"] == "UNSCORABLE":
            continue
        key = (
            event["project"]["repository"].casefold(),
            event["project"]["id"],
            event["gate_id"],
            event["episode_id"],
        )
        current = first_by_episode.get(key)
        if current is None:
            first_by_episode[key] = event
            continue
        a = v5.v4.parse_time(source[event["case_id"]]["gate"]["observed_at"], "gate.observed_at")
        b = v5.v4.parse_time(source[current["case_id"]]["gate"]["observed_at"], "gate.observed_at")
        if a < b:
            first_by_episode[key] = event

    episodes = list(first_by_episode.values())
    labels = {"TRUE_BLOCK", "TRUE_ALLOW", "FALSE_BLOCK", "FALSE_ALLOW"}
    scoreable_events = [
        event for event in events if event["classification"] != "UNSCORABLE"
    ]
    accuracy_event_counts = {
        label: sum(event["classification"] == label for event in scoreable_events)
        for label in sorted(labels)
    }
    episode_counts = {
        label: sum(event["classification"] == label for event in episodes)
        for label in sorted(labels)
    }
    event_counts = {
        label: sum(e["classification"] == label for e in events)
        for label in sorted(labels | {"UNSCORABLE"})
    }
    reason_counts: dict[str, int] = {}
    for event in events:
        for reason in event["scoreability_reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    tb, ta, fb, fa = (
        accuracy_event_counts["TRUE_BLOCK"],
        accuracy_event_counts["TRUE_ALLOW"],
        accuracy_event_counts["FALSE_BLOCK"],
        accuracy_event_counts["FALSE_ALLOW"],
    )
    etb, eta, efb, efa = (
        episode_counts["TRUE_BLOCK"],
        episode_counts["TRUE_ALLOW"],
        episode_counts["FALSE_BLOCK"],
        episode_counts["FALSE_ALLOW"],
    )
    episode_diagnostic_rates = {
        "sensitivity": _rate(etb, etb + efa),
        "specificity": _rate(eta, eta + efb),
        "false_block_rate": _rate(efb, efb + eta),
        "false_allow_rate": _rate(efa, efa + etb),
    }
    observed_micro = {
        "sensitivity": _rate(tb, tb + fa),
        "specificity": _rate(ta, ta + fb),
        "false_block_rate": _rate(fb, fb + ta),
        "false_allow_rate": _rate(fa, fa + tb),
    }
    incomplete_enumeration_frames = sorted(
        key for key, details in audit.items() if not details["denominator_complete"]
    )
    plan_coverage_horizons: dict[str, dict[str, Any]] = {}
    inconsistent_horizon_plans: list[str] = []
    for plan_id, plan in sorted(plans_by_id.items()):
        horizons: dict[str, list[dict[str, str]]] = {}
        for gate in plan["registered_gates"]:
            key = _gate_key(plan_id, gate["project_id"], gate["repository"], gate["gate_id"])
            frame = frames_by_key.get(key)
            if frame is None:
                continue
            through = v5.v4.parse_time(
                frame["observed_through"], "coverage.observed_through"
            ).isoformat()
            horizons.setdefault(through, []).append(
                {
                    "project_id": gate["project_id"],
                    "repository": gate["repository"].casefold(),
                    "gate_id": gate["gate_id"],
                }
            )
        plan_coverage_horizons[plan_id] = {
            "distinct_observed_through": sorted(horizons),
            "gates_by_observed_through": horizons,
            "coherent": len(horizons) <= 1,
        }
        if len(horizons) > 1:
            # Footnote: equal source-enumeration rules are not enough if one gate can
            # be right-truncated earlier than its siblings after an inconvenient event.
            # A shared plan therefore gets one aggregate observation horizon.
            inconsistent_horizon_plans.append(plan_id)

    gate_contract_digests: dict[tuple[str, str, str, str], set[str]] = {}
    for case, event in zip(cases, events):
        if event["classification"] == "UNSCORABLE":
            continue
        key = _case_key(case)
        gate_contract_digests.setdefault(key, set()).add(
            case["gate"]["provenance"]["proofspec_digest"]
        )
    mixed_contract_gates = sorted(
        key for key, digests in gate_contract_digests.items() if len(digests) > 1
    )

    if missing_registered_coverage:
        aggregate_withheld_reason = "MISSING_REGISTERED_COVERAGE_FRAME"
    elif incomplete_enumeration_frames:
        aggregate_withheld_reason = "INCOMPLETE_SOURCE_ENUMERATED_DENOMINATOR"
    elif inconsistent_horizon_plans:
        aggregate_withheld_reason = "INCONSISTENT_PLAN_COVERAGE_HORIZONS"
    elif mixed_contract_gates:
        aggregate_withheld_reason = "MIXED_PROOFSPEC_REVISIONS_WITHIN_REGISTERED_GATE"
    else:
        aggregate_withheld_reason = None

    if aggregate_withheld_reason is None:
        headline_rates = observed_micro
    else:
        headline_rates = {
            "sensitivity": _withheld_rate(tb, tb + fa, aggregate_withheld_reason),
            "specificity": _withheld_rate(ta, ta + fb, aggregate_withheld_reason),
            "false_block_rate": _withheld_rate(fb, fb + ta, aggregate_withheld_reason),
            "false_allow_rate": _withheld_rate(fa, fa + tb, aggregate_withheld_reason),
        }
    # Footnote: a pooled micro-average can hide a weak or entirely unobserved
    # gate behind a high-volume easy gate (a Simpson-style calibration failure).
    # Registered gates are therefore first-class strata. The aggregate rates below
    # remain descriptive of the sampled mixture only; they never substitute for
    # per-gate evidence or prove uniform Proof Spine behavior.
    registered_strata: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for plan_id, plan in plans_by_id.items():
        for gate in plan["registered_gates"]:
            key = _gate_key(
                plan_id,
                gate["project_id"],
                gate["repository"],
                gate["gate_id"],
            )
            registered_strata.setdefault(key, [])

    for event in scoreable_events:
        key = _gate_key(
            event["calibration_plan_id"],
            event["project"]["id"],
            event["project"]["repository"],
            event["gate_id"],
        )
        if key not in registered_strata:
            raise v5.v4.CalibrationError(
                "scored decision event belongs to an unregistered calibration stratum"
            )
        registered_strata[key].append(event)

    gate_strata: list[dict[str, Any]] = []
    represented_strata = 0
    for key, members in sorted(registered_strata.items()):
        stratum_counts = {
            label: sum(event["classification"] == label for event in members)
            for label in sorted(labels)
        }
        stb, sta, sfb, sfa = (
            stratum_counts["TRUE_BLOCK"],
            stratum_counts["TRUE_ALLOW"],
            stratum_counts["FALSE_BLOCK"],
            stratum_counts["FALSE_ALLOW"],
        )
        if members:
            represented_strata += 1
        gate_strata.append(
            {
                "plan_id": key[0],
                "project_id": key[1],
                "repository": key[2],
                "gate_id": key[3],
                "state": "SCORED_DECISION_EVENTS_PRESENT" if members else "NO_SCORED_DECISION_EVENTS",
                "scored_decision_event_count": len(members),
                "decision_event_counts": stratum_counts,
                "proofspec_digests": sorted(gate_contract_digests.get(key, set())),
                "proofspec_revision_count": len(gate_contract_digests.get(key, set())),
                "sensitivity": _rate(stb, stb + sfa),
                "specificity": _rate(sta, sta + sfb),
                "false_block_rate": _rate(sfb, sfb + sta),
                "false_allow_rate": _rate(sfa, sfa + stb),
            }
        )

    if missing_registered_coverage:
        registered_gate_coverage_state = "MISSING_REGISTERED_COVERAGE_FRAMES"
    elif not scoreable_events:
        registered_gate_coverage_state = "NO_SCORED_DECISION_EVENTS"
    elif represented_strata < len(registered_strata):
        registered_gate_coverage_state = "COMPLETE_ENUMERATION_WITH_UNSCORED_REGISTERED_GATES"
    else:
        registered_gate_coverage_state = "ALL_REGISTERED_GATES_REPRESENTED"

    coverage_report = [
        {
            **details,
            "plan_id": key[0],
            "project_id": key[1],
            "repository": key[2],
            "gate_id": key[3],
            "observed_from": frames_by_key[key]["observed_from"],
            "observed_through": frames_by_key[key]["observed_through"],
            "source_snapshot_digest": frames_by_key[key]["enumeration"]["source_snapshot_digest"],
            "source_event_count": frames_by_key[key]["enumeration"]["source_event_count"],
        }
        for key, details in sorted(audit.items())
    ]
    return {
        "schema_version": 6,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_REPORT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "plan_count": len(plans_by_id),
        "coverage_frame_count": len(frames_by_key),
        "decision_receipt_count": len(receipts_by_digest),
        "action_witness_count": sum(len(items) for items in witnesses_by_decision.values()),
        "consequence_evidence_counts": {
            state: sum(
                event["consequence_evidence"]["state"] == state
                for event in events
            )
            for state in sorted(
                {event["consequence_evidence"]["state"] for event in events}
            )
        },
        "complete_coverage_frame_count": sum(
            item["denominator_complete"] for item in audit.values()
        ),
        "case_count": len(events),
        "scored_decision_event_count": len(scoreable_events),
        "scored_episode_count": len(episodes),
        "headline_rate_unit": "UNIQUE_SOURCE_ENUMERATED_DECISION_EVENTS",
        "episode_rate_scope": "DIAGNOSTIC_ONLY_ANALYST_GROUPING_NOT_HEADLINE",
        "registered_gate_count": len(registered_strata),
        "registered_coverage_frame_count": len(set(frames_by_key) & registered_gate_keys),
        "plan_coverage_horizons": plan_coverage_horizons,
        "inconsistent_coverage_horizon_plans": inconsistent_horizon_plans,
        "mixed_proofspec_registered_gates": [
            {
                "plan_id": key[0],
                "project_id": key[1],
                "repository": key[2],
                "gate_id": key[3],
                "proofspec_digests": sorted(gate_contract_digests[key]),
            }
            for key in mixed_contract_gates
        ],
        "missing_registered_coverage_frames": [
            {
                "plan_id": key[0],
                "project_id": key[1],
                "repository": key[2],
                "gate_id": key[3],
            }
            for key in missing_registered_coverage
        ],
        "represented_scored_gate_count": represented_strata,
        "registered_gate_coverage_state": registered_gate_coverage_state,
        "aggregate_rate_scope": "HEADLINE_WITHHELD_UNLESS_REGISTERED_COVERAGE_IS_COMPLETE_AND_COMPARABLE",
        "observed_micro_aggregate": observed_micro,
        "gate_strata": gate_strata,
        "event_counts": event_counts,
        "scoreability_counts": dict(sorted(reason_counts.items())),
        "decision_event_counts": accuracy_event_counts,
        "episode_counts": episode_counts,
        "episode_diagnostic_rates": episode_diagnostic_rates,
        "sensitivity": headline_rates["sensitivity"],
        "specificity": headline_rates["specificity"],
        "false_block_rate": headline_rates["false_block_rate"],
        "false_allow_rate": headline_rates["false_allow_rate"],
        "episodes": episodes,
        "events": events,
        "coverage": coverage_report,
        "plan_digests": base["plan_digests"],
        "plan_verification": base["plan_verification"],
        "claim_boundary": (
            "Headline accuracy denominators require every v5 rule plus an executed, "
            "source-enumerated coverage frame for the exact registered gate. Every "
            "decision-receipt digest enumerated by that frame must be represented in "
            "the submitted cases; one missing or unexpected receipt makes the frame "
            "denominator-incomplete and withholds its rates. The enumerator must also "
            "bind its claimed event set to an exact source-snapshot digest and matching "
            "source event count. Executed cases must additionally provide the exact "
            "universal decision-receipt bytes whose canonical digest, proofspec, effective "
            "evidence, evaluation time, project identity, every key of the concrete "
            "calibration subject, gate id, and gate decision match case provenance. "
            "Coverage provenance is still evidence to audit, not authority or a guarantee "
            "that an external enumerator itself is infallible. Pooled sensitivity/"
            "specificity are micro-aggregates over the observed scoreable decision-event mixture "
            "only. Every preregistered plan/project/repository/gate is reported as its "
            "own stratum, including zero-evidence strata; a pooled rate cannot establish "
            "uniform performance or compensate for an unrepresented registered gate. Every "
            "registered gate must also have an explicit source-enumerated coverage frame, "
            "including an empty frame when the source genuinely observed zero events. "
            "Headline aggregate rates are withheld whenever a registered frame is missing "
            "or any supplied frame has an incomplete enumerated denominator, gates "
            "within one calibration plan use different right-edge observation horizons, "
            "or one registered gate mixes multiple proofspec revisions; "
            "the raw observed micro aggregate remains visible only as a diagnostic. Headline "
            "accuracy uses unique source-enumerated decision events, never analyst-authored "
            "episode grouping. episode_id deduplication is retained only as a secondary "
            "diagnostic because case authors can otherwise merge errors or split successes. "
            "Decision accuracy and consequence evidence are separate surfaces: reported "
            "action occurrence never changes TRUE/FALSE decision classification, while "
            "lead-time/pre-action consequence claims require an exact byte-addressed "
            "Action Witness bound to the same universal decision receipt. No-action "
            "observations are explicitly not treated as prevention evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plans", type=Path)
    parser.add_argument("registrations", type=Path)
    parser.add_argument("coverage", type=Path)
    parser.add_argument("decision_receipts", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--git-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = calibrate(
        json.loads(args.plans.read_text(encoding="utf-8")),
        json.loads(args.registrations.read_text(encoding="utf-8")),
        json.loads(args.coverage.read_text(encoding="utf-8")),
        json.loads(args.decision_receipts.read_text(encoding="utf-8")),
        json.loads(args.cases.read_text(encoding="utf-8")),
        git_root=args.git_root,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
