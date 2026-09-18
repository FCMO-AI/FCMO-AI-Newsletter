#!/usr/bin/env python3
"""Measure native ES/ZH Story coverage without weakening the release contract.

The canonical release contract requires complete native coverage before a candidate
may publish. Production health additionally exposes a bounded reconciliation SLO so a
source/candidate backlog is visible while the previous known-good public edition stays
live. `--require-complete` is the strict pre-release mode; the default mode preserves
the existing freshness/grace health signal for diagnosis and recovery.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOCALES = ("es-419", "zh-Hans")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def locale_ids(root: Path, locale: str) -> set[str]:
    ids: set[str] = set()
    directory = root / "site" / "data" / "i18n" / locale
    for path in sorted(directory.glob("part-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        rows = doc.get("records")
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: records object missing")
        ids.update(str(key) for key in rows)
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--grace-hours", type=float, default=1.0)
    parser.add_argument("--fresh-window-hours", type=float, default=30.0)
    parser.add_argument("--minimum-importance", type=int, default=4)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Fail if any published Story lacks either native edition; ignores health grace/window filters.",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    stories_path = args.root / "site" / "data" / "stories.json"
    stories: list[dict[str, Any]] = json.loads(stories_path.read_text(encoding="utf-8"))
    coverage = {locale: locale_ids(args.root, locale) for locale in LOCALES}

    watched: list[dict[str, Any]] = []
    overdue: list[dict[str, Any]] = []
    grace: list[dict[str, Any]] = []
    for story in stories:
        rid = str(story.get("research_id") or "")
        published_raw = str(story.get("published_at") or "")
        if not rid or not published_raw:
            continue
        published = parse_time(published_raw)
        age_h = max(0.0, (now - published).total_seconds() / 3600)
        importance = int((story.get("news_value") or {}).get("importance") or 0)
        is_lead = story.get("story_type") == "LEAD"

        # Footnote for future maintainers: release truth and health prioritization are
        # deliberately different questions. `--require-complete` checks every Story
        # identity because LOCALIZATION.md defines one EN/ES/ZH publication obligation.
        # Default health mode keeps the prior material/freshness filter so monitoring
        # can prioritize the backlog without silently redefining release eligibility.
        if not args.require_complete:
            if age_h > args.fresh_window_hours or (importance < args.minimum_importance and not is_lead):
                continue

        missing = [locale for locale in LOCALES if rid not in coverage[locale]]
        if not missing:
            continue
        item = {
            "research_id": rid,
            "story_type": story.get("story_type"),
            "importance": importance,
            "published_at": published_raw,
            "age_h": round(age_h, 3),
            "missing": missing,
        }
        watched.append(item)
        if args.require_complete:
            overdue.append(item)
        else:
            (overdue if age_h > args.grace_hours else grace).append(item)

    state = "HEALTHY"
    if overdue:
        state = "UNHEALTHY_TRANSLATION_INCOMPLETE" if args.require_complete else "UNHEALTHY_TRANSLATION_BACKLOG"
    elif grace:
        state = "DEGRADED_TRANSLATION_GRACE"
    payload = {
        "stage": "TRANSLATION_HEALTH",
        "mode": "RELEASE_GATE" if args.require_complete else "HEALTH_SLO",
        "state": state,
        "target": "complete native es-419 and zh-Hans Story coverage before release",
        "grace_hours": 0.0 if args.require_complete else args.grace_hours,
        "fresh_window_hours": None if args.require_complete else args.fresh_window_hours,
        "missing_recent": watched,
        "overdue_count": len(overdue),
        "grace_count": len(grace),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if overdue else 0


if __name__ == "__main__":
    raise SystemExit(main())
