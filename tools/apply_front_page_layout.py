#!/usr/bin/env python3
"""Attach the durable current-corpus front-page layout to an assembled Pages tree.

The frozen release overlay owns canonical content/runtime bytes. The additive
presentation patch is source-controlled under ``tools/`` and injected inline only
into the assembled candidate, so newsroom refreshes cannot erase it and no orphaned
public asset changes the release receipt's file count.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "tools" / "newsletter-current-corpus.css"
MARKER = 'data-fcmo-current-corpus="v4.2.3"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("publish"))
    args = parser.parse_args()
    root = args.site.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise SystemExit("front-page layout refused: index.html is missing")
    if not SOURCE.is_file():
        raise SystemExit("front-page layout refused: source CSS is missing")

    text = index.read_text(encoding="utf-8")
    css = SOURCE.read_text(encoding="utf-8").strip()
    tag = f'<style {MARKER}>\n{css}\n</style>'
    if MARKER in text:
        if tag not in text:
            raise SystemExit("front-page layout refused: marker exists with unexpected content")
        print("current-corpus front-page layout already attached")
        return 0
    if "</head>" not in text:
        raise SystemExit("front-page layout refused: index.html has no closing head")
    text = text.replace("</head>", tag + "\n</head>", 1)
    index.write_text(text, encoding="utf-8", newline="\n")
    print("current-corpus front-page layout attached inline: v4.2.3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
