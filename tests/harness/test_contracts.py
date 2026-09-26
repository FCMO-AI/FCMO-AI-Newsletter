"""Contract tests: schemas, fixtures, the wire state machine and the corpus guard."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from harness import oracles
from harness.clock import FakeClock, cdmx_date, format_utc
from harness.validate import (
    CONTRACTS,
    FIXTURES,
    MANIFEST,
    REPO,
    SchemaError,
    Validator,
    check_all_schemas,
    run_manifest,
    validate_file,
    validator_for,
)

REFERENCE_NOW = "2026-09-26T20:00:00Z"
PROSE_KEYS = (
    "title", "summary", "why_it_matters", "why", "importance_rationale", "limitations",
    "contradictory_evidence", "claims", "evidence_gaps", "relationships", "technical",
)


def load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def manifest_entries():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["fixtures"]


class SchemaStatusTests(unittest.TestCase):
    def test_every_schema_passes_the_meta_check(self):
        self.assertEqual(check_all_schemas(stream=io.StringIO()), 0)

    def test_status_tags(self):
        expected = {
            "stories.v2.schema.json": "v2-draft",
            "locale-overlay.v2.schema.json": "v2-draft",
            "airlock.v2.schema.json": "observed",
            "record.v2.schema.json": "observed",
        }
        schemas = sorted(CONTRACTS.glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 13)
        for path in schemas:
            doc = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(schema=path.name):
                self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(doc["x-contract"]["status"], expected.get(path.name, "v2-frozen"))
        for required in ("wire-status", "newsroom-status.v2", "stories.v2", "locale-overlay.v2", "health-state", "record.v3"):
            self.assertTrue((CONTRACTS / f"{required}.schema.json").is_file(), required)
        self.assertEqual(json.loads((CONTRACTS / "thresholds.json").read_text())["x-contract-status"], "v2-frozen")

    def test_frozen_schemas_are_closed(self):
        for path in CONTRACTS.glob("*.schema.json"):
            doc = json.loads(path.read_text(encoding="utf-8"))
            if doc["x-contract"]["status"] == "observed":
                continue
            with self.subTest(schema=path.name):
                if doc.get("type") == "object":
                    self.assertIs(doc.get("additionalProperties"), False)


class FixtureManifestTests(unittest.TestCase):
    def test_all_fixtures(self):
        out = io.StringIO()
        code = run_manifest(stream=out)
        self.assertEqual(code, 0, out.getvalue())
        match = re.search(r"fixtures OK \((\d+)\)", out.getvalue())
        self.assertIsNotNone(match)
        self.assertGreaterEqual(int(match.group(1)), 12)

    def test_required_fixtures_exist(self):
        names = {e["name"] for e in manifest_entries()}
        for name in (
            "corpus-43", "corpus-44", "wire-status.fresh", "wire-status.quiet", "wire-status.delayed",
            "wire-status.down", "stories.v2", "newsroom-status.fresh", "newsroom-status.quiet",
            "newsroom-status.delayed", "health-state.green", "health-state.red", "tombstones",
        ):
            self.assertIn(name, names)

    def test_invalid_fixtures_name_their_error(self):
        invalid = [e for e in manifest_entries() if e.get("expect") == "invalid"]
        self.assertGreaterEqual(len(invalid), 8)
        for entry in invalid:
            with self.subTest(fixture=entry["name"]):
                self.assertTrue(entry.get("expect_error"))
                errors = validate_file(REPO / entry["schema"], REPO / entry["path"])
                self.assertTrue(any(entry["expect_error"] in e for e in errors), errors)

    def test_manifest_flags_unlisted_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "MANIFEST.json"
            manifest.write_text(json.dumps({"fixtures": manifest_entries()[:1]}), encoding="utf-8")
            out = io.StringIO()
            self.assertEqual(run_manifest(manifest, stream=out), 1)
            self.assertIn("unmanaged fixture", out.getvalue())

    def test_corpus_fixtures_match_known_history(self):
        ids = {n: {r["id"] for r in oracles.read_records(FIXTURES / n)} for n in ("corpus-27", "corpus-43", "corpus-44")}
        self.assertEqual((len(ids["corpus-27"]), len(ids["corpus-43"]), len(ids["corpus-44"])), (27, 43, 44))
        self.assertEqual(ids["corpus-44"] - ids["corpus-43"], {"FCMO-FDBE3D996243"})
        self.assertLessEqual(ids["corpus-27"], ids["corpus-43"])
        self.assertEqual(len(ids["corpus-43"] - ids["corpus-27"]), 16)

    def test_no_private_or_credential_material(self):
        mailbox = re.compile(r"\b[A-Z0-9._%+-]+@(?:gmail|outlook|hotmail|protonmail)\.[A-Z]{2,}\b", re.I)
        secrets = (
            re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
            re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            re.compile(r"/(?:srv|home)/[a-z]"),
        )
        roots = [CONTRACTS, REPO / "config", REPO / "tests" / "harness"]
        for root in roots:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in {".json", ".jsonl", ".md", ".py", ".mjs"}:
                    continue
                text = path.read_text(encoding="utf-8")
                with self.subTest(path=str(path.relative_to(REPO))):
                    self.assertIsNone(mailbox.search(text))
                    for pattern in secrets:
                        self.assertIsNone(pattern.search(text), pattern.pattern)


class WireStateTests(unittest.TestCase):
    def classify(self, wire, now):
        return oracles.classify_wire(wire, now)

    def test_fixture_states_at_reference_time(self):
        entries = [e for e in manifest_entries() if "expect_state" in e]
        self.assertEqual(len(entries), 4)
        for entry in entries:
            wire = json.loads((REPO / entry["path"]).read_text(encoding="utf-8"))
            with self.subTest(fixture=entry["name"]):
                self.assertEqual(self.classify(wire, entry["evaluate_at"])[0], entry["expect_state"])
                # the bridge's own state is the classification at run time
                self.assertEqual(self.classify(wire, wire["run_at"])[0], wire["state"])

    def test_readme_boundaries(self):
        quiet, fresh = load("wire-status.quiet.json"), load("wire-status.fresh.json")
        cases = [
            (quiet, REFERENCE_NOW, ("QUIET", None)),
            (quiet, "2026-09-27T11:32:15Z", ("QUIET", None)),
            (quiet, "2026-09-27T11:32:16Z", ("DELAYED:STORY_SUPPLY", "STORY_SUPPLY")),
            (quiet, "2026-09-28T01:52:00Z", ("DELAYED:STORY_SUPPLY", "STORY_SUPPLY")),
            (quiet, "2026-09-28T01:52:01Z", ("TRANSPORT_DOWN", "WIRE_STALE")),
            (quiet, "2026-09-26T19:37:00Z", ("QUIET", None)),
            (quiet, "2026-09-26T19:36:59Z", ("TRANSPORT_DOWN", "CLOCK_SKEW")),
            (fresh, "2026-09-27T19:10:00Z", ("FRESH", None)),
            (fresh, "2026-09-27T19:10:01Z", ("QUIET", None)),
            (load("wire-status.delayed.json"), REFERENCE_NOW, ("DELAYED:ARB_MAIN_RED", "ARB_MAIN_RED")),
            (load("wire-status.down.json"), REFERENCE_NOW, ("TRANSPORT_DOWN", "WIRE_STALE")),
        ]
        for wire, now, expected in cases:
            with self.subTest(now=now, run_at=wire["run_at"]):
                self.assertEqual(self.classify(wire, now), expected)

    def test_transport_fail_grace(self):
        wire = load("wire-status.quiet.json")
        wire.update(transport="FAIL", transport_error="CLONE_FAILED", last_transport_ok_at="2026-09-26T14:00:00Z")
        self.assertEqual(validator_for(CONTRACTS / "wire-status.schema.json").errors(wire), [])
        self.assertEqual(self.classify(wire, "2026-09-26T20:00:00Z"), ("QUIET", None))
        self.assertEqual(self.classify(wire, "2026-09-26T20:00:01Z"), ("DELAYED:TRANSPORT_FAIL", "TRANSPORT_FAIL"))
        wire["last_transport_ok_at"] = None
        self.assertEqual(self.classify(wire, REFERENCE_NOW)[0], "DELAYED:TRANSPORT_FAIL")

    def test_missing_invalid_and_refused(self):
        self.assertEqual(self.classify(None, REFERENCE_NOW), ("TRANSPORT_DOWN", "WIRE_STATUS_MISSING"))
        broken = load("wire-status.quiet.json")
        broken["state"] = "TRANSPORT_DOWN"
        self.assertEqual(self.classify(broken, REFERENCE_NOW), ("TRANSPORT_DOWN", "WIRE_STATUS_INVALID"))
        refused = load("wire-status.quiet.json")
        refused["guard"] = {"verdict": "REGRESSION_REFUSED", "missing": [], "withdrawn": [], "added": 0, "ratio": 0.3721}
        self.assertEqual(self.classify(refused, REFERENCE_NOW)[0], "DELAYED:SNAPSHOT_REFUSED")

    def test_quiet_grid_with_fresh_wire(self):
        clock = FakeClock()
        base = load("wire-status.quiet.json")
        for hours in (25, 31, 37, 49, 80.5, 96):
            wire = copy.deepcopy(base)
            wire["run_at"] = wire["last_transport_ok_at"] = clock.ago(minutes=10)
            wire["last_new_story_at"] = wire["last_release_change_at"] = clock.ago(hours=hours)
            with self.subTest(hours=hours):
                state, _ = self.classify(wire, clock.iso())
                self.assertEqual(state, "QUIET")
                self.assertEqual(oracles.freshness_exit_code(state), 0)
        for hours in (31, 37, 49):
            wire = copy.deepcopy(base)
            wire["run_at"] = wire["last_transport_ok_at"] = clock.ago(hours=hours)
            with self.subTest(wire_age=hours):
                state, _ = self.classify(wire, clock.iso())
                self.assertEqual(state, "TRANSPORT_DOWN")
                self.assertEqual(oracles.freshness_exit_code(state), 1)

    def test_root_cause_wins(self):
        wire = load("wire-status.delayed.json")
        wire["last_new_story_at"] = "2026-09-26T19:00:00Z"  # checkpoint has something recent: still not FRESH
        self.assertEqual(self.classify(wire, REFERENCE_NOW)[0], "DELAYED:ARB_MAIN_RED")
        wire.update(arb_main="GREEN", arb_main_failures=[])
        self.assertEqual(self.classify(wire, REFERENCE_NOW)[0], "DELAYED:CHECKPOINT_STALE")


class NewsroomStatusTests(unittest.TestCase):
    def test_status_fixtures_follow_their_wire(self):
        entries = [e for e in manifest_entries() if "wire_fixture" in e]
        self.assertEqual(len(entries), 4)
        for entry in entries:
            status = json.loads((REPO / entry["path"]).read_text(encoding="utf-8"))
            wire = load(entry["wire_fixture"] + ".json")
            state, reason = oracles.classify_wire(wire, status["status_updated_at"])
            with self.subTest(fixture=entry["name"]):
                self.assertEqual(status["wire_state"], state)
                self.assertEqual((status["edition_state"], status["edition_reason"]), oracles.edition_fields(state, reason))
                self.assertEqual(status["wire_run_at"], wire["run_at"])
                self.assertEqual(status["edition_date"], cdmx_date(status["status_updated_at"]))
                self.assertEqual(status["last_edition_at"], wire["last_release_change_at"])
                self.assertEqual(status["quiet_since"], wire["last_new_story_at"] if state == "QUIET" else None)
                self.assertEqual(status["release_id"], wire["release_id"])


class HealthStateTests(unittest.TestCase):
    def test_overall_rule(self):
        for name in ("health-state.green.json", "health-state.red.json"):
            doc = load(name)
            required_bad = [k for k, s in doc["signals"].items() if s["required"] and s["status"] != "GREEN"]
            with self.subTest(fixture=name):
                self.assertEqual(doc["overall"], "RED" if required_bad else "GREEN")
                if required_bad:
                    keys = {a["key"] for a in doc["open_alerts"]}
                    self.assertLessEqual(set(required_bad) | {"overall"}, keys)

    def test_informational_signal_never_turns_overall_red(self):
        doc = load("health-state.green.json")
        doc["signals"]["translation"].update(status="RED", code="BACKLOG")
        self.assertEqual(validator_for(CONTRACTS / "health-state.schema.json").errors(doc), [])
        doc["signals"]["serving"].update(status="UNKNOWN", code="UNKNOWN")
        errors = validator_for(CONTRACTS / "health-state.schema.json").errors(doc)
        self.assertTrue(any("/overall" in e for e in errors), errors)


class CorpusGuardTests(unittest.TestCase):
    def test_reports_match_oracle(self):
        tombstones = load("tombstones.json")
        for entry in (e for e in manifest_entries() if "guard" in e):
            spec = entry["guard"]
            result = oracles.guard_corpora(
                FIXTURES / spec["published"], FIXTURES / spec["candidate"],
                tombstones if spec["tombstones"] else None,
            )
            with self.subTest(fixture=entry["name"]):
                self.assertEqual(result["verdict"], spec["expect_verdict"])
                self.assertEqual(result["exit_code"], spec["expect_exit"])
                self.assertEqual(oracles.guard_report(result, spec["checked_at"]),
                                 json.loads((REPO / entry["path"]).read_text(encoding="utf-8")))

    def test_first_lines_from_readme(self):
        tomb = load("tombstones.json")
        line = lambda p, c, t=None: oracles.guard_line(oracles.guard_corpora(FIXTURES / p, FIXTURES / c, t))  # noqa: E731
        self.assertEqual(line("corpus-44", "corpus-43"),
                         "CARRY_FORWARD missing=FCMO-FDBE3D996243 withdrawn=- added=0 published=44 candidate=43 ratio=0.0227")
        self.assertEqual(line("corpus-44", "corpus-43", tomb),
                         "OK missing=- withdrawn=FCMO-FDBE3D996243 added=0 published=44 candidate=43 ratio=0.0000")
        self.assertEqual(line("corpus-43", "corpus-44"),
                         "OK missing=- withdrawn=- added=1 published=43 candidate=44 ratio=0.0000")
        refused = line("corpus-43", "corpus-27")
        self.assertTrue(refused.startswith("REGRESSION_REFUSED missing=FCMO-"), refused)
        self.assertTrue(refused.endswith("withdrawn=- added=0 published=43 candidate=27 ratio=0.3721"), refused)
        readme = (CONTRACTS / "README.md").read_text(encoding="utf-8")
        self.assertIn("CARRY_FORWARD missing=FCMO-FDBE3D996243 withdrawn=- added=0 published=44 candidate=43 ratio=0.0227", readme)

    def test_ratio_boundary(self):
        live = [f"FCMO-{i:012X}" for i in range(10)]
        at_limit = oracles.guard_verdict(live, live[2:])  # 2/10 = 0.2, not above
        self.assertEqual((at_limit["verdict"], at_limit["exit_code"], at_limit["carried"]), ("CARRY_FORWARD", 0, live[:2]))
        above = oracles.guard_verdict(live, live[3:])
        self.assertEqual((above["verdict"], above["exit_code"], above["carried"]), ("REGRESSION_REFUSED", 3, []))
        self.assertEqual(oracles.guard_verdict([], [])["verdict"], "OK")

    def test_withdrawals_and_suppression(self):
        live = ["FCMO-000000000001", "FCMO-000000000002", "FCMO-000000000003"]
        upstream = oracles.guard_verdict(live, live, upstream_withdrawn=["FCMO-000000000002"])
        self.assertEqual(upstream["verdict"], "OK")
        self.assertEqual(upstream["withdrawn"], [{"id": "FCMO-000000000002", "source": "upstream"}])
        both = oracles.guard_verdict(live, live[:2], tombstoned=["FCMO-000000000003", "FCMO-00000000000A"],
                                     upstream_withdrawn=[])
        self.assertEqual(both["missing"], [])
        self.assertEqual(both["withdrawn"], [{"id": "FCMO-000000000003", "source": "tombstone"}])
        back = oracles.guard_verdict(live, live + ["FCMO-00000000000A"], tombstoned=["FCMO-00000000000A"])
        self.assertEqual((back["added"], back["suppressed"]), ([], ["FCMO-00000000000A"]))

    def test_reinstated_tombstone_is_inactive(self):
        doc = load("tombstones.json")
        self.assertEqual(oracles.active_tombstones(doc), {"FCMO-FDBE3D996243"})
        doc["tombstones"][0]["reinstated_at"] = "2026-09-27T00:00:00Z"
        self.assertEqual(validator_for(CONTRACTS / "tombstones.schema.json").errors(doc), [])
        self.assertEqual(oracles.active_tombstones(doc), set())

    def test_carried_ids_stay_live(self):
        with tempfile.TemporaryDirectory() as tmp:
            pub = Path(tmp) / "pub"
            (pub / "data").mkdir(parents=True)
            rows = oracles.read_records(FIXTURES / "corpus-43")
            (pub / "data" / "developments.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            (pub / "carried.jsonl").write_text(
                (FIXTURES / "corpus-carried.example.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
            result = oracles.guard_corpora(pub, FIXTURES / "corpus-43")
            self.assertEqual((result["verdict"], result["missing"]), ("CARRY_FORWARD", ["FCMO-FDBE3D996243"]))
            self.assertEqual(result["live_count"], 44)


class StoryLayerFixtureTests(unittest.TestCase):
    def test_first_publication_ledger(self):
        ledger = load("first-published.json")["entries"]
        self.assertEqual(len(ledger), 44)
        fad9 = ledger["FCMO-FAD9D0AFD3E4"]
        self.assertEqual(fad9["first_published_at"], "2026-09-14T02:48:13Z")
        self.assertEqual(fad9["url_date"], "2026-09-13")
        for rid, entry in ledger.items():
            self.assertEqual(entry["url_date"], cdmx_date(entry["first_published_at"]), rid)

    def test_stories_fixture_invariants(self):
        doc = load("stories.v2.json")
        stories = {s["id"]: s for s in doc["stories"]}
        ledger = load("first-published.json")["entries"]
        live = {k for k, s in stories.items() if s["status"] == "live"}
        self.assertGreaterEqual(sum(s["front_page_eligible"] for s in stories.values()), 5)
        for sid, story in stories.items():
            with self.subTest(story=sid):
                self.assertEqual(story["first_published_at"], ledger[sid]["first_published_at"])
                self.assertEqual(story["url_date"], ledger[sid]["url_date"])
                if story["status"] == "merged":
                    self.assertIn(story["merged_into"], live)
                    self.assertEqual(ledger[sid].get("redirect_to"), story["merged_into"])
                for locale, pair in story["l10n"].items():
                    if pair["state"] in {"PENDING", "FAILED"}:
                        self.assertTrue(pair["missing"], f"{locale} pending without missing fields")
        withdrawn = stories["FCMO-FDBE3D996243"]
        tomb = load("tombstones.json")["tombstones"][0]
        self.assertEqual(withdrawn["status"], "withdrawn")
        self.assertEqual(withdrawn["corrections"][0]["text"], tomb["correction"])

    def test_overlay_source_hash(self):
        overlay = load("locale-overlay.v2.es-419.json")["records"]
        records = {r["id"]: r for r in oracles.read_records(FIXTURES / "corpus-44")}
        for rid, entry in overlay.items():
            prose = {k: records[rid][k] for k in sorted(PROSE_KEYS) if k in records[rid]}
            raw = json.dumps(prose, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            with self.subTest(record=rid):
                self.assertEqual(entry["source_sha256"], hashlib.sha256(raw.encode("utf-8")).hexdigest())

    def test_site_config(self):
        site = json.loads((REPO / "config" / "site.json").read_text(encoding="utf-8"))
        self.assertTrue(site["base_url"].endswith(site["base_path"]))
        self.assertEqual(site["base_path"], "/FCMO-AI-Newsletter/")


class ValidatorTests(unittest.TestCase):
    def v(self, schema):
        return Validator({"$schema": "https://json-schema.org/draft/2020-12/schema", **schema})

    def test_unknown_keyword_is_a_schema_error(self):
        with self.assertRaises(SchemaError):
            self.v({"type": "object", "additionalProprties": False})

    def test_formats_are_assertions(self):
        v = self.v({"type": "string", "format": "date-time"})
        self.assertEqual(v.errors("2026-09-26T20:00:00Z"), [])
        self.assertTrue(v.errors("2026-13-01T00:00:00Z"))
        self.assertTrue(v.errors("yesterday"))
        self.assertTrue(self.v({"format": "date", "type": "string"}).errors("2026-02-30"))
        self.assertTrue(self.v({"format": "uri", "type": "string"}).errors("not a url"))

    def test_closed_objects_refs_and_unique_by(self):
        v = self.v({
            "type": "object", "additionalProperties": False, "required": ["items"],
            "properties": {"items": {"type": "array", "x-unique-by": "id", "items": {"$ref": "#/$defs/item"}}},
            "$defs": {"item": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
        })
        self.assertEqual(v.errors({"items": [{"id": "a"}, {"id": "b"}]}), [])
        self.assertTrue(any("duplicate id" in e for e in v.errors({"items": [{"id": "a"}, {"id": "a"}]})))
        self.assertTrue(any("not allowed" in e for e in v.errors({"items": [], "extra": 1})))
        self.assertTrue(any("missing required" in e for e in v.errors({"items": [{}]})))

    def test_conditionals_and_combinators(self):
        v = self.v({
            "type": "object",
            "properties": {"state": {"enum": ["A", "B"]}, "reason": {"type": ["string", "null"]}},
            "if": {"properties": {"state": {"const": "B"}}},
            "then": {"properties": {"reason": {"type": "string"}}},
            "else": {"properties": {"reason": {"type": "null"}}},
        })
        self.assertEqual(v.errors({"state": "A", "reason": None}), [])
        self.assertTrue(v.errors({"state": "B", "reason": None}))
        self.assertTrue(v.errors({"state": "A", "reason": "x"}))
        one = self.v({"oneOf": [{"type": "integer"}, {"type": "number", "minimum": 0}]})
        self.assertTrue(one.errors(3))  # matches both branches
        self.assertEqual(one.errors(-1), [])
        self.assertTrue(self.v({"type": "integer"}).errors(True))  # booleans are not integers

    def test_jsonl_errors_are_labelled_by_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "s.schema.json"
            schema.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                          "type": "object", "required": ["id"]}), encoding="utf-8")
            data = Path(tmp) / "d.jsonl"
            data.write_text('{"id": 1}\n{}\n', encoding="utf-8")
            errors = validate_file(schema, data)
            self.assertEqual(len(errors), 1)
            self.assertIn(":2#", errors[0])

    def test_timestamp_helpers(self):
        self.assertEqual(format_utc("2026-09-14T02:48:13.997038+00:00"), "2026-09-14T02:48:13Z")
        self.assertEqual(cdmx_date("2026-09-14T02:48:13Z"), "2026-09-13")


if __name__ == "__main__":
    unittest.main()
