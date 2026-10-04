"""Validate published Studio pieces and their reader-facing routes."""
from __future__ import annotations

import json
from pathlib import Path

from .common import GateFailure, GateResult, fail
from tools.paper.essays import LOCALES, PREFIXES, load_editorial

CODE = "PIECE_VALID"


def check(root: Path) -> GateResult:
    editorial = root / "editorial"
    if not editorial.is_dir():
        return GateResult(CODE, 0)
    problems = []
    try:
        pieces, issues = load_editorial(editorial)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        fail(CODE, [str(exc)])
        raise AssertionError("unreachable")
    by_id = {piece["id"]: piece for piece in pieces}
    story_ids = set()
    stories_path = root / "data/stories.v2.json"
    if stories_path.is_file():
        try: story_ids = {row["id"] for row in json.loads(stories_path.read_text(encoding="utf-8")).get("stories", [])}
        except (OSError, ValueError, TypeError, KeyError): pass
    for piece in pieces:
        directory = piece["directory"]
        provenance_path = directory / "provenance.json"
        try:
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{provenance_path}: {exc}")
            continue
        for locale in LOCALES:
            if piece["locales"][locale] != "ready":
                continue
            row = provenance.get(locale, {})
            if row.get("origin") not in {"human_authored", "human_translated", "agent_draft_human_edited", "agent_draft"}:
                problems.append(f"{directory.name}: {locale} has unknown authorship provenance")
            if not isinstance(row.get("human_reviewed"), bool):
                problems.append(f"{directory.name}: {locale} is missing an explicit review state")
            if row.get("human_reviewed") is True and not row.get("reviewer", "").strip():
                problems.append(f"{directory.name}: {locale} has no named human reviewer")
            if row.get("origin") == "agent_draft" and row.get("human_reviewed") is not False:
                problems.append(f"{directory.name}: agent-drafted {locale} has dishonest review provenance")
            if row.get("human_reviewed") is not True and row.get("origin") not in {"agent_draft"}:
                problems.append(f"{directory.name}: ready {locale} is not marked human-reviewed")
            route = root / PREFIXES[locale] / "cartas" / piece["slug"] / "index.html"
            if not route.is_file():
                problems.append(f"{route.relative_to(root)}: published route is missing")
            else:
                html = route.read_text(encoding="utf-8", errors="replace")
                if piece["id"] not in html or 'class="essay' not in html:
                    problems.append(f"{route.relative_to(root)}: route identity does not match piece")
        for locale in LOCALES:
            if piece["locales"][locale] == "pending":
                route = root / PREFIXES[locale] / "cartas" / piece["slug"] / "index.html"
                if route.is_file() and "essay-pending" not in route.read_text(encoding="utf-8", errors="replace"):
                    problems.append(f"{route.relative_to(root)}: pending locale is not explicit")
    for issue in issues:
        for slot in issue["slots"]:
            if slot["ref"] not in by_id and slot["ref"] not in story_ids:
                problems.append(f"issue {issue['id']}: unknown item {slot['ref']}")
    fail(CODE, problems)
    return GateResult(CODE, len(pieces) + len(issues))


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    result = check(args.root)
    print(f"{result.code} PASS ({result.checked} editorial records)")
    return 0


if __name__ == "__main__": raise SystemExit(main())
