from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import build_deployment_identity


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeploymentIdentityTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        site = root / "publish"
        (site / "data").mkdir(parents=True)
        status = {
            "release_id": "newswire-test",
            "corpus_digest": "abc123",
        }
        stories = [{"research_id": "FCMO-AAAAAAAAAAAA"}]
        (site / "data" / "newsroom-status.json").write_text(
            json.dumps(status, sort_keys=True) + "\n", encoding="utf-8"
        )
        (site / "data" / "stories.json").write_text(
            json.dumps(stories, sort_keys=True) + "\n", encoding="utf-8"
        )
        files = {
            "data/newsroom-status.json": digest(site / "data" / "newsroom-status.json"),
            "data/stories.json": digest(site / "data" / "stories.json"),
        }
        (site / "build-manifest.json").write_text(
            json.dumps({"schema_version": 5, "files": files}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return site

    def test_receipt_binds_manifest_status_and_story_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp))
            receipt = build_deployment_identity.build(site, "deadbeef")
            self.assertEqual(receipt["release_id"], "newswire-test")
            self.assertEqual(receipt["story_count"], 1)
            self.assertEqual(receipt["stories_sha256"], digest(site / "data" / "stories.json"))
            self.assertEqual(
                receipt["build_manifest_sha256"], digest(site / "build-manifest.json")
            )

    def test_manifest_story_hash_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp))
            (site / "data" / "stories.json").write_text(
                json.dumps([{"research_id": "FCMO-CHANGEDBYTES"}], sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "does not bind exact"):
                build_deployment_identity.build(site, "deadbeef")


if __name__ == "__main__":
    unittest.main()
