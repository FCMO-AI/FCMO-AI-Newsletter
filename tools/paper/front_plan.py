"""Assign each front-page story to exactly one block of the FCMO AI daily."""

from __future__ import annotations

from typing import Sequence

TOP_COUNT = 4
DEVELOPING_COUNT = 2
ESSENTIALS_COUNT = 5
BEAT_COUNT = 3
SETTLED_CONFIDENCE = frozenset({"confirmed", "strongly_supported"})


def front_plan(order: list[dict], beats: Sequence[str]) -> dict:
    """Split ``front_order`` output into lead, top, developing, essentials and beat blocks.

    Pure and clock-free: it only reads ``id``, ``confidence`` and ``beat`` and returns
    the same story dicts it was given. Blocks are filled in that priority order and a
    story shown in one block is never repeated in a later one.
    """
    lead = order[0] if order else None
    top = list(order[1:1 + TOP_COUNT])
    developing = [story for story in order[1 + TOP_COUNT:]
                  if story.get("confidence") not in SETTLED_CONFIDENCE][:DEVELOPING_COUNT]
    used = {story["id"] for story in ([lead] if lead else []) + top + developing}
    essentials = [story for story in order if story["id"] not in used][:ESSENTIALS_COUNT]
    used.update(story["id"] for story in essentials)
    by_beat: dict[str, list[dict]] = {}
    for beat in beats:
        if beat in by_beat:
            continue
        values = [story for story in order if story.get("beat") == beat and story["id"] not in used][:BEAT_COUNT]
        if values:
            by_beat[beat] = values
            used.update(story["id"] for story in values)
    return {"lead": lead, "top": top, "developing": developing, "essentials": essentials, "beats": by_beat}


# --- c6 front page: cover, board and wire (pure, clock-free) -----------------

WIRE_COUNT = 30
TOPIC_TILE_COUNT = 12
# The only confidences that let an item say «Shown». Everything else that has
# claims is «Claimed»; a story with no confidence rating and no claims is
# «Not established». The rule never rounds up.
SHOWN_CONFIDENCE = frozenset({"confirmed", "strongly_supported", "supported"})
FORMATS = ("news", "feature", "technical", "science", "letter")
_SCIENCE_TYPES = frozenset({"paper", "reproduction_or_audit"})
_TECHNICAL_TYPES = frozenset({"technical_report", "dataset_benchmark", "repository_release", "hardware_infrastructure"})


def evidence_class(story: dict) -> str:
    """Item-level evidence class: ``shown``, ``claimed`` or ``not_established``."""
    if story.get("confidence") in SHOWN_CONFIDENCE:
        return "shown"
    evidence = story.get("evidence") if isinstance(story.get("evidence"), dict) else {}
    claims = evidence.get("claims") if isinstance(evidence.get("claims"), list) else []
    if story.get("confidence") or any(isinstance(c, dict) and c.get("label") for c in claims):
        return "claimed"
    return "not_established"


def story_format(story: dict) -> str:
    """The format label of a story inside the one flow (never a separate product)."""
    kind = str(story.get("kind") or "")
    if kind in ("letter", "feature"):
        return kind
    development = story.get("development_type")
    if development in _SCIENCE_TYPES:
        return "science"
    if development in _TECHNICAL_TYPES:
        return "technical"
    return "news"


def landing_slots(order: Sequence[dict]) -> dict:
    """Cover, board and wire from ``front_order`` output; the wire never repeats the board.

    The cover is the lead, the board is the next ``TOP_COUNT`` stories (one wide card and
    three plates) and the wire starts on the story right after the board.
    """
    cover = order[0] if order else None
    board = list(order[1:1 + TOP_COUNT])
    start = 1 + TOP_COUNT
    wire = list(order[start:start + WIRE_COUNT])
    return {"cover": cover, "board": board, "wire": wire}


def class_counts(stories: Sequence[dict]) -> dict:
    counts = {"shown": 0, "claimed": 0, "not_established": 0}
    for story in stories:
        counts[evidence_class(story)] += 1
    return counts


def topic_counts(stories: Sequence[dict], known: Sequence[str], *, limit: int = TOPIC_TILE_COUNT) -> list[tuple[str, int]]:
    """Most-covered topics that have a catalogue label; a raw slug is never a tile."""
    tally: dict[str, int] = {}
    for story in stories:
        for topic in dict.fromkeys(story.get("topics") or []):
            if topic in known:
                tally[topic] = tally.get(topic, 0) + 1
    return sorted(tally.items(), key=lambda row: (-row[1], row[0]))[:limit]
