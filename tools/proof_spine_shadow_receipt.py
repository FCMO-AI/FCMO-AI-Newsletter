#!/usr/bin/env python3
"""Emit a public-safe production-health receipt for Proof Spine shadow evaluation.

This adapter deliberately does NOT contain Proof Spine rules or gates. It executes the
Newsletter's own production-health oracles, records their outputs, and exposes a small
set of source timestamps so a separate proof contract can reason about causal validity.

The script is observational: unhealthy checks are data in the receipt, not a request to
publish, deploy, roll back, or otherwise mutate production.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import editorial_freshness

ROOT = Path(__file__).resolve().parents[1]

CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("serving_health", (sys.executable, "tools/verify_live_newsroom.py")),
    ("surface_oracle", (sys.executable, "tests/oraculos/verificar_live_surfaces.py")),
    (
        "publication_freshness",
        (sys.executable, "tools/verify_live_newsroom.py", "--require-airlock", "--max-airlock-age-hours", "30"),
    ),
    (
        "editorial_freshness",
        (
            sys.executable,
            "tools/editorial_freshness.py",
            "check",
            "--stories",
            "site/data/stories.json",
            "--status",
            "site/data/newsroom-status.json",
            "--target-hours",
            "24",
            "--acceptable-hours",
            "48",
            "--max-airlock-age-hours",
            "30",
            "--max-newsroom-age-hours",
            "30",
            "--minimum-importance",
            "4",
        ),
    ),
    (
        "translation_health",
        (
            sys.executable,
            "tools/translation_health.py",
            "--grace-hours",
            "1",
            "--fresh-window-hours",
            "30",
            "--minimum-importance",
            "4",
        ),
    ),
)

# Footnote for future maintainers: keep this adapter project-local and evidence-only.
# It may normalize Newsletter observations, but it must never grow mission, claim, gate,
# or promotion semantics. Those belong to the separately reviewed Proof Spine contract.


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat().replace("+00:00", "Z") if dt is not None else None


def tail(value: str, limit: int = 2400) -> str:
    return value if len(value) <= limit else value[-limit:]


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def run_check(name: str, command: tuple[str, ...]) -> dict[str, Any]:
    started = utc_now()
    try:
        result = subprocess.run(
            list(command),
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        finished = utc_now()
        return {
            "name": name,
            "execution_state": "UNKNOWN",
            "status": "UNKNOWN",
            "return_code": None,
            "started_at": iso(started),
            "finished_at": iso(finished),
            "command": list(command),
            "structured_output": None,
            "stdout_tail": "",
            "stderr_tail": str(exc),
        }

    finished = utc_now()
    return {
        "name": name,
        "execution_state": "EXECUTED",
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "return_code": result.returncode,
        "started_at": iso(started),
        "finished_at": iso(finished),
        "command": list(command),
        "structured_output": parse_last_json(result.stdout),
        "stdout_tail": tail(result.stdout.strip()),
        "stderr_tail": tail(result.stderr.strip()),
    }


# Footnote: source facts are extracted from the same files the local health checker
# already consumes. They are observations, not reimplemented health decisions. This
# lets the downstream contract compute expiry boundaries without scraping log prose.
def source_facts() -> dict[str, Any]:
    stories_path = ROOT / "site/data/stories.json"
    status_path = ROOT / "site/data/newsroom-status.json"
    stories = editorial_freshness.load_stories(stories_path)
    status = json.loads(status_path.read_text(encoding="utf-8"))

    lead = stories[0]
    material_rows = [
        story
        for story in stories
        if editorial_freshness.material(story, 4) and editorial_freshness.story_time(story) is not None
    ]
    newest = (
        max(
            material_rows,
            key=lambda story: editorial_freshness.story_time(story)
            or datetime.min.replace(tzinfo=timezone.utc),
        )
        if material_rows
        else None
    )

    return {
        "airlock_generated_at": iso(editorial_freshness.parse_time(status.get("airlock_generated_at"))),
        "newsroom_finalized_at": iso(editorial_freshness.parse_time(status.get("finalized_at"))),
        "lead": {
            "research_id": lead.get("research_id"),
            "timestamp": iso(editorial_freshness.story_time(lead)),
            "importance": editorial_freshness.importance(lead),
        },
        "newest_material": {
            "research_id": newest.get("research_id") if newest else None,
            "timestamp": iso(editorial_freshness.story_time(newest)) if newest else None,
            "importance": editorial_freshness.importance(newest) if newest else None,
        },
    }


def git_head() -> str | None:
    if os.getenv("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build_receipt() -> dict[str, Any]:
    checks = {name: run_check(name, command) for name, command in CHECKS}
    observed_at = utc_now()

    statuses = [item["status"] for item in checks.values()]
    if "UNKNOWN" in statuses:
        local_state = "UNKNOWN"
    elif "FAIL" in statuses:
        local_state = "UNHEALTHY"
    else:
        local_state = "HEALTHY"

    editorial_state = ((checks["editorial_freshness"].get("structured_output") or {}).get("state"))
    quality_state = editorial_state if local_state == "HEALTHY" and editorial_state else local_state

    return {
        "schema_version": 1,
        "kind": "FCMO_NEWSLETTER_PRODUCTION_HEALTH_SHADOW_RECEIPT",
        "authority": "NON_NORMATIVE_EVIDENCE",
        "observed_at": iso(observed_at),
        "source": {
            "repository": "FCMO-AI/FCMO-AI-Newsletter",
            "head_sha": git_head(),
            "branch": os.getenv("GITHUB_REF_NAME"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        },
        "local_surface": {
            "state": local_state,
            "quality_state": quality_state,
            "derivation": "HEALTHY only when every exported Newsletter-local check executed and passed; UNKNOWN outranks inferred failure when execution itself is missing",
        },
        "source_facts": source_facts(),
        "checks": checks,
        "claim_boundary": (
            "This receipt records public-safe Newsletter-local observations and checker outputs. "
            "It declares no Proof Spine mission, claims, gates, publication authority, or production action."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    receipt = build_receipt()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"state": receipt["local_surface"]["state"], "quality_state": receipt["local_surface"]["quality_state"], "receipt": str(args.output)}, sort_keys=True))

    # Footnote: shadow observation must not become a hidden production gate. A local
    # checker may report FAIL inside the receipt while this exporter still exits 0;
    # only exporter/configuration failure should stop the shadow workflow itself.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
