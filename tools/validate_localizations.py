#!/usr/bin/env python3
"""Decide, field by field, whether each (story, locale) pair is really translated.

The unit of localization is the pair (story, locale). A pair is complete only when
every piece of reader-facing prose that exists in the canonical English record has
a native counterpart: title, summary, why it matters, importance rationale,
limitations, contradictory evidence, every claim, every evidence gap, every
relationship summary and every technical field. A pair that only carries a
headline is ``PENDING``; a pair that a deterministic gate rejects (English left in
place, changed numbers/IDs/URLs, broken structure) is ``FAILED``. Pending and
failed pairs are rendered as a localized notice that links to the English
original, never as English prose under a Spanish or Chinese ``lang``.

Two modes:

``--strict --corpus corpus [--locale es-419|zh-Hans|all]``
    Field-level completeness against the canonical corpus. The first stdout line is
    ``COMPLETE <n>`` (exit 0) or ``INCOMPLETE <n>`` (exit 1), where ``n`` is the
    number of incomplete pairs (or of complete pairs when nothing is missing).
    ``--write-overlays DIR`` also writes one ``contracts/locale-overlay.v2`` file
    per locale. Exit 2 means the input could not be read.

legacy (``--site release-src``)
    The structural gate the release workflows call. It still fails closed when a
    story id has no overlay at all, and it records the field-level state of every
    pair in the receipt, so the receipt never calls a headline-only pair complete.

This tool never translates and never calls a model: it measures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    from tools.reconcile_locale_overlays import canonical_records
except ImportError:  # direct script execution from tools/
    from reconcile_locale_overlays import canonical_records

LOCALES = ("es-419", "zh-Hans")
AIRLOCK_PART = "part-airlock.json"
DESK_PART = "part-desk.json"
DELTA_SCHEMA = "fcmo-airlocked-locale-delta-v1"
OVERLAY_SCHEMA = "fcmo-locale-overlay-v2"
# Footnote: punctuation adjacent to a number is editorial, not part of its value.
# This keeps grouped/decimal values intact (1,050,000; 99.9%; 3.66x) while allowing
# Spanish and Chinese to move commas or sentence punctuation naturally.
NUM = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:[.,]\d+)*(?:%|x|×|[KMBT])?", re.I)
FCMO_ID = re.compile(r"\bFCMO-[0-9A-F]{12}\b")
ID_RE = re.compile(r"^FCMO-[0-9A-F]{12}$")
URL = re.compile(r"https?://[^\s\]\[)<>'\"]+")
CJK = re.compile(r"[㐀-䶿一-鿿]")
PROSE_KEYS = {
    "title", "summary", "why_it_matters", "why", "importance_rationale",
    "limitations", "contradictory_evidence", "claims", "evidence_gaps",
    "relationships", "technical",
}
# Prose keys of locale-overlay.v2, in reading order. ``why`` is a legacy alias of
# ``why_it_matters`` and is folded into it before any comparison.
V2_PROSE_KEYS = (
    "title", "headline", "dek", "summary", "why_it_matters", "importance_rationale",
    "limitations", "contradictory_evidence", "claims", "evidence_gaps",
    "relationships", "technical",
)
# Leaves under these keys are codes, ids or timestamps, not prose. They are shown
# through the UI catalogs (claim labels, gap kinds) or not at all.
NON_PROSE_LEAF_KEYS = frozenset({
    "label", "qualifier", "kind", "state", "updated_at", "target_id", "type", "id",
    "url", "source_url",
})
COMPLETE_STATES = ("NATIVE_ARB", "MACHINE_REVIEWED")
INCOMPLETE_STATES = ("PENDING", "FAILED")

# English function words that do not exist as Spanish words. A Spanish field in
# which they make up a real share of the words is English left in place.
EN_STOPWORDS = frozenset(
    "the and of to is that with for this are was which from by on not it be have its "
    "than an or as at were but their these those into".split()
)
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
ANY_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
LATIN_RUN = re.compile(r"(?:[A-Za-z][A-Za-z'’-]*[\s,;:()\"“”]+){5,}[A-Za-z][A-Za-z'’-]*")


def stable_digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_locale_details(root: Path, locale: str) -> tuple[dict[str, dict[str, Any]], set[str], dict[str, dict[str, dict[str, Any]]], dict[str, dict[str, Any]]]:
    """Merge source packs by field. ARB wins; desk fills gaps and remains an alternate."""
    result: dict[str, dict[str, Any]] = {}
    strict: set[str] = set()
    provenance: dict[str, dict[str, dict[str, Any]]] = {}
    alternates: dict[str, dict[str, Any]] = {}
    desk_records: dict[str, dict[str, Any]] = {}
    desk_meta: dict[str, dict[str, Any]] = {}
    desk_bindings: dict[str, Any] = {}
    for path in sorted((root / locale).glob("part-*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        rows = doc.get("records")
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: records object missing")
        if path.name == DESK_PART:
            desk_records = rows
            desk_meta = doc.get("provenance") or {}
            desk_bindings = doc.get("source_bindings") or {}
            continue
        origin = "arb" if path.name == AIRLOCK_PART or re.fullmatch(r"part-\d+\.json", path.name) else None
        for rid, row in rows.items():
            if rid in result:
                raise SystemExit(f"{path}: duplicate ARB locale id {rid}")
            result[rid] = row
            provenance[rid] = {key: {"origin": origin, "at": doc.get("generated_at") or doc.get("at"),
                                     "human_reviewed": False, "network_translation": False}
                               for key in row}
            for key, binding in (doc.get("source_bindings", {}).get(rid) or {}).items():
                if key in provenance[rid]:
                    provenance[rid][key].update(binding)
        if path.name == AIRLOCK_PART:
            strict.update(rows)
    for rid, row in desk_records.items():
        if not isinstance(row, dict):
            raise SystemExit(f"{root / locale / DESK_PART}: {rid} must be an object")
        meta = desk_meta.get(rid) if isinstance(desk_meta, dict) else None
        if not isinstance(meta, dict) or meta.get("origin") != "publication-desk" or \
                not isinstance(meta.get("at"), str) or \
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", meta["at"]) or \
                meta.get("human_reviewed") is not False or meta.get("network_translation") is not False:
            raise ValueError(f"{root / locale / DESK_PART}: {rid} has missing or invalid desk provenance")
        selected = result.setdefault(rid, {})
        provenance.setdefault(rid, {})
        for key, value in row.items():
            if key in selected:
                alternates.setdefault(rid, {})[key] = {"value": value, "provenance": meta}
            else:
                selected[key] = value
                provenance[rid][key] = meta
                # Desk metadata belongs to the selected field, just like ARB metadata.
                binding = (desk_bindings.get(rid) or {}).get(key)
                if binding is not None:
                    provenance[rid][key] = {**meta, **binding}
        strict.add(rid)
    return result, strict, provenance, alternates


def load_locale(root: Path, locale: str) -> tuple[dict[str, dict[str, Any]], set[str]]:
    rows, strict, _, _ = load_locale_details(root, locale)
    return rows, strict


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


def token_errors(source: Any, overlay: Any) -> list[str]:
    """Numbers, FCMO ids and URLs must survive translation unchanged."""
    matched_source = source_for_overlay(source, overlay)
    source_text = "\n".join(strings(matched_source))
    merged_text = "\n".join(strings(overlay))
    found: list[str] = []
    for regex, label in ((NUM, "number"), (FCMO_ID, "FCMO id"), (URL, "URL")):
        src = sorted(regex.findall(source_text))
        dst = sorted(regex.findall(merged_text))
        if src != dst:
            found.append(f"{label} tokens changed: source={src} locale={dst}")
    return found


def check_strict(source: dict[str, Any], overlay: dict[str, Any], locale: str, rid: str, errors: list[str]) -> None:
    check_common(source, overlay, locale, rid, errors)
    # Footnote: strict invariants apply only to modern ARB-authored material
    # that crossed the native-edition airlock. This keeps benchmark/version
    # drift fail-closed without retroactively rewriting the validation history
    # of the 2026 bootstrap translations.
    for message in token_errors(source, overlay):
        errors.append(f"{locale}:{rid}: {message}")


# ---------------------------------------------------------------------------
# Field-level completeness (locale-overlay.v2 semantics)
# ---------------------------------------------------------------------------

def normalize_record(row: dict[str, Any]) -> dict[str, Any]:
    """Fold the legacy ``why`` alias into ``why_it_matters``."""
    if not isinstance(row, dict):
        return row
    if "why" in row:
        row = dict(row)
        why = row.pop("why")
        if "why_it_matters" not in row:
            row["why_it_matters"] = why
    return row


def prose_leaves(value: Any, path: tuple = ()) -> Iterator[tuple[tuple, str]]:
    """Yield ``(path, text)`` for every non-empty prose string under ``value``."""
    if isinstance(value, str):
        if value.strip():
            yield path, value
    elif isinstance(value, dict):
        for key in sorted(value):
            if key in NON_PROSE_LEAF_KEYS:
                continue
            yield from prose_leaves(value[key], path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from prose_leaves(item, path + (index,))


def required_keys(source: dict[str, Any]) -> list[str]:
    """Prose keys of the English record that have something to translate."""
    source = normalize_record(source)
    return [key for key in V2_PROSE_KEYS if any(True for _ in prose_leaves(source.get(key)))]


def path_text(path: tuple) -> str:
    out = ""
    for part in path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out


def field_digest(value: Any) -> str:
    """Identity of prose and its positions; enum/timestamp changes are not prose."""
    return stable_digest(list(prose_leaves(value)))


def source_binding(source: dict[str, Any], overlay: dict[str, Any]) -> dict[str, dict[str, Any]]:
    source = normalize_record(source)
    return {key: {"source_sha256": field_digest(source.get("why_it_matters" if key == "why" else key)),
                  "locale_sha256": stable_digest(value)} for key, value in overlay.items()}


def looks_english(text: str, locale: str) -> bool:
    """True when a Spanish or Chinese field is really English prose."""
    if locale == "zh-Hans":
        for run in LATIN_RUN.finditer(text):
            words = [w.lower() for w in LATIN_WORD.findall(run.group(0))]
            if len(words) >= 6 and sum(1 for w in words if w in EN_STOPWORDS) >= 2:
                return True
        return False
    words = [w.lower() for w in ANY_WORD.findall(text)]
    stop = sum(1 for w in words if w in EN_STOPWORDS)
    return stop >= 3 and stop / max(1, len(words)) >= 0.12


def pair_status(source: dict[str, Any], overlay: Any, locale: str, strict: bool = False,
                provenance: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """Classify one (story, locale) pair.

    Returns ``{"state", "missing", "missing_paths", "failure", "complete_keys"}``.
    ``missing`` lists top-level prose keys with at least one untranslated leaf;
    ``complete_keys`` lists the keys whose every leaf is translated.
    """
    source = normalize_record(source)
    needed = required_keys(source)
    if not isinstance(overlay, dict) or not any(True for _ in prose_leaves(overlay)):
        return {
            "state": "PENDING", "missing": needed, "missing_paths": [k for k in needed],
            "failure": None, "complete_keys": [],
        }
    raw_overlay = overlay
    overlay = normalize_record(overlay)

    # A metadata refresh is not a translation. Reject the old wording before
    # comparing shapes/tokens: even a same-shape semantic edit invalidates it.
    stale = []
    for key, meta in (provenance or {}).items():
        canonical_key = "why_it_matters" if key == "why" else key
        if "source_sha256" in meta and canonical_key in overlay and (
            meta["source_sha256"] != field_digest(source.get(canonical_key))
            or meta.get("locale_sha256") != stable_digest(raw_overlay.get(key))
        ):
            stale.append(canonical_key)
    if stale:
        # Keep the original artifact for editorial repair; publish no stale prose.
        return {"state": "PENDING", "missing": needed, "missing_paths": list(needed),
                "failure": None, "complete_keys": [], "stale_fields": sorted(set(stale))}

    def failed(gate: str, detail: str) -> dict[str, Any]:
        return {
            "state": "FAILED", "missing": needed, "missing_paths": list(needed),
            "failure": {"gate": gate, "detail": detail[:200]}, "complete_keys": [],
        }

    shape: list[str] = []
    assert_shape(source, overlay, "overlay", shape)
    if shape:
        detail = shape[0].split(": ", 1)[-1]
        where = shape[0].split(":", 1)[0].replace("overlay.", "", 1)
        return failed("SHAPE_MISMATCH", f"{where}: {detail}")

    source_leaves = dict(prose_leaves(source))
    overlay_leaves = dict(prose_leaves(overlay))
    for path, text in overlay_leaves.items():
        original = source_leaves.get(path)
        if original is not None and " ".join(original.split()) == " ".join(text.split()) \
                and len(LATIN_WORD.findall(text)) >= 3:
            return failed("ENGLISH_LEAK", f"{path_text(path)} is identical to the English original")
        if looks_english(text, locale):
            return failed("ENGLISH_LEAK", f"{path_text(path)} is English prose")
    if locale == "zh-Hans":
        merged = "\n".join(overlay_leaves.values())
        if len(merged) >= 120 and len(CJK.findall(merged)) < 20:
            return failed("SCRIPT_MISMATCH", "long Chinese edition has almost no Han characters")
    if strict:
        problems = token_errors(
            {k: source.get(k) for k in V2_PROSE_KEYS if k in source},
            {k: overlay.get(k) for k in V2_PROSE_KEYS if k in overlay},
        )
        if problems:
            return failed("TOKENS_CHANGED", problems[0])

    missing_paths = [path_text(p) for p in source_leaves if p not in overlay_leaves]
    missing = [key for key in needed if any(p[0] == key and p not in overlay_leaves for p in source_leaves)]
    complete = [key for key in needed if key not in missing and key in overlay]
    origins = {((provenance or {}).get(key) or {}).get("origin") for key in complete}
    if complete and (None in origins or origins - {"arb", "publication-desk"}):
        return failed("UNKNOWN_ORIGIN", "selected translation field has missing or unknown origin")
    return {
        "state": "PENDING" if missing else ("MACHINE_REVIEWED" if "publication-desk" in origins else "NATIVE_ARB"),
        "missing": missing,
        "missing_paths": missing_paths,
        "failure": None,
        "complete_keys": complete,
    }


def is_complete(status: dict[str, Any]) -> bool:
    return status.get("state") in COMPLETE_STATES


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path.name}:{number}: record must be an object")
        rows.append(value)
    return rows


def load_corpus_canonical(corpus: Path) -> dict[str, dict[str, Any]]:
    """Live English records of a corpus directory.

    Live = the upstream records plus carried-forward ones, minus records the
    upstream withdrew or superseded and minus active tombstones.
    """
    developments = corpus / "data" / "developments.jsonl"
    if not developments.is_file():
        raise ValueError("corpus has no data/developments.jsonl")
    records: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(developments):
        rid = row.get("id")
        if not isinstance(rid, str) or not ID_RE.match(rid):
            raise ValueError("corpus record without a valid public id")
        if rid in records:
            raise ValueError(f"duplicate corpus id {rid}")
        records[rid] = row
    carried = corpus / "carried.jsonl"
    if carried.is_file():
        for line in read_jsonl(carried):
            record = line.get("record")
            rid = line.get("id")
            if isinstance(record, dict) and isinstance(rid, str) and rid not in records:
                records[rid] = record
    withdrawn = {
        rid for rid, row in records.items()
        if str(row.get("status") or "").lower() in {"withdrawn", "superseded"}
    }
    tombstones = corpus / "tombstones.json"
    if tombstones.is_file():
        doc = json.loads(tombstones.read_text(encoding="utf-8"))
        for entry in doc.get("tombstones") or []:
            if isinstance(entry, dict) and entry.get("reinstated_at") is None:
                withdrawn.add(str(entry.get("id")))
    return {rid: row for rid, row in records.items() if rid not in withdrawn}


def load_delta(corpus: Path, locale: str) -> dict[str, dict[str, Any]]:
    path = corpus / "data" / "locales" / locale / "records.json"
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != DELTA_SCHEMA or doc.get("locale") != locale:
        raise ValueError(f"{locale}: locale delta does not follow {DELTA_SCHEMA}")
    rows = doc.get("records")
    if not isinstance(rows, dict):
        raise ValueError(f"{locale}: locale delta has no records object")
    return {rid: row for rid, row in rows.items() if isinstance(row, dict)}


def effective_overlays_details(locale: str, i18n_dir: Path | None, corpus: Path | None):
    """Committed locale packs with the upstream (ARB) delta laid on top.

    Upstream fields win field by field; a delta never erases a field it does
    not carry. Ids that crossed the modern airlock get the strict token gate.
    """
    rows: dict[str, dict[str, Any]] = {}
    strict: set[str] = set()
    provenance: dict[str, dict[str, dict[str, Any]]] = {}
    alternates: dict[str, dict[str, Any]] = {}
    if i18n_dir is not None and (i18n_dir / locale).is_dir():
        packs, strict_ids, provenance, alternates = load_locale_details(i18n_dir, locale)
        rows = {rid: dict(value) for rid, value in packs.items() if isinstance(value, dict)}
        strict |= strict_ids
    if corpus is not None:
        canonical = load_corpus_canonical(corpus) if (corpus / "data/developments.jsonl").is_file() else {}
        for rid, delta in load_delta(corpus, locale).items():
            previous = rows.get(rid) or {}
            bindings = source_binding(canonical.get(rid, {}), delta)
            selected = provenance.setdefault(rid, {})
            for key, value in delta.items():
                if key in previous and previous[key] == value and "source_sha256" in selected.get(key, {}):
                    continue
                selected[key] = {"origin": "arb", "at": airlock_time(corpus),
                                 "human_reviewed": False, "network_translation": False, **bindings[key]}
            # Match the importer's whole-record ARB replacement, with independent
            # desk gap fills retained under their own source bindings.
            rows[rid] = {**{key: value for key, value in previous.items()
                            if selected.get(key, {}).get("origin") == "publication-desk"}, **delta}
            provenance[rid] = {key: selected[key] for key in rows[rid]}
            strict.add(rid)
    return rows, strict, provenance, alternates


def effective_overlays(locale: str, i18n_dir: Path | None, corpus: Path | None) -> tuple[dict[str, dict[str, Any]], set[str]]:
    rows, strict, _, _ = effective_overlays_details(locale, i18n_dir, corpus)
    return rows, strict


def locale_states(
    canonical: dict[str, dict[str, Any]],
    rows: dict[str, dict[str, Any]],
    strict_ids: set[str],
    locale: str,
    provenance: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        rid: pair_status(canonical[rid], rows.get(rid), locale, strict=rid in strict_ids,
                         provenance=(provenance or {}).get(rid))
        for rid in sorted(canonical)
    }


def summarize(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    complete = sorted(rid for rid, s in states.items() if is_complete(s))
    pending = sorted(rid for rid, s in states.items() if s["state"] == "PENDING")
    failed = sorted(rid for rid, s in states.items() if s["state"] == "FAILED")
    return {
        "stories": len(states), "complete": len(complete), "pending": len(pending),
        "failed": len(failed), "pending_ids": pending, "failed_ids": failed,
        "state_counts": {state: sum(s["state"] == state for s in states.values())
                         for state in (*COMPLETE_STATES, *INCOMPLETE_STATES)},
    }


def utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_now(value: str | None) -> datetime:
    raw = value or os.environ.get("FCMO_NOW")
    if raw:
        parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def airlock_time(corpus: Path | None) -> str | None:
    if corpus is None or not (corpus / "airlock.json").is_file():
        return None
    try:
        raw = json.loads((corpus / "airlock.json").read_text(encoding="utf-8")).get("generated_at")
        return utc_text(resolve_now(str(raw))) if raw else None
    except (ValueError, TypeError):
        return None


def overlay_entry(source: dict[str, Any], overlay: Any, status: dict[str, Any], at: str,
                  provenance: dict[str, dict[str, Any]] | None = None,
                  alternates: dict[str, Any] | None = None) -> dict[str, Any]:
    """One ``locale-overlay.v2`` entry. Rejected content is never carried over."""
    source = normalize_record(source)
    overlay = normalize_record(overlay) if isinstance(overlay, dict) else {}
    fields: dict[str, Any] = {}
    if status["state"] != "FAILED":
        # Only keys whose every leaf is translated; a half-translated list stays out.
        for key in V2_PROSE_KEYS:
            if key in status["complete_keys"]:
                fields[key] = overlay[key]
    field_provenance = {key: {**(provenance or {}).get(key, {}),
                              "at": (provenance or {}).get(key, {}).get("at") or at}
                        for key in fields}
    return {
        "state": status["state"],
        "source_sha256": stable_digest(translated_projection(source)),
        "fields": fields,
        "missing": list(status["missing"]),
        "provenance": field_provenance,
        "alternates": alternates or {},
        "failure": status["failure"],
    }


def overlay_document(
    locale: str,
    canonical: dict[str, dict[str, Any]],
    rows: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]],
    generated_at: str,
    at: str,
    provenance: dict[str, dict[str, dict[str, Any]]] | None = None,
    alternates: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema": OVERLAY_SCHEMA,
        "locale": locale,
        "canonical_locale": "en",
        "generated_at": generated_at,
        "records": {
            rid: overlay_entry(canonical[rid], rows.get(rid), states[rid], at,
                               (provenance or {}).get(rid), (alternates or {}).get(rid))
            for rid in sorted(canonical)
        },
    }


# Record prose keys -> stories.v2 l10n paths.
STORY_PATHS = {
    "title": "title", "headline": "headline", "dek": "dek", "summary": "summary",
    "why_it_matters": "why_it_matters", "importance_rationale": "importance_rationale",
    "technical": "technical", "claims": "evidence.claims", "limitations": "evidence.limitations",
    "evidence_gaps": "evidence.gaps", "contradictory_evidence": "evidence.contradictory",
    "relationships": "related",
}


def to_story_l10n(entry: dict[str, Any]) -> dict[str, Any]:
    """Map a ``locale-overlay.v2`` entry to the ``l10n`` object of ``stories.v2``."""
    fields = entry.get("fields") or {}
    out: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    for key in ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale"):
        if isinstance(fields.get(key), str) and fields[key].strip():
            out[key] = fields[key]
    if isinstance(fields.get("technical"), dict):
        out["technical"] = {k: v for k, v in fields["technical"].items() if isinstance(v, str)}
    if isinstance(fields.get("claims"), list):
        evidence["claims"] = [{"text": c["text"]} for c in fields["claims"] if isinstance(c, dict) and c.get("text")]
    if isinstance(fields.get("limitations"), list):
        evidence["limitations"] = [x for x in fields["limitations"] if isinstance(x, str) and x.strip()]
    if isinstance(fields.get("evidence_gaps"), list):
        evidence["gaps"] = [{"description": g["description"]} for g in fields["evidence_gaps"]
                            if isinstance(g, dict) and g.get("description")]
    if isinstance(fields.get("contradictory_evidence"), list):
        evidence["contradictory"] = [x for x in fields["contradictory_evidence"] if isinstance(x, str) and x.strip()]
    if evidence:
        out["evidence"] = evidence
    provenance = {
        STORY_PATHS[key]: value.get("origin")
        for key, value in (entry.get("provenance") or {}).items()
        if key in STORY_PATHS and key in fields
    }
    return {
        "state": entry["state"],
        "fields": out,
        "missing": [STORY_PATHS[key] for key in entry.get("missing") or [] if key in STORY_PATHS],
        "provenance": provenance,
    }


def strict_main(args: argparse.Namespace) -> int:
    locales = LOCALES if args.locale == "all" else (args.locale,)
    try:
        canonical = load_corpus_canonical(args.corpus)
        now = resolve_now(args.now)
        results: dict[str, dict[str, dict[str, Any]]] = {}
        documents: dict[str, dict[str, Any]] = {}
        at = airlock_time(args.corpus) or utc_text(now)
        for locale in locales:
            rows, strict_ids, provenance, alternates = effective_overlays_details(locale, args.i18n_dir, args.corpus)
            stale = sorted(set(rows) - set(canonical))
            states = locale_states(canonical, rows, strict_ids, locale, provenance)
            results[locale] = states
            documents[locale] = overlay_document(locale, canonical, rows, states, utc_text(now), at, provenance, alternates)
            documents[locale]["_stale_ids"] = stale
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR {type(exc).__name__}", file=sys.stderr)
        print(str(exc)[:300], file=sys.stderr)
        return 2

    summaries = {locale: summarize(states) for locale, states in results.items()}
    incomplete = sum(s["pending"] + s["failed"] for s in summaries.values())
    complete = sum(s["complete"] for s in summaries.values())
    print(f"INCOMPLETE {incomplete}" if incomplete else f"COMPLETE {complete}")
    for locale, summary in summaries.items():
        print(
            f"locale={locale} stories={summary['stories']} complete={summary['complete']} "
            f"pending={summary['pending']} failed={summary['failed']} states={summary['state_counts']}"
        )
    for locale, states in results.items():
        for rid, status in states.items():
            if status["state"] == "PENDING":
                print(f"PENDING {locale} {rid} missing={','.join(status['missing'])}")
            elif status["state"] == "FAILED":
                print(f"FAILED {locale} {rid} gate={status['failure']['gate']}")
        stale = documents[locale].pop("_stale_ids")
        for rid in stale:
            print(f"STALE {locale} {rid} (overlay for an id that is not live; ignored)")

    if args.write_overlays:
        args.write_overlays.mkdir(parents=True, exist_ok=True)
        for locale, doc in documents.items():
            (args.write_overlays / f"{locale}.json").write_text(
                json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    if args.json:
        print(json.dumps({"locales": summaries}, ensure_ascii=False, sort_keys=True))
    return 1 if incomplete else 0


def legacy_main(args: argparse.Namespace) -> int:
    canonical = canonical_records(args.site)
    expected = set(canonical)
    errors: list[str] = []
    receipt_records: dict[str, Any] = {}
    strict_pairs = 0
    historical_pairs = 0
    field_incomplete: dict[str, list[str]] = {}
    for locale in LOCALES:
        rows, strict_ids, provenance, alternates = load_locale_details(args.i18n_dir, locale)
        missing = expected - set(rows)
        stale = set(rows) - expected
        if missing:
            errors.append(f"{locale}: missing canonical ids {sorted(missing)}")
        if stale:
            errors.append(f"{locale}: stale/non-canonical ids {sorted(stale)}")
        field_incomplete[locale] = []
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
            status = pair_status(canonical[rid], overlay, locale, strict=rid in strict_ids,
                                 provenance=provenance.get(rid))
            if not is_complete(status):
                field_incomplete[locale].append(rid)
            receipt_records.setdefault(rid, {})[locale] = {
                "canonical_digest": stable_digest(translated_projection(canonical[rid])),
                "locale_digest": stable_digest(overlay),
                "validation_tier": tier,
                "state": status["state"],
                "missing": status["missing"],
                "provenance": provenance.get(rid, {}),
                "alternates": alternates.get(rid, {}),
            }

    if errors:
        raise SystemExit("localization integrity FAILED:\n" + "\n".join(f"- {x}" for x in errors))
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    incomplete_ids = sorted(set().union(*field_incomplete.values()))
    receipt = {
        "schema": "fcmo-locale-integrity-v2",
        "canonical_locale": "en",
        "required_locales": list(LOCALES),
        "editorial_owner": "FCMO Publication Desk for es-419 and zh-Hans; ARB locale deltas imported when present; historical packs preserved as published",
        "human_reviewed": False,
        "network_translation": False,
        "strict_airlock_pairs": strict_pairs,
        "historical_structural_pairs": historical_pairs,
        "field_incomplete_by_locale": field_incomplete,
        "field_complete_story_count": len(expected) - len(incomplete_ids),
        "records": receipt_records,
        "state_counts": {loc: {state: sum(row[loc]["state"] == state for row in receipt_records.values()
                                           if loc in row)
                                for state in (*COMPLETE_STATES, *INCOMPLETE_STATES)} for loc in LOCALES},
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    counts = " ".join(f"{loc}={len(expected) - len(ids)}/{len(expected)}" for loc, ids in field_incomplete.items())
    print(
        f"localization integrity OK; stories={len(expected)}; locales={','.join(LOCALES)}; "
        f"strict={strict_pairs}; historical={historical_pairs}; field_complete {counts}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="field-level completeness against --corpus")
    parser.add_argument("--corpus", type=Path, default=Path("corpus"))
    parser.add_argument("--locale", choices=("all", *LOCALES), default="all")
    parser.add_argument("--write-overlays", type=Path, default=None, metavar="DIR")
    parser.add_argument("--json", action="store_true", help="also print a JSON summary line")
    parser.add_argument("--now", default=None)
    parser.add_argument("--site", type=Path, default=Path("release-src"))
    parser.add_argument("--i18n-dir", type=Path, default=Path("site/data/i18n"))
    parser.add_argument("--receipt", type=Path, default=Path("site/data/i18n/integrity-manifest.json"))
    args = parser.parse_args(argv)
    if args.strict:
        return strict_main(args)
    return legacy_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
