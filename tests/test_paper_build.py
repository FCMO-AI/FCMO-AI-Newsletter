from __future__ import annotations

from html.parser import HTMLParser
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

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.lang = values.get("lang")
        if tag == "article":
            self.articles += 1
        if tag == "main":
            self.main_depth += 1
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

    def test_no_binding_placeholders_or_raw_evidence_heading(self):
        for path in self.out.rglob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("—/10", text, path)
            self.assertNotIn("EVIDENCE —", text, path)

    def test_pending_locales_never_fall_back_to_english_prose(self):
        story = next(s for s in self.payload["stories"] if s["l10n"]["es-419"]["state"] == "PENDING")
        suffix = f"{story['url_date'].replace('-', '/')}/{story['slug']}/index.html"
        for prefix in ("es", "zh"):
            text = (self.out / prefix / suffix).read_text(encoding="utf-8")
            self.assertNotIn(story["summary"], text)
            self.assertIn("hreflang=\"en\"", text)

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


if __name__ == "__main__":
    unittest.main()
