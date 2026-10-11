import unittest

from tools.unittest_shards import discovered_test_ids, partition_test_ids


class UnittestShardCoverageTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
