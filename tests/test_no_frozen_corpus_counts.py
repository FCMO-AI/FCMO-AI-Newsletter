"""Tests must derive live-corpus quantities from the data, never freeze them.

The newswire adds stories continuously, so a literal that equals today's record,
live-story or front-page count is correct for one day and then breaks Deploy.
This guard goes red the moment a test file contains one of the current numbers
as a bare integer. Compute the expectation from the same data instead (see
``expected_live_ids`` in test_story_layer.py), or mark an unrelated coincidence
with ``# corpus-count-ok`` on that line.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGER = re.compile(r"(?<![\w.%#$-])(\d{3,4})(?![\w.%])")
MARK = "corpus-count-ok"


def volatile_counts() -> dict[int, str]:
    rows = [l for l in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    counts = {len(rows): "corpus records", len(rows) // 5 + 1: "20% quarantine limit"}
    stories = ROOT / "site/data/stories.v2.json"
    if stories.is_file():
        doc = json.loads(stories.read_text(encoding="utf-8"))["stories"]
        live = [s for s in doc if s.get("status") == "live"]
        counts[len(doc)] = "stories"
        counts[len(live)] = "live stories"
        counts[sum(1 for s in live if s.get("front_page_eligible"))] = "front-page stories"
    return {n: label for n, label in counts.items() if n >= 100}


class NoFrozenCorpusCounts(unittest.TestCase):
    def test_no_test_freezes_a_live_corpus_count(self):
        volatile = volatile_counts()
        found = []
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if path.name == Path(__file__).name:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if MARK in line or line.lstrip().startswith("#"):
                    continue
                for match in INTEGER.finditer(line):
                    value = int(match.group(1))
                    if value in volatile:
                        found.append(f"{path.name}:{number}: {value} equals the current {volatile[value]}: {line.strip()[:100]}")
        self.assertEqual([], found, "derive these from the live data instead of freezing them:\n" + "\n".join(found))

    def test_the_guard_sees_a_frozen_count(self):
        current = len([l for l in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()])
        self.assertIn(current, volatile_counts())
        self.assertTrue(INTEGER.search(f"self.assertEqual(len(rows), {current})"))
