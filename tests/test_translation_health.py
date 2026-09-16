"""Regression coverage for strict release localization vs. health-SLO grace."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "translation_health.py"


class TranslationHealthTests(unittest.TestCase):
    def fixture(self, *, published_at: datetime, importance: int = 6, es: bool = False, zh: bool = False) -> Path:
        temp = tempfile.TemporaryDirectory(prefix="fcmo-translation-health-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "site/data/i18n/es-419").mkdir(parents=True)
        (root / "site/data/i18n/zh-Hans").mkdir(parents=True)
        story = {
            "research_id": "FCMO-TEST-NATIVE",
            "story_type": "STANDARD",
            "published_at": published_at.isoformat().replace("+00:00", "Z"),
            "news_value": {"importance": importance},
        }
        (root / "site/data/stories.json").write_text(json.dumps([story]), encoding="utf-8")
        for locale, present in (("es-419", es), ("zh-Hans", zh)):
            records = {"FCMO-TEST-NATIVE": {"title": "x"}} if present else {}
            path = root / "site/data/i18n" / locale / "part-001.json"
            path.write_text(json.dumps({"records": records}), encoding="utf-8")
        return root

    def run_check(self, root: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root), *extra],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        return result, payload

    def test_health_slo_may_report_grace_without_claiming_release_completeness(self) -> None:
        root = self.fixture(published_at=datetime.now(timezone.utc), es=False, zh=False)
        result, payload = self.run_check(root, "--grace-hours", "1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["mode"], "HEALTH_SLO")
        self.assertEqual(payload["state"], "DEGRADED_TRANSLATION_GRACE")
        self.assertEqual(payload["grace_count"], 1)

    def test_strict_release_gate_rejects_same_missing_story_immediately(self) -> None:
        root = self.fixture(published_at=datetime.now(timezone.utc), es=False, zh=False)
        result, payload = self.run_check(root, "--require-complete")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["mode"], "RELEASE_GATE")
        self.assertEqual(payload["state"], "UNHEALTHY_TRANSLATION_INCOMPLETE")
        self.assertEqual(payload["overdue_count"], 1)
        self.assertEqual(payload["missing_recent"][0]["missing"], ["es-419", "zh-Hans"])

    def test_strict_release_gate_checks_stories_health_prioritization_would_ignore(self) -> None:
        root = self.fixture(
            published_at=datetime.now(timezone.utc) - timedelta(hours=72),
            importance=1,
            es=False,
            zh=False,
        )
        health, _ = self.run_check(root, "--fresh-window-hours", "30", "--minimum-importance", "4")
        strict, payload = self.run_check(root, "--require-complete")
        self.assertEqual(health.returncode, 0)
        self.assertEqual(strict.returncode, 1)
        self.assertEqual(payload["overdue_count"], 1)

    def test_strict_release_gate_accepts_complete_native_identity_coverage(self) -> None:
        root = self.fixture(published_at=datetime.now(timezone.utc), es=True, zh=True)
        result, payload = self.run_check(root, "--require-complete")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["mode"], "RELEASE_GATE")
        self.assertEqual(payload["state"], "HEALTHY")
        self.assertEqual(payload["overdue_count"], 0)


if __name__ == "__main__":
    unittest.main()
