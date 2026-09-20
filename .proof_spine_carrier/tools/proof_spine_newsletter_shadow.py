#!/usr/bin/env python3
"""Adapt a Newsletter shadow receipt into the universal FCMO Proof Spine boundary.

Newsletter owns its health semantics. This file translates those local observations into
the common FCMO_PROOF_SPINE_PROJECT_RECEIPT shape, then delegates evaluation to the same
universal project layer used by every other FCMO domain. It never performs a production
action and is no longer a privileged engine path.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_SPEC = ROOT / "commons/experiments/2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_PROOFSPEC_v0.2b.json"
DEFAULT_CANDIDATE_SPEC = ROOT / "commons/experiments/2026-09-15_FCMO_PROOF_SPINE_NEWSLETTER_LOCALIZATION_PROOFSPEC_v0.2c.json"

ENGINE_SPEC = importlib.util.spec_from_file_location("proof_spine_v2_newsletter", HERE / "proof_spine_v2.py")
engine = importlib.util.module_from_spec(ENGINE_SPEC)
sys.modules[ENGINE_SPEC.name] = engine
ENGINE_SPEC.loader.exec_module(engine)

FEDERATION_SPEC = importlib.util.spec_from_file_location("proof_spine_federation", HERE / "proof_spine_federation.py")
federation = importlib.util.module_from_spec(FEDERATION_SPEC)
sys.modules[FEDERATION_SPEC.name] = federation
FEDERATION_SPEC.loader.exec_module(federation)

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"

# Footnote for future maintainers: this file is intentionally only a project adapter.
# Generic evidence authority, project/federation namespacing, and state propagation live
# in proof_spine_federation.py + proof_spine_v2.py. Newsletter-specific semantics stay
# here or in the Newsletter repository; they must not leak into the shared core.


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise engine.ProofError("shadow receipt timestamps must include timezone")
    return dt.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value is not None else None


def check_item(receipt: dict[str, Any], name: str) -> dict[str, Any] | None:
    checks = receipt.get("checks")
    if not isinstance(checks, dict) or not isinstance(checks.get(name), dict):
        return None
    return checks[name]


def check_status(receipt: dict[str, Any], name: str) -> str:
    item = check_item(receipt, name)
    status = item.get("status") if item else None
    return status if status in {PASS, FAIL, UNKNOWN} else UNKNOWN


def alignment_state(receipt: dict[str, Any]) -> str:
    alignment = receipt.get("source_alignment")
    state = alignment.get("state") if isinstance(alignment, dict) else None
    return state if state in {"MATCH", "DRIFTED", "UNKNOWN", "CHANGED_DURING_OBSERVATION"} else "UNKNOWN"


def alignment_status(receipt: dict[str, Any]) -> str:
    state = alignment_state(receipt)
    if state == "MATCH":
        return PASS
    if state == "DRIFTED":
        return FAIL
    return UNKNOWN


def supported_receipt(receipt: dict[str, Any]) -> bool:
    """Accept the historical live-health receipt plus the v2 pre-action extension."""
    schema = receipt.get("schema_version")
    kind = receipt.get("kind")
    return (schema, kind) in {
        (1, "FCMO_NEWSLETTER_PRODUCTION_HEALTH_SHADOW_RECEIPT"),
        (2, "FCMO_NEWSLETTER_PROOF_SPINE_SHADOW_RECEIPT"),
    }


def candidate_localization_status(receipt: dict[str, Any]) -> str:
    """Map only source-aligned Newsletter candidate coverage into evidence status."""
    if receipt.get("schema_version") != 2 or receipt.get("kind") != "FCMO_NEWSLETTER_PROOF_SPINE_SHADOW_RECEIPT":
        return UNKNOWN
    if alignment_state(receipt) != "MATCH":
        return UNKNOWN

    candidate = receipt.get("candidate_release")
    source = receipt.get("source")
    if not isinstance(candidate, dict) or not isinstance(source, dict):
        return UNKNOWN
    candidate_sha = candidate.get("candidate_source_sha")
    main_sha = source.get("main_sha_at_observation")
    if not isinstance(candidate_sha, str) or not candidate_sha or candidate_sha != main_sha:
        return UNKNOWN

    native = candidate.get("native_edition_observation")
    state = native.get("state") if isinstance(native, dict) else None
    if state == "COMPLETE":
        return PASS
    if state == "INCOMPLETE_NATIVE_EDITIONS":
        return FAIL
    return UNKNOWN


def candidate_localization_source(receipt: dict[str, Any]) -> dict[str, Any] | None:
    candidate = receipt.get("candidate_release")
    native = candidate.get("native_edition_observation") if isinstance(candidate, dict) else None
    if not isinstance(native, dict):
        return None
    # Footnote: retain only public-safe producer facts in the normalized evidence. The
    # producer does not supply a Proof Spine gate or authority decision; it supplies the
    # exact project-local observation that the reviewed Hub contract will compose.
    return {
        "candidate_source_sha": candidate.get("candidate_source_sha"),
        "state": native.get("state"),
        "canonical_story_count": native.get("canonical_story_count"),
        "native_complete_story_count": native.get("native_complete_story_count"),
        "pending_translation_count": native.get("pending_translation_count"),
        "pending_translation_ids": native.get("pending_translation_ids"),
        "required_locales": native.get("required_locales"),
        "source_oracle": native.get("source_oracle"),
        "canonical_contract": native.get("canonical_contract"),
    }


def upstream_publication_state(receipt: dict[str, Any]) -> str:
    upstream = receipt.get("upstream_publication")
    state = upstream.get("state") if isinstance(upstream, dict) else None
    allowed = {"MATCH", "MATERIAL_PUBLIC_DELTA_AVAILABLE", "NON_MATERIAL_PUBLIC_DELTA", "UNKNOWN"}
    return state if state in allowed else "UNKNOWN"


def upstream_material_sync_status(receipt: dict[str, Any]) -> str:
    """Map only material public-publication lag into the shared evidence state."""
    state = upstream_publication_state(receipt)
    if state in {"MATCH", "NON_MATERIAL_PUBLIC_DELTA"}:
        return PASS
    if state == "MATERIAL_PUBLIC_DELTA_AVAILABLE":
        return FAIL
    return UNKNOWN


def editorial_status(receipt: dict[str, Any]) -> str:
    """Preserve stage-local causality when the composite editorial check fails."""
    item = check_item(receipt, "editorial_freshness")
    status = check_status(receipt, "editorial_freshness")
    if status != FAIL or item is None:
        return status
    structured = item.get("structured_output")
    stage = structured.get("stage") if isinstance(structured, dict) else None
    if stage == "AIRLOCK":
        # Footnote: the local editorial checker intentionally checks Airlock first.
        # If that prerequisite fails, it has not established an independent editorial
        # failure. Export UNKNOWN here and let Airlock carry the positive causal fault.
        return UNKNOWN
    return FAIL


def combine_status(*statuses: str) -> str:
    if FAIL in statuses:
        return FAIL
    if UNKNOWN in statuses:
        return UNKNOWN
    return PASS


def strict_deadline(timestamp: Any, hours: float) -> str | None:
    dt = parse_time(timestamp)
    if dt is None:
        return None
    # Footnote: Newsletter fails on age > threshold while generic Proof Spine expires
    # at now >= valid_until. One microsecond preserves the exact local boundary.
    return iso(dt + timedelta(hours=hours, microseconds=1))


def editorial_acceptability_deadline(receipt: dict[str, Any]) -> str | None:
    facts = receipt.get("source_facts") or {}
    candidates = [
        parse_time(strict_deadline(facts.get("newsroom_finalized_at"), 30)),
        parse_time(strict_deadline((facts.get("newest_material") or {}).get("timestamp"), 48)),
        parse_time(strict_deadline((facts.get("lead") or {}).get("timestamp"), 48)),
    ]
    live = [item for item in candidates if item is not None]
    # Footnote: Airlock is deliberately absent; it owns a separate causal node/deadline.
    return iso(min(live)) if live else None


def next_quality_transition(receipt: dict[str, Any]) -> str | None:
    local = receipt.get("local_surface") or {}
    if local.get("quality_state") != "HEALTHY" or alignment_state(receipt) != "MATCH":
        return None
    facts = receipt.get("source_facts") or {}
    # Footnote: 24h is Newsletter's quality lane, not the hard acceptability gate.
    return strict_deadline((facts.get("lead") or {}).get("timestamp"), 24)


def ev(eid: str, status: str, root: str, *, valid_until: str | None = None, source: dict[str, Any] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"id": eid, "status": status, "causal_root": root}
    if valid_until:
        item["valid_until"] = valid_until
    if source:
        item["source_receipt"] = source
    return item


def build_envelope(receipt: dict[str, Any]) -> dict[str, Any]:
    """Legacy helper retained for regression tests; returns engine-shaped evidence."""
    if not supported_receipt(receipt):
        raise engine.ProofError("unsupported Newsletter shadow receipt schema/kind")

    source = receipt.get("source") if isinstance(receipt.get("source"), dict) else {}
    run_root = f"newsletter-shadow-run:{source.get('workflow_run_id') or source.get('head_sha') or 'unknown'}"
    facts = receipt.get("source_facts") if isinstance(receipt.get("source_facts"), dict) else {}

    alignment = alignment_status(receipt)
    serving = combine_status(check_status(receipt, "serving_health"), check_status(receipt, "surface_oracle"))
    publication = check_status(receipt, "publication_freshness")
    editorial = editorial_status(receipt)
    translation = check_status(receipt, "translation_health")
    upstream_sync = upstream_material_sync_status(receipt)
    candidate_localization = candidate_localization_status(receipt)

    editorial_until = editorial_acceptability_deadline(receipt) if editorial == PASS else None
    airlock_until = strict_deadline(facts.get("airlock_generated_at"), 30) if publication == PASS else None

    evidence = [
        # Footnote: a live-health heartbeat does not attest the independent upstream,
        # six-gate, authority, or post-deploy portions of a candidate transaction.
        ev("candidate_arb_public_safe", UNKNOWN, f"{run_root}:candidate-not-observed"),
        ev("candidate_six_release_gates", UNKNOWN, f"{run_root}:candidate-not-observed"),
        ev("publication_authority", UNKNOWN, f"{run_root}:candidate-not-observed"),
        # Footnote: v2 receipts may observe native-edition completeness *before* a
        # future Pages action. This one premise becomes PASS/FAIL only when the producer
        # proved material inputs matched stable current main; drift stays UNKNOWN.
        ev(
            "candidate_localization_ready",
            candidate_localization,
            f"{run_root}:candidate-localization",
            source=candidate_localization_source(receipt),
        ),
        ev("candidate_pages_deploy", UNKNOWN, f"{run_root}:candidate-not-observed"),
        ev("candidate_post_deploy_browser", UNKNOWN, f"{run_root}:candidate-not-observed"),
        ev("candidate_triggered_health", UNKNOWN, f"{run_root}:candidate-not-observed"),
        ev("live_source_alignment", alignment, f"{run_root}:source-alignment"),
        ev("live_serving_probe", serving, f"{run_root}:serving+surface"),
        ev("live_airlock_freshness", publication, f"{run_root}:publication-freshness", valid_until=airlock_until),
        ev("live_editorial_freshness", editorial, f"{run_root}:editorial-freshness", valid_until=editorial_until),
        ev("live_translation_health", translation, f"{run_root}:translation-health"),
        # Footnote: material upstream sync is separate from current live health.
        ev("live_upstream_material_sync", upstream_sync, f"{run_root}:upstream-publication-sync"),
    ]
    return {"schema_version": 2, "evidence": evidence}


def build_project_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Translate Newsletter-local evidence into the universal FCMO receipt contract."""
    envelope = build_envelope(receipt)
    source = receipt.get("source") if isinstance(receipt.get("source"), dict) else {}
    local = receipt.get("local_surface") if isinstance(receipt.get("local_surface"), dict) else {}
    candidate = receipt.get("candidate_release") if isinstance(receipt.get("candidate_release"), dict) else {}
    # Footnote: a v2 source-aligned receipt is about current Newsletter main, not the
    # experiment branch commit that carried the adapter. Bind project scope to the
    # candidate SHA when the producer proved that exact applicability; legacy receipts
    # retain their historical branch-head identity.
    source_head_sha = candidate.get("candidate_source_sha") or source.get("head_sha")
    producer_scope = {
        key: source[key]
        for key in (
            "producer_id",
            "producer_contract_digest",
            "workflow_run_id",
            "workflow_run_attempt",
        )
        if isinstance(source.get(key), str) and source.get(key)
    }
    return {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_PROJECT_RECEIPT",
        "authority": "EVIDENCE_ONLY",
        "project": {"id": "newsletter", "repository": "FCMO-AI/FCMO-AI-Newsletter"},
        "observed_at": receipt.get("observed_at"),
        "scope": {
            "environment": "production",
            "product": "FCMO-AI-Newsletter",
            "source_head_sha": source_head_sha,
            # Footnote: source_sha is a stable cross-layer subject key used by
            # calibration cases. Keep the historical source_head_sha spelling too so
            # existing consumers do not regress while exact decision receipts gain a
            # generic identity overlap with project-local adjudication subjects.
            "source_sha": source_head_sha,
            # Footnote: prospective calibration may preregister the exact field
            # producer implementation. Carry producer identity through only when the
            # Newsletter receipt supplied it; historical receipts remain byte-shape
            # compatible at the project boundary without inventing missing provenance.
            **producer_scope,
        },
        "evidence": envelope["evidence"],
        "local_decisions": [
            {
                "id": "newsletter_local_health",
                "state": local.get("state", "UNKNOWN"),
                "quality_state": local.get("quality_state"),
            }
        ],
        "claim_boundary": (
            "Newsletter owns the semantics that produced these observations. This normalized receipt is evidence-only "
            "and grants no publication, deployment, release, rollback, or health-redefinition authority."
        ),
    }


def classify(local_state: str, gate: dict[str, Any], source_alignment: str) -> str:
    open_gate = gate.get("state") == "OPEN"
    proof_state = gate.get("proof_state")
    if local_state == "UNKNOWN" and source_alignment == "DRIFTED" and not open_gate:
        return "AGREE_SOURCE_DRIFT"
    if local_state == "HEALTHY" and open_gate:
        return "AGREE_HEALTHY"
    if local_state == "UNHEALTHY" and not open_gate:
        return "AGREE_UNHEALTHY"
    if local_state == "UNKNOWN" and not open_gate and proof_state == "UNKNOWN":
        return "AGREE_UNPROVEN"
    if local_state == "HEALTHY" and not open_gate:
        return "PROOF_SPINE_STRICTER"
    if local_state == "UNHEALTHY" and open_gate:
        return "PROOF_SPINE_LOOSER_DANGER"
    if local_state == "UNKNOWN" and open_gate:
        return "PROOF_SPINE_MORE_ASSERTIVE"
    return "DIVERGENCE_REVIEW"


def classify_upstream(gate: dict[str, Any]) -> str:
    if gate.get("state") == "OPEN" and gate.get("proof_state") == "VALID":
        return "UPSTREAM_MATERIAL_SYNCED"
    if gate.get("proof_state") == "INVALID":
        return "UPSTREAM_MATERIAL_LAG"
    return "UPSTREAM_SYNC_UNKNOWN"


def classify_predeploy(gate: dict[str, Any]) -> str:
    if gate.get("state") == "OPEN" and gate.get("proof_state") == "VALID":
        return "CANDIDATE_WOULD_PASS_PREDEPLOY_PROOF"
    if gate.get("proof_state") == "INVALID":
        return "CANDIDATE_WOULD_BE_BLOCKED_INVALID"
    return "CANDIDATE_WOULD_BE_BLOCKED_UNPROVEN"


def evaluate_shadow(
    spec: dict[str, Any],
    receipt: dict[str, Any],
    now: datetime,
    root: Path,
    candidate_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    project_receipt = build_project_receipt(receipt)
    universal = federation.evaluate_project(spec, project_receipt, now, root)
    report = universal["proof_report"]
    live_gate = report["gates"]["represent_live_production_healthy"]
    upstream_gate = report["gates"]["represent_live_upstream_material_synced"]

    # Footnote: candidate deploy eligibility is a different causal question from live
    # production health. Evaluate the reviewed pre-deploy contract separately over the
    # same evidence-only project receipt so a candidate failure cannot poison the live
    # branch and a healthy live site cannot launder the candidate into readiness.
    if candidate_spec is None:
        candidate_spec = json.loads(DEFAULT_CANDIDATE_SPEC.read_text(encoding="utf-8"))
    candidate_universal = federation.evaluate_project(candidate_spec, project_receipt, now, root)
    candidate_report = candidate_universal["proof_report"]
    predeploy_gate = candidate_report["gates"]["candidate_may_enter_deploy"]

    local = receipt.get("local_surface") if isinstance(receipt.get("local_surface"), dict) else {}
    local_state = local.get("state") if local.get("state") in {"HEALTHY", "UNHEALTHY", "UNKNOWN"} else "UNKNOWN"
    alignment = alignment_state(receipt)

    return {
        "schema_version": 2,
        "mode": "NEWSLETTER_PROSPECTIVE_SHADOW_VIA_FCMO_PROJECT_RECEIPT",
        "observed_at": receipt.get("observed_at"),
        "source": receipt.get("source"),
        "source_alignment": receipt.get("source_alignment"),
        "upstream_publication": receipt.get("upstream_publication"),
        "candidate_release": receipt.get("candidate_release"),
        "local_surface": local,
        "universal_project_receipt_digest": universal["project_receipt_digest"],
        "proof_spine_live_decision_receipt": universal["decision_receipt"],
        "proof_spine_live_decision_receipt_digest": universal["decision_receipt_digest"],
        "proof_spine_live_gate": live_gate,
        "comparison": classify(local_state, live_gate, alignment),
        "upstream_material_sync_gate": upstream_gate,
        "upstream_material_sync_signal": classify_upstream(upstream_gate),
        "proof_spine_predeploy_gate": predeploy_gate,
        "proof_spine_predeploy_signal": classify_predeploy(predeploy_gate),
        "proof_spine_predeploy_decision_receipt": candidate_universal["decision_receipt"],
        "proof_spine_predeploy_decision_receipt_digest": candidate_universal["decision_receipt_digest"],
        "candidate_proof_report": candidate_report,
        "next_quality_transition_at": next_quality_transition(receipt),
        "proof_spine_next_gate_recheck_at": report["temporal"]["next_gate_recheck_at"],
        "candidate_gate_observational_only": report["gates"]["advance_candidate_current_edition"],
        "proof_report": report,
        "claim_boundary": (
            "This is a project-local shadow comparison transported through the universal FCMO evidence receipt. "
            "Agreement, divergence, lag, or a pre-deploy WOULD_BLOCK result creates no Newsletter publication/deployment "
            "authority and does not rewrite project-local health or release semantics. Exact universal decision receipts "
            "are carried through for audit/calibration evidence only; exposing them grants no new action authority."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--proofspec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--candidate-proofspec", type=Path, default=DEFAULT_CANDIDATE_SPEC)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        spec = json.loads(args.proofspec.read_text(encoding="utf-8"))
        candidate_spec = json.loads(args.candidate_proofspec.read_text(encoding="utf-8"))
        now = parse_time(args.now) if args.now else parse_time(receipt.get("observed_at")) or datetime.now(timezone.utc)
        report = evaluate_shadow(spec, receipt, now, args.root.resolve(), candidate_spec)
    except (OSError, json.JSONDecodeError, ValueError, engine.ProofError, federation.engine.ProofError) as exc:
        print(f"Newsletter shadow evaluation error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"SHADOW   {report['comparison']}")
        print(f"LOCAL    {report['local_surface'].get('state')} / {report['local_surface'].get('quality_state')}")
        print(f"SOURCE   {alignment_state(receipt)}")
        gate = report["proof_spine_live_gate"]
        print(f"PROOF    {gate['state']} ({gate['proof_state']})")
        print(f"UPSTREAM {report['upstream_material_sync_signal']}")
        predeploy = report["proof_spine_predeploy_gate"]
        print(f"PREDEPLOY {report['proof_spine_predeploy_signal']} — {predeploy['state']} ({predeploy['proof_state']})")
        if report["next_quality_transition_at"]:
            print(f"QUALITY  next deterministic transition at {report['next_quality_transition_at']}")
        if report["proof_spine_next_gate_recheck_at"]:
            print(f"RECHECK  gate deadline at {report['proof_spine_next_gate_recheck_at']}")

    # Footnote: divergence remains evidence, not enforcement, during the pilot.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
