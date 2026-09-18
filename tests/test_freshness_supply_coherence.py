"""Regression coverage for the evidence-only freshness supply coherence observer."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "freshness_supply_coherence",
    ROOT / "tools" / "freshness_supply_coherence.py",
)
observer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(observer)

NOW = datetime(2026, 9, 18, 6, 0, tzinfo=timezone.utc)


class FreshnessSupplyCoherenceTests(unittest.TestCase):
    def fixture(
        self,
        *,
        story_age_h: float,
        edition_age_h: float | None,
        related_ids: list[str] | None = None,
        native_complete: bool = False,
        numbered_sections: int = 1,
    ) -> dict[str, Path]:
        temp = tempfile.TemporaryDirectory(prefix="fcmo-freshness-cut-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        stories = root / "site/data/stories.json"
        memory = root / "release-src/data/publication-memory.json"
        editions = root / "release-src/data/editions"
        locales = root / "site/data/i18n"
        stories.parent.mkdir(parents=True)
        editions.mkdir(parents=True)
        for locale in observer.LOCALES:
            (locales / locale).mkdir(parents=True)

        story_at = NOW - timedelta(hours=story_age_h)
        stories.write_text(
            json.dumps([
                {
                    "research_id": "FCMO-AAAAAAAAAAAA",
                    "published_at": story_at.isoformat(),
                    "modified_at": story_at.isoformat(),
                    "news_value": {"importance": 6},
                }
            ]),
            encoding="utf-8",
        )

        if edition_age_h is None:
            memory.write_text("[]", encoding="utf-8")
        else:
            edition_at = NOW - timedelta(hours=edition_age_h)
            date = edition_at.date().isoformat()
            preamble = [{"type": "p", "text": f"Published {edition_at.isoformat()}"}]
            memory.write_text(
                json.dumps([{
                    "date": date,
                    "published": True,
                    "authority": "published_edition",
                    "preamble": preamble,
                    "sections": [],
                    "related_brief_ids": related_ids or [],
                }]),
                encoding="utf-8",
            )
            sections = [
                {"title": f"{i + 1}. Signal {i + 1}", "blocks": [{"type": "p", "text": "public"}]}
                for i in range(numbered_sections)
            ]
            (editions / f"{date}.json").write_text(
                json.dumps({
                    "date": date,
                    "published": True,
                    "authority": "published_edition",
                    "preamble": preamble,
                    "sections": sections,
                    "related_brief_ids": related_ids or [],
                }),
                encoding="utf-8",
            )

        for locale in observer.LOCALES:
            ids = related_ids or []
            if not native_complete:
                ids = []
            (locales / locale / "part-001.json").write_text(
                json.dumps({"records": {rid: {"title": "x"} for rid in ids}}),
                encoding="utf-8",
            )
        return {
            "stories": stories,
            "memory": memory,
            "editions": editions,
            "locales": locales,
        }

    def run_observer(self, fixture: dict[str, Path]) -> dict:
        return observer.observe(
            stories_path=fixture["stories"],
            publication_memory_path=fixture["memory"],
            editions_dir=fixture["editions"],
            locales_root=fixture["locales"],
            now=NOW,
            acceptable_hours=48.0,
            minimum_importance=4,
        )

    def test_fresh_story_supply_wins_without_upstream_inference(self) -> None:
        result = self.run_observer(self.fixture(story_age_h=2, edition_age_h=1))
        self.assertEqual(result["state"], "STORY_SUPPLY_FRESH")
        self.assertEqual(result["claim_boundary"]["release_gate_implication"], "NONE")

    def test_stale_story_without_publication_stays_upstream_unknown(self) -> None:
        result = self.run_observer(self.fixture(story_age_h=60, edition_age_h=None))
        self.assertEqual(result["state"], "STORY_STALE_UPSTREAM_PUBLICATION_UNKNOWN")

    def test_newer_published_signal_without_stable_identity_is_unbound(self) -> None:
        result = self.run_observer(self.fixture(story_age_h=60, edition_age_h=10, related_ids=[]))
        self.assertEqual(result["state"], "UPSTREAM_PUBLICATION_NEWER_UNBOUND")
        self.assertFalse(result["representation"]["stable_related_story_ids"])

    def test_bound_signal_without_native_coverage_is_not_laundered_to_eligible(self) -> None:
        result = self.run_observer(
            self.fixture(
                story_age_h=60,
                edition_age_h=10,
                related_ids=["FCMO-BBBBBBBBBBBB"],
                native_complete=False,
            )
        )
        self.assertEqual(result["state"], "UPSTREAM_PUBLICATION_NEWER_BOUND_UNLOCALIZED")
        self.assertEqual(
            result["representation"]["missing_native_locales_by_id"]["FCMO-BBBBBBBBBBBB"],
            ["es-419", "zh-Hans"],
        )

    def test_bound_native_complete_signal_reports_representation_only(self) -> None:
        result = self.run_observer(
            self.fixture(
                story_age_h=60,
                edition_age_h=10,
                related_ids=["FCMO-BBBBBBBBBBBB"],
                native_complete=True,
            )
        )
        self.assertEqual(result["state"], "UPSTREAM_PUBLICATION_NEWER_BOUND_AND_LOCALIZED")
        self.assertTrue(result["representation"]["all_related_ids_native_complete"])
        self.assertEqual(result["claim_boundary"]["release_gate_implication"], "NONE")

    def test_old_upstream_publication_does_not_fake_current_supply(self) -> None:
        result = self.run_observer(self.fixture(story_age_h=72, edition_age_h=60))
        self.assertEqual(result["state"], "STORY_STALE_NO_NEWER_RECENT_PUBLICATION")


if __name__ == "__main__":
    unittest.main()
