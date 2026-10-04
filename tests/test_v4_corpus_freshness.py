"""Corpus freshness: every FCMO AI page says how fresh the corpus is, never the wall clock."""

from __future__ import annotations

import copy
import datetime
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.gates import run_all  # noqa: E402
from tools.paper.freshness import STALE_AFTER, corpus_freshness  # noqa: E402
from tools.paper.front_order import FRESH_WINDOW, front_order  # noqa: E402
from tools.paper.i18n import format_date, headline, label, load_catalogs, plural  # noqa: E402
from tools.paper.routes import output_path, story_path  # noqa: E402
from tools.paper.status_banner import render  # noqa: E402

STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))
KEYS = {"state", "checked_at", "newest_at", "lag_hours", "lag_days", "lead_id", "lead_at", "lead_gap_days"}
EDITION_STATES = ("FRESH", "QUIET", "DELAYED", "TRANSPORT_DOWN")
FRESHNESS_STATES = ("current", "lagging", "stale", "unknown")
LINE = re.compile(r'<p class="corpus-freshness"([^>]*)><strong>([^<]*)</strong> ([^<]*)</p>')
CARD = re.compile(r'<article class="status-card status-freshness"([^>]*)><span class="eyebrow">([^<]*)</span>'
                  r'<strong>([^<]*)</strong><p>([^<]*)</p>(<p class="freshness-lead">.*?</p>)?</article>', re.S)
ENGLISH_WORDS = re.compile(r"\b(?:Newest|story|before|our|last|check|days?|Front-page|lead|older|within|newest|"
                           r"cannot|date|right|now|Current|Lagging|Stale|Unknown)\b")


def S(rid: str, event_at: str | None = None, **extra) -> dict:
    story = {"id": rid, **extra}
    if event_at is not None:
        story["event_at"] = event_at
    return story


def attributes(tag: str) -> dict:
    return dict(re.findall(r' ([a-z-]+)="([^"]*)"', tag))


class CorpusFreshnessUnitTests(unittest.TestCase):
    ONE = [S("A", "2026-09-01T00:00:00Z")]

    def at(self, checked: object, stories: list[dict] | None = None) -> dict:
        return corpus_freshness(self.ONE if stories is None else stories, checked)

    def test_the_fresh_window_boundary_is_inclusive_to_the_second(self):
        self.assertEqual(FRESH_WINDOW, datetime.timedelta(hours=48))
        edge, past = self.at("2026-09-03T00:00:00Z"), self.at("2026-09-03T00:00:01Z")
        self.assertEqual((edge["state"], edge["lag_hours"], edge["lag_days"]), ("current", 48, 2))
        self.assertEqual((past["state"], past["lag_hours"], past["lag_days"]), ("lagging", 48, 2))

    def test_the_stale_boundary_is_inclusive_to_the_second(self):
        self.assertEqual(STALE_AFTER, datetime.timedelta(days=7))
        edge, past = self.at("2026-09-08T00:00:00Z"), self.at("2026-09-08T00:00:01Z")
        self.assertEqual((edge["state"], edge["lag_hours"], edge["lag_days"]), ("lagging", 168, 7))
        self.assertEqual((past["state"], past["lag_hours"], past["lag_days"]), ("stale", 168, 7))

    def test_unknown_when_the_check_time_is_missing_invalid_or_not_a_string(self):
        for checked in (None, "", "   ", "not-a-date", "2026-13-40T00:00:00Z", 20260902, 1.5, True,
                        datetime.datetime(2026, 9, 2, tzinfo=datetime.timezone.utc), ["2026-09-02T00:00:00Z"]):
            with self.subTest(checked=checked):
                result = self.at(checked)
                self.assertEqual(result["state"], "unknown")
                self.assertIsNone(result["checked_at"])
                self.assertIsNone(result["lag_hours"])
                self.assertIsNone(result["lag_days"])
                self.assertEqual(result["newest_at"], "2026-09-01T00:00:00Z")
                self.assertEqual(result["lead_id"], "A")

    def test_unknown_when_no_story_can_be_dated(self):
        for stories in ([S("B")], [S("B", ""), S("C", "garbage")], [S("D", None, first_published_at="2026-09-01T00:00:00Z")]):
            with self.subTest(stories=stories):
                result = self.at("2026-09-02T00:00:00Z", stories)
                self.assertEqual(result["state"], "unknown")
                self.assertEqual(result["checked_at"], "2026-09-02T00:00:00Z")
                self.assertIsNone(result["newest_at"])
                self.assertIsNone(result["lag_hours"])
                self.assertIsNone(result["lag_days"])
                self.assertEqual(result["lead_id"], stories[0]["id"])
                self.assertIsNone(result["lead_at"])
                self.assertIsNone(result["lead_gap_days"])

    def test_unknown_for_an_empty_corpus(self):
        self.assertEqual(self.at("2026-09-02T00:00:00Z", []), {
            "state": "unknown", "checked_at": "2026-09-02T00:00:00Z", "newest_at": None, "lag_hours": None,
            "lag_days": None, "lead_id": None, "lead_at": None, "lead_gap_days": None})
        self.assertEqual(self.at(None, [])["state"], "unknown")

    def test_an_earlier_first_publication_dates_a_future_event(self):
        story = S("A", "2026-10-10T00:00:00Z", first_published_at="2026-09-20T06:00:00Z")
        result = self.at("2026-09-21T06:00:00Z", [story])
        self.assertEqual((result["newest_at"], result["lead_at"], result["lag_hours"], result["state"]),
                         ("2026-09-20T06:00:00Z", "2026-09-20T06:00:00Z", 24, "current"))
        later = self.at("2026-09-21T06:00:00Z", [S("A", "2026-09-19T00:00:00Z", first_published_at="2026-09-20T06:00:00Z")])
        self.assertEqual(later["newest_at"], "2026-09-19T00:00:00Z")

    def test_offsets_and_naive_times_normalise_to_utc(self):
        result = self.at("2026-09-26T14:00:00+02:00", [S("A", "2026-09-25T14:00:00+02:00")])
        self.assertEqual((result["checked_at"], result["newest_at"], result["lag_hours"]),
                         ("2026-09-26T12:00:00Z", "2026-09-25T12:00:00Z", 24))
        naive = self.at("2026-09-03T00:00:00", [S("A", "2026-09-01T00:00:00")])
        self.assertEqual((naive["checked_at"], naive["newest_at"], naive["state"], naive["lag_hours"]),
                         ("2026-09-03T00:00:00Z", "2026-09-01T00:00:00Z", "current", 48))
        west = self.at("2026-09-02T18:30:00-05:30", [S("A", "2026-09-01T00:00:00Z")])
        self.assertEqual((west["checked_at"], west["lag_hours"], west["lag_days"]), ("2026-09-03T00:00:00Z", 48, 2))

    def test_a_story_newer_than_the_check_clamps_the_lag_to_zero(self):
        result = self.at("2026-09-21T00:00:00Z", [S("A", "2026-09-22T00:00:00Z")])
        self.assertEqual((result["lag_hours"], result["lag_days"], result["state"]), (0, 0, "current"))

    def test_hours_days_and_lead_gap_are_floored(self):
        stories = [S("L", "2026-09-05T13:13:07Z", front_page_eligible=True), S("N", "2026-09-11T17:55:45Z")]
        result = self.at("2026-09-27T00:54:13Z", stories)
        self.assertEqual((result["lag_hours"], result["lag_days"], result["state"]), (366, 15, "stale"))
        self.assertEqual((result["lead_id"], result["lead_at"], result["lead_gap_days"]),
                         ("L", "2026-09-05T13:13:07Z", 6))
        almost = self.at("2026-09-02T23:59:59Z", [S("L", "2026-09-01T00:00:01Z", front_page_eligible=True),
                                                  S("N", "2026-09-02T00:00:00Z")])
        self.assertEqual((almost["lead_gap_days"], almost["lag_hours"], almost["lag_days"]), (0, 23, 0))

    def test_a_lead_newer_than_the_newest_is_impossible_and_a_same_day_lead_gaps_zero(self):
        result = self.at("2026-09-03T00:00:00Z", [S("A", "2026-09-02T00:00:00Z", front_page_eligible=True)])
        self.assertEqual((result["lead_id"], result["lead_gap_days"]), ("A", 0))

    def test_an_undated_lead_keeps_its_id_without_a_date_or_gap(self):
        stories = [S("U", None, front_page_eligible=True), S("D", "2026-09-01T00:00:00Z")]
        self.assertEqual(front_order(stories)[0]["id"], "U")
        result = self.at("2026-09-02T00:00:00Z", stories)
        self.assertEqual((result["lead_id"], result["lead_at"], result["lead_gap_days"]), ("U", None, None))
        self.assertEqual((result["newest_at"], result["state"]), ("2026-09-01T00:00:00Z", "current"))

    def test_the_lead_id_is_stringified(self):
        self.assertEqual(self.at("2026-09-02T00:00:00Z", [S(1234, "2026-09-01T00:00:00Z")])["lead_id"], "1234")

    def test_pure_deterministic_and_input_untouched(self):
        stories = [S("A", "2026-09-20T00:00:00Z", front_page_eligible=True, first_published_at="2026-09-21T00:00:00Z"),
                   S("B", "2026-09-25T14:00:00+02:00", topics=["x"]), S("C")]
        snapshot = copy.deepcopy(stories)
        first = corpus_freshness(stories, "2026-09-26T12:00:00Z")
        self.assertEqual(stories, snapshot)
        self.assertEqual(first, corpus_freshness(stories, "2026-09-26T12:00:00Z"))
        self.assertEqual(first, corpus_freshness(copy.deepcopy(list(reversed(stories))), "2026-09-26T12:00:00Z"))
        self.assertEqual(first, {"state": "current", "checked_at": "2026-09-26T12:00:00Z", "newest_at": "2026-09-25T12:00:00Z",
                                 "lag_hours": 24, "lag_days": 1, "lead_id": "A", "lead_at": "2026-09-20T00:00:00Z",
                                 "lead_gap_days": 5})

    def test_exact_key_set_in_every_state(self):
        for checked, stories in (("2026-09-02T00:00:00Z", self.ONE), ("2026-09-04T00:00:00Z", self.ONE),
                                 ("2026-09-30T00:00:00Z", self.ONE), (None, self.ONE), ("2026-09-02T00:00:00Z", [])):
            with self.subTest(checked=checked):
                self.assertEqual(set(corpus_freshness(stories, checked)), KEYS)


def freshness(state: str) -> dict:
    base = {"state": state, "checked_at": "2026-09-27T00:54:13Z", "newest_at": "2026-09-11T17:55:45Z", "lag_hours": 366,
            "lag_days": 15, "lead_id": "FCMO-F63D7F3A70B9", "lead_at": "2026-09-05T13:13:07Z", "lead_gap_days": 6}
    if state == "unknown":
        base.update(checked_at=None, lag_hours=None, lag_days=None)
    elif state == "current":
        base.update(lag_hours=30, lag_days=1)
    elif state == "lagging":
        base.update(lag_hours=100, lag_days=4)
    return base


class FreshnessBannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT)
        cls.locales = {code: {"code": code, "path_prefix": prefix} for code, prefix in LOCALES}

    def status(self, state: str) -> dict:
        return {"edition_state": state, "last_edition_at": "2026-09-23T11:32:15Z",
                "status_updated_at": "2026-09-27T00:54:13Z", "quiet_since": "2026-09-22T08:00:00Z"}

    def banner(self, state: str, fresh: dict | None, code: str = "en") -> str:
        return render(self.status(state), self.catalogs[code], base=BASE, locale=self.locales[code], freshness=fresh)

    def test_every_edition_state_carries_exactly_one_line_in_its_place(self):
        for edition in EDITION_STATES:
            for state in FRESHNESS_STATES:
                with self.subTest(edition=edition, freshness=state):
                    fresh = freshness(state)
                    out = self.banner(edition, fresh)
                    plain = self.banner(edition, None)
                    self.assertEqual(out.count('class="corpus-freshness"'), 1)
                    self.assertEqual(out.count("<p class=\"corpus-freshness\""), 1)
                    line = LINE.search(out)
                    self.assertIsNotNone(line, out)
                    if edition == "FRESH":
                        update_end = out.index("</p>") + len("</p>")
                        self.assertTrue(out.startswith('<p class="edition-update">'))
                        self.assertEqual(line.start(), update_end)
                        self.assertEqual(out[line.end():], plain[update_end:])
                        self.assertTrue(out[line.end():].startswith('<div class="status-banner" hidden'))
                    else:
                        self.assertTrue(out.startswith('<div class="status-banner"'))
                        self.assertEqual(line.start(), len(plain))
                        self.assertEqual(out[:line.start()], plain)
                        self.assertEqual(line.end(), len(out))
                    tag = attributes(line.group(1))
                    for forbidden in ("data-edition-at", "data-edition-state", "hidden"):
                        self.assertNotIn(forbidden, line.group(1))
                    self.assertEqual(tag["data-freshness"], state)
                    if fresh["newest_at"] is None:
                        self.assertNotIn("data-newest-at", tag)
                    else:
                        self.assertEqual(tag["data-newest-at"], fresh["newest_at"])
                    if fresh["lag_hours"] is None:
                        self.assertNotIn("data-lag-hours", tag)
                    else:
                        self.assertEqual(tag["data-lag-hours"], str(fresh["lag_hours"]))
                    self.assertEqual(set(tag) - {"data-freshness", "data-newest-at", "data-lag-hours"}, set())
                    self.assertEqual(html.unescape(line.group(2)), label(self.catalogs["en"], "freshness_state", state))
                    self.assertEqual(out.count('data-edition-at="'), 1)

    def test_sentence_follows_what_is_known(self):
        catalog = self.catalogs["en"]
        strings = catalog["strings"]["freshness"]
        full = LINE.search(self.banner("DELAYED", freshness("stale"))).group(3)
        self.assertEqual(html.unescape(full), strings["line"].format(
            newest=format_date("2026-09-11T17:55:45Z", catalog, precision="day"), lag=plural(catalog, "freshness_day", 15),
            checked=format_date("2026-09-27T00:54:13Z", catalog, precision="day")))
        self.assertIn("(September 27, 2026)", html.unescape(full))
        self.assertIn("15 days", html.unescape(full))
        one = LINE.search(self.banner("DELAYED", dict(freshness("current"), lag_days=1))).group(3)
        self.assertIn(" 1 day before", html.unescape(one))
        unknown = LINE.search(self.banner("QUIET", freshness("unknown"))).group(3)
        self.assertEqual(html.unescape(unknown), strings["newest"].format(newest=format_date("2026-09-11T17:55:45Z", catalog, precision="day")))
        undated = LINE.search(self.banner("QUIET", dict(freshness("unknown"), newest_at=None))).group(3)
        self.assertEqual(html.unescape(undated), strings["undated"])

    def test_both_dates_are_utc_days_so_the_newest_never_follows_the_check(self):
        # 00:54 UTC is the previous evening in the newsroom zone; a same-day story must not read as after the check.
        fresh = corpus_freshness([S("A", "2026-09-27T00:00:00Z", front_page_eligible=True)], "2026-09-27T00:54:13Z")
        for code in ("en", "es-419", "zh-Hans"):
            with self.subTest(locale=code):
                catalog = self.catalogs[code]
                day = format_date("2026-09-27T00:00:00Z", catalog, precision="day")
                sentence = html.unescape(LINE.search(self.banner("DELAYED", fresh, code)).group(3))
                self.assertEqual(sentence, catalog["strings"]["freshness"]["line"].format(
                    newest=day, lag=plural(catalog, "freshness_day", 0), checked=day))

    def test_line_text_is_escaped(self):
        catalog = copy.deepcopy(self.catalogs["en"])
        catalog["labels"]["freshness_state"]["stale"] = "<b>Stale</b>"
        catalog["strings"]["freshness"]["undated"] = 'Cannot date "it" <now> & later'
        out = render(self.status("DELAYED"), catalog, base=BASE, locale=self.locales["en"],
                     freshness=dict(freshness("stale"), newest_at=None))
        self.assertIn("<strong>&lt;b&gt;Stale&lt;/b&gt;</strong>", out)
        self.assertIn("Cannot date &quot;it&quot; &lt;now&gt; &amp; later", out)

    def test_without_freshness_the_banner_is_byte_identical_to_before(self):
        expected = {
            "FRESH": '<p class="edition-update">Updated September 23, 2026</p><div class="status-banner" hidden data-edition-state="FRESH" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->This page may be out of date: its last update was September 23, 2026. <a href="/FCMO-AI-Newsletter/status/">See the system status</a></div>',
            "QUIET": '<div class="status-banner" data-edition-state="QUIET" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->No material changes since September 22, 2026; the system keeps checking sources.</div>',
            "DELAYED": '<div class="status-banner" data-edition-state="DELAYED" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->Today\'s edition is delayed. Last edition: September 23, 2026. <a href="/FCMO-AI-Newsletter/status/">See the system status</a></div>',
            "TRANSPORT_DOWN": '<div class="status-banner" data-edition-state="TRANSPORT_DOWN" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->Today\'s edition is delayed. Last edition: September 23, 2026. Our news feed is not reaching us. <a href="/FCMO-AI-Newsletter/status/">See the system status</a></div>',
        }
        for state, literal in expected.items():
            with self.subTest(state=state):
                self.assertEqual(self.banner(state, None), literal)
                self.assertEqual(render(self.status(state), self.catalogs["en"], base=BASE, locale=self.locales["en"]), literal)

    def test_spanish_and_chinese_lines_carry_no_english(self):
        for code in ("es-419", "zh-Hans"):
            for state in FRESHNESS_STATES:
                for newest in ("2026-09-11T17:55:45Z", None):
                    with self.subTest(locale=code, state=state, newest=newest):
                        line = LINE.search(self.banner("TRANSPORT_DOWN", dict(freshness(state), newest_at=newest), code))
                        text = html.unescape(line.group(2) + " " + line.group(3))
                        self.assertIsNone(ENGLISH_WORDS.search(text), text)
                        self.assertNotIn(label(self.catalogs["en"], "freshness_state", state), text)
                        if code == "zh-Hans":
                            self.assertEqual(re.findall(r"[A-Za-z]+", text.replace("FCMO AI", "")), [], text)


class CorpusFreshnessBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v4-corpus-freshness-")
        cls.out = cls.build(STATUS, "publish")
        fresh_status = dict(json.loads(STATUS.read_text(encoding="utf-8")), edition_state="FRESH", alerts=[])
        fresh_path = Path(cls.temp.name) / "fresh-status.json"
        fresh_path.write_text(json.dumps(fresh_status), encoding="utf-8")
        cls.fresh_out = cls.build(fresh_path, "fresh")
        payload = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.live = [story for story in payload["stories"] if story.get("status") == "live"]
        cls.by_id = {story["id"]: story for story in cls.live}
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))
        cls.catalogs = load_catalogs(ROOT)
        cls.oracle = cls.expected(cls.live, cls.status["status_updated_at"])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @classmethod
    def build(cls, status: Path, name: str) -> Path:
        out = Path(cls.temp.name) / name
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(status),
             "--out", str(out), "--base", BASE], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return out

    @staticmethod
    def expected(live: list[dict], checked_at: str) -> dict:
        """Independent oracle: parse the corpus by hand; only the lead comes from ``front_order``."""
        def parse(value):
            if not isinstance(value, str) or not value.strip():
                return None
            try:
                moment = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            except ValueError:
                return None
            return moment if moment.tzinfo else moment.replace(tzinfo=datetime.timezone.utc)

        def when(story):
            event, published = parse(story.get("event_at")), parse(story.get("first_published_at"))
            return None if event is None else (min(event, published) if published else event)

        stamp = lambda moment: moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        newest = max(moment for moment in map(when, live) if moment)
        checked = parse(checked_at)
        seconds = max(int((checked - newest).total_seconds()), 0)
        lead = front_order(live)[0]
        lead_at = when(lead)
        return {"newest_at": stamp(newest), "lag_hours": seconds // 3600, "lag_days": seconds // 86400,
                "lead": lead, "lead_at": stamp(lead_at),
                "lead_gap_days": max(int((newest - lead_at).total_seconds()), 0) // 86400,
                "state": "current" if seconds <= 48 * 3600 else "lagging" if seconds <= 7 * 86400 else "stale"}

    def read(self, out: Path, route: str) -> str:
        return output_path(out, route).read_text(encoding="utf-8")

    def pages(self, prefix: str) -> dict:
        locale = {"path_prefix": prefix}
        story = self.oracle["lead"] if self.oracle["lead"].get("url_date") else self.live[0]
        return {name: self.read(self.out, route) for name, route in (
            ("root", prefix), ("diario", prefix + "diario/"), ("story", story_path(locale, story)), ("status", prefix + "status/"))}

    def test_the_real_corpus_is_stale(self):
        self.assertEqual(self.oracle["state"], "stale")
        self.assertGreater(self.oracle["lag_days"], 7)
        self.assertEqual(corpus_freshness(self.live, self.status["status_updated_at"])["state"], "stale")

    def test_every_page_carries_one_line_matching_the_oracle(self):
        for code, prefix in LOCALES:
            catalog = self.catalogs[code]
            for name, page in self.pages(prefix).items():
                with self.subTest(locale=code, page=name):
                    self.assertEqual(page.count('class="corpus-freshness"'), 1)
                    line = LINE.search(page)
                    self.assertIsNotNone(line)
                    self.assertEqual(attributes(line.group(1)), {
                        "data-freshness": self.oracle["state"], "data-newest-at": self.oracle["newest_at"],
                        "data-lag-hours": str(self.oracle["lag_hours"])})
                    self.assertEqual(html.unescape(line.group(2)), label(catalog, "freshness_state", "stale"))
                    sentence = html.unescape(line.group(3))
                    self.assertIn(plural(catalog, "freshness_day", self.oracle["lag_days"]), sentence)
                    self.assertIn(format_date(self.oracle["newest_at"], catalog, precision="day"), sentence)
                    self.assertIn(format_date(self.status["status_updated_at"], catalog, precision="day"), sentence)
                    self.assertIn("FCMO AI", sentence)
                    banner = page.index('<div class="status-banner"')
                    self.assertEqual(line.start(), page.index("</div>", banner) + len("</div>"))

    def test_status_card_reports_freshness_and_links_the_lead(self):
        lead = self.oracle["lead"]
        for code, prefix in LOCALES:
            with self.subTest(locale=code):
                catalog = self.catalogs[code]
                page = self.read(self.out, prefix + "status/")
                self.assertEqual(page.count('class="status-card status-freshness"'), 1)
                card = CARD.search(page)
                self.assertIsNotNone(card)
                self.assertEqual(attributes(card.group(1)), {
                    "data-freshness": "stale", "data-newest-at": self.oracle["newest_at"],
                    "data-lag-hours": str(self.oracle["lag_hours"]), "data-lead-id": lead["id"],
                    "data-lead-at": self.oracle["lead_at"]})
                self.assertEqual(html.unescape(card.group(2)), catalog["strings"]["status_page"]["freshness"])
                self.assertEqual(html.unescape(card.group(3)), label(catalog, "freshness_state", "stale"))
                self.assertEqual(card.group(4), LINE.search(page).group(3))
                edition_card = page.index(f'<span class="eyebrow">{html.escape(catalog["strings"]["status_page"]["edition"])}</span>')
                self.assertLess(edition_card, card.start())
                self.assertEqual(page.rfind("<article", 0, card.start()), page.rfind("<article", 0, edition_card))
                paragraph = re.fullmatch(r'<p class="freshness-lead">(.*)<a href="([^"]+)">([^<]+)</a>(.*)</p>', card.group(5))
                self.assertIsNotNone(paragraph, card.group(5))
                link = html.unescape(paragraph.group(2))
                self.assertEqual(link, BASE + story_path({"path_prefix": prefix}, lead))
                self.assertIn(f'data-story-id="{lead["id"]}"', self.read(self.out, link[len(BASE):]))
                self.assertEqual(html.unescape(paragraph.group(3)), headline(lead, code, catalog))
                template = catalog["strings"]["freshness"]["lead" if self.oracle["lead_gap_days"] >= 1 else "lead_same_day"]
                before, after = template.split("{headline}")
                values = {"date": format_date(self.oracle["lead_at"], catalog, precision="day"),
                          "gap": plural(catalog, "freshness_day", self.oracle["lead_gap_days"])}
                self.assertEqual(html.unescape(paragraph.group(1)), before.format(**values))
                self.assertEqual(html.unescape(paragraph.group(4)), after.format(**values))

    def test_status_description_follows_the_edition_state(self):
        for out, state in ((self.fresh_out, "FRESH"), (self.out, self.status["edition_state"])):
            for code, prefix in LOCALES:
                with self.subTest(edition=state, locale=code):
                    catalog = self.catalogs[code]
                    page = self.read(out, prefix + "status/")
                    description = html.unescape(re.search(r'<meta name="description" content="([^"]*)">', page).group(1))
                    stale = label(catalog, "freshness_state", "stale")
                    self.assertTrue(description.startswith(stale + " · "), description)
                    self.assertEqual(description, stale + " · " + html.unescape(LINE.search(page).group(3)))
                    if state == "FRESH":
                        delayed = catalog["strings"]["edition"]["delayed"].split("{date}")[0].strip()
                        self.assertNotIn(delayed, description)
                        self.assertIn('<div class="status-banner" hidden data-edition-state="FRESH"', page)
                        line = LINE.search(page)
                        self.assertEqual(page.index('</p>', page.index('<p class="edition-update">')) + len('</p>'), line.start())
                        self.assertEqual(line.end(), page.index('<div class="status-banner" hidden'))

    def test_publication_gates_pass_on_the_fresh_build(self):
        for out in (self.out, self.fresh_out):  # the real status and a FRESH one: both placements of the line
            with self.subTest(build=out.name):
                results = run_all.run(out)
                codes = [result.code for result in results]
                self.assertEqual(len(results), 14)
                self.assertEqual(codes, [gate.__module__.rsplit(".", 1)[-1].upper() for gate in run_all.GATES])
                for code in ("NO_FCMO_GROUP", "ENGLISH_LEAK", "LOCALE_COMPLETE", "SIZE_BUDGET", "NO_MACHINE_PATHS"):
                    self.assertIn(code, codes)


if __name__ == "__main__":
    unittest.main()
