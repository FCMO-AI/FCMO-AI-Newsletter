"""Tests for tools/story_layer.py and tools/taxonomy.py (stories.v2, ledger, taxonomy)."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.harness.validate import validator_for
from tools import build_newsroom_surfaces as surfaces
from tools import ingest_corpus, story_layer, taxonomy

REPO = Path(__file__).resolve().parents[1]
CONTRACTS = REPO / "contracts"
FIXTURES = CONTRACTS / "fixtures"
CORPUS = REPO / "corpus"
TOOL = REPO / "tools" / "story_layer.py"
NOW = "2026-09-26T20:00:00Z"
FDBE = "FCMO-FDBE3D996243"
MERGES = {"FCMO-EEF757F0D806": "FCMO-1A874373897A", "FCMO-1E497EDC718A": "FCMO-C74403EE205F"}
BEATS = {"technology", "business", "policy", "society", "research"}
FULL_HISTORY = story_layer.is_full_history(REPO)


def build(corpus: Path = CORPUS, site: Path | None = REPO / "site", now: str = NOW,
          history_repo: Path | None = REPO) -> tuple[dict, str]:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        inputs = story_layer.StoryInputs(corpus, history_repo, site, site / "data" / "i18n" if site else None, now)
        document = story_layer.build_stories(inputs)
    return document, err.getvalue()


def by_id(document: dict) -> dict[str, dict]:
    return {s["id"]: s for s in document["stories"]}


def expected_live_ids(corpus: Path = CORPUS) -> set[str]:
    """Independent admission census; daily supply must not freeze a test count."""
    rows = taxonomy.read_jsonl(corpus / "data/developments.jsonl")
    dead = {r["id"] for r in rows if r.get("status") in {"withdrawn", "superseded"}}
    dead.update(e["id"] for e in json.loads((corpus / "tombstones.json").read_text())["tombstones"]
                if e.get("reinstated_at") is None)
    return {r["id"] for r in rows} - dead


class RepositoryStoryLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.stderr = build()
        cls.stories = by_id(cls.document)

    def test_published_edition_dates_survive_without_a_new_story(self):
        self.assertIn("2026-10-03", self.document["published_edition_dates"])
        self.assertIn("2026-10-04", self.document["published_edition_dates"])
        # Research snapshots carry no publication authority by their date alone.
        self.assertNotIn("2026-09-24", self.document["published_edition_dates"])
        # The October 4 dates come from these records' actual first-publication history.
        self.assertEqual({story["id"] for story in self.document["stories"]
                          if story["url_date"] == "2026-10-04"},
                         {"FCMO-045BB8282222", "FCMO-5B5B447325A8"})

    def test_validates_against_stories_v2_schema(self) -> None:
        validator = validator_for(CONTRACTS / "stories.v2.schema.json")
        self.assertEqual(validator.errors(self.document), [])

    def test_localized_relationship_summaries_reach_the_story_layer(self):
        target = "FCMO-BBBBBBBBBBBB"
        story = {
            "evidence": {"claims": [], "limitations": [], "gaps": [], "contradictory": []},
            "related": [{"id": target, "type": "related", "summary": "English relationship summary."}],
        }
        overlay = {"relationships": [{"target_id": target, "type": "related", "summary": "Resumen de la relación."}]}
        fields = story_layer.locale_fields(overlay, story, derived_headline=False, derived_dek=False)
        self.assertEqual(fields["related"], [{
            "id": target, "type": "related", "summary": "Resumen de la relación."
        }])

    def test_cli_build_writes_a_valid_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stories.json"
            proc = subprocess.run([sys.executable, str(TOOL), "build", "--corpus", str(CORPUS), "--history-git", str(REPO),
                                   "--out", str(out), "--now", NOW], capture_output=True, text=True, cwd=REPO)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(),
                             f"stories OK live={len(expected_live_ids())} withdrawn=1 merged=2 "
                             f"front_page={sum(s['front_page_eligible'] for s in self.document['stories'])}")
            validate = subprocess.run([sys.executable, str(REPO / "tests" / "harness" / "validate.py"),
                                       str(CONTRACTS / "stories.v2.schema.json"), str(out)], capture_output=True, text=True)
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)

    def test_first_publication_comes_from_the_ledger(self) -> None:
        self.assertEqual(self.stories["FCMO-FAD9D0AFD3E4"]["first_published_at"], "2026-09-14T02:48:13Z")
        ledger = json.loads((CORPUS / "first-published.json").read_text())["entries"]
        for rid, frozen in ledger.items():
            story = self.stories[rid]
            for key in ("first_published_at", "url_date", "slug"):
                self.assertEqual(story[key], frozen[key], f"{rid} {key}")
        # The bridge can deliver records before first-published.json is advanced.
        # Published fallback values come from the committed Story surface; a
        # never-published record uses the explicit candidate clock, not the seal.
        published = {row["research_id"]: row["published_at"] for row in
                     json.loads((REPO / "site/data/stories.json").read_text())}
        for rid in set(self.stories) - set(ledger):
            stamp = published.get(rid, NOW)
            self.assertEqual(self.stories[rid]["first_published_at"], stamp, rid)
            self.assertEqual(self.stories[rid]["url_date"], story_layer.mx_date(stamp), rid)

    def test_one_story_per_public_id_and_live_admission_census(self) -> None:
        corpus_ids = {json.loads(l)["id"] for l in (CORPUS / "data" / "developments.jsonl").read_text().splitlines() if l.strip()}
        self.assertEqual(set(self.stories), corpus_ids | {FDBE})
        live = [s for s in self.document["stories"] if s["status"] == "live"]
        self.assertEqual({s["id"] for s in live}, expected_live_ids())
        self.assertLessEqual({s["beat"] for s in live}, BEATS)
        self.assertEqual(self.stderr, "")

    def test_merges(self) -> None:
        for dup, survivor in MERGES.items():
            story = self.stories[dup]
            self.assertEqual((story["status"], story["merged_into"]), ("merged", survivor))
            self.assertFalse(story["front_page_eligible"])
            self.assertEqual([(c["kind"], c["reason_code"]) for c in story["corrections"]], [("merge", "DUPLICATE")])
            self.assertIn({"id": survivor, "type": "duplicate_of"}, story["related"])
            self.assertIn({"id": dup, "type": "supersedes"}, self.stories[survivor]["related"])
            self.assertEqual(self.stories[survivor]["status"], "live")
            self.assertLess(self.stories[survivor]["first_published_at"], story["first_published_at"])

    def test_orphan_is_withdrawn_with_a_public_correction(self) -> None:
        story = self.stories[FDBE]
        self.assertEqual(story["status"], "withdrawn")
        self.assertEqual(story["url_date"], "2026-09-18")
        self.assertEqual(story["first_published_at"], "2026-09-18T22:36:23Z")
        self.assertFalse(story["front_page_eligible"])
        self.assertEqual(len(story["corrections"]), 1)
        fix = story["corrections"][0]
        self.assertEqual((fix["kind"], fix["reason_code"], fix["at"]), ("withdrawal", "UNVERIFIED_RELEASE", "2026-09-23T11:32:15Z"))
        self.assertEqual(set(fix["text"]), {"en", "es-419", "zh-Hans"})
        self.assertEqual(story["updated_at"], "2026-09-23T11:32:15Z")

    def test_headline_and_dek_are_never_truncated(self) -> None:
        for story in self.document["stories"]:
            if "headline" in story:
                self.assertEqual(story["headline"], " ".join(story["title"].split()))
            if "dek" in story:
                self.assertTrue(" ".join(story["summary"].split()).startswith(story["dek"]))
                self.assertRegex(story["dek"], r"[.!?]$")
            self.assertEqual(story["front_page_eligible"],
                             story["status"] == "live" and "headline" in story and "dek" in story)
            for locale, entry in story["l10n"].items():
                for key in ("headline", "dek"):
                    if key in entry["fields"]:
                        self.assertNotRegex(entry["fields"][key], r"(\.\.\.|…)$")

    def test_matches_fixture_stories_on_derived_fields(self) -> None:
        fixture = by_id(json.loads((FIXTURES / "stories.v2.json").read_text()))
        keys = ("slug", "url_date", "kind", "status", "beat", "desk", "event_at", "date_precision",
                "first_published_at", "importance", "evidence_class", "confidence", "carried_forward",
                "sources", "organizations", "topics", "regions", "merged_into")
        for rid, expected in fixture.items():
            for key in keys:
                self.assertEqual(self.stories[rid].get(key), expected.get(key), f"{rid} {key}")
            self.assertEqual(self.stories[rid]["evidence"]["claims"], expected["evidence"]["claims"], rid)

    def test_localization_states_are_honest(self) -> None:
        for story in self.document["stories"]:
            for locale, entry in story["l10n"].items():
                if entry["state"] in {"NATIVE_ARB", "MACHINE_REVIEWED"}:
                    self.assertEqual(entry["missing"], [])
                    self.assertTrue({"title", "summary", "why_it_matters"} <= set(entry["fields"]))
                    selected = set(entry["provenance"].values())
                    if entry["state"] == "NATIVE_ARB":
                        self.assertEqual(selected, {"arb"})
                    else:
                        self.assertIn("publication-desk", selected)
                else:
                    self.assertEqual(entry["state"], "PENDING")
                    self.assertTrue(entry["missing"], f"{story['id']} {locale}")
                for field in entry["fields"]:
                    if field in ("title", "summary", "why_it_matters"):
                        self.assertNotEqual(entry["fields"][field], story[field], "no English fallback")

    def test_ledger_is_frozen_and_idempotent(self) -> None:
        entries = json.loads((CORPUS / "first-published.json").read_text())["entries"]
        ledger, tombstones, _ = story_layer.update_ledger(CORPUS, REPO, REPO / "site", NOW)
        self.assertEqual({rid: ledger["entries"][rid] for rid in entries}, entries)
        published = {s["research_id"]: s["published_at"] for s in
                     json.loads((REPO / "site/data/stories.json").read_text())}
        for rid in set(ledger["entries"]) - set(entries):
            self.assertEqual(ledger["entries"][rid]["first_published_at"], published[rid])
        # A newly composed edition can precede the corpus-owned ledger. Prove
        # idempotence on its completed ledger without modifying the real corpus.
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus"
            shutil.copytree(CORPUS, corpus)
            (corpus / "first-published.json").write_text(json.dumps(ledger))
            (corpus / "tombstones.json").write_text(json.dumps(tombstones))
            again, _, changes = story_layer.update_ledger(corpus, REPO, REPO / "site", NOW)
            self.assertEqual(again, ledger)
            self.assertEqual(changes, [])
        validator = validator_for(CONTRACTS / "first-published.schema.json")
        self.assertEqual(validator.errors(json.loads((CORPUS / "first-published.json").read_text())), [])


class TemporaryCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self._corpus: Path | None = None

    @property
    def corpus(self) -> Path:
        if self._corpus is None:
            self._corpus = Path(self.tmp.name) / "corpus"
            shutil.copytree(CORPUS, self._corpus)
            rows = taxonomy.read_jsonl(self._corpus / "data/developments.jsonl")
            valid = [row for row in rows if row["id"] != FDBE and not taxonomy.normalize_rows([row])[1]]
            (self._corpus / "data/developments.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in valid))
        return self._corpus

    def fixture_corpus(self) -> Path:
        """Build the carried-record case only from source-controlled fixtures."""
        corpus = Path(self.tmp.name) / "fixture-corpus"
        (corpus / "data").mkdir(parents=True)
        (corpus / "editions").mkdir()
        (corpus / "data" / "developments.jsonl").write_text("")
        shutil.copyfile(FIXTURES / "corpus-carried.example.jsonl", corpus / "carried.jsonl")
        ledger = json.loads((FIXTURES / "first-published.json").read_text())
        ledger["entries"] = {FDBE: ledger["entries"][FDBE]}
        (corpus / "first-published.json").write_text(json.dumps(ledger))
        shutil.copyfile(FIXTURES / "tombstones.json", corpus / "tombstones.json")
        return corpus

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def rows(self) -> list[dict]:
        path = self.corpus / "data" / "developments.jsonl"
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    def write_rows(self, rows: list[dict]) -> None:
        path = self.corpus / "data" / "developments.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))

    def tombstones(self) -> dict:
        return json.loads((self.corpus / "tombstones.json").read_text())

    def test_reinstating_is_a_one_line_data_change(self) -> None:
        doc = self.tombstones()
        next(e for e in doc["tombstones"] if e["id"] == FDBE)["reinstated_at"] = NOW
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        document, stderr = build(self.corpus)
        story = by_id(document)[FDBE]
        self.assertEqual(story["status"], "live")
        self.assertTrue(story["carried_forward"])
        self.assertEqual([c["kind"] for c in story["corrections"]], ["withdrawal", "reinstatement"])
        self.assertIn(f"ALERT STORY_ORPHAN {FDBE}", stderr)
        self.assertEqual(validator_for(CONTRACTS / "stories.v2.schema.json").errors(document), [])

    def test_bad_record_is_quarantined_not_fatal(self) -> None:
        before, _ = build(self.corpus)
        rows = self.rows()
        victim = rows[5]["id"]
        rows[5]["claims"] = []
        rows[6].pop("primary_desk")
        rows[6]["desks"] = []
        self.write_rows(rows)
        document, stderr = build(self.corpus)
        self.assertIn(f"QUARANTINE {victim} CLAIMS_MISSING", stderr)
        self.assertIn(f"QUARANTINE {rows[6]['id']} DESK_UNKNOWN", stderr)
        self.assertNotIn(victim, by_id(document))
        self.assertEqual(len(document["stories"]), len(before["stories"]) - 2)

    def test_carried_record_stays_live(self) -> None:
        self._corpus = self.fixture_corpus()
        doc = self.tombstones()
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] != FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        document, stderr = build(self.corpus, site=None, history_repo=None)
        story = by_id(document)[FDBE]
        self.assertEqual((story["status"], story["carried_forward"]), ("live", True))
        self.assertEqual(story["first_published_at"], "2026-09-18T22:36:23Z")
        self.assertEqual(stderr, "")

    def test_upstream_withdrawal_needs_no_human(self) -> None:
        rows = self.rows()
        rows[0]["status"] = "withdrawn"
        self.write_rows(rows)
        story = by_id(build(self.corpus)[0])[rows[0]["id"]]
        self.assertEqual(story["status"], "withdrawn")
        self.assertEqual(story["corrections"][0]["kind"], "withdrawal")
        self.assertEqual(story["corrections"][0]["reason_code"], "UPSTREAM_RETRACTION")

    def test_unrecorded_duplicates_are_still_merged(self) -> None:
        (self.corpus / "first-published.json").unlink()
        doc = self.tombstones()
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] == FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        document, stderr = build(self.corpus)
        for dup, survivor in MERGES.items():
            self.assertIn(f"MERGE_UNRECORDED {dup} -> {survivor}", stderr)
            self.assertEqual(by_id(document)[dup]["merged_into"], survivor)
        self.assertEqual({s["id"] for s in document["stories"] if s["status"] == "live"}, expected_live_ids())

    @unittest.skipUnless(FULL_HISTORY, "needs the full git history")
    def test_ledger_from_history_equals_the_contract_fixture(self) -> None:
        (self.corpus / "first-published.json").unlink()
        doc = self.tombstones()
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] == FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        ledger, tombstones, changes = story_layer.update_ledger(self.corpus, REPO, REPO / "site", NOW)
        historical = json.loads((FIXTURES / "first-published.json").read_text())
        self.assertEqual({rid: ledger["entries"][rid] for rid in historical["entries"]}, historical["entries"])
        # New supply extends the ledger, while every frozen historical entry stays exact.
        committed = json.loads((CORPUS / "first-published.json").read_text())
        self.assertEqual({rid: ledger["entries"][rid] for rid in committed["entries"]}, committed["entries"])
        published = {s["research_id"]: s["published_at"] for s in
                     json.loads((REPO / "site/data/stories.json").read_text())}
        for rid in set(ledger["entries"]) - set(committed["entries"]):
            self.assertEqual(ledger["entries"][rid]["first_published_at"], published[rid])
        added = [e for e in tombstones["tombstones"] if e["id"] != FDBE]
        self.assertEqual({e["id"]: e["superseded_by"] for e in added}, MERGES)
        self.assertEqual({e["action"] for e in added}, {"superseded"})
        self.assertEqual(validator_for(CONTRACTS / "tombstones.schema.json").errors(tombstones), [])

    def test_unpublished_id_is_not_frozen(self) -> None:
        rows = self.rows()
        new = dict(rows[0], id="FCMO-00000000ABCD", title="A brand new development that nobody has published yet")
        new["source_urls"] = ["https://example.org/new-development"]
        self.write_rows(rows + [new])
        ledger, _, changes = story_layer.update_ledger(self.corpus, REPO, REPO / "site", NOW)
        self.assertNotIn("FCMO-00000000ABCD", ledger["entries"])
        story = by_id(build(self.corpus, now="2026-09-27T08:00:00Z")[0])["FCMO-00000000ABCD"]
        self.assertEqual(story["first_published_at"], "2026-09-27T08:00:00Z")
        self.assertEqual(story["url_date"], "2026-09-27")
        self.assertEqual(story["slug"], "a-brand-new-development-that-nobody-has-published-yet")


class ShallowCheckoutTests(unittest.TestCase):
    """CI checkouts have no git history: the previous stories.v2 output stands in for it."""

    def build_without_history(self, previous: dict | None) -> tuple[dict, str]:
        err = io.StringIO()
        site = REPO / "site"
        with contextlib.redirect_stderr(err):
            inputs = story_layer.StoryInputs(CORPUS, None, site, site / "data" / "i18n", NOW, previous=previous or {})
            document = story_layer.build_stories(inputs)
        return document, err.getvalue()

    def test_previous_v2_restores_what_history_would(self) -> None:
        full, _ = build()
        document, stderr = self.build_without_history(full)
        self.assertEqual(document, full)
        self.assertEqual(by_id(document)[FDBE]["status"], "withdrawn")
        self.assertNotIn("STORY_RECORD_UNAVAILABLE", stderr)

    def test_previous_story_follows_the_current_tombstones(self) -> None:
        full, _ = build()
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus"
            shutil.copytree(CORPUS, corpus)
            doc = json.loads((corpus / "tombstones.json").read_text())
            next(e for e in doc["tombstones"] if e["id"] == FDBE)["reinstated_at"] = NOW
            (corpus / "tombstones.json").write_text(json.dumps(doc))
            with contextlib.redirect_stderr(io.StringIO()):
                inputs = story_layer.StoryInputs(corpus, None, REPO / "site", REPO / "site" / "data" / "i18n", NOW, previous=full)
                story = by_id(story_layer.build_stories(inputs))[FDBE]
        self.assertEqual(story["status"], "live")
        self.assertEqual([c["kind"] for c in story["corrections"]], ["withdrawal", "reinstatement"])
        self.assertEqual(story["first_published_at"], "2026-09-18T22:36:23Z")

    def test_no_source_at_all_is_reported_not_invented(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            corpus = Path(temporary) / "corpus"
            shutil.copytree(CORPUS, corpus)
            rows = [row for row in taxonomy.read_jsonl(corpus / "data/developments.jsonl") if row["id"] != FDBE]
            (corpus / "data/developments.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                document = story_layer.build_stories(story_layer.StoryInputs(corpus, None, REPO / "site", REPO / "site/data/i18n", NOW, previous={}))
            stderr = error.getvalue()
        self.assertNotIn(FDBE, by_id(document))
        self.assertIn(f"ALERT STORY_RECORD_UNAVAILABLE {FDBE}", stderr)
        self.assertEqual({s["id"] for s in document["stories"] if s["status"] == "live"}, expected_live_ids())


class NewsroomOutputTests(unittest.TestCase):
    """build_newsroom_surfaces.py writes the v2 data, corrections and notice pages."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name) / "site"
        (self.site / "news" / "en").mkdir(parents=True)
        (self.site / "developments").mkdir()
        (self.site / "news" / "en" / f"{FDBE}.html").write_text("<html><h1>Old &amp; true headline</h1></html>")
        for dup in MERGES:
            (self.site / "developments" / f"{dup}.html").write_text("stale dossier")
        self.document, _ = build()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def read(self, rel: str) -> str:
        return (self.site / rel).read_text(encoding="utf-8")

    def test_notices_corrections_and_data(self) -> None:
        notices = surfaces.write_story_layer_outputs(self.site, self.document, CORPUS)
        self.assertEqual(notices, 9)
        self.assertEqual(json.loads(self.read("data/stories.v2.json")), self.document)
        rows = json.loads(self.read("data/corrections.json"))
        self.assertEqual({(r["story_id"], r["kind"]) for r in rows},
                         {(FDBE, "withdrawal"), *((dup, "merge") for dup in MERGES)})
        for dup, survivor in MERGES.items():
            self.assertFalse((self.site / "developments" / f"{dup}.html").exists())
            page = self.read(f"news/es/{dup}.html")
            self.assertIn(f'rel="canonical" href="{surfaces.BASE}/news/es/{survivor}.html"', page)
            self.assertIn('data-fcmo-story-status="merged"', page)
        page = self.read(f"news/zh-hans/{FDBE}.html")
        self.assertIn('data-fcmo-story-status="withdrawn"', page)
        self.assertIn("noindex", page)

    def test_tombstone_alone_still_retires_the_page(self) -> None:
        document = dict(self.document, stories=[s for s in self.document["stories"] if s["id"] != FDBE])
        for _ in range(2):  # the second run reads the title back from corrections.json
            self.assertEqual(surfaces.write_story_layer_outputs(self.site, document, CORPUS), 9)
            page = self.read(f"news/en/{FDBE}.html")
            self.assertIn('data-fcmo-story-status="withdrawn"', page)
            self.assertIn("Old &amp; true headline", page)
            row = next(r for r in json.loads(self.read("data/corrections.json")) if r["story_id"] == FDBE)
            self.assertEqual((row["kind"], row["reason_code"], row["story_title"]),
                             ("withdrawal", "UNVERIFIED_RELEASE", "Old & true headline"))
        self.assertNotIn(FDBE, by_id(json.loads(self.read("data/stories.v2.json"))))


class IngestSelectionTests(unittest.TestCase):
    """ingest_corpus.publishable_rows decides per record, never for the whole batch."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.corpus = Path(self.tmp.name) / "corpus"
        shutil.copytree(CORPUS, self.corpus)
        self.rows = taxonomy.read_jsonl(self.corpus / "data" / "developments.jsonl")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def select(self, rows: list) -> tuple[list, dict, list]:
        return ingest_corpus.publishable_rows(self.corpus, rows)

    def test_historical_edition_keeps_references_to_quarantined_records(self):
        selected, _, _ = self.select(self.rows)
        edition = ingest_corpus.parse_edition(self.corpus / "editions/2026-10-03.html",
                                             {row["id"] for row in selected})
        self.assertEqual(edition["related_brief_ids"], ["FCMO-5B5B447325A8", "FCMO-045BB8282222"])

    def test_repository_corpus_publishes_every_admitted_id(self) -> None:
        selected, merged, held = self.select(self.rows)
        self.assertEqual({r["id"] for r in selected}, expected_live_ids())
        self.assertEqual(merged, MERGES)
        self.assertEqual(sorted(held), sorted([(FDBE, "TOMBSTONED:UNVERIFIED_RELEASE"),
                                               *((dup, "TOMBSTONED:DUPLICATE") for dup in MERGES)]))

    def test_one_bad_record_is_held_back_alone(self) -> None:
        rows = [dict(r) for r in self.rows]
        rows[3]["claims"] = []
        rows[4]["status"] = "withdrawn"
        selected, _, held = self.select(rows)
        self.assertEqual({r["id"] for r in selected}, expected_live_ids() - {rows[3]["id"], rows[4]["id"]})
        self.assertIn((rows[3]["id"], "QUARANTINE:CLAIMS_MISSING"), held)
        self.assertIn((rows[4]["id"], "WITHDRAWN_UPSTREAM"), held)

    def test_mass_quarantine_refuses_the_batch(self) -> None:
        # Exceed the actual 20% limit as the autonomous corpus grows.
        count = len(self.rows) // 5 + 1
        rows = [dict(r, claims=[]) if i < count else r for i, r in enumerate(self.rows)]
        with self.assertRaisesRegex(ValueError, f"refusing to publish: {count} of"):
            self.select(rows)

    def test_carried_record_is_published(self) -> None:
        doc = json.loads((self.corpus / "tombstones.json").read_text())
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] != FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        line = (FIXTURES / "corpus-carried.example.jsonl").read_text().splitlines()[0]
        (self.corpus / "carried.jsonl").write_text(line + "\n")
        selected, _, held = self.select(self.rows)
        self.assertIn(FDBE, {r["id"] for r in selected})
        self.assertEqual({r["id"] for r in selected}, expected_live_ids() | {FDBE})


class TaxonomyTests(unittest.TestCase):
    def test_every_corpus_record_normalizes_to_record_v3(self) -> None:
        validator = validator_for(CONTRACTS / "record.v3.schema.json")
        for source in (CORPUS / "data" / "developments.jsonl", FIXTURES / "corpus-44" / "data" / "developments.jsonl"):
            records, quarantined = taxonomy.normalize_rows(taxonomy.read_jsonl(source))
            self.assertEqual(quarantined, [])
            for record in records:
                self.assertEqual(validator.errors(record), [], record["id"])

    def test_invalid_event_at_is_quarantined_on_a_fixture_record(self) -> None:
        source = taxonomy.read_jsonl(FIXTURES / "corpus-44" / "data" / "developments.jsonl")[0]
        bad = dict(source, id="FCMO-00000000BAD1", event_at="not-a-date")
        records, quarantined = taxonomy.normalize_rows([source, bad])
        self.assertEqual([record["id"] for record in records], [source["id"]])
        self.assertEqual(quarantined, [("FCMO-00000000BAD1", ["EVENT_AT_INVALID"])])

    def test_not_established_claim_stays_explicit_and_unknown_claims_fail_closed(self) -> None:
        source = taxonomy.read_jsonl(FIXTURES / "corpus-44" / "data" / "developments.jsonl")[0]
        row = dict(source, claims=[{"label": "NOT_ESTABLISHED", "text": "Independent validity has not been established."}])
        record = taxonomy.normalize_record(row)
        self.assertEqual(record["claims"][0]["label"], "NOT_ESTABLISHED")
        self.assertEqual(validator_for(CONTRACTS / "record.v3.schema.json").errors(record), [])
        row["claims"] = [{"label": "UNRECOGNIZED_EVIDENCE_STATE", "text": "Unsupported label."}]
        with self.assertRaisesRegex(taxonomy.Quarantine, "CLAIM_LABEL_UNKNOWN"):
            taxonomy.normalize_record(row)

    def test_vocabulary_maps(self) -> None:
        self.assertEqual(taxonomy.normalize_desk("efficiency_quantization_sparsity_compression"), "compute_inference")
        self.assertEqual(taxonomy.normalize_desk("Evaluation / Science"), "evaluation_science")
        self.assertIsNone(taxonomy.normalize_desk("gardening"))
        self.assertEqual(taxonomy.normalize_development_type("paper_case_study"), "paper")
        self.assertEqual(taxonomy.normalize_development_type("policy_security"), "policy_action")
        self.assertEqual(taxonomy.normalize_confidence("vendor_specced_unbenchmarked"), "claimed_unverified")
        self.assertEqual(taxonomy.normalize_claim_label("DEMONSTRATED_PRIMARY"), ("DEMONSTRATED", "PRIMARY"))
        self.assertEqual(taxonomy.normalize_claim_label("VENDOR_CLAIM"), ("CLAIMED", "VENDOR"))
        self.assertEqual(taxonomy.normalize_claim_label("COUNTERPOSITION"), ("DISPUTED", "COUNTERPOSITION"))
        self.assertEqual(taxonomy.normalize_claim_label("DEMONSTRATED"), ("DEMONSTRATED", None))
        self.assertEqual(taxonomy.normalize_region("United States"), "US")
        self.assertEqual(taxonomy.normalize_region("Ohio"), "US")
        self.assertEqual(taxonomy.normalize_region("UK"), "GB")
        self.assertEqual(taxonomy.normalize_region("global"), "GLOBAL")
        self.assertIsNone(taxonomy.normalize_region("Middle East"))
        self.assertEqual(taxonomy.normalize_language("Polish"), "pl")
        self.assertEqual(taxonomy.infer_date_precision("2026-09-02T00:00:00Z"), "day")
        self.assertEqual(taxonomy.infer_date_precision("2026-09"), "month")
        self.assertEqual(taxonomy.infer_date_precision("2026-09-02T14:05:00Z"), "minute")

    def test_slugify(self) -> None:
        self.assertEqual(taxonomy.slugify("M&A: NVIDIA's $105B deal at 4.25%"), "m-a-nvidias-105b-deal-at-4-25")
        self.assertEqual(taxonomy.slugify("8–128 core Café"), "8-128-core-cafe")
        long = taxonomy.slugify("word " * 40, 72)
        self.assertLessEqual(len(long), 72)
        self.assertFalse(long.endswith("-"))

    def test_headline_and_dek_derivation_never_cuts(self) -> None:
        self.assertEqual(taxonomy.derive_headline("NVIDIA agrees to buy Hugging Face"), "NVIDIA agrees to buy Hugging Face")
        self.assertIsNone(taxonomy.derive_headline("x" * 91))
        self.assertEqual(taxonomy.derive_dek("The U.S. Commerce Department issued new rules today. More text follows here."),
                         "The U.S. Commerce Department issued new rules today.")
        self.assertIsNone(taxonomy.derive_dek("Too short. Then more."))
        self.assertIsNone(taxonomy.derive_dek("A sentence without an end " * 20))
        self.assertIsNone(taxonomy.derive_dek(("A very long first sentence " * 12) + "ends here. Second."))

    def test_one_bad_row_does_not_stop_the_batch(self) -> None:
        good = [row for row in taxonomy.read_jsonl(CORPUS / "data" / "developments.jsonl")
                if not taxonomy.normalize_rows([row])[1]][:3]
        bad = [dict(good[0], id="FCMO-000000000BAD", confidence="vibes"), "not a row",
               {"id": "nope"}]
        records, quarantined = taxonomy.normalize_rows(good + bad + [good[0]])
        self.assertEqual(len(records), 3)
        self.assertEqual(quarantined[0], ("FCMO-000000000BAD", ["CONFIDENCE_UNKNOWN"]))
        self.assertEqual([codes for _, codes in quarantined[1:]], [["NOT_AN_OBJECT"], ["ID_INVALID"], ["DUPLICATE_ID"]])


if __name__ == "__main__":
    unittest.main()
