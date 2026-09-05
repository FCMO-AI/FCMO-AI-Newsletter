#!/usr/bin/env python3
"""Independent machine-language editorial review for curated locale packs.

Translation and review are deliberately separate operations. The translator
produces the candidate locale artifact; this reviewer compares the committed
candidate against canonical English and rejects any Critical/Major error in
accuracy, claim strength, terminology, numbers, identifiers or fluency.

This remains machine-curated, not human-reviewed. A successful receipt records
what was reviewed and by which model so the public contract stays truthful.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.translate_records import _read_canonical, _source_overlay, _preserves_numbers

ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-5"
LOCALES = ("es-419", "zh-Hans")
FCMO_ID = re.compile(r"FCMO-[0-9A-F]{12}")
URL_RE = re.compile(r"https?://[^\s\]\[(){}<>\"']+")


class ReviewError(Exception):
    pass


def sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def load_locale(i18n: Path, locale: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((i18n / locale).glob("part-*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        rows = value.get("records")
        if not isinstance(rows, dict):
            raise ReviewError(f"{path}: records object missing")
        overlap = set(result) & set(rows)
        if overlap:
            raise ReviewError(f"{locale}: duplicate translated IDs {sorted(overlap)}")
        result.update(rows)
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": "fcmo-machine-language-review-v1", "reviews": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "fcmo-machine-language-review-v1":
        raise ReviewError("unsupported localization review manifest schema")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    os.replace(tmp, path)


def deterministic_checks(record_id: str, source: dict[str, Any], translated: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    overlay = _source_overlay(source)
    if not _preserves_numbers(overlay, translated):
        errors.append("numeric tokens differ from canonical prose")
    source_ids = sorted(set(FCMO_ID.findall(json.dumps(overlay, ensure_ascii=False))))
    translated_ids = sorted(set(FCMO_ID.findall(json.dumps(translated, ensure_ascii=False))))
    if source_ids != translated_ids:
        errors.append("FCMO identifiers differ from canonical prose")
    source_urls = sorted(set(URL_RE.findall(json.dumps(overlay, ensure_ascii=False))))
    translated_urls = sorted(set(URL_RE.findall(json.dumps(translated, ensure_ascii=False))))
    if source_urls != translated_urls:
        errors.append("URLs differ from canonical prose")
    # Footnote: unchanged source prose is allowed only when it is genuinely an
    # identifier/proper-name-like fragment. The existing localization gate owns
    # exhaustive prose-completeness checks; this reviewer adds cross-language QA.
    if not isinstance(translated, dict) or not translated:
        errors.append(f"{record_id}: translated overlay is empty")
    return errors


def review_prompt(locale: str, payload: dict[str, Any]) -> str:
    language = "Latin American Spanish" if locale == "es-419" else "Simplified Chinese"
    return (
        "You are the independent language editor for an evidence-first technical newspaper. "
        f"Review the candidate {language} translation against canonical English. "
        "Use an MQM-style severity model. A Critical error changes or reverses factual meaning, "
        "evidence strength, uncertainty, safety/legal meaning, a number, identity, benchmark, date, URL, or claim label. "
        "A Major error materially mistranslates meaning, terminology, scope, causal relationship, or makes the prose misleading. "
        "Minor covers non-material fluency/style issues. Do not reward literal wording; natural target-language journalism is preferred. "
        "Do not strengthen CLAIMED/INFERRED/SPECULATIVE statements into facts. Preserve names, model/version identifiers and figures exactly. "
        "Return JSON only as {\"records\": {id: {\"critical\": int, \"major\": int, \"minor\": int, \"notes\": [str]}}}. "
        "Every supplied ID must appear exactly once and no extra IDs may appear.\n\n" +
        json.dumps(payload, ensure_ascii=False, indent=2)
    )


def parse_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S | re.I)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ReviewError("reviewer returned invalid JSON")
        value = json.loads(cleaned[start:end + 1])
    rows = value.get("records") if isinstance(value, dict) else None
    if not isinstance(rows, dict):
        raise ReviewError("reviewer returned no records object")
    return rows


def anthropic_review(locale: str, payload: dict[str, Any], model: str, api_key: str) -> dict[str, Any]:
    prompt = review_prompt(locale, payload)
    body = json.dumps({
        "model": model,
        "max_tokens": 12000,
        "system": "Act only as an independent translation quality reviewer. Return JSON only.",
        "messages": [{"role": "user", "content": prompt}],
    }, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ReviewError(f"translation reviewer HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ReviewError(f"translation reviewer failed: {type(exc).__name__}") from exc
    content = result.get("content")
    text = "".join(item.get("text", "") for item in content or [] if isinstance(item, dict))
    if not text.strip():
        raise ReviewError("translation reviewer returned no text")
    return parse_response(text)


def validate_review(expected: set[str], rows: dict[str, Any]) -> None:
    if set(rows) != expected:
        raise ReviewError(f"reviewer ID mismatch: missing={sorted(expected-set(rows))} extra={sorted(set(rows)-expected)}")
    for rid, row in rows.items():
        if not isinstance(row, dict):
            raise ReviewError(f"{rid}: malformed review")
        for key in ("critical", "major", "minor"):
            if not isinstance(row.get(key), int) or row[key] < 0:
                raise ReviewError(f"{rid}: invalid {key} count")
        if row["critical"] or row["major"]:
            notes = "; ".join(str(x) for x in (row.get("notes") or [])[:4])
            raise ReviewError(
                f"{rid}: localization rejected: critical={row['critical']} major={row['major']} {notes}".strip()
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--manifest", type=Path, default=Path("site/data/i18n/review-manifest.json"))
    parser.add_argument("--model", default=os.environ.get("FCMO_TRANSLATION_REVIEW_MODEL", DEFAULT_MODEL))
    parser.add_argument("--deterministic-only", action="store_true", help="run structural cross-language checks without provider review; CI/unit-test aid only")
    args = parser.parse_args(argv)

    try:
        canonical, _ = _read_canonical(args.site)
        manifest = load_manifest(args.manifest)
        previous = manifest.get("reviews") or {}
        next_reviews = dict(previous)
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        reviewed = reused = 0

        for locale in LOCALES:
            translations = load_locale(args.i18n_dir, locale)
            if set(translations) != set(canonical):
                raise ReviewError(
                    f"{locale}: curated IDs do not match canonical: missing={sorted(set(canonical)-set(translations))} "
                    f"extra={sorted(set(translations)-set(canonical))}"
                )
            pending: dict[str, Any] = {}
            digests: dict[str, tuple[str, str]] = {}
            for rid, source in canonical.items():
                translated = translations[rid]
                errors = deterministic_checks(rid, source, translated)
                if errors:
                    raise ReviewError(f"{locale}/{rid}: " + "; ".join(errors))
                source_digest = sha(_source_overlay(source))
                translation_digest = sha(translated)
                digests[rid] = (source_digest, translation_digest)
                key = f"{locale}:{rid}"
                prior = previous.get(key) or {}
                if (
                    prior.get("source_digest") == source_digest
                    and prior.get("translation_digest") == translation_digest
                    and prior.get("result") == "PASS"
                ):
                    reused += 1
                    continue
                pending[rid] = {"source": _source_overlay(source), "translation": translated}

            if pending:
                if args.deterministic_only:
                    rows = {rid: {"critical": 0, "major": 0, "minor": 0, "notes": ["deterministic-only test mode"]} for rid in pending}
                    review_model = "deterministic-only"
                else:
                    if not api_key:
                        raise ReviewError("ANTHROPIC_API_KEY is required for independent localization review")
                    rows = anthropic_review(locale, pending, args.model, api_key)
                    review_model = args.model
                validate_review(set(pending), rows)
                now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                for rid, row in rows.items():
                    source_digest, translation_digest = digests[rid]
                    next_reviews[f"{locale}:{rid}"] = {
                        "result": "PASS",
                        "source_digest": source_digest,
                        "translation_digest": translation_digest,
                        "critical": row["critical"],
                        "major": row["major"],
                        "minor": row["minor"],
                        "notes": row.get("notes") or [],
                        "reviewed_at": now,
                        "reviewer": review_model,
                        "human_reviewed": False,
                    }
                    reviewed += 1

        valid_keys = {f"{locale}:{rid}" for locale in LOCALES for rid in canonical}
        next_reviews = {key: value for key, value in next_reviews.items() if key in valid_keys}
        atomic_json(args.manifest, {
            "schema": "fcmo-machine-language-review-v1",
            "canonical_locale": "en",
            "review_method": "independent model editorial review + deterministic invariants",
            "human_reviewed": False,
            "reviews": next_reviews,
        })
        print(f"localization review PASS; reviewed={reviewed}; reused={reused}; pairs={len(next_reviews)}")
        return 0
    except (ReviewError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"localization review FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
