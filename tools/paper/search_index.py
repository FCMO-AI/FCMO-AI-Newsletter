"""Compact, lazy-loaded search shards with a hard per-file byte budget."""

from __future__ import annotations

import json
from pathlib import Path

from .i18n import dek, headline
from .routes import href, story_path

LIMIT = 150 * 1024


def build(stories: list[dict], *, locale: dict, catalog: dict, base: str, out: Path,
          extra_rows: list[dict] | None = None) -> list[Path]:
    rows = []
    code = locale["code"]
    for story in sorted(stories, key=lambda s: (s.get("event_at", ""), s["id"]), reverse=True):
        if story.get("status") != "live":
            continue
        rows.append({
            "h": headline(story, code, catalog),
            "d": dek(story, code, catalog),
            "u": href(base, story_path(locale, story)),
            "b": catalog.get("labels", {}).get("beat", {}).get(story.get("beat"), ""),
            "o": story.get("organizations", []),
            "t": story.get("topics", []),
        })
    return write_shards(rows + (extra_rows or []), out=out)


def write_shards(rows: list[dict], *, out: Path) -> list[Path]:
    """Pack complete UTF-8 rows, including commas/brackets, without dropping text.

    The first shard stays a JSON array at search.json for existing readers.
    Corpus cardinality is unbounded; a single row must still fit the budget.
    Validate all rows before replacing any previously generated shards.
    """
    shards: list[list[bytes]] = [[]]
    size = 2  # JSON array brackets, including the empty-corpus case.
    for row in rows:
        encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) + 2 > LIMIT:
            raise ValueError(f"search row exceeds {LIMIT} bytes for {row.get('u', '')}: {len(encoded) + 2}")
        added = len(encoded) + bool(shards[-1])
        if size + added > LIMIT:
            shards.append([])
            size = 2
            added = len(encoded)
        shards[-1].append(encoded)
        size += added
    out.parent.mkdir(parents=True, exist_ok=True)
    # Rebuilding a smaller corpus must not leave obsolete served fragments.
    for path in out.parent.glob(f"{out.stem}-*{out.suffix}"):
        if path.stem.removeprefix(out.stem + "-").isdigit():
            path.unlink()
    paths = []
    for number, shard in enumerate(shards, 1):
        path = out if number == 1 else out.with_name(f"{out.stem}-{number}{out.suffix}")
        path.write_bytes(b"[" + b",".join(shard) + b"]")
        paths.append(path)
    return paths
