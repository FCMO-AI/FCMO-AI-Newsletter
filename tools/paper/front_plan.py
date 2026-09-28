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
