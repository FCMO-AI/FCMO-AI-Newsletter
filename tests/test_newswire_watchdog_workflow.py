from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / ".github" / "workflows" / "newswire-watchdog.yml"


class NewswireWatchdogWorkflowTests(unittest.TestCase):
    def test_watchdog_has_narrow_recovery_authority(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertIn("actions: write", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("FCMO_NEWSWIRE_APP_PRIVATE_KEY", text)
        self.assertNotIn("FCMO_NEWSWIRE_APP_CLIENT_ID", text)
        self.assertNotIn("AI-Research-Breakthroughs", text)

    def test_watchdog_uses_live_daily_cycle_oracle_and_only_dispatches_bridge(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        self.assertIn("tools/newswire_recovery_watchdog.py", text)
        self.assertIn("steps.recovery.outputs.recovery_needed == 'true'", text)
        self.assertIn("gh workflow run newswire-bridge.yml --ref main", text)
        self.assertNotIn("daily-refresh.yml", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("curl -X", text)

    def test_watchdog_has_schedule_and_independent_health_completion_trigger(self) -> None:
        text = WATCHDOG.read_text(encoding="utf-8")
        for cron in ("5 15", "5 16", "5 17", "5 18"):
            self.assertIn(f"cron: '{cron} * * *'", text)
        self.assertIn("workflows: ['Autonomous newsroom production health']", text)
        self.assertIn("types: [completed]", text)
        self.assertIn("cancel-in-progress: false", text)


if __name__ == "__main__":
    unittest.main()
