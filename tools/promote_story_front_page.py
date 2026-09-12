#!/usr/bin/env python3
"""Promote the current Story layer onto the reader-facing front page.

The autonomous newsroom writes ``data/stories.json`` after public research.  The
legacy front page used to survive independently of that Story layer, allowing a
successful Pages deploy to keep showing an old lead.  This deterministic step
makes the visible front page a projection of the exact Story layer being served.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def story_href(story: dict) -> str:
    rid = str(story.get("research_id") or "")
    if not rid:
        raise SystemExit("front-page build refused: Story is missing research_id")
    return f"/FCMO-AI-Newsletter/news/en/{rid}.html"


def date_label(story: dict) -> str:
    raw = str(story.get("modified_at") or story.get("published_at") or "")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return raw[:10] or "current"


def badge_text(story: dict) -> tuple[str, str, str]:
    nv = story.get("news_value") or {}
    evidence = str(nv.get("evidence") or "?")
    confidence = str(nv.get("confidence") or "unrated")
    importance = str(nv.get("importance") or "?")
    return evidence, confidence, importance


def hero_html(story: dict) -> str:
    evidence, confidence, importance = badge_text(story)
    return (
        '<section class="hero"><div>'
        '<div class="kicker">Top verified research</div>'
        f'<h2><a href="{esc(story_href(story))}">{esc(story.get("headline"))}</a></h2>'
        f'<span class="badge">Evidence {esc(evidence)}</span>'
        f'<span class="badge">{esc(confidence)}</span>'
        f'<span class="badge impact">Impact {esc(importance)}/10</span>'
        f'<span class="badge">{esc(story.get("story_type") or "current")}</span>'
        f'<p>{esc(story.get("dek"))}</p>'
        f'<p><strong>Why it matters:</strong> {esc(story.get("why_it_matters"))}</p>'
        '</div><aside><div class="kicker">Current newsroom date</div>'
        f'<h3>{esc(date_label(story))}</h3>'
        '<p>The front page is rebuilt from the current verified Story layer on every autonomous refresh.</p>'
        '<p><a href="/FCMO-AI-Newsletter/news/en/">Read the current English edition</a></p>'
        '</aside></section>'
    )


def grid_html(stories: list[dict]) -> str:
    cards: list[str] = []
    for story in stories:
        evidence, confidence, importance = badge_text(story)
        cards.append(
            '<article class="card">'
            f'<div class="kicker">{esc(story.get("story_type") or "Research")}</div>'
            f'<h3><a href="{esc(story_href(story))}">{esc(story.get("headline"))}</a></h3>'
            f'<span class="badge">Evidence {esc(evidence)}</span>'
            f'<span class="badge">{esc(confidence)}</span>'
            f'<span class="badge impact">Impact {esc(importance)}/10</span>'
            f'<p>{esc(story.get("dek"))}</p>'
            '</article>'
        )
    return '<section class="grid">' + ''.join(cards) + '</section>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args()
    site = args.site
    stories_path = site / "data" / "stories.json"
    index_path = site / "index.html"
    stories = json.loads(stories_path.read_text(encoding="utf-8"))
    if not isinstance(stories, list) or not stories:
        raise SystemExit("front-page build refused: Story layer is empty")
    if not index_path.is_file():
        raise SystemExit("front-page build refused: index.html is missing")

    text = index_path.read_text(encoding="utf-8")
    promoted = re.sub(r'<section class="hero">.*?</section>', hero_html(stories[0]), text, count=1, flags=re.S)
    if promoted == text:
        raise SystemExit("front-page build refused: hero section was not found")
    text = promoted
    promoted = re.sub(r'<section class="grid">.*?</section>', grid_html(stories[1:13]), text, count=1, flags=re.S)
    if promoted == text:
        raise SystemExit("front-page build refused: research grid was not found")
    text = promoted

    marker = f'<!-- fcmo-story-lead:{esc(stories[0]["research_id"])} -->'
    text = re.sub(r'<!-- fcmo-story-lead:[^>]+ -->\s*', '', text)
    text = text.replace('</head>', marker + '</head>', 1)
    index_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"front page promoted: {stories[0]['research_id']} :: {stories[0].get('headline')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
