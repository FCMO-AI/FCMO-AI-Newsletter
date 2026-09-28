"""Front-page order for the FCMO AI daily: freshness first, then eligibility and weight.

Pure and deterministic: the anchor is the freshest story in the input, never the
wall clock, so the same corpus always yields the same front page.
"""

from __future__ import annotations

import datetime

FRESH_WINDOW = datetime.timedelta(hours=48)


def _instant(value: object) -> datetime.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)


def fresh_instant(story: dict) -> datetime.datetime | None:
    """When the story became news: the earlier of event and first publication.

    A scheduled event announced today with a future ``event_at`` counts from its
    publication, so it cannot dominate the front page until it happens.
    """
    event = _instant(story.get("event_at"))
    if event is None:
        return None
    published = _instant(story.get("first_published_at"))
    return min(event, published) if published else event


def _importance(story: dict) -> float:
    value = story.get("importance")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def front_order(stories: list[dict]) -> list[dict]:
    """Return a full permutation of ``stories``; index 0 is the lead.

    Stories fall into 48-hour tranches counted back from the freshest one. Inside
    a tranche, front-page eligibility, importance, recency and id decide. The
    lead is the first eligible story in that order (the first story if none is).
    """
    instants = [fresh_instant(story) for story in stories]
    dated = [instant for instant in instants if instant is not None]
    anchor = max(dated) if dated else None

    def key(pair: tuple[dict, datetime.datetime | None]) -> tuple:
        story, instant = pair
        eligible = 0 if story.get("front_page_eligible") else 1
        tail = (-_importance(story),)
        if instant is None or anchor is None:
            return (1, 0, eligible, *tail, 0.0, str(story.get("id", "")))
        return (0, (anchor - instant) // FRESH_WINDOW, eligible, *tail, -instant.timestamp(), str(story.get("id", "")))

    base = [story for story, _ in sorted(zip(stories, instants), key=key)]
    lead = next((index for index, story in enumerate(base) if story.get("front_page_eligible")), 0)
    return [base[lead], *base[:lead], *base[lead + 1:]] if base else []
