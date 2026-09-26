from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import newswire_bridge, newswire_bridge_partial_locales

REPO = Path(__file__).resolve().parents[1]

RID = "FCMO-A1B2C3D4E5F6"
RID2 = "FCMO-0F0E0D0C0B0A"
RID3 = "FCMO-112233445566"


class NewswireBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "release"
        self.root.mkdir()
        self.baseline = Path(self.tmp.name) / "i18n"
        self._write_safe_release()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, rel: str, text: str = "public") -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _write_baseline(self, locale: str, records: dict[str, dict[str, str]]) -> None:
        path = self.baseline / locale / "part-01.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema": newswire_bridge.CURATED_PART_SCHEMA,
                    "locale": locale,
                    "canonical_locale": "en",
                    "records": records,
                }
            ),
            encoding="utf-8",
        )

    def _append_story(self, rid: str) -> None:
        developments = self.root / "data/developments.jsonl"
        developments.write_text(
            developments.read_text(encoding="utf-8")
            + json.dumps({"id": rid, "title": f"Public story {rid}"}) + "\n",
            encoding="utf-8",
        )
        self._write(f"developments/{rid}.html", "<html>new public story</html>")
        receipt = json.loads((self.root / "airlock.json").read_text(encoding="utf-8"))
        receipt["record_count"] += 1
        (self.root / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")
        self._restamp()

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

    def test_equal_but_sparse_locale_sets_fail_closed(self) -> None:
        # Footnote: this is the production race that escaped the older verifier:
        # both locale sets agreed with each other, but a newly promoted English
        # Story existed outside both. Standalone Airlock verification stays strict.
        self._append_story(RID2)
        with self.assertRaisesRegex(ValueError, "native-edition coverage"):
            newswire_bridge.verify_release(self.root)

    def test_sparse_airlock_plus_complete_curated_baseline_passes(self) -> None:
        # Footnote: historical Newsletter editions predate ARB's per-story delta.
        # Their public IDs may satisfy the migration baseline, while the Airlock owns
        # all newly authored/changed editions. The union must cover every Story.
        self._append_story(RID2)
        for locale in newswire_bridge.LOCALES:
            self._write_baseline(
                locale,
                {RID2: {"title": f"Historical curated {locale}"}},
            )
        receipt = newswire_bridge.verify_release(self.root, self.baseline)
        self.assertEqual(receipt["record_count"], 2)

    def test_baseline_plus_delta_still_rejects_a_new_untranslated_story(self) -> None:
        self._append_story(RID2)
        self._append_story(RID3)
        for locale in newswire_bridge.LOCALES:
            self._write_baseline(
                locale,
                {RID2: {"title": f"Historical curated {locale}"}},
            )
        with self.assertRaisesRegex(ValueError, "missing=1"):
            newswire_bridge.verify_release(self.root, self.baseline)

    def test_malformed_curated_baseline_fails_closed(self) -> None:
        self._append_story(RID2)
        for locale in newswire_bridge.LOCALES:
            self._write_baseline(locale, {RID2: {"title": "curated"}})
        path = self.baseline / "es-419" / "part-01.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["schema"] = "wrong-schema"
        path.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "curated locale part contract mismatch"):
            newswire_bridge.verify_release(self.root, self.baseline)

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

    def test_stage_uses_same_baseline_coverage_gate(self) -> None:
        self._append_story(RID2)
        for locale in newswire_bridge.LOCALES:
            self._write_baseline(locale, {RID2: {"title": f"Curated {locale}"}})
        corpus = Path(self.tmp.name) / "corpus"
        receipt = newswire_bridge.stage_release(self.root, corpus, self.baseline)
        self.assertEqual(receipt["record_count"], 2)
        newswire_bridge.verify_release(corpus, self.baseline)


    # --- G10: private markers are matched by salted digest, never kept in clear ---
    def test_source_keeps_no_private_marker_in_clear(self) -> None:
        source = (REPO / "tools" / "newswire_bridge.py").read_text(encoding="utf-8").casefold()
        self.assertNotIn("gmail", source)
        self.assertFalse(hasattr(newswire_bridge, "FORBIDDEN"))
        self.assertNotRegex(source, r"\\barb\\b")

    def test_hashed_markers_keep_word_boundaries(self) -> None:
        for text in ("private ARB context", "ARB-2026-09-01-ABCDEF12", "Hermes\u2013Jarvis", '{"projects": []}',
                     "source head 0123abcd", "the canonical\nrepository"):
            self.assertTrue(newswire_bridge.private_marker(text), text)
        for text in ("carbon arbitrage", "ARBITRARY", "a public research record", "mf20 values"):
            self.assertFalse(newswire_bridge.private_marker(text), text)
        self.assertTrue(newswire_bridge.personal_email("write to someone.else@Gmail.com"))
        self.assertFalse(newswire_bridge.personal_email("press@example.org"))

    def test_personal_email_fails_closed(self) -> None:
        (self.root / "about.html").write_text("contact: someone@outlook.com", encoding="utf-8")
        self._restamp()
        with self.assertRaisesRegex(ValueError, "personal email"):
            newswire_bridge.verify_release(self.root)

    # --- newsroom-owned corpus files ---
    def test_newsroom_files_are_outside_the_digest_but_still_scanned(self) -> None:
        before = newswire_bridge.release_digest(self.root)
        self._write("tombstones.json", json.dumps({"schema": "fcmo-tombstones-v1", "tombstones": []}))
        self._write("first-published.json", json.dumps({"schema": "fcmo-first-published-v1", "entries": {}}))
        self._write("carried.jsonl", json.dumps({"id": RID2}) + "\n")
        self._write("wire-status.json", "{}")
        self.assertEqual(newswire_bridge.release_digest(self.root), before)
        newswire_bridge.verify_release(self.root)
        self._write("wire-status.json", json.dumps({"note": "private ARB context"}))
        with self.assertRaisesRegex(ValueError, "wire-status.json: private/implementation/strategic marker"):
            newswire_bridge.verify_release(self.root)
        self._write("wire-status.json", "{}")
        self._write("carried.jsonl", "{not json\n")
        with self.assertRaisesRegex(ValueError, "carried.jsonl:1: invalid JSONL"):
            newswire_bridge.verify_release(self.root)

    def test_stage_refuses_a_release_that_carries_newsroom_files(self) -> None:
        self._write("tombstones.json", json.dumps({"schema": "fcmo-tombstones-v1", "tombstones": []}))
        with self.assertRaisesRegex(ValueError, "newsroom-owned"):
            newswire_bridge.stage_release(self.root, Path(self.tmp.name) / "corpus")

    # --- corpus guard inside the stage ---
    def _release_with(self, ids: list[str]) -> None:
        self._write("data/developments.jsonl", "".join(json.dumps({"id": i, "title": f"Public story {i}"}) + "\n" for i in ids))
        for path in (self.root / "developments").glob("*.html"):
            path.unlink()
        for rid in ids:
            self._write(f"developments/{rid}.html", "<html>public story</html>")
        for locale in newswire_bridge.LOCALES:
            self._write(f"data/locales/{locale}/records.json", json.dumps({
                "schema": newswire_bridge.LOCALE_SCHEMA, "locale": locale,
                "records": {rid: {"title": f"Localized {locale}"} for rid in ids}}))
        receipt = json.loads((self.root / "airlock.json").read_text(encoding="utf-8"))
        receipt["record_count"] = len(ids)
        (self.root / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")
        self._restamp()

    def _staged_corpus(self, ids: list[str]) -> Path:
        corpus = Path(self.tmp.name) / "corpus"
        self._release_with(ids)
        with contextlib.redirect_stdout(io.StringIO()):
            newswire_bridge.stage_release(self.root, corpus)
        (corpus / "tombstones.json").write_text(json.dumps({"schema": "fcmo-tombstones-v1", "tombstones": []}))
        (corpus / "wire-status.json").write_text("{}")
        return corpus

    IDS = [f"FCMO-00000000000{i}" for i in range(1, 6)]

    def test_stage_carries_a_missing_story_forward(self) -> None:
        corpus = self._staged_corpus(self.IDS)
        previous_release = json.loads((corpus / "airlock.json").read_text())["release_id"]
        self._release_with(self.IDS[1:])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            newswire_bridge_partial_locales.stage_release(self.root, corpus, now="2026-09-26T20:00:00Z")
        self.assertIn(f"CARRY_FORWARD missing={self.IDS[0]} withdrawn=- added=0 published=5 candidate=4 ratio=0.2000",
                      out.getvalue())
        self.assertIn(f"ALERT CORPUS_CARRY_FORWARD missing={self.IDS[0]}", err.getvalue())
        carried = [json.loads(l) for l in (corpus / "carried.jsonl").read_text().splitlines()]
        self.assertEqual(carried, [{"id": self.IDS[0], "carried_since": "2026-09-26T20:00:00Z",
                                    "last_release_id": previous_release,
                                    "record": {"id": self.IDS[0], "title": f"Public story {self.IDS[0]}"}}])
        self.assertTrue((corpus / "tombstones.json").is_file())
        self.assertTrue((corpus / "wire-status.json").is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            newswire_bridge_partial_locales.verify_release(corpus)

    def test_stage_refuses_a_regressing_release_and_writes_nothing(self) -> None:
        corpus = self._staged_corpus(self.IDS)
        before = {p.relative_to(corpus): p.read_bytes() for p in corpus.rglob("*") if p.is_file()}
        self._release_with(self.IDS[2:])
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(newswire_bridge.GuardRefused):
                newswire_bridge.stage_release(self.root, corpus)
        for tool in ("newswire_bridge.py", "newswire_bridge_partial_locales.py"):
            proc = subprocess.run([sys.executable, str(REPO / "tools" / tool), "stage", str(self.root), str(corpus)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3, proc.stderr)
            self.assertIn("REGRESSION_REFUSED", proc.stdout)
            self.assertIn("ALERT CORPUS_REGRESSION_REFUSED missing=2 ratio=0.4000", proc.stderr)
        after = {p.relative_to(corpus): p.read_bytes() for p in corpus.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertEqual(sorted(p.name for p in corpus.parent.iterdir() if p.name.startswith(".corpus")), [])


if __name__ == "__main__":
    unittest.main()
