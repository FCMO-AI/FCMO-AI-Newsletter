#!/usr/bin/env python3
"""Build the public newsroom Story layer from declassified research dossiers.

Research dossiers remain the evidence authority. Story objects are the newspaper layer:
they decide whether a dossier is a lead, standard story, signal, brief, or database-only
record without changing the underlying evidence/confidence/importance semantics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_briefs(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != "fcmo-public-brief-v1":
            raise ValueError(f"unsupported brief schema: {path}")
        rows.append(doc)
    return rows


def disposition(brief: dict[str, Any]) -> str:
    evidence = str(brief.get("evidence_class") or "")
    confidence = str(brief.get("confidence") or "")
    importance = int(brief.get("importance_effective_score") or brief.get("importance_score") or 0)
    status = str(brief.get("status") or "")
    if status in {"invalidated", "retracted"}:
        return "DATABASE_ONLY"
    if evidence == "D" or confidence in {"weak_signal", "speculation"}:
        return "SIGNAL" if importance >= 6 else "DATABASE_ONLY"
    if importance >= 8:
        return "LEAD"
    if importance >= 6:
        return "STANDARD"
    if importance >= 5:
        return "BRIEF"
    return "DATABASE_ONLY"


def story_type(brief: dict[str, Any]) -> str:
    kind = str(brief.get("development_type") or "research")
    if "incident" in kind or "policy" in kind:
        return "NEWS"
    if "release" in kind:
        return "RELEASE"
    if "paper" in kind or "research" in kind:
        return "RESEARCH"
    return "ANALYSIS"


def story(doc: dict[str, Any]) -> dict[str, Any]:
    record = doc["record"]
    brief = doc["brief"]
    limitations = list(brief.get("limitations") or [])
    contradictions = list(brief.get("contradictory_evidence") or [])
    gaps = [
        item.get("description")
        for item in (brief.get("evidence_gaps") or [])
        if isinstance(item, dict) and item.get("description") and item.get("state", "open") != "resolved"
    ]
    technical = brief.get("technical") or {}
    sources = list(brief.get("source_urls") or [])
    return {
        "schema": "fcmo-newsroom-story-v1",
        "story_id": "STORY-" + record["id"],
        "research_ids": [record["id"]],
        "headline": record["title"],
        "dek": record["summary"],
        "story_type": story_type(brief),
        "disposition": disposition(brief),
        "published_at": brief.get("event_at") or record.get("event_at"),
        "modified_at": brief.get("last_verified_at"),
        "desk": record.get("desk"),
        "evidence": brief.get("evidence_class"),
        "confidence": brief.get("confidence"),
        "importance": brief.get("importance_effective_score", brief.get("importance_score")),
        "tier": brief.get("importance_tier"),
        "what_changed": brief.get("summary", ""),
        "why_it_matters": brief.get("why_it_matters", ""),
        "strongest_baseline": technical.get("strongest_baseline", ""),
        "mechanism": technical.get("mechanism", ""),
        "demonstrated_result": technical.get("demonstrated_result", ""),
        "claimed_result": technical.get("claimed_result", ""),
        "what_is_not_proven": limitations + contradictions + gaps,
        "claims": list(brief.get("claims") or []),
        "sources": sources,
        "human_url": record.get("human_url"),
        "machine_url": record.get("machine_url"),
        # Footnote: there is intentionally no implicit FCMO strategic-analysis field.
        # Public analysis must be authored from the clean-room side, not inherited from
        # ARB's private implication blocks.
        "public_analysis": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    args = parser.parse_args()
    docs = read_briefs(args.site)
    stories = [story(doc) for doc in docs]
    stories.sort(
        key=lambda item: (
            {"LEAD": 5, "STANDARD": 4, "BRIEF": 3, "SIGNAL": 2, "DATABASE_ONLY": 1}.get(item["disposition"], 0),
            int(item.get("importance") or 0),
            str(item.get("modified_at") or ""),
            item["story_id"],
        ),
        reverse=True,
    )
    out = args.site / "data" / "stories.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stories, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    counts = {key: sum(1 for item in stories if item["disposition"] == key) for key in ("LEAD", "STANDARD", "BRIEF", "SIGNAL", "DATABASE_ONLY")}
    print(json.dumps({"stories": len(stories), "dispositions": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
