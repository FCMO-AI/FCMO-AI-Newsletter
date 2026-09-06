#!/usr/bin/env python3
"""Reality-grounded post-deploy oracle for the live FCMO AI Newsletter.

Build and Pages deployment status are not treated as proof of public visibility.
This oracle fetches the production origin, compares the live newsroom receipt
with repository truth, and opens the multilingual Story and discovery surfaces.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
USER_AGENT = "FCMO-Newsroom-Live-Oracle/1.1"


def fetch(url: str, attempts: int = 6) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
            with urllib.request.urlopen(request, timeout=20) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, RuntimeError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(5)
    raise RuntimeError(f"live fetch failed for {url}: {last}")


def load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"live {label} is not valid JSON: {exc}") from exc


def parse_utc(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result if result.tzinfo else result.replace(tzinfo=timezone.utc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--status", type=Path, default=Path("site/data/newsroom-status.json"))
    parser.add_argument("--stories", type=Path, default=Path("site/data/stories.json"))
    parser.add_argument("--allow-unbootstrapped", action="store_true")
    parser.add_argument("--max-airlock-age-hours", type=int, default=48)
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")

    root = fetch(base + "/").decode("utf-8", errors="replace")
    if "FCMO AI Newsletter" not in root:
        raise SystemExit("live oracle FAILED: production root does not identify the publication")

    if not args.status.is_file():
        if args.allow_unbootstrapped:
            print("live oracle BASELINE OK: root is live; autonomous newsroom status not bootstrapped in this commit")
            return 0
        raise SystemExit("live oracle FAILED: repository newsroom status is absent")

    expected = json.loads(args.status.read_text(encoding="utf-8"))
    expected_stories = json.loads(args.stories.read_text(encoding="utf-8"))
    if not isinstance(expected_stories, list) or not expected_stories:
        raise SystemExit("live oracle FAILED: repository Story layer is empty")

    live_status = load_json_bytes(fetch(base + "/data/newsroom-status.json"), "newsroom status")
    if live_status.get("release_id") != expected.get("release_id"):
        raise SystemExit(
            f"live oracle FAILED: release mismatch repo={expected.get('release_id')} live={live_status.get('release_id')}"
        )
    if live_status.get("story_layer_count") != len(expected_stories):
        raise SystemExit("live oracle FAILED: live status story count does not match repository Story layer")

    live_stories = load_json_bytes(fetch(base + "/data/stories.json"), "Story index")
    if not isinstance(live_stories, list) or len(live_stories) != len(expected_stories):
        raise SystemExit(
            f"live oracle FAILED: Story index count repo={len(expected_stories)} live={len(live_stories) if isinstance(live_stories, list) else 'invalid'}"
        )

    allowed_states = {
        "BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE",
        "PUBLIC_DELTA_READY",
        "NO_PUBLIC_DELTA_READY",
    }
    if live_status.get("state") not in allowed_states:
        raise SystemExit(f"live oracle FAILED: unsupported newsroom state {live_status.get('state')!r}")

    generated = live_status.get("airlock_generated_at")
    if generated:
        age = datetime.now(timezone.utc) - parse_utc(str(generated))
        if age > timedelta(hours=args.max_airlock_age_hours):
            raise SystemExit(f"live oracle FAILED: deployed airlock heartbeat is stale ({age.total_seconds()/3600:.1f}h)")

    # Footnote: these are product contracts, not decorative routes. Requiring them
    # from the production origin prevents a green build from masking a deployment
    # that still serves the former shells or omits machine-facing discovery.
    required_routes = (
        "/archive.html", "/search.html", "/topics.html", "/organizations.html",
        "/corrections.html", "/feeds.html", "/methodology.html", "/editorial-policy.html",
        "/automation.html", "/accessibility.html", "/status.html", "/news/",
        "/news/en/", "/news/es/", "/news/zh-hans/", "/sitemap.xml", "/news-sitemap.xml",
        "/feed.xml", "/feed.json", "/llms.txt", "/llms-full.txt", "/agent.json",
    )
    for path in required_routes:
        fetch(base + path)

    search = fetch(base + "/search.html").decode("utf-8", errors="replace")
    if "data-search-root" not in search or "editorial-frontends.js" not in search:
        raise SystemExit("live oracle FAILED: search route is not the native local-search frontend")
    topics = fetch(base + "/topics.html").decode("utf-8", errors="replace")
    organizations = fetch(base + "/organizations.html").decode("utf-8", errors="replace")
    if "facet-row" not in topics or "facet-row" not in organizations:
        raise SystemExit("live oracle FAILED: topic/organization discovery routes are still shells")
    gateway = fetch(base + "/news/").decode("utf-8", errors="replace")
    if "Canonical semantic edition" not in gateway or "简体中文" not in gateway:
        raise SystemExit("live oracle FAILED: /news/ is not the three-edition gateway")

    latest_id = expected_stories[0].get("research_id")
    if not latest_id:
        raise SystemExit("live oracle FAILED: latest Story lacks research_id")
    for locale in ("en", "es", "zh-hans"):
        article = fetch(f"{base}/news/{locale}/{latest_id}.html").decode("utf-8", errors="replace")
        if '"@type": "NewsArticle"' not in article and '"@type":"NewsArticle"' not in article:
            raise SystemExit(f"live oracle FAILED: {locale} latest Story lacks NewsArticle structured data")
        if "hreflang=" not in article or "FCMO AI Research Desk" not in article:
            raise SystemExit(f"live oracle FAILED: {locale} latest Story lacks multilingual/byline contract")

    if "FCMO WIRE" not in root:
        raise SystemExit("live oracle FAILED: main publication has no route into FCMO WIRE")

    print(
        f"live newsroom PRODUCTION OK: release={live_status['release_id']} "
        f"state={live_status['state']} stories={len(expected_stories)}; full editorial/machine route suite + EN/ES/ZH verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
