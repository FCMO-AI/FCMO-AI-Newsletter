#!/usr/bin/env python3
"""Promote the current Story layer onto the reader-facing front page.

The autonomous newsroom writes ``data/stories.json`` after public research. The
legacy front page used to survive independently of that Story layer, allowing a
successful Pages deploy to keep showing an old lead. This deterministic step
makes the visible lead story a projection of the exact Story layer being served.
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
    return (
        str(nv.get("evidence") or "?"),
        str(nv.get("confidence") or "unrated"),
        str(nv.get("importance") or "?"),
    )


def lead_html(story: dict) -> str:
    evidence, confidence, importance = badge_text(story)
    href = story_href(story)
    headline = esc(story.get("headline"))
    summary = esc(story.get("dek"))
    why = esc(story.get("why_it_matters"))
    published = esc(date_label(story))
    story_type = esc(story.get("story_type") or "Research")
    return (
        '<section class="lead" data-current-story-lead="true">'
        '<div class="lead-inner">'
        '<aside class="lead-rail">'
        '<div class="section-code">Front Page / Current Lead</div>'
        '<dl>'
        f'<div><dt>Evidence</dt><dd>{esc(evidence)}</dd></div>'
        f'<div><dt>Confidence</dt><dd>{esc(confidence)}</dd></div>'
        f'<div class="impact"><dt>Impact</dt><dd>{esc(importance)}/10</dd></div>'
        f'<div><dt>Published</dt><dd>{published}</dd></div>'
        '</dl></aside>'
        '<div class="lead-body">'
        f'<div class="label">{story_type}</div>'
        f'<h2><a href="{esc(href)}" style="color:inherit;text-decoration:none">{headline}</a></h2>'
        f'<p class="lead-summary">{summary}</p>'
        '<div class="lead-actions">'
        f'<a href="{esc(href)}">Read the verified dossier</a>'
        f'<span>{esc(story.get("research_id"))}</span>'
        '</div></div>'
        '<aside class="evidence-ledger">'
        '<div class="section-code">Why it matters</div>'
        '<h3>Material consequence</h3>'
        f'<p>{why}</p>'
        f'<div class="ledger-row"><span>Evidence</span><strong>{esc(evidence)}</strong></div>'
        f'<div class="ledger-row"><span>Confidence</span><strong>{esc(confidence)}</strong></div>'
        f'<div class="ledger-row"><span>Story</span><strong>{story_type}</strong></div>'
        '</aside></div></section>'
    )


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

    lead = stories[0]
    text = index_path.read_text(encoding="utf-8")

    # Signal Field's reader-visible story headline lives in the dark `.lead`
    # section. Replacing the masthead `.hero` would corrupt the publication brand
    # and still miss the actual stale headline readers reported.
    promoted, count = re.subn(
        r'<section class="lead"(?:\s[^>]*)?>.*?</section>',
        lead_html(lead),
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise SystemExit("front-page build refused: reader lead section was not found exactly once")
    text = promoted

    # Keep the visible issue/date stamp aligned with the current lead date without
    # making the publisher depend on a fragile full-page template rewrite.
    text = re.sub(
        r'(<div class="issue-stamp">.*?<strong>)(.*?)(</strong>)',
        lambda m: m.group(1) + esc(date_label(lead)) + m.group(3),
        text,
        count=1,
        flags=re.S,
    )

    marker = f'<!-- fcmo-story-lead:{esc(lead["research_id"])} -->'
    text = re.sub(r'<!-- fcmo-story-lead:[^>]+ -->\s*', '', text)
    if '</head>' not in text:
        raise SystemExit("front-page build refused: index.html has no closing head")
    text = text.replace('</head>', marker + '</head>', 1)

    # Self-check the exact bytes that will be handed to Pages.
    expected_headline = str(lead.get("headline") or "")
    expected_link = story_href(lead)
    if expected_headline not in html.unescape(text) or expected_link not in text or marker not in text:
        raise SystemExit("front-page build refused: promoted lead identity is not present in output")

    index_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"front page promoted: {lead['research_id']} :: {expected_headline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
