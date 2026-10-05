#!/usr/bin/env python3
"""Verify deployed autonomous Newsletter surfaces in a real browser.

The pre-deploy surface oracle proves geometry and semantics on the exact Pages
candidate. This companion oracle closes the post-deploy gap: it renders the live
origin after JavaScript executes and proves that Signal Field, Chronology and
Research Library still expose the deterministic current-publication contracts.
With ``--paper``, it renders the current SSG fronts and lead articles in EN/ES/ZH,
checks their language, lead identity and reader-visible publication state.
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
import urllib.request
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


def check_paper_surfaces(browser: str, base: str, identity: dict, stories: list[dict],
                         publication: dict, failures: list[str]) -> None:
    """Render the served SSG instead of testing retired SPA hash routes."""
    lead = next((s for s in stories if s.get("id") == identity.get("lead_id")), None)
    require(lead is not None, "deployed lead is absent from the Story layer", failures)
    if lead is None:
        return
    nonce = str(time.time_ns())
    date = str(lead["url_date"]).replace("-", "/")
    for locale, prefix in (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/")):
        story_route = prefix + date + "/" + lead["slug"] + "/"
        for route in (prefix, prefix + "diario/", story_route):
            page = render(browser, base + route + "?fcmo_live_surface=" + nonce)
            require(bool(re.search(r'<html\b[^>]*\blang="' + re.escape(locale) + '"', page)),
                    f"{route or '/'}: rendered language is not {locale}", failures)
            require(bool(re.search(r'<h1\b[^>]*>.*?</h1>', page, re.S)),
                    f"{route or '/'}: rendered headline missing", failures)
            require(identity["lead_id"] in page, f"{route or '/'}: deployed lead missing", failures)
            require('data-edition-state="' + publication["state"] + '"' in page,
                    f"{route or '/'}: rendered edition state differs from status.json", failures)
            if route != story_route:
                h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', page, re.S)
                require(bool(h1 and story_route in html.unescape(h1.group(1))),
                        f"{route or '/'}: rendered lead link differs from deployed identity", failures)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--paper", action="store_true", help="render the current paper SSG contracts")
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/") + "/"
    browser = browser_path()
    nonce = str(time.time_ns())
    failures: list[str] = []

    if args.paper:
        def read_json(route):
            with urllib.request.urlopen(base + route + "?fcmo_live_surface=" + nonce, timeout=25) as response:
                return json.load(response)
        identity = read_json("deployment-identity.json")
        stories = read_json("data/stories.v2.json")["stories"]
        publication = read_json("status.json")
        check_paper_surfaces(browser, base, identity, stories, publication, failures)
        if failures:
            raise SystemExit("LIVE PAPER SURFACE ORACLE FAILED:\n- " + "\n- ".join(failures))
        print(f"LIVE PAPER SURFACE ORACLE OK: lead={identity['lead_id']}; three locales; root, daily front and lead article")
        return 0

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
