#!/usr/bin/env python3
"""Verify deployed autonomous Newsletter surfaces in a real browser.

The pre-deploy surface oracle proves geometry and semantics on the exact Pages
candidate. This companion oracle closes the post-deploy gap: it renders the live
origin after JavaScript executes and proves that Signal Field, Chronology and
Research Library still expose the deterministic current-publication contracts.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

BROWSERS = (
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "msedge", "microsoft-edge", "microsoft-edge-stable",
)
DEFAULT_BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/"


def browser_path() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override:
        resolved = shutil.which(override)
        if resolved:
            return resolved
        if Path(override).is_file():
            return override
        raise RuntimeError(f"FCMO_BROWSER does not resolve: {override}")
    for name in BROWSERS:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("no supported Chrome/Chromium/Edge browser found")


def render(browser: str, url: str) -> str:
    profile = Path(tempfile.mkdtemp(prefix="fcmo-live-surfaces-"))
    try:
        completed = subprocess.run(
            [
                browser, "--headless=new", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--disable-background-networking",
                "--disable-component-update", "--disable-sync", "--hide-scrollbars",
                "--virtual-time-budget=4500", "--window-size=1400,1200",
                f"--user-data-dir={profile}", "--dump-dom", url,
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", timeout=45,
        )
        if completed.returncode != 0 or "<html" not in completed.stdout.lower():
            raise AssertionError(
                f"browser failed for {url} (exit {completed.returncode}): {completed.stderr[-1600:]}"
            )
        return completed.stdout
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def attr(source: str, name: str) -> str:
    match = re.search(rf'\b{re.escape(name)}="([^"]*)"', source)
    return html.unescape(match.group(1)) if match else ""


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/") + "/"
    browser = browser_path()
    nonce = str(time.time_ns())
    failures: list[str] = []

    home = render(browser, f"{base}?fcmo_live_surface={nonce}#/home")
    require('data-fcmo-freshness="recent-public"' in home, "Signal Field lacks recent-public contract", failures)
    latest = attr(home, "data-fcmo-latest-publication")
    require(bool(re.fullmatch(r"20\d\d-\d\d-\d\d", latest)), "Signal Field latest-publication marker missing", failures)
    signal_nodes = len(re.findall(r'class="[^"]*\bsignal-node\b[^"]*"', home))
    require(signal_nodes == 10, f"Signal Field expected 10 nodes, found {signal_nodes}", failures)
    recent_activity = re.findall(r'data-fcmo-activity="(20\d\d-\d\d-\d\d)"', home)
    require(len(recent_activity) >= 10, "Signal Field activity markers incomplete", failures)

    chronology = render(browser, f"{base}?fcmo_live_surface={nonce}#/chronology")
    chrono_latest = attr(chronology, "data-fcmo-publication-activity")
    require(chrono_latest == latest, f"Chronology publication clock {chrono_latest or 'missing'} != {latest or 'missing'}", failures)
    require('data-fcmo-origin-chronology="true"' in chronology, "Chronology lost original-development clock", failures)

    research = render(browser, f"{base}?fcmo_live_surface={nonce}#/research")
    require('data-fcmo-library-sort="latest-verified"' in research, "Research Library lost latest-verified contract", failures)
    library_latest = attr(research, "data-fcmo-library-edition")
    require(library_latest == latest, f"Research Library edition {library_latest or 'missing'} != {latest or 'missing'}", failures)

    if failures:
        raise SystemExit("LIVE SURFACE ORACLE FAILED:\n- " + "\n- ".join(failures))

    version = subprocess.run(
        [browser, "--version"], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip() or Path(browser).name
    print(
        f"LIVE SURFACE ORACLE OK: publication={latest}; Signal Field=10 current nodes; "
        f"Chronology + Research Library current; target={base}; browser={version}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
