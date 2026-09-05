#!/usr/bin/env python3
"""Build the autonomous public Story layer and multilingual news surfaces.

Research dossiers remain the evidence archive. This layer turns the same
sanitized public evidence into newspaper-shaped Story objects and static,
indexable EN/ES/ZH pages without importing any private ARB reasoning.
"""
from __future__ import annotations

import argparse
import copy
import html
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
LOCALES = {
    "en": {"slug": "en", "hreflang": "en", "name": "English"},
    "es-419": {"slug": "es", "hreflang": "es", "name": "Español"},
    "zh-Hans": {"slug": "zh-hans", "hreflang": "zh-Hans", "name": "简体中文"},
}
LABELS = {
    "en": {
        "latest": "Latest", "what_changed": "What actually changed", "evidence": "Claim vs. evidence",
        "baseline": "Strongest baseline", "caveat": "The caveat that matters", "unknown": "What remains unknown",
        "lens": "FCMO Lens", "sources": "Primary sources", "context": "Further public context",
        "method": "Autonomously researched and edited from cited public evidence. English is the canonical semantic edition.",
        "back": "FCMO AI Newsletter"
    },
    "es-419": {
        "latest": "Últimas", "what_changed": "Qué cambió realmente", "evidence": "Afirmación vs. evidencia",
        "baseline": "Baseline más fuerte", "caveat": "La salvedad que importa", "unknown": "Qué sigue sin saberse",
        "lens": "Lente FCMO", "sources": "Fuentes primarias", "context": "Contexto público adicional",
        "method": "Investigado y editado de forma autónoma a partir de evidencia pública citada. El inglés es la edición semántica canónica.",
        "back": "FCMO AI Newsletter"
    },
    "zh-Hans": {
        "latest": "最新", "what_changed": "真正发生了什么变化", "evidence": "主张与证据",
        "baseline": "最强基线", "caveat": "最重要的限制", "unknown": "仍然未知的部分",
        "lens": "FCMO 视角", "sources": "主要来源", "context": "更多公开背景",
        "method": "基于所引公开证据进行自主研究与编辑。英语版是语义上的权威版本。",
        "back": "FCMO AI Newsletter"
    }
}
CLAIM_LABELS = {
    "es-419": {"DEMONSTRATED": "DEMOSTRADO", "CLAIMED": "AFIRMADO", "INFERRED": "INFERIDO", "SPECULATIVE": "ESPECULATIVO", "DISPUTED": "DISPUTADO"},
    "zh-Hans": {"DEMONSTRATED": "已证实", "CLAIMED": "声称", "INFERRED": "推断", "SPECULATIVE": "推测", "DISPUTED": "有争议"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_briefs(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        obj = read_json(path)
        brief = obj.get("brief")
        if isinstance(brief, dict):
            result[brief["id"]] = brief
    return result


def load_locale_records(i18n_root: Path, locale: str) -> dict[str, dict[str, Any]]:
    if locale == "en":
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((i18n_root / locale).glob("part-*.json")):
        obj = read_json(path)
        rows = obj.get("records") or {}
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: locale records missing")
        result.update(rows)
    return result


def merge_overlay(source: Any, overlay: Any) -> Any:
    if isinstance(source, dict) and isinstance(overlay, dict):
        result = copy.deepcopy(source)
        for key, value in overlay.items():
            if key in result:
                result[key] = merge_overlay(result[key], value)
        return result
    if isinstance(source, list) and isinstance(overlay, list):
        result = copy.deepcopy(source)
        for index, value in enumerate(overlay[: len(result)]):
            result[index] = merge_overlay(result[index], value)
        return result
    return copy.deepcopy(overlay)


def parse_dt(value: str | None) -> datetime:
    text = str(value or "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def disposition(brief: dict[str, Any]) -> str:
    evidence = str(brief.get("evidence_class") or "")
    score = int(brief.get("importance_effective_score") or brief.get("importance_score") or 0)
    confidence = str(brief.get("confidence") or "")
    if evidence == "D" or confidence in {"weak_signal", "speculation"}:
        return "SIGNAL"
    if score >= 8:
        return "LEAD"
    if score >= 6:
        return "STANDARD"
    return "BRIEF"


def story_object(brief: dict[str, Any], research: dict[str, Any] | None, media: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "story_id": f"STORY-{brief['id'][5:]}",
        "research_id": brief["id"],
        "headline": brief.get("title"),
        "dek": brief.get("summary"),
        "story_type": disposition(brief),
        "published_at": brief.get("recorded_at") or brief.get("event_at"),
        "modified_at": brief.get("last_verified_at") or brief.get("recorded_at") or brief.get("event_at"),
        "news_value": {
            "importance": brief.get("importance_effective_score") or brief.get("importance_score"),
            "evidence": brief.get("evidence_class"),
            "confidence": brief.get("confidence")
        },
        "what_changed": brief.get("summary"),
        "why_it_matters": brief.get("why_it_matters"),
        "claims": brief.get("claims") or [],
        "technical": brief.get("technical") or {},
        "limitations": brief.get("limitations") or [],
        "contradictory_evidence": brief.get("contradictory_evidence") or [],
        "evidence_gaps": brief.get("evidence_gaps") or [],
        "sources": brief.get("source_urls") or [],
        "public_research": research or {},
        "media": media or {}
    }


def safe(value: Any) -> str:
    return html.escape(str(value or ""))


def list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{safe(x)}</li>" for x in items if x) + "</ul>" if items else "<p>—</p>"


def source_links(urls: list[str]) -> str:
    rows = []
    for url in urls:
        if not str(url).startswith(("http://", "https://")):
            continue
        rows.append(f'<li><a href="{safe(url)}" rel="noopener noreferrer">{safe(url)}</a></li>')
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p>—</p>"


def article_html(locale: str, brief: dict[str, Any], story: dict[str, Any], all_links: dict[str, str]) -> str:
    label = LABELS[locale]
    media = story.get("media") or {}
    image = media.get("image_url")
    if isinstance(image, str) and image.startswith("/"):
        image = BASE + image.removeprefix("/FCMO-AI-Newsletter")
    elif isinstance(image, str) and not image.startswith("http"):
        image = f"{BASE}/{image.lstrip('/')}"
    claims = []
    claim_map = CLAIM_LABELS.get(locale, {})
    for claim in brief.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        c = claim_map.get(str(claim.get("label")), str(claim.get("label") or ""))
        claims.append(f"<li><strong>{safe(c)}</strong> — {safe(claim.get('text'))}</li>")
    technical = brief.get("technical") or {}
    caveats = list(brief.get("limitations") or []) + list(brief.get("contradictory_evidence") or [])
    gaps = [str(x.get("description") or "") for x in brief.get("evidence_gaps") or [] if isinstance(x, dict)]
    research = story.get("public_research") or {}
    context_urls = [str(x.get("url") or "") for x in research.get("related_public_sources") or [] if isinstance(x, dict) and x.get("url")]
    url = all_links[locale]
    ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": brief.get("title"), "description": brief.get("summary"),
        "datePublished": story.get("published_at"), "dateModified": story.get("modified_at"),
        "inLanguage": locale, "mainEntityOfPage": url,
        "author": {"@type": "Organization", "name": "FCMO AI Research Desk"},
        "publisher": {"@type": "Organization", "name": "FCMO AI Newsletter", "url": BASE + "/"}
    }
    if image:
        ld["image"] = [image]
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{LOCALES[key]["hreflang"]}" href="{safe(href)}">'
        for key, href in all_links.items()
    ) + f'\n<link rel="alternate" hreflang="x-default" href="{safe(all_links["en"])}">'
    return f"""<!doctype html>
<html lang="{safe(locale)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe(brief.get("title"))} · FCMO AI Newsletter</title>
<meta name="description" content="{safe(brief.get("summary"))}">
<link rel="canonical" href="{safe(url)}">
{alternates}
<link rel="stylesheet" href="{BASE}/assets/newsroom.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body>
<header class="wire-head"><a href="{BASE}/">{safe(label["back"])}</a><span>FCMO WIRE</span></header>
<main class="story">
<div class="kicker">{safe(story["story_type"])} · {safe(brief.get("primary_desk", "research")).replace("_", " ")}</div>
<h1>{safe(brief.get("title"))}</h1>
<p class="dek">{safe(brief.get("summary"))}</p>
<p class="byline">FCMO AI Research Desk · {safe(story.get("modified_at"))}</p>
<p class="method">{safe(label["method"])}</p>
{f'<figure><img src="{safe(image)}" alt="{safe(brief.get("title"))}"><figcaption>{safe(media.get("credit"))} · {safe(media.get("license"))}</figcaption></figure>' if image else ''}
<section><h2>{safe(label["what_changed"])}</h2><p>{safe(brief.get("summary"))}</p></section>
<section><h2>{safe(label["evidence"])}</h2><ul>{''.join(claims)}</ul></section>
<section><h2>{safe(label["baseline"])}</h2><p>{safe(technical.get("strongest_baseline"))}</p></section>
<section><h2>{safe(label["caveat"])}</h2>{list_html([str(x) for x in caveats])}</section>
<section><h2>{safe(label["unknown"])}</h2>{list_html(gaps)}</section>
<section><h2>{safe(label["lens"])}</h2><p>{safe(brief.get("why_it_matters"))}</p></section>
<section><h2>{safe(label["sources"])}</h2>{source_links([str(x) for x in brief.get("source_urls") or []])}</section>
<section><h2>{safe(label["context"])}</h2>{source_links(context_urls)}</section>
</main>
</body>
</html>"""


def index_html(locale: str, stories: list[tuple[dict[str, Any], str]]) -> str:
    label = LABELS[locale]
    cards = "".join(
        f'<article><div class="kicker">{safe(story["story_type"])}</div><h2><a href="{safe(href)}">{safe(story["headline"])}</a></h2><p>{safe(story["dek"])}</p><small>{safe(story["modified_at"])}</small></article>'
        for story, href in stories
    )
    return f'<!doctype html><html lang="{safe(locale)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FCMO WIRE · {safe(label["latest"])}</title><link rel="stylesheet" href="{BASE}/assets/newsroom.css"></head><body><header class="wire-head"><a href="{BASE}/">FCMO AI Newsletter</a><span>FCMO WIRE</span></header><main class="story"><h1>{safe(label["latest"])}</h1><p class="method">{safe(label["method"])}</p><div class="cards">{cards}</div></main></body></html>'


def write_css(site: Path) -> None:
    css = """*{box-sizing:border-box}body{margin:0;background:#0b0b0c;color:#f5f5f3;font-family:Inter,Arial,sans-serif}.wire-head{display:flex;justify-content:space-between;padding:22px 5vw;border-bottom:1px solid #333;letter-spacing:.12em}.wire-head a{color:#fff;text-decoration:none}.wire-head span,.kicker{color:#fd5204}.story{max-width:980px;margin:0 auto;padding:64px 28px 100px}.story h1{font-size:clamp(2.7rem,7vw,5.9rem);line-height:.94;margin:.3em 0}.story h2{font-size:1.5rem;margin-top:2.7em}.dek{font-size:1.35rem;line-height:1.55;color:#d1d1d4}.byline,.method,small{color:#9e9ea3}.method{border-left:3px solid #fd5204;padding-left:16px}.story p,.story li{line-height:1.65}.story a{color:#ff7b42}.story figure{margin:42px 0}.story img{width:100%;max-height:560px;object-fit:cover;background:#151517}.story figcaption{font-size:.85rem;color:#9e9ea3;margin-top:8px}.cards article{padding:28px 0;border-top:1px solid #333}.cards h2{margin:.35em 0;font-size:2rem}.cards h2 a{color:#fff;text-decoration:none}@media(max-width:700px){.story{padding-top:42px}.wire-head{font-size:.75rem}.cards h2{font-size:1.5rem}}"""
    (site / "assets").mkdir(parents=True, exist_ok=True)
    (site / "assets" / "newsroom.css").write_text(css + "\n", encoding="utf-8")


def inject_wire_link(release_src: Path) -> None:
    path = release_src / "index.html"
    text = path.read_text(encoding="utf-8")
    if "data-fcmo-wire-link" in text:
        return
    link = '<a data-fcmo-wire-link href="news/" style="text-decoration:none">FCMO WIRE</a>'
    if "</nav>" in text:
        text = text.replace("</nav>", link + "</nav>", 1)
    else:
        text = text.replace("</body>", f'<div style="position:fixed;right:18px;bottom:18px">{link}</div></body>', 1)
    path.write_text(text, encoding="utf-8")


def parse_dt(value: str | None) -> datetime:
    text = str(value or "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def news_sitemap(site: Path, pages: list[dict[str, Any]]) -> None:
    register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
    register_namespace("news", "http://www.google.com/schemas/sitemap-news/0.9")
    root = Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    for page in pages:
        if parse_dt(page["published_at"]) < cutoff and parse_dt(page["modified_at"]) < cutoff:
            continue
        node = SubElement(root, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        SubElement(node, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = page["url"]
        news = SubElement(node, "{http://www.google.com/schemas/sitemap-news/0.9}news")
        pub = SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}publication")
        SubElement(pub, "{http://www.google.com/schemas/sitemap-news/0.9}name").text = "FCMO AI Newsletter"
        SubElement(pub, "{http://www.google.com/schemas/sitemap-news/0.9}language").text = page["language"]
        SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}publication_date").text = page["published_at"]
        SubElement(news, "{http://www.google.com/schemas/sitemap-news/0.9}title").text = page["headline"]
    ElementTree(root).write(site / "news-sitemap.xml", encoding="utf-8", xml_declaration=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-src", type=Path, default=Path("release-src"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args(argv)

    briefs = load_briefs(args.release_src)
    media_rows = read_json(args.release_src / "data" / "media.json")
    media = {row.get("id"): row for row in media_rows if isinstance(row, dict)}
    research_dir = args.release_src / "data" / "public-research"
    research = {path.stem: read_json(path) for path in research_dir.glob("FCMO-*.json")} if research_dir.exists() else {}
    overlays = {locale: load_locale_records(args.site / "data" / "i18n", locale) for locale in LOCALES}

    stories = {rid: story_object(brief, research.get(rid), media.get(rid)) for rid, brief in briefs.items()}
    ordered_ids = sorted(
        stories,
        key=lambda rid: (parse_dt(stories[rid]["modified_at"]), int(stories[rid]["news_value"]["importance"] or 0), rid),
        reverse=True,
    )
    (args.site / "data").mkdir(parents=True, exist_ok=True)
    (args.site / "data" / "stories.json").write_text(
        json.dumps([stories[rid] for rid in ordered_ids], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_css(args.site)
    inject_wire_link(args.release_src)

    pages: list[dict[str, Any]] = []
    for locale, meta in LOCALES.items():
        folder = args.site / "news" / meta["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        localized_cards = []
        for rid in ordered_ids:
            brief = merge_overlay(briefs[rid], overlays[locale].get(rid, {}))
            story = copy.deepcopy(stories[rid])
            story["headline"] = brief.get("title")
            story["dek"] = brief.get("summary")
            links = {key: f"{BASE}/news/{value['slug']}/{rid}.html" for key, value in LOCALES.items()}
            url = links[locale]
            (folder / f"{rid}.html").write_text(article_html(locale, brief, story, links), encoding="utf-8")
            localized_cards.append((story, url))
            pages.append({
                "url": url, "language": meta["hreflang"], "headline": str(brief.get("title") or ""),
                "published_at": str(story.get("published_at") or ""), "modified_at": str(story.get("modified_at") or "")
            })
        (folder / "index.html").write_text(index_html(locale, localized_cards), encoding="utf-8")

    (args.site / "news").mkdir(exist_ok=True)
    (args.site / "news" / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=en/"><script>location.replace("en/"+location.search+location.hash)</script>',
        encoding="utf-8",
    )
    news_sitemap(args.site, pages)
    print(f"newsroom surfaces OK; stories={len(stories)}; localized_pages={len(pages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
