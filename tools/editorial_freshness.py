#!/usr/bin/env python3
"""Editorial freshness policy for FCMO AI Newsletter.

This module keeps availability, transport freshness and editorial freshness as
separate truths.  It can deterministically select a current lead from the Story
layer and can fail production health with a stage-specific diagnosis when the
newspaper is serving stale material.

Freshness never changes evidence/confidence labels.  It only changes which
already-public-safe Story is preferred for the front page.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CONFIDENCE_RANK = {
    "strongly_supported": 5,
    "supported": 4,
    "moderate": 3,
    "mixed": 2,
    "weak": 1,
}


def parse_time(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def story_time(story: dict[str, Any]) -> datetime | None:
    return parse_time(story.get("modified_at")) or parse_time(story.get("published_at"))


def importance(story: dict[str, Any]) -> int:
    try:
        return int((story.get("news_value") or {}).get("importance") or 0)
    except (TypeError, ValueError):
        return 0


def confidence(story: dict[str, Any]) -> int:
    raw = str((story.get("news_value") or {}).get("confidence") or "").lower()
    return CONFIDENCE_RANK.get(raw, 0)


def material(story: dict[str, Any], minimum_importance: int) -> bool:
    return importance(story) >= minimum_importance


def choose_lead(
    stories: list[dict[str, Any]],
    now: datetime,
    target_hours: int,
    acceptable_hours: int,
    minimum_importance: int,
) -> dict[str, Any]:
    timed = [(story, story_time(story)) for story in stories]
    timed = [(story, ts) for story, ts in timed if ts is not None and material(story, minimum_importance)]
    if not timed:
        return stories[0]

    target_cutoff = now - timedelta(hours=target_hours)
    acceptable_cutoff = now - timedelta(hours=acceptable_hours)
    target = [(s, ts) for s, ts in timed if ts >= target_cutoff]
    acceptable = [(s, ts) for s, ts in timed if ts >= acceptable_cutoff]
    pool = target or acceptable
    if not pool:
        # There is no recent material to promote. Preserve the existing lead; the
        # health check will identify STORY_SUPPLY_STALE rather than manufacturing
        # freshness by re-dating old reporting.
        return stories[0]

    # Within the freshest valid lane, consequence and evidence quality decide the
    # lead before recency. This prevents a trivial same-hour item from displacing a
    # substantially more important, well-supported development merely because it
    # is a few minutes newer.
    return max(
        pool,
        key=lambda item: (
            importance(item[0]),
            confidence(item[0]),
            item[1],
            str(item[0].get("research_id") or ""),
        ),
    )[0]


def load_stories(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit("editorial freshness FAILED: Story layer is empty")
    if not all(isinstance(row, dict) for row in data):
        raise SystemExit("editorial freshness FAILED: Story layer contains non-object rows")
    return data


def age_hours(now: datetime, ts: datetime | None) -> float | None:
    if ts is None:
        return None
    return max(0.0, (now - ts).total_seconds() / 3600.0)


def select(args: argparse.Namespace) -> int:
    stories = load_stories(args.stories)
    now = datetime.now(timezone.utc)
    chosen = choose_lead(
        stories,
        now,
        args.target_hours,
        args.acceptable_hours,
        args.minimum_importance,
    )
    current = stories[0]
    if chosen is not current:
        stories = [chosen] + [story for story in stories if story is not chosen]
        args.stories.write_text(json.dumps(stories, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            "editorial freshness SELECTED: "
            f"{chosen.get('research_id')} replaces {current.get('research_id')} "
            f"(age={age_hours(now, story_time(chosen)):.1f}h, importance={importance(chosen)})"
        )
    else:
        chosen_age = age_hours(now, story_time(chosen))
        label = "unknown" if chosen_age is None else f"{chosen_age:.1f}h"
        print(f"editorial freshness lead unchanged: {chosen.get('research_id')} age={label}")
    return 0


def check(args: argparse.Namespace) -> int:
    stories = load_stories(args.stories)
    status = json.loads(args.status.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)

    lead = stories[0]
    lead_ts = story_time(lead)
    material_rows = [s for s in stories if material(s, args.minimum_importance) and story_time(s) is not None]
    newest = max(material_rows, key=lambda s: story_time(s) or datetime.min.replace(tzinfo=timezone.utc)) if material_rows else None
    newest_ts = story_time(newest) if newest else None
    airlock_ts = parse_time(status.get("airlock_generated_at"))
    newsroom_ts = parse_time(status.get("finalized_at"))

    metrics = {
        "airlock_age_h": age_hours(now, airlock_ts),
        "newsroom_age_h": age_hours(now, newsroom_ts),
        "newest_material_age_h": age_hours(now, newest_ts),
        "lead_age_h": age_hours(now, lead_ts),
        "lead_id": lead.get("research_id"),
        "newest_material_id": newest.get("research_id") if newest else None,
    }

    def fail(stage: str, message: str) -> None:
        print(json.dumps({"state": "UNHEALTHY", "stage": stage, "metrics": metrics}, sort_keys=True))
        raise SystemExit(f"editorial freshness FAILED [{stage}]: {message}")

    if airlock_ts is None:
        fail("AIRLOCK", "production status lacks airlock_generated_at")
    if metrics["airlock_age_h"] is not None and metrics["airlock_age_h"] > args.max_airlock_age_hours:
        fail("AIRLOCK", f"Airlock is {metrics['airlock_age_h']:.1f}h old")

    if newsroom_ts is None:
        fail("NEWSROOM", "production status lacks finalized_at")
    if metrics["newsroom_age_h"] is not None and metrics["newsroom_age_h"] > args.max_newsroom_age_hours:
        fail("NEWSROOM", f"last newsroom finalization is {metrics['newsroom_age_h']:.1f}h old")

    if newest_ts is None:
        fail("STORY_SUPPLY", "no timestamped material Story exists")
    if metrics["newest_material_age_h"] is not None and metrics["newest_material_age_h"] > args.acceptable_hours:
        fail("STORY_SUPPLY", f"newest material Story is {metrics['newest_material_age_h']:.1f}h old")

    if lead_ts is None:
        fail("LEAD_SELECTION", "front-page lead has no publication/modification timestamp")
    if metrics["lead_age_h"] is not None and metrics["lead_age_h"] > args.acceptable_hours:
        fail("LEAD_SELECTION", f"front-page lead is {metrics['lead_age_h']:.1f}h old")

    # Missing the 24h target is a production failure only when an eligible Story
    # inside the target window actually exists. Otherwise <=48h remains the
    # product's explicitly acceptable fallback and is reported as DEGRADED.
    target_cutoff = now - timedelta(hours=args.target_hours)
    target_exists = any((story_time(s) or datetime.min.replace(tzinfo=timezone.utc)) >= target_cutoff for s in material_rows)
    if target_exists and lead_ts < target_cutoff:
        fail("LEAD_SELECTION", "an eligible <=24h material Story exists but the lead is older than the target window")

    state = "HEALTHY"
    if metrics["lead_age_h"] is not None and metrics["lead_age_h"] > args.target_hours:
        state = "DEGRADED_ACCEPTABLE"
    print(json.dumps({"state": state, "stage": "EDITORIAL_FRESHNESS", "metrics": metrics}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--stories", type=Path, default=Path("site/data/stories.json"))
    common.add_argument("--target-hours", type=int, default=24)
    common.add_argument("--acceptable-hours", type=int, default=48)
    common.add_argument("--minimum-importance", type=int, default=4)

    p_select = sub.add_parser("select", parents=[common])
    p_select.set_defaults(func=select)

    p_check = sub.add_parser("check", parents=[common])
    p_check.add_argument("--status", type=Path, default=Path("site/data/newsroom-status.json"))
    p_check.add_argument("--max-airlock-age-hours", type=int, default=30)
    p_check.add_argument("--max-newsroom-age-hours", type=int, default=30)
    p_check.set_defaults(func=check)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
