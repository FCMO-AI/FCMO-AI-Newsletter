"""Corpus titles and accented organizations must not produce false release failures."""
from pathlib import Path
import tempfile
import unittest

from tools.gates import binding_complete
from tools.gates.common import GateFailure


class CorpusGateRegression(unittest.TestCase):
    def test_evidence_word_at_end_of_title_is_not_an_empty_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'index.html').write_text(
                '<title>Reports are independent evidence — FCMO AI</title>'
                '<meta property="og:title" content="Reports are independent evidence — FCMO AI">'
                '<h1>报告被视为独立证据 — FCMO AI</h1>')
            binding_complete.check(root)

    def test_an_empty_evidence_label_still_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for content in ('<p>EVIDENCE — </p>', '<dt>Evidence</dt><dd>—</dd>',
                            '<p>Evidence —<span> </span></p>', '<p>证据 — </p>'):
                (root / 'index.html').write_text(content)
                with self.assertRaises(GateFailure):
                    binding_complete.check(root)

    def test_agent_and_reader_use_identical_accented_organization_routes(self):
        from tools.paper.routes import slugify
        for name, expected in [('Siloé', 'siloé'), ('José Alejandro Aguilar López', 'josé-alejandro-aguilar-lópez'),
                               ('Cámara de Diputados', 'cámara-de-diputados')]:
            self.assertEqual(slugify(name), expected)


if __name__ == '__main__':
    unittest.main()
