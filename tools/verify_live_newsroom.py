#!/usr/bin/env python3
"""Serving oracle for the live FCMO AI Newsletter: availability and identity.

Serving is one of three separate truths (contracts/README.md, "Health state").
This oracle answers only "is the site up, and does it serve the release it
claims?". It never looks at freshness: a DELAYED newsroom that serves its last
known good release is up. Freshness lives in ``tools/wire_status.py classify``
and ``tools/editorial_freshness.py check``.

* Availability: the root and the reader route suite answer 200.
* Identity: the live ``data/newsroom-status.json`` and ``data/stories.json``
  match the repository (release id, corpus digest, Story bytes), or, with
  ``--expected-deployment-identity``, the exact bytes of the deployed candidate.
  ``--paper`` uses the current v2 deployment receipt and SSG routes. Hourly
  health proves the served receipt's critical bytes independently of newer,
  unpublished checkout state; Pages supplies an expected artifact to pin a deploy.

GitHub Pages sits behind a CDN that caches for up to 10 minutes, so a new
deployment is not visible at once. Identity is therefore polled with a
``?v=<sha>-<n>`` cache-buster for up to ``--identity-timeout-s`` (15 minutes)
before it is declared a mismatch.

The first stdout line is ``SERVING OK ...`` (exit 0) or
``SERVING FAILED <CODE> ...`` (exit 1) with CODE one of UNREACHABLE,
ROUTES_FAILED, IDENTITY_MISMATCH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from tools import verify_live_front_page
except ImportError:
    import verify_live_front_page  # type: ignore

DEFAULT_BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
USER_AGENT = "FCMO-Newsroom-Live-Oracle/2.0"
FETCH_PAUSE_S = float(os.environ.get("FCMO_LIVE_FETCH_PAUSE_S", "5"))
AVAILABILITY_ROUTES = (
    "/archive.html", "/search.html", "/topics.html", "/organizations.html",
    "/corrections.html", "/feeds.html", "/methodology.html", "/editorial-policy.html",
    "/automation.html", "/accessibility.html", "/status.html", "/news/",
    "/news/en/", "/news/es/", "/news/zh-hans/", "/sitemap.xml", "/news-sitemap.xml",
    "/feed.xml", "/feed.json", "/llms.txt", "/llms-full.txt", "/agent.json",
    "/assets/newsletter-responsive-polish.css",
)
LEGACY_STATES = {"BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE", "PUBLIC_DELTA_READY", "NO_PUBLIC_DELTA_READY"}
PAPER_ROUTES = (
    "/", "/es/", "/zh/", "/diario/", "/es/diario/", "/zh/diario/",
    "/archive/", "/search/", "/corrections/", "/feeds/", "/method/",
    "/status/", "/es/status/", "/zh/status/", "/status.json", "/sitemap.xml",
    "/feed.xml", "/feed.json", "/llms.txt", "/agent.json", "/assets/css/paper.css",
)


class ServingFailure(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


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
                time.sleep(FETCH_PAUSE_S)
    raise RuntimeError(f"live fetch failed for {url}: {last}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"live {label} is not valid JSON: {exc}") from exc


def busted(url: str, token: str) -> str:
    return f"{url}{'&' if '?' in url else '?'}v={token}"


def identity_problem(
    base: str,
    token: str,
    expected: dict[str, Any],
    expected_stories: list[Any],
    identity: dict[str, Any] | None,
    get: Callable[[str], bytes],
) -> tuple[str | None, dict[str, Any]]:
    """None when the live site serves the expected identity, else a reason."""
    status_bytes = get(busted(base + "/data/newsroom-status.json", token))
    try:
        live_status = json.loads(status_bytes.decode("utf-8"))
    except Exception:
        return "live newsroom status is not valid JSON", {}
    stories_bytes = get(busted(base + "/data/stories.json", token))
    try:
        live_stories = json.loads(stories_bytes.decode("utf-8"))
    except Exception:
        return "live Story index is not valid JSON", live_status
    if not isinstance(live_stories, list):
        return "live Story index is not a list", live_status
    if identity is not None:
        manifest_bytes = get(busted(base + "/build-manifest.json", token))
        for label, actual, wanted in (
            ("build manifest", sha256_bytes(manifest_bytes), identity.get("build_manifest_sha256")),
            ("newsroom status", sha256_bytes(status_bytes), identity.get("newsroom_status_sha256")),
            ("Story index", sha256_bytes(stories_bytes), identity.get("stories_sha256")),
        ):
            if not wanted or actual != wanted:
                return f"deployed {label} bytes differ (expected {str(wanted)[:12]} live {actual[:12]})", live_status
        if live_status.get("release_id") != identity.get("release_id"):
            return "deployed release_id differs", live_status
        if live_status.get("corpus_digest") != identity.get("corpus_digest"):
            return "deployed corpus digest differs", live_status
        if len(live_stories) != identity.get("story_count"):
            return "deployed Story count differs", live_status
        return None, live_status
    if live_status.get("release_id") != expected.get("release_id"):
        return f"release repo={expected.get('release_id')} live={live_status.get('release_id')}", live_status
    if live_status.get("corpus_digest") != expected.get("corpus_digest"):
        return "corpus digest differs from the repository", live_status
    if len(live_stories) != len(expected_stories):
        return f"Story count repo={len(expected_stories)} live={len(live_stories)}", live_status
    wanted_sha = expected.get("stories_sha256")
    if wanted_sha and sha256_bytes(stories_bytes) != wanted_sha:
        return "Story index bytes differ from the repository", live_status
    return None, live_status


def poll_identity(
    base: str,
    token: str,
    expected: dict[str, Any],
    expected_stories: list[Any],
    identity: dict[str, Any] | None,
    timeout_s: float,
    interval_s: float,
    get: Callable[[str], bytes] = fetch,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, dict[str, Any]]:
    """Poll until the CDN serves the expected identity; return attempts used."""
    deadline = clock() + max(0.0, timeout_s)
    attempt = 0
    while True:
        attempt += 1
        try:
            problem, live_status = identity_problem(base, f"{token}-{attempt}", expected, expected_stories, identity, get)
        except RuntimeError as exc:
            problem, live_status = str(exc), {}
        if problem is None:
            return attempt, live_status
        if clock() + interval_s > deadline:
            raise ServingFailure("IDENTITY_MISMATCH", f"{problem} after {attempt} polls")
        print(f"identity not served yet (poll {attempt}): {problem}", file=sys.stderr)
        sleep(interval_s)


def route_contracts(base: str, root: str, expected_stories: list[Any]) -> None:
    """Reader route markers of the current site (full post-deploy mode only)."""
    if "data-fcmo-wire-link" in root:
        responsive_css = fetch(base + "/assets/newsletter-responsive-polish.css").decode("utf-8", errors="replace")
        compact_css = re.sub(r"\s+", "", responsive_css)
        if "[data-fcmo-wire-link]{display:none!important}" not in compact_css:
            raise ServingFailure("ROUTES_FAILED", "retired reader-facing FCMO WIRE control is not suppressed")
    search = fetch(base + "/search.html").decode("utf-8", errors="replace")
    if "data-search-root" not in search or "editorial-frontends.js" not in search:
        raise ServingFailure("ROUTES_FAILED", "search route is not the native local-search frontend")
    topics = fetch(base + "/topics.html").decode("utf-8", errors="replace")
    organizations = fetch(base + "/organizations.html").decode("utf-8", errors="replace")
    if "facet-row" not in topics or "facet-row" not in organizations:
        raise ServingFailure("ROUTES_FAILED", "topic/organization discovery routes are still shells")
    gateway = fetch(base + "/news/").decode("utf-8", errors="replace")
    if "Canonical semantic edition" not in gateway or "简体中文" not in gateway:
        raise ServingFailure("ROUTES_FAILED", "/news/ is not the three-edition gateway")
    latest_id = expected_stories[0].get("research_id") if isinstance(expected_stories[0], dict) else None
    if not latest_id:
        raise ServingFailure("ROUTES_FAILED", "latest Story lacks research_id")
    for locale in ("en", "es", "zh-hans"):
        article = fetch(f"{base}/news/{locale}/{latest_id}.html").decode("utf-8", errors="replace")
        if '"@type": "NewsArticle"' not in article and '"@type":"NewsArticle"' not in article:
            raise ServingFailure("ROUTES_FAILED", f"{locale} latest Story lacks NewsArticle structured data")
        if "hreflang=" not in article or "FCMO AI Research Desk" not in article:
            raise ServingFailure("ROUTES_FAILED", f"{locale} latest Story lacks multilingual/byline contract")


def write_signal(path: Path | None, status: str, code: str, detail: str, metrics: dict[str, Any]) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": status, "code": code, "detail": detail[:300], "metrics": metrics}, indent=2) + "\n", encoding="utf-8")


def serve_paper(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    """Prove the served LKG; Pages can additionally pin a candidate artifact.

    Checkout corpus/receipt changes may be newer than the deployed edition.
    Critical hashes bind all three fronts, lead routes and Story bytes without
    treating unpublished checkout changes as a serving failure.
    """
    base = args.base_url.rstrip("/")
    try:
        if args.expected_deployment_identity:
            identity = json.loads(args.expected_deployment_identity.read_text(encoding="utf-8"))
        else:
            identity = load_json_bytes(fetch(busted(base + "/deployment-identity.json", str(time.time_ns()))), "deployment identity")
        verify_live_front_page.validate_identity(identity)
        verify_live_front_page.wait_for_candidate(
            base, identity, args.identity_timeout_s, args.poll_interval_s,
            get=lambda url, nonce: fetch(busted(url, nonce)),
        )
    except (OSError, ValueError, RuntimeError) as exc:
        raise ServingFailure("IDENTITY_MISMATCH", str(exc)) from exc
    for route in PAPER_ROUTES:
        try:
            fetch(busted(base + route, str(time.time_ns())))
        except RuntimeError as exc:
            raise ServingFailure("ROUTES_FAILED", str(exc)) from exc
    metrics = {"routes_checked": len(PAPER_ROUTES), "critical_files_checked": len(identity["critical_files"]),
               "candidate_id": identity["candidate_id"], "source_commit": identity["source_commit"]}
    return f"release={identity['release_id']} stories={identity['story_count']} identity=exact candidate={identity['candidate_id']}", metrics


def serve(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    if args.paper:
        return serve_paper(args)
    base = args.base_url.rstrip("/")
    try:
        root = fetch(base + "/").decode("utf-8", errors="replace")
    except RuntimeError as exc:
        raise ServingFailure("UNREACHABLE", str(exc)) from exc
    if "FCMO AI Newsletter" not in root:
        raise ServingFailure("UNREACHABLE", "production root does not identify the publication")

    for path in AVAILABILITY_ROUTES:
        try:
            fetch(base + path)
        except RuntimeError as exc:
            raise ServingFailure("ROUTES_FAILED", str(exc)) from exc
    metrics: dict[str, Any] = {"routes_checked": len(AVAILABILITY_ROUTES) + 1}

    if not args.status.is_file():
        if args.allow_unbootstrapped:
            return "BASELINE root is live; newsroom status not bootstrapped in this commit", metrics
        raise ServingFailure("IDENTITY_MISMATCH", "repository newsroom status is absent")
    expected = json.loads(args.status.read_text(encoding="utf-8"))
    expected_stories = json.loads(args.stories.read_text(encoding="utf-8"))
    if not isinstance(expected_stories, list) or not expected_stories:
        raise ServingFailure("IDENTITY_MISMATCH", "repository Story layer is empty")

    identity = None
    if args.expected_deployment_identity:
        try:
            identity = json.loads(args.expected_deployment_identity.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ServingFailure("IDENTITY_MISMATCH", f"deployment identity artifact unreadable: {exc}") from exc
        if identity.get("schema") != "fcmo-deployment-identity-v1":
            raise ServingFailure("IDENTITY_MISMATCH", "deployment identity schema mismatch")
    token = re.sub(r"[^0-9A-Za-z]", "", str(
        (identity or {}).get("source_commit") or os.environ.get("GITHUB_SHA") or expected.get("release_id") or "live"
    ))[:40] or "live"
    polls, live_status = poll_identity(
        base, token, expected, expected_stories, identity,
        args.identity_timeout_s, args.poll_interval_s,
    )
    metrics["identity_polls"] = polls
    if not args.serving_only:
        if live_status.get("state") not in LEGACY_STATES:
            raise ServingFailure("IDENTITY_MISMATCH", f"unsupported newsroom state {live_status.get('state')!r}")
        route_contracts(base, root, expected_stories)
    kind = "exact" if identity is not None else "release"
    return (
        f"release={live_status.get('release_id')} stories={len(expected_stories)} "
        f"routes={metrics['routes_checked']} identity={kind} polls={polls}"
    ), metrics


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--status", type=Path, default=Path("site/data/newsroom-status.json"))
    parser.add_argument("--stories", type=Path, default=Path("site/data/stories.json"))
    parser.add_argument("--serving-only", action="store_true",
                        help="availability + identity only (the health serving signal)")
    parser.add_argument("--paper", action="store_true", help="verify the deployed paper SSG and its v2 identity receipt")
    parser.add_argument("--allow-unbootstrapped", action="store_true")
    parser.add_argument("--expected-deployment-identity", type=Path)
    parser.add_argument("--identity-timeout-s", type=float, default=900.0,
                        help="how long to wait for the CDN to serve the expected identity (default 15 min)")
    parser.add_argument("--poll-interval-s", type=float, default=30.0)
    parser.add_argument("--signal-out", type=Path, help="write the health-state serving signal here")
    # Retired: freshness is not a serving property. Accepted so old callers keep working.
    parser.add_argument("--require-airlock", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--max-airlock-age-hours", type=int, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.require_airlock or args.max_airlock_age_hours is not None:
        print("note: airlock-age flags are ignored; freshness is measured by the wire status, not by serving", file=sys.stderr)
    try:
        summary, metrics = serve(args)
    except ServingFailure as exc:
        print(f"SERVING FAILED {exc.code} {exc}")
        write_signal(args.signal_out, "RED", exc.code, str(exc), {})
        return 1
    except (OSError, ValueError) as exc:
        print(f"SERVING FAILED UNREACHABLE {exc}")
        write_signal(args.signal_out, "RED", "UNREACHABLE", str(exc), {})
        return 1
    print(f"SERVING OK {summary}")
    boundary = "deployed candidate." if args.expected_deployment_identity else (
        "served deployment receipt." if args.paper else "repository release.")
    write_signal(args.signal_out, "GREEN", "OK", "All routes 200 and live identity matches the " + boundary, metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
