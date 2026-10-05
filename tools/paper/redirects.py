"""Static legacy redirect stubs and complete previous-path preservation."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

from .routes import TECHNICAL_FRONT, href, story_path

ID_RE = re.compile(r"FCMO-[A-F0-9]{12}")


def stub(target: str, base: str = "/") -> str:
    safe = escape(target, quote=True)
    favicon = escape(href(base, "assets/pwa/favicon.svg"), quote=True)
    apple_touch_icon = escape(href(base, "assets/pwa/icons/icon-192.svg"), quote=True)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={safe}"><link rel="icon" href="{favicon}" type="image/svg+xml"><link rel="apple-touch-icon" href="{apple_touch_icon}"><link rel="canonical" href="{safe}"><title>Moved · FCMO AI</title></head><body><p>This page moved to <a href="{safe}">{safe}</a>.</p></body></html>'''


def _write(out: Path, rel: str, target: str, base: str) -> None:
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub(target, base), encoding="utf-8")


def build(stories: list[dict], *, locales: list[dict], base: str, out: Path, legacy_root: Path | None = None, published_edition_dates: list[str] | None = None) -> list[str]:
    by_id = {story["id"]: story for story in stories}
    live = [story for story in stories if story.get("status") == "live"]
    locale_by_legacy = {"en": locales[0], "es": next(x for x in locales if x["code"] == "es-419"), "zh-hans": next(x for x in locales if x["code"] == "zh-Hans")}
    written = []
    # Preserve the previous technical front as an explicit legacy document.
    # Locale roots now serve the FCMO landing.
    for locale in locales:
        rel = locale["path_prefix"] + "front.html"
        _write(out, rel, href(base, locale["path_prefix"] + TECHNICAL_FRONT), base)
        written.append(rel)
    for story in stories:
        survivor = by_id.get(story.get("merged_into"))
        english_target = (
            href(base, story_path(locales[0], survivor)) if survivor and survivor.get("status") == "live"
            else href(base, story_path(locales[0], story)) if story.get("status") == "live"
            else href(base, "corrections/")
        )
        for rel in (f"developments/{story['id']}.html", f"legacy-story/{story['id']}.html"):
            _write(out, rel, english_target, base); written.append(rel)
        for legacy, locale in locale_by_legacy.items():
            rel = f"news/{legacy}/{story['id']}.html"
            target = (
                href(base, story_path(locale, survivor)) if survivor and survivor.get("status") == "live"
                else href(base, story_path(locale, story)) if story.get("status") == "live"
                else href(base, locale["path_prefix"] + "corrections/")
            )
            _write(out, rel, target, base); written.append(rel)
    live_dates = set(published_edition_dates or []) | {story["url_date"] for story in live}
    dates = sorted(set(published_edition_dates or []) | {story["url_date"] for story in stories})
    for date in dates:
        rel = f"editions/{date}.html"
        target = href(base, f"edition/{date}/") if date in live_dates else href(base, "archive/")
        _write(out, rel, target, base); written.append(rel)
    # Preserve every prior HTML path when its destination can be resolved without guessing.
    if legacy_root and legacy_root.is_dir():
        for source in sorted(legacy_root.rglob("*.html")):
            rel = source.relative_to(legacy_root).as_posix()
            if rel in written or rel == "index.html":
                continue
            match = ID_RE.search(source.name)
            if match and match.group() in by_id:
                story = by_id[match.group()]
                survivor = by_id.get(story.get("merged_into"))
                target = (
                    href(base, story_path(locales[0], survivor)) if survivor and survivor.get("status") == "live"
                    else href(base, story_path(locales[0], story)) if story.get("status") == "live"
                    else href(base, "corrections/")
                )
            elif rel.startswith("editions/"):
                target = href(base, "archive/")
            elif rel.startswith(("topics/", "organizations/")):
                target = href(base, "archive/")
            else:
                continue
            _write(out, rel, target, base); written.append(rel)
    return written
