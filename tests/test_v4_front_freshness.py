"""Front-page freshness: the FCMO AI daily leads with what is new, then with what weighs most."""

from __future__ import annotations

import datetime
import html
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import build_deployment_identity  # noqa: E402
from tools.gates import run_all  # noqa: E402
from tools.gates.common import canonical_story_path  # noqa: E402
from tools.paper.front_order import FRESH_WINDOW, front_order  # noqa: E402

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


def parse(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def t(story: dict) -> datetime.datetime:
    """The brief's freshness instant, computed independently of the module under test."""
    return min(parse(story["event_at"]), parse(story.get("first_published_at") or story["event_at"]))


def S(rid: str, event_at: str | None, importance: float, eligible: bool,
      published: str | None = "2026-09-12T00:00:00Z") -> dict:
    story = {"id": rid, "status": "live", "importance": importance, "front_page_eligible": eligible}
    if event_at is not None:
        story["event_at"] = event_at
    if published is not None:
        story["first_published_at"] = published
    return story


def ids(stories: list[dict]) -> list[str]:
    return [story["id"] for story in stories]


def build(out: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(STATUS),
         "--out", str(out), "--base", BASE],
        cwd=ROOT, text=True, capture_output=True,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)


class FrontOrderUnitTests(unittest.TestCase):
    def test_window_is_48_hours_and_empty_input_is_empty(self):
        self.assertEqual(FRESH_WINDOW, datetime.timedelta(hours=48))
        self.assertEqual(front_order([]), [])

    def test_fresh_eligible_story_beats_old_weighty_one(self):
        order = front_order([S("A", "2026-08-26T00:00:00Z", 9, True), S("B", "2026-09-05T00:00:00Z", 5, True),
                             S("C", "2026-09-11T00:00:00Z", 6, False)])
        self.assertEqual(ids(order), ["B", "C", "A"])

    def test_importance_decides_inside_one_window(self):
        order = front_order([S("D", "2026-09-11T00:00:00Z", 4, True), S("E", "2026-09-10T12:00:00Z", 8, True)])
        self.assertEqual(ids(order), ["E", "D"])

    def test_future_scheduled_event_counts_from_its_publication(self):
        future = {"id": "F", "kind": "event", "status": "live", "event_at": "2026-10-30T00:00:00Z",
                  "first_published_at": "2026-09-10T00:00:00Z", "importance": 5, "front_page_eligible": True}
        current = {"id": "G", "status": "live", "event_at": "2026-09-11T00:00:00Z",
                   "first_published_at": "2026-09-12T00:00:00Z", "importance": 5, "front_page_eligible": True}
        self.assertEqual(ids(front_order([future, current])), ["G", "F"])

    def test_eligible_stories_rank_before_weightier_ineligible_ones_in_one_window(self):
        stories = [S("X", "2026-09-11T00:00:00Z", 9, False), S("Y", "2026-09-10T00:00:00Z", 5, True),
                   S("Z", "2026-09-10T12:00:00Z", 3, True)]
        self.assertEqual(ids(front_order(stories)), ["Y", "Z", "X"])

    def test_without_eligible_stories_the_freshest_leads(self):
        order = front_order([S("I", "2026-09-01T00:00:00Z", 9, False), S("H", "2026-09-11T00:00:00Z", 3, False)])
        self.assertEqual(ids(order), ["H", "I"])

    def test_result_does_not_depend_on_input_order(self):
        stories = [S("A", "2026-08-26T00:00:00Z", 9, True), S("B", "2026-09-05T00:00:00Z", 5, True),
                   S("C", "2026-09-11T00:00:00Z", 6, False), S("D", "2026-09-11T00:00:00Z", 6, False)]
        for permutation in itertools.permutations(stories):
            with self.subTest(order=ids(list(permutation))):
                self.assertEqual(ids(front_order(list(permutation))), ["B", "C", "D", "A"])

    def test_full_ties_break_by_ascending_id(self):
        stories = [S(rid, "2026-09-11T00:00:00Z", 6, True) for rid in ("FCMO-Z", "FCMO-M", "FCMO-A")]
        self.assertEqual(ids(front_order(stories)), ["FCMO-A", "FCMO-M", "FCMO-Z"])
        self.assertEqual(ids(front_order(list(reversed(stories)))), ["FCMO-A", "FCMO-M", "FCMO-Z"])

    def test_exactly_48_hours_falls_in_the_next_window(self):
        anchor = S("N", "2026-09-11T00:00:00Z", 1, False)
        inside = S("Q", "2026-09-09T00:00:01Z", 1, False)      # 47:59:59 before the anchor: window 0
        edge = S("P", "2026-09-09T00:00:00Z", 9, False)        # exactly 48 h: window 1 despite importance 9
        edge2 = S("R", "2026-09-07T00:00:00Z", 9, False)       # exactly 96 h: window 2
        inside2 = S("U", "2026-09-07T00:00:01Z", 1, False)     # just under 96 h: window 1
        order = front_order([edge2, inside2, edge, inside, anchor])
        self.assertEqual(ids(order), ["N", "Q", "P", "U", "R"])

    def test_lead_is_first_eligible_and_the_rest_keep_base_order(self):
        stories = [S("N", "2026-09-11T00:00:00Z", 1, False), S("Q", "2026-09-09T00:00:01Z", 1, False),
                   S("P", "2026-09-09T00:00:00Z", 2, True), S("O", "2026-09-01T00:00:00Z", 9, True)]
        self.assertEqual(ids(front_order(stories)), ["P", "N", "Q", "O"])

    def test_undated_or_unparseable_stories_go_last(self):
        stories = [S("X", None, 9, False), S("Y", "not-a-date", 9, False), S("V", "2026-08-01T00:00:00Z", 1, False),
                   S("W", "2026-09-11T00:00:00Z", 1, True)]
        self.assertEqual(ids(front_order(stories)), ["W", "V", "X", "Y"])
        self.assertEqual(ids(front_order(list(reversed(stories)))), ["W", "V", "X", "Y"])

    def test_missing_or_bad_publication_time_falls_back_to_event_time(self):
        late = S("L", "2026-09-11T00:00:00Z", 1, True, published=None)
        bad = S("K", "2026-09-10T00:00:00Z", 1, True, published="garbage")
        early = S("J", "2026-09-01T00:00:00Z", 9, True, published=None)
        self.assertEqual(ids(front_order([early, bad, late])), ["L", "K", "J"])

    def test_z_suffix_and_offsets_are_the_same_instant(self):
        stories = [S("B", "2026-09-11T02:00:00+02:00", 5, True), S("A", "2026-09-11T00:00:00Z", 5, True)]
        self.assertEqual(ids(front_order(stories)), ["A", "B"])

    def test_returns_a_permutation_of_the_same_objects_without_mutating_input(self):
        stories = [S("A", "2026-08-26T00:00:00Z", 9, True), S("C", "2026-09-11T00:00:00Z", 6, False)]
        snapshot = json.dumps(stories, sort_keys=True)
        order = front_order(stories)
        self.assertEqual(sorted(map(id, order)), sorted(map(id, stories)))
        self.assertEqual(json.dumps(stories, sort_keys=True), snapshot)
        self.assertEqual(ids(stories), ["A", "C"])


class FrontFreshnessBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v4-freshness-")
        cls.out = Path(cls.temp.name) / "publish"
        build(cls.out)
        payload = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.live = [story for story in payload["stories"] if story.get("status") == "live"]
        cls.order = front_order(cls.live)
        cls.anchor = max(t(story) for story in cls.live)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, prefix: str, suffix: str = "diario/") -> str:
        return (self.out / prefix / suffix / "index.html").read_text(encoding="utf-8")

    def resolve(self, link: str) -> str:
        self.assertTrue(link.startswith(BASE), link)
        target = self.out / html.unescape(link)[len(BASE):] / "index.html"
        self.assertTrue(target.is_file(), link)
        return re.search(r'<main id="main" class="page-shell" data-story-id="([^"]+)"', target.read_text(encoding="utf-8")).group(1)

    def bucket(self, story: dict) -> int:
        return (self.anchor - t(story)) // datetime.timedelta(hours=48)

    def test_real_corpus_has_fresh_material_to_order(self):
        self.assertEqual(sorted(ids(self.order)), sorted(ids(self.live)))
        self.assertGreater(len(self.order), 5)

    def test_lead_link_resolves_to_the_same_fresh_eligible_story_in_every_locale(self):
        leads = {}
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                leads[locale] = self.resolve(LEAD.search(self.page(prefix)).group(1))
                self.assertEqual(leads[locale], self.order[0]["id"])
        self.assertEqual(len(set(leads.values())), 1)
        lead = self.order[0]
        eligible = [story for story in self.live if story.get("front_page_eligible")]
        self.assertTrue(lead.get("front_page_eligible"))
        self.assertGreaterEqual(t(lead), max(t(story) for story in eligible) - datetime.timedelta(hours=48))

    def test_landing_feature_inherits_the_same_lead(self):
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                landing = (self.out / prefix / "index.html").read_text(encoding="utf-8")
                technical = re.search(r'<section class="landing-technical".*?</section>', landing, re.S).group()
                self.assertEqual(self.resolve(LEAD.search(technical).group(1)), self.order[0]["id"])

    def test_top_stories_follow_the_order_with_non_decreasing_windows(self):
        expected = ids(self.order[1:5])
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(CARD_ID.findall(TOP.search(self.page(prefix)).group(1)), expected)
        buckets = [self.bucket(story) for story in self.order[1:5]]
        self.assertEqual(buckets, sorted(buckets))

    def test_essentials_and_beat_sections_use_the_same_order(self):
        # Pass 3: every block takes the next stories of the same order that no earlier block showed.
        used = set(ids(self.order[:5]))
        used.update([s["id"] for s in self.order[5:]
                     if s.get("confidence") not in {"confirmed", "strongly_supported"}][:2])
        essentials = [s["id"] for s in self.order if s["id"] not in used][:5]
        used.update(essentials)
        by_beat = {}
        for beat in BEATS:
            values = [s["id"] for s in self.order if s.get("beat") == beat and s["id"] not in used][:3]
            used.update(values)
            if values:
                by_beat[beat] = values
        self.assertEqual(len(essentials), 5)
        self.assertTrue(by_beat)
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                page = self.page(prefix)
                links = re.findall(r'<a href="([^"]+)"', ESSENTIALS.search(page).group(1))
                self.assertEqual([self.resolve(link) for link in links], essentials)
                seen = []
                for section in BEAT_SECTION.findall(page):
                    beat = re.search(r'beat/([a-z]+)/"', section)
                    if not beat:
                        continue
                    seen.append(beat.group(1))
                    self.assertEqual(CARD_ID.findall(section), by_beat.get(beat.group(1)), beat.group(1))
                self.assertEqual(seen, list(by_beat))

    def test_developing_well_skips_lead_and_top_stories(self):
        shown = set(ids(self.order[:5]))
        expected = [s["id"] for s in self.order
                    if s["id"] not in shown and s.get("confidence") not in {"confirmed", "strongly_supported"}][:2]
        self.assertTrue(expected)
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                cards = CARD_ID.findall(DEVELOPING.search(self.page(prefix)).group(1))
                self.assertEqual(cards, expected)
                self.assertFalse(shown & set(cards))

    def test_publication_gates_pass_on_the_fresh_build(self):
        results = run_all.run(self.out)
        codes = [result.code for result in results]
        self.assertEqual(len(codes), 14)
        self.assertEqual(codes, [gate.__module__.rsplit(".", 1)[-1].upper() for gate in run_all.GATES])
        self.assertIn("NO_FCMO_GROUP", codes)


class DeploymentIdentityLeadTests(unittest.TestCase):
    def test_identity_names_the_fresh_lead_not_the_first_eligible_in_document_order(self):
        old = {"id": "FCMO-000000000001", "status": "live", "front_page_eligible": True, "importance": 9,
               "event_at": "2026-08-26T00:00:00Z", "first_published_at": "2026-08-27T00:00:00Z",
               "url_date": "2026-08-26", "slug": "old-weighty-story"}
        fresh = {"id": "FCMO-000000000002", "status": "live", "front_page_eligible": True, "importance": 5,
                 "event_at": "2026-09-11T00:00:00Z", "first_published_at": "2026-09-12T00:00:00Z",
                 "url_date": "2026-09-11", "slug": "fresh-story"}
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "publish"
            (site / "data").mkdir(parents=True)
            stories = {"schema": "fcmo-stories-v2", "release_id": "newswire-test", "stories": [old, fresh]}
            (site / "data/stories.v2.json").write_text(json.dumps(stories), encoding="utf-8")
            (site / "data/newsroom-status.json").write_text(
                json.dumps({"release_id": "newswire-test", "corpus_digest": "abc123"}), encoding="utf-8")
            for route in ("index.html", "es/index.html", "zh/index.html"):
                path = site / route
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"<html>{route}</html>", encoding="utf-8")
            for story in (old, fresh):
                for locale in ("en", "es-419", "zh-Hans"):
                    path = site / canonical_story_path(story, locale)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(f"<html>{story['id']} {locale}</html>", encoding="utf-8")
            receipt = build_deployment_identity.build(site, "deadbeef")
        self.assertEqual(receipt["lead_id"], fresh["id"])
        self.assertEqual(receipt["lead_id"], front_order([old, fresh])[0]["id"])
        self.assertIn(canonical_story_path(fresh, "zh-Hans"), receipt["critical_files"])
        self.assertNotIn(canonical_story_path(old, "en"), receipt["critical_files"])


class CompileTests(unittest.TestCase):
    def test_compileall_is_silent(self):
        result = subprocess.run([sys.executable, "-m", "compileall", "-q", "tools", "tests"],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout + result.stderr, "")


if __name__ == "__main__":
    unittest.main()
