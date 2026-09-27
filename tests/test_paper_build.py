from __future__ import annotations

from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "fixtures"


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = None
        self.articles = 0
        self.main_depth = 0
        self.main_text = []
        self.meta = []
        self.links = []
        self.main_attrs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "article":
            self.articles += 1
        if tag == "main":
            self.main_depth += 1
            self.main_attrs.append(values)
        if tag == "meta":
            self.meta.append(values)
        if tag == "link":
            self.links.append(values)

    def handle_endtag(self, tag):
        if tag == "main":
            self.main_depth -= 1

    def handle_data(self, data):
        if self.main_depth:
            self.main_text.append(data)


class PaperBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="wpA3-")
        cls.out = Path(cls.temp.name) / "publish"
        command = [
            sys.executable, str(ROOT / "tools" / "paper" / "build.py"),
            "--stories", str(FIXTURES / "stories.v2.json"),
            "--status", str(FIXTURES / "newsroom-status.fresh.json"),
            "--out", str(cls.out), "--base", "/FCMO-AI-Newsletter/",
        ]
        cls.result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        if cls.result.returncode:
            raise AssertionError(cls.result.stdout + cls.result.stderr)
        cls.payload = json.loads((FIXTURES / "stories.v2.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def parse(self, rel: str) -> tuple[str, AuditParser]:
        text = (self.out / rel).read_text(encoding="utf-8")
        parser = AuditParser()
        parser.feed(text)
        return text, parser

    def test_acceptance_command_reports_routes(self):
        self.assertRegex(self.result.stdout, r"routes=\d+")

    def test_front_pages_are_static_and_localized(self):
        for rel, lang in (("index.html", "en"), ("es/index.html", "es-419"), ("zh/index.html", "zh-Hans")):
            with self.subTest(rel=rel):
                _, page = self.parse(rel)
                self.assertEqual(page.lang, lang)
                self.assertGreaterEqual(page.articles, 5)
                self.assertGreater(len("".join(page.main_text).strip()), 500)

    def test_hreflang_triad_and_default(self):
        _, page = self.parse("index.html")
        values = {item.get("hreflang") for item in page.links if item.get("rel") == "alternate"}
        self.assertEqual(values, {"en", "es-419", "zh-Hans", "x-default"})

    def test_every_live_story_has_exactly_one_route_per_locale(self):
        routes = json.loads((self.out / "data" / "routes.json").read_text(encoding="utf-8"))
        actual = {(row["story_id"], row["locale"]) for row in routes if row["kind"] == "story"}
        live = {story["id"] for story in self.payload["stories"] if story["status"] == "live"}
        expected = {(story_id, locale) for story_id in live for locale in ("en", "es-419", "zh-Hans")}
        self.assertEqual(actual, expected)

    def test_story_pages_bind_their_internal_identity_only_as_metadata(self):
        routes = json.loads((self.out / "data" / "routes.json").read_text(encoding="utf-8"))
        for row in routes:
            if row["kind"] != "story":
                continue
            _, page = self.parse(row["path"] + "index.html")
            self.assertEqual(page.main_attrs[0].get("data-story-id"), row["story_id"])

    def test_source_data_is_embedded_byte_for_byte(self):
        self.assertEqual(
            (self.out / "data/stories.v2.json").read_bytes(),
            (FIXTURES / "stories.v2.json").read_bytes(),
        )
        self.assertEqual(
            (self.out / "data/newsroom-status.json").read_bytes(),
            (FIXTURES / "newsroom-status.fresh.json").read_bytes(),
        )

    def test_no_binding_placeholders_or_raw_evidence_heading(self):
        for path in self.out.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("—/10", text, path)
            self.assertNotIn("EVIDENCE —", text, path)
            visible = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", "", text, flags=re.I | re.S)
            visible = re.sub(r"<[^>]+>", " ", visible)
            self.assertNotRegex(visible, r"\{[A-Za-z_][A-Za-z0-9_]*\}", path)

    def test_pending_locales_never_fall_back_to_english_prose(self):
        story = next(s for s in self.payload["stories"] if s["l10n"]["es-419"]["state"] == "PENDING")
        suffix = f"{story['url_date'].replace('-', '/')}/{story['slug']}/index.html"
        for prefix in ("es", "zh"):
            text = (self.out / prefix / suffix).read_text(encoding="utf-8")
            self.assertNotIn(story["summary"], text)
            self.assertIn("hreflang=\"en\"", text)
            self.assertIn('lang="en"', text)

    def test_pending_locales_render_only_the_fields_already_translated(self):
        story = next(s for s in self.payload["stories"] if s["l10n"]["es-419"]["state"] == "PENDING")
        suffix = f"{story['url_date'].replace('-', '/')}/{story['slug']}/index.html"
        for locale, prefix, pending in (("es-419", "es", "Traducción pendiente"), ("zh-Hans", "zh", "翻译待完成")):
            fields = story["l10n"][locale].get("fields") or {}
            text = (self.out / prefix / suffix).read_text(encoding="utf-8")
            self.assertIn(f"<h1>{pending}</h1>", text)
            for key in ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale"):
                if fields.get(key):
                    self.assertIn(html.escape(str(fields[key])), text, (locale, key))

    def test_meta_descriptions_and_og_assets(self):
        for row in json.loads((self.out / "data" / "routes.json").read_text(encoding="utf-8")):
            if row["kind"] != "story":
                continue
            _, page = self.parse(row["path"] + "index.html")
            descriptions = [m["content"] for m in page.meta if m.get("name") == "description"]
            images = [m["content"] for m in page.meta if m.get("property") == "og:image"]
            self.assertEqual(len(descriptions), 1)
            self.assertLessEqual(len(descriptions[0]), 160)
            self.assertEqual(len(images), 1)
            rel = images[0].split("/FCMO-AI-Newsletter/", 1)[-1]
            self.assertTrue((self.out / rel).is_file(), images[0])

    def test_every_referenced_story_media_file_is_copied(self):
        for story in self.payload["stories"]:
            local = (story.get("media") or {}).get("local_path")
            if local:
                self.assertTrue((self.out / local).is_file(), local)

    def test_rss_atom_json_and_sitemaps(self):
        for rel in ("feed.xml", "es/feed.xml", "zh/feed.xml"):
            root = ET.parse(self.out / rel).getroot()
            items = root.findall("./channel/item")
            self.assertTrue(items)
            self.assertTrue(all(item.find("pubDate") is not None for item in items))
        sitemap = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn("ns0:", sitemap)
        ET.fromstring(sitemap)
        ET.parse(self.out / "feed.atom")
        json.loads((self.out / "feed.json").read_text(encoding="utf-8"))

    def test_feeds_and_search_never_use_internal_ids_as_reader_copy(self):
        for rel in ("feed.xml", "feed.atom", "feed.json", "data/search.json",
                    "es/feed.xml", "es/feed.atom", "es/feed.json", "es/data/search.json",
                    "zh/feed.xml", "zh/feed.atom", "zh/feed.json", "zh/data/search.json"):
            self.assertNotRegex((self.out / rel).read_text(encoding="utf-8"), r"FCMO-[0-9A-F]{12}", rel)

    def test_fonts_are_woff2_subsetted_and_first_paint_preloads_only_latin(self):
        font_dir = self.out / "assets/fonts"
        self.assertFalse(list(font_dir.glob("*.ttf")))
        self.assertTrue((font_dir / "SourceSerif4-normal-400_700-latin.woff2").is_file())
        text = (self.out / "index.html").read_text(encoding="utf-8")
        preloads = re.findall(r'<link rel="preload" href="([^"]+)" as="font"', text)
        self.assertEqual(len(preloads), 3)
        self.assertTrue(all("-latin.woff2" in value for value in preloads), preloads)

    def test_legacy_redirects_have_new_canonical(self):
        story = next(s for s in self.payload["stories"] if s["status"] == "live")
        for rel in (f"developments/{story['id']}.html", f"news/en/{story['id']}.html", f"news/es/{story['id']}.html", f"news/zh-hans/{story['id']}.html"):
            text = (self.out / rel).read_text(encoding="utf-8")
            self.assertIn('rel="canonical"', text)
            self.assertNotIn("#/", text)

    def test_required_discovery_and_editorial_routes_exist(self):
        required = ["archive", "search", "status", "about", "method", "feeds", "corrections", "suscribete", "agenda", "autores/mesa-fcmo-ai", "privacy", "license", "disclaimer"]
        for prefix in ("", "es/", "zh/"):
            for route in required:
                self.assertTrue((self.out / prefix / route / "index.html").is_file(), prefix + route)

    def test_budgets(self):
        self.assertLessEqual((self.out / "index.html").stat().st_size, 102400)
        js = sum(path.stat().st_size for path in self.out.rglob("*.js"))
        self.assertLessEqual(js, 30720)
        for rel in ("data/search.json", "es/data/search.json", "zh/data/search.json"):
            self.assertLessEqual((self.out / rel).stat().st_size, 150 * 1024)

    def test_delayed_status_banner_is_exactly_once_in_spanish(self):
        delayed = Path(self.temp.name) / "delayed"
        command = [sys.executable, str(ROOT / "tools" / "paper" / "build.py"), "--stories", str(FIXTURES / "stories.v2.json"), "--status", str(FIXTURES / "newsroom-status.delayed.json"), "--out", str(delayed), "--base", "/FCMO-AI-Newsletter/"]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (delayed / "es" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(text.count('data-edition-state="DELAYED"'), 1)
        self.assertIn("Última edición", text)

    def test_stale_clock_safeguard_is_small(self):
        text = (self.out / "index.html").read_text(encoding="utf-8")
        scripts = re.findall(r"<script>(.*?)</script>", text, re.S)
        self.assertTrue(scripts)
        safeguard = next(script for script in scripts if "1296e5" in script)
        self.assertLessEqual(len(safeguard.encode("utf-8")), 1024)


class RealDataPaperBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="paper-real-data-")
        cls.out = Path(cls.temp.name) / "publish"
        cls.payload = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))
        result = subprocess.run([
            sys.executable, str(ROOT / "tools/paper/build.py"),
            "--stories", str(ROOT / "site/data/stories.v2.json"),
            "--status", str(ROOT / "site/data/newsroom-status.json"),
            "--out", str(cls.out), "--base", "/FCMO-AI-Newsletter/",
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_every_english_story_h1_matches_its_canonical_title(self):
        for story in self.payload["stories"]:
            if story.get("status") != "live":
                continue
            route = self.out / story["url_date"].replace("-", "/") / story["slug"] / "index.html"
            text = route.read_text(encoding="utf-8")
            match = re.search(r'<header class="story-header">.*?<h1>(.*?)</h1>', text, re.S)
            self.assertIsNotNone(match, story["id"])
            actual = html.unescape(re.sub(r"<[^>]+>", "", match.group(1)))
            self.assertEqual(actual, story.get("headline") or story["title"], story["id"])

    def test_sqd_english_page_uses_the_real_canonical_title(self):
        story = next(item for item in self.payload["stories"] if item["id"] == "FCMO-7EBD0FA07C12")
        route = self.out / story["url_date"].replace("-", "/") / story["slug"] / "index.html"
        text = route.read_text(encoding="utf-8")
        self.assertIn(f"<h1>{html.escape(story['title'])}</h1>", text)
        self.assertNotIn("Translation pending", text)


if __name__ == "__main__":
    unittest.main()
