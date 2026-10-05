"""Valid upstream confidence must survive admission without inventing freshness."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import story_layer, taxonomy

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/editorial-credible-unconfirmed.json"
NOW = "2026-10-05T23:00:00Z"


class EditorialAdmissionTests(unittest.TestCase):
    def test_all_canonical_arb_confidence_values_have_conservative_mappings(self):
        mappings = {
            "confirmed": "confirmed",
            "strongly_supported": "strongly_supported",
            "credible_unconfirmed": "claimed_unverified",
            "weak_signal": "claimed_unverified",
            "speculation": "claimed_unverified",
        }
        for upstream, expected in mappings.items():
            with self.subTest(upstream=upstream):
                self.assertEqual(taxonomy.normalize_confidence(upstream), expected)
        self.assertIsNone(taxonomy.normalize_confidence("vibes"))

    def test_public_dated_developing_story_reaches_live_health_without_redating(self):
        row = json.loads(FIXTURE.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data/developments.jsonl").write_text(json.dumps(row) + "\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                doc = story_layer.build_stories(story_layer.StoryInputs(root, None, None, None, NOW))
            self.assertEqual(len(doc["stories"]), 1, err.getvalue())
            story = doc["stories"][0]
            self.assertEqual(story["id"], row["id"])
            self.assertEqual(story["status"], "live")
            self.assertEqual(story["event_at"], row["event_at"])
            self.assertEqual(story["date_precision"], "day")
            self.assertEqual(story["confidence"], "claimed_unverified")
            self.assertEqual(story["evidence_class"], row["evidence_class"])
            self.assertEqual(story["evidence"]["claims"], row["claims"])
            stories = root / "stories.json"
            stories.write_text(json.dumps(doc))
            signal = root / "editorial.json"

            def check(now):
                return subprocess.run([
                    sys.executable, str(ROOT / "tools/editorial_freshness.py"), "check",
                    "--stories", str(stories), "--wire-status", str(root / "missing-wire.json"),
                    "--now", now, "--signal-out", str(signal),
                ], cwd=ROOT, capture_output=True, text=True)

            result = check(NOW)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(signal.read_text())["status"], "GREEN")
            self.assertEqual(json.loads(signal.read_text())["metrics"]["newest_event_age_h"], 23)
            # Rebuilding tomorrow cannot refresh the original scheduled event.
            self.assertEqual(check("2026-10-06T13:00:00Z").returncode, 1)
            self.assertEqual(json.loads(signal.read_text())["code"], "EVENT_STALE")


if __name__ == "__main__":
    unittest.main()
