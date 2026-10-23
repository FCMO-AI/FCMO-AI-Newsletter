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
# c6 / DIRECCION s2, s5, s6: the root front (route kind "landing") carries the evidence per
# item as a class chip row (evrow) on board cards and wire rows, and the corpus aggregate as
# the method band. c6 round 3 (DIRECCION s3, s6; CONTRACT-CHANGES «Round 3 — integrator»): the
# listings (topic/org/beat/archive) carry the same class chip row (list-evrow) per card instead of
# the old evidence strip, so they are held to the same per-item rule as the front.
BAND = re.compile(r'<section class="method-band" id="method-band".*?</section>', re.S)
FRONT_ITEM = re.compile(r'<(?:article|li) class="(?:plate-card|wire-row)[^"]*"[^>]*data-story-id="([^"]+)"(.*?)</(?:article|li)>', re.S)
EVROW = re.compile(r'<(p|div) class="[^"]*\bevrow\b[^"]*" data-evidence-class="([^"]*)">(.*?)</\1>', re.S)
BAND_TRIO = re.compile(r'<div class="band-trio">(.*?)</div><p class="band-note">', re.S)
BAND_NUMS = re.compile(r'<li>([0-9]+)<span>', re.S)
CLASSES = ("shown", "claimed", "not_established")
SHOWN_CONFIDENCE = {"confirmed", "strongly_supported", "supported"}


def derived_class(story: dict) -> str:
    """Independent restatement of the item-level class rule (DIRECCION s3: never rounds up)."""
    if story.get("confidence") in SHOWN_CONFIDENCE:
        return "shown"
    claims = (story.get("evidence") or {}).get("claims") or []
    if story.get("confidence") or any(isinstance(c, dict) and c.get("label") for c in claims):
        return "claimed"
    return "not_established"


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
        found = self.pages(self.out, self.routes, "landing")
        self.assertEqual(sorted(found), sorted(LOCALES))
        return found

    def boards(self) -> dict[str, str]:
        return {code: BAND.search(page).group(0) for code, page in self.fronts().items()}

    def assert_front_rows_match_corpus(self, page: str, code: str, stories: dict, *, minimum: int) -> None:
        rows = FRONT_ITEM.findall(page)
        self.assertGreaterEqual(len(rows), minimum)
        proof = self.catalogs[code]["strings"]["proof"]
        for story_id, body in rows:
            with self.subTest(story=story_id):
                found = EVROW.findall(body)
                self.assertEqual(len(found), 1)
                klass = found[0][1]
                story = stories[story_id]
                self.assertEqual(klass, derived_class(story))
                visible = text(found[0][2])
                self.assertIn(proof[klass], visible)
                self.assertIn(plural(self.catalogs[code], "primary_source", primary(story)), visible)
                self.assertIn(plural(self.catalogs[code], "open_gap", gaps(story)), visible)
        for _, klass, _ in EVROW.findall(page):
            self.assertIn(klass, CLASSES)

    def assert_listing_rows_match_corpus(self, page: str, code: str, stories: dict, *, minimum: int) -> None:
        cards = CARD.findall(page)
        self.assertGreaterEqual(len(cards), minimum)
        proof = self.catalogs[code]["strings"]["proof"]
        for story_id, body in cards:
            with self.subTest(story=story_id):
                self.assertEqual(STRIP.findall(body), [])  # one evidence line per card, never two
                found = EVROW.findall(body)
                self.assertEqual(len(found), 1)
                klass = found[0][1]
                story = stories[story_id]
                self.assertIn(klass, CLASSES)
                self.assertEqual(klass, derived_class(story))
                visible = text(found[0][2])
                self.assertIn(proof[klass], visible)
                self.assertIn(plural(self.catalogs[code], "primary_source", primary(story)), visible)
                self.assertIn(plural(self.catalogs[code], "open_gap", gaps(story)), visible)

    def test_strips_on_front_and_listings_match_the_corpus_in_every_locale(self):
        fronts = self.fronts()
        self.assertEqual(sorted(fronts), sorted(LOCALES))
        for code in LOCALES:
            with self.subTest(locale=code, page="front"):
                self.assert_front_rows_match_corpus(fronts[code], code, self.stories, minimum=5)
            for kind in ("topic", "org", "beat"):
                with self.subTest(locale=code, page=kind):
                    listing = self.pages(self.out, self.routes, kind)[code]
                    self.assert_listing_rows_match_corpus(listing, code, self.stories, minimum=1)

    def test_board_aggregates_every_live_story_in_every_locale(self):
        # c6: the aggregate is the front's method band (class trio + corpus figures).
        counts = Counter(derived_class(s) for s in self.live)
        topics = len({t for s in self.live for t in s.get("topics", [])})
        orgs = len({o for s in self.live for o in s.get("organizations", [])})
        for code, band in self.boards().items():
            catalog = self.catalogs[code]
            proof = catalog["strings"]["proof"]
            with self.subTest(locale=code):
                self.assertNotRegex(band[1:], r"<section\b")
                trio = BAND_TRIO.search(band).group(1)
                cells = re.findall(r"<div><b>(.*?)</b>", trio, re.S)
                self.assertEqual([text(cell) for cell in cells],
                                 [f"{proof[key]} · {plural(catalog, 'story', counts[key])}" for key in CLASSES])
                self.assertEqual(sum(counts.values()), len(self.live))
                self.assertEqual([int(n) for n in BAND_NUMS.findall(band)], [len(self.live), topics, orgs])
                self.assertIn('/method/"', band)

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
            proof = self.catalogs[code]["strings"]["proof"]
            for key in CLASSES:
                self.assertIn(proof[key], board)
            strips = " ".join(text(body) for _, _, body in EVROW.findall(fronts[code]))
            self.assertTrue(strips)
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
        fronts = self.pages(self.fixture_out, self.fixture_routes, "landing")
        self.assertEqual(sorted(fronts), sorted(LOCALES))
        unknown, missing, bare = self.fixture_ids
        fixture_stories = {s["id"]: s for s in json.loads((Path(self.temp.name) / "fixture.json").read_text(encoding="utf-8"))["stories"]}
        for code, page in fronts.items():
            band = BAND.search(page).group(0)
            with self.subTest(locale=code):
                # Whatever an item claims about itself, the class is derived: raw text
                # never reaches the page and nothing is rounded up to «Shown».
                self.assertNotIn("not_a_real_level", text(page))
                self.assertNotIn("<x>", page)
                self.assertNotIn("<x>", text(page))
                self.assertNotIn(">&lt;x&gt;<", page)
                self.assertNotIn('data-evidence-class="&lt;x&gt;"', page)
                self.assert_front_rows_match_corpus(page, code, fixture_stories, minimum=5)
                trio = BAND_TRIO.search(band).group(1)
                shown = Counter(derived_class(s) for s in fixture_stories.values() if s.get("status") == "live")
                proof = self.catalogs[code]["strings"]["proof"]
                self.assertEqual([text(c) for c in re.findall(r"<div><b>(.*?)</b>", trio, re.S)],
                                 [f"{proof[k]} · {plural(self.catalogs[code], 'story', shown[k])}" for k in CLASSES])
        self.assertEqual(derived_class(fixture_stories[unknown]), "claimed")  # an unknown level is never «Shown»
        self.assertEqual(derived_class(fixture_stories[bare]), "claimed" if fixture_stories[bare].get("confidence") else "not_established")
        rendered = {**self.pages(self.fixture_out, self.fixture_routes, "archive")}
        self.assertEqual(sorted(rendered), sorted(LOCALES))
        for code, page in rendered.items():
            with self.subTest(locale=code, page="archive"):
                self.assertNotIn("not_a_real_level", text(page))
                self.assertNotIn("<x>", text(page))
                self.assertNotIn('data-evidence-class="&lt;x&gt;"', page)
                cards = dict(CARD.findall(page))
                for story_id in (unknown, missing, bare):
                    self.assertIn(story_id, cards)
                    row = EVROW.search(cards[story_id])
                    self.assertIsNotNone(row)
                    self.assertEqual(row.group(2), derived_class(fixture_stories[story_id]))
                self.assertNotEqual(EVROW.search(cards[unknown]).group(2), "shown")  # never rounded up
                visible = text(EVROW.search(cards[bare]).group(3))
                self.assertIn(plural(self.catalogs[code], "primary_source", 0), visible)
                self.assertIn(plural(self.catalogs[code], "open_gap", 0), visible)
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
            cards = CARD.findall(archive)
            self.assertGreater(len(cards), 0)
            for story_id, body in cards:
                match = EVROW.search(body)
                visible = text(match.group(3))
                sources, open_gaps = primary(self.stories[story_id]), gaps(self.stories[story_id])
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
            surfaces = BAND.search(page).group(0) + "".join(match.group(0) for match in EVROW.finditer(page)) + "".join(match.group(0) for match in STRIP.finditer(page))
            self.assertNotRegex(surfaces, re.compile(r"FCMO\s+Group", re.I), code)


if __name__ == "__main__":
    unittest.main()
