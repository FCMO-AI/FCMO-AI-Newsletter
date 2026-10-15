"""Production health measures the edition readers see, not the repository.

Regression (2026-10-11 .. 10-14): every Pages deploy was cancelled for days.
The health workflow measured main's ``site/data/stories.v2.json`` and kept
reporting ``EDITORIAL OK`` while the public origin served a 2026-10-09
edition.  These tests go red if the health check can again be satisfied by the
repository's undeployed Story layer.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from tools import editorial_freshness, served_edition
from tools.build_deployment_identity import SCHEMA

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / ".github/workflows/newsroom-health.yml"
NOW = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


def iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class ServedEditionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "test")
        # Edition the public origin serves: built 80 h ago, newest event 90 h old.
        self.served = self.commit_stories(NOW - timedelta(hours=90), NOW - timedelta(hours=80))
        # main then received fresh stories 70 h ago and 2 h ago, never deployed.
        self.commit_stories(NOW - timedelta(hours=71), NOW - timedelta(hours=70))
        self.head = self.commit_stories(NOW - timedelta(hours=3), NOW - timedelta(hours=2))
        self.wire = Path(self.tmp.name) / "wire-status.json"  # absent: wire state is not under test
        self.records = Path(self.tmp.name) / "developments.jsonl"
        self.records.write_text("", encoding="utf-8")

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, text=True,
                              capture_output=True, env={**os.environ, **(env or {})}).stdout.strip()

    def commit_stories(self, event_at: datetime, committed_at: datetime) -> str:
        path = self.repo / "site/data/stories.v2.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema": "fcmo-stories-v2", "stories": [
            {"id": "FCMO-AAAAAAAAAAAA", "status": "live", "event_at": iso(event_at)},
            # Withdrawn and future stories can never make an edition fresh.
            {"id": "FCMO-BBBBBBBBBBBB", "status": "withdrawn", "event_at": iso(NOW)},
            {"id": "FCMO-CCCCCCCCCCCC", "status": "live", "event_at": iso(NOW + timedelta(days=3))},
        ]}), encoding="utf-8")
        self.git("add", "-A")
        stamp = f"{int(committed_at.timestamp())} +0000"
        self.git("commit", "-q", "-m", "stories", env={"GIT_COMMITTER_DATE": stamp, "GIT_AUTHOR_DATE": stamp})
        return self.git("rev-parse", "HEAD")

    def identity(self, **fields) -> Path:
        path = Path(self.tmp.name) / "identity.json"
        path.write_text(json.dumps({"schema": SCHEMA, "source_commit": self.served, **fields}), encoding="utf-8")
        return path

    def run_served(self, identity: Path, *extra: str) -> tuple[int, dict]:
        out = Path(self.tmp.name) / "signal.json"
        with contextlib.redirect_stdout(io.StringIO()):
            rc = served_edition.main([
                "--identity-file", str(identity), "--repo", str(self.repo), "--ref", "HEAD",
                "--wire-status", str(self.wire), "--records", str(self.records),
                "--work-dir", str(Path(self.tmp.name) / "work"), "--now", iso(NOW),
                "--signal-out", str(out), *extra,
            ])
        return rc, json.loads(out.read_text(encoding="utf-8"))

    def test_repository_probe_is_green_while_the_served_edition_is_stale(self) -> None:
        # The former probe: main's Story layer says the paper is fresh ...
        with contextlib.redirect_stdout(io.StringIO()):
            old_rc = editorial_freshness.main([
                "check", "--stories", str(self.repo / "site/data/stories.v2.json"),
                "--wire-status", str(self.wire), "--records", str(self.records), "--now", iso(NOW)])
        self.assertEqual(old_rc, 0)
        # ... the served-edition probe sees what readers see.
        rc, signal = self.run_served(self.identity())
        self.assertEqual(rc, 1)
        self.assertEqual(signal["status"], "RED")
        self.assertEqual(signal["code"], "EVENT_STALE")
        self.assertEqual(signal["metrics"]["served_commit"], self.served)
        self.assertEqual(signal["metrics"]["newest_event_age_h"], 90.0)
        self.assertEqual(signal["metrics"]["deploy_lag_h"], 70.0)
        self.assertEqual(signal["metrics"]["pending_story_commits"], 2)
        self.assertIn("behind main", signal["detail"])

    def test_current_edition_is_green_with_no_lag(self) -> None:
        rc, signal = self.run_served(self.identity(source_commit=self.head))
        self.assertEqual(rc, 0, signal)
        self.assertEqual((signal["status"], signal["code"]), ("GREEN", "OK"))
        self.assertEqual(signal["metrics"]["deploy_lag_h"], 0.0)
        self.assertEqual(signal["metrics"]["pending_story_commits"], 0)

    def test_lag_beyond_the_limit_is_red_even_with_a_recent_event(self) -> None:
        # A generous event limit keeps the editorial signal GREEN; the deploy lag
        # (70 h > 36 h) must still fail and must not leave GREEN with a red rc.
        rc, signal = self.run_served(self.identity(), "--max-event-age-hours", "200", "--max-lag-hours", "36")
        self.assertEqual(rc, 1)
        self.assertEqual((signal["status"], signal["code"]), ("RED", "EVENT_STALE"))

    def test_unknown_served_edition_fails_closed(self) -> None:
        cases = {
            "wrong schema": {"schema": "fcmo-deployment-identity-v0"},
            "no commit": {"source_commit": None},
            "short commit": {"source_commit": self.served[:12]},
            "foreign commit": {"source_commit": "0" * 40},
        }
        for label, fields in cases.items():
            with self.subTest(label):
                rc, signal = self.run_served(self.identity(**fields))
                self.assertEqual(rc, 1)
                self.assertEqual((signal["status"], signal["code"]), ("UNKNOWN", "UNKNOWN"))
                self.assertNotIn("metrics", signal, "an unknown edition must not borrow the repo's freshness")

    def test_unreadable_identity_fails_closed(self) -> None:
        broken = Path(self.tmp.name) / "broken.json"
        broken.write_text("<html>404</html>", encoding="utf-8")
        rc, signal = self.run_served(broken)
        self.assertEqual((rc, signal["code"]), (1, "UNKNOWN"))

    def test_served_commit_off_main_fails_closed(self) -> None:
        self.git("checkout", "-q", "-b", "side", self.served)
        side = self.commit_stories(NOW - timedelta(hours=1), NOW - timedelta(hours=1))
        self.git("checkout", "-q", "main")
        rc, signal = self.run_served(self.identity(source_commit=side))
        self.assertEqual((rc, signal["code"]), (1, "UNKNOWN"))


class HealthWorkflowTests(unittest.TestCase):
    def test_editorial_job_measures_the_served_edition(self) -> None:
        workflow = yaml.safe_load(HEALTH.read_text(encoding="utf-8"))
        job = workflow["jobs"]["editorial-freshness"]
        checkout = next(step for step in job["steps"] if str(step.get("uses", "")).startswith("actions/checkout"))
        self.assertEqual(checkout["with"]["fetch-depth"], 0, "the served commit must be resolvable")
        runs = "\n".join(step.get("run", "") for step in job["steps"])
        self.assertIn("python tools/served_edition.py", runs)
        self.assertIn("--identity-url https://fcmo-ai.github.io/FCMO-AI-Newsletter/deployment-identity.json", runs)
        self.assertIn('exit "$rc"', runs)
        # The repository's own Story layer must never be the measured edition again.
        self.assertNotIn("--stories site/data/stories.v2.json", runs)
        self.assertNotIn("editorial_freshness.py check", runs)

    def test_health_reruns_when_the_probe_changes(self) -> None:
        workflow = yaml.safe_load(HEALTH.read_text(encoding="utf-8"))
        triggers = workflow.get("on", workflow.get(True))
        self.assertIn("tools/served_edition.py", triggers["push"]["paths"])


if __name__ == "__main__":
    unittest.main()
