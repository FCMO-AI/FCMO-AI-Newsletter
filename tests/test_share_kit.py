"""Share kit: /comparte/ page, ready-to-post texts and per-edition Open Graph cards."""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper import og_image  # noqa: E402
from tools.paper.i18n import load_catalogs  # noqa: E402
from tools.paper.templates import share  # noqa: E402

FORBIDDEN = ("independent", "independiente", "most auditable", "más auditable", "FCMO Group", "error rate", "tasa de error", "世界第一")


def build(out: Path, og_source: Path | None = None) -> None:
    command = [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(ROOT / "site/data/stories.v2.json"),
               "--status", str(ROOT / "site/data/newsroom-status.json"), "--out", str(out), "--base", "/FCMO-AI-Newsletter/"]
    if og_source:
        command += ["--og-source", str(og_source)]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


class ShareTexts(unittest.TestCase):
    def test_x_post_fits_for_every_locale_even_with_a_very_long_headline(self):
        url = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/edition/2026-10-08/"
        for locale in share.COPY:
            with self.subTest(locale=locale):
                text = share.posts(locale, "A very long headline " * 20, url)["x"]
                self.assertLessEqual(share.x_length(text), share.X_LIMIT)
                self.assertTrue(text.endswith(url), "the link is never trimmed")

    def test_cjk_counts_double_and_urls_cost_23(self):
        self.assertEqual(share.x_length("你好"), 4)
        self.assertEqual(share.x_length("https://example.org/" + "a" * 80), 23)

    def test_copy_makes_no_unearned_claims(self):
        blob = json.dumps(share.COPY, ensure_ascii=False).lower()
        for word in FORBIDDEN:
            self.assertNotIn(word.lower(), blob)


class ShareCards(unittest.TestCase):
    def test_brand_card_and_one_card_per_edition(self):
        payload = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))
        catalogs = load_catalogs(ROOT)
        config = json.loads((ROOT / "config/site.json").read_text(encoding="utf-8"))
        template = (ROOT / "tools/paper/og_card.html").read_text(encoding="utf-8")
        dates = {s["url_date"] for s in payload["stories"] if s.get("status") not in {"withdrawn", "merged"} and s.get("url_date")}
        for locale in config["locales"]:
            names = [name for name, _ in og_image.share_cards(payload, locale, catalogs[locale["code"]], template)]
            self.assertEqual(names[0], "brand")
            self.assertEqual(set(names[1:]), {f"edition-{d}" for d in dates})
            self.assertNotIn("{{", "".join(html for _, html in og_image.share_cards(payload, locale, catalogs[locale["code"]], template)))


class SharePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="share-kit-")
        cls.out = Path(cls.tmp.name) / "site"
        cls.og = Path(cls.tmp.name) / "og"
        payload = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))
        cls.dates = sorted({s["url_date"] for s in payload["stories"] if s.get("url_date")}, reverse=True)
        for code in ("en", "es-419", "zh-Hans"):
            (cls.og / code).mkdir(parents=True)
            for name in ["brand"] + [f"edition-{d}" for d in cls.dates]:
                (cls.og / code / f"{name}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        build(cls.out, cls.og)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_page_exists_in_every_locale_with_three_posts_and_cards(self):
        for prefix, code in (("", "en"), ("es/", "es-419"), ("zh/", "zh-Hans")):
            with self.subTest(prefix=prefix):
                page = (self.out / prefix / "comparte/index.html").read_text(encoding="utf-8")
                self.assertIn('class="page-share"', page)
                for channel in ("linkedin", "x", "whatsapp"):
                    self.assertIn(f'data-channel="{channel}"', page)
                self.assertIn(f"og/{code}/brand.png", page)
                self.assertIn(f"og/{code}/edition-{self.dates[0]}.png", page)
                self.assertIn("share.js", page)
                self.assertTrue((self.out / "assets/js/share.js").is_file())
                self.assertIn(f'<meta property="og:image" content="https://fcmo-ai.github.io/FCMO-AI-Newsletter/og/{code}/brand.png">', page)
                self.assertRegex(page, r'href="/FCMO-AI-Newsletter/' + re.escape(prefix) + r'comparte/"')
                visible = re.sub(r"<[^>]+>", " ", page)
                self.assertNotRegex(visible, r"[\w.+-]+@[\w-]+\.[\w.]+")

    def test_posts_on_the_page_respect_the_x_limit(self):
        for prefix in ("", "es/", "zh/"):
            page = (self.out / prefix / "comparte/index.html").read_text(encoding="utf-8")
            body = re.search(r'data-channel="x".*?<textarea[^>]*>(.*?)</textarea>', page, re.S).group(1)
            import html
            self.assertLessEqual(share.x_length(html.unescape(body)), share.X_LIMIT)

    def test_every_edition_page_has_its_own_card(self):
        for prefix, code in (("", "en"), ("es/", "es-419"), ("zh/", "zh-Hans")):
            for date in self.dates:
                page = (self.out / prefix / "edition" / date / "index.html").read_text(encoding="utf-8")
                self.assertIn(f"og/{code}/edition-{date}.png", page)
                self.assertIn('name="twitter:card" content="summary_large_image"', page)

    def test_share_page_is_in_the_sitemap_routes(self):
        routes = json.loads((self.out / "data/routes.json").read_text(encoding="utf-8"))
        self.assertEqual({r["locale"] for r in routes if r["kind"] == "share"}, {"en", "es-419", "zh-Hans"})


if __name__ == "__main__":
    unittest.main()
