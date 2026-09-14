#!/usr/bin/env python3
"""Measure whether recent material stories have native ES/ZH editions.

Publication remains fail-open to canonical English, but localization health is a
separate SLO: a missing native edition may exist briefly while upstream ARB lands
its authored overlay, then becomes an explicit unhealthy production condition.
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
        (overdue if age_h > args.grace_hours else grace).append(item)

    state = "HEALTHY"
    if overdue:
        state = "UNHEALTHY_TRANSLATION_BACKLOG"
    elif grace:
        state = "DEGRADED_TRANSLATION_GRACE"
    payload = {
        "stage": "TRANSLATION_HEALTH",
        "state": state,
        "target": "native es-419 and zh-Hans at publication time",
        "grace_hours": args.grace_hours,
        "fresh_window_hours": args.fresh_window_hours,
        "missing_recent": watched,
        "overdue_count": len(overdue),
        "grace_count": len(grace),
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if overdue else 0


if __name__ == "__main__":
    raise SystemExit(main())
