#!/usr/bin/env python3
"""Verify that the release proven in CI is the one actually live on GitHub Pages.

Pre-deploy browser checks prove the candidate. This oracle closes the final gap by
checking the deployed origin: release identity, machine surfaces and one story in each
native locale. A successful deployment action without matching live bytes is not a
successful newspaper release.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

# Footnote: launching this file as ``python tests/oraculos/verificar_live.py`` puts
# only tests/oraculos on sys.path. Add the repository root explicitly so CI and local
# execution import the sibling oracle through the same stable package path.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.oraculos.verificar_dom import browser_path, render, require


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "FCMO-Live-Oracle/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "FCMO-Live-Oracle/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", "replace")


def verify_once(expected: Path, base: str) -> None:
    status = json.loads((expected / "data" / "newsroom-status.json").read_text(encoding="utf-8"))
    live_status = fetch_json(urljoin(base, "data/newsroom-status.json"))
    require(live_status.get("release_id") == status.get("release_id"), "live release_id does not match candidate")
    require(
        live_status.get("corpus_digest_sha256") == status.get("corpus_digest_sha256"),
        "live corpus digest does not match candidate",
    )
    for path, marker in (
        ("feed.json", "FCMO AI Newsletter"),
        ("sitemap.xml", "urlset"),
        ("news-sitemap.xml", "urlset"),
        ("data/news-articles.json", "NewsArticle"),
    ):
        require(marker in fetch_text(urljoin(base, path)), f"live {path} missing expected marker")

    stories = json.loads((expected / "data" / "stories.json").read_text(encoding="utf-8"))
    require(bool(stories), "candidate contains no Story objects")
    chosen = next(
        (story for story in stories if story.get("disposition") in {"LEAD", "STANDARD", "BRIEF", "SIGNAL"}),
        stories[0],
    )
    identifier = chosen["research_ids"][0]
    browser = browser_path()
    for segment, locale in (("en", "en"), ("es", "es-419"), ("zh-hans", "zh-Hans")):
        url = urljoin(base, f"{segment}/developments/{identifier}.html")
        dom = render(browser, url)
        require(dom.lang == locale, f"live {segment} story resolved with html lang={dom.lang!r}, expected {locale!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expected", type=Path)
    parser.add_argument("base_url")
    parser.add_argument("--attempts", type=int, default=8)
    parser.add_argument("--retry-seconds", type=float, default=8.0)
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    last: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            verify_once(args.expected.resolve(), base)
            print(f"LIVE oracle OK: candidate release is serving from {base}")
            return 0
        except (AssertionError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last = exc
            if attempt < args.attempts:
                time.sleep(args.retry_seconds)
    raise SystemExit(f"LIVE oracle FAILED after deploy: {last}")


if __name__ == "__main__":
    raise SystemExit(main())
