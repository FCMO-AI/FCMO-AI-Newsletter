from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_ready_receipt as receipt


class StaticPaperReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.candidate = self.root / "publish"
        (self.candidate / "data").mkdir(parents=True)
        (self.candidate / "assets" / "story-media").mkdir(parents=True)
        self.stories = self.root / "stories.v2.json"
        self.status = self.root / "newsroom-status.json"
        self.stories.write_text(json.dumps({
            "schema": "fcmo-stories-v2",
            "generated_at": "2026-09-26T12:00:00Z",
            "release_id": "newswire-example",
            "stories": [
                {"id": "FCMO-000000000001", "status": "live"},
                {"id": "FCMO-000000000002", "status": "withdrawn"},
            ],
        }) + "\n", encoding="utf-8")
        self.status.write_text(json.dumps({
            "schema": "fcmo-newsroom-status-v2",
            "edition_date": "2026-09-26",
            "edition_state": "CURRENT",
        }) + "\n", encoding="utf-8")
        (self.candidate / "data" / "routes.json").write_text(json.dumps([
            {"path": "", "kind": "front", "locale": "en"},
            {"path": "story/", "kind": "story", "locale": "en"},
            {"path": "es/story/", "kind": "story", "locale": "es-419"},
            {"path": "zh/story/", "kind": "story", "locale": "zh-Hans"},
        ]) + "\n", encoding="utf-8")
        (self.candidate / "data" / "stories.v2.json").write_bytes(self.stories.read_bytes())
        (self.candidate / "data" / "newsroom-status.json").write_bytes(self.status.read_bytes())
        (self.candidate / "index.html").write_text("<!doctype html>\n", encoding="utf-8")
        (self.candidate / "assets" / "story-media" / "lead.svg").write_text("<svg/>\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_measurement_uses_final_routes_and_byte_exact_embedded_data(self) -> None:
        values = receipt.measure_candidate(self.candidate, self.stories, self.status)
        self.assertEqual(values["receipt_schema"], "fcmo-paper-receipt-v1")
        self.assertEqual(values["route_count"], "4")
        self.assertEqual(values["story_route_count"], "3")
        self.assertEqual(values["live_story_count"], "1")
        self.assertEqual(values["route_locales"], "en=2, es-419=1, zh-Hans=1")
        self.assertEqual(values["media_files"], "1")
        self.assertEqual(values["stories_sha256"], receipt.sha256(self.stories.read_bytes()))

    def test_measurement_rejects_nonidentical_embedded_story_layer(self) -> None:
        (self.candidate / "data" / "stories.v2.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "byte-for-byte source copy"):
            receipt.measure_candidate(self.candidate, self.stories, self.status)

    def test_receipt_describes_ssg_contract_not_legacy_overlay(self) -> None:
        values = receipt.measure_candidate(self.candidate, self.stories, self.status)
        text = receipt.render_receipt(values)
        self.assertEqual(receipt.receipt_values(text), values)
        self.assertIn("data/routes.json", text)
        self.assertIn("byte-identical to the Story layer", text)
        self.assertNotIn("release archive SHA-256", text)
        self.assertNotIn("frozen edition routes", text)

    def test_newsroom_receipt_explicitly_excludes_independent_human_editorial_input(self):
        observed = []
        def build(command, **kwargs):
            editorial = Path(command[command.index('--editorial') + 1])
            self.assertTrue(editorial.is_dir())
            self.assertEqual(list(editorial.iterdir()), [])
            observed.append(command)
        with mock.patch.object(receipt, 'read_object', return_value={'base_path': '/paper/'}), mock.patch.object(receipt.subprocess, 'run', side_effect=build), mock.patch.object(receipt, 'measure_candidate', return_value={'newsroom': 'unchanged'}):
            self.assertEqual(receipt.measured_values(), {'newsroom': 'unchanged'})
        self.assertEqual(len(observed), 1)

    def test_cli_write_and_check_keep_existing_exit_semantics(self) -> None:
        values = receipt.measure_candidate(self.candidate, self.stories, self.status)
        output = self.root / "READY_TO_PUBLISH.md"
        with mock.patch.object(receipt, "RECEIPT_PATH", output), mock.patch.object(
            receipt, "measured_values", return_value=values
        ):
            self.assertEqual(receipt.main([]), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), receipt.render_receipt(values))
            self.assertEqual(receipt.main(["--check"]), 0)
            output.write_text(output.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "narrative/structure drift"):
                receipt.main(["--check"])


if __name__ == "__main__":
    unittest.main()
