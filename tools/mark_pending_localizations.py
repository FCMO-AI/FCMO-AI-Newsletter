#!/usr/bin/env python3
"""Render every incomplete native edition as an explicit, localized pending page.

The newsroom builder starts from canonical English and merges native overlays,
so without this pass an ES/ZH route whose translation is missing or partial
would show English prose under a non-English ``lang``. Here every (story,
locale) pair is judged field by field (``validate_localizations.pair_status``):

* complete pairs keep the page the builder wrote;
* ``PENDING`` pairs (no overlay, or one that lacks any prose field the English
  record has, such as a headline-only delta) get a localized page that shows
  the native fields that do exist, a "translation pending" notice and a link to
  the English original; the English headline appears only inside an element
  marked ``lang="en"`` and labelled as the original;
* ``FAILED`` pairs (the overlay was rejected: English left in place, numbers or
  ids changed) show no overlay text at all, only the notice.

It also writes ``data/i18n/translation-status.json`` with the real backlog per
locale. Reader copy (notice, labels, dates) comes from ``i18n/ui/<locale>.json``;
dates use explicit month tables (never the platform's ``Sept``) in
America/Mexico_City, and day- or month-precision dates are never shifted.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from tools.validate_localizations import (
        LOCALES as NATIVE_LOCALES,
        is_complete,
        load_corpus_canonical,
        load_locale_details,
        pair_status,
    )
except ImportError:  # direct script execution from tools/
    from validate_localizations import (  # type: ignore[no-redef]
        LOCALES as NATIVE_LOCALES,
        is_complete,
        load_corpus_canonical,
        load_locale_details,
        pair_status,
    )

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "i18n" / "ui"
DEFAULT_BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/"
# Legacy newsroom route folders (news/<slug>/<id>.html).
ROUTE_SLUG = {"en": "en", "es-419": "es", "zh-Hans": "zh-hans"}
# America/Mexico_City has had no daylight-saving time since 2022-10-30.
CDMX = timezone(timedelta(hours=-6), "America/Mexico_City")
PLACEHOLDER = re.compile(r"\{([a-z][a-z0-9_]*)\}")


# --------------------------------------------------------------------------- catalogs


@lru_cache(maxsize=None)
def _load_catalog(path: str) -> dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != "fcmo-ui-catalog-v1":
        raise ValueError(f"{path}: not an fcmo-ui-catalog-v1 catalog")
    return doc


def load_ui_catalog(locale: str, catalog_dir: Path | None = None) -> dict[str, Any]:
    """The reader-facing UI catalog for ``locale`` (en, es-419 or zh-Hans)."""
    return _load_catalog(str((catalog_dir or CATALOG_DIR) / f"{locale}.json"))


def _fill(template: str, params: dict[str, Any]) -> str:
    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in params:
            raise KeyError(f"missing placeholder {{{key}}}")
        return str(params[key])

    return PLACEHOLDER.sub(sub, template)


def ui(locale: str, key: str, catalog_dir: Path | None = None, **params: Any) -> str:
    """``strings.<key>`` (dotted) with ``{name}`` placeholders filled."""
    node: Any = load_ui_catalog(locale, catalog_dir)["strings"]
    for part in key.split("."):
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(f"strings.{key} is not a string")
    return _fill(node, params)


def label(locale: str, group: str, code: Any, default: str | None = None, catalog_dir: Path | None = None) -> str | None:
    """Human label for an enum code; ``default`` (never the raw code) when unknown."""
    labels = load_ui_catalog(locale, catalog_dir)["labels"].get(group) or {}
    value = labels.get(str(code)) if code is not None else None
    return value if isinstance(value, str) else default


def plural(locale: str, key: str, count: int, catalog_dir: Path | None = None) -> str:
    catalog = load_ui_catalog(locale, catalog_dir)
    forms = catalog["plurals"][key]
    category = "one" if catalog.get("plural_rule") == "one_other" and count == 1 else "other"
    return _fill(forms.get(category) or forms["other"], {"count": count})


def parse_instant(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            text += "T00:00:00+00:00"
        elif re.fullmatch(r"\d{4}-\d{2}", text):
            text += "-01T00:00:00+00:00"
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def infer_precision(value: Any) -> str:
    """Date-only values and exact UTC midnights are calendar dates, not instants."""
    text = str(value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return "month"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return "day"
    parsed = parse_instant(text)
    if parsed is not None and (parsed.hour, parsed.minute, parsed.second, parsed.microsecond) == (0, 0, 0, 0):
        return "day"
    return "minute"


def format_date(
    value: Any,
    locale: str,
    precision: str | None = None,
    style: str = "date_long",
    catalog_dir: Path | None = None,
) -> str:
    """Format a date for readers from the catalog's own month tables.

    ``precision`` minute/hour: the instant is shown in America/Mexico_City.
    ``precision`` day/month: the calendar date is shown as recorded (no shift),
    so an event on 8 September never becomes 7 September. When ``precision``
    is None it is inferred (exact UTC midnight means a date-only value).
    ``style`` is a pattern name: date_long, date_medium, date_short,
    month_year, weekday_date, datetime. Returns "" for an unreadable value.
    """
    parsed = parse_instant(value)
    if parsed is None:
        return ""
    precision = precision or infer_precision(value)
    calendar = precision in {"day", "month"}
    local = parsed if calendar else parsed.astimezone(CDMX)
    date_table = load_ui_catalog(locale, catalog_dir)["date"]
    patterns = date_table["patterns"]
    if precision == "month" and style not in {"month_year"}:
        style = "month_year"
    if calendar and style == "datetime":
        style = "date_long"
    fields = {
        "year": local.year,
        "month": date_table["months"][local.month - 1],
        "month_short": date_table["months_short"][local.month - 1],
        "month_number": local.month,
        "day": local.day,
        "weekday": date_table["weekdays"][local.weekday()],
        "hour24": f"{local.hour:02d}",
        "hour12": str((local.hour % 12) or 12),
        "minute": f"{local.minute:02d}",
        "ampm": date_table["am_pm"][0 if local.hour < 12 else 1],
        "tz": date_table["tz_label"],
    }
    if style == "datetime":
        fields["date"] = _fill(patterns["date_long"], fields)
        fields["time"] = _fill(patterns["time"], fields)
    return _fill(patterns[style], fields)


# --------------------------------------------------------------------------- pages


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def site_base(config: Path | None) -> str:
    if config and config.is_file():
        base = json.loads(config.read_text(encoding="utf-8")).get("base_url")
        if isinstance(base, str) and base.startswith("https://"):
            return base if base.endswith("/") else base + "/"
    return DEFAULT_BASE


def story_url(base: str, locale: str, rid: str) -> str:
    return f"{base}news/{ROUTE_SLUG[locale]}/{rid}.html"


def native_text(overlay: Any, key: str, status: dict[str, Any]) -> str:
    """Overlay text for ``key`` only when that field passed the completeness gates."""
    if status.get("state") == "FAILED" or not isinstance(overlay, dict):
        return ""
    if key not in set(status.get("complete_keys") or ()):
        return ""
    value = overlay.get(key)
    return value.strip() if isinstance(value, str) else ""


def desk_label(locale: str, story: dict[str, Any], source: dict[str, Any] | None, catalog_dir: Path | None) -> str:
    for code in ((source or {}).get("primary_desk"), story.get("primary_desk")):
        text = label(locale, "desk", code, catalog_dir=catalog_dir)
        if text:
            return text
    return label(locale, "story_type", story.get("story_type"), catalog_dir=catalog_dir) or ""


def event_line(locale: str, story: dict[str, Any], source: dict[str, Any] | None, catalog_dir: Path | None) -> str:
    event = (source or {}).get("event_at") or story.get("event_at")
    precision = (source or {}).get("date_precision") or story.get("date_precision")
    when = format_date(event, locale, precision, catalog_dir=catalog_dir)
    return ui(locale, "story.event_date", catalog_dir, date=when) if when else ""


def pending_page(
    locale: str,
    story: dict[str, Any],
    status: dict[str, Any],
    overlay: Any = None,
    source: dict[str, Any] | None = None,
    base: str = DEFAULT_BASE,
    catalog_dir: Path | None = None,
) -> str:
    """A native route whose edition is incomplete: native parts, notice, link to English."""
    cat = load_ui_catalog(locale, catalog_dir)
    rid = str(story.get("research_id") or "")
    english = story_url(base, "en", rid)
    self_url = story_url(base, locale, rid)
    pending_title = ui(locale, "l10n.pending_title", catalog_dir)
    title = native_text(overlay, "title", status)
    summary = native_text(overlay, "summary", status)
    why = native_text(overlay, "why_it_matters", status)
    notice_key = "l10n.pending_partial" if title and summary else "l10n.pending_notice"
    notice = ui(locale, notice_key, catalog_dir)
    headline_en = str(story.get("headline") or (source or {}).get("title") or rid)
    kicker = desk_label(locale, story, source, catalog_dir)
    published = format_date(story.get("published_at"), locale, "minute", "datetime", catalog_dir)
    updated = format_date(story.get("modified_at"), locale, "minute", "datetime", catalog_dir)
    page_title = title or pending_title
    ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_title,
        "description": notice,
        "inLanguage": cat["html_lang"],
        "url": self_url,
        "about": {"@type": "NewsArticle", "headline": headline_en, "inLanguage": "en", "url": english},
        "publisher": {"@type": "Organization", "name": ui(locale, "site.name", catalog_dir), "url": base},
    }
    ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    parts: list[str] = [
        "<!doctype html>",
        f'<html lang="{esc(cat["html_lang"])}" data-translation-status="pending" '
        f'data-l10n-state="{esc(status.get("state"))}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{esc(page_title)} · {esc(ui(locale, 'site.name', catalog_dir))}</title>",
        f'<meta name="description" content="{esc(summary or notice)}">',
        '<meta name="robots" content="noindex">',
        # Until the edition is complete the English story is the canonical page.
        f'<link rel="canonical" href="{esc(english)}">',
        f'<link rel="alternate" hreflang="en" href="{esc(english)}">',
        f'<link rel="alternate" hreflang="x-default" href="{esc(english)}">',
        '<link rel="stylesheet" href="../../assets/newsroom.css">',
        f'<script type="application/ld+json">{ld_json}</script>',
        "</head>",
        "<body>",
        f'<header class="wire-head"><a href="{esc(base)}">{esc(ui(locale, "site.name", catalog_dir))}</a>'
        f'<span>{esc(ui(locale, "site.tagline", catalog_dir))}</span></header>',
        '<main class="story">',
    ]
    if kicker:
        parts.append(f'<div class="kicker">{esc(kicker)}</div>')
    parts.append(f"<h1>{esc(page_title)}</h1>")
    if summary:
        parts.append(f'<p class="dek">{esc(summary)}</p>')
    meta_bits = [x for x in (event_line(locale, story, source, catalog_dir),
                             ui(locale, "story.published", catalog_dir, date=published) if published else "",
                             ui(locale, "story.updated", catalog_dir, date=updated) if updated and updated != published else "")
                 if x]
    parts.append(f'<p class="byline">{esc(ui(locale, "story.byline", catalog_dir))}'
                 + "".join(f" · {esc(x)}" for x in meta_bits) + "</p>")
    parts.append(
        '<aside class="l10n-pending" role="note">'
        f"<h2>{esc(pending_title)}</h2>"
        f"<p>{esc(notice)}</p>"
        f'<p><a href="{esc(english)}" hreflang="en">{esc(ui(locale, "l10n.read_original", catalog_dir))}</a></p>'
        "</aside>"
    )
    if why:
        parts.append(f"<section><h2>{esc(ui(locale, 'story.why_it_matters', catalog_dir))}</h2><p>{esc(why)}</p></section>")
    parts.append(
        '<section class="l10n-original">'
        f"<h2>{esc(ui(locale, 'l10n.original_headline', catalog_dir))}</h2>"
        f'<p lang="en">{esc(headline_en)}</p>'
        "</section>"
    )
    parts += ["</main>", "</body>", "</html>"]
    return "\n".join(parts) + "\n"


def index_page(
    locale: str,
    stories: list[dict[str, Any]],
    rows: dict[str, Any],
    statuses: dict[str, dict[str, Any]],
    canonical: dict[str, dict[str, Any]],
    base: str = DEFAULT_BASE,
    catalog_dir: Path | None = None,
) -> str:
    cat = load_ui_catalog(locale, catalog_dir)
    cards: list[str] = []
    for story in stories:
        rid = str(story.get("research_id") or "")
        status = statuses.get(rid) or {"state": "PENDING", "complete_keys": []}
        overlay = rows.get(rid)
        href = story_url(base, locale, rid)
        title = native_text(overlay, "title", status)
        summary = native_text(overlay, "summary", status)
        when = format_date(story.get("modified_at"), locale, "minute", "date_medium", catalog_dir)
        if is_complete(status):
            kicker = desk_label(locale, story, canonical.get(rid), catalog_dir)
        else:
            kicker = ui(locale, "l10n.pending_title", catalog_dir)
        heading = (
            f'<a href="{esc(href)}">{esc(title)}</a>' if title
            else f'<a href="{esc(href)}" lang="en">{esc(story.get("headline") or rid)}</a>'
        )
        body = summary or ui(locale, "l10n.pending_notice", catalog_dir)
        cards.append(
            f'<article data-translation-status="{"complete" if is_complete(status) else "pending"}">'
            f'<div class="kicker">{esc(kicker)}</div><h2>{heading}</h2>'
            f"<p>{esc(body)}</p><small>{esc(when)}</small></article>"
        )
    latest = ui(locale, "nav.latest", catalog_dir)
    name = ui(locale, "site.name", catalog_dir)
    return (
        f'<!doctype html><html lang="{esc(cat["html_lang"])}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(latest)} · {esc(name)}</title>"
        f'<link rel="stylesheet" href="../../assets/newsroom.css"></head><body>'
        f'<header class="wire-head"><a href="{esc(base)}">{esc(name)}</a><span>{esc(ui(locale, "site.tagline", catalog_dir))}</span></header>'
        f'<main class="story"><h1>{esc(latest)}</h1><div class="cards">{"".join(cards)}</div></main></body></html>\n'
    )


# --------------------------------------------------------------------------- status


def translation_status(stories: list[dict[str, Any]], statuses: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    ids = [str(s.get("research_id") or "") for s in stories]
    per_locale: dict[str, Any] = {}
    incomplete: set[str] = set()
    for locale in NATIVE_LOCALES:
        pending = sorted(rid for rid in ids if statuses[locale][rid]["state"] == "PENDING")
        failed = {rid: (statuses[locale][rid]["failure"] or {}).get("gate") for rid in ids
                  if statuses[locale][rid]["state"] == "FAILED"}
        complete = len(ids) - len(pending) - len(failed)
        incomplete |= set(pending) | set(failed)
        per_locale[locale] = {
            "complete": complete,
            "pending": len(pending),
            "failed": len(failed),
            "pending_ids": pending,
            "failed_ids": dict(sorted(failed.items())),
            "state_counts": {state: sum(statuses[locale][rid]["state"] == state for rid in ids)
                             for state in ("NATIVE_ARB", "MACHINE_REVIEWED", "PENDING", "FAILED")},
        }
    return {
        "schema": "fcmo-translation-status-v2",
        "canonical_locale": "en",
        "required_native_locales": list(NATIVE_LOCALES),
        "unit": "story_locale_pair",
        "rule": "a pair is complete only when every non-empty English prose field has a native counterpart that passes the gates",
        "canonical_story_count": len(ids),
        "native_complete_story_count": len(ids) - len(incomplete),
        "pending_translation_count": len(incomplete),
        "pending_translation_ids": sorted(incomplete),
        "locales": per_locale,
        "state": "COMPLETE" if not incomplete else "DEGRADED_TRANSLATION_BACKLOG",
    }


def render_pending(site: Path, canonical: dict[str, dict[str, Any]], i18n_dir: Path | None = None,
                   config: Path | None = Path("config/site.json"), catalog_dir: Path | None = None) -> int:
    """Render pending routes and measure the exact rebuilt Story set in one pass."""
    i18n_dir = i18n_dir or site / "data" / "i18n"
    admission_path = site.parent / 'release-src/data/publication-admission.json'
    if admission_path.is_file():
        try:
            from tools.native_admission import published_sources
        except ImportError:
            from native_admission import published_sources
        carried = set(json.loads(admission_path.read_text())['carried_ids'])
        canonical = dict(canonical)
        selected = published_sources(site.parent / 'release-src')
        canonical.update({rid: selected[rid] for rid in carried})
    stories = json.loads((site / "data" / "stories.json").read_text(encoding="utf-8"))
    if not isinstance(stories, list):
        raise SystemExit("pending localization renderer: stories.json must be a list")
    base = site_base(config)
    for locale in ("en", *NATIVE_LOCALES):
        load_ui_catalog(locale, catalog_dir)  # fail before writing anything

    all_statuses: dict[str, dict[str, dict[str, Any]]] = {}
    written: dict[str, int] = {}
    for locale in NATIVE_LOCALES:
        rows, strict_ids, provenance, _ = load_locale_details(i18n_dir, locale)
        statuses: dict[str, dict[str, Any]] = {}
        for story in stories:
            rid = str(story.get("research_id") or "")
            source = canonical.get(rid)
            if source is None:
                # No canonical English to judge against: never call it translated.
                statuses[rid] = {"state": "PENDING", "missing": ["canonical"], "missing_paths": [],
                                 "failure": None, "complete_keys": []}
            else:
                statuses[rid] = pair_status(source, rows.get(rid), locale, strict=rid in strict_ids,
                                            provenance=provenance.get(rid))
        folder = site / "news" / ROUTE_SLUG[locale]
        folder.mkdir(parents=True, exist_ok=True)
        count = 0
        for story in stories:
            rid = str(story.get("research_id") or "")
            if not is_complete(statuses[rid]):
                page = pending_page(locale, story, statuses[rid], rows.get(rid), canonical.get(rid), base, catalog_dir)
                (folder / f"{rid}.html").write_text(page, encoding="utf-8")
                count += 1
        (folder / "index.html").write_text(
            index_page(locale, stories, rows, statuses, canonical, base, catalog_dir), encoding="utf-8"
        )
        all_statuses[locale] = statuses
        written[locale] = count

    status_doc = translation_status(stories, all_statuses)
    manifest = i18n_dir / "translation-status.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(status_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    per_locale = " ".join(
        f"{loc}:pending={status_doc['locales'][loc]['pending']},failed={status_doc['locales'][loc]['failed']}"
        for loc in NATIVE_LOCALES
    )
    print(
        f"pending localization rendering OK; stories={len(stories)}; "
        f"native_complete={status_doc['native_complete_story_count']}; {per_locale}; state={status_doc['state']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--corpus", type=Path, default=Path("corpus"), help="canonical English records")
    parser.add_argument("--i18n-dir", type=Path, default=None, help="default: <site>/data/i18n")
    parser.add_argument("--config", type=Path, default=Path("config/site.json"))
    parser.add_argument("--catalog-dir", type=Path, default=None, help="default: i18n/ui of this repository")
    args = parser.parse_args(argv)
    return render_pending(args.site, load_corpus_canonical(args.corpus),
                          args.i18n_dir, args.config, args.catalog_dir)


if __name__ == "__main__":
    raise SystemExit(main())
