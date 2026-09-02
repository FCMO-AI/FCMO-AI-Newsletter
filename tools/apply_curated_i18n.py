#!/usr/bin/env python3
"""Apply FCMO AI Newsletter curated EN/ES/ZH localization to an assembled public tree.

English remains canonical. Spanish and Simplified Chinese are committed, reviewable
locale packs. No network translation provider or runtime generative fallback exists.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SUPPORTED = ("en", "es-419", "zh-Hans")
CURATED = ("es-419", "zh-Hans")
REQUIRED_FIELDS = ("title", "summary", "why_it_matters")
BUNDLE_MARKER = 'id="fcmo-i18n-data"'
SCRIPT_MARKER = 'assets/curated-i18n.js'
STYLE_MARKER = 'assets/curated-i18n.css'
TRANSLATION_ENDPOINT_MARKERS = (
    "translate.googleapis.com", "googleapis.com/language/translate", "api.deepl.com",
    "api.cognitive.microsofttranslator.com", "api.openai.com", "api.anthropic.com",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_editorial(index_text: str) -> dict[str, dict[str, str]]:
    match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', index_text, re.S)
    if not match:
        raise ValueError("index is missing embedded fcmo-data corpus")
    data = json.loads(match.group(1))
    records = data.get("records") or []
    if not records:
        raise ValueError("canonical corpus contains no news records")
    editorial: dict[str, dict[str, str]] = {}
    for row in records:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError("canonical corpus contains a record without a stable id")
        if rid in editorial:
            raise ValueError(f"canonical corpus contains duplicate record id: {rid}")
        missing = [field for field in REQUIRED_FIELDS if not isinstance(row.get(field), str) or not row[field].strip()]
        if missing:
            raise ValueError(f"canonical record {rid} is missing required editorial fields: {', '.join(missing)}")
        editorial[rid] = {field: row[field] for field in REQUIRED_FIELDS}
    return editorial


def _canonical_digest(canonical: dict[str, dict[str, str]]) -> str:
    return sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def _load_pack(target: Path, locale: str) -> dict:
    # Locale packs are deliberately split into small reviewable source files so a
    # story translation can be audited without wading through a monolithic blob.
    locale_dir = target / "data" / "i18n" / locale
    ui_path = locale_dir / "ui.json"
    parts = sorted(locale_dir.glob("part-*.json")) if locale_dir.is_dir() else []
    if not ui_path.is_file() or not parts:
        raise ValueError(f"missing curated locale pack directory: {locale_dir.relative_to(target)}")
    ui = json.loads(ui_path.read_text(encoding="utf-8"))
    records: dict[str, dict[str, str]] = {}
    for path in parts:
        part = json.loads(path.read_text(encoding="utf-8"))
        if part.get("schema") != "fcmo-curated-locale-part-v1" or part.get("locale") != locale:
            raise ValueError(f"{path.relative_to(target)}: invalid locale part metadata")
        if part.get("canonical_source_sha256") != ui.get("canonical_source_sha256"):
            raise ValueError(f"{path.relative_to(target)}: canonical source hash drift")
        overlap = set(records) & set(part.get("records") or {})
        if overlap:
            raise ValueError(f"{path.relative_to(target)}: duplicate record IDs {sorted(overlap)}")
        records.update(part.get("records") or {})
    return {
        "schema": "fcmo-curated-locale-v1",
        "locale": locale,
        "language_name": "Español (Latinoamérica)" if locale == "es-419" else "简体中文",
        "canonical_locale": "en",
        "curation": ui.get("curation") or {},
        "canonical_record_count": ui.get("canonical_record_count"),
        "canonical_source_sha256": ui.get("canonical_source_sha256"),
        "records": records,
        "ui": ui.get("ui") or {},
    }


def validate_curated_i18n(target: Path, canonical_index_sha256: str | None = None) -> dict:
    index = target / "index.html"
    text = index.read_text(encoding="utf-8")
    canonical = _canonical_editorial(text)
    expected_ids = set(canonical)
    canonical_count = len(expected_ids)
    digest = _canonical_digest(canonical)
    errors: list[str] = []
    packs: dict[str, dict] = {}

    for locale in CURATED:
        try:
            pack = _load_pack(target, locale)
            packs[locale] = pack
        except Exception as exc:
            errors.append(str(exc)); continue
        if pack.get("schema") != "fcmo-curated-locale-v1":
            errors.append(f"{locale}: wrong locale schema")
        if pack.get("locale") != locale or pack.get("canonical_locale") != "en":
            errors.append(f"{locale}: locale/canonical metadata mismatch")
        if pack.get("curation", {}).get("runtime_machine_translation") is not False:
            errors.append(f"{locale}: runtime translation must be explicitly false")
        if pack.get("curation", {}).get("human_reviewed") is not False:
            errors.append(f"{locale}: pack must not claim human review")
        if pack.get("canonical_record_count") != canonical_count:
            errors.append(
                f"{locale}: canonical_record_count metadata is {pack.get('canonical_record_count')!r}, "
                f"expected {canonical_count}"
            )
        if pack.get("canonical_source_sha256") != digest:
            errors.append(f"{locale}: canonical editorial source hash mismatch")
        rows = pack.get("records") or {}
        if set(rows) != expected_ids:
            missing = sorted(expected_ids - set(rows))
            extra = sorted(set(rows) - expected_ids)
            detail = []
            if missing:
                detail.append(f"missing {missing}")
            if extra:
                detail.append(f"extra {extra}")
            errors.append(f"{locale}: record IDs do not exactly match canonical corpus ({'; '.join(detail)})")
        for rid in sorted(expected_ids & set(rows)):
            for field in REQUIRED_FIELDS:
                value = rows[rid].get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{locale}: {rid}.{field} missing")
                elif value.strip() == canonical[rid][field].strip():
                    errors.append(f"{locale}: {rid}.{field} is unchanged canonical English")
        if not isinstance(pack.get("ui"), dict) or len(pack["ui"]) < 40:
            errors.append(f"{locale}: UI catalogue is unexpectedly incomplete")

    for marker in TRANSLATION_ENDPOINT_MARKERS:
        for path in [target / "assets" / "curated-i18n.js", *(target / "data" / "i18n").rglob("*.json")]:
            if path.is_file() and marker in path.read_text(encoding="utf-8").lower():
                errors.append(f"runtime translation/provider endpoint detected in {path.relative_to(target)}: {marker}")

    localized = BUNDLE_MARKER in text and SCRIPT_MARKER in text and STYLE_MARKER in text
    if localized:
        manifest_path = target / "data" / "i18n" / "manifest.json"
        if not manifest_path.is_file():
            errors.append("localized index exists but data/i18n/manifest.json is missing")
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("supported_locales") != list(SUPPORTED):
                errors.append("i18n manifest must expose exactly en, es-419, zh-Hans")
            if manifest.get("canonical_record_count") != canonical_count:
                errors.append("i18n manifest canonical record count mismatch")
            if manifest.get("canonical_editorial_sha256") != digest:
                errors.append("i18n manifest canonical editorial hash mismatch")
            if canonical_index_sha256 and manifest.get("canonical_index_sha256") != canonical_index_sha256:
                errors.append("i18n manifest canonical index hash mismatch")
            current_index_hash = sha256(index.read_bytes())
            if manifest.get("localized_index_sha256") != current_index_hash:
                errors.append("i18n manifest localized index hash mismatch")

    if errors:
        raise ValueError("curated localization validation failed:\n- " + "\n- ".join(errors))
    return {"records": canonical_count, "canonical_editorial_sha256": digest, "packs": packs}


def apply_curated_i18n(target: Path, canonical_index_sha256: str) -> None:
    index = target / "index.html"
    original = index.read_text(encoding="utf-8")
    if BUNDLE_MARKER in original:
        raise ValueError("curated localization was already applied")
    if sha256(index.read_bytes()) != canonical_index_sha256:
        raise ValueError("refusing to localize an index that is not the frozen canonical English release")

    result = validate_curated_i18n(target)
    bundle = {
        "schema": "fcmo-curated-i18n-bundle-v1",
        "canonical_locale": "en",
        "supported_locales": list(SUPPORTED),
        "curated_locales": list(CURATED),
        "packs": {locale: result["packs"][locale] for locale in CURATED},
    }
    encoded = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    style_tag = '<link rel="stylesheet" href="assets/curated-i18n.css" data-fcmo-i18n="style">'
    payload = f'<script id="fcmo-i18n-data" type="application/json">{encoded}</script><script src="assets/curated-i18n.js" data-fcmo-i18n="runtime"></script>'

    localized = original.replace("</head>", style_tag + "</head>", 1)
    match = re.search(r'(<script id="fcmo-data" type="application/json">.*?</script>)', localized, re.S)
    if not match:
        raise ValueError("unable to locate canonical data block for deterministic injection")
    localized = localized[:match.end()] + payload + localized[match.end():]
    index.write_text(localized, encoding="utf-8")

    manifest = {
        "schema": "fcmo-curated-i18n-manifest-v1",
        "canonical_locale": "en",
        "supported_locales": list(SUPPORTED),
        "curated_locales": list(CURATED),
        "canonical_record_count": result["records"],
        "canonical_index_sha256": canonical_index_sha256,
        "canonical_editorial_sha256": result["canonical_editorial_sha256"],
        "localized_index_sha256": sha256(index.read_bytes()),
        "runtime_machine_translation": False,
        "human_review_claim": False,
        "locale_resolution": ["?lang=", "saved manual selection", "navigator.languages", "en fallback"],
    }
    (target / "data" / "i18n" / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # The frozen release builder writes build-manifest.json before localization. Refresh it
    # after adding the curated runtime so the published integrity ledger describes the
    # actual bytes that GitHub Pages will serve.
    build_path = target / "build-manifest.json"
    if build_path.is_file():
        build = json.loads(build_path.read_text(encoding="utf-8"))
        entries = {}
        for path in sorted(p for p in target.rglob("*") if p.is_file()):
            rel = path.relative_to(target).as_posix()
            if rel == "build-manifest.json":
                continue
            entries[rel] = sha256(path.read_bytes())
        build["files"] = entries
        build["localization"] = {
            "schema": manifest["schema"],
            "supported_locales": manifest["supported_locales"],
            "canonical_index_sha256": manifest["canonical_index_sha256"],
            "localized_index_sha256": manifest["localized_index_sha256"],
        }
        build_path.write_text(json.dumps(build, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    validate_curated_i18n(target, canonical_index_sha256)


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    canonical_hash = sys.argv[2] if len(sys.argv) > 2 else sha256((root / "index.html").read_bytes())
    apply_curated_i18n(root, canonical_hash)
    print(f"Curated FCMO localization applied: {', '.join(SUPPORTED)}")
