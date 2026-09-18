#!/usr/bin/env python3
"""Attach durable current-corpus presentation/freshness fixes to Pages.

The frozen release overlay owns canonical content/runtime bytes. Additive
post-overlay patches are source-controlled under ``tools/`` and injected inline
only into the assembled candidate, so newsroom refreshes cannot erase them and
research agents never need to curate presentation state.
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STYLE_SOURCES = (
    REPO / "tools" / "newsletter-current-corpus.css",
    REPO / "tools" / "newsletter-mobile-overflow.css",
    REPO / "tools" / "newsletter-autonomous-surfaces.css",
    REPO / "tools" / "newsletter-visual-regressions.css",
)
SCRIPT_SOURCE = REPO / "tools" / "newsletter-current-corpus.js"
STYLE_MARKER = 'data-fcmo-current-corpus="v4.3.2"'
SCRIPT_MARKER = 'data-fcmo-autonomous-surfaces="v1"'


def strip_tag(text: str, start_token: str, close_token: str) -> str:
    start = text.find(start_token)
    if start == -1:
        return text
    end = text.find(close_token, start)
    if end == -1:
        raise SystemExit(f"front-page layout refused: unterminated injected block {start_token}")
    return text[:start] + text[end + len(close_token):]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("publish"))
    args = parser.parse_args()
    root = args.site.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise SystemExit("front-page layout refused: index.html is missing")
    missing = [path for path in (*STYLE_SOURCES, SCRIPT_SOURCE) if not path.is_file()]
    if missing:
        raise SystemExit(f"front-page layout refused: source patch is missing: {missing}")

    text = index.read_text(encoding="utf-8")

    # The frozen overlay's D.meta.count is the Story-layer count, not the full
    # research-index count. Keep reader copy semantically honest so the front
    # page's ~40 curated stories does not contradict the ~200-record Library.
    text = text.replace(" public briefs</span>", " newsroom stories</span>")
    text = text.replace(
        "public briefs / complete corpus inside",
        "newsroom stories / full research library inside",
    )

    css = "\n\n".join(path.read_text(encoding="utf-8").strip() for path in STYLE_SOURCES)
    js = SCRIPT_SOURCE.read_text(encoding="utf-8").strip()
    style_tag = f'<style {STYLE_MARKER}>\n{css}\n</style>'
    script_tag = f'<script {SCRIPT_MARKER}>\n{js}\n</script>'

    # Build state is replaceable: an older assembled tree must never stack patches.
    text = strip_tag(text, '<style data-fcmo-current-corpus="', '</style>')
    text = strip_tag(text, '<script data-fcmo-autonomous-surfaces="', '</script>')

    if "</head>" not in text or "</body>" not in text:
        raise SystemExit("front-page layout refused: index.html lacks closing head/body")
    text = text.replace("</head>", style_tag + "\n</head>", 1)
    text = text.replace("</body>", script_tag + "\n</body>", 1)
    index.write_text(text, encoding="utf-8", newline="\n")
    print("current-corpus presentation/freshness attached inline: v4.3.2 / surfaces-v1 / visual-guards-v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
