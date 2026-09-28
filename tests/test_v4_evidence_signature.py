"""The FCMO AI evidence signature: per-card evidence strips and the front-page evidence board."""

from __future__ import annotations

from collections import Counter
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

from tools.paper.i18n import load_catalogs, plural  # noqa: E402
from tools.paper.templates.pages import evidence_board, evidence_strip  # noqa: E402

LOCALES = ("en", "es-419", "zh-Hans")
STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
CARD = re.compile(r'<article class="(?:story-card|archive-item)[^"]*"[^>]*data-story-id="([^"]+)"(.*?)</article>', re.S)
STRIP = re.compile(r'<p class="evidence-strip"([^>]*)>(.*?)</p>', re.S)
BOARD = re.compile(r'<section[^>]*id="evidence-board".*?</section>', re.S)


def build(stories: Path, out: Path) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(stories), "--status", str(STATUS),
         "--out", str(out), "--base", "/FCMO-AI-Newsletter/"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads((out / "data/routes.json").read_text(encoding="utf-8"))


def attrs(fragment: str) -> dict[str, str]:
    return {key: html.unescape(value) for key, value in re.findall(r'data-([a-z-]+)="([^"]*)"', fragment)}


def text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def primary(story: dict) -> int:
    return sum(1 for source in story.get("sources") or [] if source.get("primary"))


def gaps(story: dict) -> int:
    return len((story.get("evidence") or {}).get("gaps") or [])


class EvidenceSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v4-evidence-")
        temp = Path(cls.temp.name)
        cls.catalogs = load_catalogs(ROOT)
        payload = json.loads(STORIES.read_text(encoding="utf-8"))
        cls.stories = {story["id"]: story for story in payload["stories"]}
        cls.live = [story for story in payload["stories"] if story.get("status") == "live"]
        cls.out = temp / "real" / "FCMO-AI-Newsletter"
        cls.routes = build(STORIES, cls.out)

        fixture = json.loads(STORIES.read_text(encoding="utf-8"))
        live = [story for story in fixture["stories"] if story.get("status") == "live"]
        live[0]["confidence"] = "not_a_real_level"
        live[1].pop("confidence", None)
        live[2].pop("evidence", None)
        live[2].pop("sources", None)
        for story in live:
            story["evidence_class"] = "<x>"
        cls.fixture_ids = [story["id"] for story in live[:3]]
        (temp / "fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
        cls.fixture_out = temp / "fixture" / "FCMO-AI-Newsletter"
        cls.fixture_routes = build(temp / "fixture.json", cls.fixture_out)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def pages(out: Path, routes: list[dict], kind: str) -> dict[str, str]:
        found = {}
        for route in routes:
            if route["kind"] == kind and route["locale"] not in found:
                found[route["locale"]] = (out / route["path"].strip("/") / "index.html").read_text(encoding="utf-8")
        return found

    def fronts(self) -> dict[str, str]:
        return self.pages(self.out, self.routes, "front")

    def boards(self) -> dict[str, str]:
        return {code: BOARD.search(page).group(0) for code, page in self.fronts().items()}

    def assert_strips_match_corpus(self, page: str, *, minimum: int) -> None:
        cards = CARD.findall(page)
        self.assertGreaterEqual(len(cards), minimum)
        for story_id, body in cards:
            with self.subTest(story=story_id):
                strips = STRIP.findall(body)
                self.assertEqual(len(strips), 1)
                values = attrs(strips[0][0])
                story = self.stories[story_id]
                self.assertEqual(values["evidence-class"], story.get("evidence_class", ""))
                self.assertEqual(values["confidence"], story.get("confidence", ""))
                self.assertEqual(int(values["primary-sources"]), primary(story))
                self.assertEqual(int(values["open-gaps"]), gaps(story))
                self.assertEqual(int(values["claims"]), len((story.get("evidence") or {}).get("claims") or []))

    def test_strips_on_front_and_listings_match_the_corpus_in_every_locale(self):
        fronts = self.fronts()
        self.assertEqual(sorted(fronts), sorted(LOCALES))
        for code in LOCALES:
            with self.subTest(locale=code, page="front"):
                self.assert_strips_match_corpus(fronts[code], minimum=5)
            for kind in ("topic", "org", "beat"):
                with self.subTest(locale=code, page=kind):
                    listing = self.pages(self.out, self.routes, kind)[code]
                    self.assert_strips_match_corpus(listing, minimum=1)

    def test_board_aggregates_every_live_story_in_every_locale(self):
        known = self.catalogs["en"]["labels"]["confidence"]
        levels = Counter(s.get("confidence") if s.get("confidence") in known else "unrated" for s in self.live)
        claims = Counter((c.get("label") or "UNLABELED") for s in self.live for c in (s.get("evidence") or {}).get("claims", []))
        order = [*known, "unrated"]
        for code, board in self.boards().items():
            with self.subTest(locale=code):
                self.assertNotRegex(board[1:], r"<section\b")
                head = attrs(board[:board.index(">")])
                self.assertEqual(int(head["stories"]), len(self.live))
                self.assertEqual(int(head["primary-sources"]), sum(primary(s) for s in self.live))
                self.assertEqual(int(head["open-gaps"]), sum(gaps(s) for s in self.live))
                segments = [(key, int(count)) for key, count in re.findall(r'data-segment="([^"]+)" data-count="([0-9]+)"', board)]
                self.assertEqual(dict(segments), dict(levels))
                self.assertEqual([key for key, _ in segments], [key for key in order if levels[key]])
                self.assertTrue(all(count >= 1 for _, count in segments))
                for key, count in segments:
                    self.assertIn(f'data-count="{count}" style="flex-grow:{count}"', board)
                labels = {key: int(count) for key, count in re.findall(r'data-claim-label="([^"]+)" data-count="([0-9]+)"', board)}
                self.assertEqual(labels, dict(claims))
                figures = re.findall(r"<strong>([0-9]+)</strong>", board.split('class="evidence-figures"', 1)[1].split("</ul>", 1)[0])
                self.assertEqual(figures, [str(len(self.live)), head["primary-sources"], head["open-gaps"]])
                self.assertIn('/method/"', board)

    def test_visible_labels_are_localized_and_the_catalog_covers_the_live_corpus(self):
        english = {value for group in ("confidence", "claim_label", "evidence_class")
                   for value in self.catalogs["en"]["labels"][group].values()}
        for code in LOCALES:
            labels = self.catalogs[code]["labels"]
            for story in self.live:
                for group, key in (("confidence", "confidence"), ("evidence_class", "evidence_class")):
                    if story.get(key) is not None:
                        self.assertIn(story[key], labels[group], (code, story["id"]))
                for claim in (story.get("evidence") or {}).get("claims") or []:
                    self.assertIn(claim.get("label"), labels["claim_label"], (code, story["id"]))
        boards = self.boards()
        fronts = self.fronts()
        for code in LOCALES:
            labels = self.catalogs[code]["labels"]
            board = text(boards[code])
            for key in re.findall(r'data-segment="([^"]+)"', boards[code]):
                self.assertIn(labels["confidence"][key], board)
            for key in re.findall(r'data-claim-label="([^"]+)"', boards[code]):
                self.assertIn(labels["claim_label"][key], board)
            strips = " ".join(text(body) for _, body in STRIP.findall(fronts[code]))
            if code == "en":
                continue
            for value in english:
                pattern = r"(?i)\b" + re.escape(value) + r"\b"
                with self.subTest(locale=code, label=value):
                    self.assertNotRegex(board, pattern)
                    self.assertNotRegex(strips, pattern)
            for word in ("primary source", "open gap", "live stor", "Not yet graded"):
                self.assertNotIn(word, board + strips)

    def test_unknown_or_missing_confidence_is_unrated_escaped_and_never_invented(self):
        fronts = self.pages(self.fixture_out, self.fixture_routes, "front")
        self.assertEqual(sorted(fronts), sorted(LOCALES))
        unknown, missing, bare = self.fixture_ids
        for code, page in fronts.items():
            unrated = self.catalogs[code]["strings"]["evidence_board"]["unrated"]
            board = BOARD.search(page).group(0)
            with self.subTest(locale=code):
                segments = dict(re.findall(r'data-segment="([^"]+)" data-count="([0-9]+)"', board))
                self.assertGreaterEqual(int(segments.get("unrated", 0)), 2)
                self.assertIn(unrated, text(board))
                self.assertNotIn("not_a_real_level", text(page))
                self.assertNotIn("<x>", page)
                self.assertIn('data-evidence-class="&lt;x&gt;"', page)
                self.assertNotIn(">&lt;x&gt;<", page)
        rendered = {**self.pages(self.fixture_out, self.fixture_routes, "archive")}
        for code, page in rendered.items():
            unrated = self.catalogs[code]["strings"]["evidence_board"]["unrated"]
            cards = dict(CARD.findall(page))
            for story_id in (unknown, missing):
                strip = STRIP.search(cards[story_id])
                self.assertIn(unrated, text(strip.group(2)))
                self.assertEqual(attrs(strip.group(1))["confidence"],
                                 "not_a_real_level" if story_id == unknown else "")
            strip = STRIP.search(cards[bare])
            values = attrs(strip.group(1))
            self.assertEqual((values["primary-sources"], values["open-gaps"], values["claims"]), ("0", "0", "0"))
            self.assertIn(plural(self.catalogs[code], "primary_source", 0), text(strip.group(2)))
        catalog = self.catalogs["en"]
        empty = evidence_strip({"id": "x"}, catalog)
        self.assertIn('data-evidence-class="" data-confidence="" data-primary-sources="0" data-open-gaps="0" data-claims="0"', empty)
        self.assertIn(catalog["strings"]["evidence_board"]["unrated"], empty)
        board = evidence_board([{"id": "x"}, {"id": "y", "evidence": {"claims": [{"text": "t"}, {"label": "NOT_IN_GLOSSARY"}]}}], catalog)
        self.assertIn('data-segment="unrated" data-count="2"', board)
        self.assertIn('data-claim-label="UNLABELED" data-count="1"', board)
        self.assertIn('data-claim-label="NOT_IN_GLOSSARY" data-count="1"', board)
        self.assertIn(catalog["strings"]["evidence_board"]["unlabeled"], board)
        self.assertNotIn(">NOT_IN_GLOSSARY<", board)

    def test_plural_forms_follow_the_catalog_for_one_and_many(self):
        cases = {
            "en": ("1 primary source", "3 primary sources", "1 open gap", "3 open gaps"),
            "es-419": ("1 fuente primaria", "3 fuentes primarias", "1 vacío abierto", "3 vacíos abiertos"),
        }
        for code, (one_source, many_sources, one_gap, many_gaps) in cases.items():
            catalog = self.catalogs[code]
            self.assertEqual(plural(catalog, "primary_source", 1), one_source)
            self.assertEqual(plural(catalog, "primary_source", 3), many_sources)
            self.assertEqual(plural(catalog, "open_gap", 1), one_gap)
            self.assertEqual(plural(catalog, "open_gap", 3), many_gaps)
            archive = self.pages(self.out, self.routes, "archive")[code]
            for story_id, body in CARD.findall(archive):
                match = STRIP.search(body)
                values, visible = attrs(match.group(1)), text(match.group(2))
                sources, open_gaps = int(values["primary-sources"]), int(values["open-gaps"])
                self.assertIn(plural(catalog, "primary_source", sources), visible)
                self.assertIn(plural(catalog, "open_gap", open_gaps), visible)
                if sources == 1:
                    self.assertNotIn(many_sources.replace("3", "1"), visible)
                if open_gaps == 1:
                    self.assertNotIn(many_gaps.replace("3", "1"), visible)

    def test_css_styles_board_and_strip_including_mobile(self):
        css = (self.out / "assets/css/paper.css").read_text(encoding="utf-8")
        for selector in (".evidence-board{", "p.evidence-strip{", ".evidence-seg{", ".evidence-legend{", ".evidence-claims ul{"):
            self.assertIn(selector, css)
        rules = css[css.index("/* v4 evidence signature"):]
        mobile = rules[rules.index("@media(max-width:520px){"):]
        self.assertRegex(mobile, r"\.evidence-board\{[^}]*padding")
        self.assertRegex(mobile, r"p\.evidence-strip\{[^}]*font-size")
        self.assertRegex(mobile, r"\.evidence-legend\{grid-template-columns:minmax\(0,1fr\)\}")
        self.assertNotRegex(rules, r"url\(")

    def test_no_fcmo_group_in_board_or_strips(self):
        for code, page in self.fronts().items():
            surfaces = BOARD.search(page).group(0) + "".join(match.group(0) for match in STRIP.finditer(page))
            self.assertNotRegex(surfaces, re.compile(r"FCMO\s+Group", re.I), code)


if __name__ == "__main__":
    unittest.main()
