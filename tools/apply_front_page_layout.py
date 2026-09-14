#!/usr/bin/env python3
"""Attach durable current-corpus presentation fixes to an assembled Pages tree.

The frozen release overlay owns canonical content/runtime bytes. Additive
presentation patches are source-controlled under ``tools/`` and injected inline
only into the assembled candidate, so newsroom refreshes cannot erase them and no
orphaned public asset changes the release receipt's file count.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES = (
    REPO / "tools" / "newsletter-current-corpus.css",
    REPO / "tools" / "newsletter-mobile-overflow.css",
)
MARKER = 'data-fcmo-current-corpus="v4.2.4"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("publish"))
    args = parser.parse_args()
    root = args.site.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise SystemExit("front-page layout refused: index.html is missing")
    missing = [path for path in SOURCES if not path.is_file()]
    if missing:
        raise SystemExit(f"front-page layout refused: source CSS is missing: {missing}")

    text = index.read_text(encoding="utf-8")
    css = "\n\n".join(path.read_text(encoding="utf-8").strip() for path in SOURCES)
    tag = f'<style {MARKER}>\n{css}\n</style>'

    # Remove a previously injected current-corpus style block when rebuilding an
    # older assembled tree. The style is deterministic build state, not canonical
    # editorial content, so upgrading v4.2.x must replace rather than stack it.
    start = text.find('<style data-fcmo-current-corpus="')
    if start != -1:
        end = text.find('</style>', start)
        if end == -1:
            raise SystemExit("front-page layout refused: unterminated existing current-corpus style")
        text = text[:start] + text[end + len('</style>'):]

    if "</head>" not in text:
        raise SystemExit("front-page layout refused: index.html has no closing head")
    text = text.replace("</head>", tag + "\n</head>", 1)
    index.write_text(text, encoding="utf-8", newline="\n")
    print("current-corpus front-page layout attached inline: v4.2.4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
