"""Lane B: the essay page frame. Body HTML comes from the A1 renderer; this frame
wraps it in the 6.1 class contract and never lets text escape unescaped."""
import re
import unittest

from tools.paper.templates import essay

BODY = ('<h2 id="s-1">Primera idea</h2><p>Un párrafo<sup class="fn-ref"><a href="#fn-aaaa1111" id="fnref-aaaa1111">1</a></sup> '
        '<cite class="src-ref"><a href="#src-gr">Gr</a></cite>.</p><h3 id="s-2">Detalle</h3><p>Otro.</p>'
        '<figure class="essay-figure"><img src="f.webp" width="800" height="450" alt="Alt">'
        '<figcaption>Pie <span class="credit">Crédito</span></figcaption></figure>'
        '<aside class="evidence-box" data-class="B"><p>Evidencia</p></aside>')
NOTES = '<section class="essay-notes"><ol><li id="fn-aaaa1111">Nota <a href="#fnref-aaaa1111">↩</a></li></ol></section>'
SOURCES = '<section class="essay-sources"><ol><li id="src-gr">Fuente</li></ol></section>'
LOCALE = {"code": "es-419", "html_lang": "es-419", "hreflang": "es-419", "path_prefix": "es/"}
PIECE = {"id": "FCMO-P-0123456789ab", "kind": "essay", "slug": "una-idea", "authors": [{"key": "javier", "name": "Javier"}],
         "first_published_at": "2026-10-04T12:00:00Z", "updated_at": "2026-10-04T12:00:00Z", "status": "published", "corrections": []}


def ctx(**extra):
    base = {"title": "Una <idea>", "dek": "Subtítulo", "date_text": "4 de octubre de 2026", "base": "/",
            "hrefs": {"original": "/cartas/una-idea/", "shelf": "/es/cartas/", "others": []}}
    base.update(extra)
    return base


class EssayTemplate(unittest.TestCase):
    def test_returns_title_description_body(self):
        title, desc, html = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx())
        self.assertIn("Una <idea>", title)
        self.assertTrue(desc)
        self.assertNotIn("<idea>", html)  # escaped
        self.assertIn("Una &lt;idea&gt;", html)

    def test_class_contract(self):
        _, _, html = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx())
        for needle in ('<article class="essay"', 'data-piece-id="FCMO-P-0123456789ab"', 'lang="es-419"',
                       'class="essay-head"', 'class="essay-title"', 'class="essay-dek"', 'class="essay-byline"',
                       '<time datetime="2026-10-04">', 'class="essay-toc"', 'class="essay-body"',
                       'class="essay-notes"', 'class="essay-sources"'):
            self.assertIn(needle, html, needle)

    def test_toc_lists_headings_with_anchors(self):
        _, _, html = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx())
        toc = re.search(r'<nav class="essay-toc".*?</nav>', html, re.S).group(0)
        self.assertIn('href="#s-1"', toc)
        self.assertIn("Primera idea", toc)
        self.assertIn('href="#s-2"', toc)

    def test_no_toc_for_short_pieces(self):
        _, _, html = essay.render(PIECE, LOCALE, "<p>Corto</p>", "", "", ctx())
        self.assertNotIn('class="essay-toc"', html)

    def test_reading_time_cjk_and_latin(self):
        zh = {"code": "zh-Hans", "html_lang": "zh-Hans", "hreflang": "zh-Hans", "path_prefix": "zh/"}
        _, _, html = essay.render(PIECE, zh, "<p>" + "字" * 1200 + "</p>", "", "", ctx(date_text="2026年10月4日"))
        self.assertIn("3 分钟", html)
        _, _, html = essay.render(PIECE, LOCALE, "<p>" + "palabra " * 460 + "</p>", "", "", ctx())
        self.assertIn("2 min", html)

    def test_machine_disclosure_and_original_link(self):
        _, _, html = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx(machine_prepared=True))
        self.assertIn('class="mt-disclosure"', html)
        self.assertIn('href="/cartas/una-idea/"', html)
        _, _, plain = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx())
        self.assertNotIn("mt-disclosure", plain)

    def test_correction_box(self):
        piece = dict(PIECE, corrections=[{"at": "2026-10-05T10:00:00Z", "type": "clarification", "note": {"es-419": "Se aclaró <b>x</b>."}}])
        _, _, html = essay.render(piece, LOCALE, BODY, NOTES, SOURCES, ctx())
        self.assertIn('class="correction-box"', html)
        self.assertIn("&lt;b&gt;", html)

    def test_pending_page_never_falls_back_silently(self):
        _, _, html = essay.render(PIECE, LOCALE, "", "", "", ctx(mode="pending"))
        self.assertIn("todavía no está disponible en español", html)
        self.assertIn('href="/cartas/una-idea/"', html)
        self.assertNotIn('class="essay-body"', html)

    def test_tombstone(self):
        piece = dict(PIECE, status="withdrawn", withdrawal={"at": "2026-10-09T00:00:00Z", "reason_code": "x", "note": {"es-419": "Retirado."}})
        _, _, html = essay.render(piece, LOCALE, "", "", "", ctx(mode="tombstone"))
        self.assertIn("Retirado.", html)
        self.assertIn("retirado", html.lower())
        self.assertNotIn('class="essay-body"', html)

    def test_stylesheet_and_sidenote_enhancement_present(self):
        _, _, html = essay.render(PIECE, LOCALE, BODY, NOTES, SOURCES, ctx())
        self.assertIn("assets/css/essay.css", html)
        self.assertIn("<script>", html)

    def test_unknown_locale_rejected(self):
        with self.assertRaises(KeyError):
            essay.render(PIECE, dict(LOCALE, code="fr"), BODY, NOTES, SOURCES, ctx())


if __name__ == "__main__":
    unittest.main()
