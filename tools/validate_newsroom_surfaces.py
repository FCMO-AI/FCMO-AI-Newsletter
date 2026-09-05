#!/usr/bin/env python3
"""Validate Airlock-v2 newsroom surfaces once an autonomous receipt exists.

The pre-Airlock release is allowed exactly as a migration state. Presence of
``data/newsroom-status.json`` permanently activates the stricter contract: story parity,
clean-room research provenance, media rights, localized routes, NewsArticle metadata and
both sitemaps must all exist together.
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.validate_media_rights import main as _media_cli  # imported only for compile visibility


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(site: Path) -> list[str]:
    errors: list[str] = []
    status_path = site / "data" / "newsroom-status.json"
    if not status_path.is_file():
        print("newsroom surface gate: migration release has no autonomous receipt; strict gate not yet activated")
        return errors
    try:
        status = load(status_path)
    except Exception as exc:
        return [f"newsroom-status.json is invalid: {exc}"]
    if status.get("state") != "HEALTHY":
        errors.append("newsroom status is not HEALTHY")
    if status.get("public_delta_state") not in {"PUBLIC_DELTA", "NO_PUBLIC_DELTA"}:
        errors.append("newsroom status has invalid public_delta_state")
    if not str(status.get("release_id") or "").startswith("FCMO-NEWSWIRE-"):
        errors.append("newsroom status lacks FCMO-NEWSWIRE release identity")

    brief_ids = {path.stem for path in (site / "data" / "briefs").glob("FCMO-*.json")}
    try:
        stories = load(site / "data" / "stories.json")
    except Exception as exc:
        errors.append(f"stories.json is missing/invalid: {exc}")
        stories = []
    story_ids: set[str] = set()
    for item in stories if isinstance(stories, list) else []:
        ids = item.get("research_ids") if isinstance(item, dict) else None
        if not isinstance(ids, list) or len(ids) != 1 or ids[0] not in brief_ids:
            errors.append(f"malformed Story research identity: {item!r}"[:400])
            continue
        identifier = ids[0]
        story_ids.add(identifier)
        if item.get("story_id") != f"STORY-{identifier}":
            errors.append(f"{identifier}: Story ID mismatch")
        if item.get("disposition") not in {"LEAD", "STANDARD", "BRIEF", "SIGNAL", "DATABASE_ONLY"}:
            errors.append(f"{identifier}: invalid Story disposition")
        if item.get("publication_event") not in {"CURRENT", "CORRECTION", "RETRACTION", "SUPERSESSION"}:
            errors.append(f"{identifier}: invalid publication_event")
        research_url = item.get("public_research_url")
        if research_url:
            research_path = site.parent / "site" / str(research_url)
            # In assembled publish/ the same file lives directly under data/. This
            # source-tree gate runs before assembly, where clean-room records persist
            # under the repository's public site/ base.
            if not research_path.is_file():
                errors.append(f"{identifier}: clean-room research pointer is missing")
    if story_ids != brief_ids:
        errors.append(
            f"Story/brief parity mismatch missing={sorted(brief_ids-story_ids)} extra={sorted(story_ids-brief_ids)}"
        )

    try:
        media = load(site / "data" / "media.json")
        media_ids = {item.get("id") for item in media if isinstance(item, dict)}
        if media_ids != brief_ids:
            errors.append("media/brief parity mismatch")
    except Exception as exc:
        errors.append(f"media.json is invalid: {exc}")

    for identifier in sorted(brief_ids):
        for segment in ("en", "es", "zh-hans"):
            if not (site / segment / "developments" / f"{identifier}.html").is_file():
                errors.append(f"{identifier}: missing localized {segment} story route")

    try:
        articles = load(site / "data" / "news-articles.json")
        if set(articles) != brief_ids:
            errors.append("NewsArticle/brief parity mismatch")
        for identifier, article in articles.items():
            if article.get("@type") != "NewsArticle" or not article.get("headline"):
                errors.append(f"{identifier}: invalid NewsArticle metadata")
    except Exception as exc:
        errors.append(f"news-articles.json is invalid: {exc}")

    for rel in ("sitemap.xml", "news-sitemap.xml"):
        try:
            ET.parse(site / rel)
        except Exception as exc:
            errors.append(f"{rel} is invalid XML: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    args = parser.parse_args()
    errors = validate(args.site)
    if errors:
        print("autonomous newsroom surface gate FAILED")
        for error in errors:
            print("-", error)
        return 1
    print("autonomous newsroom surface gate OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
