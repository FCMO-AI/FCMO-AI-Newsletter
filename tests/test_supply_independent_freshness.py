"""L3: a frozen upstream clock cannot block honest public freshness reporting."""
from __future__ import annotations

import copy
import json
import re
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
from tools.paper.freshness import corpus_freshness
from tools.paper.i18n import load_catalogs
from tools.paper.status_banner import render
from tools.publication_freshness import publication_status

NOW = "2026-10-04T12:00:00Z"


class SupplyIndependentFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        shutil.copytree(ROOT / "contracts/fixtures/corpus-43", self.corpus)
        (self.corpus / "developments").mkdir()
        (self.corpus / "index.html").write_text("fixture")
        self.status = self.root / "newsroom-status.json"
        self.status.write_bytes((ROOT / "site/data/newsroom-status.json").read_bytes())
        self.site = self.root / "site"
        (self.site / "data").mkdir(parents=True)
        (self.site / "data/stories.v2.json").write_bytes((ROOT / "contracts/fixtures/stories.v2.json").read_bytes())
        self.wire = self.root / "wire-status.json"
        self.wire.write_bytes((ROOT / "contracts/fixtures/wire-status.down.json").read_bytes())

    def receipt(self, mode):
        return subprocess.run([sys.executable, "tools/newsroom_receipt.py", mode,
                               "--corpus", str(self.corpus), "--status", str(self.status),
                               "--wire-status", str(self.wire), "--site", str(self.site),
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
        # This outage counterfactual needs stale supply even after production recovers.
        PaperBuilder(stories_path=ROOT / "contracts/fixtures/stories.v2.json", status_path=self.status,
                     out=output, base="/FCMO-AI-Newsletter/").build()
        public_path = output / "status.json"
        self.assertTrue(public_path.is_file(), "public freshness endpoint is missing")
        public = json.loads(public_path.read_text())
        self.assertEqual((public["state"], public["reason"]), ("DELAYED", "STORY_SUPPLY"))
        for prefix in ("", "es/", "zh/"):
            for route in ("diario/", "status/"):
                page = (output / prefix / route / "index.html").read_text()
                self.assertIn('data-edition-state="DELAYED"', page)
                self.assertNotIn('hidden data-edition-state="FRESH"', page)
        self.assertEqual((output / "data/newsroom-status.json").read_bytes(), self.status.read_bytes())
        # Execute the exact generated safeguard. An old edition with a recent
        # successful check must remain QUIET; an abandoned check must warn.
        page = (output / "diario/index.html").read_text()
        script = next(value for value in re.findall(r"<script>(.*?)</script>", page, re.S) if "1296e5" in value)
        program = """const vm = require('node:vm');
const script = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
for (const [checked, expected] of [['2026-10-04T11:00:00Z', 'QUIET'], ['2026-10-02T11:00:00Z', 'DELAYED']]) {
  const banner = {hidden:true, dataset:{editionState:'QUIET', editionAt:'2026-09-18T22:36:23Z', statusUpdatedAt:checked}};
  vm.runInNewContext(script, {Date:{now:()=>Date.parse('2026-10-04T12:00:00Z'), parse:Date.parse},
    document:{querySelector:()=>banner}, location:{hash:''}});
  if (banner.dataset.editionState !== expected || banner.hidden !== (expected === 'QUIET')) process.exit(1);
}
"""
        if shutil.which("node"):
            result = subprocess.run(["node", "-e", program], input=json.dumps(script), text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejected_supply_schema_leaves_last_good_status_untouched(self):
        before = self.status.read_bytes()
        path = self.corpus / "airlock.json"
        receipt = json.loads(path.read_text())
        receipt["schema"] = "unsupported-future-schema"
        path.write_text(json.dumps(receipt))
        result = self.receipt("status")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.status.read_bytes(), before)


class PublicFreshnessContractTests(unittest.TestCase):
    def status(self, wire="FRESH", event="2026-10-02T12:00:00Z", checked=NOW):
        live = [{"id": "FCMO-000000000001", "event_at": event, "first_published_at": event}] if event else []
        base = {"wire_state": wire, "edition_state": wire.split(":")[0],
                "edition_reason": wire.split(":")[1] if ":" in wire else None,
                "status_updated_at": checked, "last_edition_at": "2026-10-02T12:00:00Z",
                "release_id": "newswire-" + "a" * 24, "corpus_digest": "a" * 64}
        public = publication_status(corpus_freshness(live, checked), base)
        return {**base, "publication_status": public}, public

    def test_48_hours_is_inclusive_and_one_second_later_is_delayed(self):
        self.assertEqual(self.status()[1]["state"], "FRESH")
        public = self.status(checked="2026-10-04T12:00:01Z")[1]
        self.assertEqual((public["state"], public["reason"]), ("DELAYED", "STORY_SUPPLY"))

    def test_missing_or_future_dates_never_claim_freshness(self):
        for event, checked, reason in ((None, NOW, "STORY_SUPPLY"),
                                       ("2026-10-04T12:16:00Z", NOW, "CLOCK_SKEW"),
                                       ("2026-10-02T12:00:00Z", None, "STORY_SUPPLY")):
            with self.subTest(event=event, checked=checked):
                public = self.status(event=event, checked=checked)[1]
                self.assertEqual((public["state"], public["reason"]), ("DELAYED", reason))

    def test_fresh_corpus_preserves_upstream_failure_reason(self):
        public = self.status(wire="DELAYED:ARB_MAIN_RED")[1]
        self.assertEqual((public["state"], public["reason"]), ("DELAYED", "ARB_MAIN_RED"))

    def test_all_three_states_use_curated_visible_copy_in_all_locales(self):
        catalogs = load_catalogs(ROOT)
        for wire, event, expected in (("FRESH", "2026-10-04T00:00:00Z", "FRESH"),
                                      ("QUIET", "2026-10-03T00:00:00Z", "QUIET"),
                                      ("FRESH", "2026-09-11T00:00:00Z", "DELAYED")):
            status, public = self.status(wire=wire, event=event)
            self.assertEqual(public["state"], expected)
            for code, prefix in (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/")):
                with self.subTest(state=expected, locale=code):
                    catalog = catalogs[code]
                    output = render(status, catalog, base="/", locale={"path_prefix": prefix})
                    self.assertIn(f'data-edition-state="{expected}"', output)
                    self.assertIn(f'data-status-updated-at="{NOW}"', output)
                    if expected == "FRESH":
                        self.assertIn('class="edition-update"', output)
                    else:
                        key = "quiet" if expected == "QUIET" else "delayed"
                        self.assertIn(catalog["strings"]["edition"][key].split("{date}")[0], output)

    def test_public_status_schema_is_closed_and_rejects_false_freshness(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from harness.validate import validator_for
        validator = validator_for(ROOT / "contracts/publication-status.v1.schema.json")
        _, public = self.status()
        self.assertEqual(validator.errors(public), [])
        forged = {**public, "newest_age_hours": 49}
        self.assertTrue(validator.errors(forged))
        self.assertTrue(validator.errors({**public, "private_debug": "forbidden"}))


if __name__ == "__main__":
    unittest.main()
