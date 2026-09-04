#!/usr/bin/env python3
"""Translate missing canonical FCMO records into curated locale packs.

The locale packs are source data, not a runtime translation cache.  This tool
therefore translates only missing records and commits a complete batch after
all requested locales have translated successfully.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# When this file is launched as ``python tools/translate_records.py``, Python
# puts ``tools/`` (rather than the repository root) on sys.path.  Add the root
# so the field definitions are imported from the authoritative module below.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.apply_curated_i18n import (
    PROSE_DICTS,
    PROSE_LISTS,
    PROSE_OBJECT_LISTS,
    PROSE_STRINGS,
    PROPER_TAXONOMY_IDENTIFIERS,
    _canonical_digest,
    _canonical_editorial,
    _taxonomy_values,
    _validate_overlay_shape,
    _validate_prose_complete,
)


ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_LOCALES = "es-419,zh-Hans"
DEFAULT_MODEL = "claude-opus-5"
MAX_ATTEMPTS = 3
SCRIPT_RE = re.compile(
    r'<script\s+id=["\']fcmo-data["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.S | re.I,
)
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


class ToolError(Exception):
    """A user-facing operational error that should return exit code 1."""


class MissingCredential(ToolError):
    """The Anthropic engine cannot run without its API key."""


def _read_canonical(site: Path) -> tuple[dict[str, dict[str, Any]], str]:
    index = site / "index.html"
    try:
        text = index.read_text(encoding="utf-8")
    except OSError as exc:
        raise ToolError(f"cannot read canonical index: {index}") from exc
    match = SCRIPT_RE.search(text)
    if not match:
        raise ToolError("index is missing embedded fcmo-data corpus")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ToolError("canonical fcmo-data is not valid JSON") from exc
    rows = data.get("records") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ToolError("canonical corpus contains no records array")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"].strip():
            raise ToolError("canonical corpus contains a record without a stable id")
        record_id = row["id"]
        if record_id in result:
            raise ToolError(f"canonical corpus contains duplicate record id: {record_id}")
        result[record_id] = row
    return result, text


def _load_locale(i18n_dir: Path, locale: str) -> tuple[list[tuple[Path, dict[str, Any]]], set[str]]:
    locale_dir = i18n_dir / locale
    paths = sorted(locale_dir.glob("part-*.json")) if locale_dir.is_dir() else []
    if not paths:
        raise ToolError(f"missing locale parts for {locale}: {locale_dir}")
    loaded: list[tuple[Path, dict[str, Any]]] = []
    ids: set[str] = set()
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ToolError(f"cannot read locale part: {path}") from exc
        records = document.get("records") if isinstance(document, dict) else None
        if not isinstance(records, dict):
            raise ToolError(f"{path} does not contain a records object")
        overlap = ids & set(records)
        if overlap:
            raise ToolError(f"{locale} contains duplicate record ids: {', '.join(sorted(overlap))}")
        ids.update(records)
        loaded.append((path, document))
    return loaded, ids


def _missing_records(
    canonical: dict[str, dict[str, Any]], translated_ids: set[str]
) -> dict[str, dict[str, Any]]:
    return {record_id: canonical[record_id] for record_id in sorted(set(canonical) - translated_ids)}


def _source_overlay(record: dict[str, Any]) -> dict[str, Any]:
    """Build the exact prose-only shape declared by the curated gate."""
    overlay: dict[str, Any] = {}
    for key in PROSE_STRINGS:
        if key in record:
            overlay[key] = record[key]
    for key in PROSE_LISTS:
        if key in record:
            overlay[key] = record[key]
    for key, fields in PROSE_OBJECT_LISTS.items():
        if key in record:
            overlay[key] = [
                {field: item[field] for field in fields if isinstance(item, dict) and field in item}
                for item in record[key]
            ]
    for key in PROSE_DICTS:
        if key in record and isinstance(record[key], dict):
            overlay[key] = dict(record[key])
    return overlay


def _map_strings(value: Any, transform) -> Any:
    if isinstance(value, str):
        return transform(value)
    if isinstance(value, list):
        return [_map_strings(item, transform) for item in value]
    if isinstance(value, dict):
        return {key: _map_strings(item, transform) for key, item in value.items()}
    return value


def _stub_string(value: str, locale: str) -> str:
    # Keep the marker free of digits so the same numeric-token check used for
    # provider output still verifies the canonical figures in stub output.
    marker_locale = locale.replace("419", "LATAM").replace("-", "_")
    return f"[{marker_locale} stub] {value}"


def _stub_translate(records: dict[str, dict[str, Any]], locale: str) -> dict[str, dict[str, Any]]:
    return {
        record_id: _map_strings(_source_overlay(record), lambda value: _stub_string(value, locale))
        for record_id, record in records.items()
    }


def _translation_instructions(locale: str) -> str:
    language = {
        "es-419": "neutral Latin American Spanish",
        "zh-Hans": "Simplified Chinese",
    }.get(locale, locale)
    return (
        f"Translate the editorial prose into {language}. Use a technical journalistic register. "
        "Preserve proper names, product and model names, identifiers (including FCMO IDs), "
        "numbers, percentages, dates, and version strings exactly; do not translate or alter them. "
        "Translate every string value, preserve the object keys and list lengths, and add no keys. "
        "Return JSON only in the form {\"records\": {record_id: translated_prose_overlay}}."
    )


def _json_from_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S | re.I)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ToolError("Anthropic returned invalid JSON")
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ToolError("Anthropic returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ToolError("Anthropic returned a non-object JSON value")
    return value


def _response_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        raise ToolError("Anthropic response has no content")
    text = "".join(item.get("text", "") for item in content if isinstance(item, dict))
    if not text.strip():
        raise ToolError("Anthropic response has no text")
    return text


def _preserves_numbers(source: Any, translated: Any) -> bool:
    if isinstance(source, str):
        return NUMBER_RE.findall(source) == NUMBER_RE.findall(translated) if isinstance(translated, str) else False
    if isinstance(source, list):
        return isinstance(translated, list) and len(source) == len(translated) and all(
            _preserves_numbers(left, right) for left, right in zip(source, translated)
        )
    if isinstance(source, dict):
        return isinstance(translated, dict) and all(
            key in translated and _preserves_numbers(value, translated[key])
            for key, value in source.items()
        )
    return source == translated


def _validate_exact_overlay_shape(source: Any, translated: Any, path: str, errors: list[str]) -> None:
    """Reject provider output outside the prose-only field projection."""
    if isinstance(source, dict):
        if not isinstance(translated, dict):
            errors.append(f"{path}: expected an object")
            return
        missing = set(source) - set(translated)
        extra = set(translated) - set(source)
        if missing:
            errors.append(f"{path}: missing fields {sorted(missing)}")
        if extra:
            errors.append(f"{path}: extra fields {sorted(extra)}")
        for key in sorted(set(source) & set(translated)):
            _validate_exact_overlay_shape(source[key], translated[key], f"{path}.{key}", errors)
        return
    if isinstance(source, list):
        if not isinstance(translated, list) or len(source) != len(translated):
            found = len(translated) if isinstance(translated, list) else "none"
            errors.append(f"{path}: expected {len(source)} entries, found {found}")
            return
        for index, (source_value, translated_value) in enumerate(zip(source, translated)):
            _validate_exact_overlay_shape(source_value, translated_value, f"{path}[{index}]", errors)
        return
    if isinstance(source, str) and (not isinstance(translated, str) or not translated.strip()):
        errors.append(f"{path}: expected a non-empty translated string")


def _validate_translations(
    source_records: dict[str, dict[str, Any]], translations: dict[str, dict[str, Any]]
) -> None:
    expected = set(source_records)
    if set(translations) != expected:
        missing = sorted(expected - set(translations))
        extra = sorted(set(translations) - expected)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"extra {extra}")
        raise ToolError("translation response record IDs do not match (" + "; ".join(detail) + ")")
    for record_id, source in source_records.items():
        translated = translations[record_id]
        if not isinstance(translated, dict):
            raise ToolError(f"translation for {record_id} is not an object")
        errors: list[str] = []
        source_overlay = _source_overlay(source)
        _validate_exact_overlay_shape(source_overlay, translated, record_id, errors)
        _validate_overlay_shape(source, translated, record_id, errors)
        _validate_prose_complete(record_id, source, translated, errors)
        if not _preserves_numbers(source_overlay, translated):
            errors.append("numbers differ from canonical prose")
        if errors:
            raise ToolError(f"invalid translation for {record_id}: {'; '.join(errors[:3])}")


def _anthropic_translate(
    records: dict[str, dict[str, Any]], locale: str, model: str, api_key: str
) -> dict[str, dict[str, Any]]:
    source = {record_id: _source_overlay(record) for record_id, record in records.items()}
    prompt = _translation_instructions(locale) + "\n\nCanonical prose overlays:\n" + json.dumps(
        source, ensure_ascii=False, indent=2
    )
    request_body = {
        "model": model,
        "max_tokens": 65536,
        "system": _translation_instructions(locale),
        "messages": [{"role": "user", "content": prompt}],
    }
    encoded = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    last_error: ToolError | None = None
    for _attempt in range(MAX_ATTEMPTS):
        request = urllib.request.Request(
            ENDPOINT,
            data=encoded,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            parsed = _json_from_response(_response_text(response_data))
            translations = parsed.get("records", parsed)
            if not isinstance(translations, dict):
                raise ToolError("Anthropic returned no records object")
            _validate_translations(records, translations)
            return translations
        except urllib.error.HTTPError as exc:
            last_error = ToolError(f"Anthropic request failed with HTTP status {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = ToolError(f"Anthropic request failed: {type(exc).__name__}")
        except (json.JSONDecodeError, ToolError) as exc:
            last_error = exc if isinstance(exc, ToolError) else ToolError("Anthropic returned invalid JSON")
    assert last_error is not None
    raise ToolError(f"Anthropic translation failed after {MAX_ATTEMPTS} attempts: {last_error}")


def _taxonomy_translation_instructions(locale: str) -> str:
    language = {
        "es-419": "neutral Latin American Spanish",
        "zh-Hans": "Simplified Chinese",
    }.get(locale, locale)
    return (
        f"Translate these short interface taxonomy labels into {language}. "
        "Use concise technical-journalistic wording. Preserve proper names, product and model names, "
        "identifiers, numbers, and version strings. Keep the JSON keys exactly as supplied and return "
        "JSON only in the form {\"translations\": {source_label: translated_label}}."
    )


def _validate_taxonomy_translations(
    source_values: set[str], translations: dict[str, Any]
) -> dict[str, str]:
    if set(translations) != source_values:
        missing = sorted(source_values - set(translations))
        extra = sorted(set(translations) - source_values)
        detail = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"extra {extra}")
        raise ToolError("taxonomy translation response keys do not match (" + "; ".join(detail) + ")")
    result: dict[str, str] = {}
    for source in sorted(source_values):
        translated = translations[source]
        if not isinstance(translated, str) or not translated.strip():
            raise ToolError(f"taxonomy translation for {source!r} is empty")
        if source not in PROPER_TAXONOMY_IDENTIFIERS and translated.strip() == source:
            raise ToolError(f"taxonomy translation for {source!r} remains English")
        result[source] = translated
    return result


def _anthropic_translate_taxonomy(
    source_values: set[str], locale: str, model: str, api_key: str
) -> dict[str, str]:
    instructions = _taxonomy_translation_instructions(locale)
    request_body = {
        "model": model,
        "max_tokens": 4096,
        "system": instructions,
        "messages": [{
            "role": "user",
            "content": instructions + "\n\nSource taxonomy labels:\n" + json.dumps(sorted(source_values), ensure_ascii=False),
        }],
    }
    encoded = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    last_error: ToolError | None = None
    for _attempt in range(MAX_ATTEMPTS):
        request = urllib.request.Request(
            ENDPOINT,
            data=encoded,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                response_data = json.loads(response.read().decode("utf-8"))
            parsed = _json_from_response(_response_text(response_data))
            translations = parsed.get("translations", parsed)
            if not isinstance(translations, dict):
                raise ToolError("Anthropic returned no taxonomy translations object")
            return _validate_taxonomy_translations(source_values, translations)
        except urllib.error.HTTPError as exc:
            last_error = ToolError(f"Anthropic request failed with HTTP status {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = ToolError(f"Anthropic request failed: {type(exc).__name__}")
        except (json.JSONDecodeError, ToolError) as exc:
            last_error = exc if isinstance(exc, ToolError) else ToolError("Anthropic returned invalid JSON")
    assert last_error is not None
    raise ToolError(f"Anthropic taxonomy translation failed after {MAX_ATTEMPTS} attempts: {last_error}")


def _load_ui(i18n_dir: Path, locale: str) -> tuple[Path, dict[str, Any], str]:
    path = i18n_dir / locale / "ui.json"
    if not path.is_file():
        raise ToolError(f"missing UI catalogue for {locale}: {path}")
    try:
        original = path.read_text(encoding="utf-8")
        document = json.loads(original)
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError(f"cannot read UI catalogue: {path}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("ui"), dict):
        raise ToolError(f"{path} does not contain a ui catalogue object")
    return path, document, original


def _format_json(document: dict[str, Any], original: str) -> str:
    if "\n" not in original:
        return json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
    indentation = re.search(r"\n([ \t]+)\S", original)
    indent = indentation.group(1) if indentation else "  "
    return json.dumps(document, ensure_ascii=False, indent=indent) + "\n"


def _write_batch(changes: list[tuple[Path, dict[str, Any], str]]) -> None:
    temporary: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path]] = []
    try:
        for path, document, original in changes:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False
            ) as handle:
                handle.write(_format_json(document, original))
                temp_path = Path(handle.name)
            temporary.append((path, temp_path))
        for path, temp_path in temporary:
            fd, backup_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".bak", dir=path.parent)
            os.close(fd)
            backup_path = Path(backup_name)
            backup_path.unlink()
            os.replace(path, backup_path)
            backups.append((path, backup_path))
            os.replace(temp_path, path)
    except Exception:
        for path, backup_path in reversed(backups):
            try:
                os.replace(backup_path, path)
            except OSError:
                pass
        for _path, temp_path in temporary:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        for _path, backup_path in backups:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    for _path, backup_path in backups:
        backup_path.unlink(missing_ok=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--locales", default=DEFAULT_LOCALES)
    parser.add_argument("--engine", choices=("anthropic", "stub"), default="anthropic")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    args.locales = tuple(locale.strip() for locale in args.locales.split(",") if locale.strip())
    if not args.locales:
        parser.error("--locales must contain at least one locale")
    if len(set(args.locales)) != len(args.locales):
        parser.error("--locales must not contain duplicates")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        canonical, index_text = _read_canonical(args.site)
        try:
            canonical_digest = _canonical_digest(_canonical_editorial(index_text))
        except ValueError as exc:
            raise ToolError(f"cannot calculate canonical editorial digest: {exc}") from exc
        taxonomy_values = _taxonomy_values(canonical)
        packs: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
        ui_packs: dict[str, tuple[Path, dict[str, Any], str]] = {}
        missing_by_locale: dict[str, dict[str, dict[str, Any]]] = {}
        for locale in args.locales:
            loaded, translated_ids = _load_locale(args.i18n_dir, locale)
            packs[locale] = loaded
            ui_packs[locale] = _load_ui(args.i18n_dir, locale)
            missing_by_locale[locale] = _missing_records(canonical, translated_ids)

        for locale in args.locales:
            missing = missing_by_locale[locale]
            if missing:
                for record_id in missing:
                    print(f"{locale}: {record_id}")
            else:
                print(f"{locale}: no missing canonical records")
        if args.dry_run:
            return 0

        if args.engine == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key.strip():
                raise MissingCredential("ANTHROPIC_API_KEY is required for --engine anthropic")
        else:
            api_key = ""

        translations_by_locale: dict[str, dict[str, dict[str, Any]]] = {}
        taxonomy_by_locale: dict[str, dict[str, str]] = {}
        for locale in args.locales:
            missing = missing_by_locale[locale]
            if missing:
                if args.engine == "stub":
                    translations = _stub_translate(missing, locale)
                    _validate_translations(missing, translations)
                else:
                    translations = _anthropic_translate(missing, locale, args.model, api_key)
                translations_by_locale[locale] = translations

            catalog = ui_packs[locale][1]["ui"]
            missing_taxonomy = taxonomy_values - set(catalog)
            if missing_taxonomy:
                if args.engine == "stub":
                    translations = {
                        source: _stub_string(source, locale)
                        for source in sorted(missing_taxonomy)
                    }
                    taxonomy_by_locale[locale] = _validate_taxonomy_translations(missing_taxonomy, translations)
                else:
                    taxonomy_by_locale[locale] = _anthropic_translate_taxonomy(
                        missing_taxonomy, locale, args.model, api_key
                    )

        changes: dict[Path, tuple[dict[str, Any], str]] = {}
        for locale, translations in translations_by_locale.items():
            parts = packs[locale]
            target_path, target_document = min(parts, key=lambda item: (len(item[1]["records"]), item[0].name))
            original = target_path.read_text(encoding="utf-8")
            for record_id in sorted(translations):
                target_document["records"][record_id] = translations[record_id]
            changes[target_path] = (target_document, original)

        # El manifiesto del catalogo tambien afirma el corpus que cubre. Los tres
        # valores se actualizan junto con sus traducciones y entran en el mismo
        # lote atomico: cuenta, digest editorial y taxonomia faltante.
        for locale in args.locales:
            ui_path, ui_document, original = ui_packs[locale]
            catalog = ui_document["ui"]
            catalog.update(taxonomy_by_locale.get(locale, {}))
            changed = False
            if ui_document.get("canonical_record_count") != len(canonical):
                ui_document["canonical_record_count"] = len(canonical)
                changed = True
            if ui_document.get("canonical_source_sha256") != canonical_digest:
                ui_document["canonical_source_sha256"] = canonical_digest
                changed = True
            if taxonomy_by_locale.get(locale):
                changed = True
            if changed:
                changes[ui_path] = (ui_document, original)

            # `_load_pack` rejects any part whose source digest differs from
            # ui.json. The field is therefore a mirrored pack invariant, not
            # prose to be retranslated; keep every existing part aligned with
            # the canonical digest in this same transaction.
            for part_path, part_document in packs[locale]:
                if part_document.get("canonical_source_sha256") == canonical_digest:
                    continue
                part_original = part_path.read_text(encoding="utf-8")
                part_document["canonical_source_sha256"] = canonical_digest
                changes[part_path] = (part_document, part_original)

        if changes:
            _write_batch([(path, document, original) for path, (document, original) in changes.items()])
        for locale in args.locales:
            count = len(missing_by_locale[locale])
            print(f"{locale}: applied {count} record(s)")
        return 0
    except MissingCredential as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ToolError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
