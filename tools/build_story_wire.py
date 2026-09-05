#!/usr/bin/env python3
"""Build the public newsroom Story layer from declassified research dossiers.

Research dossiers remain the evidence authority. Story objects are the newspaper layer:
they decide whether a dossier is a lead, standard story, signal, brief, or database-only
record without changing the underlying evidence/confidence/importance semantics.

The newspaper also owns publication memory. Source-event time is not the same thing as
FCMO publication time: a three-day-old paper discovered today must not be backdated as a
new article, while the one-time Airlock-v2 migration must not flood today's News sitemap
with every historical dossier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def read_briefs(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != "fcmo-public-brief-v1":
            raise ValueError(f"unsupported brief schema: {path}")
        rows.append(doc)
    return rows


def read_public_research(root: Path) -> dict[str, dict[str, Any]]:
    if not root.is_dir():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("FCMO-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != "fcmo-public-clean-room-research-v1":
            raise ValueError(f"unsupported clean-room research schema: {path}")
        result[value["id"]] = value
    return result


def read_new_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    value = json.loads(path.read_text(encoding="utf-8"))
    return {
        item for item in (value.get("newly_ingested_brief_ids") or [])
        if isinstance(item, str)
    }


def read_status(site: Path) -> dict[str, Any]:
    path = site / "data" / "newsroom-status.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def read_memory(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not isinstance(value.get("stories"), dict):
        raise ValueError("newsroom publication memory has invalid schema")
    return value["stories"]


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


def event_for(brief: dict[str, Any], *, is_new: bool, changed: bool, migration: bool) -> str:
    status = str(brief.get("status") or "")
    if status == "retracted":
        return "RETRACTION"
    if status == "invalidated":
        return "CORRECTION"
    if status == "superseded":
        return "SUPERSESSION"
    if is_new:
        return "NEW"
    if changed and not migration:
        return "MATERIAL_UPDATE"
    return "CURRENT"


def publication_memory_for(
    doc: dict[str, Any],
    old: dict[str, Any] | None,
    *,
    is_new: bool,
    delivered_at: str | None,
) -> tuple[dict[str, Any], str]:
    record = doc["record"]
    brief = doc["brief"]
    identifier = record["id"]
    public_digest = digest(doc)
    migration = old is None and not is_new
    changed = old is not None and old.get("public_digest_sha256") != public_digest

    if old is None:
        # Footnote: existing dossiers during the one-time v2 migration retain their
        # historical event/publication date so they do not masquerade as today's news.
        first_published = (
            delivered_at if is_new and delivered_at
            else brief.get("event_at") or record.get("event_at") or brief.get("last_verified_at")
        )
        last_material = first_published
    else:
        first_published = old.get("first_published_at")
        last_material = (
            delivered_at if changed and delivered_at
            else old.get("last_material_update_at") or first_published
        )

    event = event_for(brief, is_new=is_new, changed=changed, migration=migration)
    memory = {
        "id": identifier,
        "first_published_at": first_published,
        "last_material_update_at": last_material,
        "source_event_at": brief.get("event_at") or record.get("event_at"),
        "public_digest_sha256": public_digest,
        "last_publication_event": event,
    }
    return memory, event


def story(
    doc: dict[str, Any],
    memory: dict[str, Any],
    publication_event: str,
    research: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    public_analysis = list((research or {}).get("public_analysis") or [])
    additional_sources = [
        item["url"]
        for item in ((research or {}).get("independent_sources") or [])
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    ]
    clean_room_contradictions = [
        item["text"]
        for item in ((research or {}).get("contradictions") or [])
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    return {
        "schema": "fcmo-newsroom-story-v1",
        "story_id": "STORY-" + record["id"],
        "research_ids": [record["id"]],
        "headline": record["title"],
        "dek": record["summary"],
        "story_type": story_type(brief),
        "publication_event": publication_event,
        "disposition": disposition(brief),
        "published_at": memory.get("first_published_at"),
        "modified_at": memory.get("last_material_update_at"),
        "source_event_at": memory.get("source_event_at"),
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
        "what_is_not_proven": limitations + contradictions + gaps + clean_room_contradictions,
        "claims": list(brief.get("claims") or []),
        "sources": list(dict.fromkeys(sources + additional_sources)),
        "human_url": record.get("human_url"),
        "machine_url": record.get("machine_url"),
        # Footnote: public analysis can enter only from the clean-room web research
        # record. It is never inherited from ARB's private implication blocks. Also,
        # the clean-room model's confidence is exposed separately and cannot silently
        # upgrade the canonical ARB evidence/confidence used for disposition.
        "public_analysis": public_analysis,
        "public_context_summary": (research or {}).get("public_context_summary"),
        "public_research_confidence": (research or {}).get("confidence_after_public_check"),
        "independent_source_count": len(additional_sources),
        "public_research_url": (
            f"data/newsroom-research/{record['id']}.json" if research else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--research-dir", type=Path, default=Path("site/data/newsroom-research"))
    parser.add_argument("--memory", type=Path, default=Path("site/data/newsroom-publication-memory.json"))
    parser.add_argument("--new-ids", type=Path, default=Path(".release-src.agent-run.json"))
    args = parser.parse_args()

    docs = read_briefs(args.site)
    research = read_public_research(args.research_dir)
    old_memory = read_memory(args.memory)
    new_ids = read_new_ids(args.new_ids)
    status = read_status(args.site)
    delivered_at = status.get("delivered_at")

    stories: list[dict[str, Any]] = []
    new_memory: dict[str, dict[str, Any]] = {}
    events: dict[str, int] = {}
    for doc in docs:
        identifier = doc["record"]["id"]
        memory, event = publication_memory_for(
            doc,
            old_memory.get(identifier),
            is_new=identifier in new_ids,
            delivered_at=delivered_at,
        )
        new_memory[identifier] = memory
        events[event] = events.get(event, 0) + 1
        stories.append(story(doc, memory, event, research.get(identifier)))

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

    args.memory.parent.mkdir(parents=True, exist_ok=True)
    args.memory.write_text(
        json.dumps(
            {"schema_version": 1, "stories": new_memory},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    counts = {
        key: sum(1 for item in stories if item["disposition"] == key)
        for key in ("LEAD", "STANDARD", "BRIEF", "SIGNAL", "DATABASE_ONLY")
    }
    print(
        json.dumps(
            {
                "stories": len(stories),
                "stories_with_clean_room_research": sum(1 for item in stories if item.get("public_research_url")),
                "dispositions": counts,
                "publication_events": events,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
