"""Integration checks for v3 public naming and n2 editorial structures."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.classes: dict[str, int] = {}
        self.ledger_values: list[str] = []
        self._in_ledger = False
        self._in_strong = False
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        for class_name in classes:
            self.classes[class_name] = self.classes.get(class_name, 0) + 1
        if "front-ledger" in classes:
            self._in_ledger = True
        if "archive-item" in classes:
            self._row = []
            self.rows.append(self._row)
        if self._row is not None and tag in {"time", "a", "div"}:
            self._row.append(tag)
        if self._in_ledger and tag == "strong":
            self._in_strong = True
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "strong":
            self._in_strong = False
        if tag == "section" and self._in_ledger:
            self._in_ledger = False
        if tag == "article" and self._row is not None:
            self._row = None
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]

    def handle_data(self, data):
        if self._in_ledger and self._in_strong and data.strip():
            self.ledger_values.append(data.strip())


class V3IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v3-integration-")
        cls.out = Path(cls.temp.name) / "FCMO-AI-Newsletter"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"),
             "--stories", str(ROOT / "site/data/stories.v2.json"),
             "--status", str(ROOT / "site/data/newsroom-status.json"),
             "--out", str(cls.out), "--base", "/FCMO-AI-Newsletter/"],
            cwd=ROOT, text=True, capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.routes = json.loads((cls.out / "data/routes.json").read_text(encoding="utf-8"))
        cls.css = (cls.out / "assets/css/paper.css").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def page(cls, kind: str, locale: str = "en") -> str:
        route = next(row for row in cls.routes if row["kind"] == kind and row["locale"] == locale)
        relative = route["path"].strip("/")
        return (cls.out / relative / "index.html").read_text(encoding="utf-8")

    @staticmethod
    def rule(css: str, selector: str) -> str:
        found = re.findall(re.escape(selector) + r"\s*\{([^{}]*)\}", css)
        if not found:
            raise AssertionError(f"missing CSS rule for {selector}")
        return found[-1]

    def test_public_legal_and_native_catalogs_use_the_approved_brand_names(self):
        files = [
            ROOT / "CONTENT_LICENSE.md", ROOT / "scaffold/release-index.html",
            ROOT / "release-src/index.html", ROOT / "site/about.html",
            ROOT / "site/privacy.html", ROOT / "site/license.html",
            ROOT / "site/disclaimer.html",
            ROOT / "site/data/i18n/es-419/ui.json",
            ROOT / "site/data/i18n/zh-Hans/ui.json",
        ]
        for path in files:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotRegex(path.read_text(encoding="utf-8"), re.compile(r"FCMO\s+Group", re.I))
        es = json.loads((ROOT / "site/data/i18n/es-419/ui.json").read_text(encoding="utf-8"))
        zh = json.loads((ROOT / "site/data/i18n/zh-Hans/ui.json").read_text(encoding="utf-8"))
        self.assertEqual(es["ui"]["FCMO"], "FCMO")
        self.assertEqual(zh["ui"]["FCMO"], "FCMO")
        self.assertIn("FCMO", es["ui"]["Founder, FCMO."])
        self.assertIn("FCMO", zh["ui"]["Founder, FCMO."])
        self.assertIn("does not grant rights", (ROOT / "site/license.html").read_text(encoding="utf-8"))
        self.assertIn("no determina por sí misma", es["ui"]["The FCMO brand remains the public-facing umbrella and does not, by itself, determine legal authorship or ownership of FCMO AI material."])

    def test_generated_front_archive_story_and_status_match_the_scoped_layout(self):
        front = self.page("front")
        archive = self.page("archive")
        story = self.page("story")
        status = self.page("status")
        parsed_front = StructureParser()
        parsed_front.feed(front)
        parsed_archive = StructureParser()
        parsed_archive.feed(archive)
        parsed_status = StructureParser()
        parsed_status.feed(status)

        self.assertEqual(parsed_front.classes.get("front-ledger"), 1)
        self.assertEqual(len(parsed_front.ledger_values), 3)
        self.assertGreaterEqual(parsed_archive.classes.get("archive-item", 0), 10)
        self.assertTrue(all(row[:3] == ["time", "a", "img"] or row[:2] == ["time", "a"] for row in parsed_archive.rows[:1]))
        self.assertEqual(parsed_status.classes.get("status-card"), 4)
        self.assertRegex(story, r'<div class="story-body"><figure class="hero story-hero">')
        self.assertIn('class="edition-neighbors"', story)
        self.assertIn('class="related-reading"', story)
        self.assertIn('class="story-taxonomy"', story)

    def test_css_keeps_editorial_columns_and_balanced_responsive_cards(self):
        editorial_rules = self.css[self.css.rfind("/* n2 editorial structures"):]
        desktop_rules = editorial_rules[:editorial_rules.index("@media(max-width:850px)")]
        archive = self.rule(desktop_rules, ".archive-item")
        self.assertIn("grid-template-columns:8rem minmax(8rem,12rem) minmax(0,1fr)", archive)
        art = self.rule(desktop_rules, ".archive-art img")
        self.assertIn("aspect-ratio:16/9", art)
        self.assertIn("object-fit:cover", art)
        hero = self.rule(desktop_rules, ".story-body>.story-hero")
        self.assertIn("max-width:var(--read)", hero)
        self.assertIn("repeat(4,minmax(0,1fr))", self.rule(desktop_rules, ".status-grid"))
        self.assertIn("grid-template-columns:minmax(0,1fr)", self.css[self.css.rfind("@media(max-width:520px)"):])
        self.assertIn("--metis", self.rule(desktop_rules, ".method-steps li::before"))
        self.assertIn("outline:3px solid var(--metis)", self.css)
        for selector in (".front-ledger ul", ".archive-totals", ".taxonomy-neighbors ul",
                         ".edition-neighbors a", ".related-reading", ".story-taxonomy ul",
                         ".method-steps ol", ".method-example"):
            with self.subTest(selector=selector):
                self.rule(desktop_rules, selector)


if __name__ == "__main__":
    unittest.main()
