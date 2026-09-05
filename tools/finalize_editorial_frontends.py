#!/usr/bin/env python3
"""Final consistency pass over generated editorial-discovery HTML.

The discovery builder is intentionally independent of the Story builder. This pass
binds their route contracts, writes path-accurate canonical URLs and rejects remote
executable dependencies before Pages can see the result.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

BASE_URL = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
CANONICAL = re.compile(r'<link rel="canonical" href="[^"]*">', re.I)
REMOTE_EXEC = re.compile(r'<(?:script|link)\b[^>]+(?:src|href)="https?://', re.I)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"))
    args = parser.parse_args(argv)
    root = args.site
    targets = [
        root / name for name in (
            "archive.html", "search.html", "topics.html", "organizations.html",
            "corrections.html", "feeds.html", "methodology.html", "editorial-policy.html",
            "automation.html", "accessibility.html", "status.html", "404.html",
        )
    ]
    targets += sorted((root / "topics").glob("*.html"))
    targets += sorted((root / "organizations").glob("*.html"))
    targets += [root / "news" / "index.html"]

    errors: list[str] = []
    touched = 0
    for path in targets:
        if not path.is_file():
            errors.append(f"missing generated frontend: {path.relative_to(root)}")
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        # Footnote: the Story builder's stable route is `news/en/FCMO-*.html`.
        # Repairing this before publication also protects no-JS readers/crawlers.
        text = text.replace("/news/en/STORY-", "/news/en/FCMO-")
        canonical = f'{BASE_URL}/{rel}'
        replacement = f'<link rel="canonical" href="{canonical}">'
        if CANONICAL.search(text):
            text = CANONICAL.sub(replacement, text, count=1)
        else:
            text = text.replace("</head>", replacement + "</head>", 1)
        if REMOTE_EXEC.search(text):
            errors.append(f"{rel}: remote executable/style dependency detected")
        path.write_text(text, encoding="utf-8")
        touched += 1

    if errors:
        raise SystemExit("editorial frontend finalization FAILED:\n" + "\n".join(f"- {x}" for x in errors))
    print(f"editorial frontend finalization OK; pages={touched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
