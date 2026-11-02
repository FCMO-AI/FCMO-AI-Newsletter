"""A story event dated without a time means "sometime that day": its age runs from the end of that day.

Regression (incident inc-10172de8, 2026-11-01): the newest event was dated 2026-10-30 (no time, stored as
T00:00:00Z); the 36 h SLO went red at 12:00Z on 10-31+1 even though the event could be 23 h newer.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tools import editorial_freshness

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def sig(event: str) -> dict:
    return editorial_freshness.editorial_signal("FRESH", event, NOW, 36.0)


class DayEndFreshnessTests(unittest.TestCase):
    def test_date_without_time_from_yesterday_at_13z_is_not_red(self) -> None:
        # date-only 11-01 at 11-02 13:00Z: old rule 37h (red), end-of-day rule 13h
        now = datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)
        out = editorial_freshness.editorial_signal("FRESH", "2026-11-01T00:00:00Z", now, 36.0)
        self.assertEqual(out["status"], "GREEN")
        out = editorial_freshness.editorial_signal("FRESH", "2026-11-01", now, 36.0)
        self.assertEqual(out["status"], "GREEN")

    def test_date_without_time_from_three_days_ago_is_red(self) -> None:
        self.assertEqual(sig("2026-10-30T00:00:00Z")["status"], "RED")
        self.assertEqual(sig("2026-10-30T00:00:00Z")["code"], "EVENT_STALE")

    def test_date_with_time_40h_ago_is_red(self) -> None:
        event = (NOW - timedelta(hours=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(sig(event)["status"], "RED")

    def test_date_with_time_is_measured_unchanged(self) -> None:
        self.assertEqual(sig("2026-11-01T06:30:00Z")["metrics"]["newest_event_age_h"], 29.5)

    def test_today_date_without_time_is_age_zero_not_negative(self) -> None:
        self.assertEqual(sig("2026-11-02T00:00:00Z")["metrics"]["newest_event_age_h"], 0.0)

    def test_boundary_still_36h(self) -> None:
        # day ended 10-31 23:59:59Z -> at 11-02 12:00Z that is 36.0h (round) -> still within the limit
        self.assertEqual(sig("2026-10-31T00:00:00Z")["status"], "GREEN")


if __name__ == "__main__":
    unittest.main()
