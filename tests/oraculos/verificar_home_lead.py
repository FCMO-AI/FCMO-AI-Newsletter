#!/usr/bin/env python3
"""Verify the reader-visible homepage lead in a real browser for EN/ES/ZH.

This closes the gap between static HTML/route checks and what a reader actually
sees after the app-shell and curated i18n runtime execute. It can test either a
local assembled publication tree or the deployed GitHub Pages origin.
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
from urllib.parse import quote, urlencode

BROWSER_CANDIDATES = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "msedge", "microsoft-edge", "microsoft-edge-stable",
)


class VisibleDOM(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.parts: list[str] = []
        self.lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {k.lower(): v or "" for k, v in attrs}
        if tag.lower() == "html":
            self.lang = attrs_map.get("lang", "")
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


def translated_title(root: Path, locale: str, rid: str) -> str:
    if locale == "en":
        stories = json.loads((root / "data" / "stories.json").read_text(encoding="utf-8"))
        return str(stories[0]["headline"])
    records: dict[str, dict] = {}
    locale_dir = root / "data" / "i18n" / locale
    for path in sorted(locale_dir.glob("part-*.json")):
        part = json.loads(path.read_text(encoding="utf-8"))
        records.update(part.get("records") or {})
    row = records.get(rid) or {}
    title = row.get("title")
    if not isinstance(title, str) or not title.strip():
        raise AssertionError(f"{locale}: missing current lead translation for {rid}")
    return title.strip()


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
        locale: translated_title(root, locale, rid)
        for locale in ("en", "es-419", "zh-Hans")
    }

    @contextmanager
    def origin():
        if base_url:
            yield base_url.rstrip("/") + "/"
        else:
            with serve(root) as local:
                yield local

    with origin() as base:
        for locale, title in expected.items():
            params = urlencode({
                "lang": locale,
                "fcmo_verify": str(time.time_ns()),
            })
            url = f"{base}?{params}#/home"
            dom = render(browser, url)
            if dom.lang != locale:
                raise AssertionError(f"home/{locale}: html lang is {dom.lang!r}")
            if title not in dom.text:
                raise AssertionError(
                    f"home/{locale}: reader-visible lead is not current {rid}; expected {title!r}"
                )

    version = subprocess.run(
        [browser, "--version"], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip()
    where = base_url or str(root)
    print(f"HOME LEAD BROWSER OK: {rid}; EN/ES/ZH reader render current; target={where}; browser={version}")
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
