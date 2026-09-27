from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".jsonl", ".md", ".txt", ".xml"}
LOCALE_PREFIX = {"en": "", "es-419": "es", "zh-Hans": "zh"}


@dataclass(frozen=True)
class GateResult:
    code: str
    checked: int
    warnings: tuple[str, ...] = ()


class GateFailure(ValueError):
    def __init__(self, code: str, problems: Iterable[str]):
        self.code = code
        self.problems = tuple(str(problem) for problem in problems)
        super().__init__(f"{code}: " + "; ".join(self.problems))


def fail(code: str, problems: Iterable[str]) -> None:
    items = tuple(problems)
    if items:
        raise GateFailure(code, items)


def public_files(root: Path, suffixes: set[str] | None = None) -> list[Path]:
    wanted = TEXT_SUFFIXES if suffixes is None else suffixes
    return [path for path in sorted(root.rglob("*")) if path.is_file() and path.suffix.lower() in wanted]


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def story_document(root: Path) -> tuple[Path, dict]:
    candidates = (root / "data" / "stories.v2.json", root / "data" / "stories.json")
    errors: list[str] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            value = read_json(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{rel(root, path)}: {exc}")
            continue
        if isinstance(value, dict) and isinstance(value.get("stories"), list):
            return path, value
        if isinstance(value, list):
            # Read-only compatibility for the pre-SSG LKG. New builds must emit v2.
            normalized = []
            for row in value:
                if not isinstance(row, dict):
                    continue
                rid = row.get("id") or row.get("research_id")
                if rid:
                    normalized.append({**row, "id": rid, "status": row.get("status", "live")})
            return path, {"schema": "legacy-story-list", "stories": normalized}
        errors.append(f"{rel(root, path)}: expected an object with stories[]")
    detail = errors or ["missing data/stories.v2.json (or legacy data/stories.json for LKG rollback)"]
    raise GateFailure("ID_SET_EQUALITY", detail)


def live_stories(root: Path) -> tuple[dict, list[dict]]:
    _, document = story_document(root)
    rows = [row for row in document["stories"] if isinstance(row, dict)]
    return document, [row for row in rows if row.get("status", "live") == "live"]


def canonical_story_path(story: dict, locale: str) -> str | None:
    date = str(story.get("url_date") or "")
    slug = str(story.get("slug") or "")
    if len(date) == 10 and slug:
        parts = date.split("-")
        prefix = LOCALE_PREFIX[locale]
        route = "/".join(part for part in (prefix, *parts, slug, "index.html") if part)
        return route
    rid = str(story.get("id") or "")
    if rid:
        legacy_locale = {"en": "en", "es-419": "es", "zh-Hans": "zh-hans"}[locale]
        return f"news/{legacy_locale}/{rid}.html"
    return None

