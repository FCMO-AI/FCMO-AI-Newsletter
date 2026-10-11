import sys
import unittest
from importlib.machinery import PathFinder
from pathlib import Path
from unittest.mock import patch

from tools.unittest_shards import (
    discovered_test_ids,
    ensure_repository_root_on_path,
    partition_test_ids,
)


class UnittestShardCoverageTests(unittest.TestCase):
    def test_shard_runner_adds_repository_root_for_package_imports(self):
        root = Path(__file__).resolve().parents[1]
        with patch.object(sys, "path", [str(root / "tests")]):
            self.assertIsNone(PathFinder.find_spec("tools", sys.path))
            ensure_repository_root_on_path()
            self.assertEqual(Path(sys.path[0]), root)
            spec = PathFinder.find_spec("tools", sys.path)
            self.assertIsNotNone(spec)
            self.assertIn(root / "tools", {Path(item) for item in spec.submodule_search_locations})

    def test_discovered_suite_is_assigned_exactly_once(self):
        test_ids = discovered_test_ids()
        shards = partition_test_ids(test_ids, 4)
        assigned = [test_id for shard in shards for test_id in shard]
        self.assertEqual(len(assigned), len(test_ids))
        self.assertEqual(set(assigned), set(test_ids))
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_partition_is_stable_and_rejects_duplicate_ids(self):
        ids = ["suite.test_c", "suite.test_a", "suite.test_b"]
        self.assertEqual(partition_test_ids(ids, 2), partition_test_ids(list(reversed(ids)), 2))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            partition_test_ids(["suite.test_a", "suite.test_a"], 2)
        with self.assertRaisesRegex(ValueError, "at least one test per shard"):
            partition_test_ids(["suite.test_a"], 2)


    def test_release_gate_call_is_detected_by_input_not_event_name(self):
        # Inside a called workflow github.event_name is the caller's event, so a
        # condition on 'workflow_call' silently skips the shards (PR #80, first run).
        from pathlib import Path
        text = (Path(__file__).resolve().parents[1] / ".github/workflows/contract-tests.yml").read_text()
        self.assertNotIn("event_name == 'workflow_call'", text)
        self.assertNotIn("event_name != 'workflow_call'", text)
        self.assertIn("if: ${{ !inputs.source_commit }}", text)
        self.assertIn("if: ${{ inputs.source_commit != null && inputs.source_commit != '' }}", text)


if __name__ == "__main__":
    unittest.main()
