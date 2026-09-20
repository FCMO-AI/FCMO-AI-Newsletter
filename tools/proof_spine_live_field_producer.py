#!/usr/bin/env python3
"""Emit one preregisterable Newsletter live-health Proof Spine field event.

This producer is evidence-only. It runs Newsletter-owned observational checks, binds the
result to an exact copied Hub proof contract, and emits a universal decision receipt.
It never deploys, publishes, merges, rolls back, or changes Newsletter production state.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIELD_ROOT = ROOT / ".proof_spine_field"
MANIFEST_PATH = FIELD_ROOT / "FIELD_PRODUCER_MANIFEST.json"
PROOFSPEC_PATH = (
    FIELD_ROOT
    / "commons/experiments/2026-09-14_FCMO_PROOF_SPINE_NEWSLETTER_PROOFSPEC_v0.2b.json"
)
HUB_ADAPTER_PATH = FIELD_ROOT / "tools/proof_spine_newsletter_shadow.py"
PRODUCER_ID = "newsletter-proof-spine-live-field-v0.3i"
GATE_ID = "represent_live_production_healthy"

import proof_spine_preaction_shadow_receipt as newsletter_source


class ProducerError(RuntimeError):
    pass


def canonical_sha256(payload: Any) -> str:
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise ProducerError(
            "git " + " ".join(args) + " failed: "
            + (result.stderr.strip() or result.stdout.strip())
        )
    return result.stdout.strip()


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProducerError(f"producer manifest unavailable or invalid: {exc}") from exc
    if (
        manifest.get("schema_version") != 1
        or manifest.get("kind") != "FCMO_PROOF_SPINE_FIELD_PRODUCER_CONTRACT"
        or manifest.get("authority") != "NON_NORMATIVE_EVIDENCE"
        or manifest.get("producer_id") != PRODUCER_ID
    ):
        raise ProducerError("producer manifest schema/kind/authority/id mismatch")
    return manifest


def verify_manifest(manifest: dict[str, Any]) -> str:
    expected_branch = manifest.get("branch")
    if os.getenv("GITHUB_REF_NAME") != expected_branch:
        raise ProducerError(
            f"producer branch mismatch: {os.getenv('GITHUB_REF_NAME')!r} != {expected_branch!r}"
        )

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ProducerError("producer manifest requires a non-empty files map")
    for path, record in sorted(files.items()):
        if not isinstance(record, dict):
            raise ProducerError(f"manifest file record is not an object: {path}")
        expected = record.get("git_blob_sha")
        if not isinstance(expected, str) or len(expected) != 40:
            raise ProducerError(f"manifest git_blob_sha invalid: {path}")
        actual = git_output("rev-parse", f"HEAD:{path}")
        if actual != expected:
            raise ProducerError(
                f"producer byte identity mismatch for {path}: {actual} != {expected}"
            )

    # Footnote: the manifest intentionally excludes its own digest to avoid a circular
    # hash. The calibration plan preregisters this canonical digest, while this runtime
    # independently verifies every behavior-bearing file named by the manifest.
    return canonical_sha256(manifest)


def load_hub_adapter():
    spec = importlib.util.spec_from_file_location(
        "proof_spine_newsletter_field_adapter", HUB_ADAPTER_PATH
    )
    if spec is None or spec.loader is None:
        raise ProducerError("could not load pinned Hub Newsletter adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    run_id = os.getenv("GITHUB_RUN_ID")
    run_attempt = os.getenv("GITHUB_RUN_ATTEMPT")
    if not run_id or not run_attempt:
        raise ProducerError("GitHub Actions run identity is required for a field event")
    source_event_id = f"github-actions-run:{run_id}"

    manifest = load_manifest()
    producer_contract_digest = verify_manifest(manifest)
    proofspec = json.loads(PROOFSPEC_PATH.read_text(encoding="utf-8"))
    proofspec_digest = canonical_sha256(proofspec)
    if proofspec_digest != manifest.get("proofspec_digest"):
        raise ProducerError(
            "pinned proofspec bytes disagree with producer manifest proofspec_digest"
        )

    # Footnote: the Newsletter producer owns observations, not Proof Spine verdicts.
    # Its checks are executed first; producer identity is appended only after the
    # observation exists, then the pinned Hub adapter translates those exact facts.
    receipt = newsletter_source.build_receipt(upstream_seal_state="NOT_OBSERVED")
    source = receipt.get("source")
    if not isinstance(source, dict):
        raise ProducerError("Newsletter source receipt did not expose source identity")
    source["producer_id"] = PRODUCER_ID
    source["producer_contract_digest"] = producer_contract_digest
    source["source_event_id"] = source_event_id
    source["workflow_run_id"] = run_id
    source["workflow_run_attempt"] = run_attempt

    hub_adapter = load_hub_adapter()
    project_receipt = hub_adapter.build_project_receipt(receipt)
    evaluated_at = datetime.now(timezone.utc)
    evaluated = hub_adapter.federation.evaluate_project(
        proofspec,
        project_receipt,
        evaluated_at,
        FIELD_ROOT,
    )
    decision_receipt = evaluated["decision_receipt"]
    decision_digest = evaluated["decision_receipt_digest"]
    gate = evaluated["proof_report"]["gates"].get(GATE_ID)
    if not isinstance(gate, dict):
        raise ProducerError(f"pinned proofspec did not emit gate {GATE_ID}")

    context = decision_receipt.get("context") or {}
    for key, expected in {
        "producer_id": PRODUCER_ID,
        "producer_contract_digest": producer_contract_digest,
        "source_event_id": source_event_id,
        "workflow_run_id": run_id,
        "workflow_run_attempt": run_attempt,
        "source_observed_at": receipt.get("observed_at"),
    }.items():
        if context.get(key) != expected:
            raise ProducerError(
                f"decision receipt context lost {key}: {context.get(key)!r} != {expected!r}"
            )

    event = {
        "schema_version": 1,
        "kind": "FCMO_PROOF_SPINE_SOURCE_PRODUCER_EVENT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "source_event_id": source_event_id,
        "state": "DECISION_RECEIPT_EMITTED",
        "producer_id": PRODUCER_ID,
        "producer_contract_digest": producer_contract_digest,
        "repository": "FCMO-AI/FCMO-AI-Newsletter",
        "branch": os.getenv("GITHUB_REF_NAME"),
        "workflow_run_id": run_id,
        "workflow_run_attempt": run_attempt,
        "source_sha": context.get("source_sha"),
        "source_observed_at": context.get("source_observed_at"),
        "evaluated_at": decision_receipt.get("evaluated_at"),
        "proofspec_digest": decision_receipt.get("proofspec_digest"),
        "gate_id": GATE_ID,
        "gate_state": gate.get("state"),
        "gate_proof_state": gate.get("proof_state"),
        "decision_receipt_digest": decision_digest,
        "claim_boundary": (
            "This event proves only that the preregisterable evidence-only field producer "
            "executed Newsletter-owned observations and the pinned Proof Spine gate. It "
            "creates no publication, deployment, rollback, merge, or health authority."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "newsletter_source_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "proof_spine_project_receipt.json").write_text(
        json.dumps(project_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "proof_spine_decision_receipt.json").write_text(
        json.dumps(decision_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "field_event.json").write_text(
        json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "FCMO_FIELD_EVENT_JSON="
        + json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ProducerError) as exc:
        print(f"Proof Spine live field producer error: {exc}", file=sys.stderr)
        raise SystemExit(2)
