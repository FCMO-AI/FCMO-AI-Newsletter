"""The publication desk history remains readable in actual activation order."""

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PublicationLedgerTests(unittest.TestCase):
    def test_activation_history_is_chronological_in_utc(self):
        rows = (ROOT / "ops/publication-desk/LEDGER.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertTrue(rows)
        times = []
        for number, line in enumerate(rows, 1):
            with self.subTest(line=number):
                record = json.loads(line)
                self.assertTrue(record["run_id"])
                timestamp = datetime.fromisoformat(record["T0"].replace("Z", "+00:00"))
                self.assertIsNotNone(timestamp.tzinfo)
                times.append(timestamp.astimezone(timezone.utc))
        self.assertEqual(times, sorted(times), "desk activations are out of chronological order")


if __name__ == "__main__":
    unittest.main()
