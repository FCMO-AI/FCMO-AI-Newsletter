from __future__ import annotations

import re
from pathlib import Path

from .common import GateFailure, GateResult, canonical_story_path, fail, live_stories, story_routes

CODE = "LOCALE_COMPLETE"
COMPLETE = {"NATIVE_ARB", "MACHINE_REVIEWED"}
PENDING_COPY = {"es-419": "Traducción pendiente", "zh-Hans": "翻译待完成"}
PROSE_KEYS = ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale", "technical", "evidence", "related")
NON_PROSE_KEYS = frozenset({
    "label", "qualifier", "kind", "state", "updated_at", "target_id", "type", "id",
    "url", "source_url",
})


def prose_leaves(value, path=()):
    """Yield non-empty reader-facing strings, excluding codes and identifiers."""
    if isinstance(value, str):
        if value.strip():
            yield path, value
    elif isinstance(value, dict):
        for key in sorted(value):
            if key not in NON_PROSE_KEYS:
                yield from prose_leaves(value[key], path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from prose_leaves(item, path + (index,))


def localized_leaves(fields):
    """Flatten localized fields while supporting title/summary display fallbacks."""
    fields = fields if isinstance(fields, dict) else {}
    normalized = dict(fields)
    if "headline" not in normalized and "title" in normalized:
        normalized["headline"] = normalized["title"]
    if "dek" not in normalized and "summary" in normalized:
        normalized["dek"] = normalized["summary"]
    return dict(prose_leaves(normalized))


def check(root: Path) -> GateResult:
    try:
        document, stories = live_stories(root)
    except GateFailure:
        problems = []; rows = story_routes(root)
        for row in rows:
            locale = row.get("locale")
            if locale not in {"es-419", "zh-Hans"}: continue
            route = str(row.get("path") or "").lstrip("/")
            route = route if route.endswith("index.html") else route.rstrip("/") + "/index.html"
            page = root / route
            if not page.is_file(): continue
            text = page.read_text(encoding="utf-8", errors="replace")
            if not re.search(rf'<html\b[^>]*\blang=["\']{re.escape(locale)}["\']', text, re.I):
                problems.append(f"{route}: html lang is not {locale}")
            if "pending-panel" in text and PENDING_COPY[locale] not in text:
                problems.append(f"{route}: pending page lacks its localized notice")
        fail(CODE, problems)
        return GateResult(CODE, sum(row.get("locale") in {"es-419", "zh-Hans"} for row in rows),
                          ("output-only mode: locale parity comes from data/routes.json",))
    # Legacy is accepted only for rebuilding a previously verified LKG tag.
    if document.get("schema") == "legacy-story-list":
        return GateResult(CODE, len(stories), ("legacy LKG: locale completeness was established by its original release gates",))
    problems = []
    checked = 0
    required_leaves = 0
    coverage = {locale: {"complete": 0, "incomplete": 0, "missing_leaves": 0}
                for locale in ("es-419", "zh-Hans")}
    for story in stories:
        rid = story.get("id", "<missing>")
        source = {key: story[key] for key in PROSE_KEYS if key in story}
        source_leaves = dict(prose_leaves(source))
        l10n = story.get("l10n") if isinstance(story.get("l10n"), dict) else {}
        for locale in ("es-419", "zh-Hans"):
            checked += 1
            required_leaves += len(source_leaves)
            item = l10n.get(locale) if isinstance(l10n.get(locale), dict) else {}
            state = item.get("state")
            missing = item.get("missing")
            fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
            if state not in {"NATIVE_ARB", "MACHINE_REVIEWED", "PENDING", "FAILED"}:
                problems.append(f"{rid}/{locale}: invalid locale state {state!r}")
                continue
            if not isinstance(missing, list):
                problems.append(f"{rid}/{locale}: missing[] absent")
                continue
            translated_leaves = localized_leaves(fields)
            missing_paths = [path for path in source_leaves if path not in translated_leaves]
            coverage[locale]["missing_leaves"] += len(missing_paths)
            if state in COMPLETE and missing_paths:
                labels = [".".join(str(part) for part in path) for path in missing_paths[:12]]
                suffix = " …" if len(missing_paths) > len(labels) else ""
                problems.append(
                    f"{rid}/{locale}: {state} omits {len(missing_paths)} prose leaves: {', '.join(labels)}{suffix}"
                )
            pair_complete = state in COMPLETE and not missing_paths and not missing
            if pair_complete:
                coverage[locale]["complete"] += 1
            else:
                coverage[locale]["incomplete"] += 1
            if state in COMPLETE:
                if missing:
                    problems.append(f"{rid}/{locale}: {state} has missing={missing!r}")
            route = canonical_story_path(story, locale)
            page = root / route if route else None
            if not page or not page.is_file():
                continue  # ID_SET_EQUALITY owns route absence.
            text = page.read_text(encoding="utf-8", errors="replace")
            expected_lang = locale
            if not re.search(rf'<html\b[^>]*\blang=["\']{re.escape(expected_lang)}["\']', text, re.I):
                problems.append(f"{route}: html lang is not {expected_lang}")
            pending_panel = re.search(r'<[^>]+class=["\'][^"\']*\bpending-panel\b[^"\']*["\'][^>]*>[\s\S]*?</[^>]+>', text, re.I)
            if state in {"PENDING", "FAILED"} and (not pending_panel or PENDING_COPY[locale] not in pending_panel.group(0)):
                problems.append(f"{route}: {state} is not visibly marked pending")
            if state in COMPLETE and pending_panel:
                problems.append(f"{route}: complete locale renders a pending panel")
    detail = tuple(
        f"{locale}: complete={counts['complete']} incomplete={counts['incomplete']} "
        f"missing_prose_leaves={counts['missing_leaves']}"
        for locale, counts in coverage.items()
    )
    if problems:
        fail(CODE, (*problems, *(f"coverage {row}" for row in detail)))
    return GateResult(CODE, required_leaves, detail)


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} prose leaves across locale pairs)")
    for warning in result.warnings:
        print(f"{result.code} INFO: {warning}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
