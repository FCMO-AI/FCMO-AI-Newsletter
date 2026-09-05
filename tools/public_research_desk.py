#!/usr/bin/env python3
"""Clean-room public research desk.

The desk has access only to the already-sanitized Newsletter brief and public
Internet endpoints. It re-opens cited public sources and performs a lightweight
OpenAlex related-work search. It never receives private ARB state, so any
analysis generated downstream is reconstructable from public evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+_-]{2,}")
USER_AGENT = "FCMO-AI-Newsletter-PublicResearchDesk/1.0 (+public evidence verification)"


def load_briefs(root: Path) -> list[dict[str, Any]]:
    result = []
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        brief = value.get("brief")
        if isinstance(brief, dict):
            result.append(brief)
    return result


def signature(brief: dict[str, Any]) -> str:
    basis = {
        "id": brief.get("id"),
        "title": brief.get("title"),
        "last_verified_at": brief.get("last_verified_at"),
        "source_urls": brief.get("source_urls") or [],
        "claims": brief.get("claims") or [],
    }
    return hashlib.sha256(json.dumps(basis, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def fetch_source(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = response.read(1_250_000)
            text = data.decode("utf-8", errors="replace")
            title_match = TITLE_RE.search(text)
            return {
                "url": url,
                "final_url": response.geturl(),
                "status": getattr(response, "status", 200),
                "content_type": response.headers.get("content-type", ""),
                "title": html.unescape(re.sub(r"\s+", " ", title_match.group(1))).strip() if title_match else "",
                "reachable": True,
            }
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": exc.code, "reachable": False, "error": "HTTPError"}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"url": url, "reachable": False, "error": type(exc).__name__}


def tokens(value: str) -> set[str]:
    stop = {"the", "and", "for", "with", "from", "into", "while", "that", "this", "new", "using", "use", "model", "models", "ai"}
    return {m.group(0).lower() for m in WORD_RE.finditer(value) if m.group(0).lower() not in stop}


def title_overlap(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    return len(a & b) / max(1, len(a | b))


def openalex_related(title: str) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode({"search": title, "per-page": "5"})
    url = f"https://api.openalex.org/works?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    rows = []
    for work in payload.get("results") or []:
        work_title = str(work.get("display_name") or "")
        if title_overlap(title, work_title) < 0.16:
            continue
        primary = work.get("primary_location") or {}
        source = primary.get("source") or {}
        landing = primary.get("landing_page_url")
        doi = work.get("doi")
        rows.append({
            "openalex_id": work.get("id"),
            "title": work_title,
            "publication_year": work.get("publication_year"),
            "doi": doi,
            "url": landing or doi,
            "source": source.get("display_name"),
            "cited_by_count": work.get("cited_by_count"),
            "relationship": "title-similar public scholarly context; not treated as corroboration by count alone",
        })
    return rows[:3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-src", type=Path, default=Path("release-src"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    out = args.release_src / "data" / "public-research"
    out.mkdir(parents=True, exist_ok=True)
    updated = reused = 0
    for brief in load_briefs(args.release_src):
        rid = brief["id"]
        sig = signature(brief)
        path = out / f"{rid}.json"
        if path.exists():
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
                if previous.get("canonical_signature") == sig:
                    reused += 1
                    continue
            except Exception:
                pass

        checks = []
        related = []
        if not args.offline:
            checks = [fetch_source(url) for url in list(brief.get("source_urls") or [])[:6]]
            related = openalex_related(str(brief.get("title") or ""))
        receipt = {
            "schema": "fcmo-public-research-receipt-v1",
            "id": rid,
            "canonical_signature": sig,
            "researched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "trust_boundary": "sanitized public brief + public Internet only",
            "source_checks": checks,
            "related_public_sources": related,
            "coverage": {
                "cited_public_sources_reopened": len(checks),
                "reachable_sources": sum(1 for row in checks if row.get("reachable")),
                "scholarly_context_candidates": len(related),
                "exhaustive_web_search_claim": False,
            },
        }
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    print(f"public research desk OK; updated={updated}; reused={reused}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
