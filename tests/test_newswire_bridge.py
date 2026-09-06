from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import newswire_bridge

RID = "FCMO-A1B2C3D4E5F6"


class NewswireBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "release"
        self.root.mkdir()
        self._write_safe_release()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, rel: str, text: str = "public") -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _write_safe_release(self) -> None:
        json_paths = {
            "build-manifest.json": {},
            "data/corrections.json": [],
            "data/search.json": [],
            "feed.json": {},
        }
        for rel in newswire_bridge.EXACT_PATHS - {
            "airlock.json",
            "data/developments.jsonl",
            "data/relationships.jsonl",
            "data/locales/es-419/records.json",
            "data/locales/zh-Hans/records.json",
        }:
            if rel.endswith(".json"):
                self._write(rel, json.dumps(json_paths.get(rel, {})))
            elif rel.endswith(".xml"):
                self._write(rel, "<?xml version='1.0'?><root/>")
            else:
                self._write(rel, "public publication surface")
        self._write(
            "data/developments.jsonl",
            json.dumps({"id": RID, "title": "Public story"}) + "\n",
        )
        self._write("data/relationships.jsonl", "")
        for locale in newswire_bridge.LOCALES:
            self._write(
                f"data/locales/{locale}/records.json",
                json.dumps(
                    {
                        "schema": newswire_bridge.LOCALE_SCHEMA,
                        "locale": locale,
                        "records": {RID: {"title": f"Localized {locale}"}},
                    }
                ),
            )
        self._write(f"developments/{RID}.html", "<html>public story</html>")
        self._write("editions/2026-09-05.html", "<html>public edition</html>")
        digest = newswire_bridge.release_digest(self.root)
        self._write(
            "airlock.json",
            json.dumps(
                {
                    "schema": newswire_bridge.AIRLOCK_SCHEMA,
                    "schema_version": 2,
                    "state": newswire_bridge.AIRLOCK_STATE,
                    "release_id": f"newswire-{digest[:24]}",
                    "corpus_digest": digest,
                    "record_count": 1,
                    "declassification_policy_version": 1,
                    "generated_at": "2026-09-06T04:00:00Z",
                    "contract": {
                        "public_only": True,
                        "semantic_declassification": True,
                        "raw_private_source_forbidden": True,
                    },
                }
            ),
        )

    def _restamp(self) -> None:
        digest = newswire_bridge.release_digest(self.root)
        receipt = json.loads((self.root / "airlock.json").read_text(encoding="utf-8"))
        receipt["corpus_digest"] = digest
        receipt["release_id"] = f"newswire-{digest[:24]}"
        (self.root / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")

    def test_safe_release_passes(self) -> None:
        receipt = newswire_bridge.verify_release(self.root)
        self.assertEqual(receipt["record_count"], 1)

    def test_digest_tamper_fails_closed(self) -> None:
        (self.root / "index.html").write_text("changed after receipt", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "corpus digest"):
            newswire_bridge.verify_release(self.root)

    def test_private_marker_fails_even_with_valid_digest(self) -> None:
        (self.root / "index.html").write_text("private ARB context", encoding="utf-8")
        self._restamp()
        with self.assertRaisesRegex(ValueError, "private/implementation/strategic marker"):
            newswire_bridge.verify_release(self.root)

    def test_unallowlisted_file_fails_closed(self) -> None:
        self._write("private-notes.txt", "should never transfer")
        self._restamp()
        with self.assertRaisesRegex(ValueError, "path not allowlisted"):
            newswire_bridge.verify_release(self.root)

    def test_locale_id_sets_must_match(self) -> None:
        doc = json.loads(
            (self.root / "data/locales/zh-Hans/records.json").read_text(encoding="utf-8")
        )
        doc["records"] = {}
        (self.root / "data/locales/zh-Hans/records.json").write_text(
            json.dumps(doc), encoding="utf-8"
        )
        self._restamp()
        with self.assertRaisesRegex(ValueError, "delta ID sets differ"):
            newswire_bridge.verify_release(self.root)

    def test_record_count_must_match_public_jsonl(self) -> None:
        receipt = json.loads((self.root / "airlock.json").read_text(encoding="utf-8"))
        receipt["record_count"] = 2
        (self.root / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "record_count"):
            newswire_bridge.verify_release(self.root)

    def test_stage_replaces_old_corpus_only_after_verification(self) -> None:
        corpus = Path(self.tmp.name) / "corpus"
        corpus.mkdir()
        (corpus / "stale.txt").write_text("old", encoding="utf-8")
        receipt = newswire_bridge.stage_release(self.root, corpus)
        self.assertEqual(receipt["record_count"], 1)
        self.assertFalse((corpus / "stale.txt").exists())
        self.assertTrue((corpus / "airlock.json").is_file())
        newswire_bridge.verify_release(corpus)


if __name__ == "__main__":
    unittest.main()
