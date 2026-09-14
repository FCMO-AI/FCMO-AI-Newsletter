#!/usr/bin/env python3
"""Verify the reader-visible homepage lead in a real browser for EN/ES/ZH.

This closes the gap between static HTML/route checks and what a reader actually
sees after the app-shell and curated i18n runtime execute. It can test either a
local assembled publication tree or the deployed GitHub Pages origin.

Native locales are first-class, but a truthful, explicit translation backlog must
not roll the canonical English newspaper backward. When the current lead has no
native overlay yet, the localized article route must be an explicit pending shell
that links to the canonical English story; the homepage may therefore retain the
canonical English headline until the native overlay lands. This is degraded but
valid publication, never a fake translation.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

BROWSER_CANDIDATES = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "msedge", "microsoft-edge", "microsoft-edge-stable",
)

LOCALE_SLUG = {"es-419": "es", "zh-Hans": "zh-hans"}


class VisibleDOM(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.parts: list[str] = []
        self.lang = ""
        self.attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "html":
            self.lang = attrs_map.get("lang", "")
            self.attrs = attrs_map
        if tag.lower() in {"script", "style", "noscript", "template"}:
            self.ignored += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "template"} and self.ignored:
            self.ignored -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)

    @property
    def text(self) -> str:
        return " ".join(self.parts)


def browser_path() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override:
        resolved = shutil.which(override)
        if resolved:
            return resolved
        if Path(override).is_file():
            return override
        raise RuntimeError(f"FCMO_BROWSER does not resolve: {override}")
    for name in BROWSER_CANDIDATES:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("no supported Chrome/Chromium/Edge browser found")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def render(browser: str, url: str) -> VisibleDOM:
    profile = Path(tempfile.mkdtemp(prefix="fcmo-home-profile-"))
    try:
        completed = subprocess.run(
            [
                browser, "--headless=new", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--disable-background-networking",
                "--disable-component-update", "--disable-sync", "--hide-scrollbars",
                "--lang=ja-JP", "--virtual-time-budget=3000",
                f"--user-data-dir={profile}", "--dump-dom", url,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=40,
        )
        if completed.returncode != 0 or "<html" not in completed.stdout.lower():
            raise AssertionError(
                f"browser failed for {url} (exit {completed.returncode}): {completed.stderr[-2000:]}"
            )
        dom = VisibleDOM()
        dom.feed(completed.stdout)
        return dom
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def load_native_records(root: Path, locale: str) -> dict[str, dict]:
    records: dict[str, dict] = {}
    locale_dir = root / "data" / "i18n" / locale
    for path in sorted(locale_dir.glob("part-*.json")):
        part = json.loads(path.read_text(encoding="utf-8"))
        records.update(part.get("records") or {})
    return records


def canonical_title(root: Path) -> str:
    stories = json.loads((root / "data" / "stories.json").read_text(encoding="utf-8"))
    return str(stories[0]["headline"]).strip()


def locale_expectation(root: Path, locale: str, rid: str) -> tuple[str, bool]:
    """Return homepage title plus whether this locale is explicitly pending."""
    if locale == "en":
        return canonical_title(root), False
    row = load_native_records(root, locale).get(rid) or {}
    title = row.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip(), False

    status_path = root / "data" / "i18n" / "translation-status.json"
    if not status_path.is_file():
        raise AssertionError(f"{locale}: missing current lead translation for {rid} and no backlog manifest")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    pending = set(status.get("pending_translation_ids") or [])
    if rid not in pending:
        raise AssertionError(f"{locale}: missing current lead translation for {rid} but it is not declared pending")
    return canonical_title(root), True


def prove_pending_route(root: Path, browser: str, base: str, locale: str, rid: str) -> None:
    slug = LOCALE_SLUG[locale]
    url = f"{base}news/{slug}/{rid}.html?fcmo_verify={time.time_ns()}"
    dom = render(browser, url)
    if dom.lang != locale:
        raise AssertionError(f"pending/{locale}: html lang is {dom.lang!r}")
    if dom.attrs.get("data-translation-status") != "pending":
        raise AssertionError(f"pending/{locale}: route is not explicitly marked pending")
    expected_notice = "Traducción pendiente" if locale == "es-419" else "翻译待完成"
    if expected_notice not in dom.text:
        raise AssertionError(f"pending/{locale}: localized pending notice is not reader-visible")
    canonical_href = f"/news/en/{rid}.html"
    # dump-dom preserves the absolute/relative href string; checking the raw page
    # through visible content alone would not prove the canonical escape hatch.
    page_path = root / "news" / slug / f"{rid}.html"
    if page_path.is_file():
        source = page_path.read_text(encoding="utf-8")
        if canonical_href not in source and f"/FCMO-AI-Newsletter{canonical_href}" not in source:
            raise AssertionError(f"pending/{locale}: no canonical-English link for {rid}")


def run(root: Path, base_url: str | None) -> int:
    root = root.resolve()
    stories = json.loads((root / "data" / "stories.json").read_text(encoding="utf-8"))
    if not isinstance(stories, list) or not stories:
        raise AssertionError("Story layer is empty")
    rid = str(stories[0].get("research_id") or "")
    if not rid:
        raise AssertionError("current Story lead has no research_id")

    browser = browser_path()
    expected = {
        locale: locale_expectation(root, locale, rid)
        for locale in ("en", "es-419", "zh-Hans")
    }

    @contextmanager
    def origin():
        if base_url:
            yield base_url.rstrip("/") + "/"
        else:
            with serve(root) as local:
                yield local

    pending_locales: list[str] = []
    with origin() as base:
        for locale, (title, pending) in expected.items():
            params = urlencode({
                "lang": locale,
                "fcmo_verify": str(time.time_ns()),
            })
            url = f"{base}?{params}#/home"
            dom = render(browser, url)
            if dom.lang != locale:
                raise AssertionError(f"home/{locale}: html lang is {dom.lang!r}")
            if title not in dom.text:
                state = "pending canonical-English" if pending else "native"
                raise AssertionError(
                    f"home/{locale}: reader-visible lead is not current {rid} ({state}); expected {title!r}"
                )
            if pending:
                prove_pending_route(root, browser, base, locale, rid)
                pending_locales.append(locale)

    version = subprocess.run(
        [browser, "--version"], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip()
    where = base_url or str(root)
    state = "DEGRADED_TRANSLATION_BACKLOG" if pending_locales else "FULLY_LOCALIZED"
    detail = ",".join(pending_locales) if pending_locales else "none"
    print(
        f"HOME LEAD BROWSER OK: {rid}; EN/ES/ZH reader render current; "
        f"localization={state}; pending={detail}; target={where}; browser={version}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("publish"))
    parser.add_argument("--base-url")
    args = parser.parse_args(argv)
    try:
        return run(args.root, args.base_url)
    except (OSError, RuntimeError, AssertionError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"HOME LEAD BROWSER FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
