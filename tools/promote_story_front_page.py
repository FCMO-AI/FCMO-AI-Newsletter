#!/usr/bin/env python3
"""Promote the current Story layer onto the reader-facing front page.

The autonomous newsroom writes ``data/stories.json`` after public research. The
reader page exists in two deterministic templates during the publication path:
``site/`` uses a compact ``hero`` lead while the frozen Signal Field overlay uses
``lead``. Both must project the exact same current Story lead or publication
fails closed.

The frozen Signal Field release is also a client-rendered SPA. Updating static
HTML alone is not sufficient: historical release evolution left more than one
homepage/runtime implementation in the assembled document. Any one stale runtime
can repaint a correct static page after JavaScript executes. This promoter binds
*every* explicit homepage/Signal-Field lead selector, every legacy lead headline,
and every issue stamp to the current Story identity before deployment.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")
RUNTIME_LEAD = re.compile(r"lead=record\('FCMO-[0-9A-F]{12}'\)\|\|ranked\[0\]")
RUNTIME_PLOT_LEAD = re.compile(r"const leadId='FCMO-[0-9A-F]{12}'")
ISSUE_STAMP = re.compile(
    r'(<div class="issue-stamp">.*?<strong>)(.*?)(</strong>)', re.S
)


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


def signal_lead_html(story: dict) -> str:
    evidence, confidence, importance = badge_text(story)
    href = story_href(story)
    headline = esc(story.get("headline"))
    summary = esc(story.get("dek"))
    why = esc(story.get("why_it_matters"))
    published = esc(date_label(story))
    story_type = esc(story.get("story_type") or "Research")
    return (
        '<section class="lead" data-current-story-lead="true"><div class="lead-inner">'
        '<aside class="lead-rail"><div class="section-code">Front Page / Current Lead</div><dl>'
        f'<div><dt>Evidence</dt><dd>{esc(evidence)}</dd></div>'
        f'<div><dt>Confidence</dt><dd>{esc(confidence)}</dd></div>'
        f'<div class="impact"><dt>Impact</dt><dd>{esc(importance)}/10</dd></div>'
        f'<div><dt>Published</dt><dd>{published}</dd></div></dl></aside>'
        '<div class="lead-body">'
        f'<div class="label">{story_type}</div>'
        f'<h2><a href="{esc(href)}" style="color:inherit;text-decoration:none">{headline}</a></h2>'
        f'<p class="lead-summary">{summary}</p><div class="lead-actions">'
        f'<a href="{esc(href)}">Read the verified dossier</a><span>{esc(story.get("research_id"))}</span>'
        '</div></div><aside class="evidence-ledger"><div class="section-code">Why it matters</div>'
        f'<h3>Material consequence</h3><p>{why}</p>'
        f'<div class="ledger-row"><span>Evidence</span><strong>{esc(evidence)}</strong></div>'
        f'<div class="ledger-row"><span>Confidence</span><strong>{esc(confidence)}</strong></div>'
        f'<div class="ledger-row"><span>Story</span><strong>{story_type}</strong></div>'
        '</aside></div></section>'
    )


def compact_hero_html(story: dict) -> str:
    evidence, confidence, importance = badge_text(story)
    href = story_href(story)
    return (
        '<section class="hero" data-current-story-lead="true"><div>'
        '<div class="kicker">Top verified research</div>'
        f'<h2><a href="{esc(href)}">{esc(story.get("headline"))}</a></h2>'
        f'<span class="badge">Evidence {esc(evidence)}</span>'
        f'<span class="badge">{esc(confidence)}</span>'
        f'<span class="badge impact">Impact {esc(importance)}/10</span>'
        f'<span class="badge">{esc(story.get("story_type") or "Research")}</span>'
        f'<p>{esc(story.get("dek"))}</p>'
        f'<p><strong>Why it matters:</strong> {esc(story.get("why_it_matters"))}</p>'
        '</div><aside><div class="kicker">Current newsroom date</div>'
        f'<h3>{esc(date_label(story))}</h3>'
        '<p>Front-page placement is rebuilt from the current verified Story layer.</p>'
        f'<p><a href="{esc(href)}">Read the current lead dossier</a></p>'
        '</aside></section>'
    )


def bind_runtime_home(text: str, story: dict) -> tuple[str, bool]:
    """Bind every SPA homepage renderer to the exact promoted Story lead.

    Release history can legitimately contain multiple isolated runtime blocks.
    The rule is therefore universal rather than first-match: after this function
    returns, no explicit homepage selector may point at any other stable FCMO ID.
    """
    rid = str(story.get("research_id") or "")
    if not PUBLIC_ID.fullmatch(rid):
        raise SystemExit(f"front-page build refused: invalid Story research_id {rid!r}")

    has_runtime = "function home()" in text or "function initPlot()" in text
    if not has_runtime:
        return text, False

    text, home_id_count = RUNTIME_LEAD.subn(
        f"lead=record('{rid}')||ranked[0]", text
    )

    legacy_headline = (
        '<h2>Agents crossed the boundary between <em>evaluation</em> and the real world.</h2>'
    )
    runtime_headline = '<h2>${esc(lead.title)}</h2>'
    legacy_count = text.count(legacy_headline)
    if legacy_count:
        text = text.replace(legacy_headline, runtime_headline)

    text, plot_id_count = RUNTIME_PLOT_LEAD.subn(
        f"const leadId='{rid}'", text
    )

    # The date badge was another historical literal embedded in each runtime.
    # Bind all copies to the same current Story date; leaving even one old copy is
    # enough for a later-executing runtime to make the site look rolled back.
    issue_date = esc(date_label(story))
    text, issue_count = ISSUE_STAMP.subn(
        lambda m: m.group(1) + issue_date + m.group(3), text
    )

    if home_id_count < 1 or plot_id_count < 1 or issue_count < 1:
        raise SystemExit(
            "front-page build refused: SPA runtime anchors are incomplete "
            f"(home_ids={home_id_count}, plot_ids={plot_id_count}, issue_stamps={issue_count})"
        )

    # Every explicit homepage selector must now resolve to the same Story. This
    # catches duplicate or newly-added runtimes instead of silently patching only
    # whichever implementation happened to appear first in the file.
    expected_home = f"lead=record('{rid}')||ranked[0]"
    home_values = RUNTIME_LEAD.findall(text)
    if not home_values or any(value != expected_home for value in home_values):
        raise SystemExit("front-page build refused: a stale runtime home lead survived binding")

    expected_plot = f"const leadId='{rid}'"
    plot_values = RUNTIME_PLOT_LEAD.findall(text)
    if not plot_values or any(value != expected_plot for value in plot_values):
        raise SystemExit("front-page build refused: a stale Signal Field lead survived binding")

    if legacy_headline in text:
        raise SystemExit("front-page build refused: legacy hard-coded lead headline survived binding")
    if runtime_headline not in text:
        raise SystemExit("front-page build refused: runtime headline is not data-driven")

    # Preserve the counts in the build log: more than one is not itself an error,
    # but it proves why universal binding is necessary and keeps future drift visible.
    print(
        "front-page runtime binding: "
        f"home_selectors={home_id_count}; plot_selectors={plot_id_count}; "
        f"legacy_headlines={legacy_count}; issue_stamps={issue_count}"
    )
    return text, True


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

    text2, lead_count = re.subn(
        r'<section class="lead"(?:\s[^>]*)?>.*?</section>',
        signal_lead_html(lead), text, count=1, flags=re.S,
    )
    template = "lead"
    if lead_count == 1:
        text = text2
    else:
        text2, hero_count = re.subn(
            r'<section class="hero"(?:\s[^>]*)?>.*?</section>',
            compact_hero_html(lead), text, count=1, flags=re.S,
        )
        if hero_count != 1:
            raise SystemExit("front-page build refused: neither reader lead template was found exactly once")
        text = text2
        template = "hero"

    text, runtime_bound = bind_runtime_home(text, lead)

    marker = f'<!-- fcmo-story-lead:{esc(lead["research_id"])} -->'
    text = re.sub(r'<!-- fcmo-story-lead:[^>]+ -->\s*', '', text)
    if '</head>' not in text:
        raise SystemExit("front-page build refused: index.html has no closing head")
    text = text.replace('</head>', marker + '</head>', 1)

    expected_headline = str(lead.get("headline") or "")
    expected_link = story_href(lead)
    if expected_headline not in html.unescape(text) or expected_link not in text or marker not in text:
        raise SystemExit("front-page build refused: promoted lead identity is not present in output")

    index_path.write_text(text, encoding="utf-8", newline="\n")
    runtime_note = "; all SPA runtimes bound" if runtime_bound else ""
    print(
        f"front page promoted ({template}{runtime_note}): "
        f"{lead['research_id']} :: {expected_headline}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
