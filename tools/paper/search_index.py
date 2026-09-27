"""Compact, lazy-loaded search indexes with a hard per-locale budget."""

from __future__ import annotations

import json
from pathlib import Path

from .i18n import dek, headline
from .routes import href, story_path

LIMIT = 150 * 1024


def build(stories: list[dict], *, locale: dict, catalog: dict, base: str, out: Path) -> int:
    rows = []
    code = locale["code"]
    for story in stories:
        if story.get("status") != "live":
            continue
        rows.append({
            "id": story["id"],
            "h": headline(story, code, catalog),
            "d": dek(story, code, catalog),
            "u": href(base, story_path(locale, story)),
            "b": catalog.get("labels", {}).get("beat", {}).get(story.get("beat"), ""),
            "o": story.get("organizations", []),
            "t": story.get("topics", []),
            # Keep the compact local-search fields above while retaining the
            # original public agent index's query and citation vocabulary.
            "title": headline(story, code, catalog),
            "summary": story.get("summary", dek(story, code, catalog)),
            "desk": story.get("desk") or story.get("beat", ""),
            "event_at": story.get("event_at", ""),
            "evidence": story.get("evidence_class", ""),
            "confidence": story.get("confidence", ""),
            "importance": story.get("importance", 0),
            "kind": story.get("kind", ""),
            "human_url": href(base, story_path(locale, story)),
            "machine_url": href(base, f"api/v1/stories/{story['id']}.json"),
            "citation": {"id": story["id"], "source": href(base, story_path(locale, story))},
            "search_text": " ".join([headline(story, code, catalog), dek(story, code, catalog), story.get("desk", ""), *story.get("topics", []), *story.get("organizations", [])]),
        })
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > LIMIT:
        raise ValueError(f"search index exceeds {LIMIT} bytes for {code}: {len(payload)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return len(payload)
