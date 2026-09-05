from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from tools.airlock_health import inspect, recompute_release_digest
from tools.build_story_wire import disposition, publication_memory_for
from tools.build_visual_desk import render_svg
from tools.prune_locale_packs import prune
from tools.public_research_desk import pick_targets


class AutonomousNewsroomTests(unittest.TestCase):
    def test_story_disposition_keeps_evidence_separate_from_impact(self):
        self.assertEqual(
            disposition({"evidence_class": "D", "confidence": "weak_signal", "importance_effective_score": 10, "status": "active"}),
            "SIGNAL",
        )
        self.assertEqual(
            disposition({"evidence_class": "A", "confidence": "confirmed", "importance_effective_score": 8, "status": "active"}),
            "LEAD",
        )
        self.assertEqual(
            disposition({"evidence_class": "A", "confidence": "confirmed", "importance_effective_score": 4, "status": "active"}),
            "DATABASE_ONLY",
        )

    def test_locale_prune_removes_only_noncanonical_fields(self):
        canonical = {"title": "English", "technical": {"mechanism": "x"}, "claims": [{"text": "c"}]}
        overlay = {
            "title": "Español",
            "engineering_implications": ["private now"],
            "technical": {"mechanism": "mecanismo", "private_note": "no"},
            "claims": [{"text": "afirmación", "secret": "no"}],
        }
        self.assertEqual(
            prune(canonical, overlay),
            {"title": "Español", "technical": {"mechanism": "mecanismo"}, "claims": [{"text": "afirmación"}]},
        )

    def test_airlock_health_distinguishes_delivery_delta_and_starvation(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp)
            (corpus / "index.html").write_text("ok", encoding="utf-8")
            (corpus / "build-manifest.json").write_text("{}\n", encoding="utf-8")
            digest = recompute_release_digest(corpus)
            release = {
                "schema_version": 1,
                "state": "READY",
                "release_id": "FCMO-NEWSWIRE-TEST",
                "corpus_digest_sha256": digest,
                "public_evidence_cutoff": "2026-09-04T20:00:00Z",
                "development_count": 1,
                "semantic_boundary": "default-private-v1",
            }
            transport = {
                "schema_version": 1,
                "state": "DELIVERED",
                "release_id": release["release_id"],
                "corpus_digest_sha256": digest,
                "delivered_at": "2026-09-04T20:30:00Z",
            }
            (corpus / "newsroom-release.json").write_text(json.dumps(release), encoding="utf-8")
            (corpus / "_transport-receipt.json").write_text(json.dumps(transport), encoding="utf-8")
            status = inspect(
                corpus,
                now=dt.datetime(2026, 9, 4, 21, 0, tzinfo=dt.timezone.utc),
                max_age_hours=30,
            )
            self.assertEqual(status["state"], "HEALTHY")
            self.assertEqual(status["public_delta_state"], "PUBLIC_DELTA")
            quiet = inspect(
                corpus,
                now=dt.datetime(2026, 9, 4, 21, 0, tzinfo=dt.timezone.utc),
                max_age_hours=30,
                previous_corpus_digest=digest,
            )
            self.assertEqual(quiet["public_delta_state"], "NO_PUBLIC_DELTA")
            with self.assertRaisesRegex(ValueError, "starvation"):
                inspect(
                    corpus,
                    now=dt.datetime(2026, 9, 7, 21, 0, tzinfo=dt.timezone.utc),
                    max_age_hours=30,
                )

    def test_newspaper_memory_does_not_backdate_a_new_story(self):
        doc = {
            "record": {"id": "FCMO-0123456789AB", "event_at": "2026-09-01T00:00:00Z"},
            "brief": {"event_at": "2026-09-01T00:00:00Z", "last_verified_at": "2026-09-04T20:00:00Z", "status": "active"},
        }
        memory, event = publication_memory_for(
            doc,
            None,
            is_new=True,
            delivered_at="2026-09-04T21:00:00Z",
        )
        self.assertEqual(event, "NEW")
        self.assertEqual(memory["first_published_at"], "2026-09-04T21:00:00Z")
        self.assertEqual(memory["source_event_at"], "2026-09-01T00:00:00Z")
        migrated, migrated_event = publication_memory_for(
            doc,
            None,
            is_new=False,
            delivered_at="2026-09-04T21:00:00Z",
        )
        self.assertEqual(migrated_event, "CURRENT")
        self.assertEqual(migrated["first_published_at"], "2026-09-01T00:00:00Z")

    def test_public_research_prioritizes_new_then_bounded_high_impact_backfill(self):
        briefs = {
            "FCMO-NEW000000001": {"brief": {"importance_effective_score": 4, "last_verified_at": "2026-09-04"}},
            "FCMO-HIGH00000001": {"brief": {"importance_effective_score": 9, "last_verified_at": "2026-09-03"}},
            "FCMO-MID000000001": {"brief": {"importance_effective_score": 6, "last_verified_at": "2026-09-04"}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            targets, backfill = pick_targets(
                briefs,
                ["FCMO-NEW000000001"],
                Path(tmp),
                1,
            )
        self.assertEqual(targets[0], "FCMO-NEW000000001")
        self.assertEqual(backfill, ["FCMO-HIGH00000001"])

    def test_visual_fallback_is_owned_deterministic_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "visual.svg"
            record = {"id": "FCMO-0123456789AB", "title": "A useful public result", "desk": "Models", "evidence": "A", "importance": 8}
            render_svg(record, path)
            first = path.read_text(encoding="utf-8")
            render_svg(record, path)
            second = path.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertIn("FCMO AI NEWSLETTER", first)
            self.assertIn("EVIDENCE A", first)


if __name__ == "__main__":
    unittest.main()
