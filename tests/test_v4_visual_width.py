"""Truncation by visual width: a Han dek takes as much room as a Latin one, not twice as much."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.paper.i18n import dek, field, load_catalogs, truncate, visual_width  # noqa: E402

STORIES = ROOT / "site/data/stories.v2.json"
LIMITS = (160, 180, 190, 220)


def old_truncate(text: str, limit: int = 160) -> str:
    """The character-count algorithm this pass replaced, kept verbatim as the Latin-text oracle."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    shortened = text[:limit - 1].rsplit(" ", 1)[0]
    return (shortened or text[:limit - 1]).rstrip(".,;: ") + "…"


class VisualWidthTests(unittest.TestCase):
    def test_wide_and_fullwidth_count_two_everything_else_one(self):
        self.assertEqual(visual_width(""), 0)
        self.assertEqual(visual_width("abc 123"), 7)
        self.assertEqual(visual_width("汉字"), 4)
        self.assertEqual(visual_width("ab汉，"), 6)          # ， is fullwidth (F)
        self.assertEqual(visual_width("ＡＢ"), 4)            # fullwidth Latin (F)
        self.assertEqual(visual_width("…·—"), 3)            # ambiguous width counts one
        self.assertEqual(visual_width("ｱｲ"), 2)             # halfwidth katakana (H)
        self.assertEqual(visual_width("é ñ ü"), 5)


class TruncateTests(unittest.TestCase):
    def test_text_that_fits_is_only_normalized(self):
        self.assertEqual(truncate("短句。", 190), "短句。")
        self.assertEqual(truncate("  two   words\n", 190), "two words")
        self.assertEqual(truncate("汉" * 95, 190), "汉" * 95)

    def test_han_text_is_cut_by_width_not_by_characters(self):
        result = truncate("汉" * 300, 190)
        self.assertEqual(result, "汉" * 94 + "…")
        self.assertEqual(visual_width(result), 189)

    def test_a_cut_inside_a_latin_run_backs_out_to_the_run_start(self):
        self.assertEqual(truncate("汉" * 93 + "abcdefgh", 190), "汉" * 93 + "…")
        self.assertEqual(truncate("汉" * 93 + "GPT5 模型", 190), "汉" * 93 + "…")

    def test_a_latin_prefix_uses_the_old_rule_and_a_long_run_backs_out_to_the_last_han(self):
        text = "a" * 200 + "汉"
        self.assertEqual(truncate(text, 190), old_truncate(text, 190))
        self.assertEqual(truncate("汉" + "a" * 200, 190), "汉…")

    def test_a_cut_at_a_run_edge_keeps_the_whole_run(self):
        # The cut falls right after "abc": the next character is Han, so nothing backs out.
        self.assertEqual(truncate("汉" * 93 + "abc" + "汉" * 10, 190), "汉" * 93 + "abc…")

    def test_trailing_ascii_and_cjk_punctuation_is_removed(self):
        mixed = truncate("在 GLM 5.2 上提升 53%，" * 30, 190)
        self.assertTrue(mixed.endswith("…"))
        self.assertFalse(mixed[:-1].endswith(("，", " ", ".")), mixed)
        self.assertLessEqual(visual_width(mixed), 190)
        self.assertGreaterEqual(visual_width(mixed), 175)
        self.assertEqual(truncate("汉" * 93 + "，、；：。" + "汉" * 10, 190), "汉" * 93 + "…")
        self.assertEqual(truncate("汉" * 92 + "汉. " + "汉" * 10, 190), "汉" * 93 + "…")

    def test_latin_text_keeps_the_old_word_boundary_output(self):
        words = " ".join(["word"] * 100)
        self.assertEqual(truncate(words, 190), words[:189].rsplit(" ", 1)[0].rstrip(".,;: ") + "…")
        self.assertEqual(truncate("x" * 400, 190), "x" * 189 + "…")

    def test_result_never_exceeds_the_limit(self):
        pieces = ("汉", "字", "a", "b", "1", " ", "，", "。", ".", "…", "Ａ", "—")
        for size, limit in itertools.product((1, 7, 13, 60), (1, 2, 3, 10, 50, 190)):
            for combo in itertools.islice(itertools.product(pieces, repeat=3), 0, None, 37):
                text = "".join(combo) * size
                with self.subTest(text=text[:12], size=size, limit=limit):
                    self.assertLessEqual(visual_width(truncate(text, limit)), max(limit, 1))


class CorpusSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stories = json.loads(STORIES.read_text(encoding="utf-8"))["stories"]
        cls.catalog = load_catalogs(ROOT)["zh-Hans"]

    def test_english_and_spanish_deks_truncate_exactly_as_before(self):
        compared = shortened = 0
        for story, locale, key, limit in itertools.product(self.stories, ("en", "es-419"), ("dek", "summary"), LIMITS):
            text = field(story, locale, key)
            if not isinstance(text, str) or not text:
                continue
            compared += 1
            shortened += old_truncate(text, limit) != " ".join(text.split())
            with self.subTest(story=story["id"], locale=locale, key=key, limit=limit):
                self.assertEqual(truncate(text, limit), old_truncate(text, limit))
        self.assertGreater(compared, 200)
        self.assertGreater(shortened, 20)

    def test_every_live_chinese_dek_fits_190_columns(self):
        live = [story for story in self.stories if story.get("status") == "live"]
        self.assertGreater(len(live), 20)
        cut = 0
        for story in live:
            text = dek(story, "zh-Hans", self.catalog)
            result = truncate(text, 190)
            cut += result != " ".join(text.split())
            with self.subTest(story=story["id"]):
                self.assertLessEqual(visual_width(result), 190)
                self.assertFalse(result.endswith("，"), result)
                self.assertFalse(result.endswith("，…"), result)
        self.assertGreater(cut, 0)


if __name__ == "__main__":
    unittest.main()
