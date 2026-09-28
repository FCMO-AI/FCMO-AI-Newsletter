from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

from tools.paper.i18n import format_date, headline, load_catalogs
from tools.paper.templates.landing import render


ROOT = Path(__file__).resolve().parents[1]
STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))


class LandingFeatureBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="landing-feature-")
        cls.out = Path(cls.temp.name) / "publish"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES),
             "--status", str(STATUS), "--out", str(cls.out), "--base", BASE],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.payload = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.catalogs = load_catalogs(ROOT)
        cls.routes = json.loads((cls.out / "data/routes.json").read_text(encoding="utf-8"))
        cls.lead = sorted(
            (story for story in cls.payload["stories"] if story.get("status") == "live"),
            key=lambda story: (bool(story.get("front_page_eligible")), story.get("importance", 0),
                               story.get("event_at", ""), story["id"]),
            reverse=True,
        )[0]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_localized_feature_uses_ranked_story_route_and_local_media(self):
        story = self.lead
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                page = (self.out / prefix / "index.html").read_text(encoding="utf-8")
                intro = re.search(r'<section class="landing-intro".*?</section>', page, re.S).group()
                feature = re.search(r'<article class="landing-feature story-card".*?</article>', intro, re.S)
                self.assertIsNotNone(feature)
                card = feature.group()
                title = headline(story, locale, self.catalogs[locale])
                date = format_date(story["event_at"], self.catalogs[locale],
                                   precision=story.get("date_precision", "day"))
                route = next(row for row in self.routes
                             if row.get("story_id") == story["id"] and row.get("locale") == locale
                             and row.get("kind") == "story")
                link = re.search(r'<a href="([^"]+)"><img', card).group(1)
                self.assertEqual(urlsplit(link).path, BASE + route["path"].lstrip("/"))
                self.assertIn(f'<h2><a href="{escape(link, quote=True)}">{escape(title)}</a></h2>', card)
                self.assertIn(f'<time datetime="{escape(story["event_at"], quote=True)}">{escape(date)}</time>', card)
                self.assertIn("FCMO AI", card)

                image = re.search(r'<img src="([^"]+)" alt="([^"]*)"', card)
                self.assertIsNotNone(image)
                image_path = urlsplit(image.group(1)).path
                self.assertTrue(image_path.startswith(BASE))
                local_image = self.out / image_path[len(BASE):]
                self.assertTrue(local_image.is_file(), image_path)
                expected_alt = (story.get("media", {}).get("alt", {}).get(locale) or title)
                self.assertEqual(image.group(2), expected_alt)
                expected_credit = self.catalogs[locale]["strings"]["story"]["image_credit"].format(
                    credit=story.get("media", {}).get("credit", "FCMO AI"))
                self.assertIn(escape(expected_credit), card)
                self.assertLess(intro.index(card), intro.index("<strong>"))


class LandingFeatureTemplateTests(unittest.TestCase):
    def render(self, feature=None):
        return render(locale={"code": "en"}, home="/", technical="/daily/", about="/about/",
                      subscribe="/subscribe/", lead="", top="", cartas="", feature=feature)

    def test_optional_feature_supports_empty_corpus(self):
        page = self.render()
        self.assertIn('<div class="landing-record"', page)
        self.assertNotIn("landing-feature", page)
        self.assertIn("0 <small>stories</small>", page)

    def test_feature_values_are_escaped(self):
        page = self.render({"label": "Lead", "title": 'A & <report> "title"', "href": '/story/?x="&',
                            "image": '/assets/a.svg?x="&', "alt": 'Graphic <description> & detail',
                            "credit": 'Desk & <credit>', "datetime": '2026-08-26T00:00:00Z',
                            "date": 'August 26 & <2026>'})
        self.assertIn(escape('A & <report> "title"'), page)
        self.assertIn('href="/story/?x=&quot;&amp;"', page)
        self.assertIn('alt="Graphic &lt;description&gt; &amp; detail"', page)
        self.assertIn('Desk &amp; &lt;credit&gt;', page)
        self.assertIn('August 26 &amp; &lt;2026&gt;', page)


if __name__ == "__main__":
    unittest.main()
