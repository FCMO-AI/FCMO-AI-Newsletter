"""Namespace-correct standard and Google News sitemaps."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path


def write(routes: list[dict], *, out: Path, generated_at: str) -> None:
    chunks = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for route in routes:
        if not route.get("index", True):
            continue
        links = "".join(f'<xhtml:link rel="alternate" hreflang="{escape(code)}" href="{escape(url)}"/>' for code, url in route.get("alternates", []))
        chunks.append(f'<url><loc>{escape(route["url"])}</loc><lastmod>{escape(route["lastmod"][:10])}</lastmod>{links}</url>')
    chunks.append("</urlset>")
    (out / "sitemap.xml").write_text("".join(chunks), encoding="utf-8")

    now = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    cutoff = now - timedelta(hours=48)
    news = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    for route in routes:
        if route.get("kind") != "story" or route.get("locale") != "en":
            continue
        published = datetime.fromisoformat(route["published"].replace("Z", "+00:00"))
        if published >= cutoff:
            news.append(f'<url><loc>{escape(route["url"])}</loc><news:news><news:publication><news:name>FCMO AI</news:name><news:language>en</news:language></news:publication><news:publication_date>{escape(route["published"])}</news:publication_date><news:title>{escape(route["title"])}</news:title></news:news></url>')
    news.append("</urlset>")
    (out / "news-sitemap.xml").write_text("".join(news), encoding="utf-8")
