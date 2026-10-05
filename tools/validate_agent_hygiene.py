#!/usr/bin/env python3
"""Validate machine-surface freshness, feed attribution and localized Story JSON-LD."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

LOCALE_CODES = ("en", "es-419", "zh-Hans")
HEADER = re.compile(r"^<!-- generated_at: ([^;]+); stale_after: ([^ ]+) -->$")
BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"


class JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_jsonld = False
        self.parts: list[str] = []
        self.documents: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.in_jsonld = True
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.in_jsonld:
            try:
                value = json.loads("".join(self.parts))
                if isinstance(value, dict):
                    self.documents.append(value)
            except json.JSONDecodeError:
                self.documents.append({"_invalid_json": True})
            self.in_jsonld = False


def _date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _load_jsonld(path: Path) -> list[dict]:
    parser = JsonLdParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.documents


def _validate_citation(root: Path, citation_url: str, story_id: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    parsed_url = urlparse(citation_url)
    prefix = "/FCMO-AI-Newsletter/"
    if not citation_url.startswith(BASE + "/data/citations/") or not re.fullmatch(r"[0-9a-f]{64}\.json", parsed_url.path.rsplit("/", 1)[-1]):
        return [f"{story_id}: citation is not a versioned local permalink"], []
    relative = parsed_url.path.split(prefix, 1)[-1]
    path = root / relative
    if not path.is_file():
        return [f"{story_id}: citation permalink target is missing: {relative}"], []
    try:
        citation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [f"{story_id}: citation permalink is not valid JSON"], []
    version = citation.pop("version", None)
    expected = hashlib.sha256(json.dumps(citation, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if version != expected or path.stem != expected:
        errors.append(f"{story_id}: citation content hash does not match permalink version")
    if citation.get("schema") != "fcmo-versioned-citation-v1" or citation.get("id") != story_id:
        errors.append(f"{story_id}: citation schema or story identity is invalid")
    sources = citation.get("source_urls")
    if not isinstance(sources, list) or not sources or any(not isinstance(x, str) or not x.startswith(("https://", "http://")) for x in sources):
        errors.append(f"{story_id}: versioned citation has no valid source URLs")
        return errors, []
    return errors, sources


def validate(root: Path, expected_generated_at: str | None = None) -> list[str]:
    errors: list[str] = []
    headers: list[tuple[datetime, datetime]] = []
    llms_paths = sorted(path for path in root.rglob("llms*.txt") if path.is_file())
    for required in (root / "llms.txt", root / "llms-full.txt"):
        if required not in llms_paths:
            errors.append(f"missing {required.relative_to(root)}")
    for path in llms_paths:
        filename = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        first = text.splitlines()[0] if text.splitlines() else ""
        match = HEADER.fullmatch(first)
        if not match:
            errors.append(f"{filename}: missing freshness header with generated_at and stale_after")
            continue
        try:
            generated, stale = _date(match.group(1)), _date(match.group(2))
            if stale <= generated or stale - generated != timedelta(hours=48):
                errors.append(f"{filename}: stale_after must be 48 hours after generated_at")
            headers.append((generated, stale))
            if expected_generated_at and generated != _date(expected_generated_at):
                errors.append(f"{filename}: generated_at does not match the requested build time")
        except ValueError as exc:
            errors.append(f"{filename}: invalid freshness timestamp ({exc})")
        if "## Reading hierarchy (R0–R4)" not in text:
            errors.append(f"{filename}: missing agent-readable R0–R4 hierarchy")
    if len(headers) == 2 and headers[0] != headers[1]:
        errors.append("llms.txt and llms-full.txt freshness headers differ")

    feed_path = root / "feed.json"
    feed_items: dict[str, dict] = {}
    if not feed_path.is_file():
        errors.append("missing feed.json")
    else:
        try:
            feed = json.loads(feed_path.read_text(encoding="utf-8"))
            if feed.get("version") != "https://jsonfeed.org/version/1.1" or not isinstance(feed.get("items"), list):
                errors.append("feed.json: invalid JSON Feed 1.1 envelope")
            else:
                feed_items = {str(row.get("id")): row for row in feed["items"] if isinstance(row, dict)}
        except (OSError, json.JSONDecodeError):
            errors.append("feed.json: invalid JSON")

    validated_pages = 0
    page_sources: dict[str, list[str]] = {}
    page_urls: dict[str, str] = {}
    story_locales: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.html")):
        documents = _load_jsonld(path)
        if any(doc.get("_invalid_json") for doc in documents):
            errors.append(f"{path.relative_to(root)}: malformed JSON-LD script")
        articles = [doc for doc in documents if doc.get("@type") == "NewsArticle"]
        for article in articles:
            rid = str(article.get("identifier") or "")
            locale = str(article.get("inLanguage") or "")
            if not re.fullmatch(r"FCMO-[0-9A-F]{12}", rid):
                errors.append(f"{path.relative_to(root)}: NewsArticle lacks a public FCMO story identifier")
                continue
            if locale not in LOCALE_CODES:
                errors.append(f"{path.relative_to(root)}: NewsArticle has unsupported inLanguage {locale!r}")
                continue
            if not all(article.get(key) for key in ("headline", "description", "datePublished", "dateModified", "mainEntityOfPage", "author", "publisher")):
                errors.append(f"{locale}/{rid}: NewsArticle is missing required fields")
            story_locales.setdefault(rid, set()).add(locale)
            sources = article.get("isBasedOn")
            if not isinstance(sources, list) or not sources or any(not isinstance(url, str) or not url.startswith(("https://", "http://")) for url in sources):
                errors.append(f"{locale}/{rid}: isBasedOn must list valid original-source URLs")
                sources = []
            citation_url = article.get("citation")
            if not isinstance(citation_url, str):
                errors.append(f"{locale}/{rid}: missing versioned citation permalink")
            else:
                citation_errors, citation_sources = _validate_citation(root, citation_url, rid)
                errors.extend(citation_errors)
                if citation_sources != sources:
                    errors.append(f"{locale}/{rid}: JSON-LD sources diverge from versioned citation")
            page_sources[rid] = sources
            page_urls[rid] = str(article.get("mainEntityOfPage") or "")
            validated_pages += 1
    covered_stories = {rid for rid, locales in story_locales.items() if set(LOCALE_CODES).issubset(locales)}
    if validated_pages < 9 or len(covered_stories) < 3:
        errors.append(f"JSON-LD coverage: expected at least 3 stories × 3 locales; found {len(covered_stories)} complete stories and {validated_pages} pages")
    for rid, sources in page_sources.items():
        item = next((row for row in feed_items.values() if row.get("external_url") == (sources[0] if sources else None)), None)
        if item is None:
            item = next((row for row in feed_items.values() if row.get("url") == page_urls.get(rid)), None)
            if item is not None:
                errors.append(f"{rid}: feed external_url must point to the primary source")
            else:
                errors.append(f"{rid}: missing from JSON Feed")
        elif not sources or item.get("external_url") != sources[0]:
            errors.append(f"{rid}: feed external_url must point to the primary source")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--expected-generated-at")
    args = parser.parse_args(argv)
    errors = validate(args.site, args.expected_generated_at)
    if errors:
        for error in errors:
            print(f"AGENT_HYGIENE FAIL {error}")
        return 1
    print("AGENT_HYGIENE OK; freshness, source feed and 3×3 NewsArticle citations validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
