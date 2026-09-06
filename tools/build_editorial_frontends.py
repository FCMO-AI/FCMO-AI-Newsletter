#!/usr/bin/env python3
"""Build first-class editorial/discovery frontends from public newsroom data.

Story pages remain owned by build_newsroom_surfaces.py. This second deterministic
stage turns archive/search/topics/organizations/corrections/feeds/method/status and
error routes into native publication surfaces without reading private research state.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_PATH = "/FCMO-AI-Newsletter"
BASE_URL = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def href(path: str = "") -> str:
    path = path.lstrip("/")
    return f"{BASE_PATH}/{path}" if path else f"{BASE_PATH}/"


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"
    # Footnote: the hash suffix prevents two Unicode-heavy or punctuation-heavy
    # organization names from collapsing onto the same filesystem route.
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:6]
    return f"{text[:64]}-{suffix}"


def dt(value: Any) -> datetime:
    text = str(value or "").replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def story_link(row: dict[str, Any], locale: str = "en") -> str:
    rid = str(row.get("id") or row.get("research_id") or "")
    if not rid.startswith("FCMO-"):
        return href("news/en/")
    story_id = f"STORY-{rid[5:]}"
    loc = {"en": "en", "es-419": "es", "zh-Hans": "zh-hans"}.get(locale, "en")
    return href(f"news/{loc}/{story_id}.html")


def page(title: str, kicker: str, body: str, description: str = "") -> str:
    desc = description or "FCMO AI Newsletter — evidence-first autonomous AI research journalism."
    nav = "".join(
        f'<a href="{href(path)}">{label}</a>' for path, label in (
            ("", "Latest"), ("archive.html", "Archive"), ("search.html", "Search"),
            ("topics.html", "Topics"), ("organizations.html", "Organizations"),
            ("corrections.html", "Corrections"), ("feeds.html", "Feeds"),
            ("methodology.html", "Method"), ("status.html", "Status"),
        )
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · FCMO AI Newsletter</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE_URL}/{esc(title.lower().replace(' ', '-'))}">
<link rel="stylesheet" href="{href('assets/editorial-frontends.css')}">
</head><body><header class="mast"><a class="brand" href="{href()}">FCMO <span>AI</span> Newsletter</a>
<div class="rule"></div><nav aria-label="Publication">{nav}</nav></header>
<main><p class="kicker">{esc(kicker)}</p>{body}</main>
<footer><strong>FCMO AI Newsletter</strong><span>Evidence, confidence and impact are separate signals.</span>
<span><a href="{href('editorial-policy.html')}">Editorial policy</a> · <a href="{href('automation.html')}">Automation</a> · <a href="{href('accessibility.html')}">Accessibility</a></span></footer>
<script src="{href('assets/editorial-frontends.js')}" defer></script></body></html>'''


def signal(row: dict[str, Any]) -> str:
    score = row.get("importance_effective_score") or row.get("importance_score") or "—"
    return (
        f'<span class="signal">EVIDENCE {esc(row.get("evidence_class") or "—")}</span>'
        f'<span class="signal">{esc(row.get("confidence") or "—")}</span>'
        f'<span class="signal strong">IMPACT {esc(score)}/10</span>'
    )


def item(row: dict[str, Any], eyebrow: str | None = None) -> str:
    title = row.get("title") or row.get("headline") or "Untitled"
    summary = row.get("summary") or row.get("dek") or ""
    meta = eyebrow or row.get("primary_desk") or row.get("development_type") or "Research"
    return f'''<article class="index-item"><div class="item-meta">{esc(meta)}</div>
<h2><a href="{story_link(row)}">{esc(title)}</a></h2><div class="signals">{signal(row)}</div>
<p>{esc(summary)}</p></article>'''


def build_archive(rows: list[dict[str, Any]]) -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        stamp = row.get("event_at") or row.get("recorded_at") or row.get("last_verified_at")
        groups[dt(stamp).strftime("%Y-%m")].append(row)
    sections = []
    for month in sorted(groups, reverse=True):
        ordered = sorted(groups[month], key=lambda r: dt(r.get("event_at") or r.get("recorded_at")), reverse=True)
        sections.append(f'<section class="timeline"><div class="timeline-date">{esc(month)}</div><div>{"".join(item(r) for r in ordered)}</div></section>')
    body = f'''<header class="page-head"><h1>Archive</h1><p>A chronological evidence spine, not an engagement feed. Older reporting stays addressable while current assessments can evolve.</p></header>
<div class="metric-line"><strong>{len(rows)}</strong><span>public research records</span><span>ordered by event / record time</span></div>{''.join(sections) or '<p class="empty">No public records yet.</p>'}'''
    return page("Archive", "TIME / EVIDENCE", body)


def build_search(rows: list[dict[str, Any]]) -> str:
    body = f'''<header class="page-head"><h1>Search the research</h1><p>Search titles, mechanisms, organizations, topics and evidence summaries locally in your browser.</p></header>
<section class="search-tool" data-search-root data-source="{href('data/search.json')}">
<label for="fcmo-search">QUERY</label><input id="fcmo-search" type="search" autocomplete="off" placeholder="agent memory, speculative decoding, DeepMind…">
<div class="search-filters"><select data-filter="evidence"><option value="">All evidence</option><option>A</option><option>B</option><option>C</option><option>D</option></select>
<select data-filter="impact"><option value="">All impact</option><option value="8">8+ field-shifting</option><option value="6">6+ major</option><option value="4">4+ notable</option></select></div>
<p class="search-count"><span data-search-count>{len(rows)}</span> matching records</p><div data-search-results>{''.join(item(r) for r in rows[:12])}</div></section>'''
    return page("Search", "INSTRUMENT / QUERY", body)


def build_facets(rows: list[dict[str, Any]], key: str, title: str, kicker: str, route: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for value in row.get(key) or []:
            if isinstance(value, str) and value.strip():
                mapping[value.strip()].append(row)
    ordered = sorted(mapping.items(), key=lambda pair: (-len(pair[1]), pair[0].lower()))
    links: dict[str, str] = {}
    index_rows = []
    for name, members in ordered:
        s = slug(name)
        links[name] = f"{route}/{s}.html"
        index_rows.append(
            f'<a class="facet-row" href="{href(links[name])}"><span>{esc(name)}</span><strong>{len(members)}</strong><i>{esc(members[0].get("title") or "")}</i></a>'
        )
    intro = "A map of recurring research beats and mechanisms." if key == "topics" else "Organizations appearing in public evidence, indexed by coverage rather than prestige."
    body = f'''<header class="page-head"><h1>{esc(title)}</h1><p>{esc(intro)}</p></header>
<div class="metric-line"><strong>{len(mapping)}</strong><span>{esc(key)}</span><span>{len(rows)} records mapped</span></div><section class="facet-list">{''.join(index_rows) or '<p class="empty">No facets yet.</p>'}</section>'''
    return page(title, kicker, body), links


def build_facet_pages(site: Path, rows: list[dict[str, Any]], key: str, route: str, links: dict[str, str]) -> None:
    mapping: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for value in row.get(key) or []:
            if value in links:
                mapping[value].append(row)
    out = site / route
    out.mkdir(parents=True, exist_ok=True)
    for name, members in mapping.items():
        ordered = sorted(members, key=lambda r: (int(r.get("importance_effective_score") or r.get("importance_score") or 0), dt(r.get("last_verified_at"))), reverse=True)
        label = "TOPIC" if key == "topics" else "ORGANIZATION"
        body = f'''<header class="page-head"><p class="back"><a href="{href(route + '.html')}">← All {esc(route)}</a></p><h1>{esc(name)}</h1><p>{len(ordered)} evidence-bearing public record{'s' if len(ordered) != 1 else ''}.</p></header>{''.join(item(r) for r in ordered)}'''
        (out / Path(links[name]).name).write_text(page(name, f"{label} / COVERAGE", body), encoding="utf-8")


def build_corrections(corrections: list[Any]) -> str:
    if corrections:
        rows = []
        for entry in corrections:
            if not isinstance(entry, dict):
                continue
            rows.append(f'''<article class="correction"><time>{esc(entry.get('date') or entry.get('modified_at') or '')}</time><h2>{esc(entry.get('title') or entry.get('story_id') or 'Correction')}</h2><p>{esc(entry.get('summary') or entry.get('note') or '')}</p></article>''')
        content = "".join(rows)
    else:
        content = '''<div class="empty-state"><strong>NO MATERIAL CORRECTIONS RECORDED</strong><p>This is not a claim of infallibility. When a material factual correction, retraction or supersession occurs, the ledger will preserve it here instead of silently rewriting history.</p></div>'''
    body = f'''<header class="page-head"><h1>Corrections ledger</h1><p>Corrections are publication events. Material changes remain visible and dated.</p></header>{content}'''
    return page("Corrections", "ACCOUNTABILITY / LEDGER", body)


def build_feeds() -> str:
    surfaces = (
        ("RSS", "feed.xml", "Reader and aggregator subscription."),
        ("JSON Feed", "feed.json", "Structured story feed."),
        ("Search JSON", "data/search.json", "Public discovery index."),
        ("Research JSONL", "data/developments.jsonl", "One public evidence record per line."),
        ("Stories JSON", "data/stories.json", "Newspaper Story layer."),
        ("News sitemap", "news-sitemap.xml", "Recent news URLs for crawlers."),
        ("Sitemap", "sitemap.xml", "Public route inventory."),
        ("llms.txt", "llms.txt", "Compact machine orientation."),
        ("llms-full.txt", "llms-full.txt", "Expanded machine-readable publication context."),
        ("Agent API", "agent.json", "Agent-oriented publication metadata."),
    )
    body = '''<header class="page-head"><h1>Feeds & machine surfaces</h1><p>The newspaper is equally addressable by humans, readers, search engines and agents. These are publication interfaces, not internal repository exports.</p></header><section class="feed-list">''' + "".join(
        f'<a href="{href(path)}"><strong>{esc(name)}</strong><span>{esc(note)}</span><code>{esc(path)}</code></a>' for name, path, note in surfaces
    ) + "</section>"
    return page("Feeds", "DISTRIBUTION / OPEN SURFACES", body)


def build_methodology() -> str:
    body = '''<header class="page-head"><h1>How the newsroom works</h1><p>Research depth stays upstream; public claims must survive an explicit declassification and evidence boundary.</p></header>
<section class="method-flow"><div><b>01</b><h2>Research</h2><p>Agents discover, deduplicate, verify and preserve contradictions using public evidence.</p></div><div><b>02</b><h2>Declassify</h2><p>Only public-reconstructable evidence crosses the airlock. Internal strategic analysis stays internal.</p></div><div><b>03</b><h2>Edit ×3</h2><p>The same ARB editorial task writes English, Spanish and Simplified Chinese editions before publication.</p></div><div><b>04</b><h2>Validate</h2><p>Deterministic gates protect identifiers, numbers, links, locale coverage, privacy, structure and release integrity.</p></div><div><b>05</b><h2>Publish</h2><p>Static pages, feeds and machine surfaces are generated from the same public evidence set.</p></div></section>
<section class="prose"><h2>Evidence is not importance</h2><p>A high-impact possibility can still be weak evidence. FCMO keeps evidence class, confidence and potential consequence separate so dramatic implications do not upgrade truth status.</p><h2>What the public edition does not contain</h2><p>Private consumer relevance, internal hypotheses, experiment plans, credentials, control-plane state and strategically sensitive deductions are outside the publication contract.</p></section>'''
    return page("Methodology", "METHOD / RECONSTRUCTABILITY", body)


def build_policy() -> str:
    body = '''<header class="page-head"><h1>Editorial policy</h1><p>Maximum useful public understanding without laundering uncertainty or leaking private strategy.</p></header><section class="prose"><h2>Source hierarchy</h2><p>Primary papers, official technical artifacts, standards, code and direct attributable evidence are preferred. First-party claims are labeled as claims until stronger evidence exists.</p><h2>Story selection</h2><p>News value combines consequence, evidence, novelty, freshness and public relevance. There is no fixed story quota; a quiet day may be quiet.</p><h2>Corrections</h2><p>Material factual changes receive correction, retraction or supersession treatment. Publication dates are not artificially refreshed to manufacture recency.</p><h2>Images</h2><p>Visuals must have a defensible reuse basis and provenance. Original charts and clearly labeled editorial illustrations are preferred over untraceable web images.</p></section>'''
    return page("Editorial policy", "POLICY / TRUTH", body)


def build_automation() -> str:
    body = '''<header class="page-head"><h1>Automation disclosure</h1><p>FCMO AI Newsletter is an autonomous publication, not a fake human newsroom.</p></header><section class="prose"><h2>What is automated</h2><p>FCMO research agents perform discovery, evidence synthesis and editorial preparation. The publication agent prepares the English, Spanish and Simplified Chinese editions together. GitHub Actions then performs deterministic validation, compilation and deployment.</p><h2>What does not happen at runtime</h2><p>The website does not generate articles or translations when a reader opens a page. Published text is source-controlled publication material that has already crossed the release gates.</p><h2>Accountability</h2><p>Automation does not weaken evidence standards. Claims, limitations, public sources, corrections and publication receipts remain inspectable.</p></section>'''
    return page("Automation", "AUTONOMOUS / DISCLOSED", body)


def build_accessibility() -> str:
    body = '''<header class="page-head"><h1>Accessibility</h1><p>The publication is designed to remain legible, navigable and useful without animation or pointer-only interaction.</p></header><section class="prose"><h2>Current commitments</h2><p>Semantic headings, visible focus states, keyboard-operable search controls, high-contrast text, responsive layouts and meaningful link text are part of the frontend contract. Motion is non-essential and honors reduced-motion preferences.</p><h2>Known boundary</h2><p>Third-party source pages and external media are outside FCMO's control. Where an image is editorially important, the publication should carry useful alternative text and provenance.</p></section>'''
    return page("Accessibility", "ACCESS / LEGIBILITY", body)


def build_status(status: dict[str, Any], stories: list[dict[str, Any]]) -> str:
    release = status.get("release_id") or status.get("received_release_id") or "not reported"
    verified = status.get("live_verified_at") or status.get("generated_at") or "not reported"
    body = f'''<header class="page-head"><h1>Newsroom status</h1><p>Operational evidence is surfaced without exposing private control-plane state.</p></header>
<section class="status-grid"><div><span>PUBLIC STORIES</span><strong>{len(stories)}</strong></div><div><span>RELEASE</span><strong class="mono">{esc(release)}</strong></div><div><span>LAST VERIFIED</span><strong>{esc(verified)}</strong></div></section>
<section class="prose"><h2>Healthy means more than “the workflow was green”</h2><p>A valid publication run requires a fresh airlock heartbeat, a complete three-language story set, successful privacy and release gates, deterministic build output and a deployable static candidate. A quiet release may have no content delta; a missing or stale upstream heartbeat is not treated as quiet.</p></section>'''
    return page("Status", "OPERATIONS / EVIDENCE", body)


def build_not_found() -> str:
    body = f'''<section class="not-found"><p class="code404">404</p><h1>This route is not in the edition.</h1><p>Use the research index instead of guessing around a dead link.</p><p><a class="action" href="{href('search.html')}">Search the newsroom →</a></p></section>'''
    return page("Not found", "ROUTE / ABSENT", body)


def build_language_gateway() -> str:
    body = f'''<header class="page-head"><h1>Read the native edition</h1><p>Three editorial editions are prepared before publication; language choice is not a runtime translation service.</p></header><section class="language-gateway">
<a lang="en" href="{href('news/en/')}"><small>EN</small><strong>English</strong><span>Canonical semantic edition</span></a>
<a lang="es" href="{href('news/es/')}"><small>ES</small><strong>Español</strong><span>Edición curada para español latinoamericano</span></a>
<a lang="zh-Hans" href="{href('news/zh-hans/')}"><small>中文</small><strong>简体中文</strong><span>简体中文编辑版</span></a></section>'''
    return page("Language editions", "LANGUAGE / NATIVE EDITIONS", body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args(argv)
    site = args.site
    rows = read_json(site / "data" / "search.json", [])
    stories = read_json(site / "data" / "stories.json", [])
    corrections = read_json(site / "data" / "corrections.json", [])
    status = read_json(site / "data" / "newsroom-status.json", {})
    if not isinstance(rows, list) or not isinstance(stories, list):
        raise SystemExit("editorial frontends: public search/story data missing")

    (site / "archive.html").write_text(build_archive(rows), encoding="utf-8")
    (site / "search.html").write_text(build_search(rows), encoding="utf-8")
    topics, topic_links = build_facets(rows, "topics", "Topics", "BEATS / MECHANISMS", "topics")
    orgs, org_links = build_facets(rows, "organizations", "Organizations", "ENTITIES / EVIDENCE", "organizations")
    (site / "topics.html").write_text(topics, encoding="utf-8")
    (site / "organizations.html").write_text(orgs, encoding="utf-8")
    build_facet_pages(site, rows, "topics", "topics", topic_links)
    build_facet_pages(site, rows, "organizations", "organizations", org_links)
    (site / "corrections.html").write_text(build_corrections(corrections if isinstance(corrections, list) else []), encoding="utf-8")
    (site / "feeds.html").write_text(build_feeds(), encoding="utf-8")
    (site / "methodology.html").write_text(build_methodology(), encoding="utf-8")
    (site / "editorial-policy.html").write_text(build_policy(), encoding="utf-8")
    (site / "automation.html").write_text(build_automation(), encoding="utf-8")
    (site / "accessibility.html").write_text(build_accessibility(), encoding="utf-8")
    (site / "status.html").write_text(build_status(status if isinstance(status, dict) else {}, stories), encoding="utf-8")
    (site / "404.html").write_text(build_not_found(), encoding="utf-8")
    news = site / "news"
    news.mkdir(parents=True, exist_ok=True)
    (news / "index.html").write_text(build_language_gateway(), encoding="utf-8")
    print(f"editorial frontends OK; records={len(rows)}; topics={len(topic_links)}; organizations={len(org_links)}; stories={len(stories)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
