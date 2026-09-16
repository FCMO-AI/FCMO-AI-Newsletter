#!/usr/bin/env python3
"""Emit a pre-action Newsletter candidate receipt for Proof Spine shadow evaluation.

This file deliberately does not contain a Proof Spine graph, gate, promotion rule, or
production action. It reuses the existing public-safe shadow producer and Newsletter's
own localization-integrity machinery, then records whether the *current main candidate*
has complete native Story identities before a future Pages action has a chance to run.

The receipt is observational. An incomplete candidate is evidence for a separate
reviewed contract; this script itself never blocks, deploys, publishes, rolls back,
merges, dispatches, or changes production state.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import proof_spine_shadow_receipt as base

ROOT = Path(__file__).resolve().parents[1]

# Footnote for future maintainers: the original live-health adapter only needed the
# files that determine current serving/health truth. Candidate-release applicability
# additionally depends on the canonical localization contract, frozen candidate source,
# and the validator that measures native-edition coverage. Extend the *applicability*
# envelope instead of pretending a green stale branch can describe current main.
CANDIDATE_INPUTS = (
    "LOCALIZATION.md",
    "release-src",
    "tools/validate_localizations_partial.py",
)
base.MATERIAL_INPUTS = tuple(dict.fromkeys((*base.MATERIAL_INPUTS, *CANDIDATE_INPUTS)))


def classify_integrity_receipt(doc: Any) -> dict[str, Any]:
    """Normalize project-native localization facts without inventing release authority."""
    if not isinstance(doc, dict) or doc.get("schema") != "fcmo-locale-integrity-v3":
        return {
            "state": "UNKNOWN",
            "reason": "localization integrity receipt missing or schema-invalid",
        }

    pending = doc.get("pending_translation_count")
    pending_ids = doc.get("pending_translation_ids")
    canonical = doc.get("canonical_story_count")
    complete = doc.get("native_complete_story_count")
    if (
        not isinstance(pending, int)
        or pending < 0
        or not isinstance(pending_ids, list)
        or len(pending_ids) != pending
        or not isinstance(canonical, int)
        or canonical < 0
        or not isinstance(complete, int)
        or complete < 0
        or complete + pending != canonical
    ):
        return {
            "state": "UNKNOWN",
            "reason": "localization integrity receipt has inconsistent coverage counts",
        }

    # Footnote: COMPLETE/INCOMPLETE_NATIVE_EDITIONS are observations of the local
    # publication obligation, not Proof Spine VALID/INVALID states. The private Hub
    # contract decides how these facts compose with other independent prerequisites.
    return {
        "state": "COMPLETE" if pending == 0 else "INCOMPLETE_NATIVE_EDITIONS",
        "validator_state": doc.get("state"),
        "canonical_story_count": canonical,
        "native_complete_story_count": complete,
        "pending_translation_count": pending,
        "pending_translation_ids": [str(value) for value in pending_ids],
        "required_locales": doc.get("required_locales"),
        "network_translation": doc.get("network_translation"),
        "human_reviewed": doc.get("human_reviewed"),
        "reason": (
            "every canonical Story identity has both required native editions"
            if pending == 0
            else "one or more canonical Story identities lack required native editions"
        ),
    }


def candidate_localization_observation() -> dict[str, Any]:
    """Run the existing project validator into an ephemeral receipt and normalize it."""
    with tempfile.TemporaryDirectory(prefix="fcmo-proof-spine-candidate-") as tmp:
        receipt_path = Path(tmp) / "localization-integrity.json"
        command = [
            sys.executable,
            "tools/validate_localizations_partial.py",
            "--site",
            "release-src",
            "--i18n-dir",
            "site/data/i18n",
            "--receipt",
            str(receipt_path),
        ]
        started = base.utc_now()
        result = base.run_command(command)
        finished = base.utc_now()
        if result is None:
            return {
                "execution_state": "UNKNOWN",
                "state": "UNKNOWN",
                "command": command,
                "started_at": base.iso(started),
                "finished_at": base.iso(finished),
                "reason": "candidate localization validator did not execute",
            }
        if result.returncode != 0 or not receipt_path.is_file():
            return {
                "execution_state": "EXECUTED",
                "state": "UNKNOWN",
                "return_code": result.returncode,
                "command": command,
                "started_at": base.iso(started),
                "finished_at": base.iso(finished),
                "stdout_tail": base.tail(result.stdout.strip()),
                "stderr_tail": base.tail(result.stderr.strip()),
                "reason": "candidate localization validator failed before producing a trustworthy coverage receipt",
            }
        try:
            doc = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "execution_state": "EXECUTED",
                "state": "UNKNOWN",
                "return_code": result.returncode,
                "command": command,
                "started_at": base.iso(started),
                "finished_at": base.iso(finished),
                "reason": f"candidate localization receipt could not be decoded: {exc}",
            }

    normalized = classify_integrity_receipt(doc)
    normalized.update(
        {
            "execution_state": "EXECUTED",
            "return_code": result.returncode,
            "command": command,
            "started_at": base.iso(started),
            "finished_at": base.iso(finished),
            "stdout_tail": base.tail(result.stdout.strip()),
            "stderr_tail": base.tail(result.stderr.strip()),
            "source_oracle": "tools/validate_localizations_partial.py",
            "canonical_contract": "LOCALIZATION.md",
        }
    )
    return normalized


def build_receipt(
    *,
    upstream_release: Path | None = None,
    upstream_seal_state: str = "NOT_OBSERVED",
) -> dict[str, Any]:
    """Build one bracketed receipt covering live health and current-main candidate facts."""
    alignment_before = base.alignment_snapshot()
    checks = {name: base.run_check(name, command) for name, command in base.CHECKS}
    facts = base.source_facts()
    upstream = base.upstream_publication_observation(upstream_release, upstream_seal_state)
    candidate_localization = candidate_localization_observation()
    alignment_after = base.alignment_snapshot()
    alignment = base.source_alignment(alignment_before, alignment_after)
    observed_at = base.utc_now()

    statuses = [item["status"] for item in checks.values()]
    if alignment["state"] != "MATCH" or "UNKNOWN" in statuses:
        local_state = "UNKNOWN"
    elif "FAIL" in statuses:
        local_state = "UNHEALTHY"
    else:
        local_state = "HEALTHY"

    editorial_state = ((checks["editorial_freshness"].get("structured_output") or {}).get("state"))
    quality_state = editorial_state if local_state == "HEALTHY" and editorial_state else local_state
    current_main_sha = alignment_after.get("main_sha") if alignment.get("state") == "MATCH" else None

    return {
        "schema_version": 2,
        "kind": "FCMO_NEWSLETTER_PROOF_SPINE_SHADOW_RECEIPT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "observed_at": base.iso(observed_at),
        "source": {
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "head_sha": base.git_head(),
            "branch": os.getenv("GITHUB_REF_NAME"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
            "main_sha_at_observation": alignment_after.get("main_sha"),
        },
        "source_alignment": alignment,
        "local_surface": {
            "state": local_state,
            "quality_state": quality_state,
            "derivation": (
                "HEALTHY only when declared material inputs match stable current main and every exported Newsletter-local live check executes and passes; "
                "source drift/execution uncertainty yields UNKNOWN rather than stale health certainty"
            ),
        },
        "source_facts": facts,
        "upstream_publication": upstream,
        "candidate_release": {
            "candidate_source_sha": current_main_sha,
            "scope": "current Newsletter main candidate represented by this source-aligned checkout",
            "native_edition_observation": candidate_localization,
            "six_release_gates": {
                "state": "NOT_OBSERVED",
                "reason": "this receipt does not substitute candidate localization facts for the independent six-gate release contract",
            },
            "publication_authority": {
                "state": "NOT_OBSERVED",
                "reason": "this evidence adapter never manufactures publication authority",
            },
            "claim_boundary": (
                "Candidate localization completeness is an observation from Newsletter-owned files and validator semantics. "
                "It is not a deploy decision and does not prove unrelated release prerequisites."
            ),
        },
        "checks": checks,
        "claim_boundary": (
            "This v2 receipt records public-safe Newsletter-local live observations, current-main applicability, sanitized ARB-publication synchronization, "
            "and candidate native-edition coverage. It declares no Proof Spine mission, claims, gates, publication authority, or production action."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--upstream-release", type=Path)
    parser.add_argument(
        "--upstream-seal-state",
        default="NOT_OBSERVED",
        choices=("SEALED", "CURRENT_MAIN_UNSEALABLE", "NOT_OBSERVED", "UNKNOWN"),
    )
    args = parser.parse_args()

    receipt = build_receipt(
        upstream_release=args.upstream_release,
        upstream_seal_state=args.upstream_seal_state,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate = receipt["candidate_release"]["native_edition_observation"]
    print(
        json.dumps(
            {
                "state": receipt["local_surface"]["state"],
                "quality_state": receipt["local_surface"]["quality_state"],
                "source_alignment": receipt["source_alignment"]["state"],
                "upstream_publication": receipt["upstream_publication"]["state"],
                "candidate_source_sha": receipt["candidate_release"]["candidate_source_sha"],
                "candidate_native_editions": candidate.get("state"),
                "candidate_pending_translation_count": candidate.get("pending_translation_count"),
                "receipt": str(args.output),
            },
            sort_keys=True,
        )
    )

    # Footnote: this remains a shadow producer. A truthful INCOMPLETE_NATIVE_EDITIONS
    # observation is written into the receipt while the exporter itself exits zero; a
    # separate reviewed consumer may say “would block”, but this workflow never does.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
