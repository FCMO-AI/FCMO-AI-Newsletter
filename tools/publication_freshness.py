"""Reader freshness, independent of the immutable airlock generation timestamp.

The frozen v2 receipt keeps its transport classification. This additive public
status measures actual news age and projects it into three reader states.
"""
from __future__ import annotations

from datetime import timezone
from tools.paper.front_order import FRESH_WINDOW, _instant

SCHEMA = "fcmo-publication-status-v1"


def publication_status(freshness: dict, status: dict, *, stories: list[dict] | None = None) -> dict:
    checked = _instant(freshness.get("checked_at"))
    newest = _instant(freshness.get("newest_at"))
    age = (checked - newest).total_seconds() / 3600 if checked and newest else None
    wire = str(status.get("wire_state") or status.get("edition_state") or "TRANSPORT_DOWN")
    wire_reason = status.get("edition_reason")
    state, reason = "DELAYED", wire_reason or "STORY_SUPPLY"
    if age is not None and age < -0.25:
        reason = "CLOCK_SKEW"
    elif age is not None and max(0, age) <= FRESH_WINDOW.total_seconds() / 3600 and wire in ("FRESH", "QUIET"):
        state, reason = wire, None
    # A seal or rebuild date is not the date a story was published.
    published = [_instant(story.get("first_published_at")) for story in stories or []]
    published = [stamp for stamp in published if stamp and checked and stamp <= checked]
    last_edition_at = (max(published).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                       if published else status.get("last_edition_at"))
    return {
        "schema": SCHEMA,
        "state": state,
        "reason": reason,
        "checked_at": freshness.get("checked_at"),
        "newest_at": freshness.get("newest_at"),
        "newest_age_hours": round(max(0, age), 3) if age is not None else None,
        "stale_after_hours": int(FRESH_WINDOW.total_seconds() / 3600),
        "last_edition_at": last_edition_at,
        "wire_state": wire,
        "wire_reason": wire_reason,
        "release_id": status.get("release_id"),
        "corpus_digest": status.get("corpus_digest"),
    }


def reader_status(status: dict) -> dict:
    """Use the public projection when available; old receipts remain readable."""
    public = status.get("publication_status")
    if not isinstance(public, dict):
        return status
    return {**status, "edition_state": public["state"], "edition_reason": public["reason"],
            "last_edition_at": public["last_edition_at"] or status.get("last_edition_at")}
