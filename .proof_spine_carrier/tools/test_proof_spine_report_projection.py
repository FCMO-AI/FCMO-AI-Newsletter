#!/usr/bin/env python3
"""Regressions for strict historical JSON projection checking."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "proof_spine_report_projection",
    HERE / "proof_spine_report_projection.py",
)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
assert SPEC.loader is not None
SPEC.loader.exec_module(m)


class ProjectionTests(unittest.TestCase):
    def test_projection_may_omit_full_report_dictionary_detail(self) -> None:
        m.assert_projection(
            {"rate": 1.0, "events": [{"id": "e1"}], "nested": {"a": 1, "b": 2}},
            {"rate": 1.0, "nested": {"a": 1}},
        )

    def test_projection_cannot_change_claimed_scalar(self) -> None:
        with self.assertRaises(m.ProjectionError):
            m.assert_projection({"rate": 0.5}, {"rate": 1.0})

    def test_projection_cannot_claim_missing_key(self) -> None:
        with self.assertRaises(m.ProjectionError):
            m.assert_projection({"rate": 1.0}, {"specificity": None})

    def test_projection_lists_must_match_exactly(self) -> None:
        # Footnote: we allow missing dictionary fields, not selective event lists.
        with self.assertRaises(m.ProjectionError):
            m.assert_projection(
                {"events": [{"id": "a"}, {"id": "b"}]},
                {"events": [{"id": "a"}]},
            )

    def test_json_types_do_not_coerce(self) -> None:
        with self.assertRaises(m.ProjectionError):
            m.assert_projection({"value": 1}, {"value": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)
