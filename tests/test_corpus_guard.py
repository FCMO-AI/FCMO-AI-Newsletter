"""Tests for tools/corpus_guard.py against contracts/README.md and the harness oracle."""
from __future__ import annotations

import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.harness import oracles
from tests.harness.validate import validator_for
from tools import corpus_guard

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "contracts" / "fixtures"
TOOL = REPO / "tools" / "corpus_guard.py"
NOW = "2026-09-26T20:00:00Z"
FDBE = "FCMO-FDBE3D996243"

# contracts/README.md, "Examples (real corpus history, see fixtures)".
EXAMPLES = (
    ("corpus-44", "corpus-43", None, "corpus-guard.carry-forward.json", 0,
     "CARRY_FORWARD missing=FCMO-FDBE3D996243 withdrawn=- added=0 published=44 candidate=43 ratio=0.0227"),
    ("corpus-44", "corpus-43", "tombstones.json", "corpus-guard.withdrawn.json", 0,
     "OK missing=- withdrawn=FCMO-FDBE3D996243 added=0 published=44 candidate=43 ratio=0.0000"),
    ("corpus-43", "corpus-27", None, "corpus-guard.refused.json", 3, None),
    ("corpus-43", "corpus-44", None, "corpus-guard.added.json", 0,
     "OK missing=- withdrawn=- added=1 published=43 candidate=44 ratio=0.0000"),
)


def run_tool(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, cwd=REPO)


def ids_of(corpus: Path) -> list[str]:
    return [json.loads(l)["id"] for l in (corpus / "data" / "developments.jsonl").read_text().splitlines() if l.strip()]


class GuardExamplesTests(unittest.TestCase):
    def test_readme_examples_first_line_exit_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for pub, cand, tomb, expected_report, code, line in EXAMPLES:
                with self.subTest(pub=pub, cand=cand, tomb=tomb):
                    out = Path(tmp) / expected_report
                    args = ["check", "--published", str(FIXTURES / pub), "--candidate", str(FIXTURES / cand),
                            "--now", NOW, "--report", str(out)]
                    if tomb:
                        args += ["--tombstones", str(FIXTURES / tomb)]
                    proc = run_tool(*args)
                    self.assertEqual(proc.returncode, code, proc.stderr)
                    first = proc.stdout.splitlines()[0]
                    if line:
                        self.assertEqual(first, line)
                    else:
                        self.assertTrue(first.startswith("REGRESSION_REFUSED missing="))
                        self.assertTrue(first.endswith("withdrawn=- added=0 published=43 candidate=27 ratio=0.3721"))
                        self.assertEqual(len(first.split(" ")[1].split("=")[1].split(",")), 16)
                    self.assertEqual(json.loads(out.read_text()), json.loads((FIXTURES / expected_report).read_text()))
                    self.assertNotIn(str(FIXTURES), out.read_text(), "the report never holds paths")

    def test_alerts_go_to_stderr(self) -> None:
        proc = run_tool("check", "--published", str(FIXTURES / "corpus-44"), "--candidate", str(FIXTURES / "corpus-43"))
        self.assertEqual(proc.stderr.strip(), f"ALERT CORPUS_CARRY_FORWARD missing={FDBE}")
        proc = run_tool("check", "--published", str(FIXTURES / "corpus-43"), "--candidate", str(FIXTURES / "corpus-27"))
        self.assertEqual(proc.stderr.strip(), "ALERT CORPUS_REGRESSION_REFUSED missing=16 ratio=0.3721")

    def test_reports_validate_against_schema(self) -> None:
        validator = validator_for(REPO / "contracts" / "corpus-guard.report.schema.json")
        for pub, cand, tomb, _, _, _ in EXAMPLES:
            tombstones = corpus_guard.load_tombstones(FIXTURES / tomb) if tomb else None
            result = corpus_guard.check(FIXTURES / pub, FIXTURES / cand, tombstones)
            self.assertEqual(validator.errors(corpus_guard.report(result, NOW, 0.2)), [])

    def test_matches_oracle_on_fixture_corpora(self) -> None:
        tombstones = json.loads((FIXTURES / "tombstones.json").read_text())
        for pub, cand, tomb, _, _, _ in EXAMPLES:
            doc = tombstones if tomb else None
            ours = corpus_guard.check(FIXTURES / pub, FIXTURES / cand, doc)
            theirs = oracles.guard_corpora(FIXTURES / pub, FIXTURES / cand, doc)
            self.assertEqual(corpus_guard.report(ours, NOW, 0.2), oracles.guard_report(theirs, NOW, 0.2))
            self.assertEqual(corpus_guard.first_line(ours), oracles.guard_line(theirs))

    def test_verdict_matches_oracle_on_random_sets(self) -> None:
        rng = random.Random(20260926)
        universe = [f"FCMO-{i:012X}" for i in range(40)]
        for _ in range(400):
            live = set(rng.sample(universe, rng.randint(0, 30)))
            cand = set(rng.sample(universe, rng.randint(0, 30)))
            tomb = set(rng.sample(universe, rng.randint(0, 5)))
            up = set(rng.sample(sorted(cand), min(len(cand), rng.randint(0, 4)))) if cand else set()
            limit = rng.choice([0.0, 0.1, 0.2, 0.5, 1.0])
            self.assertEqual(corpus_guard.verdict(live, cand, tomb, up, limit),
                             oracles.guard_verdict(live, cand, tomb, up, limit))

    def test_ratio_boundary_is_strictly_greater(self) -> None:
        live = [f"FCMO-{i:012X}" for i in range(10)]
        at_limit = corpus_guard.verdict(live, live[2:], max_missing_ratio=0.2)
        self.assertEqual((at_limit["verdict"], at_limit["exit_code"]), ("CARRY_FORWARD", 0))
        over = corpus_guard.verdict(live, live[3:], max_missing_ratio=0.2)
        self.assertEqual((over["verdict"], over["exit_code"]), ("REGRESSION_REFUSED", 3))

    def test_upstream_withdrawal_is_not_missing(self) -> None:
        live = ["FCMO-000000000001", "FCMO-000000000002"]
        result = corpus_guard.verdict(live, live, upstream_withdrawn=[live[0]])
        self.assertEqual(result["verdict"], "OK")
        self.assertEqual(result["withdrawn"], [{"id": live[0], "source": "upstream"}])
        both = corpus_guard.verdict(live, live, tombstoned=[live[0]], upstream_withdrawn=[live[0]])
        self.assertEqual(both["withdrawn"], [{"id": live[0], "source": "tombstone"}], "tombstone wins")

    def test_tombstoned_new_id_is_suppressed_not_added(self) -> None:
        result = corpus_guard.verdict(["FCMO-000000000001"], ["FCMO-000000000001", "FCMO-000000000002"],
                                      tombstoned=["FCMO-000000000002"])
        self.assertEqual((result["added"], result["suppressed"]), ([], ["FCMO-000000000002"]))

    def test_max_missing_ratio_defaults_to_thresholds(self) -> None:
        self.assertEqual(corpus_guard.default_max_missing_ratio(), 0.2)
        proc = run_tool("check", "--published", str(FIXTURES / "corpus-43"), "--candidate", str(FIXTURES / "corpus-27"),
                        "--max-missing-ratio", "0.5")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith("CARRY_FORWARD "))


class _TmpCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def copy(self, name: str, dest: str | None = None) -> Path:
        target = self.root / (dest or name)
        shutil.copytree(FIXTURES / name, target)
        return target


class GuardInputTests(_TmpCase):
    def test_usage_errors_exit_2_and_write_nothing(self) -> None:
        pub = self.copy("corpus-44")
        broken = self.copy("corpus-43", "broken")
        with (broken / "data" / "developments.jsonl").open("a") as handle:
            handle.write("{not json\n")
        out = self.root / "out"
        cases = [
            ["check", "--published", str(self.root / "absent"), "--candidate", str(broken)],
            ["apply", "--published", str(pub), "--candidate", str(broken), "--out", str(out)],
            ["check", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-43"), "--now", "yesterday"],
            ["check", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-43"), "--max-missing-ratio", "2"],
            ["check", "--published", str(pub)],
        ]
        bad_tombs = self.root / "tombs.json"
        bad_tombs.write_text('{"schema": "other", "tombstones": []}')
        cases.append(["check", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-43"),
                      "--tombstones", str(bad_tombs)])
        for args in cases:
            with self.subTest(args=args[0:1] + args[-2:]):
                proc = run_tool(*args)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertEqual(proc.stdout, "")
        self.assertFalse(out.exists())

    def test_jsonl_files_are_accepted(self) -> None:
        proc = run_tool("check", "--published", str(FIXTURES / "corpus-44" / "data" / "developments.jsonl"),
                        "--candidate", str(FIXTURES / "corpus-43" / "data" / "developments.jsonl"))
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith("CARRY_FORWARD missing=FCMO-FDBE3D996243 "))

    def test_tombstones_default_to_published_directory(self) -> None:
        pub = self.copy("corpus-44")
        shutil.copy(FIXTURES / "tombstones.json", pub / "tombstones.json")
        proc = run_tool("check", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-43"))
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith("OK missing=- withdrawn=FCMO-FDBE3D996243 "))

    def test_reinstated_tombstone_is_inactive(self) -> None:
        doc = json.loads((FIXTURES / "tombstones.json").read_text())
        doc["tombstones"][0]["reinstated_at"] = NOW
        self.assertEqual(corpus_guard.active_tombstones(doc), set())
        result = corpus_guard.check(FIXTURES / "corpus-44", FIXTURES / "corpus-43", doc)
        self.assertEqual(result["verdict"], "CARRY_FORWARD")


class GuardApplyTests(_TmpCase):
    def carried(self, corpus: Path) -> list[dict]:
        path = corpus / "carried.jsonl"
        return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []

    def test_carry_forward_writes_candidate_and_carried_record(self) -> None:
        pub = self.copy("corpus-44", "published")
        (pub / "first-published.json").write_text('{"schema": "fcmo-first-published-v1", "entries": {}}\n')
        (pub / "wire-status.json").write_text("{}\n")
        out = self.root / "out"
        proc = run_tool("apply", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-43"),
                        "--out", str(out), "--now", NOW)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(ids_of(out), ids_of(FIXTURES / "corpus-43"))
        self.assertEqual((out / "airlock.json").read_bytes(), (FIXTURES / "corpus-43" / "airlock.json").read_bytes())
        lines = self.carried(out)
        self.assertEqual([l["id"] for l in lines], [FDBE])
        validator = validator_for(REPO / "contracts" / "corpus-carried.schema.json")
        self.assertEqual(validator.errors(lines[0]), [])
        self.assertEqual(lines[0]["carried_since"], NOW)
        self.assertEqual(lines[0]["last_release_id"], "newswire-925e1ca37c00649e54180549")
        published = {json.loads(l)["id"]: json.loads(l) for l in (pub / "data" / "developments.jsonl").read_text().splitlines()}
        self.assertEqual(lines[0]["record"], published[FDBE])
        # Newsroom files of the published corpus survive; the candidate's content wins elsewhere.
        self.assertTrue((out / "first-published.json").is_file())
        self.assertTrue((out / "wire-status.json").is_file())
        # The carried id counts as live for the next run.
        again = corpus_guard.check(out, FIXTURES / "corpus-43")
        self.assertEqual((again["live_count"], again["verdict"]), (44, "CARRY_FORWARD"))

    def test_carried_since_survives_and_reappearance_drops_the_line(self) -> None:
        pub = self.copy("corpus-44", "published")
        first = self.root / "first"
        corpus_guard.apply(pub, FIXTURES / "corpus-43", first, now=NOW)
        second = self.root / "second"
        corpus_guard.apply(first, FIXTURES / "corpus-43", second, now="2026-09-27T20:00:00Z")
        self.assertEqual([(l["id"], l["carried_since"]) for l in self.carried(second)], [(FDBE, NOW)])
        back = self.root / "back"
        result = corpus_guard.apply(second, FIXTURES / "corpus-44", back, now="2026-09-28T20:00:00Z")
        self.assertEqual(result["verdict"], "OK")
        self.assertFalse((back / "carried.jsonl").exists())
        self.assertIn(FDBE, ids_of(back))

    def test_tombstone_drops_the_carried_line(self) -> None:
        pub = self.copy("corpus-44", "published")
        first = self.root / "first"
        corpus_guard.apply(pub, FIXTURES / "corpus-43", first, now=NOW)
        shutil.copy(FIXTURES / "tombstones.json", first / "tombstones.json")
        proc = run_tool("apply", "--published", str(first), "--candidate", str(FIXTURES / "corpus-43"),
                        "--out", str(first), "--now", NOW)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("OK missing=- withdrawn=FCMO-FDBE3D996243 "))
        self.assertFalse((first / "carried.jsonl").exists())
        self.assertTrue((first / "tombstones.json").is_file(), "in-place apply keeps the tombstones")

    def test_refused_apply_writes_nothing(self) -> None:
        pub = self.copy("corpus-43", "published")
        before = {p.relative_to(pub): p.read_bytes() for p in pub.rglob("*") if p.is_file()}
        out = self.root / "out"
        for target in (out, pub):
            proc = run_tool("apply", "--published", str(pub), "--candidate", str(FIXTURES / "corpus-27"),
                            "--out", str(target), "--now", NOW)
            self.assertEqual(proc.returncode, 3)
            self.assertTrue(proc.stdout.startswith("REGRESSION_REFUSED "))
        self.assertFalse(out.exists())
        after = {p.relative_to(pub): p.read_bytes() for p in pub.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["published"], "no temp dirs left behind")

    def test_live_ids(self) -> None:
        pub = self.copy("corpus-44", "published")
        proc = run_tool("live-ids", str(pub))
        self.assertEqual(proc.stdout.split(), sorted(ids_of(pub)))
        shutil.copy(FIXTURES / "tombstones.json", pub / "tombstones.json")
        proc = run_tool("live-ids", str(pub), "--publishable")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn(FDBE, proc.stdout.split())
        self.assertEqual(len(proc.stdout.split()), 43)


class RepositoryTombstonesTests(unittest.TestCase):
    def test_corpus_tombstones_are_valid_and_withdraw_the_orphan(self) -> None:
        path = REPO / "corpus" / "tombstones.json"
        validator = validator_for(REPO / "contracts" / "tombstones.schema.json")
        document = json.loads(path.read_text())
        self.assertEqual(validator.errors(document), [])
        self.assertIn(FDBE, corpus_guard.active_tombstones(document))
        entry = next(e for e in document["tombstones"] if e["id"] == FDBE)
        self.assertEqual(entry["decided_by"], "operator")
        self.assertEqual(entry["reason_code"], "UNVERIFIED_RELEASE")
        self.assertEqual(set(entry["correction"]), {"en", "es-419", "zh-Hans"})

    def test_live_corpus_passes_the_guard_against_itself(self) -> None:
        corpus = REPO / "corpus"
        result = corpus_guard.check(corpus, corpus, corpus_guard.load_tombstones(corpus / "tombstones.json"))
        self.assertEqual(result["verdict"], "OK")


if __name__ == "__main__":
    unittest.main()
