#!/usr/bin/env python3
"""Reader-facing edition banner for the current site (front page and /news pages).

Two layers, both first-party and static-first:

1. Build time. The banner is rendered from ``data/newsroom-status.json``
   (contracts/newsroom-status.v2.schema.json) in English, Spanish and Chinese:
   ``FRESH`` shows only an "Updated <date>" line, ``QUIET`` says there are no
   material changes since <date>, ``DELAYED`` and ``TRANSPORT_DOWN`` say today's
   edition is delayed and give the latest edition date (``TRANSPORT_DOWN`` also
   links the status page). Dates are Mexico City calendar dates.
2. Reader time. If GitHub Actions stops, nothing rebuilds and the build-time
   banner would keep saying the edition is fine. Every page therefore embeds
   the status time (``status_updated_at``) and a script of at most 1 KB that
   reveals a pre-rendered "may be out of date" notice once the reader's clock is
   more than ``reader_stale_banner_after_h`` (36 h) past it.

The block sits right after ``<body>`` between two markers, so applying it again
replaces it. The root front page switches language at runtime, so it carries
all three languages and CSS ``:lang()`` shows the one matching ``<html lang>``;
localized pages carry only their own language.

Usage::

    python tools/edition_banner.py --site publish            # inject into the Pages candidate
    python tools/edition_banner.py --site publish --check    # verify every target page has it
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from tools import wire_status
except ImportError:  # executed as tools/edition_banner.py
    import wire_status  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- fcmo-edition:start -->"
END = "<!-- fcmo-edition:end -->"
BLOCK = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
BODY = re.compile(r"<body\b[^>]*>", re.I)
HTML_LANG = re.compile(r"<html\b[^>]*\blang=\"([^\"]+)\"", re.I)
STATES = ("FRESH", "QUIET", "DELAYED", "TRANSPORT_DOWN")
LANGS = ("en", "es", "zh")
HTML_LANGS = {"en": "en", "es": "es-419", "zh": "zh-Hans"}
MONTHS = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "es": ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"),
}
TEXT = {
    "en": {
        "FRESH": "Updated {date}",
        "QUIET": "No material changes since {date}; the system keeps checking sources.",
        "DELAYED": "Today’s edition is delayed. Latest edition: {date}.",
        "STATUS_LINK": "See newsroom status",
        "STALE": "This page may be out of date: the newsroom has not confirmed an update since {date}. Latest edition: {edition}.",
    },
    "es": {
        "FRESH": "Actualizado {date}",
        "QUIET": "Sin cambios materiales desde {date}; el sistema sigue verificando fuentes.",
        "DELAYED": "La edición de hoy está retrasada. Última edición: {date}.",
        "STATUS_LINK": "Ver estado de la redacción",
        "STALE": "Esta página puede estar desactualizada: la redacción no confirma una actualización desde el {date}. Última edición: {edition}.",
    },
    "zh": {
        "FRESH": "更新于 {date}",
        "QUIET": "自 {date} 以来没有实质性更新；系统仍在持续核查来源。",
        "DELAYED": "今日版本延迟发布。最新一期：{date}。",
        "STATUS_LINK": "查看编辑部状态",
        "STALE": "本页内容可能已过时：编辑部自 {date} 起未确认任何更新。最新一期：{edition}。",
    },
}
STYLE = (
    "<style>.fcmo-edition{margin:0;padding:.5rem 1rem;font:500 14px/1.45 system-ui,-apple-system,"
    "'Segoe UI',sans-serif;background:#f2efe8;color:#0a0a0a;border-bottom:1px solid #d6d0c2;"
    "overflow-wrap:anywhere}.fcmo-edition p{margin:0}.fcmo-edition[data-edition-state=DELAYED],"
    ".fcmo-edition[data-edition-state=TRANSPORT_DOWN],.fcmo-edition-stale{background:#fff1e6;"
    "border-bottom:2px solid #b3470f}.fcmo-edition a{color:#8a2d00;font-weight:700}"
    ".fcmo-edition [data-l]{display:none}html:not(:lang(es)):not(:lang(zh)) .fcmo-edition [data-l=en],"
    "html:lang(es) .fcmo-edition [data-l=es],html:lang(zh) .fcmo-edition [data-l=zh]{display:block}</style>"
)
# Reader-side fail-safe. Kept tiny on purpose (budget: 1024 bytes).
WATCH_SCRIPT = (
    "(function(){var e=document.getElementById('fcmo-edition-stale');"
    "if(!e)return;var t=Date.parse(e.getAttribute('data-status-updated-at')),"
    "h=+e.getAttribute('data-stale-after-h')||36;"
    "if(t&&Date.now()-t>h*36e5)e.hidden=false})();"
)
SCRIPT_BUDGET = 1024


def lang_key(value: str | None) -> str:
    value = (value or "en").lower()
    return "es" if value.startswith("es") else "zh" if value.startswith("zh") else "en"


def local_date(value: Any, lang: str) -> str:
    day = wire_status.cdmx_date(value)
    year, month, dom = (int(part) for part in day.split("-"))
    if lang == "zh":
        return f"{year}年{month}月{dom}日"
    if lang == "es":
        return f"{dom} {MONTHS['es'][month - 1]} {year}"
    return f"{MONTHS['en'][month - 1]} {dom}, {year}"


def status_fields(status: dict[str, Any]) -> dict[str, Any]:
    """Banner inputs; legacy status files (before the v2 fields) get no state line."""
    state = status.get("edition_state") if status.get("edition_state") in STATES else None
    stamp = status.get("status_updated_at") or status.get("finalized_at")
    edition = status.get("last_edition_at") or status.get("airlock_generated_at") or stamp
    return {
        "state": state,
        "reason": status.get("edition_reason"),
        "status_at": wire_status.fmt_utc(stamp) if stamp else None,
        "edition_at": wire_status.fmt_utc(edition) if edition else None,
        "quiet_since": status.get("quiet_since") or edition,
    }


def render(status: dict[str, Any], langs: tuple[str, ...], base_path: str, stale_after_h: int) -> str:
    """The banner block for one page (``langs`` = languages to carry)."""
    fields = status_fields(status)
    parts = [START, STYLE]
    state = fields["state"]
    if state:
        attrs = f' data-edition-state="{state}"'
        if fields["reason"]:
            attrs += f' data-edition-reason="{html.escape(str(fields["reason"]))}"'
        if fields["edition_at"]:
            attrs += f' data-last-edition-at="{fields["edition_at"]}"'
        role = ' role="status"' if state in ("DELAYED", "TRANSPORT_DOWN") else ""
        lines = []
        for lang in langs:
            key = "DELAYED" if state == "TRANSPORT_DOWN" else state
            when = fields["quiet_since"] if state == "QUIET" else fields["status_at"] if state == "FRESH" else fields["edition_at"]
            text = html.escape(TEXT[lang][key].format(date=local_date(when, lang)))
            if state == "TRANSPORT_DOWN":
                href = html.escape(base_path.rstrip("/") + "/status.html")
                text += f' <a href="{href}">{html.escape(TEXT[lang]["STATUS_LINK"])}</a>'
            lines.append(f'<p data-l="{lang}" lang="{HTML_LANGS[lang]}">{text}</p>')
        parts.append(f'<div class="fcmo-edition" id="fcmo-edition"{attrs}{role}>' + "".join(lines) + "</div>")
    if fields["status_at"]:
        stale = []
        for lang in langs:
            text = TEXT[lang]["STALE"].format(
                date=local_date(fields["status_at"], lang),
                edition=local_date(fields["edition_at"] or fields["status_at"], lang),
            )
            stale.append(f'<p data-l="{lang}" lang="{HTML_LANGS[lang]}">{html.escape(text)}</p>')
        parts.append(
            f'<div class="fcmo-edition fcmo-edition-stale" id="fcmo-edition-stale" role="alert" hidden '
            f'data-status-updated-at="{fields["status_at"]}" data-stale-after-h="{int(stale_after_h)}">'
            + "".join(stale) + "</div>"
        )
        parts.append(f"<script>{WATCH_SCRIPT}</script>")
    parts.append(END)
    return "".join(parts)


def target_pages(site: Path) -> list[Path]:
    pages = [site / "index.html", site / "news" / "index.html"]
    for locale in ("en", "es", "zh-hans"):
        folder = site / "news" / locale
        if folder.is_dir():
            pages += sorted(folder.glob("*.html"))
    return [page for page in pages if page.is_file()]


def apply(text: str, status: dict[str, Any], *, all_languages: bool, base_path: str, stale_after_h: int) -> str:
    text = BLOCK.sub("", text)
    match = BODY.search(text)
    if not match:
        raise ValueError("page has no <body> tag")
    lang = HTML_LANG.search(text)
    langs = LANGS if all_languages else (lang_key(lang.group(1) if lang else "en"),)
    block = render(status, langs, base_path, stale_after_h)
    return text[: match.end()] + block + text[match.end():]


def base_path_from_config() -> str:
    config = ROOT / "config" / "site.json"
    try:
        return json.loads(config.read_text(encoding="utf-8")).get("base_path") or "/"
    except (OSError, ValueError):
        return "/"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", type=Path, required=True, help="site tree to update (e.g. the Pages candidate)")
    parser.add_argument("--status", type=Path, help="newsroom status (default: <site>/data/newsroom-status.json)")
    parser.add_argument("--base-path", default=None, help="site base path (default: config/site.json)")
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    args = parser.parse_args(argv)
    status_path = args.status or args.site / "data" / "newsroom-status.json"
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if not isinstance(status, dict):
            raise ValueError("newsroom status is not an object")
        stale_after_h = int(wire_status.load_thresholds()["editorial"]["reader_stale_banner_after_h"])
        base_path = args.base_path or base_path_from_config()
        pages = target_pages(args.site)
        if not pages:
            raise ValueError("no front page or /news pages found")
        if len(WATCH_SCRIPT.encode("utf-8")) > SCRIPT_BUDGET:
            raise ValueError("reader-side script exceeds 1 KB")
        state = status_fields(status)["state"] or "LEGACY"
        bad = []
        for page in pages:
            text = page.read_text(encoding="utf-8")
            is_front = page == args.site / "index.html"
            wanted = apply(text, status, all_languages=is_front, base_path=base_path, stale_after_h=stale_after_h)
            if args.check:
                if wanted != text:
                    bad.append(page.relative_to(args.site).as_posix())
            elif wanted != text:
                page.write_text(wanted, encoding="utf-8")
        if bad:
            print(f"EDITION BANNER MISSING pages={len(bad)} first={bad[0]}", file=sys.stderr)
            return 1
        verb = "checked" if args.check else "applied"
        print(f"EDITION BANNER {verb} state={state} pages={len(pages)} script_bytes={len(WATCH_SCRIPT.encode('utf-8'))}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"edition banner FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
