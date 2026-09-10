#!/usr/bin/env python3
"""Apply the approved 2026-09-10 Newsletter visual maintenance migration once.

The migration preserves the existing app/corpus and makes only the approved
presentation changes: responsive viewport polish, two thumbnail collision fixes,
Front Page copy, and removal of reader-facing FCMO Wire navigation if present.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INDEX = REPO / "release-src" / "index.html"
STYLE_HREF = "assets/newsletter-responsive-polish.css"
MANIFEST = REPO / "release-overlay" / "final" / "manifest.json"
HANDOFF = REPO / "HANDOFF.md"
RELEASE = "signal-field-v4.1.1-viewport-polish"

NEW_HEADING = "What else <em>matters now.</em>"
NEW_DECK = (
    "Five consequential developments beyond the lead, ranked by editorial importance. "
    "Each opens into the evidence, mechanisms, caveats and sources behind the signal."
)
OLD_HEADINGS = ("A newspaper, not a <em>landing page.</em>",)
OLD_DECKS = (
    "Visuals identify and clarify stories; the hierarchy still comes from editorial consequence and evidence.",
    "The front page prioritizes; it does not hide the rest. Every story opens into a dossier and the complete corpus is always one click away.",
)
TRANSLATIONS = {
    "es-419": {
        "What else matters now.": "Qué más importa ahora.",
        "What else": "Qué más",
        "matters now.": "importa ahora.",
        NEW_DECK: (
            "Cinco desarrollos de peso más allá de la señal principal, priorizados por importancia editorial. "
            "Cada uno abre la evidencia, los mecanismos, las salvedades y las fuentes detrás de la señal."
        ),
    },
    "zh-Hans": {
        "What else matters now.": "现在还有什么值得关注。",
        "What else": "还有什么",
        "matters now.": "现在值得关注。",
        NEW_DECK: "除主信号之外的五项重要进展，按编辑重要性排序。每一项都可深入查看该信号背后的证据、机制、限制与来源。",
    },
}
NOTE_HEADING = "## 7. Visual maintenance — 2026-09-10"
NOTE = f"""{NOTE_HEADING}

An intentional **bug fix + mild visual refinement** was approved for the public webapp. It is a forward presentation improvement, not a rollback or accidental regression: desktop composition now responds to viewport height as well as width, the cover uses its existing left field more deliberately, Front Page and Chronology thumbnail/text collisions are guarded at their actual local grid widths, and the Front Page section heading now describes the five next-ranked signals directly. Reader-facing **FCMO Wire** navigation is intentionally absent; the separate Newswire Bridge ingestion infrastructure is unaffected.

No research record, evidence status, dossier semantics, publication-memory rule, privacy boundary, or release gate is changed by this visual maintenance pass. The responsive behavior is protected by a browser-rendered layout oracle across mobile, short-laptop, standard desktop, and wide-desktop viewports."""


def replace_exact(text: str, old_values: tuple[str, ...], new_value: str, label: str) -> str:
    # Footnote: exact source strings are safer than broad prose regexes. If the
    # canonical scaffold drifts, fail visibly instead of rewriting nearby copy.
    hits = sum(text.count(value) for value in old_values)
    if hits == 0 and new_value not in text:
        raise RuntimeError(f"approved {label} source was not found")
    for value in old_values:
        text = text.replace(value, new_value)
    return text


def remove_reader_wire(text: str) -> tuple[str, int]:
    # Footnote: never match "Newswire". The ingestion bridge is infrastructure;
    # the approved deletion concerns only the reader-facing FCMO Wire control.
    patterns = (
        re.compile(r'<a\b(?=[^>]*\bdata-fcmo-wire-link(?:\s*=\s*["\'][^"\']*["\'])?)[^>]*>.*?</a>', re.I | re.S),
        re.compile(r'<button\b(?=[^>]*\bdata-fcmo-wire-link(?:\s*=\s*["\'][^"\']*["\'])?)[^>]*>.*?</button>', re.I | re.S),
        re.compile(r'<a\b[^>]*>\s*FCMO\s+Wire\s*</a>', re.I),
        re.compile(r'<button\b[^>]*>\s*FCMO\s+Wire\s*</button>', re.I),
    )
    removed = 0
    for pattern in patterns:
        text, count = pattern.subn("", text)
        removed += count
    return text, removed


def ensure_stylesheet(text: str) -> str:
    if STYLE_HREF in text:
        return text
    close = text.lower().find("</head>")
    if close < 0:
        raise RuntimeError("release-src/index.html has no </head>")
    # Footnote: the visual delta lives in one local stylesheet so future corpus
    # ingestion keeps the hand-authored scaffold while the override remains easy
    # to inspect or retire. This adds no remote dependency.
    link = f'\n<link rel="stylesheet" href="{STYLE_HREF}">\n'
    return text[:close] + link + text[close:]


def update_locales() -> None:
    for locale, additions in TRANSLATIONS.items():
        path = REPO / "site" / "data" / "i18n" / locale / "ui.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        ui = data.get("ui")
        if not isinstance(ui, dict):
            raise RuntimeError(f"{path} has no ui object")
        ui.update(additions)
        # Footnote: do not sort/rebuild the catalogue. Preserve existing human
        # review order and append only the newly introduced source strings.
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    text = INDEX.read_text(encoding="utf-8")
    text = replace_exact(text, OLD_HEADINGS, NEW_HEADING, "Front Page heading")
    text = replace_exact(text, OLD_DECKS, NEW_DECK, "Front Page deck")
    text, removed_wire = remove_reader_wire(text)
    text = ensure_stylesheet(text)
    INDEX.write_text(text, encoding="utf-8")

    update_locales()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["release"] = RELEASE
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    handoff = HANDOFF.read_text(encoding="utf-8").rstrip()
    if NOTE_HEADING not in handoff:
        HANDOFF.write_text(handoff + "\n\n" + NOTE + "\n", encoding="utf-8")

    print(f"visual maintenance applied; scoped FCMO Wire controls removed={removed_wire}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
