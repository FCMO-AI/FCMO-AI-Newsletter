"""Real-data checks for the FCMO AI paper's editorial navigation and context."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PaperEditorialDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="paper-editorial-depth-")
        cls.out = Path(cls.tmp.name) / "FCMO-AI-Newsletter"
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

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def page(self, route: dict) -> str:
        relative = route["path"].strip("/")
        return (self.out / relative / "index.html").read_text(encoding="utf-8")

    def test_story_has_a_visual_anchor_and_two_reading_paths(self):
        route = next(route for route in self.routes if route["kind"] == "story" and route["locale"] == "en")
        page = self.page(route)
        self.assertIn('class="hero story-hero"', page)
        self.assertIn('class="edition-neighbors"', page)
        self.assertIn('class="related-reading"', page)
        self.assertIn('class="story-taxonomy"', page)
        self.assertGreaterEqual(page.count('href="/FCMO-AI-Newsletter/topic/'), 1)

    def test_taxonomy_and_edition_pages_show_corpus_context_and_navigation(self):
        for kind in ("archive", "edition", "topic", "org"):
            route = next(route for route in self.routes if route["kind"] == kind and route["locale"] == "en")
            page = self.page(route)
            with self.subTest(kind=kind):
                self.assertIn('class="archive-totals"', page)
                self.assertIn('class="archive-item"', page)
                self.assertIn('data-story-id="FCMO-', page)
                if kind == "edition":
                    self.assertIn('class="edition-neighbors"', page)
                if kind in {"topic", "org"}:
                    self.assertIn('class="taxonomy-neighbors"', page)

    def test_front_method_and_status_expose_live_publication_facts_in_all_locales(self):
        for locale, prefix in (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/")):
            front = (self.out / prefix / "diario/index.html").read_text(encoding="utf-8")
            method = (self.out / prefix / "method/index.html").read_text(encoding="utf-8")
            status = (self.out / prefix / "status/index.html").read_text(encoding="utf-8")
            with self.subTest(locale=locale):
                self.assertIn('class="front-ledger"', front)
                self.assertIn('class="method-steps"', method)
                self.assertIn('class="method-example"', method)
                self.assertIn('class="status-grid"', status)
                self.assertIn("41", front)
                self.assertIn("41", method)
                self.assertIn("41", status)


if __name__ == "__main__":
    unittest.main()
