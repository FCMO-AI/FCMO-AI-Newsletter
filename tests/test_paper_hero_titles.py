"""Regression for the 2026-10-27 cover leads that blocked the browser gate."""
import html
from pathlib import Path
import re
import tempfile
import unittest

from tools.paper.build import PaperBuilder
from tools.paper.front_order import front_order


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "contracts" / "fixtures"
REPORTED_LEADS = (
    "China releases a progress report on its AI capacity-building plan",
    "Aleph Alpha releases Kolibri, German-English open-weight model",
    "NgramRL uses prior rollouts to accelerate structured RL post-training generation",
)
MIXED_CJK_LEAD = "OpenAI系统卡报告GPT-6.1 Terra安全与授权结果不一"


class PaperHeroTitleTests(unittest.TestCase):
    def test_reported_leads_take_the_smaller_hero_step(self):
        for title in REPORTED_LEADS:
            with self.subTest(title=title):
                self.assertEqual(PaperBuilder._title_class(title, "en", hero=True), "title-large")

    def test_rendered_cover_keeps_the_complete_reported_title(self):
        with tempfile.TemporaryDirectory(prefix="paper-hero-title-") as temporary:
            builder = PaperBuilder(
                stories_path=FIXTURES / "stories.v2.json",
                status_path=FIXTURES / "newsroom-status.fresh.json",
                out=Path(temporary), base="/FCMO-AI-Newsletter/",
            )
            locale = next(row for row in builder.config["locales"] if row["code"] == "en")
            lead = front_order(builder.live)[0]
            for title in REPORTED_LEADS:
                with self.subTest(title=title):
                    lead["headline"] = title
                    builder._front(locale)
                    page = (Path(temporary) / "index.html").read_text(encoding="utf-8")
                    hero = re.search(r'<h1 class="cover-title ([^"]+)"><a href="[^"]+">(.*?)</a></h1>', page)
                    self.assertIsNotNone(hero)
                    self.assertEqual(html.unescape(hero[2]), title)
                    self.assertEqual(hero[1], "title-large")

    def test_short_hero_retains_display_hierarchy(self):
        self.assertEqual(PaperBuilder._title_class("China releases AI plan", "en", hero=True), "title-short")

    def test_current_mixed_cjk_lead_takes_the_smaller_hero_step(self):
        # The checked-in edition now leads with this story, rather than the
        # three leads captured in the incident brief. Keep both regressions.
        with tempfile.TemporaryDirectory(prefix="paper-hero-cjk-") as temporary:
            builder = PaperBuilder(
                stories_path=FIXTURES / "stories.v2.json",
                status_path=FIXTURES / "newsroom-status.fresh.json",
                out=Path(temporary), base="/FCMO-AI-Newsletter/",
            )
            locale = next(row for row in builder.config["locales"] if row["code"] == "zh-Hans")
            lead = front_order(builder.live)[0]
            lead["l10n"]["zh-Hans"]["fields"]["headline"] = MIXED_CJK_LEAD
            builder._front(locale)
            page = (Path(temporary) / "zh" / "index.html").read_text(encoding="utf-8")
            hero = re.search(r'<h1 class="cover-title ([^"]+)"><a href="[^"]+">(.*?)</a></h1>', page)
            self.assertIsNotNone(hero)
            self.assertEqual(html.unescape(hero[2]), MIXED_CJK_LEAD)
            self.assertEqual(hero[1], "title-large")

    def test_story_headers_keep_their_wider_column_scale(self):
        for title, expected in zip(REPORTED_LEADS, ("title-short", "title-short", "title-medium")):
            with self.subTest(title=title):
                self.assertEqual(PaperBuilder._title_class(title, "en"), expected)


if __name__ == "__main__":
    unittest.main()
