#!/usr/bin/env python3
"""Run a clean-room public-web research pass for newly ingested sanitized dossiers.

This process receives only Newsletter's public dossier plus public web search. It never
has credentials for, paths to, or identifiers from the private ARB repository. Results
are useful only if their source URLs are present in the server-side web-search evidence
returned by the provider; unsupported URLs are rejected rather than laundered into the
public newsroom.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-5"
WEB_TOOL = "web_search_20260318"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def load_new_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read ingest run receipt: {path}") from exc
    ids = value.get("newly_ingested_brief_ids") if isinstance(value, dict) else None
    return sorted({item for item in (ids or []) if isinstance(item, str) and item.startswith("FCMO-")})


def load_brief(site: Path, identifier: str) -> dict[str, Any]:
    path = site / "data" / "briefs" / f"{identifier}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "fcmo-public-brief-v1":
        raise ValueError(f"{identifier}: unsupported public brief schema")
    return value


def public_seed(document: dict[str, Any]) -> dict[str, Any]:
    """Project only already-public content into the clean-room research prompt."""
    record = document["record"]
    brief = document["brief"]
    technical = brief.get("technical") or {}
    return {
        "id": record["id"],
        "title": record.get("title"),
        "summary": record.get("summary"),
        "why_it_matters": brief.get("why_it_matters"),
        "event_at": record.get("event_at"),
        "evidence_class": brief.get("evidence_class"),
        "confidence": brief.get("confidence"),
        "importance": brief.get("importance_effective_score", brief.get("importance_score")),
        "claims": brief.get("claims") or [],
        "technical": {
            key: technical.get(key)
            for key in (
                "mechanism", "demonstrated_result", "claimed_result", "strongest_baseline",
                "regime", "reproducibility",
            )
            if technical.get(key)
        },
        "limitations": brief.get("limitations") or [],
        "contradictory_evidence": brief.get("contradictory_evidence") or [],
        "evidence_gaps": brief.get("evidence_gaps") or [],
        "source_urls": brief.get("source_urls") or [],
    }


def instructions() -> str:
    return (
        "You are the public clean-room research desk of FCMO AI Newsletter. You have NO private FCMO/ARB context and must not infer or request any. "
        "Use web search aggressively enough to verify what changed, find independent corroboration or contradiction, establish the strongest public baseline, and check whether later evidence materially changes the sanitized seed. Prefer primary papers, official documentation, independent benchmark/evaluation sources, and credible technical reporting. Avoid SEO summaries and anonymous aggregation. "
        "Do not disclose or invent implementation advice for private systems. Distinguish demonstrated facts, publisher claims and editorial inference. "
        "Return JSON only with keys: public_context_summary (string), independent_sources (array of {url,title,role}), contradictions (array of {text,url}), verification_notes (array of strings), public_analysis (array of concise generalizable strings), confidence_after_public_check (one of confirmed,strongly_supported,credible_unconfirmed,weak_signal,speculation). "
        "Every URL you return MUST be a URL actually surfaced by your web search in this request. If no independent source exists, say so in verification_notes and return an empty independent_sources array."
    )


def response_text(payload: dict[str, Any]) -> str:
    chunks = [
        item.get("text", "")
        for item in payload.get("content", [])
        if isinstance(item, dict) and item.get("type") == "text"
    ]
    if not chunks:
        raise ValueError("public research model returned no text")
    return chunks[-1].strip()


def result_urls(payload: dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    stack: list[Any] = [payload.get("content", [])]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if value.get("type") == "web_search_result" and isinstance(value.get("url"), str):
                urls.add(value["url"])
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return urls


def parse_json_text(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S | re.I)
    if fenced:
        text = fenced.group(1).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("public research model returned invalid JSON")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("public research model returned non-object JSON")
    return value


def validate_result(value: dict[str, Any], searched_urls: set[str]) -> dict[str, Any]:
    required = {
        "public_context_summary", "independent_sources", "contradictions",
        "verification_notes", "public_analysis", "confidence_after_public_check",
    }
    if set(value) != required:
        raise ValueError(f"public research output keys differ: {sorted(set(value) ^ required)}")
    if not isinstance(value["public_context_summary"], str) or not value["public_context_summary"].strip():
        raise ValueError("public research summary is empty")
    if value["confidence_after_public_check"] not in {
        "confirmed", "strongly_supported", "credible_unconfirmed", "weak_signal", "speculation"
    }:
        raise ValueError("public research confidence state is invalid")
    for key in ("independent_sources", "contradictions", "verification_notes", "public_analysis"):
        if not isinstance(value[key], list):
            raise ValueError(f"public research {key} must be an array")
    cited: set[str] = set()
    for item in value["independent_sources"]:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ("url", "title", "role")):
            raise ValueError("independent source entry is malformed")
        cited.add(item["url"])
    for item in value["contradictions"]:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError("contradiction entry is malformed")
        if item.get("url"):
            if not isinstance(item["url"], str):
                raise ValueError("contradiction URL is malformed")
            cited.add(item["url"])
    unsupported = cited - searched_urls
    if unsupported:
        raise ValueError(f"public research cited URLs not returned by web search: {sorted(unsupported)}")
    return value


def research(seed: dict[str, Any], model: str, api_key: str, max_uses: int) -> dict[str, Any]:
    prompt = instructions() + "\n\nSanitized public seed:\n" + json.dumps(seed, ensure_ascii=False, indent=2)
    body = {
        "model": model,
        "max_tokens": 8192,
        "system": instructions(),
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{
            "type": WEB_TOOL,
            "name": "web_search",
            "max_uses": max_uses,
            # Footnote: direct calling keeps the response's search-result blocks
            # observable to this validator, which is how unsupported source URLs
            # are prevented from entering the newsroom record.
            "allowed_callers": ["direct"],
        }],
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[-1000:]
        raise RuntimeError(f"public research request HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"public research request failed: {type(exc).__name__}") from exc
    searched = result_urls(payload)
    if not searched:
        raise RuntimeError("public research request returned no observable web-search results")
    return validate_result(parse_json_text(response_text(payload)), searched)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--store", type=Path, default=Path("site/data/newsroom-research"))
    parser.add_argument("--new-ids", type=Path, default=Path(".release-src.agent-run.json"))
    parser.add_argument("--model", default=os.environ.get("FCMO_PUBLIC_RESEARCH_MODEL", DEFAULT_MODEL))
    parser.add_argument("--max-searches", type=int, default=6)
    parser.add_argument("--engine", choices=("anthropic", "stub"), default="anthropic")
    args = parser.parse_args()
    ids = load_new_ids(args.new_ids)
    if not ids:
        print(json.dumps({"researched": 0, "reason": "NO_NEW_PUBLIC_DOSSIERS"}, sort_keys=True))
        return 0
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if args.engine == "anthropic" and not api_key.strip():
        raise SystemExit("ANTHROPIC_API_KEY is required for clean-room public web research")
    args.store.mkdir(parents=True, exist_ok=True)
    researched = 0
    for identifier in ids:
        document = load_brief(args.site, identifier)
        seed = public_seed(document)
        if args.engine == "stub":
            result = {
                "public_context_summary": "Stub public research context.",
                "independent_sources": [],
                "contradictions": [],
                "verification_notes": ["Stub mode performs no web search."],
                "public_analysis": [],
                "confidence_after_public_check": seed.get("confidence") or "credible_unconfirmed",
            }
        else:
            result = research(seed, args.model, api_key, args.max_searches)
        record = {
            "schema": "fcmo-public-clean-room-research-v1",
            "id": identifier,
            "seed_digest_sha256": digest(seed),
            "research_model": args.model if args.engine == "anthropic" else "stub",
            "web_search_tool": WEB_TOOL if args.engine == "anthropic" else None,
            **result,
        }
        (args.store / f"{identifier}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        researched += 1
    index = []
    for path in sorted(args.store.glob("FCMO-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        index.append({
            "id": value["id"],
            "seed_digest_sha256": value["seed_digest_sha256"],
            "confidence_after_public_check": value["confidence_after_public_check"],
            "independent_source_count": len(value.get("independent_sources") or []),
            "contradiction_count": len(value.get("contradictions") or []),
        })
    (args.store / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"researched": researched, "ids": ids}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
