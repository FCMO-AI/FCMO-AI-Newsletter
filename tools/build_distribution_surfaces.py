#!/usr/bin/env python3
"""Build search/news distribution surfaces from the autonomous Story wire.

The existing SPA remains the reading runtime. This tool adds independently addressable
language URLs, hreflang/canonical metadata, NewsArticle JSON-LD and deterministic
sitemaps so browsers, crawlers and agents do not have to infer publication structure
from a hash route.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
from urllib.parse import quote

BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/"
LANGS = {"en": "en", "es-419": "es", "zh-Hans": "zh-hans"}
HREFLANG = {"en": "en", "es-419": "es", "zh-Hans": "zh-Hans"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def absolute(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return BASE + url.lstrip("/")


def locale_records(i18n: Path, locale: str) -> dict[str, dict]:
    if locale == "en":
        return {}
    result: dict[str, dict] = {}
    for path in sorted((i18n / locale).glob("part-*.json")):
        result.update((load_json(path).get("records") or {}))
    return result


def story_url(locale: str, identifier: str) -> str:
    segment = LANGS[locale]
    return f"{BASE}{segment}/developments/{identifier}.html"


def json_ld(story: dict, media: dict | None) -> dict:
    identifier = story["research_ids"][0]
    image = absolute((media or {}).get("image_url"))
    value = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": story["headline"],
        "description": story["dek"],
        "datePublished": story.get("published_at"),
        "dateModified": story.get("modified_at") or story.get("published_at"),
        "mainEntityOfPage": {"@type": "WebPage", "@id": story_url("en", identifier)},
        "author": {"@type": "Organization", "name": "FCMO AI Research Desk", "url": BASE + "about.html"},
        "publisher": {"@type": "Organization", "name": "FCMO AI Newsletter", "url": BASE},
        "isAccessibleForFree": True,
        "inLanguage": "en",
        "citation": story.get("sources") or [],
    }
    if image:
        value["image"] = [image]
    return {key: item for key, item in value.items() if item not in (None, "", [])}


def shell(identifier: str, locale: str, title: str, description: str, ld: dict) -> str:
    target = f"../../index.html?lang={quote(locale)}#/brief/{identifier}"
    canonical = story_url(locale, identifier)
    alternates = "".join(
        f'<link rel="alternate" hreflang="{HREFLANG[source]}" href="{story_url(source, identifier)}">'
        for source in LANGS
    ) + f'<link rel="alternate" hreflang="x-default" href="{story_url("en", identifier)}">'
    return (
        "<!doctype html><html lang=\"" + html.escape(HREFLANG[locale]) + "\"><head>"
        "<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{html.escape(title)} · FCMO AI Newsletter</title>"
        f"<meta name=\"description\" content=\"{html.escape(description, quote=True)}\">"
        f"<link rel=\"canonical\" href=\"{canonical}\">{alternates}"
        f"<meta property=\"og:type\" content=\"article\"><meta property=\"og:title\" content=\"{html.escape(title, quote=True)}\">"
        f"<meta property=\"og:description\" content=\"{html.escape(description, quote=True)}\">"
        f"<meta property=\"og:url\" content=\"{canonical}\">"
        f"<script type=\"application/ld+json\">{html.escape(json.dumps(ld, ensure_ascii=False), quote=False)}</script>"
        f"<meta http-equiv=\"refresh\" content=\"0;url={html.escape(target, quote=True)}\">"
        "</head><body><main><p>Opening the FCMO AI Newsletter dossier… "
        f"<a href=\"{html.escape(target, quote=True)}\">Continue</a>.</p></main></body></html>"
    )


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def sitemap(urls: list[tuple[str, str | None]]) -> str:
    rows = []
    for loc, modified in urls:
        lastmod = f"<lastmod>{html.escape(modified[:10])}</lastmod>" if modified else ""
        rows.append(f"<url><loc>{html.escape(loc)}</loc>{lastmod}</url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(rows) + "</urlset>\n"


def news_sitemap(stories: list[dict], reference: dt.datetime) -> str:
    rows = []
    for story in stories:
        if story.get("disposition") not in {"LEAD", "STANDARD", "BRIEF", "SIGNAL"}:
            continue
        when = parse_time(story.get("published_at")) or parse_time(story.get("modified_at"))
        if not when or (reference - when).total_seconds() > 2 * 24 * 3600:
            continue
        identifier = story["research_ids"][0]
        rows.append(
            "<url>"
            f"<loc>{html.escape(story_url('en', identifier))}</loc>"
            "<news:news><news:publication><news:name>FCMO AI Newsletter</news:name><news:language>en</news:language></news:publication>"
            f"<news:publication_date>{html.escape(when.isoformat().replace('+00:00','Z'))}</news:publication_date>"
            f"<news:title>{html.escape(story['headline'])}</news:title></news:news></url>"
        )
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">' + "".join(rows) + "</urlset>\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    args = parser.parse_args()
    stories = load_json(args.site / "data" / "stories.json")
    media = {item["id"]: item for item in load_json(args.site / "data" / "media.json")}
    status_path = args.site / "data" / "newsroom-status.json"
    status = load_json(status_path) if status_path.is_file() else {}
    localizations = {locale: locale_records(args.i18n_dir, locale) for locale in LANGS if locale != "en"}
    all_urls: list[tuple[str, str | None]] = [(BASE, None)]
    articles: dict[str, dict] = {}
    for story in stories:
        identifier = story["research_ids"][0]
        ld = json_ld(story, media.get(identifier))
        articles[identifier] = ld
        for locale in LANGS:
            if locale == "en":
                title, description = story["headline"], story["dek"]
            else:
                overlay = localizations[locale].get(identifier) or {}
                title = overlay.get("title") or story["headline"]
                description = overlay.get("summary") or story["dek"]
            route = args.site / LANGS[locale] / "developments" / f"{identifier}.html"
            route.parent.mkdir(parents=True, exist_ok=True)
            route.write_text(shell(identifier, locale, title, description, ld), encoding="utf-8")
            all_urls.append((story_url(locale, identifier), story.get("modified_at")))
    (args.site / "data" / "news-articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.site / "sitemap.xml").write_text(sitemap(all_urls), encoding="utf-8")
    reference = parse_time(status.get("delivered_at")) or parse_time(status.get("public_evidence_cutoff"))
    if reference is None:
        candidates = [parse_time(story.get("modified_at")) for story in stories]
        reference = max([item for item in candidates if item is not None], default=dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc))
    (args.site / "news-sitemap.xml").write_text(news_sitemap(stories, reference), encoding="utf-8")
    print(json.dumps({"localized_story_routes": len(stories) * len(LANGS), "news_articles": len(articles)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
