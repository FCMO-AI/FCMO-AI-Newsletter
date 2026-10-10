import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from tools.gates import english_leak, piece_valid
from tools.gates.common import GateFailure
from tools.paper.build import PaperBuilder

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/editorial"


class PieceGateTests(unittest.TestCase):
    def build(self, out):
        PaperBuilder(stories_path=ROOT / "site/data/stories.v2.json",
                     status_path=ROOT / "site/data/newsroom-status.json",
                     editorial_path=FIXTURE, out=out, base="/FCMO-AI-Newsletter/").build()

    def test_complete_fixture_passes_piece_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            self.build(out)
            result = piece_valid.check(out)
            self.assertEqual(result.code, "PIECE_VALID")
            self.assertEqual(result.checked, 3)

    def test_defect_fixtures_fail_the_piece_gate(self):
        defects = ("unknown-node", "javascript-href", "id-mismatch", "figure-without-credit",
                   "footnote-without-body", "duplicate-block")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "clean-candidate"
            with mock.patch.object(self, "build", wraps=self.build) as build:
                self.build(template)
            build.assert_called_once_with(template)
            for defect in defects:
                with self.subTest(defect=defect):
                    out = root / defect
                    shutil.copytree(template, out)
                    piece_dir = out / "editorial/pieces/fixture-essay"
                    doc_path = piece_dir / "doc.es-419.json"
                    doc = json.loads(doc_path.read_text())
                    if defect == "unknown-node":
                        doc["blocks"][0]["type"] = "raw_html"
                    elif defect == "javascript-href":
                        doc["blocks"][1]["content"][0] = {"t": "link", "href": "javascript:alert(1)", "c": [{"t": "text", "v": "x"}]}
                    elif defect == "id-mismatch":
                        doc["blocks"][0]["id"] = "b-87654321"
                    elif defect == "figure-without-credit":
                        figures_path = piece_dir / "figures.json"
                        figures = json.loads(figures_path.read_text())
                        figures["fig-cover"].pop("credit")
                        figures_path.write_text(json.dumps(figures))
                    elif defect == "footnote-without-body":
                        doc["footnotes"] = {}
                    elif defect == "duplicate-block":
                        doc["blocks"][1]["id"] = doc["blocks"][0]["id"]
                    doc_path.write_text(json.dumps(doc))
                    with self.assertRaises(GateFailure) as caught:
                        piece_valid.check(out)
                    self.assertEqual(caught.exception.code, "PIECE_VALID")

    def test_unmarked_english_still_fails_but_structured_lang_quote_is_exempt(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            self.build(out)
            page = out / "es/cartas/fixture-essay/index.html"
            html = page.read_text()
            html = html.replace("Un registro público duradero ayuda a tomar decisiones cuidadosas.",
                                "This is English prose that remains a release defect.")
            page.write_text(html)
            with self.assertRaises(GateFailure) as caught:
                english_leak.check(out)
            self.assertEqual(caught.exception.code, "ENGLISH_LEAK")
            html = page.read_text().replace("This is English prose that remains a release defect.",
                                            '<span class="quote-orig" lang="en" translate="no" data-field="quotation">This is an original English quotation from the source.</span>')
            page.write_text(html)
            english_leak.check(out)


if __name__ == "__main__":
    unittest.main()
