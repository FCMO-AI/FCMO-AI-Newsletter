from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock

from tools import email_live_receipt, verify_live_front_page

ROOT = Path(__file__).resolve().parents[1]


class EmailLiveReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lkg = "a" * 40
        self.stories = json.dumps({"schema": "fcmo-stories-v2", "release_id": "release-1", "stories": []}).encode()
        self.status = json.dumps({"schema": "fcmo-newsroom-status-v2", "release_id": "release-1",
                                  "corpus_digest": "corpus-1", "edition_state": "FRESH"}).encode()
        self.files = {
            "data/stories.v2.json": self.stories,
            "data/newsroom-status.json": self.status,
            "index.html": b"<html>publication</html>",
        }
        self.identity = {
            "schema": "fcmo-deployment-identity-v2", "source_commit": self.lkg,
            "candidate_id": "candidate-1", "release_id": "release-1", "corpus_digest": "corpus-1",
            "critical_files": {path: hashlib.sha256(raw).hexdigest() for path, raw in self.files.items()},
        }

    def fetch(self, url: str, nonce: str) -> bytes:
        path = url.split("/FCMO-AI-Newsletter/", 1)[1]
        if path == "deployment-identity.json":
            return json.dumps(self.identity).encode()
        return self.files[path]

    def collect(self):
        with mock.patch.object(verify_live_front_page, "fetch", side_effect=self.fetch):
            return email_live_receipt.collect("https://example.org/FCMO-AI-Newsletter/", self.lkg)

    def test_reads_only_verified_live_candidate(self):
        identity, stories, status = self.collect()
        self.assertEqual(identity["source_commit"], self.lkg)
        self.assertEqual(stories, self.stories)
        self.assertEqual(status, self.status)

    def test_unpromoted_candidate_cannot_be_emailed(self):
        self.identity["source_commit"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "not the live-verified LKG"):
            self.collect()

    def test_corrupt_live_route_cannot_be_emailed(self):
        self.files["index.html"] = b"corrupt"
        with self.assertRaisesRegex(ValueError, "verification failed"):
            self.collect()

    def test_data_change_after_first_verification_cannot_be_emailed(self):
        calls = {"stories": 0}
        def fetch(url, nonce):
            if url.endswith("data/stories.v2.json"):
                calls["stories"] += 1
                if calls["stories"] > 1:
                    return b"changed"
            return self.fetch(url, nonce)
        with mock.patch.object(verify_live_front_page, "fetch", side_effect=fetch):
            with self.assertRaisesRegex(ValueError, "changed after verification"):
                email_live_receipt.collect("https://example.org/FCMO-AI-Newsletter/", self.lkg)

    def test_workflow_has_daily_retry_and_uses_verified_v2_input(self):
        workflow = (ROOT / ".github/workflows/dispatch-email.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '35 12 * * *'", workflow)
        self.assertIn("cron: '35 13 * * *'", workflow)
        self.assertIn("refs/tags/lkg^{commit}", workflow)
        self.assertIn("tools/email_live_receipt.py", workflow)
        self.assertIn("email-edition/stories.v2.json", workflow)
        self.assertNotIn("--stories site/data/stories.json", workflow)


if __name__ == "__main__":
    unittest.main()
