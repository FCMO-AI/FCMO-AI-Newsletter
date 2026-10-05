from __future__ import annotations

import re
from pathlib import Path

from .common import GateFailure, GateResult, canonical_story_path, fail, live_stories, public_files, rel, story_routes

CODE = "ID_SET_EQUALITY"
ID_MARKER = re.compile(r'\bdata-story-id=["\'](FCMO-[0-9A-F]{12})["\']', re.I)
DATED_ROUTE = re.compile(r"^(?:(?:es|zh)/)?20\d\d/\d\d/\d\d/[^/]+/index\.html$")


def check(root: Path) -> GateResult:
    expected: dict[str, str] = {}
    problems: list[str] = []
    ids: set[str] = set()
    try:
        _, stories = live_stories(root)
    except GateFailure:
        stories = []
        rows = story_routes(root)
        pairs = set()
        for row in rows:
            rid, locale = str(row.get("story_id") or ""), str(row.get("locale") or "")
            route = str(row.get("path") or "").lstrip("/")
            route = route if route.endswith("index.html") else route.rstrip("/") + "/index.html"
            if not rid or locale not in {"en", "es-419", "zh-Hans"} or not DATED_ROUTE.fullmatch(route):
                problems.append(f"data/routes.json: invalid story route {row!r}")
                continue
            if (rid, locale) in pairs: problems.append(f"duplicate story route for {rid}/{locale}")
            pairs.add((rid, locale)); ids.add(rid); expected[route] = rid
        wanted = {(rid, locale) for rid in ids for locale in ("en", "es-419", "zh-Hans")}
        if pairs != wanted:
            problems.append(f"route locale parity mismatch: missing={sorted(wanted-pairs)} extra={sorted(pairs-wanted)}")
    else:
        for story in stories:
            rid = str(story.get("id") or "")
            if not rid or rid in ids:
                problems.append(f"duplicate or missing live story id: {rid or '<empty>'}")
                continue
            ids.add(rid)
            for locale in ("en", "es-419", "zh-Hans"):
                route = canonical_story_path(story, locale)
                if not route:
                    problems.append(f"{rid}: cannot derive {locale} route")
                else:
                    expected[route] = rid

    for route, rid in expected.items():
        page = root / route
        if not page.is_file():
            problems.append(f"{route}: missing live story route for {rid}")
            continue
        text = page.read_text(encoding="utf-8", errors="replace")
        markers = set(ID_MARKER.findall(text))
        if markers and markers != {rid}:
            problems.append(f"{route}: story marker {sorted(markers)} != {rid}")

    for page in public_files(root, {".html"}):
        route = rel(root, page)
        text = page.read_text(encoding="utf-8", errors="replace")
        markers = set(ID_MARKER.findall(text))
        for rid in markers - ids:
            problems.append(f"{route}: orphan story marker {rid}")
        if DATED_ROUTE.fullmatch(route) and route not in expected:
            problems.append(f"{route}: orphan canonical story route")

    fail(CODE, problems)
    return GateResult(CODE, len(expected))


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check(args.root)
    except GateFailure as exc:
        raise SystemExit(f"{exc.code} FAIL: {'; '.join(exc.problems)}") from exc
    print(f"{result.code} PASS ({result.checked} routes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
