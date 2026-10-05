"""Production health must exercise the deployed SSG, including a delayed LKG."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import test_deployment_identity
from tools import build_deployment_identity, verify_live_newsroom
from tools import editorial_freshness
from tests.oraculos import verificar_live_surfaces


class PaperServingHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = test_deployment_identity.DeploymentIdentityTests().fixture(self.root)
        # The public umbrella brand is FCMO; no retired publication-name marker.
        (self.site / "index.html").write_text('<title>FCMO</title><h1>Current lead</h1>')
        self.identity = build_deployment_identity.build(self.site, "deployed-lkg")
        (self.site / "deployment-identity.json").write_text(json.dumps(self.identity))

    def fetch(self, url):
        route = url.split("https://example/", 1)[1].split("?", 1)[0] or "index.html"
        if route.endswith("/"):
            route += "index.html"
        path = self.site / route
        if path.is_file():
            return path.read_bytes()
        # Noncritical current reader routes are available in this fixture.
        return b"<html>Reader route</html>"

    def run_health(self):
        signal = self.root / "signal.json"
        with mock.patch.object(verify_live_newsroom, "fetch", side_effect=self.fetch), contextlib.redirect_stdout(io.StringIO()):
            rc = verify_live_newsroom.main([
                "--paper", "--serving-only", "--base-url", "https://example",
                "--identity-timeout-s", "0", "--signal-out", str(signal),
                # A newer checkout must not invalidate a correctly served LKG.
                "--status", str(self.root / "newer-unpublished-status.json"),
            ])
        return rc, json.loads(signal.read_text())

    def test_current_paper_serves_without_retired_name_or_legacy_routes(self):
        rc, signal = self.run_health()
        self.assertEqual(rc, 0)
        self.assertEqual((signal["status"], signal["code"]), ("GREEN", "OK"))
        self.assertEqual(signal["metrics"]["candidate_id"], self.identity["candidate_id"])

    def test_changed_critical_story_bytes_fail_closed(self):
        (self.site / "data/stories.v2.json").write_text('{"stories":[]}')
        rc, signal = self.run_health()
        self.assertEqual(rc, 1)
        self.assertEqual(signal["code"], "IDENTITY_MISMATCH")

    def test_empty_or_forged_identity_cannot_make_serving_green(self):
        self.identity["critical_files"] = {}
        (self.site / "deployment-identity.json").write_text(json.dumps(self.identity))
        rc, signal = self.run_health()
        self.assertEqual(rc, 1)
        self.assertEqual(signal["code"], "IDENTITY_MISMATCH")

    def test_current_health_workflow_checks_paper_instead_of_signal_field(self):
        text = (Path(__file__).resolve().parents[1] / ".github/workflows/newsroom-health.yml").read_text()
        self.assertIn("verify_live_newsroom.py --serving-only --paper", text)
        self.assertIn("run: python tests/oraculos/verificar_live_surfaces.py --paper", text)

    def test_paper_browser_oracle_rejects_a_wrong_rendered_language(self):
        story = {"id": "FCMO-AAAAAAAAAAAA", "url_date": "2026-09-26", "slug": "identity-story"}
        failures = []
        with mock.patch.object(verificar_live_surfaces, "render", return_value='<html lang="en"><h1>Lead</h1></html>'):
            verificar_live_surfaces.check_paper_surfaces("browser", "https://example/", self.identity,
                                                        [story], {"state": "DELAYED"}, failures)
        self.assertTrue(any("es-419" in failure for failure in failures))

    def test_editorial_health_cannot_use_a_recent_withdrawn_story(self):
        stories = self.site / "data/stories.v2.json"
        stories.write_text(json.dumps({"schema": "fcmo-stories-v2", "stories": [
            {"id": "FCMO-AAAAAAAAAAAA", "status": "live", "event_at": "2026-09-11T00:00:00Z"},
            {"id": "FCMO-BBBBBBBBBBBB", "status": "withdrawn", "event_at": "2026-10-05T00:00:00Z"},
        ]}))
        signal = self.root / "editorial.json"
        with contextlib.redirect_stdout(io.StringIO()):
            rc = editorial_freshness.main(["check", "--stories", str(stories),
                "--now", "2026-10-05T05:00:00Z", "--signal-out", str(signal)])
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads(signal.read_text())["metrics"]["newest_event_at"], "2026-09-11T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
