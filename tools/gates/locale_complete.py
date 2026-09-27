from __future__ import annotations

import re
from pathlib import Path

from .common import GateFailure, GateResult, canonical_story_path, fail, live_stories

CODE = "LOCALE_COMPLETE"
COMPLETE = {"NATIVE_ARB", "MACHINE_REVIEWED"}
PENDING_COPY = {"es-419": "Traducción pendiente", "zh-Hans": "翻译待完成"}
PROSE_KEYS = ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale", "technical", "evidence")


def check(root: Path) -> GateResult:
    document, stories = live_stories(root)
    # Legacy is accepted only for rebuilding a previously verified LKG tag.
    if document.get("schema") == "legacy-story-list":
        return GateResult(CODE, len(stories), ("legacy LKG: locale completeness was established by its original release gates",))
    problems = []
    checked = 0
    for story in stories:
        rid = story.get("id", "<missing>")
        l10n = story.get("l10n") if isinstance(story.get("l10n"), dict) else {}
        for locale in ("es-419", "zh-Hans"):
            checked += 1
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
            if state in COMPLETE:
                absent = [key for key in PROSE_KEYS if key in story and not fields.get(key)]
                if missing or absent:
                    problems.append(f"{rid}/{locale}: {state} has missing={missing!r}, absent={absent!r}")
            route = canonical_story_path(story, locale)
            page = root / route if route else None
            if not page or not page.is_file():
                continue  # ID_SET_EQUALITY owns route absence.
            text = page.read_text(encoding="utf-8", errors="replace")
            expected_lang = locale
            if not re.search(rf'<html\b[^>]*\blang=["\']{re.escape(expected_lang)}["\']', text, re.I):
                problems.append(f"{route}: html lang is not {expected_lang}")
            if state in {"PENDING", "FAILED"} and PENDING_COPY[locale] not in text:
                problems.append(f"{route}: {state} is not visibly marked pending")
            if state in COMPLETE and PENDING_COPY[locale] in text:
                problems.append(f"{route}: complete locale still renders the pending notice")
    fail(CODE, problems)
    return GateResult(CODE, checked)


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} locale pairs)"); return 0


if __name__ == "__main__": raise SystemExit(main())
