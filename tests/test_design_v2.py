"""Public route and brand-boundary checks for the v2 shell."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DesignV2Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="design-v2-")
        cls.out = Path(cls.tmp.name) / "site"
        result = subprocess.run([
            sys.executable, str(ROOT / "tools/paper/build.py"),
            "--stories", str(ROOT / "site/data/stories.v2.json"),
            "--status", str(ROOT / "site/data/newsroom-status.json"),
            "--out", str(cls.out), "--base", "/FCMO-AI-Newsletter/",
        ], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_locale_roots_and_technical_fronts_are_distinct_and_linked(self):
        for prefix in ("", "es/", "zh/"):
            with self.subTest(prefix=prefix):
                landing = (self.out / prefix / "index.html").read_text(encoding="utf-8")
                technical = (self.out / prefix / "diario/index.html").read_text(encoding="utf-8")
                self.assertIn('class="page-landing"', landing)
                self.assertIn('class="page-front"', technical)
                self.assertIn('id="letters"', landing)
                self.assertIn('id="start-here"', landing)
                self.assertIn('id="technical"', landing)
                self.assertIn(f'/FCMO-AI-Newsletter/{prefix}diario/', landing)
                self.assertIn(f'/FCMO-AI-Newsletter/{prefix}search/', landing)
                self.assertIn('<!-- agent-alternates -->', landing)
                self.assertIn(f'/FCMO-AI-Newsletter/{prefix}diario/', (self.out / prefix / "front.html").read_text(encoding="utf-8"))

    def test_language_switch_preserves_story_and_technical_front(self):
        routes = json.loads((self.out / "data/routes.json").read_text(encoding="utf-8"))
        story = next(row for row in routes if row["kind"] == "story" and row["locale"] == "en")
        for path in (story["path"], "diario/"):
            page = (self.out / path / "index.html").read_text(encoding="utf-8")
            for prefix in ("es/", "zh/"):
                self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}{path}"', page)

    def test_404_has_all_three_locale_destinations(self):
        page = (self.out / "404.html").read_text(encoding="utf-8")
        for prefix in ("", "es/", "zh/"):
            self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}diario/"', page)
            self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}search/"', page)


if __name__ == "__main__":
    unittest.main()
