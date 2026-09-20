#!/usr/bin/env python3
"""Calibration v7: preregistered, byte-addressed ground-truth adjudication.

v6 makes the sampled decision population omission-resistant. It does not, by itself,
prevent an analyst from choosing a convenient independent adjudicator after seeing the
Proof Spine outcome. v7 closes that remaining outcome-selection surface.

A scoreable v7 event therefore needs all v6 guarantees plus:
- one adjudication contract preregistered for the exact plan/project/repository/gate;
- an exact adjudication receipt whose canonical digest is named by the case;
- byte-for-byte agreement between that receipt and the case's project, gate, subject,
  state, time, basis, and mechanism;
- exact agreement with the preregistered adjudicator implementation identity,
  independence relation, measurement roots, and evidence namespaces.

v7 does not decide project truth. The project-local adjudicator still does that. This
layer only proves that the truth label entering calibration came from the exact
precommitted observation channel rather than an outcome-selected substitute.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "calibration_v6", HERE / "proof_spine_calibration_ledger_v6.py"
)
v6 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = v6
assert SPEC.loader is not None
SPEC.loader.exec_module(v6)

ADJUDICATION_RECEIPT_KIND = "FCMO_PROOF_SPINE_ADJUDICATION_RECEIPT"
ADJUDICATION_RECEIPT_AUTHORITY = "EVIDENCE_ONLY"
ADJUDICATION_SOURCE_AUTHORITY = "PROJECT_LOCAL"
ADJUDICATION_RELATION = "INDEPENDENT_OF_SPINE"
ADJUDICATION_CONTRACT_MODE = "EXACT_PREREGISTERED_ADJUDICATION_RECEIPT"
ALLOWED_ADJUDICATION_ORIGINS = set(v6.v5.v4.INDEPENDENT_MECHANISM_ORIGINS)


def _text(value: Any, label: str) -> str:
    return v6._text(value, label)


def _strings(value: Any, label: str) -> list[str]:
    return v6._strings(value, label)


def _gate_key(
    plan_id: str, project_id: str, repository: str, gate_id: str
) -> tuple[str, str, str, str]:
    return v6._gate_key(plan_id, project_id, repository, gate_id)


def index_adjudication_contracts(
    plans_by_id: dict[str, dict[str, Any]],
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    """Validate one preregistered truth-label channel for every registered gate."""

    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for plan_id, plan in plans_by_id.items():
        contracts = plan.get("adjudication_contracts")
        if not isinstance(contracts, list) or not contracts:
            raise v6.v5.v4.CalibrationError(
                "v7 plan requires a non-empty adjudication_contracts list"
            )

        registered = {
            _gate_key(
                plan_id,
                gate["project_id"],
                gate["repository"],
                gate["gate_id"],
            )
            for gate in plan["registered_gates"]
        }
        seen: set[tuple[str, str, str, str]] = set()

        for i, contract in enumerate(contracts):
            if not isinstance(contract, dict):
                raise v6.v5.v4.CalibrationError(
                    f"adjudication_contracts[{i}] must be an object"
                )
            gate = contract.get("gate")
            if not isinstance(gate, dict):
                raise v6.v5.v4.CalibrationError(
                    f"adjudication_contracts[{i}].gate must be an object"
                )
            key = _gate_key(
                plan_id,
                _text(
                    gate.get("project_id"),
                    f"adjudication_contracts[{i}].gate.project_id",
                ),
                _text(
                    gate.get("repository"),
                    f"adjudication_contracts[{i}].gate.repository",
                ),
                _text(
                    gate.get("gate_id"),
                    f"adjudication_contracts[{i}].gate.gate_id",
                ),
            )
            if key not in registered:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract references an unregistered gate"
                )
            if key in seen:
                raise v6.v5.v4.CalibrationError(
                    "duplicate adjudication contract for one registered gate"
                )
            seen.add(key)

            if contract.get("mode") != ADJUDICATION_CONTRACT_MODE:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract mode mismatch"
                )
            if contract.get("receipt_kind") != ADJUDICATION_RECEIPT_KIND:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract receipt_kind mismatch"
                )
            if contract.get("source_authority") != ADJUDICATION_SOURCE_AUTHORITY:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract source_authority must remain PROJECT_LOCAL"
                )
            if contract.get("relation_to_spine") != ADJUDICATION_RELATION:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract must be independent of Proof Spine"
                )
            required_subject_keys = _strings(
                contract.get("required_subject_keys"),
                "adjudication contract required_subject_keys",
            )
            if len(required_subject_keys) != len(set(required_subject_keys)):
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract required_subject_keys must be unique"
                )

            mechanism = contract.get("mechanism")
            if not isinstance(mechanism, dict):
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract mechanism must be an object"
                )
            _text(mechanism.get("id"), "adjudication contract mechanism.id")
            if mechanism.get("origin") not in ALLOWED_ADJUDICATION_ORIGINS:
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract mechanism origin must be independently admissible"
                )
            contract_digest = _text(
                mechanism.get("contract_digest"),
                "adjudication contract mechanism.contract_digest",
            )
            if not v6.DIGEST_RE.fullmatch(contract_digest):
                raise v6.v5.v4.CalibrationError(
                    "adjudication contract mechanism.contract_digest must be canonical sha256"
                )
            _strings(
                mechanism.get("measurement_roots"),
                "adjudication contract mechanism.measurement_roots",
            )
            prefixes = _strings(
                mechanism.get("evidence_ref_prefixes"),
                "adjudication contract mechanism.evidence_ref_prefixes",
            )
            if any(prefix.strip() != prefix for prefix in prefixes):
                raise v6.v5.v4.CalibrationError(
                    "adjudication evidence_ref_prefixes must not contain surrounding whitespace"
                )

            out[key] = contract

        if seen != registered:
            missing = sorted(registered - seen)
            raise v6.v5.v4.CalibrationError(
                "every registered gate needs exactly one adjudication contract; "
                f"missing={missing!r}"
            )
    return out


def validate_adjudication_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise v6.v5.v4.CalibrationError("adjudication receipt must be an object")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("kind") != ADJUDICATION_RECEIPT_KIND
        or receipt.get("authority") != ADJUDICATION_RECEIPT_AUTHORITY
        or receipt.get("source_authority") != ADJUDICATION_SOURCE_AUTHORITY
        or receipt.get("relation_to_spine") != ADJUDICATION_RELATION
    ):
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt schema/kind/authority/relation mismatch"
        )

    project = receipt.get("project")
    if not isinstance(project, dict):
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt project must be an object"
        )
    _text(project.get("id"), "adjudication receipt project.id")
    repository = _text(
        project.get("repository"), "adjudication receipt project.repository"
    )
    if repository.count("/") != 1:
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt project.repository must use owner/repository form"
        )
    _text(receipt.get("gate_id"), "adjudication receipt gate_id")
    v6.v5.v4._subject(receipt.get("subject"), "adjudication receipt subject")
    if receipt.get("state") not in v6.v5.v4.ACTUAL:
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt state is not a supported project-local label"
        )
    v6.v5.v4.parse_time(
        receipt.get("observed_at"), "adjudication receipt observed_at"
    )
    _text(receipt.get("basis"), "adjudication receipt basis")

    mechanism = receipt.get("mechanism")
    if not isinstance(mechanism, dict):
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt mechanism must be an object"
        )
    _text(mechanism.get("id"), "adjudication receipt mechanism.id")
    if mechanism.get("origin") not in ALLOWED_ADJUDICATION_ORIGINS:
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt mechanism origin is not independently admissible"
        )
    digest = _text(
        mechanism.get("contract_digest"),
        "adjudication receipt mechanism.contract_digest",
    )
    if not v6.DIGEST_RE.fullmatch(digest):
        raise v6.v5.v4.CalibrationError(
            "adjudication receipt mechanism.contract_digest must be canonical sha256"
        )
    v6.v5.v4.parse_time(
        mechanism.get("established_at"),
        "adjudication receipt mechanism.established_at",
    )
    _strings(
        mechanism.get("evidence_refs"),
        "adjudication receipt mechanism.evidence_refs",
    )
    _strings(
        mechanism.get("measurement_roots"),
        "adjudication receipt mechanism.measurement_roots",
    )
    return receipt


def index_adjudication_receipts(
    receipts: Any,
) -> dict[str, dict[str, Any]]:
    if receipts is None:
        receipts = []
    if not isinstance(receipts, list):
        raise v6.v5.v4.CalibrationError(
            "adjudication receipts input must be a list"
        )
    out: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        validate_adjudication_receipt(receipt)
        digest = v6.v5.canonical_digest(receipt)
        if digest in out:
            raise v6.v5.v4.CalibrationError(
                f"duplicate adjudication receipt digest: {digest}"
            )
        out[digest] = receipt
    return out


def _adjudication_contract_reasons(
    case: dict[str, Any],
    contract: dict[str, Any],
    receipts_by_digest: dict[str, dict[str, Any]],
) -> list[str]:
    adjudication = case["adjudication"]
    provenance = adjudication.get("provenance")
    if not isinstance(provenance, dict):
        return ["ADJUDICATION_RECEIPT_PROVENANCE_MISSING"]
    if provenance.get("state") != "EXECUTED":
        return ["ADJUDICATION_RECEIPT_NOT_EXECUTED"]
    if provenance.get("receipt_kind") != ADJUDICATION_RECEIPT_KIND:
        return ["ADJUDICATION_RECEIPT_KIND_MISMATCH"]

    digest = provenance.get("receipt_digest")
    if not isinstance(digest, str) or not v6.DIGEST_RE.fullmatch(digest):
        return ["ADJUDICATION_RECEIPT_DIGEST_INVALID"]
    receipt = receipts_by_digest.get(digest)
    if receipt is None:
        return ["ADJUDICATION_RECEIPT_BYTES_UNAVAILABLE"]

    # Footnote: once exact bytes exist, disagreement between those bytes and the case
    # is corruption, not merely weak evidence. Fail hard instead of letting an analyst
    # relabel an exact receipt while retaining its cryptographic identity.
    project = case["project"]
    receipt_project = receipt["project"]
    if (
        receipt_project.get("id") != project["id"]
        or str(receipt_project.get("repository", "")).casefold()
        != project["repository"].casefold()
    ):
        raise v6.v5.v4.CalibrationError(
            "case project disagrees with exact adjudication receipt"
        )
    if receipt["gate_id"] != case["gate"]["id"]:
        raise v6.v5.v4.CalibrationError(
            "case gate disagrees with exact adjudication receipt"
        )
    if receipt["subject"] != case["subject"]:
        raise v6.v5.v4.CalibrationError(
            "case subject disagrees with exact adjudication receipt"
        )
    if receipt["state"] != adjudication["state"]:
        raise v6.v5.v4.CalibrationError(
            "case adjudication state disagrees with exact adjudication receipt"
        )
    if receipt["basis"] != adjudication["basis"]:
        raise v6.v5.v4.CalibrationError(
            "case adjudication basis disagrees with exact adjudication receipt"
        )
    if (
        v6.v5.v4.parse_time(
            receipt["observed_at"], "adjudication receipt observed_at"
        )
        != v6.v5.v4.parse_time(
            adjudication["observed_at"], "adjudication.observed_at"
        )
    ):
        raise v6.v5.v4.CalibrationError(
            "case adjudication time disagrees with exact adjudication receipt"
        )

    case_mechanism = adjudication["mechanism"]
    receipt_mechanism = receipt["mechanism"]
    for key in ("id", "origin", "contract_digest", "measurement_roots", "evidence_refs"):
        if receipt_mechanism.get(key) != case_mechanism.get(key):
            raise v6.v5.v4.CalibrationError(
                f"case adjudication mechanism {key} disagrees with exact receipt"
            )
    if (
        v6.v5.v4.parse_time(
            receipt_mechanism["established_at"],
            "adjudication receipt mechanism.established_at",
        )
        != v6.v5.v4.parse_time(
            case_mechanism["established_at"],
            "adjudication.mechanism.established_at",
        )
    ):
        raise v6.v5.v4.CalibrationError(
            "case adjudication mechanism established_at disagrees with exact receipt"
        )

    reasons: list[str] = []
    required_subject = set(contract["required_subject_keys"])
    if not required_subject.issubset(case["subject"]):
        reasons.append("ADJUDICATION_SUBJECT_OUTSIDE_PREREGISTERED_CONTRACT")

    if (
        receipt.get("source_authority") != contract["source_authority"]
        or receipt.get("relation_to_spine") != contract["relation_to_spine"]
    ):
        reasons.append("ADJUDICATION_OUTSIDE_PREREGISTERED_CONTRACT")

    contract_mechanism = contract["mechanism"]
    if (
        receipt_mechanism.get("id") != contract_mechanism["id"]
        or receipt_mechanism.get("origin") != contract_mechanism["origin"]
        or receipt_mechanism.get("contract_digest")
        != contract_mechanism["contract_digest"]
        or receipt_mechanism.get("measurement_roots")
        != contract_mechanism["measurement_roots"]
    ):
        reasons.append("ADJUDICATION_OUTSIDE_PREREGISTERED_CONTRACT")

    prefixes = contract_mechanism["evidence_ref_prefixes"]
    if any(
        not any(ref.startswith(prefix) for prefix in prefixes)
        for ref in receipt_mechanism["evidence_refs"]
    ):
        reasons.append("ADJUDICATION_OUTSIDE_PREREGISTERED_EVIDENCE_NAMESPACE")

    return list(dict.fromkeys(reasons))


def calibrate(
    plans: list[dict[str, Any]],
    registrations: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    decision_receipts: list[dict[str, Any]],
    adjudication_receipts: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    *,
    action_witnesses: list[dict[str, Any]] | None = None,
    git_root: Path | None = None,
) -> dict[str, Any]:
    plans_by_id = v6.v5.index_plans(plans)
    adjudication_contracts = index_adjudication_contracts(plans_by_id)
    receipts_by_digest = index_adjudication_receipts(adjudication_receipts)

    transformed: list[dict[str, Any]] = []
    exactness_reasons: dict[str, list[str]] = {}
    exact_receipt_digests: dict[str, str | None] = {}
    for case in cases:
        key = _gate_key(
            case["enrollment"]["plan_id"],
            case["project"]["id"],
            case["project"]["repository"],
            case["gate"]["id"],
        )
        contract = adjudication_contracts.get(key)
        if contract is None:
            raise v6.v5.v4.CalibrationError(
                "case gate lacks a preregistered adjudication contract"
            )
        reasons = _adjudication_contract_reasons(
            case, contract, receipts_by_digest
        )
        exactness_reasons[case["case_id"]] = reasons
        provenance = case.get("adjudication", {}).get("provenance")
        exact_receipt_digests[case["case_id"]] = (
            provenance.get("receipt_digest")
            if isinstance(provenance, dict)
            and isinstance(provenance.get("receipt_digest"), str)
            else None
        )

        candidate = copy.deepcopy(case)
        if reasons:
            # Footnote: v6 already knows how to propagate an unscoreable truth label
            # through denominator completeness. Demote only the working copy to UNKNOWN
            # so v6 withholds the frame; preserve the original case untouched for audit.
            candidate["adjudication"]["state"] = "UNKNOWN"
            candidate["adjudication"]["relation_to_spine"] = "UNKNOWN"
        transformed.append(candidate)

    base = v6.calibrate(
        plans,
        registrations,
        coverage,
        decision_receipts,
        transformed,
        action_witnesses=action_witnesses,
        git_root=git_root,
    )

    reason_counts: dict[str, int] = {}
    source_cases = {case["case_id"]: case for case in cases}
    for event in base["events"]:
        case_id = event["case_id"]
        reasons = exactness_reasons.get(case_id, [])
        if reasons:
            event["scoreability_reasons"] = list(
                dict.fromkeys(event["scoreability_reasons"] + reasons)
            )
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        event["adjudication_receipt_digest"] = exact_receipt_digests.get(case_id)
        event["adjudication_receipt_verified"] = not reasons
        event["reported_project_local_actual"] = source_cases[case_id][
            "adjudication"
        ]["state"]

    # v6 already withheld any frame whose demoted event became unscoreable. Keep its
    # arithmetic untouched; v7 adds provenance diagnostics rather than forking rates.
    base["schema_version"] = 7
    base["adjudication_receipt_count"] = len(receipts_by_digest)
    base["adjudication_contract_count"] = len(adjudication_contracts)
    base["exact_adjudication_receipt_event_count"] = sum(
        event["adjudication_receipt_verified"] for event in base["events"]
    )
    base["adjudication_exactness_counts"] = dict(sorted(reason_counts.items()))
    base["adjudication_contract_digests"] = {
        "|".join(key): v6.v5.canonical_digest(contract)
        for key, contract in sorted(adjudication_contracts.items())
    }
    base["claim_boundary"] = (
        base["claim_boundary"]
        + " Calibration v7 additionally requires project-local truth labels to come "
        "from exact byte-addressed adjudication receipts whose mechanism, implementation "
        "digest, independence relation, measurement roots, evidence namespaces, and "
        "required subject keys were committed in the Git-preregistered plan before the "
        "sampled event. Outcome-selected or hand-reconstructed adjudicators cannot "
        "improve headline accuracy."
    )
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plans", type=Path)
    parser.add_argument("registrations", type=Path)
    parser.add_argument("coverage", type=Path)
    parser.add_argument("decision_receipts", type=Path)
    parser.add_argument("adjudication_receipts", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--git-root", type=Path)
    parser.add_argument("--action-witnesses", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = calibrate(
        json.loads(args.plans.read_text(encoding="utf-8")),
        json.loads(args.registrations.read_text(encoding="utf-8")),
        json.loads(args.coverage.read_text(encoding="utf-8")),
        json.loads(args.decision_receipts.read_text(encoding="utf-8")),
        json.loads(args.adjudication_receipts.read_text(encoding="utf-8")),
        json.loads(args.cases.read_text(encoding="utf-8")),
        action_witnesses=(
            json.loads(args.action_witnesses.read_text(encoding="utf-8"))
            if args.action_witnesses
            else None
        ),
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
