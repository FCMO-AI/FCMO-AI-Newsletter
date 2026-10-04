"""Front-page plan: every story on the FCMO AI daily appears in exactly one block."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.gates import run_all  # noqa: E402
from tools.paper.build import PaperBuilder  # noqa: E402
from tools.paper.front_order import front_order  # noqa: E402
from tools.paper.front_plan import front_plan  # noqa: E402
from tools.paper.i18n import headline, load_catalogs, plural  # noqa: E402

STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))
BEATS = ("technology", "business", "policy", "society", "research")
LEAD = re.compile(r'<article class="lead">.*?<h[13][^>]*><a href="([^"]+)"', re.S)
TOP = re.compile(r'<aside class="top-stories">(.*?)</aside>', re.S)
DEVELOPING = re.compile(r'<section class="developing-well">(.*?)</section>', re.S)
ESSENTIALS = re.compile(r'<section class="essentials">.*?<ol>(.*?)</ol>', re.S)
BEAT_SECTION = re.compile(r'<section class="beat-section">(.*?)</section>', re.S)
CARD_ID = re.compile(r'<article class="story-card" data-story-id="([^"]+)"')
ESSENTIAL_ITEM = re.compile(r'<li( [^>]*)>(.*?)</li>', re.S)
EDITION_CARD = re.compile(
    r'<article class="story-card edition-card"><h3><a href="([^"]+)">([^<]+)</a></h3>'
    r'<p class="edition-count">([^<]+)</p><p class="edition-lead"><a href="([^"]+)">([^<]+)</a></p></article>')


def S(rid: str, beat: str = "technology", confidence: str = "confirmed") -> dict:
    return {"id": rid, "beat": beat, "confidence": confidence}


def ids(stories: list[dict]) -> list[str]:
    return [story["id"] for story in stories]


def everything(plan: dict) -> list[str]:
    lead = [plan["lead"]["id"]] if plan["lead"] else []
    return (lead + ids(plan["top"]) + ids(plan["developing"]) + ids(plan["essentials"])
            + [rid for values in plan["beats"].values() for rid in ids(values)])


class FrontPlanUnitTests(unittest.TestCase):
    def setUp(self):
        # Twenty stories, in the order front_order would give them.
        self.order = [S(f"S{n:02d}", beat=("technology", "business", "policy")[n % 3],
                        confidence="claimed" if n in (3, 6, 9, 14) else "confirmed") for n in range(20)]

    def test_empty_order_gives_an_empty_plan(self):
        self.assertEqual(front_plan([], BEATS),
                         {"lead": None, "top": [], "developing": [], "essentials": [], "beats": {}})

    def test_lead_and_top_are_the_head_of_the_order(self):
        plan = front_plan(self.order, BEATS)
        self.assertIs(plan["lead"], self.order[0])
        self.assertEqual(ids(plan["top"]), ["S01", "S02", "S03", "S04"])

    def test_developing_takes_the_first_two_unsettled_stories_after_the_top(self):
        plan = front_plan(self.order, BEATS)
        # S03 is unsettled but already a top story; S06 and S09 come next.
        self.assertEqual(ids(plan["developing"]), ["S06", "S09"])
        self.assertEqual(ids(front_plan(self.order[:5], BEATS)["developing"]), [])

    def test_essentials_are_the_next_five_unused_stories(self):
        plan = front_plan(self.order, BEATS)
        self.assertEqual(ids(plan["essentials"]), ["S05", "S07", "S08", "S10", "S11"])

    def test_beats_are_greedy_in_the_given_order_and_empty_beats_are_omitted(self):
        plan = front_plan(self.order, BEATS)
        self.assertEqual(list(plan["beats"]), ["technology", "business", "policy"])
        self.assertEqual({beat: ids(values) for beat, values in plan["beats"].items()},
                         {"technology": ["S12", "S15", "S18"], "business": ["S13", "S16", "S19"],
                          "policy": ["S14", "S17"]})
        reversed_plan = front_plan(self.order, tuple(reversed(BEATS)))
        self.assertEqual(list(reversed_plan["beats"]), ["policy", "business", "technology"])

    def test_a_beat_never_repeats_a_story_from_an_earlier_block(self):
        # Kills the mutation "beat sections ignore what was already shown": every
        # story before S12 is used, so an unfiltered technology beat would start at S00.
        plan = front_plan(self.order, BEATS)
        self.assertNotIn("S00", ids(plan["beats"]["technology"]))
        order = [S("A", "policy"), S("B", "policy"), S("C", "policy"), S("D", "policy"), S("E", "policy"),
                 S("F", "policy"), S("G", "business")]
        plan = front_plan(order, ("policy", "business"))
        self.assertEqual(ids(plan["essentials"]), ["F", "G"])
        self.assertEqual(plan["beats"], {})

    def test_no_story_appears_twice_and_duplicate_beats_do_not_repeat(self):
        plan = front_plan(self.order, BEATS + ("technology",))
        shown = everything(plan)
        self.assertEqual(len(shown), len(set(shown)))
        self.assertEqual(sorted(shown), ids(self.order))

    def test_returns_the_same_dicts_without_mutating_them(self):
        snapshot = json.dumps(self.order, sort_keys=True)
        plan = front_plan(self.order, BEATS)
        blocks = [plan["lead"], *plan["top"], *plan["developing"], *plan["essentials"],
                  *(story for values in plan["beats"].values() for story in values)]
        for story in blocks:
            self.assertIs(story, self.order[int(story["id"][1:])])
        self.assertEqual(json.dumps(self.order, sort_keys=True), snapshot)

    def test_short_orders_fill_only_what_they_can(self):
        plan = front_plan(self.order[:3], BEATS)
        self.assertEqual(ids(plan["top"]), ["S01", "S02"])
        self.assertEqual(plan["essentials"], [])
        self.assertEqual(plan["beats"], {})


class EditionLeadUnitTests(unittest.TestCase):
    def test_edition_lead_is_ordered_within_its_own_edition(self):
        def story(rid: str, url_date: str, event_at: str, importance: int, title: str) -> dict:
            return {"id": rid, "status": "live", "url_date": url_date, "slug": rid.lower(), "event_at": event_at,
                    "first_published_at": event_at, "importance": importance, "front_page_eligible": False,
                    "title": title}
        newer = story("FCMO-X", "2026-09-20", "2026-09-20T00:00:00Z", 5, "Newer edition story")
        fresher = story("FCMO-A", "2026-09-10", "2026-09-09T00:00:00Z", 1, "Fresher but lighter")
        weightier = story("FCMO-B", "2026-09-10", "2026-09-07T12:00:00Z", 9, "Older but weightier")
        # Across the whole paper A and B fall in different 48 h windows and A comes first; inside
        # their own edition they share one window, so the weightier B leads that edition.
        self.assertEqual(ids(front_order([newer, fresher, weightier])), ["FCMO-X", "FCMO-A", "FCMO-B"])
        with mock.patch.dict(os.environ, {"GHOST_CONTENT_API_KEY": ""}):
            builder = PaperBuilder(stories_path=STORIES, status_path=STATUS, out=Path(tempfile.gettempdir()), base=BASE)
        builder.live = [newer, fresher, weightier]
        english = {"code": "en", "path_prefix": ""}
        card = builder._edition_card("2026-09-10", english)
        self.assertIn('<p class="edition-count">2 stories</p>', card)
        self.assertRegex(card, r'<p class="edition-lead"><a href="[^"]*/2026/09/10/fcmo-b/?">Older but weightier</a></p>')


class FrontPlanBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v4-front-plan-")
        cls.out = Path(cls.temp.name) / "publish"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(STATUS),
             "--out", str(cls.out), "--base", BASE], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        payload = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.live = [story for story in payload["stories"] if story.get("status") == "live"]
        cls.by_id = {story["id"]: story for story in cls.live}
        cls.order = front_order(cls.live)
        cls.catalogs = load_catalogs(ROOT)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, prefix: str) -> str:
        return (self.out / prefix / "diario" / "index.html").read_text(encoding="utf-8")

    def target(self, link: str) -> str:
        self.assertTrue(link.startswith(BASE), link)
        path = self.out / html.unescape(link)[len(BASE):] / "index.html"
        self.assertTrue(path.is_file(), link)
        return path.read_text(encoding="utf-8")

    def resolve(self, link: str) -> str:
        return re.search(r'<main id="main" class="page-shell" data-story-id="([^"]+)"', self.target(link)).group(1)

    def test_no_story_repeats_across_front_blocks(self):
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                page = self.page(prefix)
                shown = [self.resolve(LEAD.search(page).group(1))]
                shown += CARD_ID.findall(TOP.search(page).group(1))
                shown += CARD_ID.findall(DEVELOPING.search(page).group(1))
                shown += [re.search(r'data-story-id="([^"]+)"', item).group(1)
                          for item, _ in ESSENTIAL_ITEM.findall(ESSENTIALS.search(page).group(1))]
                beats = [section for section in BEAT_SECTION.findall(page) if re.search(r'beat/[a-z]+/"', section)]
                self.assertTrue(beats)
                for section in beats:
                    shown += CARD_ID.findall(section)
                self.assertEqual(len(shown), len(set(shown)), shown)
                self.assertGreaterEqual(len(shown), 12)
                self.assertTrue(set(shown) <= set(self.by_id))

    def test_essential_items_carry_only_their_story_id_and_link_to_it(self):
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                listing = ESSENTIALS.search(self.page(prefix)).group(1)
                items = ESSENTIAL_ITEM.findall(listing)
                self.assertEqual(len(items), 5)
                self.assertEqual(listing.count("<li"), 5)
                for attributes, inner in items:
                    story_id = re.fullmatch(r' data-story-id="([^"]+)"', attributes).group(1)
                    link = re.fullmatch(r'<a href="([^"]+)">([^<]+)</a>', inner)
                    self.assertEqual(self.resolve(link.group(1)), story_id)
                    self.assertEqual(html.unescape(link.group(2)),
                                     headline(self.by_id[story_id], locale, self.catalogs[locale]))

    def test_edition_cards_show_count_and_lead_headline(self):
        dates = sorted({story["url_date"] for story in self.live}, reverse=True)[:6]
        self.assertEqual(len(dates), 6)
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                catalog = self.catalogs[locale]
                page = self.page(prefix)
                cards = EDITION_CARD.findall(page)
                self.assertEqual(len(cards), 6)
                self.assertEqual(page.count('class="story-card edition-card"'), 6)
                for date, (edition_link, _, count, lead_link, lead_text) in zip(dates, cards):
                    edition = [story for story in self.live if story["url_date"] == date]
                    self.assertTrue(edition_link.endswith(f"edition/{date}/"), edition_link)
                    self.target(edition_link)
                    self.assertEqual(html.unescape(count), plural(catalog, "edition_story", len(edition)))
                    lead = front_order(edition)[0]
                    self.assertEqual(self.resolve(lead_link), lead["id"])
                    self.assertEqual(html.unescape(lead_text), headline(lead, locale, catalog))

    def test_publication_gates_pass_on_the_fresh_build(self):
        results = run_all.run(self.out)
        self.assertEqual(len(results), 14)
        self.assertEqual([result.code for result in results],
                         [gate.__module__.rsplit(".", 1)[-1].upper() for gate in run_all.GATES])
        self.assertIn("NO_FCMO_GROUP", [result.code for result in results])
        self.assertIn("NO_MACHINE_PATHS", [result.code for result in results])


if __name__ == "__main__":
    unittest.main()
