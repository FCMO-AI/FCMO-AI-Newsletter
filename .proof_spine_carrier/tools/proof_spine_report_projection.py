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
import math
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


def assert_semantic_equivalence(left: Any, right: Any, path: str = "$") -> None:
    """Require identical JSON structure and meaning, ignoring numeric typography only."""
    if isinstance(left, dict) or isinstance(right, dict):
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise ProjectionError(f"{path}: one value is an object and the other is not")
        if set(left) != set(right):
            missing_left = sorted(set(right) - set(left))
            missing_right = sorted(set(left) - set(right))
            raise ProjectionError(
                f"{path}: object keys differ; only_left={missing_right!r} only_right={missing_left!r}"
            )
        for key in sorted(left):
            assert_semantic_equivalence(left[key], right[key], f"{path}.{key}")
        return

    if isinstance(left, list) or isinstance(right, list):
        if not isinstance(left, list) or not isinstance(right, list):
            raise ProjectionError(f"{path}: one value is a list and the other is not")
        if len(left) != len(right):
            raise ProjectionError(
                f"{path}: list lengths differ ({len(left)} != {len(right)})"
            )
        for index, (a, b) in enumerate(zip(left, right)):
            assert_semantic_equivalence(a, b, f"{path}[{index}]")
        return

    # Footnote: JSON numbers have one semantic category even though Python decodes
    # integer-looking and decimal-looking literals to int/float. Normalize only that
    # typography distinction; booleans are excluded explicitly so true cannot equal 1.
    numeric_left = isinstance(left, (int, float)) and not isinstance(left, bool)
    numeric_right = isinstance(right, (int, float)) and not isinstance(right, bool)
    if numeric_left or numeric_right:
        if not (numeric_left and numeric_right):
            raise ProjectionError(
                f"{path}: numeric/non-numeric type mismatch ({type(left).__name__} vs {type(right).__name__})"
            )
        if not (math.isfinite(float(left)) and math.isfinite(float(right))):
            raise ProjectionError(f"{path}: non-finite numbers are not valid portable JSON evidence")
        if float(left) != float(right):
            raise ProjectionError(
                f"{path}: numeric values differ ({left!r} != {right!r})"
            )
        return

    if type(left) is not type(right) or left != right:
        raise ProjectionError(
            f"{path}: values differ ({left!r} [{type(left).__name__}] != "
            f"{right!r} [{type(right).__name__}])"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("full", type=Path, help="Regenerated full JSON report")
    parser.add_argument("projection", type=Path, help="Preserved historical JSON artifact")
    parser.add_argument(
        "--exact-shape",
        action="store_true",
        help=(
            "Require identical JSON structure/values while treating integer/decimal "
            "spellings of the same finite JSON number as semantically equal."
        ),
    )
    args = parser.parse_args()

    full = json.loads(args.full.read_text(encoding="utf-8"))
    projection = json.loads(args.projection.read_text(encoding="utf-8"))
    if args.exact_shape:
        assert_semantic_equivalence(full, projection)
        print("JSON exact semantic equivalence PASS")
    else:
        assert_projection(full, projection)
        print("JSON projection equivalence PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
