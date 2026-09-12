#!/usr/bin/env python3
"""Fail unless the reader-facing GitHub Pages front page shows the current Story lead."""
from __future__ import annotations

import html
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/"
STORIES = Path("site/data/stories.json")
UA = "FCMO-Front-Page-Oracle/1.0"


def fetch_fresh(url: str, attempts: int = 12) -> str:
    last = ""
    for attempt in range(attempts):
        bust = ("&" if "?" in url else "?") + urllib.parse.urlencode({"fcmo_verify": str(time.time_ns())})
        req = urllib.request.Request(url + bust, headers={"User-Agent": UA, "Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                text = response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # network/transient propagation
            last = str(exc)
            text = ""
        if text:
            return text
        if attempt + 1 < attempts:
            time.sleep(5)
    raise SystemExit(f"front-page oracle FAILED: could not fetch production: {last}")


def main() -> int:
    stories = json.loads(STORIES.read_text(encoding="utf-8"))
    if not isinstance(stories, list) or not stories:
        raise SystemExit("front-page oracle FAILED: repository Story layer is empty")
    lead = stories[0]
    rid = str(lead.get("research_id") or "")
    headline = str(lead.get("headline") or "")
    if not rid or not headline:
        raise SystemExit("front-page oracle FAILED: repository lead lacks identity/headline")

    expected_marker = f"fcmo-story-lead:{rid}"
    expected_link = f"/FCMO-AI-Newsletter/news/en/{rid}.html"

    # GitHub Pages propagation can lag a successful deploy. Retry the actual
    # reader-facing root until the deployed bytes expose the exact current lead.
    last_problem = ""
    for attempt in range(12):
        root = fetch_fresh(BASE, attempts=1)
        marker_ok = expected_marker in root
        headline_ok = headline in html.unescape(root)
        link_ok = expected_link in root
        if marker_ok and headline_ok and link_ok:
            print(f"LIVE FRONT PAGE OK: {rid} :: {headline}")
            return 0
        last_problem = f"marker={marker_ok} headline={headline_ok} link={link_ok}"
        if attempt + 1 < 12:
            time.sleep(5)

    raise SystemExit(
        "front-page oracle FAILED: GitHub Pages is not serving the current Story lead; "
        f"expected {rid!r} / {headline!r}; {last_problem}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
