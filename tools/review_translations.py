#!/usr/bin/env python3
"""Second-pass editorial QA for curated Spanish and Simplified Chinese records.

Translation generation and translation approval are separate operations. The reviewer
receives canonical English plus the committed candidate translation, but never the
translator's chain-of-thought or hidden context. A changed source/translation digest
invalidates its previous review automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Footnote: like the first-pass translator, this editor is invoked directly by path in
# Actions. Add the repository root explicitly so `tools.*` imports do not depend on how
# Python happened to populate sys.path in a test runner.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.translate_records import (
    ANTHROPIC_VERSION,
    ENDPOINT,
    _load_locale,
    _read_canonical,
    _source_overlay,
)

DEFAULT_MODEL = "claude-opus-5"
LOCALES = ("es-419", "zh-Hans")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def merged_locale(i18n_dir: Path, locale: str) -> dict[str, dict[str, Any]]:
    parts, _ids = _load_locale(i18n_dir, locale)
    rows: dict[str, dict[str, Any]] = {}
    for _path, document in parts:
        rows.update(document["records"])
    return rows


def instructions(locale: str) -> str:
    target = "neutral Latin American Spanish" if locale == "es-419" else "Simplified Chinese"
    return (
        f"You are the independent publication editor for {target}. Review translation fidelity, not style preference. "
        "A PASS requires: same factual meaning and uncertainty strength as canonical English; no stronger claim; no "
        "omission or hallucination; exact preservation of numbers, percentages, dates, model/version names, IDs and URLs; "
        "natural technical-journalistic language; and faithful distinctions among demonstrated, claimed, inferred, disputed "
        "and speculative content. Return JSON only in the exact requested review object. Any material evidence-strength "
        "shift is CRITICAL. Any factual mistranslation/omission is MAJOR."
    )


def call_reviewer(batch: dict[str, Any], locale: str, model: str, api_key: str) -> dict[str, Any]:
    schema_hint = {
        "reviews": {
            "FCMO-EXAMPLE": {
                "decision": "PASS",
                "errors": [],
                "mqm_major": 0,
                "mqm_critical": 0,
            }
        }
    }
    prompt = (
        instructions(locale)
        + "\nReturn JSON matching this shape (replace the example ID with every supplied record ID):\n"
        + json.dumps(schema_hint, ensure_ascii=False)
        + "\n\nReview batch:\n"
        + json.dumps(batch, ensure_ascii=False, indent=2)
    )
    body = {
        "model": model,
        "max_tokens": 12000,
        "system": instructions(locale),
        "messages": [{"role": "user", "content": prompt}],
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
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"translation reviewer HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"translation reviewer network failure: {type(exc).__name__}") from exc
    text = "".join(
        item.get("text", "") for item in payload.get("content", []) if isinstance(item, dict)
    ).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("translation reviewer returned invalid JSON") from exc
    reviews = parsed.get("reviews") if isinstance(parsed, dict) else None
    if not isinstance(reviews, dict):
        raise RuntimeError("translation reviewer returned no reviews object")
    return reviews


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--ledger", type=Path, default=Path("site/data/i18n/review-ledger.json"))
    # Footnote: an unset Actions variable is injected as an empty environment string;
    # ``or DEFAULT_MODEL`` preserves the actual default instead of sending model="".
    parser.add_argument("--model", default=os.environ.get("FCMO_TRANSLATION_REVIEW_MODEL") or DEFAULT_MODEL)
    parser.add_argument("--engine", choices=("anthropic", "stub"), default="anthropic")
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    canonical, _index = _read_canonical(args.site)
    ledger = {"schema_version": 1, "reviews": {}}
    if args.ledger.is_file():
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        if ledger.get("schema_version") != 1 or not isinstance(ledger.get("reviews"), dict):
            raise SystemExit("invalid translation review ledger")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if args.engine == "anthropic" and not api_key.strip():
        raise SystemExit("ANTHROPIC_API_KEY is required for independent translation review")

    pending: dict[str, list[tuple[str, dict[str, Any], dict[str, Any], str, str]]] = {}
    for locale in LOCALES:
        translated = merged_locale(args.i18n_dir, locale)
        missing = sorted(set(canonical) - set(translated))
        if missing:
            raise SystemExit(f"{locale}: missing translated records before review: {missing}")
        queue = []
        for record_id in sorted(canonical):
            source = _source_overlay(canonical[record_id])
            candidate = translated[record_id]
            source_digest = digest(source)
            translation_digest = digest(candidate)
            key = f"{locale}:{record_id}"
            old = ledger["reviews"].get(key) or {}
            if (
                old.get("decision") == "PASS"
                and old.get("source_digest") == source_digest
                and old.get("translation_digest") == translation_digest
            ):
                continue
            queue.append((record_id, source, candidate, source_digest, translation_digest))
        pending[locale] = queue

    new_entries: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for locale, queue in pending.items():
        for start in range(0, len(queue), max(1, args.batch_size)):
            chunk = queue[start : start + max(1, args.batch_size)]
            payload = {
                record_id: {"canonical": source, "translation": candidate}
                for record_id, source, candidate, _sd, _td in chunk
            }
            if args.engine == "stub":
                reviews = {
                    record_id: {"decision": "PASS", "errors": [], "mqm_major": 0, "mqm_critical": 0}
                    for record_id, *_rest in chunk
                }
            else:
                reviews = call_reviewer(payload, locale, args.model, api_key)
            expected = {record_id for record_id, *_rest in chunk}
            if set(reviews) != expected:
                raise SystemExit(f"{locale}: reviewer IDs do not match batch")
            for record_id, _source, _candidate, source_digest, translation_digest in chunk:
                review = reviews[record_id]
                decision = review.get("decision")
                major = int(review.get("mqm_major") or 0)
                critical = int(review.get("mqm_critical") or 0)
                if decision != "PASS" or major or critical:
                    failures.append(
                        f"{locale}:{record_id}: decision={decision} major={major} critical={critical} errors={review.get('errors') or []}"
                    )
                    continue
                new_entries[f"{locale}:{record_id}"] = {
                    "decision": "PASS",
                    "source_digest": source_digest,
                    "translation_digest": translation_digest,
                    "review_model": args.model if args.engine == "anthropic" else "stub",
                    "mqm_major": 0,
                    "mqm_critical": 0,
                }
    if failures:
        print("translation editorial review FAILED")
        for failure in failures:
            print("-", failure)
        return 1
    ledger["reviews"].update(new_entries)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed": len(new_entries), "cached_passes": 2 * len(canonical) - len(new_entries)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
