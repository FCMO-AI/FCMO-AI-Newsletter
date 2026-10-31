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

    def redirect_target(self, relative: str) -> str:
        page = (self.out / relative / "index.html").read_text(encoding="utf-8")
        return page

    def test_locale_roots_is_the_one_front_and_retired_fronts_redirect_to_it(self):
        # CONTRACT-CHANGES.md #1: the technical daily front is retired; the locale root is the only front.
        for prefix in ("", "es/", "zh/"):
            with self.subTest(prefix=prefix):
                landing = (self.out / prefix / "index.html").read_text(encoding="utf-8")
                self.assertIn('class="page-landing"', landing)
                for anchor in ("letters", "start-here", "technical"):
                    self.assertNotIn(f'id="{anchor}"', landing)
                self.assertNotIn(f'/FCMO-AI-Newsletter/{prefix}diario/', landing)
                self.assertIn(f'/FCMO-AI-Newsletter/{prefix}search/', landing)
                self.assertIn('<link rel="alternate" type="text/plain" href="/FCMO-AI-Newsletter/llms.txt">', landing)
                self.assertIn('<link rel="alternate" type="application/json" href="/FCMO-AI-Newsletter/agent.json">', landing)
                retired = self.redirect_target(f"{prefix}diario")
                self.assertIn(f'content="0; url=/FCMO-AI-Newsletter/{prefix}"', retired)
                self.assertIn('name="robots" content="noindex"', retired)
                self.assertIn(f'content="0; url=/FCMO-AI-Newsletter/{prefix}"',
                              (self.out / prefix / "front.html").read_text(encoding="utf-8"))

    def test_language_switch_preserves_story_and_front(self):
        routes = json.loads((self.out / "data/routes.json").read_text(encoding="utf-8"))
        story = next(row for row in routes if row["kind"] == "story" and row["locale"] == "en")
        for path in (story["path"], ""):
            page = (self.out / path / "index.html").read_text(encoding="utf-8")
            for prefix in ("es/", "zh/"):
                self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}{path}"', page)

    def test_retired_product_routes_redirect_and_one_subscribe_page_is_real(self):
        # CONTRACT-CHANGES.md #2: cartas/, empieza/, diario/ go to the front page; suscribete/ goes to the one subscribe page.
        for prefix in ("", "es/", "zh/"):
            for path, target in (("cartas/", ""), ("empieza/", ""), ("diario/", ""), ("comunidad/", ""), ("suscribete/", "subscribe/")):
                with self.subTest(prefix=prefix, path=path):
                    html = self.redirect_target(f"{prefix}{path}")
                    self.assertIn(f'content="0; url=/FCMO-AI-Newsletter/{prefix}{target}"', html)
                    self.assertIn('name="robots" content="noindex"', html)
            with self.subTest(prefix=prefix, path="subscribe/"):
                html = (self.out / prefix / "subscribe/index.html").read_text(encoding="utf-8")
                self.assertIn('class="page-subscribe"', html)
                self.assertIn('class="newsletter-record subscribe-reading"', html)
                self.assertNotIn(f'/FCMO-AI-Newsletter/{prefix}diario/', html)
                self.assertNotIn("FCMO" + " Group", html)
            landing = (self.out / prefix / "index.html").read_text(encoding="utf-8")
            self.assertNotIn(f'/FCMO-AI-Newsletter/{prefix}cartas/', landing)
            self.assertNotIn(f'/FCMO-AI-Newsletter/{prefix}empieza/', landing)
            # R4: the Bone band is the legend only; the counts row is retired and the trio (3 classes) remains.
            self.assertNotIn('class="band-counts"', landing)
            self.assertEqual(landing.split('class="band-trio"', 1)[1].split('class="band-note"', 1)[0].count("<p>"), 3)

    def test_404_has_all_three_locale_destinations(self):
        page = (self.out / "404.html").read_text(encoding="utf-8")
        for prefix in ("", "es/", "zh/"):
            self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}"', page)
            self.assertIn(f'href="/FCMO-AI-Newsletter/{prefix}search/"', page)


if __name__ == "__main__":
    unittest.main()
