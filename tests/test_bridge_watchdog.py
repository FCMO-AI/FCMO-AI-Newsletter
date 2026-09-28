from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.bridge_watchdog import decision, run
from tools.install_bridge_watchdog import units

NOW = datetime(2026, 9, 27, 18, 0, tzinfo=timezone.utc)


class BridgeWatchdogTests(unittest.TestCase):
    def row(self, hours_ago):
        return {"head_branch": "main", "created_at": (NOW - timedelta(hours=hours_ago)).isoformat()}

    def test_fresh_run_requires_no_dispatch(self):
        self.assertEqual(decision([self.row(5)], None, NOW), "RECENT_RUN")

    def test_old_run_dispatches_once_then_waits(self):
        self.assertEqual(decision([self.row(7)], None, NOW), "DISPATCH")
        self.assertEqual(decision([self.row(7)], (NOW - timedelta(hours=1)).isoformat(), NOW),
                         "AWAITING_DISPATCH")
        self.assertEqual(decision([self.row(9)], (NOW - timedelta(hours=3)).isoformat(), NOW),
                         "DISPATCH")

    def test_accepted_request_is_recorded_but_never_called_a_successful_run(self):
        calls = []
        def api(method, url, token, body=None):
            calls.append((method, url, body))
            return {"workflow_runs": [self.row(8)]} if method == "GET" else None
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "watchdog.json"
            self.assertEqual(run("FCMO-AI/FCMO-AI-Newsletter", "fake-token", state, NOW, api=api),
                             "DISPATCH_REQUESTED")
            self.assertEqual(json.loads(state.read_text())["result"], "accepted_not_confirmed")
            self.assertEqual(run("FCMO-AI/FCMO-AI-Newsletter", "fake-token", state, NOW, api=api),
                             "AWAITING_DISPATCH")
            self.assertEqual([method for method, _, _ in calls], ["GET", "POST", "GET"])

    def test_api_failure_cannot_write_a_false_receipt(self):
        def api(method, url, token, body=None):
            if method == "POST":
                raise OSError("offline")
            return {"workflow_runs": [self.row(8)]}
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "watchdog.json"
            with self.assertRaises(OSError):
                run("FCMO-AI/FCMO-AI-Newsletter", "fake-token", state, NOW, api=api)
            self.assertFalse(state.exists())

    def test_host_timer_runs_outside_actions_and_uses_a_token_file(self):
        service, timer = units(Path("/opt/newsletter"), Path("/opt/secret/token"),
                               Path("/opt/state/bridge.json"))
        self.assertIn("--token-file /opt/secret/token", service)
        self.assertIn("OnCalendar=hourly", timer)
        self.assertIn("Persistent=true", timer)
        self.assertNotIn("FCMO_WATCHDOG_TOKEN=", service)


if __name__ == "__main__":
    unittest.main()
