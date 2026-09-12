#!/usr/bin/env python3
"""Promote the current Story layer onto the reader-facing front page.

The autonomous newsroom writes ``data/stories.json`` after public research. The
reader page exists in two deterministic templates during the publication path:
``site/`` uses a compact ``hero`` lead while the frozen Signal Field overlay uses
``lead``. Both must project the exact same current Story lead or publication
fails closed.

The frozen Signal Field release is also a client-rendered SPA. Updating static
HTML alone is not sufficient: its ``home()`` renderer and interactive Signal
Field historically pinned a specific research ID and could overwrite a freshly
promoted lead after JavaScript ran. This promoter therefore binds both the
static candidate and the runtime homepage to the same Story identity.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path


PUBLIC_ID = re.compile(r"^FCMO-[0-9A-F]{12}$")


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
    """Bind the SPA homepage renderer to the exact promoted Story lead.

    The frozen release contains client-side ``home()`` and ``initPlot()`` code.
    Both used to pin an old FCMO ID. The browser then replaced correct static
    publication bytes with the stale record, so source-level deployment checks
    could pass while readers still saw yesterday's headline.

    This is intentionally a narrow post-overlay transform. If the SPA runtime is
    present but its expected anchors drift, fail closed rather than silently
    shipping an unverified homepage.
    """
    rid = str(story.get("research_id") or "")
    if not PUBLIC_ID.fullmatch(rid):
        raise SystemExit(f"front-page build refused: invalid Story research_id {rid!r}")

    has_runtime = "function home()" in text or "function initPlot()" in text
    if not has_runtime:
        return text, False

    # home(): the editorial lead must be the same identity as stories[0].
    text, home_id_count = re.subn(
        r"const lead=record\('FCMO-[0-9A-F]{12}'\)\|\|ranked\[0\];",
        f"const lead=record('{rid}')||ranked[0];",
        text,
        count=1,
    )

    # The legacy homepage encoded its old lead as prose instead of rendering the
    # selected record title. Make headline identity data-driven so later releases
    # cannot regress merely because the Story lead changes.
    legacy_headline = (
        '<h2>Agents crossed the boundary between <em>evaluation</em> and the real world.</h2>'
    )
    runtime_headline = '<h2>${esc(lead.title)}</h2>'
    headline_count = 0
    if legacy_headline in text:
        text = text.replace(legacy_headline, runtime_headline, 1)
        headline_count = 1
    elif runtime_headline in text:
        headline_count = 1

    # initPlot(): orange lead node/readout must track the same Story identity.
    text, plot_id_count = re.subn(
        r"const leadId='FCMO-[0-9A-F]{12}'",
        f"const leadId='{rid}'",
        text,
        count=1,
    )

    if home_id_count != 1 or headline_count != 1 or plot_id_count != 1:
        raise SystemExit(
            "front-page build refused: SPA runtime anchors drifted "
            f"(home_id={home_id_count}, headline={headline_count}, plot_id={plot_id_count})"
        )

    # Strong source invariant for the runtime itself. The runtime may still carry
    # historical records elsewhere; only its explicit homepage selectors matter.
    if f"const lead=record('{rid}')||ranked[0];" not in text:
        raise SystemExit("front-page build refused: runtime home lead was not rebound")
    if f"const leadId='{rid}'" not in text:
        raise SystemExit("front-page build refused: runtime Signal Field lead was not rebound")
    if runtime_headline not in text:
        raise SystemExit("front-page build refused: runtime headline is not data-driven")
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

    # Frozen Signal Field candidate.
    text2, lead_count = re.subn(
        r'<section class="lead"(?:\s[^>]*)?>.*?</section>',
        signal_lead_html(lead), text, count=1, flags=re.S,
    )
    template = "lead"
    if lead_count == 1:
        text = text2
    else:
        # Autonomous newsroom source prior to overlay.
        text2, hero_count = re.subn(
            r'<section class="hero"(?:\s[^>]*)?>.*?</section>',
            compact_hero_html(lead), text, count=1, flags=re.S,
        )
        if hero_count != 1:
            raise SystemExit("front-page build refused: neither reader lead template was found exactly once")
        text = text2
        template = "hero"

    # Crucial: the browser runtime is another publication layer. Bind it after
    # static promotion so JavaScript cannot put a stale Story back on screen.
    text, runtime_bound = bind_runtime_home(text, lead)

    text = re.sub(
        r'(<div class="issue-stamp">.*?<strong>)(.*?)(</strong>)',
        lambda m: m.group(1) + esc(date_label(lead)) + m.group(3),
        text, count=1, flags=re.S,
    )

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
    runtime_note = "; SPA runtime bound" if runtime_bound else ""
    print(
        f"front page promoted ({template}{runtime_note}): "
        f"{lead['research_id']} :: {expected_headline}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
