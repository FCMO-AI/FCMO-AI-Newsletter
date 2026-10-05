#!/usr/bin/env python3
"""Editorial freshness policy for FCMO AI Newsletter.

Availability (serving), transport liveness, upstream state and editorial
freshness are separate signals (contracts/README.md, "Health state").

* ``select`` deterministically picks the current lead from the Story layer.
* ``check`` measures the editorial signal: GREEN only when the newest story
  event is at most ``newest_event_max_age_h`` (36 h) old; otherwise ``EVENT_STALE`` (or ``STORY_SUPPLY`` when no story has
  an event time). It reads ``corpus/wire-status.json``, never
  ``airlock.generated_at``, and exits 1 when the signal is not GREEN.

Freshness never changes evidence/confidence labels.  It only changes which
already-public-safe Story is preferred for the front page.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from tools import wire_status
except ImportError:  # executed as tools/editorial_freshness.py
    import wire_status  # type: ignore[no-redef]


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
    now = wire_status.resolve_now(getattr(args, "now", None))
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


def editorial_signal(wire_state: str, newest_event: str | None, now: datetime, max_age_h: float) -> dict[str, Any]:
    """The health-state ``editorial`` signal."""
    age = round(wire_status.hours_between(newest_event, now), 1) if newest_event else None
    metrics = {"newest_event_age_h": age}
    if age is not None and age <= max_age_h:
        return {"status": "GREEN", "code": "OK", "detail": f"Newest story event is {age}h old (limit {max_age_h:g}h).", "metrics": metrics}
    if age is None:
        return {"status": "RED", "code": "STORY_SUPPLY", "detail": "No live story has an event time.", "metrics": metrics}
    return {"status": "RED", "code": "EVENT_STALE", "detail": f"Newest story event is {age}h old (limit {max_age_h:g}h).", "metrics": metrics}


def check(args: argparse.Namespace) -> int:
    now = wire_status.resolve_now(args.now)
    thresholds = wire_status.load_thresholds()
    max_age_h = float(args.max_event_age_hours or thresholds["editorial"]["newest_event_max_age_h"])
    wire_state, _reason, wire = wire_status.classify_path(args.wire_status, now)
    newest = wire_status.newest_event_at(args.records) or (wire or {}).get("newest_event_at")
    sig = editorial_signal(wire_state, newest, now, max_age_h)
    if args.signal_out:
        args.signal_out.parent.mkdir(parents=True, exist_ok=True)
        args.signal_out.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
    print(f"EDITORIAL {sig['code']} edition={wire_state} newest_event_at={newest or '-'} "
          f"newest_event_age_h={sig['metrics']['newest_event_age_h']}")
    print(sig["detail"])
    return 0 if sig["status"] == "GREEN" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--stories", type=Path, default=Path("site/data/stories.json"))
    common.add_argument("--target-hours", type=int, default=24)
    common.add_argument("--acceptable-hours", type=int, default=48)
    common.add_argument("--minimum-importance", type=int, default=4)

    common.add_argument("--now", help="ISO 8601 time (else FCMO_NOW, else the real clock)")

    p_select = sub.add_parser("select", parents=[common])
    p_select.set_defaults(func=select)

    p_check = sub.add_parser("check", help="editorial freshness signal (exit 1 when not GREEN)")
    p_check.add_argument("--wire-status", type=Path, default=Path("corpus/wire-status.json"))
    p_check.add_argument("--records", type=Path, default=Path("corpus/data/developments.jsonl"))
    p_check.add_argument("--max-event-age-hours", type=float, default=None)
    p_check.add_argument("--now", help="ISO 8601 time (else FCMO_NOW, else the real clock)")
    p_check.add_argument("--signal-out", type=Path)
    p_check.set_defaults(func=check)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
