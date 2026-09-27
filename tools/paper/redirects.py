"""Static legacy redirect stubs and complete previous-path preservation."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

from .routes import href, story_path

ID_RE = re.compile(r"FCMO-[A-F0-9]{12}")


def stub(target: str) -> str:
    safe = escape(target, quote=True)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={safe}"><link rel="canonical" href="{safe}"><title>Moved · FCMO AI</title></head><body><p>This page moved to <a href="{safe}">{safe}</a>.</p></body></html>'''


def _write(out: Path, rel: str, target: str) -> None:
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub(target), encoding="utf-8")


def build(stories: list[dict], *, locales: list[dict], base: str, out: Path, legacy_root: Path | None = None) -> list[str]:
    by_id = {story["id"]: story for story in stories}
    locale_by_legacy = {"en": locales[0], "es": next(x for x in locales if x["code"] == "es-419"), "zh-hans": next(x for x in locales if x["code"] == "zh-Hans")}
    written = []
    for story in stories:
        english_target = href(base, story_path(locales[0], story))
        for rel in (f"developments/{story['id']}.html", f"legacy-story/{story['id']}.html"):
            _write(out, rel, english_target); written.append(rel)
        for legacy, locale in locale_by_legacy.items():
            rel = f"news/{legacy}/{story['id']}.html"
            _write(out, rel, href(base, story_path(locale, story))); written.append(rel)
    dates = sorted({story["url_date"] for story in stories})
    for date in dates:
        rel = f"editions/{date}.html"
        _write(out, rel, href(base, f"edition/{date}/")); written.append(rel)
    # Preserve every prior HTML path when its destination can be resolved without guessing.
    if legacy_root and legacy_root.is_dir():
        for source in sorted(legacy_root.rglob("*.html")):
            rel = source.relative_to(legacy_root).as_posix()
            if rel in written or rel == "index.html":
                continue
            match = ID_RE.search(source.name)
            if match and match.group() in by_id:
                target = href(base, story_path(locales[0], by_id[match.group()]))
            elif rel.startswith("editions/"):
                target = href(base, "archive/")
            elif rel.startswith(("topics/", "organizations/")):
                target = href(base, "archive/")
            else:
                continue
            _write(out, rel, target); written.append(rel)
    return written
