#!/usr/bin/env python3
"""Fail closed unless every public story has structurally sound ES and ZH editions.

This is deliberately a deterministic integrity gate, not a machine-translation judge.
ARB's publication agent owns editorial equivalence; Newsletter proves coverage and
high-value invariants without any external model, API key or network request.

Historical locale packs are validated truthfully under a structural compatibility
tier. Any story written or refreshed by the modern ARB airlock lives in
``part-airlock.json`` and receives the stricter numeric/ID/URL preservation tier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from tools.reconcile_locale_overlays import canonical_records
except ImportError:  # direct script execution from tools/
    from reconcile_locale_overlays import canonical_records

LOCALES = ("es-419", "zh-Hans")
AIRLOCK_PART = "part-airlock.json"
NUM = re.compile(r"(?<![A-Za-z])[-+]?\d[\d,.]*(?:%|x|×|[KMBT])?", re.I)
FCMO_ID = re.compile(r"\bFCMO-[0-9A-F]{12}\b")
URL = re.compile(r"https?://[^\s\]\[)<>'\"]+")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
PROSE_KEYS = {
    "title", "summary", "why_it_matters", "why", "importance_rationale",
    "limitations", "contradictory_evidence", "claims", "evidence_gaps",
    "relationships", "technical",
}


def stable_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_locale(root: Path, locale: str) -> tuple[dict[str, dict[str, Any]], set[str]]:
    result: dict[str, dict[str, Any]] = {}
    strict: set[str] = set()
    for path in sorted((root / locale).glob("part-*.json")):
        rows = json.loads(path.read_text(encoding="utf-8")).get("records")
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: records object missing")
        overlap = set(result) & set(rows)
        if overlap:
            raise SystemExit(f"{path}: duplicate locale ids {sorted(overlap)}")
        result.update(rows)
        if path.name == AIRLOCK_PART:
            strict.update(rows)
    return result, strict


def strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def assert_shape(source: Any, translated: Any, path: str, errors: list[str]) -> None:
    if isinstance(translated, dict):
        if not isinstance(source, dict):
            errors.append(f"{path}: overlay object does not match canonical shape")
            return
        extra = set(translated) - set(source)
        if extra:
            errors.append(f"{path}: non-canonical keys {sorted(extra)}")
        for key, value in translated.items():
            if key in source:
                assert_shape(source[key], value, f"{path}.{key}", errors)
    elif isinstance(translated, list):
        if not isinstance(source, list) or len(translated) != len(source):
            errors.append(f"{path}: list cardinality differs from canonical source")
            return
        for i, value in enumerate(translated):
            assert_shape(source[i], value, f"{path}[{i}]", errors)
    elif isinstance(source, (dict, list)):
        errors.append(f"{path}: scalar overlay replaced canonical structure")


def source_for_overlay(source: Any, overlay: Any) -> Any:
    """Return the exact canonical paths represented by a sparse locale overlay."""
    if isinstance(source, dict) and isinstance(overlay, dict):
        return {
            key: source_for_overlay(source[key], value)
            for key, value in overlay.items()
            if key in source
        }
    if isinstance(source, list) and isinstance(overlay, list):
        return [source_for_overlay(s, t) for s, t in zip(source, overlay)]
    return source


def translated_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in sorted(PROSE_KEYS) if key in row}


def check_common(source: dict[str, Any], overlay: dict[str, Any], locale: str, rid: str, errors: list[str]) -> tuple[Any, str]:
    assert_shape(source, overlay, f"{locale}:{rid}", errors)
    matched_source = source_for_overlay(source, overlay)
    merged_text = "\n".join(strings(overlay))
    if not merged_text.strip():
        errors.append(f"{locale}:{rid}: empty locale overlay")
        return matched_source, merged_text
    title = str(overlay.get("title") or "").strip()
    summary = str(overlay.get("summary") or "").strip()
    why = str(overlay.get("why_it_matters") or overlay.get("why") or "").strip()
    if not title or not summary or not why:
        errors.append(f"{locale}:{rid}: title/summary/why_it_matters must be editorially complete")
    if locale == "zh-Hans" and len(merged_text) >= 120 and len(CJK.findall(merged_text)) < 20:
        errors.append(f"{locale}:{rid}: long edition lacks expected Han-script content")
    if stable_digest(matched_source) == stable_digest(overlay):
        errors.append(f"{locale}:{rid}: edition is unchanged from canonical English")
    return matched_source, merged_text


def check_strict(source: dict[str, Any], overlay: dict[str, Any], locale: str, rid: str, errors: list[str]) -> None:
    matched_source, merged_text = check_common(source, overlay, locale, rid, errors)
    source_text = "\n".join(strings(matched_source))
    for regex, label in ((NUM, "number"), (FCMO_ID, "FCMO id"), (URL, "URL")):
        src = sorted(regex.findall(source_text))
        dst = sorted(regex.findall(merged_text))
        # Footnote: strict invariants apply only to modern ARB-authored material
        # that crossed the native-edition airlock. This keeps benchmark/version
        # drift fail-closed without retroactively rewriting the validation history
        # of the 2026 bootstrap translations.
        if src != dst:
            errors.append(f"{locale}:{rid}: {label} tokens changed: source={src} locale={dst}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--receipt", type=Path, default=Path("site/data/i18n/integrity-manifest.json"))
    args = parser.parse_args(argv)

    canonical = canonical_records(args.site)
    expected = set(canonical)
    errors: list[str] = []
    receipt_records: dict[str, Any] = {}
    strict_pairs = 0
    historical_pairs = 0
    for locale in LOCALES:
        rows, strict_ids = load_locale(args.i18n_dir, locale)
        missing = expected - set(rows)
        stale = set(rows) - expected
        if missing:
            errors.append(f"{locale}: missing canonical ids {sorted(missing)}")
        if stale:
            errors.append(f"{locale}: stale/non-canonical ids {sorted(stale)}")
        for rid in sorted(expected & set(rows)):
            overlay = rows[rid]
            if not isinstance(overlay, dict):
                errors.append(f"{locale}:{rid}: overlay must be object")
                continue
            if rid in strict_ids:
                check_strict(canonical[rid], overlay, locale, rid, errors)
                tier = "strict_airlock"
                strict_pairs += 1
            else:
                check_common(canonical[rid], overlay, locale, rid, errors)
                tier = "historical_structural"
                historical_pairs += 1
            receipt_records.setdefault(rid, {})[locale] = {
                "canonical_digest": stable_digest(translated_projection(canonical[rid])),
                "locale_digest": stable_digest(overlay),
                "validation_tier": tier,
            }

    if errors:
        raise SystemExit("localization integrity FAILED:\n" + "\n".join(f"- {x}" for x in errors))
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "fcmo-locale-integrity-v2",
        "canonical_locale": "en",
        "required_locales": list(LOCALES),
        "editorial_owner": "ARB publication agent for modern airlocked editions; historical packs preserved as published",
        "human_reviewed": False,
        "network_translation": False,
        "strict_airlock_pairs": strict_pairs,
        "historical_structural_pairs": historical_pairs,
        "records": receipt_records,
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"localization integrity OK; stories={len(expected)}; locales={','.join(LOCALES)}; "
        f"strict={strict_pairs}; historical={historical_pairs}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
