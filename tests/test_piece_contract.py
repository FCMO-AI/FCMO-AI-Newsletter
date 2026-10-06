import json
import unittest
from pathlib import Path

from tests.harness.validate import Validator

ROOT = Path(__file__).resolve().parents[1]


class PieceContractTests(unittest.TestCase):
    def test_fixture_matches_closed_piece_schema(self):
        schema = json.loads((ROOT / "contracts/piece.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/fixtures/piece.v1/fixture-essay/piece.json").read_text())
        self.assertEqual(Validator(schema).errors(fixture), [])

    def test_unknown_piece_fields_are_rejected(self):
        schema = json.loads((ROOT / "contracts/piece.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/fixtures/piece.v1/fixture-essay/piece.json").read_text())
        fixture["debug"] = True
        self.assertTrue(Validator(schema).errors(fixture))

    def test_document_schema_rejects_unknown_node_and_javascript_link(self):
        schema = json.loads((ROOT / "contracts/essay-doc.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/fixtures/piece.v1/fixture-essay/doc.en.json").read_text())
        self.assertTrue(Validator(schema).errors({**fixture, "blocks": [{"id": "b-12345678", "type": "raw_html"}]}))
        bad = json.loads(json.dumps(fixture))
        bad["blocks"][0]["content"] = [{"t": "link", "href": "javascript:alert(1)", "c": [{"t": "text", "v": "x"}]}]
        self.assertTrue(Validator(schema).errors(bad))

    def test_issue_fixture_matches_closed_schema(self):
        schema = json.loads((ROOT / "contracts/issue.v1.schema.json").read_text())
        fixture = json.loads((ROOT / "contracts/fixtures/piece.v1/fixture-essay/issue.json").read_text())
        self.assertEqual(Validator(schema).errors(fixture), [])


if __name__ == "__main__":
    unittest.main()
