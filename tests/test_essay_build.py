import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.paper.build import PaperBuilder
from tools.paper.essay_doc import render_document

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/editorial"


class EssayBuildTests(unittest.TestCase):
    def test_semantic_renderer_covers_node_types_and_escapes_text(self):
        document = {
            "schema": "fcmo-essay-doc-v1", "locale": "es-419", "title": "Ensayo", "dek": "",
            "blocks": [
                {"id": "b-00000001", "type": "p", "content": [{"t": "text", "v": "<script>alert(1)</script>", "marks": ["strong", "em"]}, {"t": "link", "href": "https://example.org/x", "c": [{"t": "text", "v": "fuente"}]}, {"t": "lang", "lang": "en", "c": [{"t": "text", "v": "Original words"}]}, {"t": "fn", "id": "fn-00000001"}, {"t": "cite", "key": "source-one"}]},
                {"id": "b-00000002", "type": "h2", "content": [{"t": "text", "v": "Sección"}]},
                {"id": "b-00000003", "type": "h3", "content": [{"t": "text", "v": "Subsección"}]},
                {"id": "b-00000004", "type": "blockquote", "content": [{"t": "text", "v": "Cita"}]},
                {"id": "b-00000005", "type": "pullquote", "content": [{"t": "text", "v": "Destacada"}]},
                {"id": "b-00000006", "type": "ul", "items": [[{"t": "text", "v": "Uno"}]]},
                {"id": "b-00000007", "type": "ol", "items": [[{"t": "text", "v": "Dos"}]]},
                {"id": "b-00000008", "type": "hr"},
                {"id": "b-00000009", "type": "figure", "attrs": {"fig": "fig-cover"}},
                {"id": "b-0000000a", "type": "evidence", "attrs": {"class": "B", "confidence": "Media", "limits": [{"t": "text", "v": "Límite"}]}}
            ], "footnotes": {"fn-00000001": [{"t": "text", "v": "Nota"}]}
        }
        sources = [{"key": "source-one", "title": "Fuente", "url": "https://example.org", "author": "A"}]
        figures = {"fig-cover": {"file": "figures/cover.webp", "width": 100, "height": 80, "alt": {"es-419": "Libro"}, "caption": {"es-419": "Leyendo"}, "credit": "FCMO", "licence": "Original"}}
        body, notes, source_html, toc = render_document(document, sources, figures, locale="es-419", base="/site", asset_prefix="editorial/pieces/demo")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", body)
        self.assertNotIn("<script>", body)
        for token in ('<h2 id=', '<h3 id=', '<blockquote id=', 'class="pullquote"', '<ul id=', '<ol id=', '<hr', 'class="essay-figure"', 'class="evidence-box"', 'data-field="quotation"'):
            self.assertIn(token, body)
        # Every document block must remain addressable for review comments,
        # not just the headings used by the table of contents.
        for block in document['blocks']:
            self.assertEqual(body.count('id="' + block['id'] + '"'), 1)
        self.assertIn('class="essay-notes"', notes)
        self.assertIn('class="essay-sources"', source_html)
        self.assertIn('class="essay-toc"', toc)

    def test_build_emits_piece_pages_and_discovery_surfaces(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            builder = PaperBuilder(stories_path=ROOT / "site/data/stories.v2.json",
                                   status_path=ROOT / "site/data/newsroom-status.json",
                                   editorial_path=FIXTURE, out=out, base="/FCMO-AI-Newsletter/")
            builder.build()
            slug = "fixture-essay"
            for route in (f"cartas/{slug}/", f"es/cartas/{slug}/", f"zh/cartas/{slug}/"):
                self.assertTrue((out / route / "index.html").is_file(), route)
            es = (out / "es/cartas/fixture-essay/index.html").read_text()
            self.assertIn("<article class=\"essay\"", es)
            self.assertIn("<section class=\"essay-notes\"", es)
            self.assertIn("<section class=\"essay-sources\"", es)
            self.assertTrue((out / "es/cartas/ediciones/2026-10-01-primeras-decisiones/index.html").is_file())
            self.assertIn("fixture-essay", (out / "es/cartas/index.html").read_text())
            self.assertIn("fixture-essay", (out / "es/feed.xml").read_text())
            self.assertIn("fixture-essay", (out / "es/feed.atom").read_text())
            self.assertIn("fixture-essay", (out / "es/feed.json").read_text())
            self.assertIn("fixture-essay", (out / "sitemap.xml").read_text())
            self.assertIn("fixture-essay", (out / "es/data/search.json").read_text())
            self.assertIn("fixture-essay", (out / "es/llms.txt").read_text())
            self.assertIn("A durable public record", (out / "llms-full.txt").read_text())
            self.assertIn("Primeras decisiones", (out / "es/cartas/index.html").read_text())

    def test_pending_locale_is_explicit_and_withdrawn_piece_is_tombstone(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            builder = PaperBuilder(stories_path=ROOT / "site/data/stories.v2.json",
                                   status_path=ROOT / "site/data/newsroom-status.json",
                                   editorial_path=FIXTURE, out=out, base="/FCMO-AI-Newsletter/")
            builder.build()
            pending = (out / "zh/cartas/fixture-essay/index.html").read_text()
            self.assertIn("尚未提供", pending)
            self.assertNotIn("A durable public record", pending)
            tombstone = (out / "es/cartas/fixture-withdrawn/index.html").read_text()
            self.assertIn("Retirado", tombstone)
            self.assertIn("Aviso de retiro", tombstone)

    def test_machine_prepared_language_is_disclosed_and_links_to_original(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            editorial = temp_root / "editorial"
            shutil.copytree(FIXTURE, editorial)
            piece_path = editorial / "pieces/fixture-essay/piece.json"
            piece = json.loads(piece_path.read_text())
            piece["locales"]["zh-Hans"] = "ready"
            piece_path.write_text(json.dumps(piece))
            provenance_path = editorial / "pieces/fixture-essay/provenance.json"
            provenance = json.loads(provenance_path.read_text())
            provenance["zh-Hans"] = {"origin": "agent_draft", "human_reviewed": False, "model": "fixture", "source_locale": "en"}
            provenance_path.write_text(json.dumps(provenance))
            out = temp_root / "out"
            PaperBuilder(stories_path=ROOT / "site/data/stories.v2.json",
                         status_path=ROOT / "site/data/newsroom-status.json",
                         editorial_path=editorial, out=out, base="/FCMO-AI-Newsletter/").build()
            page = (out / "zh/cartas/fixture-essay/index.html").read_text()
            self.assertIn('class="mt-disclosure"', page)
            self.assertIn("尚未经过人工审核", page)
            self.assertIn('href="/FCMO-AI-Newsletter/cartas/fixture-essay/"', page)


if __name__ == "__main__":
    unittest.main()
