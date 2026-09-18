#!/usr/bin/env python3
"""Reality-grounded post-deploy oracle for the live FCMO AI Newsletter.

Build and Pages deployment status are not treated as proof of public visibility.
This oracle fetches the production origin, compares the live newsroom receipt
with repository truth, and opens the multilingual Story and discovery surfaces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
USER_AGENT = "FCMO-Newsroom-Live-Oracle/1.3"


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    parser.add_argument("--require-airlock", action="store_true")
    parser.add_argument("--max-airlock-age-hours", type=int, default=48)
    parser.add_argument("--expected-deployment-identity", type=Path)
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")

    root = fetch(base + "/").decode("utf-8", errors="replace")
    if "FCMO AI Newsletter" not in root:
        raise SystemExit("live oracle FAILED: production root does not identify the publication")

    # The reader-facing FCMO Wire control is retired, while the underlying /news/
    # gateway and Newswire Bridge transport remain valid. The DOM keeps a stable
    # marker so one shared stylesheet can suppress the retired reader control.
    # Source-string presence is therefore not visibility. Require the live CSS to
    # carry the approved fail-closed hide rule whenever the marker is present.
    if "data-fcmo-wire-link" in root:
        responsive_css = fetch(base + "/assets/newsletter-responsive-polish.css").decode("utf-8", errors="replace")
        compact_css = re.sub(r"\s+", "", responsive_css)
        if "[data-fcmo-wire-link]{display:none!important}" not in compact_css:
            raise SystemExit("live oracle FAILED: retired reader-facing FCMO WIRE control is not suppressed")

    if not args.status.is_file():
        if args.allow_unbootstrapped and not args.require_airlock:
            print("live oracle BASELINE OK: root is live; autonomous newsroom status not bootstrapped in this commit")
            return 0
        raise SystemExit("live oracle FAILED: repository newsroom status is absent")

    expected = json.loads(args.status.read_text(encoding="utf-8"))
    expected_stories = json.loads(args.stories.read_text(encoding="utf-8"))
    if not isinstance(expected_stories, list) or not expected_stories:
        raise SystemExit("live oracle FAILED: repository Story layer is empty")

    live_status_bytes = fetch(base + "/data/newsroom-status.json")
    live_status = load_json_bytes(live_status_bytes, "newsroom status")

    if live_status.get("release_id") != expected.get("release_id"):
        raise SystemExit(
            f"live oracle FAILED: release mismatch repo={expected.get('release_id')} live={live_status.get('release_id')}"
        )
    if live_status.get("story_layer_count") != len(expected_stories):
        raise SystemExit("live oracle FAILED: live status story count does not match repository Story layer")

    live_stories_bytes = fetch(base + "/data/stories.json")
    live_stories = load_json_bytes(live_stories_bytes, "Story index")
    if not isinstance(live_stories, list) or len(live_stories) != len(expected_stories):
        raise SystemExit(
            f"live oracle FAILED: Story index count repo={len(expected_stories)} live={len(live_stories) if isinstance(live_stories, list) else 'invalid'}"
        )
    expected_stories_sha = expected.get("stories_sha256")
    if expected_stories_sha and sha256_bytes(live_stories_bytes) != expected_stories_sha:
        raise SystemExit("live oracle FAILED: Story index bytes do not match the validated newsroom artifact")
    if expected.get("corpus_digest") != live_status.get("corpus_digest"):
        raise SystemExit("live oracle FAILED: live corpus digest does not match repository newsroom truth")
    if expected.get("airlock_record_count") != live_status.get("airlock_record_count"):
        raise SystemExit("live oracle FAILED: live Airlock record count does not match repository newsroom truth")
    if expected.get("translation_state") != live_status.get("translation_state"):
        raise SystemExit("live oracle FAILED: live translation state does not match repository newsroom truth")
    if expected.get("translation_counts") != live_status.get("translation_counts"):
        raise SystemExit("live oracle FAILED: live translation counts do not match repository newsroom truth")

    deployment_identity_verified = False
    if args.expected_deployment_identity:
        try:
            identity = json.loads(args.expected_deployment_identity.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"live oracle FAILED: deployment identity artifact unreadable: {exc}") from exc
        if identity.get("schema") != "fcmo-deployment-identity-v1":
            raise SystemExit("live oracle FAILED: deployment identity schema mismatch")
        live_manifest_bytes = fetch(base + "/build-manifest.json")
        checks = (
            ("build manifest", sha256_bytes(live_manifest_bytes), identity.get("build_manifest_sha256")),
            ("newsroom status", sha256_bytes(live_status_bytes), identity.get("newsroom_status_sha256")),
            ("Story index", sha256_bytes(live_stories_bytes), identity.get("stories_sha256")),
        )
        for label, actual_digest, expected_digest in checks:
            if not expected_digest or actual_digest != expected_digest:
                raise SystemExit(
                    f"live oracle FAILED: exact deployed {label} identity mismatch "
                    f"expected={expected_digest} live={actual_digest}"
                )
        if live_status.get("release_id") != identity.get("release_id"):
            raise SystemExit("live oracle FAILED: deployment artifact release_id does not match production")
        if live_status.get("corpus_digest") != identity.get("corpus_digest"):
            raise SystemExit("live oracle FAILED: deployment artifact corpus digest does not match production")
        if len(live_stories) != identity.get("story_count"):
            raise SystemExit("live oracle FAILED: deployment artifact Story count does not match production")
        deployment_identity_verified = True

    allowed_states = {
        "BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE",
        "PUBLIC_DELTA_READY",
        "NO_PUBLIC_DELTA_READY",
    }
    if live_status.get("state") not in allowed_states:
        raise SystemExit(f"live oracle FAILED: unsupported newsroom state {live_status.get('state')!r}")

    generated = live_status.get("airlock_generated_at")
    if args.require_airlock:
        if live_status.get("state") == "BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE" or not generated:
            raise SystemExit("live oracle FRESHNESS FAILED: no real Airlock-backed production release is active")

    if generated:
        age = datetime.now(timezone.utc) - parse_utc(str(generated))
        if age > timedelta(hours=args.max_airlock_age_hours):
            raise SystemExit(f"live oracle FAILED: deployed airlock heartbeat is stale ({age.total_seconds()/3600:.1f}h)")

    required_routes = (
        "/archive.html", "/search.html", "/topics.html", "/organizations.html",
        "/corrections.html", "/feeds.html", "/methodology.html", "/editorial-policy.html",
        "/automation.html", "/accessibility.html", "/status.html", "/news/",
        "/news/en/", "/news/es/", "/news/zh-hans/", "/sitemap.xml", "/news-sitemap.xml",
        "/feed.xml", "/feed.json", "/llms.txt", "/llms-full.txt", "/agent.json",
        "/assets/newsletter-responsive-polish.css",
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

    mode = "FRESHNESS" if args.require_airlock else "PRODUCTION"
    print(
        f"live newsroom {mode} OK: release={live_status['release_id']} "
        f"state={live_status['state']} stories={len(expected_stories)}; "
        f"deployment_identity={'verified' if deployment_identity_verified else 'repo-bound'}; "
        "full editorial/machine route suite + EN/ES/ZH verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
