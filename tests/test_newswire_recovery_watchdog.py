from __future__ import annotations

import unittest
from datetime import datetime, timezone

from tools import newswire_recovery_watchdog as watchdog


class NewswireRecoveryWatchdogTests(unittest.TestCase):
    def test_before_recovery_window_never_dispatches(self) -> None:
        needed, reason = watchdog.recovery_decision(None, datetime(2026, 9, 7, 14, 59, tzinfo=timezone.utc))
        self.assertFalse(needed)
        self.assertEqual(reason, "BEFORE_RECOVERY_WINDOW")

    def test_bootstrap_after_recovery_window_requires_recovery(self) -> None:
        needed, reason = watchdog.recovery_decision(
            {"state": "BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE", "airlock_generated_at": None},
            datetime(2026, 9, 7, 15, 5, tzinfo=timezone.utc),
        )
        self.assertTrue(needed)
        self.assertEqual(reason, "NO_AIRLOCK_BACKED_RELEASE")

    def test_yesterdays_airlock_after_recovery_window_requires_recovery(self) -> None:
        needed, reason = watchdog.recovery_decision(
            {"state": "PUBLIC_DELTA_READY", "airlock_generated_at": "2026-09-07T03:30:00Z"},
            datetime(2026, 9, 7, 16, 5, tzinfo=timezone.utc),
        )
        self.assertTrue(needed)
        self.assertEqual(reason, "DAILY_CYCLE_MISSING")

    def test_current_local_day_airlock_is_healthy_noop(self) -> None:
        # Footnote: 15:05Z is 09:05 in Mexico City; an 15:01Z heartbeat belongs to
        # the same local publication day and therefore suppresses duplicate recovery.
        needed, reason = watchdog.recovery_decision(
            {"state": "NO_PUBLIC_DELTA_READY", "airlock_generated_at": "2026-09-07T15:01:00Z"},
            datetime(2026, 9, 7, 15, 5, tzinfo=timezone.utc),
        )
        self.assertFalse(needed)
        self.assertEqual(reason, "CURRENT_DAILY_CYCLE_LIVE")

    def test_missing_live_status_recovers_after_window(self) -> None:
        needed, reason = watchdog.recovery_decision(None, datetime(2026, 9, 7, 18, 5, tzinfo=timezone.utc))
        self.assertTrue(needed)
        self.assertEqual(reason, "LIVE_STATUS_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
