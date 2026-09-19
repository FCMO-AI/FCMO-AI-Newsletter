#!/usr/bin/env python3
"""Build an observational temporal witness between a Proof Spine gate and a later action.

This module does not execute, approve, cancel, or block the observed action. It only
answers whether a reviewed proof observation existed before an externally observed
action and whether both observations are bound to the same declared subject.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CONTRACT_KIND = "FCMO_PROOF_SPINE_ACTION_WITNESS_CONTRACT"
PROOF_KIND = "FCMO_PROOF_SPINE_GATE_OBSERVATION"
ACTION_KIND = "FCMO_PROOF_SPINE_OBSERVED_ACTION"
CORROBORATION_KIND = "FCMO_PROOF_SPINE_SUBJECT_CORROBORATION"
DECISION_RECEIPT_KIND = "FCMO_PROOF_SPINE_DECISION_RECEIPT"
WITNESS_KIND = "FCMO_PROOF_SPINE_ACTION_WITNESS"
AUTHORITY = "OBSERVATIONAL_ONLY"


class WitnessError(ValueError):
    """Raised when a witness input is malformed or tries to weaken reviewed law."""


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise WitnessError(f"{field} must be a non-empty RFC3339 timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise WitnessError(f"{field} is not valid RFC3339/ISO-8601: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WitnessError(f"{field} must include an explicit timezone")
    return parsed.astimezone(timezone.utc)


def _require_kind(payload: Mapping[str, Any], expected: str, name: str) -> None:
    if payload.get("kind") != expected:
        raise WitnessError(f"{name}.kind must be {expected!r}")


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise WitnessError(f"{field} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise WitnessError(f"{field} must not contain duplicates")
    return value


def _subject_value(subject: Mapping[str, Any], key: str) -> tuple[bool, Any]:
    # FOOTNOTE [1]: Subject keys are deliberately flat. Nested/dotted paths make it too easy
    # for adapters to accidentally compare structurally different objects as if they were the
    # same candidate. Projects should normalize identity facts before they reach this layer.
    return (key in subject, subject.get(key))


def _compare_subjects(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    keys: Iterable[str],
) -> dict[str, Any]:
    matched: list[str] = []
    missing: list[str] = []
    mismatched: list[dict[str, Any]] = []
    for key in keys:
        left_has, left_value = _subject_value(left, key)
        right_has, right_value = _subject_value(right, key)
        if not left_has or not right_has:
            missing.append(key)
        elif left_value != right_value:
            mismatched.append({"key": key, "left": left_value, "right": right_value})
        else:
            matched.append(key)
    return {"matched": matched, "missing": missing, "mismatched": mismatched}


def _select_action_boundary(action: Mapping[str, Any], preference: Sequence[str]) -> tuple[str, str, datetime]:
    boundaries = action.get("time_boundaries")
    if not isinstance(boundaries, Mapping):
        raise WitnessError("action.time_boundaries must be an object")
    for name in preference:
        value = boundaries.get(name)
        if value:
            return name, str(value), _parse_time(value, f"action.time_boundaries.{name}")
    raise WitnessError("action has none of the contract-approved time boundaries")


def _normalize_proof_input(
    contract: Mapping[str, Any],
    proof: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize legacy observations and exact universal decision receipts."""

    gate_id = contract.get("gate_id")
    if not isinstance(gate_id, str) or not gate_id:
        raise WitnessError("contract.gate_id must be a non-empty string")

    require_exact = contract.get("require_exact_decision_receipt", False)
    if not isinstance(require_exact, bool):
        raise WitnessError("contract.require_exact_decision_receipt must be boolean")

    kind = proof.get("kind")
    if kind == DECISION_RECEIPT_KIND:
        if proof.get("schema_version") != 1 or proof.get("authority") != "EVIDENCE_ONLY":
            raise WitnessError("decision receipt schema/authority mismatch")
        if proof.get("mode") != "FCMO_PROOF_SPINE_PROJECT":
            raise WitnessError("action witness requires a project-scoped decision receipt")
        context = proof.get("context")
        gates = proof.get("gate_decisions")
        if not isinstance(context, Mapping) or not isinstance(gates, Mapping):
            raise WitnessError("decision receipt requires context and gate_decisions objects")
        gate = gates.get(gate_id)
        if not isinstance(gate, Mapping):
            raise WitnessError("decision receipt does not contain the reviewed gate")
        gate_state = gate.get("state")
        proof_state = gate.get("proof_state")
        if gate_state not in {"OPEN", "CLOSED"}:
            raise WitnessError("decision receipt gate state must be OPEN or CLOSED")
        if proof_state not in {"VALID", "INVALID", "STALE", "UNKNOWN"}:
            raise WitnessError(
                "decision receipt gate proof_state must be VALID, INVALID, STALE, or UNKNOWN"
            )
        evaluated_at = proof.get("evaluated_at")
        _parse_time(evaluated_at, "decision_receipt.evaluated_at")
        return {
            "binding_mode": "EXACT_DECISION_RECEIPT",
            "exact_executed": True,
            "gate_id": gate_id,
            "gate_state": gate_state,
            "proof_state": proof_state,
            "evaluated_at": evaluated_at,
            "subject": context,
            "digest": _canonical_digest(proof),
        }

    if kind != PROOF_KIND:
        raise WitnessError(
            f"proof.kind must be {PROOF_KIND!r} or {DECISION_RECEIPT_KIND!r}"
        )
    if require_exact:
        # FOOTNOTE [2]: legacy gate observations remain useful historical evidence, but
        # a contract that asks for byte-bound execution must not be satisfied by a
        # parallel hand-authored summary of the decision.
        raise WitnessError("reviewed contract requires exact universal decision receipt")
    if proof.get("schema_version") != 1:
        raise WitnessError("proof.schema_version must be 1")
    if proof.get("gate_id") != gate_id:
        raise WitnessError("proof gate_id does not match reviewed witness contract")
    subject = proof.get("subject")
    if not isinstance(subject, Mapping):
        raise WitnessError("proof.subject must be an object")
    evaluated_at = proof.get("evaluated_at")
    _parse_time(evaluated_at, "proof.evaluated_at")
    gate_state = proof.get("gate_state")
    proof_state = proof.get("proof_state")
    if gate_state not in {"OPEN", "CLOSED"}:
        raise WitnessError("proof.gate_state must be OPEN or CLOSED")
    if proof_state not in {"VALID", "INVALID", "STALE", "UNKNOWN"}:
        raise WitnessError("proof.proof_state must be VALID, INVALID, STALE, or UNKNOWN")
    return {
        "binding_mode": "LEGACY_GATE_OBSERVATION",
        "exact_executed": False,
        "gate_id": gate_id,
        "gate_state": gate_state,
        "proof_state": proof_state,
        "evaluated_at": evaluated_at,
        "subject": subject,
        "digest": _canonical_digest(proof),
    }


def evaluate_action_witness(
    contract: Mapping[str, Any],
    proof: Mapping[str, Any],
    action: Mapping[str, Any],
    corroboration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic observational witness.

    The reviewed contract owns identity law. Neither the Proof Spine receipt nor the action
    receipt may decide which fields are sufficient to claim that they concern the same subject.
    """
    _require_kind(contract, CONTRACT_KIND, "contract")
    _require_kind(action, ACTION_KIND, "action")
    if corroboration is not None:
        _require_kind(corroboration, CORROBORATION_KIND, "corroboration")

    if contract.get("schema_version") != 1:
        raise WitnessError("contract.schema_version must be 1")
    if action.get("schema_version") != 1:
        raise WitnessError("action.schema_version must be 1")
    if corroboration is not None and corroboration.get("schema_version") != 1:
        raise WitnessError("corroboration.schema_version must be 1")

    normalized_proof = _normalize_proof_input(contract, proof)
    gate_id = normalized_proof["gate_id"]

    expected_action_kind = contract.get("action_kind")
    if not isinstance(expected_action_kind, str) or not expected_action_kind:
        raise WitnessError("contract.action_kind must be a non-empty string")
    if action.get("action_kind") != expected_action_kind:
        raise WitnessError("action_kind does not match reviewed witness contract")

    direct_keys = _require_string_list(contract.get("direct_subject_keys", []), "contract.direct_subject_keys")
    continuity_keys = _require_string_list(
        contract.get("continuity_subject_keys", []), "contract.continuity_subject_keys"
    )
    if not direct_keys:
        raise WitnessError("contract.direct_subject_keys must contain at least one key")

    preference = _require_string_list(
        contract.get("time_boundary_preference", ["queued_at", "created_at", "started_at"]),
        "contract.time_boundary_preference",
    )
    if not preference:
        raise WitnessError("contract.time_boundary_preference must not be empty")

    proof_subject = normalized_proof["subject"]
    action_subject = action.get("subject")
    if not isinstance(proof_subject, Mapping) or not isinstance(action_subject, Mapping):
        raise WitnessError("proof.subject and action.subject must be objects")

    direct = _compare_subjects(proof_subject, action_subject, direct_keys)
    subject_state = "EXACT"
    if direct["mismatched"]:
        subject_state = "MISMATCH"
    elif direct["missing"]:
        subject_state = "UNDERBOUND"

    continuity: dict[str, Any] = {"required": continuity_keys, "state": "NOT_REQUIRED"}
    corroboration_time: datetime | None = None
    if continuity_keys:
        continuity["state"] = "MISSING"
        if corroboration is not None:
            corroboration_subject = corroboration.get("subject")
            if not isinstance(corroboration_subject, Mapping):
                raise WitnessError("corroboration.subject must be an object")
            continuity_compare = _compare_subjects(proof_subject, corroboration_subject, continuity_keys)
            continuity = {"required": continuity_keys, **continuity_compare}
            if continuity_compare["mismatched"]:
                continuity["state"] = "MISMATCH"
            elif continuity_compare["missing"]:
                continuity["state"] = "UNDERBOUND"
            else:
                continuity["state"] = "MATCH"
            corroboration_time = _parse_time(corroboration.get("observed_at"), "corroboration.observed_at")

    proof_time = _parse_time(normalized_proof["evaluated_at"], "proof.evaluated_at")
    boundary_name, boundary_value, action_time = _select_action_boundary(action, preference)
    proof_precedes_action = proof_time < action_time
    lead_seconds = (action_time - proof_time).total_seconds()

    corroboration_follows_action: bool | None = None
    if corroboration_time is not None:
        corroboration_follows_action = corroboration_time > action_time
        if not corroboration_follows_action and continuity.get("state") == "MATCH":
            continuity["state"] = "TEMPORALLY_INVALID"

    gate_state = normalized_proof["gate_state"]
    proof_state = normalized_proof["proof_state"]

    if subject_state == "MISMATCH" or continuity.get("state") == "MISMATCH":
        classification = "SUBJECT_MISMATCH"
    elif subject_state == "UNDERBOUND" or continuity.get("state") in {"MISSING", "UNDERBOUND"}:
        classification = "SUBJECT_UNDERBOUND"
    elif continuity.get("state") == "TEMPORALLY_INVALID":
        classification = "TEMPORAL_UNCERTAIN"
    elif not proof_precedes_action:
        classification = "POST_ACTION_ONLY"
    elif gate_state == "CLOSED":
        classification = "PRE_ACTION_CLOSED_CORROBORATED" if continuity_keys else "PRE_ACTION_CLOSED"
    else:
        classification = "PRE_ACTION_OPEN_CORROBORATED" if continuity_keys else "PRE_ACTION_OPEN"

    # FOOTNOTE [2]: A successful external action does not rewrite the earlier gate state. The
    # witness records chronology and identity only; it never claims the Proof Spine prevented,
    # caused, authorized, or should retroactively invalidate that external action.
    result = {
        "schema_version": 1,
        "kind": WITNESS_KIND,
        "authority": AUTHORITY,
        "classification": classification,
        "gate": {
            "gate_id": gate_id,
            "gate_state": gate_state,
            "proof_state": proof_state,
            "evaluated_at": normalized_proof["evaluated_at"],
        },
        "proof_binding": {
            "mode": normalized_proof["binding_mode"],
            "exact_executed": normalized_proof["exact_executed"],
            "decision_receipt_digest": (
                normalized_proof["digest"]
                if normalized_proof["binding_mode"] == "EXACT_DECISION_RECEIPT"
                else None
            ),
        },
        "action": {
            "action_kind": expected_action_kind,
            "action_id": action.get("action_id"),
            "selected_time_boundary": boundary_name,
            "selected_time": boundary_value,
            "outcome": action.get("outcome"),
        },
        "temporal_relation": {
            "proof_precedes_action": proof_precedes_action,
            "lead_seconds": lead_seconds,
            "corroboration_follows_action": corroboration_follows_action,
        },
        "subject_binding": {
            "state": subject_state,
            "direct": direct,
            "continuity": continuity,
        },
        "digests": {
            "contract": _canonical_digest(contract),
            "proof_input": normalized_proof["digest"],
            "proof_observation": (
                normalized_proof["digest"]
                if normalized_proof["binding_mode"] == "LEGACY_GATE_OBSERVATION"
                else None
            ),
            "decision_receipt": (
                normalized_proof["digest"]
                if normalized_proof["binding_mode"] == "EXACT_DECISION_RECEIPT"
                else None
            ),
            "action_observation": _canonical_digest(action),
            "corroboration": _canonical_digest(corroboration) if corroboration is not None else None,
        },
        "claim_boundary": (
            "Observational chronology only. This witness grants no execution, deployment, "
            "publication, cancellation, or blocking authority and makes no claim of prevention. "
            "EXACT_DECISION_RECEIPT binds chronology to executed universal decision bytes; "
            "LEGACY_GATE_OBSERVATION remains weaker historical evidence."
        ),
    }
    result["witness_digest"] = _canonical_digest(result)
    return result


def _load(path: str) -> Mapping[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise WitnessError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract")
    parser.add_argument("proof")
    parser.add_argument("action")
    parser.add_argument("--corroboration")
    parser.add_argument("--output")
    args = parser.parse_args()

    witness = evaluate_action_witness(
        _load(args.contract),
        _load(args.proof),
        _load(args.action),
        _load(args.corroboration) if args.corroboration else None,
    )
    rendered = json.dumps(witness, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    # FOOTNOTE [3]: Exit 0 means the witness was evaluated successfully, not that the observed
    # gate was open. This prevents observational tooling from quietly acquiring action authority.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
