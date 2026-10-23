"""c6.1 polish: whole story dek, proportionate tablet plate, solid «Shown» swatch, hero probes at tablet widths."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("verificar_c6", ROOT / "tests/oraculos/verificar_c6.py")
oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)

from tools.paper.i18n import visual_width  # noqa: E402
from tools.paper.templates.reader import first_sentence  # noqa: E402

CSS = (ROOT / "site-src/assets/css/paper.css").read_text(encoding="utf-8")

ZH_DEK = ("Scale AI的一篇预印本评估了在14项继任模型训练任务和16种侧任务中隐蔽植入目标的情况。"
          "作者报告，在374次受控攻击测试中，有135次植入了侧任务且保留了主任务表现；总体有180次达成侧任务目标。")
EN_DEK = ("A Scale AI preprint tests covert side-task installation across 14 successor-training tasks and 16 side tasks. "
          "In 374 controlled attack runs, the authors report 135 installations.")


class WholeDekTests(unittest.TestCase):
    def test_story_dek_is_the_whole_first_sentence_never_cut_mid_sentence(self):
        zh = first_sentence(ZH_DEK, 320)
        self.assertTrue(zh.endswith("情况。"), zh)
        self.assertNotIn("…", zh)
        en = first_sentence(EN_DEK, 320)
        self.assertTrue(en.endswith("16 side tasks."), en)

    def test_the_old_160_column_cut_would_have_clipped_the_zh_claim(self):
        from tools.paper.i18n import truncate
        self.assertTrue(truncate(ZH_DEK, 160).endswith("…"))
        self.assertLessEqual(visual_width(first_sentence(ZH_DEK, 320)), 160)

    def test_the_story_header_gets_the_whole_sentence_while_meta_keeps_the_short_form(self):
        source = (ROOT / "tools/paper/build.py").read_text(encoding="utf-8")
        self.assertIn("dek_text=first_sentence(dek(story, code, catalog), 320)", source)
        self.assertIn("description = truncate(dek(story, code, catalog))", source)


class TabletPlateTests(unittest.TestCase):
    def test_story_plate_is_proportionate_between_761_and_1100(self):
        match = re.search(r"@media\(min-width:761px\) and \(max-width:1100px\)\{body \.story-cover \.plate\{aspect-ratio:(\d+)/(\d+)\}\}", CSS)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)) / int(match.group(2)), 2.5)


class ShownSwatchTests(unittest.TestCase):
    def test_shown_swatch_is_solid_and_the_zero_state_adds_no_box_numeral_or_dimming(self):
        self.assertIn(".sample-shown{background:var(--fg,var(--ink))}", CSS)
        self.assertNotIn('.er-zero .sample::after{content:"0"}', CSS)
        self.assertNotIn(".er-zero{opacity", CSS)
        self.assertIn(".sample-claimed{background:repeating-linear-gradient", CSS)
        self.assertIn(".sample-gap{border:2px dashed", CSS)


class HeroProbeWidthTests(unittest.TestCase):
    def test_probes_run_at_tablet_and_desktop_widths_for_every_locale(self):
        self.assertEqual(oracle.HERO_WIDTHS, (820, 1100, 1440))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "data").mkdir()
            routes = [{"kind": "story", "locale": loc, "path": f"/{loc}/s/"} for loc in oracle.LOCALE_PREFIX]
            (out / "data/routes.json").write_text(json.dumps(routes), encoding="utf-8")
            jobs = oracle.build_plan(out)
        seen = {(j["locale"], j["width"]) for j in jobs if j["route"] == "hero"}
        self.assertEqual(seen, {(loc, w) for loc in oracle.LOCALE_PREFIX for w in oracle.HERO_WIDTHS})

    def test_a_five_line_hero_at_820_goes_red_and_names_the_width(self):
        job = {"locale": "en", "width": 820, "route": "hero",
               "results": [{"units": 84, "cls": "title-extra-compact", "lines": 5, "dekTop": 500.0}]}
        problems = oracle.evaluate(job)
        self.assertEqual(len(problems), 1)
        self.assertIn("820px", problems[0])

    def test_a_next_line_below_the_first_screen_at_1100_goes_red(self):
        job = {"locale": "zh-Hans", "width": 1100, "route": "hero",
               "results": [{"units": 70, "cls": "title-compact", "lines": 2, "dekTop": 901.0}]}
        self.assertEqual(len(oracle.evaluate(job)), 1)


if __name__ == "__main__":
    unittest.main()
