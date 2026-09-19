#!/usr/bin/env python3
"""Assert that one JSON document is an exact semantic projection of another.

This exists for preserved historical Proof Spine summaries whose original artifact
intentionally omitted diagnostic detail that the full ledger already emitted. It is
strict about every value the historical artifact *does* claim; it only permits the
generated full report to contain additional dictionary keys.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class ProjectionError(ValueError):
    """Raised when a preserved JSON projection disagrees with its full source."""


def assert_projection(full: Any, projection: Any, path: str = "$") -> None:
    """Require every projected value to exist identically in the full document."""
    if isinstance(projection, dict):
        if not isinstance(full, dict):
            raise ProjectionError(
                f"{path}: projection is object but full value is {type(full).__name__}"
            )
        for key, projected_value in projection.items():
            if key not in full:
                raise ProjectionError(f"{path}.{key}: projected key missing from full report")
            assert_projection(full[key], projected_value, f"{path}.{key}")
        return

    if isinstance(projection, list):
        # Footnote: dictionary projection is intentional; list projection is not.
        # Permitting omitted/reordered list elements could hide event-level drift, so a
        # historical list must remain exactly equal when it is present in the artifact.
        if full != projection:
            raise ProjectionError(f"{path}: projected list differs from full report")
        return

    # Footnote: bool is a subclass of int in Python; direct JSON-value equality avoids
    # accidental numeric coercion and keeps null/string/boolean meanings exact.
    if type(full) is not type(projection) or full != projection:
        raise ProjectionError(
            f"{path}: projected value {projection!r} differs from full value {full!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("full", type=Path, help="Regenerated full JSON report")
    parser.add_argument("projection", type=Path, help="Preserved historical summary JSON")
    args = parser.parse_args()

    full = json.loads(args.full.read_text(encoding="utf-8"))
    projection = json.loads(args.projection.read_text(encoding="utf-8"))
    assert_projection(full, projection)
    print("JSON projection equivalence PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
