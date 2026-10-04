"""L3: a frozen upstream clock cannot block honest public freshness reporting."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import editorial_freshness, wire_status
from tools.paper.build import PaperBuilder

NOW = "2026-10-04T12:00:00Z"


class SupplyIndependentFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        shutil.copytree(ROOT / "contracts/fixtures/corpus-43", self.corpus)
        self.status = self.root / "newsroom-status.json"
        self.status.write_bytes((ROOT / "site/data/newsroom-status.json").read_bytes())
        self.wire = self.root / "wire-status.json"
        self.wire.write_bytes((ROOT / "contracts/fixtures/wire-status.down.json").read_bytes())

    def receipt(self, mode):
        return subprocess.run([sys.executable, "tools/newsroom_receipt.py", mode,
                               "--corpus", str(self.corpus), "--status", str(self.status),
                               "--wire-status", str(self.wire), "--site", str(ROOT / "site"),
                               "--now", NOW], cwd=ROOT, text=True, capture_output=True)

    def test_frozen_heartbeat_does_not_hard_fail_refresh_but_health_stays_red(self):
        result = self.receipt("preflight")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout.splitlines()[1])["wire_state"], "TRANSPORT_DOWN")
        health = subprocess.run([sys.executable, "tools/wire_status.py", "classify",
                                 "--wire-status", str(self.wire), "--now", NOW],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(health.returncode, 1)

    def test_status_only_refresh_records_the_real_corpus_age(self):
        result = self.receipt("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        status = json.loads(self.status.read_text())
        public = status.get("publication_status", {})
        self.assertEqual(public.get("state"), "DELAYED")
        self.assertGreater(public["newest_age_hours"], 48)
        self.assertEqual(public["checked_at"], NOW)
        self.assertEqual(public["wire_state"], "TRANSPORT_DOWN")

    def test_fresh_transport_does_not_mask_stale_editorial_content(self):
        for state in ("FRESH", "QUIET"):
            with self.subTest(state=state):
                result = editorial_freshness.editorial_signal(
                    state, "2026-09-11T17:55:45Z", wire_status.parse_utc(NOW), 36)
                self.assertEqual(result["status"], "RED")
                self.assertEqual(result["code"], "EVENT_STALE")

    def test_current_corpus_build_exposes_delayed_in_every_language_and_json(self):
        source = json.loads(self.status.read_text())
        source.update(status_updated_at=NOW, edition_state="FRESH", edition_reason=None,
                      wire_state="FRESH", alerts=[])
        self.status.write_text(json.dumps(source))
        output = self.root / "publish"
        PaperBuilder(stories_path=ROOT / "site/data/stories.v2.json", status_path=self.status,
                     out=output, base="/FCMO-AI-Newsletter/").build()
        public_path = output / "status.json"
        self.assertTrue(public_path.is_file(), "public freshness endpoint is missing")
        public = json.loads(public_path.read_text())
        self.assertEqual((public["state"], public["reason"]), ("DELAYED", "STORY_SUPPLY"))
        for prefix in ("", "es/", "zh/"):
            for route in ("ai/", "status/"):
                page = (output / prefix / route / "index.html").read_text()
                self.assertIn('data-edition-state="DELAYED"', page)
                self.assertNotIn('hidden data-edition-state="FRESH"', page)
        self.assertEqual((output / "data/newsroom-status.json").read_bytes(), self.status.read_bytes())


if __name__ == "__main__":
    unittest.main()
