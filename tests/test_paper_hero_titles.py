"""Regression for the 2026-10-27 cover leads that blocked the browser gate."""
import html
import os
from pathlib import Path
import re
import subprocess
import sys
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
SPANISH_LEAD = (
    "La ficha de seguridad de OpenAI informa resultados mixtos sobre seguridad y "
    "autorización para GPT-6.1 Terra"
)
# Sanitized typography probes, never publication data. Include long words and
# wide capitals: character count alone does not predict the number of lines.
LONG_HERO_PROBES = (
    ("es-419", SPANISH_LEAD),
    ("es-419", SPANISH_LEAD + " y nuevas evaluaciones"),
    ("es-419", "La investigación documenta autorizaciones y responsabilidades empresariales "
     "en sistemas de inteligencia artificial de uso habitual"),
    ("en", "ANVIL separates LLM formulation from deterministic optimization-code compilation"),
    ("en", "Anthropic reports Claude-authored machine-checked proofs across OSS-Fuzz RISC-V binaries"),
    ("zh-Hans", MIXED_CJK_LEAD),
    ("zh-Hans", "研究报告分析人工智能系统在企业任务中的安全性授权边界以及可靠性验证方法" * 2),
    ("zh-Hans", "研究安全授权边界" * 10),
)


class PaperHeroTitleTests(unittest.TestCase):
    def test_browser_battery_rejects_bad_measurements_with_a_fake(self):
        # This verifies the runnable battery's failure logic, not real layout.
        fake = """
exports.chromium = {launch: async () => ({
  close: async () => {}, newPage: async () => ({
    route: async () => {}, setViewportSize: async () => {}, goto: async () => {},
    evaluate: async (_, probe) => ({
      text: process.env.PROBE_LOST_TEXT ? '' : probe.text,
      lines: Number(process.env.PROBE_LINES || 3),
      height: Number(process.env.PROBE_HEIGHT || 100),
      overflow: Number(process.env.PROBE_OVERFLOW || 0),
      nextTop: process.env.PROBE_MISSING_NEXT ? null : 500
    })
  })
})};
"""
        with tempfile.TemporaryDirectory(prefix="paper-hero-browser-fake-") as temporary:
            module = Path(temporary) / "playwright.cjs"
            module.write_text(fake, encoding="utf-8")
            for mutation in ({}, {"PROBE_LINES": "5"}, {"PROBE_HEIGHT": "380"},
                             {"PROBE_OVERFLOW": "1"}, {"PROBE_MISSING_NEXT": "1"},
                             {"PROBE_LOST_TEXT": "1"}):
                with self.subTest(mutation=mutation):
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "tests/check_paper_hero_titles.py"), temporary],
                        env={**os.environ, "PLAYWRIGHT_MODULE": str(module), **mutation},
                        capture_output=True, text=True, cwd=ROOT, timeout=30,
                    )
                    self.assertEqual(result.returncode, 1 if mutation else 0, result.stdout + result.stderr)
                    self.assertEqual(len(result.stdout.splitlines()), 2 * len(LONG_HERO_PROBES))

    def test_exact_spanish_lead_leaves_the_five_line_scale(self):
        self.assertEqual(len(SPANISH_LEAD), 107)
        self.assertEqual([len(title) for code, title in LONG_HERO_PROBES if code == "es-419"], [107, 129, 130])
        self.assertEqual(PaperBuilder._title_class(SPANISH_LEAD, "es-419", hero=True), "title-extra-compact")
        # This title still belongs to title-large in the wider story header.
        self.assertEqual(PaperBuilder._title_class(SPANISH_LEAD, "es-419"), "title-large")

    def test_hero_has_independent_compact_and_extra_compact_steps(self):
        for title, expected, story_expected in (
            (LONG_HERO_PROBES[3][1], "title-compact", "title-medium"),
            (LONG_HERO_PROBES[4][1], "title-extra-compact", "title-medium"),
        ):
            with self.subTest(title=title):
                self.assertEqual(PaperBuilder._title_class(title, "en", hero=True), expected)
                self.assertEqual(PaperBuilder._title_class(title, "en"), story_expected)

    def test_long_localized_covers_keep_the_complete_text(self):
        with tempfile.TemporaryDirectory(prefix="paper-hero-long-") as temporary:
            builder = PaperBuilder(
                stories_path=FIXTURES / "stories.v2.json",
                status_path=FIXTURES / "newsroom-status.fresh.json",
                out=Path(temporary), base="/FCMO-AI-Newsletter/",
            )
            lead = front_order(builder.live)[0]
            for code, title in LONG_HERO_PROBES:
                with self.subTest(locale=code, title=title):
                    locale = next(row for row in builder.config["locales"] if row["code"] == code)
                    if code == "en":
                        lead["headline"] = title
                    else:
                        lead["l10n"][code]["fields"]["headline"] = title
                    builder._front(locale)
                    prefix = {"en": "", "es-419": "es", "zh-Hans": "zh"}[code]
                    page = (Path(temporary) / prefix / "index.html").read_text(encoding="utf-8")
                    hero = re.search(r'<h1 class="cover-title ([^"]+)"><a href="[^"]+">(.*?)</a></h1>', page)
                    self.assertIsNotNone(hero)
                    self.assertEqual(html.unescape(hero[2]), title)
                    self.assertEqual(hero[1], PaperBuilder._title_class(title, code, hero=True))

    def test_reported_leads_take_the_smaller_hero_step(self):
        # Round 2 explicitly adds hero compact cutoffs. The 42-unit NgramRL
        # lead now takes that step; the two shorter round-1 leads stay large.
        for title, expected in zip(REPORTED_LEADS, ("title-large", "title-large", "title-compact")):
            with self.subTest(title=title):
                self.assertEqual(PaperBuilder._title_class(title, "en", hero=True), expected)

    def test_rendered_cover_keeps_the_complete_reported_title(self):
        with tempfile.TemporaryDirectory(prefix="paper-hero-title-") as temporary:
            builder = PaperBuilder(
                stories_path=FIXTURES / "stories.v2.json",
                status_path=FIXTURES / "newsroom-status.fresh.json",
                out=Path(temporary), base="/FCMO-AI-Newsletter/",
            )
            locale = next(row for row in builder.config["locales"] if row["code"] == "en")
            lead = front_order(builder.live)[0]
            for title, expected in zip(REPORTED_LEADS, ("title-large", "title-large", "title-compact")):
                with self.subTest(title=title):
                    lead["headline"] = title
                    builder._front(locale)
                    page = (Path(temporary) / "index.html").read_text(encoding="utf-8")
                    hero = re.search(r'<h1 class="cover-title ([^"]+)"><a href="[^"]+">(.*?)</a></h1>', page)
                    self.assertIsNotNone(hero)
                    self.assertEqual(html.unescape(hero[2]), title)
                    self.assertEqual(hero[1], expected)

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
