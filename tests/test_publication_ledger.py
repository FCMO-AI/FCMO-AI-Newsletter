"""The active desk history and future migration preserve the activation contract."""

import json
from pathlib import Path
import subprocess
import unittest

from ops.publish_ledger import validate_ledger

ROOT = Path(__file__).resolve().parents[1]


class PublicationLedgerTests(unittest.TestCase):
    def encoded(self, *timestamps):
        return ''.join(json.dumps({'run_id': f'run-{i}', 'T0': stamp}) + '\n'
                       for i, stamp in enumerate(timestamps)).encode()

    def test_activation_history_is_chronological_in_utc(self):
        # Local clock strings are deliberately in the opposite order to UTC.
        data = self.encoded('2026-10-04T01:00:00+02:00', '2026-10-04T00:00:00Z')
        self.assertEqual(len(validate_ledger(data)), 2)
        with self.assertRaisesRegex(ValueError, 'chronological'):
            validate_ledger(self.encoded('2026-10-04T00:00:00Z', '2026-10-04T01:00:00+02:00'))

    def test_naive_timestamps_and_duplicate_run_ids_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'timezone'):
            validate_ledger(self.encoded('2026-10-04T00:00:00'))
        row = self.encoded('2026-10-04T00:00:00Z')
        with self.assertRaisesRegex(ValueError, 'unique'):
            validate_ledger(row + row)

    def test_product_branch_preserves_active_desk_history_until_writers_migrate(self):
        tracked = subprocess.check_output(['git', 'ls-files', 'ops/publication-desk/LEDGER.jsonl'],
                                          cwd=ROOT, text=True)
        self.assertEqual(tracked.strip(), 'ops/publication-desk/LEDGER.jsonl')
        # Missing history is an error, never an empty ledger. Validate the actual
        # writer's persisted records, including ordering and unique run IDs.
        rows = validate_ledger((ROOT / tracked.strip()).read_bytes())
        self.assertGreater(len(rows), 0)


if __name__ == '__main__':
    unittest.main()
