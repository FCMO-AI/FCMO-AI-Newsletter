#!/usr/bin/env python3
"""Render the assembled Newsletter in a real browser and verify runtime contracts.

This oracle deliberately inspects the rendered DOM, not source strings.  The
curated i18n layer runs after load, so static grep can report green while the
reader still sees stale English or stale corpus metrics.  Chrome/Chromium and
Edge are supported; ``FCMO_BROWSER`` may override auto-detection.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from contextlib import contextmanager
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


BROWSER_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "msedge",
    "microsoft-edge",
    "microsoft-edge-stable",
)
WINDOWS_EDGE = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)


class RenderedDOM(HTMLParser):
    """Collect reader-facing text and corpus-stat nodes from dumped DOM."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ignored_depth = 0
        self.text: list[str] = []
        self.lang = ""
        self._stat_stack: list[str | None] = []
        self._stat_parts: dict[str, list[str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.lang = attrs_map.get("lang", "")
        if tag in {"script", "style", "noscript", "template"}:
            self.ignored_depth += 1
        stat = attrs_map.get("data-fcmo-stat")
        self._stat_stack.append(stat or None)
        if stat:
            self._stat_parts.setdefault(stat, [])

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._stat_stack:
            self._stat_stack.pop()
        if tag in {"script", "style", "noscript", "template"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.ignored_depth:
            return
        cleaned = " ".join(data.split())
        if cleaned:
            self.text.append(cleaned)
        for stat in self._stat_stack:
            if stat and cleaned:
                self._stat_parts.setdefault(stat, []).append(cleaned)

    @property
    def visible_text(self) -> str:
        return " ".join(self.text)

    @property
    def stats(self) -> dict[str, str]:
        return {key: " ".join(parts).strip() for key, parts in self._stat_parts.items()}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


def browser_path() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return str(candidate)
        resolved = shutil.which(override)
        if resolved:
            return resolved
        raise RuntimeError(f"FCMO_BROWSER does not resolve to an executable: {override}")
    for name in BROWSER_CANDIDATES:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    for candidate in WINDOWS_EDGE:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(
        "no supported headless browser found; install Chrome/Chromium/Edge or set FCMO_BROWSER"
    )


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/index.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def render(browser: str, url: str) -> RenderedDOM:
    # Footnote: each navigation gets a fresh browser profile so localStorage from
    # one locale cannot make the next case pass accidentally. ja-JP also makes
    # browser-language fallback useless to ES/ZH assertions. Chrome can leave a
    # short-lived profile helper after its main process exits, so cleanup is best
    # effort; profile leftovers must never turn a successful DOM assertion red.
    profile = Path(tempfile.mkdtemp(prefix="fcmo-dom-profile-"))
    try:
        command = [
            browser,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--hide-scrollbars",
            "--lang=ja-JP",
            "--virtual-time-budget=2500",
            f"--user-data-dir={profile}",
            "--dump-dom",
            url,
        ]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"browser failed for {url} (exit {completed.returncode}):\n{completed.stderr[-3000:]}"
            )
        if "<html" not in completed.stdout.lower():
            raise AssertionError(f"browser returned no DOM for {url}")
        dom = RenderedDOM()
        dom.feed(completed.stdout)
        return dom
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expected_metrics(root: Path) -> dict[str, str]:
    source = (root / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', source, re.S)
    if not match:
        raise AssertionError("assembled index is missing fcmo-data")
    import json

    meta = json.loads(match.group(1))["meta"]
    return {key: str(meta[key]) for key in ("count", "evidenceA", "open_gaps", "relationships")}


def run(root: Path) -> int:
    root = root.resolve()
    require((root / "index.html").is_file(), f"assembled tree has no index.html: {root}")
    browser = browser_path()
    metrics = expected_metrics(root)
    checks = 0

    with serve(root) as base:
        cases = (
            ("en", "research", "Evidence distribution", None),
            ("es-419", "research", "Distribución de evidencia", "Evidence distribution"),
            ("zh-Hans", "research", "证据分布", "Evidence distribution"),
            (
                "es-419",
                "route-that-does-not-exist",
                "Esa ruta independiente no existe. Usa la navegación de la publicación que aparece arriba.",
                "That standalone route does not exist. Use the publication navigation above.",
            ),
            (
                "zh-Hans",
                "route-that-does-not-exist",
                "该独立路由不存在。请使用上方的出版物导航。",
                "That standalone route does not exist. Use the publication navigation above.",
            ),
            ("en", "agent", None, "22 BRIEFS"),
            ("es-419", "agent", None, "22 BRIEFS"),
            ("zh-Hans", "agent", None, "22 BRIEFS"),
        )
        for locale, route, required_text, forbidden_text in cases:
            url = f"{base}?lang={quote(locale)}#/{route}"
            dom = render(browser, url)
            require(dom.lang == locale, f"{route}/{locale}: html lang is {dom.lang!r}")
            for key, value in metrics.items():
                require(
                    dom.stats.get(key) == value,
                    f"{route}/{locale}: persistent stat {key}={dom.stats.get(key)!r}, expected {value!r}",
                )
            if required_text:
                require(required_text in dom.visible_text, f"{route}/{locale}: missing {required_text!r}")
            if forbidden_text:
                require(forbidden_text not in dom.visible_text, f"{route}/{locale}: leaked {forbidden_text!r}")
            checks += 1

    version = subprocess.run(
        [browser, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip()
    print(
        f"DOM browser oracle OK: {checks} route/locale renders; "
        f"metrics={metrics}; browser={version or Path(browser).name}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("publish"))
    args = parser.parse_args(argv)
    try:
        return run(args.root)
    except (OSError, RuntimeError, AssertionError, subprocess.SubprocessError) as exc:
        print(f"DOM browser oracle FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
