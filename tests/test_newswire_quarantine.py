"""One defective record must never block the whole newswire release (incident inc-6019d1f2).

2026-10-16: ARB re-sent two bad records (blank claim label, Chinese es-419 prose); the bridge
refused the entire release every hour from 11:40Z, so no story landed and the edition went DELAYED.
"""
from __future__ import annotations

import json
import unittest

from tests.test_newswire_bridge import RID, RID2, RID3, NewswireBridgeTests
from tools import newswire_bridge, newswire_bridge_partial_locales as partial, wire_status


class QuarantineTests(unittest.TestCase):
    # Borrow only the release fixture helpers; the parent's tests are not re-run.
    setUp = NewswireBridgeTests.setUp
    tearDown = NewswireBridgeTests.tearDown
    _write = NewswireBridgeTests._write
    _write_safe_release = NewswireBridgeTests._write_safe_release
    _restamp = NewswireBridgeTests._restamp

    def _poison(self) -> None:
        rows = [
            {"id": RID, "title": "Good story", "claims": [{"label": "CLAIMED", "text": "ok"}]},
            {"id": RID2, "title": "Blank label", "claims": [{"label": "", "text": "unclassified"}]},
            {"id": RID3, "title": "Chinese es pack", "claims": [{"label": "CLAIMED", "text": "ok"}]},
        ]
        self._write("data/developments.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
        for rid in (RID2, RID3):
            self._write(f"developments/{rid}.html", "<html>story</html>")
        for locale in newswire_bridge.LOCALES:
            recs = {rid: {"title": f"Localized {locale}"} for rid in (RID, RID2, RID3)}
            if locale == "es-419":
                recs[RID3]["title"] = "机器人护栏提高遥操作成功率"
            self._write(
                f"data/locales/{locale}/records.json",
                json.dumps({"schema": newswire_bridge.LOCALE_SCHEMA, "locale": locale, "records": recs}),
            )
        receipt = json.loads((self.root / "airlock.json").read_text(encoding="utf-8"))
        receipt["record_count"] = 3
        (self.root / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")
        self._restamp()

    def test_bad_records_are_quarantined_and_the_rest_of_the_release_passes(self) -> None:
        self._poison()
        with self.assertRaises(ValueError):  # the unquarantined release is refused as before
            partial.verify_release(self.root)
        self.assertEqual(partial.quarantine_release(self.root), sorted([RID2, RID3]))
        receipt = partial.verify_release(self.root)  # must now pass
        self.assertEqual(receipt["record_count"], 1)
        ids = [json.loads(x)["id"] for x in (self.root / "data/developments.jsonl").read_text().splitlines()]
        self.assertEqual(ids, [RID])
        for locale in newswire_bridge.LOCALES:
            doc = json.loads((self.root / f"data/locales/{locale}/records.json").read_text())
            self.assertEqual(sorted(doc["records"]), [RID])

    def test_orphan_pages_of_quarantined_records_are_removed(self) -> None:
        self._poison()
        partial.quarantine_release(self.root)
        self.assertFalse((self.root / f"developments/{RID2}.html").exists())
        self.assertFalse((self.root / f"developments/{RID3}.html").exists())
        self.assertTrue((self.root / f"developments/{RID}.html").exists())

    def test_provenance_of_the_original_seal_is_kept(self) -> None:
        self._poison()
        original = json.loads((self.root / "airlock.json").read_text())
        partial.quarantine_release(self.root)
        sealed = json.loads((self.root / "airlock.json").read_text())
        self.assertEqual(sealed["quarantined_from"], {
            "release_id": original["release_id"], "corpus_digest": original["corpus_digest"],
            "ids": sorted([RID2, RID3])})

    def test_tampered_bytes_are_never_resealed(self) -> None:
        self._poison()
        (self.root / "editions/2026-09-05.html").write_text("<html>TAMPERED</html>", encoding="utf-8")  # no restamp
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(ValueError, "do not match the original receipt"):
            partial.quarantine_release(self.root)
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)  # nothing mutated

    def test_clean_release_quarantines_nothing(self) -> None:
        self.assertEqual(partial.quarantine_release(self.root), [])
        partial.verify_release(self.root)

    def test_structural_defects_still_refuse_the_release(self) -> None:
        self._poison()
        partial.quarantine_release(self.root)
        self._write("data/secret.txt", "not an allowed public path")
        self._restamp()
        with self.assertRaises(ValueError):
            partial.verify_release(self.root)

    def test_wire_status_lists_quarantined_ids(self) -> None:
        doc = wire_status.build_wire_status(
            None, run_at="2026-10-16T23:00:00Z", run_id=None, trigger="local", drill=None, transport="OK",
            transport_error=None, source_mode="MAIN", arb_failures=[], checkpoint_at=None,
            airlock={"release_id": "newswire-" + "a" * 24, "corpus_digest": "a" * 64, "record_count": 1,
                     "generated_at": "2026-10-16T22:00:00Z"},
            newest_event="2026-10-16T00:00:00Z",
            guard={"verdict": "OK", "missing": [], "withdrawn": [], "added": 0, "ratio": 0.0},
            release_changed=True, quarantined=[RID3, RID2],
        )
        self.assertEqual(doc["quarantined"], sorted([RID2, RID3]))
        self.assertEqual(wire_status.wire_errors(doc), [])


class WorkflowWiringTests(unittest.TestCase):
    def test_bridge_quarantines_before_it_verifies(self) -> None:
        from pathlib import Path
        text = (Path(__file__).resolve().parents[1] / ".github/workflows/newswire-bridge.yml").read_text()
        step = text.split("Independently verify the airlocked bytes", 1)[1].split("- name:", 1)[0]
        self.assertIn("newswire_bridge_partial_locales.py quarantine", step)
        self.assertLess(step.index(" quarantine "), step.index(" verify "))
        self.assertIn('--quarantined "$CODES/quarantined"', text)


if __name__ == "__main__":
    unittest.main()
