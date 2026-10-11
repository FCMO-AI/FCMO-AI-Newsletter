#!/usr/bin/env python3
"""Run the repository unittest suite in deterministic, complete shards."""
from __future__ import annotations

import argparse
import hashlib
import sys
import unittest


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def partition_test_ids(test_ids: list[str], shard_count: int) -> list[list[str]]:
    """Return stable, count-balanced shards; duplicate IDs are an error."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if len(test_ids) < shard_count:
        raise ValueError("discovery must find at least one test per shard")
    if len(test_ids) != len(set(test_ids)):
        raise ValueError("discovery returned duplicate unittest IDs")
    ordered = sorted(test_ids, key=lambda test_id: hashlib.sha256(test_id.encode("utf-8")).digest())
    shards = [[] for _ in range(shard_count)]
    for position, test_id in enumerate(ordered):
        shards[position % shard_count].append(test_id)
    return shards


def discovered_test_ids(start_dir: str = "tests") -> list[str]:
    suite = unittest.defaultTestLoader.discover(start_dir)
    return [test.id() for test in flatten(suite)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--start-dir", default="tests")
    args = parser.parse_args(argv)
    if args.count < 1 or not 0 <= args.index < args.count:
        parser.error("index must be in [0, count), and count must be positive")

    # Discover once: a second discover() in the same process sees already
    # imported modules and can differ (it did on GitHub runners).
    tests = list(flatten(unittest.defaultTestLoader.discover(args.start_dir)))
    all_ids = [test.id() for test in tests]
    shards = partition_test_ids(all_ids, args.count)
    selected_ids = set(shards[args.index])
    by_id = {test.id(): test for test in tests}
    print(f"unittest shard {args.index + 1}/{args.count}: {len(selected_ids)} of {len(all_ids)} tests", flush=True)
    suite = unittest.TestSuite(by_id[test_id] for test_id in all_ids if test_id in selected_ids)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
