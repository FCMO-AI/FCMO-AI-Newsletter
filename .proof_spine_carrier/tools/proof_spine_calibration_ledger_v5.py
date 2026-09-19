#!/usr/bin/env python3
"""Calibration v5: outcome-blind enrollment with verifiable Git preregistration.

v4 protects executed decision provenance, independent adjudication, and disjoint
measurement roots. v5 closes a different loophole: case selection after seeing an
outcome. A scoreable case must belong to an outcome-blind plan whose exact bytes are
proven to have existed in Git before the gate observation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("calibration_v4", HERE / "proof_spine_calibration_ledger_v4.py")
v4 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v4)

PLAN_KIND = "FCMO_PROOF_SPINE_CALIBRATION_PLAN"
PLAN_AUTHORITY = "NON_NORMATIVE_EVIDENCE"
REGISTRATION_KIND = "FCMO_PROOF_SPINE_CALIBRATION_PLAN_REGISTRATION"
SAMPLING_MODE = "ALL_QUALIFYING_FUTURE_EVENTS"
ENROLLMENT_MODES = {"PROSPECTIVE", "RETROSPECTIVE"}
COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


class PlanVerificationError(v4.CalibrationError):
    """Raised when version-control preregistration cannot be proven."""


def canonical_digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise v4.CalibrationError(f"{label} must be non-empty text")
    return value.strip()


def validate_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise v4.CalibrationError("calibration plan must be an object")
    if plan.get("schema_version") != 1 or plan.get("kind") != PLAN_KIND or plan.get("authority") != PLAN_AUTHORITY:
        raise v4.CalibrationError("calibration plan schema/kind/authority mismatch")
    _text(plan.get("plan_id"), "plan_id")
    v4.parse_time(plan.get("authored_at"), "plan.authored_at")
    if plan.get("sampling_mode") != SAMPLING_MODE:
        raise v4.CalibrationError(f"plan.sampling_mode must equal {SAMPLING_MODE}")
    if plan.get("outcome_blind") is not True:
        raise v4.CalibrationError("plan.outcome_blind must be true")
    gates = plan.get("registered_gates")
    if not isinstance(gates, list) or not gates:
        raise v4.CalibrationError("plan.registered_gates must be a non-empty list")
    seen: set[tuple[str, str, str]] = set()
    for i, gate in enumerate(gates):
        if not isinstance(gate, dict):
            raise v4.CalibrationError(f"registered_gates[{i}] must be an object")
        key = (
            _text(gate.get("project_id"), f"registered_gates[{i}].project_id"),
            _text(gate.get("repository"), f"registered_gates[{i}].repository").casefold(),
            _text(gate.get("gate_id"), f"registered_gates[{i}].gate_id"),
        )
        if key in seen:
            raise v4.CalibrationError(f"duplicate registered gate: {key}")
        seen.add(key)
    notes = plan.get("notes", [])
    if not isinstance(notes, list) or any(not isinstance(x, str) or not x.strip() for x in notes):
        raise v4.CalibrationError("plan.notes must be a list of non-empty strings")
    return plan


def index_plans(plans: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(plans, list) or not plans:
        raise v4.CalibrationError("calibration plans must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for plan in plans:
        validate_plan(plan)
        pid = plan["plan_id"]
        if pid in out:
            raise v4.CalibrationError(f"duplicate plan_id: {pid}")
        out[pid] = plan
    return out


def validate_registration(registration: Any, plans_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(registration, dict):
        raise v4.CalibrationError("plan registration must be an object")
    if registration.get("schema_version") != 1 or registration.get("kind") != REGISTRATION_KIND:
        raise v4.CalibrationError("plan registration schema/kind mismatch")
    if registration.get("authority") != PLAN_AUTHORITY:
        raise v4.CalibrationError("plan registration authority mismatch")
    plan_id = _text(registration.get("plan_id"), "registration.plan_id")
    plan = plans_by_id.get(plan_id)
    if plan is None:
        raise v4.CalibrationError(f"registration references unknown plan_id: {plan_id}")
    if registration.get("plan_digest") != canonical_digest(plan):
        raise v4.CalibrationError("registration.plan_digest does not match exact plan bytes")
    repository = _text(registration.get("repository"), "registration.repository")
    if repository.count("/") != 1:
        raise v4.CalibrationError("registration.repository must use owner/repository form")
    path = _text(registration.get("path"), "registration.path")
    if path.startswith("/") or ".." in Path(path).parts:
        raise v4.CalibrationError("registration.path must be repository-relative without traversal")
    commit_sha = _text(registration.get("commit_sha"), "registration.commit_sha")
    if not COMMIT_RE.fullmatch(commit_sha):
        raise v4.CalibrationError("registration.commit_sha must be lowercase Git commit hex")
    v4.parse_time(registration.get("committed_at"), "registration.committed_at")
    v4._strings(registration.get("evidence_refs"), "registration.evidence_refs")
    return registration


def index_registrations(registrations: Any, plans_by_id: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(registrations, list) or not registrations:
        raise v4.CalibrationError("plan registrations must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for registration in registrations:
        validate_registration(registration, plans_by_id)
        pid = registration["plan_id"]
        if pid in out:
            raise v4.CalibrationError(f"duplicate plan registration: {pid}")
        out[pid] = registration
    return out


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise PlanVerificationError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def verify_registration_in_git(
    registration: dict[str, Any],
    plan: dict[str, Any],
    *,
    git_root: Path,
) -> dict[str, Any]:
    """Prove the exact registered plan existed in immutable Git history.

    The registration JSON is metadata, not the trust root. The Git commit itself is
    the trust root: we re-read the registered path from that commit and compare its
    canonical plan digest before using the commit timestamp for preregistration order.
    """
    commit = registration["commit_sha"]
    resolved = _git(git_root, "rev-parse", f"{commit}^{{commit}}")
    if resolved != commit:
        raise PlanVerificationError("registration.commit_sha did not resolve exactly")
    raw = _git(git_root, "show", f"{commit}:{registration['path']}")
    try:
        committed_doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanVerificationError("registered plan path is not JSON at referenced commit") from exc
    # Footnote [2]: registry files may contain several plans. Git verification selects
    # the registered plan_id from the committed document and binds that exact entry,
    # rather than quietly assuming a single-object fixture that production does not use.
    if isinstance(committed_doc, list):
        committed_plans = index_plans(committed_doc)
        committed_plan = committed_plans.get(registration["plan_id"])
        if committed_plan is None:
            raise PlanVerificationError("registered plan_id is absent from Git-committed plan registry")
    else:
        committed_plan = validate_plan(committed_doc)
        if committed_plan["plan_id"] != registration["plan_id"]:
            raise PlanVerificationError("Git-committed single plan has a different plan_id")
    if canonical_digest(committed_plan) != registration["plan_digest"]:
        raise PlanVerificationError("Git-committed plan digest differs from registration.plan_digest")
    if canonical_digest(committed_plan) != canonical_digest(plan):
        raise PlanVerificationError("supplied plan differs from the Git-preregistered plan")
    committed_at = _git(git_root, "show", "-s", "--format=%cI", commit)
    if v4.parse_time(committed_at, "git commit time") != v4.parse_time(registration["committed_at"], "registration.committed_at"):
        raise PlanVerificationError("registration.committed_at does not match Git commit time")
    return {
        "state": "VERIFIED_GIT_COMMIT",
        "commit_sha": commit,
        "committed_at": committed_at,
        "plan_digest": registration["plan_digest"],
    }


def _gate_registered(plan: dict[str, Any], case: dict[str, Any]) -> bool:
    wanted = (case["project"]["id"], case["project"]["repository"].casefold(), case["gate"]["id"])
    allowed = {
        (g["project_id"], g["repository"].casefold(), g["gate_id"])
        for g in plan["registered_gates"]
    }
    return wanted in allowed


def selection_reasons(
    case: dict[str, Any],
    plans_by_id: dict[str, dict[str, Any]],
    registrations_by_id: dict[str, dict[str, Any]],
    verified_plans: set[str],
) -> list[str]:
    enrollment = case.get("enrollment")
    if not isinstance(enrollment, dict):
        raise v4.CalibrationError("v5 case requires enrollment object")
    mode = enrollment.get("mode")
    if mode not in ENROLLMENT_MODES:
        raise v4.CalibrationError(f"enrollment.mode must be one of {sorted(ENROLLMENT_MODES)}")
    plan_id = _text(enrollment.get("plan_id"), "enrollment.plan_id")
    plan = plans_by_id.get(plan_id)
    if plan is None:
        raise v4.CalibrationError(f"unknown enrollment.plan_id: {plan_id}")
    registration = registrations_by_id.get(plan_id)
    if registration is None:
        raise v4.CalibrationError(f"missing plan registration for {plan_id}")
    if enrollment.get("plan_digest") != canonical_digest(plan):
        raise v4.CalibrationError("enrollment.plan_digest does not match referenced plan")

    reasons: list[str] = []
    if mode == "RETROSPECTIVE":
        reasons.append("RETROSPECTIVE_ENROLLMENT")
    if not _gate_registered(plan, case):
        reasons.append("GATE_NOT_REGISTERED_IN_PLAN")
    if plan_id not in verified_plans:
        reasons.append("PLAN_PROVENANCE_NOT_GIT_VERIFIED")

    # Footnote [1]: the version-control commit, not a self-declared plan timestamp, is
    # the preregistration boundary. A plan committed after the gate can never be used
    # retroactively to improve calibration statistics, even if its JSON is backdated.
    registered_at = v4.parse_time(registration["committed_at"], "registration.committed_at")
    gate_at = v4.parse_time(case["gate"]["observed_at"], "gate.observed_at")
    if registered_at > gate_at:
        reasons.append("PLAN_POSTDATES_GATE")
    return reasons


def classify(
    case: dict[str, Any],
    plans_by_id: dict[str, dict[str, Any]],
    registrations_by_id: dict[str, dict[str, Any]],
    verified_plans: set[str],
) -> dict[str, Any]:
    base = v4.classify(case)
    reasons = list(
        dict.fromkeys(
            base["scoreability_reasons"]
            + selection_reasons(case, plans_by_id, registrations_by_id, verified_plans)
        )
    )
    if reasons:
        base["classification"] = "UNSCORABLE"
    base["scoreability_reasons"] = reasons
    base["calibration_plan_id"] = case["enrollment"]["plan_id"]
    base["enrollment_mode"] = case["enrollment"]["mode"]
    base["plan_git_verified"] = case["enrollment"]["plan_id"] in verified_plans
    return base


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": numerator, "denominator": denominator, "rate": numerator / denominator if denominator else None}


def calibrate(
    plans: list[dict[str, Any]],
    registrations: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    *,
    git_root: Path | None = None,
) -> dict[str, Any]:
    plans_by_id = index_plans(plans)
    registrations_by_id = index_registrations(registrations, plans_by_id)
    if set(plans_by_id) != set(registrations_by_id):
        raise v4.CalibrationError("every supplied plan must have exactly one registration")

    verified: set[str] = set()
    verification: dict[str, dict[str, Any]] = {}
    if git_root is not None:
        for pid, plan in plans_by_id.items():
            verification[pid] = verify_registration_in_git(registrations_by_id[pid], plan, git_root=git_root)
            verified.add(pid)

    if not isinstance(cases, list) or not cases:
        raise v4.CalibrationError("calibration input must be a non-empty list")
    for case in cases:
        v4.validate_case(case)
    events = [classify(case, plans_by_id, registrations_by_id, verified) for case in cases]
    ids = [e["case_id"] for e in events]
    if len(ids) != len(set(ids)):
        raise v4.CalibrationError("duplicate case_id")

    source = {c["case_id"]: c for c in cases}
    first_by_episode: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for event in events:
        if event["classification"] == "UNSCORABLE":
            continue
        key = (event["project"]["repository"].casefold(), event["project"]["id"], event["gate_id"], event["episode_id"])
        current = first_by_episode.get(key)
        if current is None:
            first_by_episode[key] = event
            continue
        a = v4.parse_time(source[event["case_id"]]["gate"]["observed_at"], "gate.observed_at")
        b = v4.parse_time(source[current["case_id"]]["gate"]["observed_at"], "gate.observed_at")
        if a < b:
            first_by_episode[key] = event

    episodes = list(first_by_episode.values())
    labels = {"TRUE_BLOCK", "TRUE_ALLOW", "FALSE_BLOCK", "FALSE_ALLOW"}
    counts = {label: sum(e["classification"] == label for e in episodes) for label in sorted(labels)}
    event_counts = {label: sum(e["classification"] == label for e in events) for label in sorted(labels | {"UNSCORABLE"})}
    reason_counts: dict[str, int] = {}
    for event in events:
        for reason in event["scoreability_reasons"]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    tb, ta, fb, fa = counts["TRUE_BLOCK"], counts["TRUE_ALLOW"], counts["FALSE_BLOCK"], counts["FALSE_ALLOW"]
    return {
        "schema_version": 5,
        "kind": "FCMO_PROOF_SPINE_CALIBRATION_REPORT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "plan_count": len(plans_by_id),
        "case_count": len(events),
        "scored_episode_count": len(episodes),
        "executed_gate_case_count": sum(e["gate_provenance_state"] == "EXECUTED" for e in events),
        "prospective_enrollment_case_count": sum(e["enrollment_mode"] == "PROSPECTIVE" for e in events),
        "git_verified_plan_count": len(verified),
        "observed_action_count": sum(e["action_occurred"] for e in events),
        "event_counts": event_counts,
        "scoreability_counts": dict(sorted(reason_counts.items())),
        "episode_counts": counts,
        "sensitivity": _rate(tb, tb + fa),
        "specificity": _rate(ta, ta + fb),
        "false_block_rate": _rate(fb, fb + ta),
        "false_allow_rate": _rate(fa, fa + tb),
        "episodes": episodes,
        "events": events,
        "plan_digests": {pid: canonical_digest(p) for pid, p in sorted(plans_by_id.items())},
        "plan_verification": verification,
        "claim_boundary": (
            "Accuracy denominators require every v4 execution/adjudication/measurement-independence rule plus outcome-blind enrollment in a calibration plan whose exact bytes are Git-verified at a commit predating the gate. Self-declared plan timestamps, retrospective enrollment, unverified plan provenance, and post-outcome case selection cannot improve sensitivity/specificity. Zero denominators remain null."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plans", type=Path)
    parser.add_argument("registrations", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--git-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = calibrate(
        json.loads(args.plans.read_text(encoding="utf-8")),
        json.loads(args.registrations.read_text(encoding="utf-8")),
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
