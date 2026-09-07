from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.synchronize_relationship_surfaces import synchronize


class RelationshipSurfaceTests(unittest.TestCase):
    def test_jsonl_is_rebuilt_from_exact_json_order(self) -> None:
        rows = [
            {"source_id": "FCMO-AAAAAAAAAAAA", "target_id": "FCMO-BBBBBBBBBBBB", "kind": "extends"},
            {"source_id": "FCMO-CCCCCCCCCCCC", "target_id": "FCMO-DDDDDDDDDDDD", "kind": "contrasts"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "data").mkdir()
            (site / "data" / "relationships.json").write_text(
                json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            # Footnote: begin from a deliberately stale, differently ordered JSONL
            # to reproduce the production failure that reached readiness receipt.
            (site / "data" / "relationships.jsonl").write_text(
                json.dumps(rows[1]) + "\n", encoding="utf-8"
            )
            self.assertEqual(synchronize(site), 2)
            roundtrip = [
                json.loads(line)
                for line in (site / "data" / "relationships.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(roundtrip, rows)

    def test_empty_relationship_set_is_valid_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "data").mkdir()
            (site / "data" / "relationships.json").write_text("[]\n", encoding="utf-8")
            self.assertEqual(synchronize(site), 0)
            self.assertEqual((site / "data" / "relationships.jsonl").read_text(encoding="utf-8"), "")

    def test_non_array_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            (site / "data").mkdir()
            (site / "data" / "relationships.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "array of JSON objects"):
                synchronize(site)


if __name__ == "__main__":
    unittest.main()
