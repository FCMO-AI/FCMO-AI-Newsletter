#!/usr/bin/env python3
"""Run the repository unittest suite as deterministic, complete shards.

The release regression gate is the same ``python -m unittest discover -s
tests`` suite, split across parallel jobs so the publication path stops
taking longer than the newsroom's refresh cadence.  Sharding may only make the
gate faster; it must never make it weaker, so every shard:

* discovers the whole suite once, in a single process;
* partitions it by test *class* (a class's ``setUpClass`` runs exactly once,
  in exactly one shard) with a stable longest-processing-time assignment;
* refuses to run unless the partition covers every discovered test exactly
  once, and refuses a suite that fails to import (``unittest.loader`` turns
  an import error into a ``_FailedTest``; it is kept and therefore fails);
* prints a digest of the full test-ID list, so the shard jobs of one run can
  be checked to have seen the same suite.

``--list`` prints the partition without running anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


DEFAULT_SECONDS_PER_TEST = 2.0
WEIGHTS = Path(__file__).with_name("unittest_shard_weights.json")


def group_key(test_id: str) -> str:
    """The unit of assignment: the test class (``module.Class``)."""
    head, _, _ = test_id.rpartition(".")
    return head or test_id


def _stable(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def partition_test_ids(test_ids: list[str], shard_count: int,
                       weights: dict[str, float] | None = None) -> list[list[str]]:
    """Return ``shard_count`` shards that cover ``test_ids`` exactly once.

    Classes are kept whole and assigned heaviest-first to the currently
    lightest shard (ties broken by shard index), so the result depends only on
    the set of IDs and the committed weights, not on discovery order or the
    machine.  A class's weight is its measured seconds from ``weights`` when
    known, else ``DEFAULT_SECONDS_PER_TEST`` per test (without ``weights``,
    simply its test count).  Inside a shard the discovery order is preserved.
    """
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if len(test_ids) != len(set(test_ids)):
        raise ValueError("discovery returned duplicate unittest IDs")
    groups: dict[str, list[str]] = {}
    for test_id in test_ids:
        groups.setdefault(group_key(test_id), []).append(test_id)
    if len(groups) < shard_count:
        raise ValueError("discovery must find at least one test class per shard")

    def weight(key: str) -> float:
        if weights is None:
            return float(len(groups[key]))
        known = weights.get(key)
        return float(known) if isinstance(known, (int, float)) and known > 0 else \
            DEFAULT_SECONDS_PER_TEST * len(groups[key])

    ordered = sorted(groups, key=lambda key: (-weight(key), _stable(key)))
    loads = [0.0] * shard_count
    owner: dict[str, int] = {}
    for key in ordered:
        target = min(range(shard_count), key=lambda index: (loads[index], index))
        owner[key] = target
        loads[target] += weight(key)
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    for test_id in test_ids:
        shards[owner[group_key(test_id)]].append(test_id)
    assert_complete(test_ids, shards)
    return shards


def load_weights(path: Path) -> dict[str, float]:
    """Measured seconds per test class; a missing file means count balancing."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    classes = data.get("class_seconds", {}) if isinstance(data, dict) else {}
    return {str(key): float(value) for key, value in classes.items() if isinstance(value, (int, float))}


def assert_complete(test_ids: list[str], shards: list[list[str]]) -> None:
    """Fail closed unless every test lands in exactly one shard."""
    seen: dict[str, int] = {}
    for index, shard in enumerate(shards):
        for test_id in shard:
            if test_id in seen:
                raise ValueError(f"{test_id} is in shards {seen[test_id]} and {index}")
            seen[test_id] = index
    missing = set(test_ids) - set(seen)
    extra = set(seen) - set(test_ids)
    if missing or extra:
        raise ValueError(f"partition is not complete: missing={sorted(missing)[:5]} extra={sorted(extra)[:5]}")


def suite_digest(test_ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(test_ids)).encode("utf-8")).hexdigest()


class TimedResult(unittest.TextTestResult):
    """Record wall time per test class so shard balance can be tuned from logs.

    Everything since the previous test stopped is charged to the next test's
    class, so ``setUpModule``/``setUpClass`` cost lands on the class that
    needed it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_seconds: dict[str, float] = {}
        self._last = time.monotonic()

    def stopTest(self, test):
        super().stopTest(test)
        now = time.monotonic()
        key = group_key(test.id())
        self.class_seconds[key] = self.class_seconds.get(key, 0.0) + now - self._last
        self._last = now


def ensure_repository_root_on_path() -> Path:
    """Make repository package imports match ``python -m unittest`` discovery."""
    root = Path(__file__).resolve().parents[1]
    root_string = str(root)
    if root_string in sys.path:
        sys.path.remove(root_string)
    sys.path.insert(0, root_string)
    return root


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, help="0-based shard to run")
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--start-dir", default="tests")
    parser.add_argument("--list", action="store_true", help="print the partition as JSON and exit")
    parser.add_argument("--weights", type=Path, default=WEIGHTS, help="measured class seconds (balance only)")
    args = parser.parse_args(argv)
    if args.count < 1:
        parser.error("count must be positive")
    if not args.list and (args.index is None or not 0 <= args.index < args.count):
        parser.error("index must be in [0, count)")

    # Script execution puts ``tools/`` rather than the repository root on
    # sys.path; add the root so imports behave like the serial discover job.
    ensure_repository_root_on_path()

    # The serial suite creates the ignored ``_audit/`` scratch directory in an
    # early test and several later tests write temporary trees under it without
    # creating it; every shard reproduces that precondition.
    Path("_audit").mkdir(exist_ok=True)

    # Discover once: a second discover() in one process sees already imported
    # modules and can differ.
    tests = list(flatten(unittest.defaultTestLoader.discover(args.start_dir)))
    all_ids = [test.id() for test in tests]
    shards = partition_test_ids(all_ids, args.count, load_weights(args.weights))
    digest = suite_digest(all_ids)
    if args.list:
        print(json.dumps({"tests": len(all_ids), "suite_sha256": digest,
                          "shards": [len(shard) for shard in shards]}, indent=2))
        return 0
    selected = set(shards[args.index])
    print(f"unittest shard {args.index + 1}/{args.count}: {len(selected)} of {len(all_ids)} tests; "
          f"suite_sha256={digest}", flush=True)
    suite = unittest.TestSuite(test for test in tests if test.id() in selected)
    result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(suite)
    slowest = sorted(result.class_seconds.items(), key=lambda item: -item[1])
    print("slowest classes in this shard: " + "; ".join(f"{key} {seconds:.0f}s" for key, seconds in slowest[:10]),
          flush=True)
    print("class seconds: " + json.dumps({key: round(seconds, 1) for key, seconds in slowest if seconds >= 5},
                                         sort_keys=True), flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
