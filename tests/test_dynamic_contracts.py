from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNT_KEY = re.compile(r"\b\d+\s+(?:public\s+)?briefs?\b", re.I)


class DynamicPublicationContractTests(unittest.TestCase):
    def test_corpus_metrics_are_not_frozen_in_the_shell(self):
        text = (ROOT / "release-src" / "index.html").read_text(encoding="utf-8")
        for label in ("count", "evidenceA", "open_gaps", "relationships"):
            self.assertIn(f'data-fcmo-stat="{label}"', text)
        self.assertNotRegex(text, r"<b>\d+</b> public briefs")
        self.assertNotRegex(text, r"<b>\d+</b> open evidence gaps")
        self.assertNotRegex(text, r"<b>\d+</b> explicit relationships")
        self.assertNotRegex(text, r">\d+ BRIEFS<")
        self.assertIn("${D.meta.count} BRIEFS", text)
        self.assertNotRegex(text, r"<span>\d+</span><strong>Research briefs</strong>")

    def test_curated_catalogues_cannot_embed_live_brief_counts(self):
        required = {
            "Evidence distribution",
            "That standalone route does not exist. Use the publication navigation above.",
            "Curated dossier · English canonical source",
            "This view translates the full dossier. Use the English version for the canonical semantic source.",
        }
        for locale in ("es-419", "zh-Hans"):
            data = json.loads((ROOT / "site" / "data" / "i18n" / locale / "ui.json").read_text(encoding="utf-8"))
            keys = set(data["ui"])
            self.assertTrue(required <= keys, (locale, sorted(required - keys)))
            self.assertFalse([key for key in keys if COUNT_KEY.search(key)], locale)
            self.assertNotIn("Evidence distribution / 22 briefs", keys)

    def test_public_operational_docs_no_longer_describe_prelaunch(self):
        receipt_builder = (ROOT / "tools" / "build_ready_receipt.py").read_text(encoding="utf-8")
        self.assertNotIn("Change the repository visibility from **Private** to **Public**", receipt_builder)
        self.assertNotIn("The private repository is staged", receipt_builder)
        policy = (ROOT / "PUBLICATION_POLICY.md").read_text(encoding="utf-8")
        for token in ("corpus/", "site/", "release-src/", "release-overlay/final/", "publish/"):
            self.assertIn(token, policy)
        manifest = json.loads((ROOT / "release-overlay" / "final" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("Private integration", manifest.get("launch_gate", ""))


if __name__ == "__main__":
    unittest.main()
