#!/usr/bin/env python3
"""Validate a portable FCMO mission claim→evidence graph.

Proof Spine does not decide whether a proposition is true. It checks whether the
*kind* of evidence attached to a material claim is strong enough to justify making
that kind of claim, whether freshness windows are still live, and whether local
artifact digests still bind to the bytes being cited.

A PASS therefore means "traceability and evidence-shape checks passed", not
"reality has been proven by this script." That boundary is intentional.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
CLAIM_TYPES = {"fact", "execution", "performance", "completion", "freshness", "authority", "decision"}
MATERIALITY = {"routine", "material", "critical"}
EVIDENCE_KINDS = {
    "source",
    "artifact",
    "observation",
    "snapshot_execution",
    "test",
    "benchmark",
    "receipt",
    "approval",
    "policy",
    "user_instruction",
    "plan",
    "attempt",
}
EXECUTION_KINDS = {"snapshot_execution", "test", "benchmark", "receipt"}
PERFORMANCE_KINDS = {"benchmark", "test"}
AUTHORITY_KINDS = {"approval", "policy", "user_instruction"}
FACT_KINDS = {"source", "artifact", "observation", "snapshot_execution", "test", "benchmark", "receipt"}
DECISION_KINDS = FACT_KINDS | AUTHORITY_KINDS
WEAK_ONLY_KINDS = {"plan", "attempt"}
PASS_STATUSES = {"PASS", "VERIFIED", "OBSERVED"}

# Footnote for future maintainers: keep "plan" and "attempt" as explicit evidence
# kinds rather than banning them. They are useful historical evidence that work was
# intended or tried; the safety property is that they must never satisfy execution,
# completion, performance, freshness, or authority claims by themselves.


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message}


def parse_time(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def indexed_items(items: Any, label: str, issues: list[Issue]) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        issues.append(Issue("ERROR", f"{label.upper()}_NOT_LIST", f"{label} must be a list"))
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(Issue("ERROR", f"{label.upper()}_ITEM_NOT_OBJECT", f"{label}[{index}] must be an object"))
            continue
        item_id = item.get("id")
        if not nonempty_text(item_id):
            issues.append(Issue("ERROR", f"{label.upper()}_ID_MISSING", f"{label}[{index}] needs a non-empty id"))
            continue
        if item_id in result:
            issues.append(Issue("ERROR", f"{label.upper()}_ID_DUPLICATE", f"duplicate {label} id: {item_id}"))
            continue
        result[item_id] = item
    return result


def evidence_is_passing(evidence: dict[str, Any]) -> bool:
    status = evidence.get("status")
    if status is None:
        return evidence.get("kind") not in EXECUTION_KINDS
    return isinstance(status, str) and status.upper() in PASS_STATUSES


def validate_local_binding(evidence_id: str, evidence: dict[str, Any], root: Path, issues: list[Issue]) -> None:
    locator = evidence.get("locator")
    expected = evidence.get("sha256")
    if not isinstance(locator, str) or not locator.startswith("file:"):
        if expected is not None:
            issues.append(Issue("ERROR", "HASH_WITHOUT_FILE_LOCATOR", f"{evidence_id} declares sha256 but locator is not file:<path>"))
        return

    relative = locator[5:]
    if not relative:
        issues.append(Issue("ERROR", "EMPTY_FILE_LOCATOR", f"{evidence_id} has an empty file locator"))
        return
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        issues.append(Issue("ERROR", "FILE_ESCAPES_ROOT", f"{evidence_id} resolves outside --root: {relative}"))
        return
    if not path.is_file():
        issues.append(Issue("ERROR", "BOUND_FILE_MISSING", f"{evidence_id} points to missing file: {relative}"))
        return
    if expected is None:
        issues.append(Issue("WARN", "BOUND_FILE_UNHASHED", f"{evidence_id} points to a local file without sha256 binding"))
        return
    if not isinstance(expected, str) or len(expected) != 64:
        issues.append(Issue("ERROR", "INVALID_SHA256", f"{evidence_id} sha256 must be a 64-character hex digest"))
        return
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        issues.append(Issue("ERROR", "SHA256_MISMATCH", f"{evidence_id} digest mismatch for {relative}: expected {expected}, observed {actual}"))


# Footnote for future maintainers: file: locators are deliberately root-confined.
# Proof metadata must not become a convenient way for a validator to read arbitrary
# host files. External evidence can still be cited with ordinary URL/text locators;
# this validator simply cannot byte-bind those sources without a separate fetch step.


def freshness_state(evidence_id: str, evidence: dict[str, Any], now: datetime, issues: list[Issue]) -> bool | None:
    max_age = evidence.get("max_age_hours")
    observed = evidence.get("observed_at")
    if max_age is None:
        return None
    if not isinstance(max_age, (int, float)) or isinstance(max_age, bool) or max_age <= 0:
        issues.append(Issue("ERROR", "INVALID_MAX_AGE", f"{evidence_id} max_age_hours must be a positive number"))
        return False
    if not nonempty_text(observed):
        issues.append(Issue("ERROR", "FRESHNESS_WITHOUT_OBSERVED_AT", f"{evidence_id} declares max_age_hours without observed_at"))
        return False
    try:
        observed_at = parse_time(observed)
    except (TypeError, ValueError) as exc:
        issues.append(Issue("ERROR", "INVALID_OBSERVED_AT", f"{evidence_id} observed_at is invalid: {exc}"))
        return False
    age_hours = (now - observed_at).total_seconds() / 3600.0
    if age_hours < -0.01:
        issues.append(Issue("ERROR", "OBSERVED_IN_FUTURE", f"{evidence_id} observed_at is {abs(age_hours):.2f}h in the future"))
        return False
    if age_hours > float(max_age):
        issues.append(Issue("ERROR", "STALE_EVIDENCE", f"{evidence_id} is {age_hours:.2f}h old; max_age_hours={max_age}"))
        return False
    return True


def validate_claim(
    claim_id: str,
    claim: dict[str, Any],
    evidence_index: dict[str, dict[str, Any]],
    freshness: dict[str, bool | None],
    issues: list[Issue],
) -> None:
    statement = claim.get("statement")
    claim_type = claim.get("type")
    materiality = claim.get("materiality", "material")
    refs = claim.get("evidence", [])

    if not nonempty_text(statement):
        issues.append(Issue("ERROR", "CLAIM_STATEMENT_MISSING", f"{claim_id} needs a non-empty statement"))
    if claim_type not in CLAIM_TYPES:
        issues.append(Issue("ERROR", "CLAIM_TYPE_INVALID", f"{claim_id} type must be one of {sorted(CLAIM_TYPES)}"))
        return
    if materiality not in MATERIALITY:
        issues.append(Issue("ERROR", "MATERIALITY_INVALID", f"{claim_id} materiality must be one of {sorted(MATERIALITY)}"))
    if not isinstance(refs, list) or not all(nonempty_text(ref) for ref in refs):
        issues.append(Issue("ERROR", "EVIDENCE_REFS_INVALID", f"{claim_id} evidence must be a list of non-empty evidence ids"))
        return
    if not refs:
        issues.append(Issue("ERROR", "CLAIM_UNSUPPORTED", f"{claim_id} has no evidence references"))
        return

    if materiality in {"material", "critical"} and not nonempty_text(claim.get("boundary")):
        issues.append(Issue("ERROR", "CLAIM_BOUNDARY_MISSING", f"{claim_id} is {materiality} and needs an explicit claim boundary"))

    resolved: list[dict[str, Any]] = []
    resolved_ids: list[str] = []
    for ref in refs:
        evidence = evidence_index.get(ref)
        if evidence is None:
            issues.append(Issue("ERROR", "UNKNOWN_EVIDENCE_REF", f"{claim_id} references missing evidence {ref}"))
            continue
        resolved.append(evidence)
        resolved_ids.append(ref)

    if not resolved:
        return

    passing = [(eid, ev) for eid, ev in zip(resolved_ids, resolved) if evidence_is_passing(ev)]
    passing_kinds = {ev.get("kind") for _, ev in passing}

    if passing_kinds and passing_kinds <= WEAK_ONLY_KINDS:
        issues.append(Issue("ERROR", "WEAK_EVIDENCE_ONLY", f"{claim_id} is supported only by plans/attempts"))

    if claim_type == "fact" and not (passing_kinds & FACT_KINDS):
        issues.append(Issue("ERROR", "FACT_EVIDENCE_TOO_WEAK", f"{claim_id} fact claim lacks passing source/artifact/observation/execution evidence"))
    elif claim_type == "execution" and not (passing_kinds & EXECUTION_KINDS):
        issues.append(Issue("ERROR", "EXECUTION_NOT_PROVEN", f"{claim_id} execution claim lacks passing execution/test/benchmark/receipt evidence"))
    elif claim_type == "performance":
        performance = [(eid, ev) for eid, ev in passing if ev.get("kind") in PERFORMANCE_KINDS]
        if not performance:
            issues.append(Issue("ERROR", "PERFORMANCE_NOT_PROVEN", f"{claim_id} performance claim lacks a passing benchmark/test"))
        elif not any(nonempty_text(ev.get("comparison")) for _, ev in performance):
            issues.append(Issue("ERROR", "PERFORMANCE_COMPARISON_MISSING", f"{claim_id} performance claim needs benchmark/test evidence with a comparison"))
    elif claim_type == "completion":
        if not nonempty_text(claim.get("acceptance_criteria")):
            issues.append(Issue("ERROR", "COMPLETION_CRITERIA_MISSING", f"{claim_id} completion claim needs explicit acceptance_criteria"))
        if not (passing_kinds & EXECUTION_KINDS):
            issues.append(Issue("ERROR", "COMPLETION_NOT_PROVEN", f"{claim_id} completion claim lacks passing execution/test/benchmark/receipt evidence"))
    elif claim_type == "freshness":
        fresh_refs = [eid for eid, _ in passing if freshness.get(eid) is True]
        if not fresh_refs:
            issues.append(Issue("ERROR", "FRESHNESS_NOT_PROVEN", f"{claim_id} freshness claim lacks passing evidence with a live max_age_hours window"))
    elif claim_type == "authority" and not (passing_kinds & AUTHORITY_KINDS):
        issues.append(Issue("ERROR", "AUTHORITY_NOT_PROVEN", f"{claim_id} authority claim lacks passing approval/policy/user_instruction evidence"))
    elif claim_type == "decision" and not (passing_kinds & DECISION_KINDS):
        issues.append(Issue("ERROR", "DECISION_EVIDENCE_TOO_WEAK", f"{claim_id} decision claim lacks substantive source/execution/authority evidence"))


# Footnote for future maintainers: Proof Spine checks evidence *shape*, not semantic
# truth. Do not "improve" it by treating a JSON declaration as cryptographic proof
# that an external benchmark, approval, or command actually occurred. Exact external
# attestation belongs in the evidence object itself (for example an integrity receipt)
# and can then be byte-bound or independently verified by the appropriate tool.


def validate_receipt(payload: Any, root: Path, now: datetime) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(payload, dict):
        return [Issue("ERROR", "ROOT_NOT_OBJECT", "receipt root must be a JSON object")]
    if payload.get("schema_version") != SCHEMA_VERSION:
        issues.append(Issue("ERROR", "SCHEMA_VERSION_INVALID", f"schema_version must equal {SCHEMA_VERSION}"))

    mission = payload.get("mission")
    if not isinstance(mission, dict) or not nonempty_text(mission.get("objective")):
        issues.append(Issue("ERROR", "MISSION_OBJECTIVE_MISSING", "mission.objective must be non-empty"))

    evidence_index = indexed_items(payload.get("evidence"), "evidence", issues)
    claim_index = indexed_items(payload.get("claims"), "claims", issues)
    freshness: dict[str, bool | None] = {}

    for evidence_id, evidence in evidence_index.items():
        kind = evidence.get("kind")
        if kind not in EVIDENCE_KINDS:
            issues.append(Issue("ERROR", "EVIDENCE_KIND_INVALID", f"{evidence_id} kind must be one of {sorted(EVIDENCE_KINDS)}"))
        if not nonempty_text(evidence.get("locator")):
            issues.append(Issue("ERROR", "EVIDENCE_LOCATOR_MISSING", f"{evidence_id} needs a non-empty locator"))
        if kind in EXECUTION_KINDS and not nonempty_text(evidence.get("status")):
            issues.append(Issue("ERROR", "EXECUTION_STATUS_MISSING", f"{evidence_id} execution-like evidence needs status"))
        validate_local_binding(evidence_id, evidence, root, issues)
        freshness[evidence_id] = freshness_state(evidence_id, evidence, now, issues)

    referenced: set[str] = set()
    for claim_id, claim in claim_index.items():
        refs = claim.get("evidence")
        if isinstance(refs, list):
            referenced.update(ref for ref in refs if isinstance(ref, str))
        validate_claim(claim_id, claim, evidence_index, freshness, issues)

    for evidence_id in evidence_index:
        if evidence_id not in referenced:
            issues.append(Issue("WARN", "ORPHAN_EVIDENCE", f"{evidence_id} is declared but not used by any claim"))

    if not claim_index:
        issues.append(Issue("ERROR", "NO_CLAIMS", "at least one claim is required"))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, help="Proof Spine JSON receipt")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root for file: evidence locators")
    parser.add_argument("--now", help="Override current time (ISO-8601) for deterministic validation")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation output")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Proof Spine: FAIL — cannot read receipt: {exc}", file=sys.stderr)
        return 2

    try:
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    except ValueError as exc:
        print(f"Proof Spine: FAIL — invalid --now: {exc}", file=sys.stderr)
        return 2

    issues = validate_receipt(payload, args.root.resolve(), now)
    errors = [item for item in issues if item.level == "ERROR"]
    warnings = [item for item in issues if item.level == "WARN"]
    status = "PASS" if not errors and not (args.strict and warnings) else "FAIL"

    result = {
        "proof_spine_version": "0.1",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "checked_at": now.isoformat(),
        "errors": [item.as_dict() for item in errors],
        "warnings": [item.as_dict() for item in warnings],
        "claim_boundary": (
            "PASS proves only that declared claims satisfy Proof Spine traceability/evidence-shape, "
            "freshness, and optional local byte-binding checks. It does not itself prove external truth or authority."
        ),
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for item in issues:
            print(f"[{item.level}] {item.code}: {item.message}")
        print(f"FCMO Proof Spine: {status}")
        print(result["claim_boundary"])
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
