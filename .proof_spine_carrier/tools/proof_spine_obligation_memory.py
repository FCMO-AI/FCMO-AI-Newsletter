#!/usr/bin/env python3
"""Temporal memory for Proof Spine obligations that must not disappear by aging out.

Freshness law prevents an old PASS from living forever. This module supplies the
symmetric rule: a known OPEN obligation remains open until reviewed semantics receive
explicit closure evidence. Absence from a later detector window is not resolution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


CONTRACT_KIND = "FCMO_PROOF_SPINE_OBLIGATION_CONTRACT"
SNAPSHOT_KIND = "FCMO_PROOF_SPINE_OBLIGATION_SNAPSHOT"
MEMORY_KIND = "FCMO_PROOF_SPINE_OBLIGATION_MEMORY"
AUTHORITY = "OBSERVATIONAL_ONLY"


class ObligationError(ValueError):
    pass


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ObligationError(f"{field} must be a non-empty timezone-aware timestamp")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ObligationError(f"{field} is not valid ISO-8601/RFC3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ObligationError(f"{field} must include timezone")
    return parsed.astimezone(timezone.utc)


def _strings(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ObligationError(f"{field} must be a list of non-empty strings")
    if len(value) != len(set(value)):
        raise ObligationError(f"{field} must not contain duplicates")
    if nonempty and not value:
        raise ObligationError(f"{field} must not be empty")
    return value


def _identity(subject: Mapping[str, Any], keys: Sequence[str]) -> tuple[str, dict[str, Any]]:
    missing = [key for key in keys if key not in subject]
    if missing:
        raise ObligationError(f"obligation subject missing identity keys: {missing}")
    identity = {key: subject[key] for key in keys}
    return _digest(identity), identity


def evaluate_obligation_memory(contract: Mapping[str, Any], snapshots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if contract.get("kind") != CONTRACT_KIND or contract.get("schema_version") != 1:
        raise ObligationError("invalid obligation contract kind/schema")
    identity_keys = _strings(contract.get("identity_keys"), "contract.identity_keys", nonempty=True)
    open_states = set(_strings(contract.get("open_states"), "contract.open_states", nonempty=True))
    resolved_states = set(_strings(contract.get("resolved_states"), "contract.resolved_states", nonempty=True))
    if open_states & resolved_states:
        raise ObligationError("open_states and resolved_states must be disjoint")
    resolution_evidence_required = contract.get("resolution_evidence_required", False)
    if not isinstance(resolution_evidence_required, bool):
        raise ObligationError("contract.resolution_evidence_required must be boolean")

    project = contract.get("project")
    if not isinstance(project, Mapping) or not project.get("id") or not project.get("repository"):
        raise ObligationError("contract.project requires id and repository")

    normalized: list[tuple[datetime, Mapping[str, Any]]] = []
    for index, snapshot in enumerate(snapshots):
        if snapshot.get("kind") != SNAPSHOT_KIND or snapshot.get("schema_version") != 1:
            raise ObligationError(f"snapshot[{index}] has invalid kind/schema")
        if snapshot.get("authority") != "EVIDENCE_ONLY":
            raise ObligationError(f"snapshot[{index}] authority must be EVIDENCE_ONLY")
        if snapshot.get("project") != project:
            raise ObligationError(f"snapshot[{index}] project does not match reviewed contract")
        observed_at = _parse_time(snapshot.get("observed_at"), f"snapshot[{index}].observed_at")
        observations = snapshot.get("observations")
        if not isinstance(observations, list) or any(not isinstance(item, Mapping) for item in observations):
            raise ObligationError(f"snapshot[{index}].observations must be a list of objects")
        normalized.append((observed_at, snapshot))

    normalized.sort(key=lambda pair: pair[0])
    state: dict[str, dict[str, Any]] = {}
    transitions: list[dict[str, Any]] = []

    for observed_at, snapshot in normalized:
        seen: set[str] = set()
        for observation in snapshot["observations"]:
            subject = observation.get("subject")
            if not isinstance(subject, Mapping):
                raise ObligationError("observation.subject must be an object")
            oid, identity = _identity(subject, identity_keys)
            if oid in seen:
                raise ObligationError("a snapshot may not observe the same obligation twice")
            seen.add(oid)
            observed_state = observation.get("state")
            previous = state.get(oid)

            if observed_state in open_states:
                reopened = previous is not None and previous["state"] == "RESOLVED"
                generation = (
                    1
                    if previous is None
                    else previous["generation"] + (1 if reopened else 0)
                )
                opened_at = (
                    observed_at.isoformat()
                    if previous is None or reopened
                    else previous["opened_at"]
                )
                # FOOTNOTE [1]: repeated observations of one still-open obligation
                # refresh last_seen_at, not opened_at. Resetting opened_at on every
                # detector hit would make old debt look young and erase its real age.
                state[oid] = {
                    "identity": identity,
                    "state": "ACTIVE",
                    "generation": generation,
                    "opened_at": opened_at,
                    "last_seen_at": observed_at.isoformat(),
                    "last_observed_state": observed_state,
                    "closure_evidence": False,
                    "closure_evidence_digest": None,
                    "closure_evidence_refs": [],
                    "closure_measurement_roots": [],
                    "absent_since": None,
                }
                transitions.append(
                    {
                        "at": observed_at.isoformat(),
                        "identity": identity,
                        "event": "REOPEN_OBSERVED" if reopened else "OPEN_OBSERVED",
                    }
                )
            elif observed_state in resolved_states:
                # FOOTNOTE [2]: explicit closure can resolve only an already-known
                # obligation. When the reviewed contract requires closure evidence,
                # the producer must also expose the measurement roots and evidence
                # references behind the resolution instead of supplying a bare word.
                if previous is None:
                    transitions.append(
                        {
                            "at": observed_at.isoformat(),
                            "identity": identity,
                            "event": "ORPHAN_RESOLUTION_IGNORED",
                        }
                    )
                    continue

                resolution_evidence = observation.get("resolution_evidence")
                refs: list[str] = []
                roots: list[str] = []
                evidence_digest: str | None = None
                if resolution_evidence is not None:
                    if not isinstance(resolution_evidence, Mapping):
                        raise ObligationError("observation.resolution_evidence must be an object")
                    refs = _strings(
                        resolution_evidence.get("evidence_refs"),
                        "observation.resolution_evidence.evidence_refs",
                        nonempty=True,
                    )
                    roots = _strings(
                        resolution_evidence.get("measurement_roots"),
                        "observation.resolution_evidence.measurement_roots",
                        nonempty=True,
                    )
                    evidence_time = _parse_time(
                        resolution_evidence.get("observed_at"),
                        "observation.resolution_evidence.observed_at",
                    )
                    if evidence_time > observed_at:
                        raise ObligationError(
                            "resolution evidence cannot postdate its enclosing snapshot"
                        )
                    evidence_digest = _digest(resolution_evidence)
                elif resolution_evidence_required:
                    raise ObligationError(
                        "reviewed contract requires explicit resolution_evidence"
                    )

                previous["state"] = "RESOLVED"
                previous["last_seen_at"] = observed_at.isoformat()
                previous["last_observed_state"] = observed_state
                previous["closure_evidence"] = True
                previous["closure_evidence_digest"] = evidence_digest
                previous["closure_evidence_refs"] = refs
                previous["closure_measurement_roots"] = roots
                previous["resolved_at"] = observed_at.isoformat()
                previous["absent_since"] = None
                transitions.append(
                    {
                        "at": observed_at.isoformat(),
                        "identity": identity,
                        "event": "RESOLUTION_OBSERVED",
                        "closure_evidence_digest": evidence_digest,
                    }
                )
            else:
                # FOOTNOTE [3]: unknown producer vocabulary is never allowed to close debt.
                # If the obligation was active, preserve it and mark uncertainty instead.
                if previous is not None and previous["state"] == "ACTIVE":
                    previous["last_seen_at"] = observed_at.isoformat()
                    previous["last_observed_state"] = observed_state
                    transitions.append({"at": observed_at.isoformat(), "identity": identity, "event": "UNKNOWN_STATE_CARRIED_OPEN"})

        for oid, obligation in state.items():
            if obligation["state"] != "ACTIVE" or oid in seen:
                continue
            if obligation.get("absent_since") is None:
                obligation["absent_since"] = observed_at.isoformat()
                transitions.append(
                    {
                        "at": observed_at.isoformat(),
                        "identity": obligation["identity"],
                        "event": "ABSENT_BUT_CARRIED_OPEN",
                    }
                )
            # FOOTNOTE [4]: absence is intentionally not a state transition to RESOLVED.
            # Detector windows, retention, sampling, or filtering may hide old debt; only a
            # contract-recognized explicit resolution observation may close it.

    obligations = sorted(state.values(), key=lambda item: json.dumps(item["identity"], sort_keys=True))
    active = [item for item in obligations if item["state"] == "ACTIVE"]
    resolved = [item for item in obligations if item["state"] == "RESOLVED"]
    result = {
        "schema_version": 1,
        "kind": MEMORY_KIND,
        "authority": AUTHORITY,
        "project": dict(project),
        "contract_digest": _digest(contract),
        "snapshot_digests": [_digest(snapshot) for _, snapshot in normalized],
        "summary": {"active": len(active), "resolved": len(resolved), "total_known": len(obligations)},
        "obligations": obligations,
        "transitions": transitions,
        "claim_boundary": (
            "Temporal evidence memory only. A detector returning healthy or omitting an old item "
            "does not close a known obligation without contract-recognized resolution evidence. "
            "When resolution_evidence_required is enabled, a closure must also expose exact "
            "measurement roots and evidence references; repeated open observations preserve "
            "the generation's original opened_at rather than rejuvenating old debt."
        ),
    }
    result["memory_digest"] = _digest(result)
    return result


def _load(path: str) -> Mapping[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ObligationError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract")
    parser.add_argument("snapshots", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate_obligation_memory(_load(args.contract), [_load(path) for path in args.snapshots])
    rendered = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
