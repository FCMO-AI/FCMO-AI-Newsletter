from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_deployment_identity, verify_live_front_page
from tools.gates.common import canonical_story_path


class DeploymentIdentityTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        site = root / "publish"; (site / "data").mkdir(parents=True)
        story = {"id": "FCMO-AAAAAAAAAAAA", "status": "live", "front_page_eligible": True,
                 "url_date": "2026-09-26", "slug": "identity-story"}
        stories = {"schema": "fcmo-stories-v2", "release_id": "newswire-test", "stories": [story]}
        status = {"release_id": "newswire-test", "corpus_digest": "abc123"}
        (site / "data/stories.v2.json").write_text(json.dumps(stories), encoding="utf-8")
        (site / "data/newsroom-status.json").write_text(json.dumps(status), encoding="utf-8")
        for route in ("index.html", "es/index.html", "zh/index.html"):
            path = site / route; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(f"<html>{route}</html>", encoding="utf-8")
        for locale in ("en", "es-419", "zh-Hans"):
            route = canonical_story_path(story, locale); path = site / route
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(f"<html>{locale}</html>", encoding="utf-8")
        return site

    def test_receipt_binds_tree_and_critical_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp)); receipt = build_deployment_identity.build(site, "deadbeef")
            self.assertEqual(receipt["schema"], "fcmo-deployment-identity-v2")
            self.assertEqual(receipt["release_id"], "newswire-test")
            self.assertEqual(receipt["lead_id"], "FCMO-AAAAAAAAAAAA")
            self.assertEqual(receipt["story_count"], 1)
            self.assertEqual(receipt["critical_files"]["index.html"], hashlib.sha256((site / "index.html").read_bytes()).hexdigest())

    def test_any_candidate_byte_changes_tree_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp)); before = build_deployment_identity.build(site, "deadbeef")
            (site / "asset.css").write_text("body{}", encoding="utf-8")
            after = build_deployment_identity.build(site, "deadbeef")
            self.assertNotEqual(before["tree_sha256"], after["tree_sha256"])
            self.assertNotEqual(before["candidate_id"], after["candidate_id"])

    def test_live_oracle_rejects_stale_public_freshness_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp))
            (site / "status.json").write_text('{"state":"DELAYED"}', encoding="utf-8")
            expected = build_deployment_identity.build(site, "deadbeef")
            self.assertIn("status.json", expected["critical_files"])

            def fetch(url, nonce):
                route = url.rsplit("/FCMO-AI-Newsletter/", 1)[-1]
                if route == "deployment-identity.json": return json.dumps(expected).encode()
                return (site / route).read_bytes()

            with mock.patch.object(verify_live_front_page, "fetch", side_effect=fetch):
                self.assertEqual(verify_live_front_page.verify_once("https://example/FCMO-AI-Newsletter/", expected, "1")[:2], (True, True))
                (site / "status.json").write_text('{"state":"FRESH"}', encoding="utf-8")
                seen, valid, detail = verify_live_front_page.verify_once("https://example/FCMO-AI-Newsletter/", expected, "2")
                self.assertTrue(seen)
                self.assertFalse(valid)
                self.assertIn("status.json", detail)

    def test_live_oracle_requires_expected_identity_and_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = self.fixture(Path(tmp)); expected = build_deployment_identity.build(site, "deadbeef")
            def fetch(url, nonce):
                route = url.rsplit("/FCMO-AI-Newsletter/", 1)[-1]
                if route == "deployment-identity.json": return json.dumps(expected).encode()
                return (site / route).read_bytes()
            with mock.patch.object(verify_live_front_page, "fetch", side_effect=fetch):
                self.assertEqual(verify_live_front_page.verify_once("https://example/FCMO-AI-Newsletter/", expected, "1")[:2], (True, True))
                (site / "index.html").write_text("tampered", encoding="utf-8")
                seen, valid, detail = verify_live_front_page.verify_once("https://example/FCMO-AI-Newsletter/", expected, "2")
                self.assertTrue(seen); self.assertFalse(valid); self.assertIn("index.html", detail)


if __name__ == "__main__": unittest.main()
