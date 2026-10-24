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
# A frozen corpus count is a quantity of stories/records: the line measures one (len(...), a count or total)
# or names one. Pixel coordinates, widths, timeouts and byte sizes that merely equal today's number are not.
COUNT_CONTEXT = re.compile(r"len\(|count|total|stor(?:y|ies)|record|live|front|corpus|quarantine", re.IGNORECASE)


def frozen_counts_in(line: str, volatile: dict[int, str]) -> list[int]:
    if MARK in line or line.lstrip().startswith("#") or not COUNT_CONTEXT.search(line):
        return []
    return [int(m.group(1)) for m in INTEGER.finditer(line) if int(m.group(1)) in volatile]


def volatile_counts(root: Path = ROOT) -> dict[int, str]:
    rows = [l for l in (root / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    counts = {len(rows): "corpus records", len(rows) // 5 + 1: "20% quarantine limit"}
    stories = root / "site/data/stories.v2.json"
    if stories.is_file():
        doc = json.loads(stories.read_text(encoding="utf-8"))["stories"]
        live = [s for s in doc if s.get("status") == "live"]
        counts[len(doc)] = "stories"
        counts[len(live)] = "live stories"
        counts[sum(1 for s in live if s.get("front_page_eligible"))] = "front-page stories"
    return {n: label for n, label in counts.items() if n >= 100}


def find_frozen(root: Path = ROOT) -> list[str]:
    """Every test line under ``root`` that freezes one of ``root``'s current corpus counts."""
    volatile = volatile_counts(root)
    found = []
    for path in sorted((root / "tests").glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for value in frozen_counts_in(line, volatile):
                found.append(f"{path.name}:{number}: {value} equals the current {volatile[value]}: {line.strip()[:100]}")
    return found


class NoFrozenCorpusCounts(unittest.TestCase):
    def test_no_test_freezes_a_live_corpus_count(self):
        found = find_frozen(ROOT)
        self.assertEqual([], found, "derive these from the live data instead of freezing them:\n" + "\n".join(found))

    def test_the_guard_sees_a_frozen_count(self):
        current = len([l for l in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()])
        self.assertIn(current, volatile_counts())
        self.assertTrue(INTEGER.search(f"self.assertEqual(len(rows), {current})"))
        self.assertEqual(frozen_counts_in(f"self.assertEqual(len(rows), {current})", volatile_counts()), [current])

    def test_count_shaped_lines_are_flagged_and_geometry_is_not(self):
        volatile = {306: "front-page stories", 2013: "live stories"}
        for line in ("self.assertEqual(len(front), 306)", "self.assertEqual(front_count, 306)",
                     "self.assertEqual(total, 2013)", "expected_stories = 2013", "assert live == 306"):
            with self.subTest(line=line):
                self.assertEqual(frozen_counts_in(line, volatile), [int(line.rstrip(")")[-4:].strip(" ,(="))])
        for line in ('"banner": {"state": "DELAYED", **r(223, 306)},', "timeout=306)", "viewport = (2013, 900)",
                     "self.assertEqual(len(front), 306)  # corpus-count-ok: unrelated", "# len(front) == 306"):
            with self.subTest(line=line):
                self.assertEqual(frozen_counts_in(line, volatile), [])
