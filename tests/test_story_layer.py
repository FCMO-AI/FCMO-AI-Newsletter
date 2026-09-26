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
from tools import story_layer, taxonomy

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


def build(corpus: Path = CORPUS, site: Path | None = REPO / "site", now: str = NOW) -> tuple[dict, str]:
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        inputs = story_layer.StoryInputs(corpus, REPO, site, site / "data" / "i18n" if site else None, now)
        document = story_layer.build_stories(inputs)
    return document, err.getvalue()


def by_id(document: dict) -> dict[str, dict]:
    return {s["id"]: s for s in document["stories"]}


class RepositoryStoryLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.stderr = build()
        cls.stories = by_id(cls.document)

    def test_validates_against_stories_v2_schema(self) -> None:
        validator = validator_for(CONTRACTS / "stories.v2.schema.json")
        self.assertEqual(validator.errors(self.document), [])

    def test_cli_build_writes_a_valid_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "stories.json"
            proc = subprocess.run([sys.executable, str(TOOL), "build", "--corpus", str(CORPUS), "--history-git", str(REPO),
                                   "--out", str(out), "--now", NOW], capture_output=True, text=True, cwd=REPO)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), "stories OK live=41 withdrawn=1 merged=2 front_page=7")
            validate = subprocess.run([sys.executable, str(REPO / "tests" / "harness" / "validate.py"),
                                       str(CONTRACTS / "stories.v2.schema.json"), str(out)], capture_output=True, text=True)
            self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)

    def test_first_publication_comes_from_the_ledger(self) -> None:
        self.assertEqual(self.stories["FCMO-FAD9D0AFD3E4"]["first_published_at"], "2026-09-14T02:48:13Z")
        ledger = json.loads((CORPUS / "first-published.json").read_text())["entries"]
        for rid, story in self.stories.items():
            self.assertEqual(story["first_published_at"], ledger[rid]["first_published_at"], rid)
            self.assertEqual(story["url_date"], ledger[rid]["url_date"], rid)
            self.assertEqual(story["slug"], ledger[rid]["slug"], rid)

    def test_one_story_per_public_id_and_41_live(self) -> None:
        corpus_ids = {json.loads(l)["id"] for l in (CORPUS / "data" / "developments.jsonl").read_text().splitlines() if l.strip()}
        self.assertEqual(set(self.stories), corpus_ids | {FDBE})
        live = [s for s in self.document["stories"] if s["status"] == "live"]
        self.assertEqual(len(live), 41)
        self.assertLessEqual({s["beat"] for s in live}, BEATS)
        self.assertEqual(self.stderr, "", "the repository corpus needs no quarantine, orphan or unrecorded merge")

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
                if entry["state"] == "NATIVE_ARB":
                    self.assertEqual(entry["missing"], [])
                    self.assertTrue({"title", "summary", "why_it_matters"} <= set(entry["fields"]))
                else:
                    self.assertEqual(entry["state"], "PENDING")
                    self.assertTrue(entry["missing"], f"{story['id']} {locale}")
                for field in entry["fields"]:
                    if field in ("title", "summary", "why_it_matters"):
                        self.assertNotEqual(entry["fields"][field], story[field], "no English fallback")

    def test_ledger_is_frozen_and_idempotent(self) -> None:
        proc = subprocess.run([sys.executable, str(TOOL), "ledger", "--corpus", str(CORPUS), "--history-git", str(REPO),
                               "--check", "--now", NOW], capture_output=True, text=True, cwd=REPO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "ledger OK entries=44 changes=0")
        validator = validator_for(CONTRACTS / "first-published.schema.json")
        self.assertEqual(validator.errors(json.loads((CORPUS / "first-published.json").read_text())), [])


class TemporaryCorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.corpus = Path(self.tmp.name) / "corpus"
        shutil.copytree(CORPUS, self.corpus)

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
        self.assertEqual(len(document["stories"]), 44 - 2)

    def test_carried_record_stays_live(self) -> None:
        doc = self.tombstones()
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] != FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        record = json.loads((FIXTURES / "corpus-carried.example.jsonl").read_text().splitlines()[0])
        (self.corpus / "carried.jsonl").write_text(json.dumps(record) + "\n")
        document, stderr = build(self.corpus)
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
        self.assertEqual(sum(s["status"] == "live" for s in document["stories"]), 41)

    @unittest.skipUnless(FULL_HISTORY, "needs the full git history")
    def test_ledger_from_history_equals_the_contract_fixture(self) -> None:
        (self.corpus / "first-published.json").unlink()
        doc = self.tombstones()
        doc["tombstones"] = [e for e in doc["tombstones"] if e["id"] == FDBE]
        (self.corpus / "tombstones.json").write_text(json.dumps(doc))
        ledger, tombstones, changes = story_layer.update_ledger(self.corpus, REPO, REPO / "site", NOW)
        self.assertEqual(ledger, json.loads((FIXTURES / "first-published.json").read_text()))
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


class TaxonomyTests(unittest.TestCase):
    def test_every_corpus_record_normalizes_to_record_v3(self) -> None:
        validator = validator_for(CONTRACTS / "record.v3.schema.json")
        for source in (CORPUS / "data" / "developments.jsonl", FIXTURES / "corpus-44" / "data" / "developments.jsonl"):
            records, quarantined = taxonomy.normalize_rows(taxonomy.read_jsonl(source))
            self.assertEqual(quarantined, [])
            for record in records:
                self.assertEqual(validator.errors(record), [], record["id"])

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
        good = taxonomy.read_jsonl(CORPUS / "data" / "developments.jsonl")[:3]
        bad = [dict(good[0], id="FCMO-000000000BAD", confidence="vibes"), "not a row",
               {"id": "nope"}]
        records, quarantined = taxonomy.normalize_rows(good + bad + [good[0]])
        self.assertEqual(len(records), 3)
        self.assertEqual(quarantined[0], ("FCMO-000000000BAD", ["CONFIDENCE_UNKNOWN"]))
        self.assertEqual([codes for _, codes in quarantined[1:]], [["NOT_AN_OBJECT"], ["ID_INVALID"], ["DUPLICATE_ID"]])


if __name__ == "__main__":
    unittest.main()
