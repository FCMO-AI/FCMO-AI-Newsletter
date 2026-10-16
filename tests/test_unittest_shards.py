"""The deploy regression gate is sharded, complete, and cannot starve Pages.

Regression (2026-10-11 .. 10-14): the Deploy workflow ran the whole suite
serially (43 min on 10-11, 129 min on 10-14) under ``cancel-in-progress: true``
while refreshes arrived every 30-60 min, so every candidate was cancelled
before deploy.  These tests pin the two halves of the fix: the suite runs as
complete parallel shards that the build needs, and automatic runs queue on the
single Pages lease instead of cancelling the candidate in flight.
"""
from __future__ import annotations

import contextlib
import io
import json
import random
import unittest
from pathlib import Path

import yaml

from tools import unittest_shards

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / ".github/workflows/pages.yml"


def ids(spec: dict[str, int]) -> list[str]:
    return [f"test_mod.{cls}.test_{n}" for cls, count in spec.items() for n in range(count)]


class PartitionTests(unittest.TestCase):
    def test_every_test_lands_in_exactly_one_shard(self) -> None:
        test_ids = ids({"A": 40, "B": 3, "C": 17, "D": 1, "E": 9, "F": 22, "G": 5})
        for count in range(1, 8):
            with self.subTest(count=count):
                shards = unittest_shards.partition_test_ids(test_ids, count)
                self.assertEqual(len(shards), count)
                flat = [test_id for shard in shards for test_id in shard]
                self.assertCountEqual(flat, test_ids)

    def test_a_class_is_never_split(self) -> None:
        test_ids = ids({"A": 40, "B": 3, "C": 17, "D": 1, "E": 9})
        shards = unittest_shards.partition_test_ids(test_ids, 3)
        owners: dict[str, set[int]] = {}
        for index, shard in enumerate(shards):
            for test_id in shard:
                owners.setdefault(unittest_shards.group_key(test_id), set()).add(index)
        self.assertTrue(all(len(found) == 1 for found in owners.values()), owners)

    def test_partition_ignores_discovery_order_and_keeps_it_inside_a_shard(self) -> None:
        test_ids = ids({"A": 4, "B": 6, "C": 2, "D": 5, "E": 3})
        shuffled = list(test_ids)
        random.Random(7).shuffle(shuffled)
        left = unittest_shards.partition_test_ids(test_ids, 3)
        right = unittest_shards.partition_test_ids(shuffled, 3)
        self.assertEqual([sorted(shard) for shard in left], [sorted(shard) for shard in right])
        for shard in right:
            self.assertEqual(shard, [test_id for test_id in shuffled if test_id in set(shard)])

    def test_largest_first_balances_by_test_count(self) -> None:
        shards = unittest_shards.partition_test_ids(ids({"A": 10, "B": 6, "C": 5, "D": 4, "E": 3}), 2)
        self.assertEqual(sorted(len(shard) for shard in shards), [14, 14])

    def test_measured_weights_balance_by_seconds_without_changing_coverage(self) -> None:
        test_ids = ids({"Slow": 2, "A": 10, "B": 10, "C": 10})
        shards = unittest_shards.partition_test_ids(test_ids, 2, {"test_mod.Slow": 600.0})
        self.assertCountEqual([test_id for shard in shards for test_id in shard], test_ids)
        slow = next(shard for shard in shards if "test_mod.Slow.test_0" in shard)
        self.assertEqual({unittest_shards.group_key(test_id) for test_id in slow}, {"test_mod.Slow"})

    def test_committed_weights_are_valid_and_optional(self) -> None:
        weights = unittest_shards.load_weights(unittest_shards.WEIGHTS)
        self.assertTrue(weights, "the measured weights file is missing or empty")
        self.assertTrue(all(seconds > 0 for seconds in weights.values()))
        self.assertEqual(unittest_shards.load_weights(ROOT / "does-not-exist.json"), {})

    def test_invalid_partitions_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            unittest_shards.partition_test_ids(ids({"A": 2}), 0)
        with self.assertRaises(ValueError):
            unittest_shards.partition_test_ids(ids({"A": 2}), 2)  # an empty shard would pass vacuously
        with self.assertRaises(ValueError):
            unittest_shards.partition_test_ids(["m.A.t", "m.A.t", "m.B.t"], 2)
        with self.assertRaises(ValueError):
            unittest_shards.assert_complete(["m.A.t", "m.B.t"], [["m.A.t"], []])

    def test_repository_suite_is_fully_covered_by_the_deploy_shard_count(self) -> None:
        count = len(yaml.safe_load(PAGES.read_text())["jobs"]["regression"]["strategy"]["matrix"]["shard"])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(unittest_shards.main(["--count", str(count), "--list"]), 0)
        listing = json.loads(out.getvalue())
        self.assertEqual(sum(listing["shards"]), listing["tests"])
        self.assertTrue(all(size > 0 for size in listing["shards"]))
        self.assertGreater(listing["tests"], 500, "discovery lost most of the suite")


class PagesCadenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PAGES.read_text(encoding="utf-8")
        cls.workflow = yaml.safe_load(cls.text)

    def test_automatic_runs_queue_and_only_manual_main_dispatch_preempts(self) -> None:
        concurrency = self.workflow["concurrency"]
        self.assertEqual(concurrency["cancel-in-progress"], "${{ github.event_name == 'workflow_dispatch' }}")
        # One shared lease for every run that can write Pages.
        self.assertIn("|| 'active' }}", concurrency["group"])
        self.assertIn("github.event_name == 'workflow_dispatch' && github.ref != 'refs/heads/main'",
                      concurrency["group"])

    def test_build_needs_every_shard_and_no_longer_runs_the_suite_serially(self) -> None:
        jobs = self.workflow["jobs"]
        self.assertEqual(jobs["build"]["needs"], "regression")
        shards = jobs["regression"]["strategy"]["matrix"]["shard"]
        self.assertEqual(shards, list(range(len(shards))))
        run = jobs["regression"]["steps"][-1]["run"]
        self.assertEqual(run, f"python3 tools/unittest_shards.py --index ${{{{ matrix.shard }}}} --count {len(shards)}")
        self.assertIs(jobs["regression"]["strategy"]["fail-fast"], False)
        self.assertNotIn("continue-on-error", json.dumps(jobs["regression"]))
        build_runs = [step.get("run", "") for step in jobs["build"]["steps"]]
        self.assertFalse(any("unittest discover" in run for run in build_runs))

    def test_shards_get_the_serial_suite_environment_and_no_write_access(self) -> None:
        regression = self.workflow["jobs"]["regression"]
        runs = "\n".join(step.get("run", "") for step in regression["steps"])
        for needle in ("playwright@1.63.0 axe-core@4.14.0", "PLAYWRIGHT_MODULE=", "AXE_CORE_PATH=",
                       "PyYAML==6.0.2", "apt-get install -y age"):
            self.assertIn(needle, runs)
        checkout = regression["steps"][0]
        self.assertEqual(checkout["with"]["fetch-depth"], 0)
        self.assertFalse(checkout["with"]["persist-credentials"])
        self.assertEqual(regression["permissions"], {"contents": "read"})
        self.assertNotIn("environment", regression)

    def test_branch_dispatch_can_run_shards_but_never_build_or_deploy(self) -> None:
        jobs = self.workflow["jobs"]
        self.assertNotIn("refs/heads/main", jobs["regression"]["if"])
        self.assertIn("inputs.operation == 'deploy' && github.ref == 'refs/heads/main'", jobs["build"]["if"])
        self.assertEqual(jobs["deploy"]["needs"], "build")


if __name__ == "__main__":
    unittest.main()
