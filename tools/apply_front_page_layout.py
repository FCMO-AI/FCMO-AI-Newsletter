#!/usr/bin/env python3
"""Attach the durable current-corpus front-page layout to an assembled Pages tree.

The frozen release overlay owns canonical content/runtime bytes, while additive
responsive presentation lives under ``site/assets`` so newsroom refreshes cannot
erase it. This deterministic post-overlay step merely links that committed asset;
it does not generate or mutate editorial content.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ASSET = "assets/newsletter-current-corpus.css"
MARKER = 'data-fcmo-current-corpus="v4.2.2"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("publish"))
    args = parser.parse_args()
    root = args.site.resolve()
    index = root / "index.html"
    asset = root / ASSET
    if not index.is_file():
        raise SystemExit("front-page layout refused: index.html is missing")
    if not asset.is_file():
        raise SystemExit(f"front-page layout refused: {ASSET} is missing")

    text = index.read_text(encoding="utf-8")
    tag = f'<link rel="stylesheet" href="{ASSET}" {MARKER}>'
    if MARKER in text:
        if tag not in text:
            raise SystemExit("front-page layout refused: marker exists with unexpected tag")
        print("current-corpus front-page layout already attached")
        return 0
    if "</head>" not in text:
        raise SystemExit("front-page layout refused: index.html has no closing head")
    text = text.replace("</head>", tag + "</head>", 1)
    index.write_text(text, encoding="utf-8", newline="\n")
    print(f"current-corpus front-page layout attached: {ASSET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
