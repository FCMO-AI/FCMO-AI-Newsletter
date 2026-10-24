"""c6.1 polish: whole story dek, proportionate tablet plate, solid «Shown» swatch, hero probes at tablet widths."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("verificar_c6", ROOT / "tests/oraculos/verificar_c6.py")
oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)

from tools.paper.i18n import visual_width  # noqa: E402
from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module  # noqa: E402
from tools.paper.templates.reader import brief20, first_sentence, rest_after  # noqa: E402

BASE = "/FCMO-AI-Newsletter/"
BROWSER_PROBE = r"""
const { chromium } = require(process.argv[1]);
const jobs = JSON.parse(process.argv[2]);
(async () => {
  const browser = await chromium.launch();
  const out = [];
  for (const job of jobs) {
    const page = await browser.newPage({ viewport: { width: job.width, height: 1200 } });
    await page.goto('file://' + job.file);
    out.push(await page.evaluate(() => {
      const rect = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); return { w: r.width, h: r.height }; };
      const style = (el, pseudo) => { const c = getComputedStyle(el, pseudo || null); return { bg: c.backgroundColor, image: c.backgroundImage, border: c.borderTopStyle, borderWidth: c.borderTopWidth, content: c.content, opacity: c.opacity, color: c.color, display: c.display }; };
      const plate = document.querySelector('.story-cover .plate');
      const swatch = (sel) => { const el = document.querySelector(sel); return el ? { box: rect(el), style: style(el), after: style(el, '::after'), rowOpacity: getComputedStyle(el.closest('div') || el).opacity } : null; };
      return { plate: plate && { box: rect(plate), display: getComputedStyle(plate).display }, zeroShown: swatch('.er-legend .er-zero .sample-shown'),
               claimed: swatch('.er-legend .sample-claimed'), gap: swatch('.er-legend .sample-gap'), zeroRows: document.querySelectorAll('.er-legend .er-zero').length };
    }));
    await page.close();
  }
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
"""

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


class BuiltPageBehaviour(unittest.TestCase):
    """The plate and the «Shown» swatch, judged by what Chromium computes on pages the real build wrote."""

    @classmethod
    def setUpClass(cls):
        cls.module = resolve_playwright_module()
        if not cls.module:
            raise unittest.SkipTest(missing_playwright_message())
        cls.tmp = tempfile.TemporaryDirectory(prefix="c6-polish-")
        out = Path(cls.tmp.name) / "site"
        built = subprocess.run([sys.executable, str(ROOT / "tools/paper/build.py"),
                                "--stories", str(ROOT / "site/data/stories.v2.json"),
                                "--status", str(ROOT / "site/data/newsroom-status.json"),
                                "--editorial", str(ROOT / "editorial"), "--out", str(out), "--base", BASE],
                               cwd=ROOT, text=True, capture_output=True)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        css = (out / "assets/css/paper.css").read_text(encoding="utf-8")
        routes = json.loads((out / "data/routes.json").read_text(encoding="utf-8"))
        cls.pages = []
        for row in [r for r in routes if r["kind"] == "story" and r["locale"] == "en"]:
            html_text = (out / row["path"] / "index.html").read_text(encoding="utf-8")
            if re.search(r'class="er-zero"><dt><span class="sample sample-shown"', html_text) and re.search(r'<dl class="er-legend">.*sample-claimed.*sample-gap', html_text, re.S) and "story-cover" in html_text:
                target = Path(cls.tmp.name) / f"page{len(cls.pages)}.html"
                target.write_text(re.sub(r"<script\b.*?</script>", "", re.sub(r'<link rel="stylesheet" href="[^"]*paper\.css">', lambda _: f"<style>{css}</style>", html_text), flags=re.S), encoding="utf-8")
                cls.pages.append(target)
            if len(cls.pages) == 2:
                break
        if not cls.pages:
            raise AssertionError("no built story page has a zero-Shown legend row with Claimed and Not-established samples")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def measure(self, width):
        jobs = [{"file": str(page), "width": width} for page in self.pages]
        result = subprocess.run(["node", "-e", BROWSER_PROBE, self.module, json.dumps(jobs)], text=True, capture_output=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_story_plate_is_proportionate_between_761_and_1100(self):
        for width in (820, 1100):
            for found in self.measure(width):
                box = found["plate"]["box"]
                self.assertGreaterEqual(box["w"] / box["h"], 2.5, f"plate {box} at {width}")

    def test_story_plate_keeps_its_desktop_shape_and_is_gone_on_a_phone(self):
        for found in self.measure(1440):
            box = found["plate"]["box"]
            self.assertLess(box["w"] / box["h"], 2.0, box)
        for found in self.measure(390):
            self.assertEqual(found["plate"]["display"], "none")

    def test_shown_swatch_is_solid_and_the_zero_state_adds_no_box_numeral_or_dimming(self):
        for found in self.measure(1440):
            shown = found["zeroShown"]
            self.assertGreater(shown["box"]["w"], 8)
            self.assertNotIn(shown["style"]["bg"], ("rgba(0, 0, 0, 0)", "transparent"))
            self.assertEqual(shown["style"]["bg"], shown["style"]["color"], "a solid swatch is filled with the text colour")
            self.assertIn(shown["after"]["content"], ("none", "normal"))
            self.assertEqual(shown["rowOpacity"], "1")
            self.assertEqual(shown["style"]["image"], "none")
            self.assertIn("gradient", found["claimed"]["style"]["image"])
            self.assertEqual(found["gap"]["style"]["border"], "dashed")
            self.assertEqual(found["gap"]["style"]["bg"], "rgba(0, 0, 0, 0)")


class HeaderDekTests(unittest.TestCase):
    LONG = ("The authors report that a fixed meta-agent, working over four long-horizon benchmarks and ten models, "
            "proposes localized memory edits, keeps only those that a deterministic held-out validation gate accepts, "
            "and so improves 35 of 37 completed model-benchmark pairs while the downstream model stays frozen and the harness keeps its verified working state across every run in the study, and the authors add that released code, frozen splits and memory packages make the whole mechanism inspectable by outside groups who wish to repeat it. "
            "A second sentence follows.")

    def test_a_long_sentence_is_cut_between_clauses_within_the_eight_line_budget(self):
        cut = first_sentence(self.LONG, 480, clause=True)
        self.assertLessEqual(visual_width(cut), 480)
        self.assertTrue(cut.endswith("…"))
        self.assertIn(cut[:-1][-1], "abcdefghijklmnopqrstuvwxyz0123456789", "the cut keeps whole words")
        self.assertTrue(self.LONG.startswith(cut[:-1]))
        self.assertIn(self.LONG[len(cut) - 1], ",;:— ", "the cut lands on a clause boundary")

    def test_zh_clause_cut_lands_on_a_clause_mark(self):
        text = "。".join(["Scale AI的一篇预印本评估了在14项继任模型训练任务和16种侧任务中隐蔽植入目标的情况，作者报告在374次受控攻击测试中有135次植入了侧任务且保留了主任务表现，总体有180次达成侧任务目标，" * 3 + "结束"])
        cut = first_sentence(text, 170, clause=True)
        self.assertLessEqual(visual_width(cut), 170)
        self.assertTrue(cut.endswith("…"))
        self.assertEqual(text[len(cut) - 1], "，")

    def test_a_sentence_that_fits_is_kept_whole(self):
        self.assertEqual(first_sentence(ZH_DEK, 480, clause=True), ZH_DEK.split("。")[0] + "。")

    def test_what_happened_continues_after_the_header_sentence(self):
        summary = "First claim of the story. Second sentence adds the detail. Third closes."
        self.assertEqual(rest_after(summary, "First claim of the story."), "Second sentence adds the detail. Third closes.")
        cell = brief20({}, _catalog(), summary=summary, why="Why it matters. More.", evidence={}, header_dek="First claim of the story.")
        self.assertNotIn("First claim", cell)
        self.assertIn("Second sentence adds the detail.", cell)

    def test_a_one_sentence_summary_is_never_emptied(self):
        summary = "Only one sentence here."
        self.assertEqual(rest_after(summary, "Only one sentence here."), summary)
        cell = brief20({}, _catalog(), summary=summary, why="Why.", evidence={}, header_dek="Only one sentence here.")
        self.assertIn("Only one sentence here.", cell)

    def test_a_different_header_dek_leaves_the_summary_alone(self):
        summary = "First claim. Second."
        self.assertEqual(rest_after(summary, "Something else entirely."), summary)


def _catalog():
    from tools.paper.i18n import load_catalogs
    return load_catalogs(ROOT)["en"]


class BuiltDekRepeatTests(unittest.TestCase):
    """Zero story pages in any locale say the header sentence again as the first thing under «What happened»."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="c6-dek-")
        cls.out = Path(cls.tmp.name) / "site"
        built = subprocess.run([sys.executable, str(ROOT / "tools/paper/build.py"),
                                "--stories", str(ROOT / "site/data/stories.v2.json"),
                                "--status", str(ROOT / "site/data/newsroom-status.json"),
                                "--editorial", str(ROOT / "editorial"), "--out", str(cls.out), "--base", BASE],
                               cwd=ROOT, text=True, capture_output=True)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        cls.routes = json.loads((cls.out / "data/routes.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_no_story_page_reads_the_same_sentence_twice_in_a_row(self):
        import html as htmllib
        norm = lambda t: re.sub(r"\s+", "", htmllib.unescape(re.sub(r"<[^>]+>", "", t))).rstrip("….。.")
        repeats, seen = [], {}
        for row in [r for r in self.routes if r["kind"] == "story"]:
            text = (self.out / row["path"] / "index.html").read_text(encoding="utf-8")
            dek = re.search(r'<p class="story-dek">(.*?)</p>', text, re.S)
            cell = re.search(r'<span class="brief-val">(.*?)</span>', text, re.S)
            seen[row["locale"]] = seen.get(row["locale"], 0) + 1
            self.assertIsNotNone(cell, row["path"])
            self.assertTrue(norm(cell.group(1)), f"empty «What happened» on {row['path']}")
            if dek and norm(dek.group(1)) == norm(cell.group(1)):
                repeats.append(row["path"])
        self.assertEqual(set(seen), {"en", "es-419", "zh-Hans"})
        self.assertEqual(repeats, [])

    def test_the_story_dek_never_ends_mid_clause_unless_the_sentence_is_over_budget(self):
        for row in [r for r in self.routes if r["kind"] == "story"]:
            text = (self.out / row["path"] / "index.html").read_text(encoding="utf-8")
            dek = re.search(r'<p class="story-dek">(.*?)</p>', text, re.S)
            if dek:
                import html as htmllib
                self.assertLessEqual(visual_width(htmllib.unescape(dek.group(1))), 480, row["path"])


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
