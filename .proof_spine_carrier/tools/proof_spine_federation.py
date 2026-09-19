#!/usr/bin/env python3
"""FCMO Proof Spine v0.3 — universal project/federation integration layer.

Projects own truth production and local semantics. This layer accepts one common
EVIDENCE_ONLY receipt shape, namespaces evidence for cross-project composition,
and delegates deterministic claim/gate evaluation to the generic v0.2 engine.
It knows no Newsletter, CMPCT, BLM, model, codec, website, or product semantics.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

ENGINE_SPEC = importlib.util.spec_from_file_location("proof_spine_v2", HERE / "proof_spine_v2.py")
engine = importlib.util.module_from_spec(ENGINE_SPEC)
sys.modules[ENGINE_SPEC.name] = engine
ENGINE_SPEC.loader.exec_module(engine)

PROJECT_RECEIPT_SCHEMA = 1
PROJECT_RECEIPT_KIND = "FCMO_PROOF_SPINE_PROJECT_RECEIPT"
EVIDENCE_ONLY = "EVIDENCE_ONLY"
RESERVED_SCOPE_KEYS = {"project_id", "repository"}
FEDERATION_DELIMITER = "::"
DECISION_RECEIPT_SCHEMA = 1
DECISION_RECEIPT_KIND = "FCMO_PROOF_SPINE_DECISION_RECEIPT"


def canonical_sha256(payload: Any) -> str:
    """Return the cross-component digest spelling used by calibration contracts."""
    return "sha256:" + engine.digest(payload)


def build_decision_receipt(
    *,
    mode: str,
    spec: dict[str, Any],
    source_evidence_digest: str,
    report: dict[str, Any],
    now: datetime,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Bind one executed universal evaluation to exact contract/evidence/decision bytes."""
    gates = report.get("gates")
    if not isinstance(gates, dict):
        raise engine.ProofError("proof report must contain gate decisions before receipt emission")
    receipt = {
        "schema_version": DECISION_RECEIPT_SCHEMA,
        "kind": DECISION_RECEIPT_KIND,
        "authority": EVIDENCE_ONLY,
        "mode": mode,
        "evaluated_at": now.isoformat(),
        "context": copy.deepcopy(context),
        "proofspec_digest": canonical_sha256(spec),
        "source_evidence_digest": source_evidence_digest,
        "effective_evidence_digest": "sha256:" + report["evidence_digest"],
        "proof_report_digest": canonical_sha256(report),
        "gate_decisions": copy.deepcopy(gates),
    }
    # Footnote: the receipt intentionally carries no self-hash. Its canonical digest
    # is emitted beside it by the caller, avoiding a circular object while still giving
    # calibration and downstream witnesses one byte-addressed identity for the exact
    # contract + source evidence + effective evidence + gate result that actually ran.
    return receipt


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_time(value: Any, label: str = "timestamp") -> datetime:
    if not _text(value):
        raise engine.ProofError(f"{label} must be a timezone-aware timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise engine.ProofError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def _positive_hours(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise engine.ProofError(f"{label} must be a positive number of hours")
    return float(value)


def _repository_key(value: Any, label: str) -> str:
    if not _text(value):
        raise engine.ProofError(f"{label} must be non-empty owner/repository text")
    cleaned = value.strip()
    parts = cleaned.split("/")
    if len(parts) != 2 or not all(parts) or any(any(ch.isspace() for ch in part) for part in parts):
        raise engine.ProofError(f"{label} must use owner/repository form")
    # Footnote: GitHub owner/repository identity is case-insensitive. Federation keeps
    # the producer's original spelling for provenance but compares a case-folded key so
    # the same repository cannot masquerade as two independent members by casing alone.
    return cleaned.casefold()


def _index(items: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise engine.ProofError(f"{label} must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict) or not _text(item.get("id")):
            raise engine.ProofError(f"{label}[{i}] needs an object with non-empty id")
        if FEDERATION_DELIMITER in item["id"]:
            raise engine.ProofError(f"{label}[{i}].id may not contain reserved delimiter {FEDERATION_DELIMITER!r}")
        if item["id"] in out:
            raise engine.ProofError(f"duplicate {label} id: {item['id']}")
        out[item["id"]] = item
    return out


def project_context(receipt: dict[str, Any]) -> dict[str, Any]:
    project = receipt["project"]
    # Footnote: project identity is written last so even a malformed caller cannot
    # override it through generic scope metadata. validate_project_receipt separately
    # rejects those reserved keys to keep the receipt contract explicit and auditable.
    return {**receipt.get("scope", {}), "project_id": project["id"], "repository": project["repository"]}


def validate_project_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise engine.ProofError("project receipt must be an object")
    if receipt.get("schema_version") != PROJECT_RECEIPT_SCHEMA:
        raise engine.ProofError(f"project receipt schema_version must equal {PROJECT_RECEIPT_SCHEMA}")
    if receipt.get("kind") != PROJECT_RECEIPT_KIND:
        raise engine.ProofError(f"project receipt kind must equal {PROJECT_RECEIPT_KIND}")
    if receipt.get("authority") != EVIDENCE_ONLY:
        raise engine.ProofError("project receipt authority must equal EVIDENCE_ONLY")

    # Footnote for future maintainers: producers are evidence sources, not judges.
    # Keeping contract fields out of receipts prevents a project/runtime producer from
    # silently lowering the acceptance rule that will later evaluate its own evidence.
    forbidden = {"mission", "claims", "gates"} & set(receipt)
    if forbidden:
        raise engine.ProofError(f"project receipt contains proof-contract fields: {sorted(forbidden)}")

    project = receipt.get("project")
    if not isinstance(project, dict) or not _text(project.get("id")) or not _text(project.get("repository")):
        raise engine.ProofError("project receipt requires project.id and project.repository")
    if FEDERATION_DELIMITER in project["id"]:
        raise engine.ProofError(
            f"project.id may not contain {FEDERATION_DELIMITER!r}; it is reserved for federation namespaces"
        )
    _repository_key(project["repository"], "project.repository")

    receipt_observed = _parse_time(receipt.get("observed_at"), "project receipt observed_at")
    scope = receipt.get("scope", {})
    if not isinstance(scope, dict):
        raise engine.ProofError("project receipt scope must be an object")
    reserved = RESERVED_SCOPE_KEYS & set(scope)
    if reserved:
        raise engine.ProofError(f"project receipt scope contains reserved identity keys: {sorted(reserved)}")

    evidence = _index(receipt.get("evidence"), "evidence")
    local_context = project_context(receipt)
    for eid, item in evidence.items():
        if not _text(item.get("status")):
            raise engine.ProofError(f"evidence {eid} needs explicit status")
        if not _text(item.get("causal_root")):
            raise engine.ProofError(f"evidence {eid} needs causal_root")
        if "shared_causal_root" in item:
            raise engine.ProofError(
                f"evidence {eid} may not declare shared_causal_root; cross-project causal equivalence belongs in the reviewed proofspec"
            )
        if item.get("observed_at") is not None:
            evidence_observed = _parse_time(item["observed_at"], f"evidence {eid}.observed_at")
            if evidence_observed > receipt_observed:
                raise engine.ProofError(
                    f"evidence {eid}.observed_at cannot be later than project receipt observed_at"
                )
        if item.get("max_age_hours") is not None:
            _positive_hours(item["max_age_hours"], f"evidence {eid}.max_age_hours")
            if item.get("observed_at") is None:
                raise engine.ProofError(f"evidence {eid}.max_age_hours requires observed_at")
        if item.get("valid_until") is not None:
            _parse_time(item["valid_until"], f"evidence {eid}.valid_until")
        applies_to = item.get("applies_to", {})
        if not isinstance(applies_to, dict):
            raise engine.ProofError(f"evidence {eid} applies_to must be an object")
        for key, expected in applies_to.items():
            if local_context.get(key) != expected:
                raise engine.ProofError(
                    f"evidence {eid} receipt-scope mismatch {key}={local_context.get(key)!r}, expected {expected!r}"
                )

    decisions = receipt.get("local_decisions", [])
    if not isinstance(decisions, list) or any(not isinstance(item, dict) for item in decisions):
        raise engine.ProofError("local_decisions must be a list of objects")

    # Footnote: the universal layer deliberately does not decide what PASS/FAIL means
    # for a project. CMPCT benchmark law, BLM model-science law, Newsletter health law,
    # and future project laws remain authoritative in their own repositories.
    return receipt


def local_envelope(receipt: dict[str, Any]) -> dict[str, Any]:
    validate_project_receipt(receipt)
    evidence = copy.deepcopy(receipt["evidence"])
    for item in evidence:
        # Footnote: applies_to has already been checked against the producer's signed/
        # digested project receipt context. Engine mission.context is a proof-contract
        # namespace, not a second project-receipt namespace, so carrying applies_to
        # through would make valid local scope look invalid whenever the proofspec omits
        # a redundant scope key.
        item.pop("applies_to", None)
    return {"schema_version": 2, "evidence": evidence}


def federated_envelope(receipts: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not receipts:
        raise engine.ProofError("federation requires at least one project receipt")

    evidence: list[dict[str, Any]] = []
    seen_projects: set[str] = set()
    seen_repositories: set[str] = set()
    members: list[dict[str, Any]] = []

    for raw in receipts:
        receipt = validate_project_receipt(raw)
        project = receipt["project"]
        pid = project["id"]
        repository = project["repository"]
        repository_key = _repository_key(repository, f"project {pid}.repository")
        if pid in seen_projects:
            raise engine.ProofError(f"duplicate project receipt in federation: {pid}")
        if repository_key in seen_repositories:
            raise engine.ProofError(f"duplicate repository represented under multiple federation members: {repository}")
        seen_projects.add(pid)
        seen_repositories.add(repository_key)
        receipt_digest = engine.digest(receipt)
        members.append(
            {
                "project_id": pid,
                "repository": repository,
                "observed_at": receipt["observed_at"],
                "receipt_digest": receipt_digest,
                "scope": receipt.get("scope", {}),
            }
        )

        for source in receipt["evidence"]:
            item = copy.deepcopy(source)
            local_id = item["id"]
            item["id"] = f"{pid}{FEDERATION_DELIMITER}{local_id}"

            # Footnote: a project's local causal lineage is namespaced by default.
            # Cross-project equivalence is intentionally NOT producer-controlled; the
            # reviewed proofspec may group roots later when a real common cause exists.
            item["causal_root"] = f"{pid}{FEDERATION_DELIMITER}{item['causal_root']}"

            # Footnote: project-local applicability was checked against the receipt's
            # own project/scope above. A federation has one mission context and cannot
            # simultaneously equal several local project contexts; reviewed federation
            # receipt_requirements below bind each member to the scope the contract expects.
            item.pop("applies_to", None)
            item["source_project"] = {
                "id": pid,
                "repository": repository,
                "local_evidence_id": local_id,
                "receipt_digest": receipt_digest,
            }
            evidence.append(item)

    return {"schema_version": 2, "evidence": evidence}, {"members": members}


def federation_config(spec: dict[str, Any]) -> dict[str, Any]:
    cfg = spec.get("federation", {})
    if not isinstance(cfg, dict):
        raise engine.ProofError("proofspec federation must be an object when present")
    return cfg


def _tighten_valid_until(item: dict[str, Any], deadline: datetime) -> None:
    existing = item.get("valid_until")
    if existing is not None:
        deadline = min(deadline, _parse_time(existing, f"evidence {item['id']}.valid_until"))
    item["valid_until"] = deadline.isoformat()


def _apply_temporal_integrity(envelope: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for item in envelope["evidence"]:
        observed_raw = item.get("observed_at")
        if observed_raw is None:
            continue
        observed = _parse_time(observed_raw, f"evidence {item['id']}.observed_at")
        if observed > now:
            # Footnote: future-dated evidence is impossible at evaluation time. Marking
            # the evidence INVALID rather than throwing away the whole federation keeps
            # unrelated projects evaluable while preventing clock fiction from extending
            # this premise's lifetime or opening any gate that depends on it.
            item["status"] = "INVALID"
            applied.append(
                {
                    "evidence_id": item["id"],
                    "action": "future_observation_invalidated",
                    "observed_at": observed.isoformat(),
                }
            )
    return applied


def _apply_evidence_freshness_requirements(
    requirements: Any,
    envelope: dict[str, Any],
    now: datetime,
    *,
    label: str,
) -> list[dict[str, Any]]:
    if requirements is None:
        requirements = {}
    if not isinstance(requirements, dict):
        raise engine.ProofError(f"{label} must be an object")

    evidence = {item["id"]: item for item in envelope["evidence"]}
    applied: list[dict[str, Any]] = []
    for eid, policy in requirements.items():
        if not _text(eid) or not isinstance(policy, dict):
            raise engine.ProofError(f"{label} entries need non-empty evidence ids and object policies")
        item = evidence.get(eid)
        if item is None:
            raise engine.ProofError(f"{label} references unknown evidence id: {eid}")
        max_age = _positive_hours(policy.get("max_age_hours"), f"{label}.{eid}.max_age_hours")
        observed_raw = item.get("observed_at")
        action = "bounded"
        if observed_raw is None:
            # Footnote: a fresh receipt is not proof that the underlying observation is
            # fresh. When the reviewed contract requires evidence age and the producer
            # omitted the observation time, fail closed as UNKNOWN rather than treating
            # receipt regeneration as a freshness refresh.
            if str(item.get("status", "")).upper() in engine.PASS:
                item["status"] = "UNKNOWN"
            action = "missing_observed_at"
            applied.append(
                {
                    "evidence_id": eid,
                    "contract_max_age_hours": max_age,
                    "effective_max_age_hours": None,
                    "action": action,
                }
            )
            continue

        observed = _parse_time(observed_raw, f"evidence {eid}.observed_at")
        producer_max_age = item.get("max_age_hours")
        effective = max_age
        if producer_max_age is not None:
            effective = min(effective, _positive_hours(producer_max_age, f"evidence {eid}.max_age_hours"))
        item["max_age_hours"] = effective
        applied.append(
            {
                "evidence_id": eid,
                "contract_max_age_hours": max_age,
                "effective_max_age_hours": effective,
                "observed_at": observed.isoformat(),
                "action": action,
            }
        )

    # Footnote: producer freshness metadata is allowed only to tighten validity. The
    # reviewed contract supplies the outer ceiling, so a producer cannot keep its own
    # PASS alive by omitting a TTL or choosing an arbitrarily generous one.
    return applied


def validate_receipt_requirements(
    spec: dict[str, Any],
    federation: dict[str, Any],
    envelope: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Bind every federation member to repository/scope reviewed by the proofspec."""
    cfg = federation_config(spec)
    requirements = cfg.get("receipt_requirements", {})
    if not isinstance(requirements, dict) or not requirements:
        raise engine.ProofError("proofspec federation.receipt_requirements must be a non-empty object")

    members = {member["project_id"]: member for member in federation["members"]}
    member_ids = set(members)
    requirement_ids = set(requirements)
    missing = sorted(requirement_ids - member_ids)
    extra = sorted(member_ids - requirement_ids)
    if missing:
        raise engine.ProofError(f"required federation project receipts missing: {missing}")
    if extra:
        raise engine.ProofError(f"unreviewed federation project receipts are not allowed: {extra}")

    observed_times: dict[str, datetime] = {}
    for pid, member in members.items():
        observed = _parse_time(member["observed_at"], f"federation member {pid}.observed_at")
        if now is not None and observed > now:
            raise engine.ProofError(f"federation member {pid}.observed_at cannot be in the future")
        observed_times[pid] = observed

    applied: list[dict[str, Any]] = []
    for pid, requirement in requirements.items():
        if not _text(pid) or not isinstance(requirement, dict):
            raise engine.ProofError("receipt_requirements entries need non-empty project ids and object requirements")
        member = members[pid]
        repository = requirement.get("repository")
        if not _text(repository):
            raise engine.ProofError(f"receipt requirement {pid}.repository is required")
        expected_repository = _repository_key(repository, f"receipt requirement {pid}.repository")
        actual_repository = _repository_key(member["repository"], f"federation member {pid}.repository")
        if actual_repository != expected_repository:
            raise engine.ProofError(
                f"receipt requirement {pid} repository mismatch: {member['repository']!r} != {repository!r}"
            )
        expected_scope = requirement.get("scope", {})
        if not isinstance(expected_scope, dict):
            raise engine.ProofError(f"receipt requirement {pid}.scope must be an object")
        actual_scope = member.get("scope", {})
        for key, expected in expected_scope.items():
            if actual_scope.get(key) != expected:
                raise engine.ProofError(
                    f"receipt requirement {pid} scope mismatch {key}={actual_scope.get(key)!r}, expected {expected!r}"
                )

        record = {"project_id": pid, "repository": repository, "scope": copy.deepcopy(expected_scope)}
        observed = observed_times[pid]
        max_receipt_age = requirement.get("max_receipt_age_hours")
        if max_receipt_age is not None:
            if envelope is None or now is None:
                raise engine.ProofError("receipt max-age enforcement requires envelope and evaluation time")
            max_receipt_age = _positive_hours(
                max_receipt_age,
                f"receipt requirement {pid}.max_receipt_age_hours",
            )
            deadline = observed + timedelta(hours=max_receipt_age)
            for item in envelope["evidence"]:
                source_project = item.get("source_project", {})
                if source_project.get("id") == pid:
                    _tighten_valid_until(item, deadline)
            record["max_receipt_age_hours"] = max_receipt_age
            record["receipt_valid_until"] = deadline.isoformat()
        applied.append(record)

    # Footnote: federation membership is contract-closed. Runtime evidence may supply
    # observations, but it cannot self-enroll a project identity or smuggle an extra
    # repository into cross-project reasoning. This is the federation analogue of
    # source applicability and preserves the reviewed authority boundary.
    return applied


def apply_causal_equivalence(spec: dict[str, Any], envelope: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply reviewed cross-project common-cause groups before engine evaluation."""
    cfg = federation_config(spec)
    groups = cfg.get("causal_equivalence", [])
    if not isinstance(groups, list):
        raise engine.ProofError("proofspec federation.causal_equivalence must be a list")

    evidence = {item["id"]: item for item in envelope["evidence"]}
    assigned: dict[str, str] = {}
    applied: list[dict[str, Any]] = []
    for i, group in enumerate(groups):
        if not isinstance(group, dict) or not _text(group.get("id")):
            raise engine.ProofError(f"causal_equivalence[{i}] needs a non-empty id")
        members = group.get("members")
        if not isinstance(members, list) or len(members) < 2 or not all(_text(member) for member in members):
            raise engine.ProofError(f"causal_equivalence[{i}].members must contain at least two evidence ids")
        if len(set(members)) != len(members):
            raise engine.ProofError(f"causal_equivalence[{i}] contains duplicate members")
        unknown = [member for member in members if member not in evidence]
        if unknown:
            raise engine.ProofError(f"causal_equivalence[{i}] unknown evidence ids: {unknown}")
        collisions = [member for member in members if member in assigned]
        if collisions:
            raise engine.ProofError(
                f"causal_equivalence[{i}] reassigns evidence already grouped by {[(m, assigned[m]) for m in collisions]}"
            )
        root = f"federation-cause{FEDERATION_DELIMITER}{group['id']}"
        for member in members:
            evidence[member]["causal_root"] = root
            assigned[member] = group["id"]
        applied.append({"id": group["id"], "members": list(members), "causal_root": root})

    # Footnote: common-cause equivalence changes the independence semantics used by
    # at_least.independent, so it lives in the reviewed proof contract and therefore
    # inside the proofspec digest. Runtime producers cannot self-award independence.
    return applied


def _rule_evidence_dependencies(
    rule: Any,
    claims: dict[str, dict[str, Any]],
    *,
    stack: tuple[str, ...] = (),
) -> set[str]:
    """Resolve one engine-valid rule to the primitive evidence ids it consumes."""

    # Footnote: Proof Spine has one rule grammar, not a validator-only superset.
    # Delegate parsing to the engine itself so decision-cut dependency analysis can
    # never bless nested/novel shapes that the evaluator would later reject.
    _kind, refs, _count, _independent = engine.rule(rule)
    out: set[str] = set()
    for ref in refs:
        claim = claims.get(ref)
        if claim is None:
            out.add(ref)
            continue
        if ref in stack:
            raise engine.ProofError(
                f"decision-cut dependency cycle through claim {ref!r}"
            )
        out.update(
            _rule_evidence_dependencies(
                claim.get("rule"),
                claims,
                stack=stack + (ref,),
            )
        )
    return out

def validate_decision_cuts(
    spec: dict[str, Any],
    envelope: dict[str, Any],
    cuts: Any,
    freshness_requirements: Any,
    *,
    label: str,
) -> list[dict[str, Any]]:
    """Prove that reviewed mutable-action cuts are actually wired into their gates."""
    if cuts in (None, []):
        return []
    if not isinstance(cuts, list):
        raise engine.ProofError(f"{label} must be a list")

    if freshness_requirements is None:
        freshness_requirements = {}
    if not isinstance(freshness_requirements, dict):
        raise engine.ProofError(f"{label} freshness requirements must be an object")

    claims = {
        item["id"]: item
        for item in spec.get("claims", [])
        if isinstance(item, dict) and _text(item.get("id"))
    }
    gates = {
        item["id"]: item
        for item in spec.get("gates", [])
        if isinstance(item, dict) and _text(item.get("id"))
    }
    available = {item["id"] for item in envelope.get("evidence", []) if isinstance(item, dict)}
    seen_ids: set[str] = set()
    seen_gates: set[str] = set()
    applied: list[dict[str, Any]] = []

    for index, cut in enumerate(cuts):
        if not isinstance(cut, dict) or not _text(cut.get("id")) or not _text(cut.get("gate_id")):
            raise engine.ProofError(f"{label}[{index}] requires non-empty id and gate_id")
        cid = cut["id"]
        gate_id = cut["gate_id"]
        if cid in seen_ids:
            raise engine.ProofError(f"duplicate decision cut id: {cid}")
        if gate_id in seen_gates:
            raise engine.ProofError(f"multiple decision cuts target gate {gate_id!r}; compose one coherent cut")
        seen_ids.add(cid)
        seen_gates.add(gate_id)

        gate = gates.get(gate_id)
        if gate is None:
            raise engine.ProofError(f"{label} references unknown gate: {gate_id}")

        required = cut.get("required_evidence")
        if (
            not isinstance(required, list)
            or not required
            or any(not _text(eid) for eid in required)
            or len(required) != len(set(required))
        ):
            raise engine.ProofError(f"{label}.{cid}.required_evidence must be a non-empty unique string list")
        stable = cut.get("stable_evidence", [])
        if (
            not isinstance(stable, list)
            or any(not _text(eid) for eid in stable)
            or len(stable) != len(set(stable))
        ):
            raise engine.ProofError(f"{label}.{cid}.stable_evidence must be a unique string list")
        if not set(stable) <= set(required):
            raise engine.ProofError(f"{label}.{cid}.stable_evidence must be a subset of required_evidence")

        missing_runtime = sorted(set(required) - available)
        if missing_runtime:
            # Footnote: a reviewed cut names the evidence surfaces that make the
            # decision current. Missing one is not "probably clear"; evaluation must
            # fail closed before the gate can masquerade as a complete lease.
            raise engine.ProofError(
                f"{label}.{cid} missing required runtime evidence: {missing_runtime}"
            )

        dependencies = _rule_evidence_dependencies(gate.get("rule"), claims)
        unwired = sorted(set(required) - dependencies)
        if unwired:
            # Footnote: decision_cuts are executable anti-omission contracts, not
            # comments. A required invalidator/check that does not transitively feed
            # the gate is rejected so a producer cannot report it while the decision
            # silently ignores it.
            raise engine.ProofError(
                f"{label}.{cid} required evidence is not wired into gate {gate_id!r}: {unwired}"
            )

        mutable = cut.get("mutable", True)
        if not isinstance(mutable, bool):
            raise engine.ProofError(f"{label}.{cid}.mutable must be boolean")
        unbounded = []
        if mutable:
            unbounded = sorted(
                eid for eid in dependencies
                if eid not in stable and eid not in freshness_requirements
            )
            if unbounded:
                # Footnote: OPEN is a lease on the complete causal surface that can
                # enable the gate, not only on the subset marked "required". This is
                # intentionally path-friendly: optional/alternative evidence need not
                # be present, but if it can participate in an OPEN decision it must be
                # governed by reviewed freshness when present. Otherwise an unlisted
                # alternative can become a zombie enabling path.
                raise engine.ProofError(
                    f"{label}.{cid} mutable gate evidence lacks reviewed freshness: {unbounded}"
                )

        applied.append(
            {
                "id": cid,
                "gate_id": gate_id,
                "required_evidence": list(required),
                "stable_evidence": list(stable),
                "mutable": mutable,
                "transitive_gate_evidence": sorted(dependencies),
                "freshness_bound": not bool(unbounded),
            }
        )
    return applied


def _bind_project_contract_context(spec: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    mission = spec.get("mission") or {}
    context = mission.get("context", {})
    if not isinstance(context, dict):
        raise engine.ProofError("proofspec mission.context must be an object")
    required_identity = {"project_id", "repository"}
    missing_identity = sorted(required_identity - set(context))
    if missing_identity:
        raise engine.ProofError(
            f"project-mode proofspec mission.context must bind project identity: missing {missing_identity}"
        )

    expected = project_context(receipt)
    for key, required in context.items():
        if key not in expected:
            raise engine.ProofError(f"proofspec context key {key!r} is absent from project receipt identity/scope")
        actual = expected[key]
        if key == "repository":
            if _repository_key(actual, "project receipt repository") != _repository_key(required, "proofspec context repository"):
                raise engine.ProofError(
                    f"proofspec context mismatch repository={required!r}, receipt has {actual!r}"
                )
        elif actual != required:
            raise engine.ProofError(
                f"proofspec context mismatch {key}={required!r}, receipt has {actual!r}"
            )

    # Footnote: project mode is contract-closed just like federation mode. A receipt may
    # report who it is, but the reviewed proof contract must independently name the
    # project/repository it intends to judge. Generic reusable templates should be
    # instantiated into a project-bound proofspec before evaluation.
    return context


def evaluate_project(spec: dict[str, Any], receipt: dict[str, Any], now: datetime, root: Path) -> dict[str, Any]:
    validate_project_receipt(receipt)
    receipt_observed = _parse_time(receipt["observed_at"], "project receipt observed_at")
    if receipt_observed > now:
        raise engine.ProofError("project receipt observed_at cannot be in the future")
    _bind_project_contract_context(spec, receipt)

    envelope = local_envelope(receipt)
    temporal_integrity = _apply_temporal_integrity(envelope, now)
    freshness = _apply_evidence_freshness_requirements(
        spec.get("freshness_requirements", {}),
        envelope,
        now,
        label="proofspec freshness_requirements",
    )
    decision_cuts = validate_decision_cuts(
        spec,
        envelope,
        spec.get("decision_cuts", []),
        spec.get("freshness_requirements", {}),
        label="proofspec decision_cuts",
    )
    report = engine.evaluate(spec, envelope, now, root)
    project_receipt_digest = engine.digest(receipt)
    decision_receipt = build_decision_receipt(
        mode="FCMO_PROOF_SPINE_PROJECT",
        spec=spec,
        source_evidence_digest=canonical_sha256(receipt),
        report=report,
        now=now,
        context={
            **project_context(receipt),
            # Footnote: evaluation time and source-observation time are different causal
            # facts. Calibration needs both so a post-outcome evaluator cannot turn old,
            # already-known project evidence into a nominally prospective decision merely
            # by running the universal gate after plan registration.
            "source_observed_at": receipt["observed_at"],
        },
    )
    return {
        "schema_version": 1,
        "mode": "FCMO_PROOF_SPINE_PROJECT",
        "project": receipt["project"],
        "scope": receipt.get("scope", {}),
        "observed_at": receipt["observed_at"],
        "project_receipt_digest": project_receipt_digest,
        "local_decisions": receipt.get("local_decisions", []),
        "temporal_integrity": temporal_integrity,
        "freshness_requirements": freshness,
        "decision_cuts": decision_cuts,
        "proofspec_digest": decision_receipt["proofspec_digest"],
        "effective_evidence_digest": report["evidence_digest"],
        "decision_receipt": decision_receipt,
        "decision_receipt_digest": canonical_sha256(decision_receipt),
        "proof_report": report,
        "claim_boundary": (
            "The universal adapter proves only deterministic consequences of the supplied project-owned evidence "
            "and reviewed proof contract. It does not replace project semantics, create promotion authority, or "
            "establish truth not present in the receipt."
        ),
    }


def evaluate_federation(spec: dict[str, Any], receipts: list[dict[str, Any]], now: datetime, root: Path) -> dict[str, Any]:
    envelope, federation = federated_envelope(receipts)

    # Footnote: capture the raw namespaced envelope before any proof-contract policy
    # mutates effective TTLs or causal roots. This keeps evidence identity independent
    # from the contract that judges it. The engine's evidence_digest below intentionally
    # describes the post-contract effective envelope used for evaluation.
    source_federated_evidence_digest = engine.digest(envelope)

    federation["receipt_requirements"] = validate_receipt_requirements(spec, federation, envelope, now)
    federation["temporal_integrity"] = _apply_temporal_integrity(envelope, now)
    federation["freshness_requirements"] = _apply_evidence_freshness_requirements(
        federation_config(spec).get("freshness_requirements", {}),
        envelope,
        now,
        label="proofspec federation.freshness_requirements",
    )
    federation["decision_cuts"] = validate_decision_cuts(
        spec,
        envelope,
        federation_config(spec).get("decision_cuts", []),
        federation_config(spec).get("freshness_requirements", {}),
        label="proofspec federation.decision_cuts",
    )
    federation["causal_equivalence"] = apply_causal_equivalence(spec, envelope)
    report = engine.evaluate(spec, envelope, now, root)
    decision_receipt = build_decision_receipt(
        mode="FCMO_PROOF_SPINE_FEDERATION",
        spec=spec,
        source_evidence_digest="sha256:" + source_federated_evidence_digest,
        report=report,
        now=now,
        context={"members": copy.deepcopy(federation["members"])},
    )
    return {
        "schema_version": 1,
        "mode": "FCMO_PROOF_SPINE_FEDERATION",
        "evaluated_at": now.isoformat(),
        "federation": federation,
        "federated_evidence_digest": source_federated_evidence_digest,
        "proofspec_digest": decision_receipt["proofspec_digest"],
        "effective_evidence_digest": report["evidence_digest"],
        "decision_receipt": decision_receipt,
        "decision_receipt_digest": canonical_sha256(decision_receipt),
        "proof_report": report,
        "claim_boundary": (
            "Federation namespaces project evidence and preserves project-owned truth semantics. Cross-project "
            "claims, gates, accepted receipt scopes, common-cause equivalence, and accepted freshness lifetimes "
            "exist only where the reviewed proof contract explicitly declares them; universal does not mean one "
            "global health score."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proofspec", type=Path)
    parser.add_argument("receipts", nargs="+", type=Path)
    parser.add_argument("--federation", action="store_true")
    parser.add_argument("--now")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        spec = json.loads(args.proofspec.read_text(encoding="utf-8"))
        receipts = [json.loads(path.read_text(encoding="utf-8")) for path in args.receipts]
        now = _parse_time(args.now, "evaluation time") if args.now else datetime.now(timezone.utc)
        if args.federation:
            result = evaluate_federation(spec, receipts, now, args.root.resolve())
        else:
            if len(receipts) != 1:
                raise engine.ProofError("project mode accepts exactly one receipt; use --federation for multiple")
            result = evaluate_project(spec, receipts[0], now, args.root.resolve())
    except (OSError, json.JSONDecodeError, ValueError, engine.ProofError) as exc:
        print(f"Proof Spine universal adapter error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = result["proof_report"]["summary"]
        print(f"MODE    {result['mode']}")
        print(f"OPEN    {', '.join(summary['open_gates']) or '-'}")
        print(f"CLOSED  {', '.join(summary['closed_gates']) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())