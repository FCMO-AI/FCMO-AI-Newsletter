"""Falsifiers for the c6 browser oracle's tablet top-bar and landing-hero checks.

The oracle (tests/oraculos/verificar_c6.py) measures in Chromium, then judges with
pure functions. These tests feed those functions a healthy measurement and then
mutated ones (the defects the oracle must catch) and require red on each mutation.
"""

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("verificar_c6", ROOT / "tests/oraculos/verificar_c6.py")
oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)


def healthy_job(width=820, locale="en", route="home"):
    return {
        "locale": locale, "width": width, "route": route, "overflowPx": 0, "axe": [],
        "topbar": {
            "barOverflow": 0, "innerOverflow": 0, "barHeight": 56,
            "mark": {"top": 14, "bottom": 42, "left": 24, "right": 140, "lineHeight": 18, "textLines": 1, "whiteSpace": "nowrap"},
            "cta": {"top": 10, "bottom": 46, "left": width - 140, "right": width - 24, "shown": True},
            "ctaHit": True,
        },
    }


def healthy_hero(locale="en"):
    return {"locale": locale, "width": 1440, "route": "hero", "results": [
        {"units": 84, "cls": "title-extra-compact", "lines": 4, "dekTop": 560.0},
    ]}


class TopBarOracle(unittest.TestCase):
    def test_healthy_bar_is_green_at_every_wide_width(self):
        for width in (820, 1100, 1440):
            self.assertEqual(oracle.evaluate(healthy_job(width)), [])

    def test_tablet_widths_are_in_the_sweep(self):
        self.assertIn(820, oracle.WIDTHS)
        self.assertIn(1100, oracle.WIDTHS)
        self.assertIn(390, oracle.WIDTHS)
        self.assertIn(1440, oracle.WIDTHS)

    def test_phone_width_does_not_require_the_top_bar(self):
        job = healthy_job(390)
        job["topbar"]["cta"] = None
        self.assertEqual(oracle.evaluate_topbar(job), [])

    def test_wide_element_in_top_bar_goes_red(self):
        job = healthy_job()
        job["topbar"]["innerOverflow"] = 96
        out = oracle.evaluate(job)
        self.assertTrue(any("topbar-overflow" in line for line in out), out)

    def test_bar_box_overflow_goes_red(self):
        job = healthy_job()
        job["topbar"]["barOverflow"] = 1
        self.assertTrue(any("topbar-overflow" in line for line in oracle.evaluate(job)))

    def test_wrapping_wordmark_goes_red(self):
        job = healthy_job()
        job["topbar"]["mark"]["textLines"] = 2
        out = oracle.evaluate(job)
        self.assertTrue(any("wordmark" in line for line in out), out)

    def test_hidden_subscribe_goes_red(self):
        job = healthy_job()
        job["topbar"]["cta"]["shown"] = False
        out = oracle.evaluate(job)
        self.assertTrue(any("subscribe-cta" in line for line in out), out)

    def test_missing_subscribe_goes_red(self):
        job = healthy_job()
        job["topbar"]["cta"] = None
        self.assertTrue(any("subscribe-cta" in line for line in oracle.evaluate(job)))

    def test_subscribe_pushed_off_screen_goes_red(self):
        job = healthy_job(820)
        job["topbar"]["cta"]["left"], job["topbar"]["cta"]["right"] = 900, 1010
        self.assertTrue(any("subscribe-cta" in line for line in oracle.evaluate(job)))

    def test_subscribe_covered_goes_red(self):
        job = healthy_job()
        job["topbar"]["ctaHit"] = False
        self.assertTrue(any("subscribe-cta" in line for line in oracle.evaluate(job)))

    def test_missing_topbar_goes_red(self):
        job = healthy_job()
        job["topbar"] = None
        self.assertTrue(any("no .topbar" in line for line in oracle.evaluate(job)))

    def test_document_overflow_still_goes_red(self):
        job = healthy_job()
        job["overflowPx"] = 12
        self.assertTrue(any("overflow" in line for line in oracle.evaluate(job)))

    def test_each_mutation_is_independent(self):
        base = healthy_job()
        mutated = copy.deepcopy(base)
        mutated["topbar"]["mark"]["textLines"] = 3
        self.assertEqual(oracle.evaluate(base), [])
        self.assertNotEqual(oracle.evaluate(mutated), [])


class HeroOracle(unittest.TestCase):
    def test_healthy_hero_is_green(self):
        self.assertEqual(oracle.evaluate(healthy_hero()), [])

    def test_five_line_hero_goes_red(self):
        job = healthy_hero()
        job["results"][0]["lines"] = 5
        self.assertTrue(any("lines=5" in line for line in oracle.evaluate(job)))

    def test_next_line_below_900_goes_red(self):
        job = healthy_hero()
        job["results"][0]["dekTop"] = 900.0
        self.assertTrue(oracle.evaluate(job))

    def test_missing_next_line_goes_red(self):
        job = healthy_hero()
        job["results"][0]["dekTop"] = None
        self.assertTrue(oracle.evaluate(job))

    def test_missing_h1_goes_red(self):
        job = healthy_hero()
        job["results"] = [{"units": 30, "cls": "title-short", "missing": True}]
        self.assertTrue(oracle.evaluate(job))


class HeroProbes(unittest.TestCase):
    def test_class_comes_from_the_build_function(self):
        from tools.paper.build import PaperBuilder
        for locale in ("en", "es-419", "zh-Hans"):
            for probe in oracle.hero_probes(locale):
                self.assertEqual(probe["cls"], PaperBuilder._title_class(probe["text"], locale, hero=True))

    def test_probes_span_the_class_change(self):
        for locale in ("en", "es-419", "zh-Hans"):
            classes = {p["cls"] for p in oracle.hero_probes(locale)}
            self.assertGreaterEqual(len(classes), 3, (locale, classes))

    def test_probe_widths_are_ordered_and_reach_their_target(self):
        for locale in ("en", "zh-Hans"):
            widths = [oracle._units(p["text"], locale) for p in oracle.hero_probes(locale)]
            self.assertEqual(widths, sorted(widths))
            for target, width in zip(oracle.HERO_UNITS, widths):
                self.assertGreaterEqual(width, target)

    def test_han_probe_is_han(self):
        text = oracle.hero_probes("zh-Hans")[-1]["text"]
        self.assertTrue(all("一" <= ch <= "鿿" for ch in text))


if __name__ == "__main__":
    unittest.main()
