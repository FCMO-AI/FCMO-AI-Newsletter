"""RSS 2.0, Atom, JSON Feed and iCalendar generation."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import json
from pathlib import Path

from .i18n import dek, headline
from .routes import absolute, story_path


def _stories(stories: list[dict], beat: str | None = None) -> list[dict]:
    values = [s for s in stories if s.get("status") == "live" and (beat is None or s.get("beat") == beat)]
    return sorted(values, key=lambda s: (s.get("event_at", ""), s["id"]), reverse=True)


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def rss(stories: list[dict], *, locale: dict, catalog: dict, base_url: str, self_url: str, beat: str | None = None) -> str:
    code = locale["code"]
    title = catalog["strings"]["site"]["name"] + (f" · {catalog['labels']['beat'][beat]}" if beat else "")
    items = []
    values = _stories(stories, beat)
    for story in values:
        url = absolute(base_url, story_path(locale, story))
        items.append(f'''<item><title>{escape(headline(story, code, catalog))}</title><link>{escape(url)}</link><guid isPermaLink="true">{escape(url)}</guid><pubDate>{format_datetime(_date(story["first_published_at"]), usegmt=True)}</pubDate><description>{escape(dek(story, code, catalog))}</description></item>''')
    build = format_datetime(max((_date(s["updated_at"]) for s in values), default=datetime.now(timezone.utc)), usegmt=True)
    return f'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{escape(title)}</title><link>{escape(absolute(base_url, locale["path_prefix"]))}</link><description>{escape(catalog["strings"]["site"]["description"])}</description><language>{escape(locale["html_lang"])}</language><lastBuildDate>{build}</lastBuildDate><atom:link href="{escape(self_url)}" rel="self" type="application/rss+xml"/>{''.join(items)}</channel></rss>'''


def atom(stories: list[dict], *, locale: dict, catalog: dict, base_url: str, self_url: str, beat: str | None = None) -> str:
    code = locale["code"]
    values = _stories(stories, beat)
    title = catalog["strings"]["site"]["name"] + (f" · {catalog['labels']['beat'][beat]}" if beat else "")
    updated = max((s["updated_at"] for s in values), default=datetime.now(timezone.utc).isoformat())
    entries = []
    for story in values:
        url = absolute(base_url, story_path(locale, story))
        entries.append(f'''<entry><title>{escape(headline(story, code, catalog))}</title><id>{escape(url)}</id><link href="{escape(url)}"/><published>{escape(story["first_published_at"])}</published><updated>{escape(story["updated_at"])}</updated><summary>{escape(dek(story, code, catalog))}</summary></entry>''')
    return f'''<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{escape(locale["html_lang"])}"><title>{escape(title)}</title><id>{escape(self_url)}</id><link href="{escape(self_url)}" rel="self"/><link href="{escape(absolute(base_url, locale["path_prefix"]))}"/><updated>{escape(updated)}</updated>{''.join(entries)}</feed>'''


def json_feed(stories: list[dict], *, locale: dict, catalog: dict, base_url: str, feed_url: str, beat: str | None = None) -> str:
    code = locale["code"]
    values = _stories(stories, beat)
    def primary_source(story: dict) -> str:
        sources = [source for source in story.get("sources") or [] if isinstance(source, dict)
                   and isinstance(source.get("url"), str) and source["url"].startswith(("https://", "http://"))]
        sources.sort(key=lambda source: (not bool(source.get("primary")), str(source.get("url"))))
        return str(sources[0]["url"]) if sources else ""
    value = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": catalog["strings"]["site"]["name"] + (f" · {catalog['labels']['beat'][beat]}" if beat else ""),
        "home_page_url": absolute(base_url, locale["path_prefix"]),
        "feed_url": feed_url,
        "language": locale["html_lang"],
        "items": [{
            "id": absolute(base_url, story_path(locale, story)),
            "url": absolute(base_url, story_path(locale, story)),
            "external_url": primary_source(story),
            "title": headline(story, code, catalog), "summary": dek(story, code, catalog),
            "date_published": story["first_published_at"], "date_modified": story["updated_at"],
        } for story in values],
    }
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def write_all(stories: list[dict], *, locales: list[dict], catalogs: dict[str, dict], base_url: str, out: Path) -> list[str]:
    paths = []
    beats = (None, "technology", "business", "policy", "society", "research")
    for locale in locales:
        root = out / locale["path_prefix"]
        for beat in beats:
            stem = "feed" if beat is None else f"feeds/{beat}"
            for extension, renderer in (("xml", rss), ("atom", atom), ("json", json_feed)):
                rel = locale["path_prefix"] + stem + "." + extension
                path = out / rel
                url = absolute(base_url, rel)
                kwargs = {"locale": locale, "catalog": catalogs[locale["code"]], "base_url": base_url, "beat": beat}
                text = renderer(stories, **kwargs, **({"feed_url": url} if extension == "json" else {"self_url": url}))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                paths.append(rel)
        events = [s for s in stories if s.get("kind") == "event" and s.get("status") == "live"]
        calendar = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FCMO AI//Agenda//EN"]
        for story in events:
            start = story.get("scheduled_at") or story.get("event_at")
            calendar.extend(("BEGIN:VEVENT", f"UID:{story['id']}@fcmo.ai", f"DTSTART:{start.replace('-', '').replace(':', '').replace('Z', 'Z')}", f"SUMMARY:{headline(story, locale['code'], catalogs[locale['code']])}", "END:VEVENT"))
        calendar.append("END:VCALENDAR")
        calendar_path = root / "agenda.ics"
        calendar_path.parent.mkdir(parents=True, exist_ok=True)
        calendar_path.write_text("\r\n".join(calendar) + "\r\n", encoding="utf-8")
        paths.append(locale["path_prefix"] + "agenda.ics")
    return paths
