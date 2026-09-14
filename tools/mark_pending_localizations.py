#!/usr/bin/env python3
"""Replace accidental English fallbacks with explicit pending-translation pages.

The newsroom builder intentionally starts from canonical English and merges native
locale overlays. When a fresh Story has no overlay yet, that default would otherwise
make English prose appear under an ES/ZH route. This post-build pass makes the backlog
truthful: the native route remains stable, but it displays a localized status notice
and links to the canonical English article instead of pretending to be translated.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from validate_localizations import load_locale

BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
LOCALES = {
    "es-419": {
        "slug": "es",
        "lang": "es-419",
        "title": "Traducción pendiente",
        "notice": "Esta historia ya está publicada en la edición canónica en inglés, pero su edición nativa en español latinoamericano todavía está pendiente. No mostramos texto en inglés como si fuera una traducción.",
        "cta": "Leer la edición canónica en inglés",
        "latest": "Últimas",
        "pending": "TRADUCCIÓN PENDIENTE",
        "english_headline": "Titular original en inglés",
    },
    "zh-Hans": {
        "slug": "zh-hans",
        "lang": "zh-Hans",
        "title": "翻译待完成",
        "notice": "这篇报道已经在权威英文版发布，但简体中文原生版本仍在准备中。我们不会把英文内容伪装成中文翻译。",
        "cta": "阅读权威英文版",
        "latest": "最新",
        "pending": "翻译待完成",
        "english_headline": "英文原始标题",
    },
}


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def pending_page(locale: str, story: dict[str, Any]) -> str:
    meta = LOCALES[locale]
    rid = str(story["research_id"])
    english = f"{BASE}/news/en/{rid}.html"
    self_url = f"{BASE}/news/{meta['slug']}/{rid}.html"
    headline = str(story.get("headline") or rid)
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": headline,
        "description": meta["notice"],
        "datePublished": story.get("published_at"),
        "dateModified": story.get("modified_at"),
        # This route is a localized status shell around the canonical English Story.
        # Do not falsely claim the article body is translated.
        "inLanguage": "en",
        "mainEntityOfPage": self_url,
        "author": {"@type": "Organization", "name": "FCMO AI Research Desk"},
        "publisher": {"@type": "Organization", "name": "FCMO AI Newsletter", "url": BASE + "/"},
    }
    return f'''<!doctype html>
<html lang="{esc(meta['lang'])}" data-translation-status="pending">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['title'])} · FCMO AI Newsletter</title>
<meta name="description" content="{esc(meta['notice'])}">
<link rel="canonical" href="{esc(self_url)}">
<link rel="alternate" hreflang="en" href="{esc(english)}">
<link rel="alternate" hreflang="{esc(meta['lang'])}" href="{esc(self_url)}">
<link rel="alternate" hreflang="x-default" href="{esc(english)}">
<link rel="stylesheet" href="../../assets/newsroom.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body>
<header class="wire-head"><a href="{BASE}/">FCMO AI Newsletter</a><span>FCMO WIRE</span></header>
<main class="story">
<div class="kicker">{esc(meta['pending'])}</div>
<h1>{esc(meta['title'])}</h1>
<p class="dek">{esc(meta['notice'])}</p>
<p class="byline">FCMO AI Research Desk · {esc(story.get('modified_at'))}</p>
<section>
<h2>{esc(meta['english_headline'])}</h2>
<p>{esc(headline)}</p>
<p><a href="{esc(english)}">{esc(meta['cta'])}</a></p>
</section>
</main>
</body>
</html>'''


def index_page(locale: str, stories: list[dict[str, Any]], localized: dict[str, dict[str, Any]]) -> str:
    meta = LOCALES[locale]
    cards: list[str] = []
    for story in stories:
        rid = str(story.get("research_id") or "")
        overlay = localized.get(rid)
        href = f"{BASE}/news/{meta['slug']}/{rid}.html"
        if overlay:
            headline = str(overlay.get("title") or story.get("headline") or rid)
            summary = str(overlay.get("summary") or story.get("dek") or "")
            kicker = str(story.get("story_type") or "STORY")
        else:
            headline = str(story.get("headline") or rid)
            summary = meta["notice"]
            kicker = meta["pending"]
        cards.append(
            f'<article><div class="kicker">{esc(kicker)}</div>'
            f'<h2><a href="{esc(href)}">{esc(headline)}</a></h2>'
            f'<p>{esc(summary)}</p><small>{esc(story.get("modified_at"))}</small></article>'
        )
    return (
        f'<!doctype html><html lang="{esc(meta["lang"])}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>FCMO WIRE · {esc(meta["latest"])}</title>'
        f'<link rel="stylesheet" href="../../assets/newsroom.css"></head><body>'
        f'<header class="wire-head"><a href="{BASE}/">FCMO AI Newsletter</a><span>FCMO WIRE</span></header>'
        f'<main class="story"><h1>{esc(meta["latest"])}</h1><div class="cards">{"".join(cards)}</div></main></body></html>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args()
    site = args.site
    stories = json.loads((site / "data" / "stories.json").read_text(encoding="utf-8"))
    if not isinstance(stories, list):
        raise SystemExit("pending localization renderer: stories.json must be a list")

    total_pending = 0
    pending_sets: dict[str, set[str]] = {}
    for locale, meta in LOCALES.items():
        localized, _strict = load_locale(site / "data" / "i18n", locale)
        expected = {str(s.get("research_id") or "") for s in stories}
        pending = expected - set(localized)
        pending_sets[locale] = pending
        folder = site / "news" / meta["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        for story in stories:
            rid = str(story.get("research_id") or "")
            if rid in pending:
                (folder / f"{rid}.html").write_text(pending_page(locale, story), encoding="utf-8")
        (folder / "index.html").write_text(index_page(locale, stories, localized), encoding="utf-8")
        total_pending += len(pending)

    if pending_sets["es-419"] != pending_sets["zh-Hans"]:
        raise SystemExit("pending localization renderer: ES/ZH backlog differs")

    manifest = site / "data" / "i18n" / "translation-status.json"
    pending = sorted(pending_sets["es-419"])
    manifest.write_text(
        json.dumps(
            {
                "schema": "fcmo-translation-status-v1",
                "canonical_locale": "en",
                "required_native_locales": ["es-419", "zh-Hans"],
                "canonical_story_count": len(stories),
                "native_complete_story_count": len(stories) - len(pending),
                "pending_translation_count": len(pending),
                "pending_translation_ids": pending,
                "state": "COMPLETE" if not pending else "DEGRADED_TRANSLATION_BACKLOG",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"pending localization rendering OK; stories={len(stories)}; pending_per_locale={len(pending)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
