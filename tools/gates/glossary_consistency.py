from __future__ import annotations

import json
import re
from pathlib import Path

from .common import GateFailure, GateResult, fail, live_stories, rel

CODE = "GLOSSARY_CONSISTENCY"


def contains(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    if re.search(r"[A-Za-z0-9]", phrase):
        return bool(re.search(rf"(?<![\w-]){escaped}(?![\w-])", text, re.I))
    return phrase in text


def glossary_path(root: Path) -> Path:
    for candidate in (root / "data" / "glossary.json", root.parent / "i18n" / "glossary.yml", Path("i18n/glossary.yml")):
        if candidate.is_file(): return candidate
    raise GateFailure(CODE, ["glossary not found (expected data/glossary.json or i18n/glossary.yml)"])


def check(root: Path) -> GateResult:
    path = glossary_path(root)
    try: doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc: raise GateFailure(CODE, [f"{path}: {exc}"]) from exc
    terms = doc.get("terms") if isinstance(doc, dict) else None
    if not isinstance(terms, list): raise GateFailure(CODE, ["glossary terms[] absent"])
    problems = []; seen_ids = set(); seen_en = set(); preferred = {"es-419": set(), "zh-Hans": set()}
    for term in terms:
        tid = term.get("id"); english = term.get("en")
        if not tid or tid in seen_ids: problems.append(f"duplicate/empty glossary id {tid!r}")
        if not english or english.casefold() in seen_en: problems.append(f"duplicate/empty English term {english!r}")
        seen_ids.add(tid); seen_en.add(str(english).casefold())
        for locale in preferred:
            value = term.get(locale)
            if not isinstance(value, str) or not value.strip(): problems.append(f"{tid}/{locale}: empty preferred form")
            else: preferred[locale].add(value.casefold())
    for term in terms:
        avoid = term.get("avoid") if isinstance(term.get("avoid"), dict) else {}
        for locale in preferred:
            for bad in avoid.get(locale, []):
                if str(bad).casefold() in preferred[locale]: problems.append(f"{term.get('id')}/{locale}: avoided form is preferred elsewhere: {bad}")

    warnings = []
    try: _, stories = live_stories(root)
    except GateFailure: stories = []
    by_locale = {locale: [] for locale in preferred}
    for story in stories:
        for locale in preferred:
            item = ((story.get("l10n") or {}).get(locale) or {})
            fields = item.get("fields") or {}; provenance = item.get("provenance") or {}
            for key, value in fields.items():
                values = [value] if isinstance(value, str) else []
                if isinstance(value, (dict, list)): values = [json.dumps(value, ensure_ascii=False)]
                for text in values: by_locale[locale].append((story.get("id"), key, provenance.get(key, "arb"), text))
    for term in terms:
        avoid = term.get("avoid") or {}
        for locale in preferred:
            for rid, field, origin, text in by_locale[locale]:
                for bad in avoid.get(locale, []):
                    if contains(text, bad):
                        message = f"{rid}/{locale}/{field}: {origin} uses avoided {bad!r}"
                        (warnings if origin == "arb" else problems).append(message)
    fail(CODE, problems)
    return GateResult(CODE, len(terms), tuple(warnings))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    try: result = check(args.root)
    except GateFailure as exc: raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    for warning in result.warnings: print(f"{result.code} WARN: {warning}")
    print(f"{result.code} PASS ({result.checked} terms)"); return 0


if __name__ == "__main__": raise SystemExit(main())
