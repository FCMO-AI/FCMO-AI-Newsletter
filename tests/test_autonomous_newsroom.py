from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools import build_newsroom_surfaces, newsroom_receipt, translation_freshness, visual_desk


RID = "FCMO-0C0DE0000001"
NOW = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def record() -> dict:
    return {
        "id": RID,
        "title": "Synthetic public research result",
        "summary": "A measured public result improved by 12%.",
        "why_it_matters": "It changes a public engineering tradeoff.",
        "primary_desk": "evaluation_science",
        "evidence_class": "A",
        "confidence": "confirmed",
        "importance_score": 6,
        "importance_effective_score": 6,
        "recorded_at": NOW,
        "last_verified_at": NOW,
        "claims": [{"label": "DEMONSTRATED", "text": "The public result improved by 12%."}],
        "technical": {"strongest_baseline": "The previous public baseline."},
        "limitations": ["Small public test set."],
        "contradictory_evidence": [],
        "evidence_gaps": [{"description": "Independent reproduction remains open."}],
        "source_urls": ["https://example.com/public-source"],
    }


def write_index(path: Path, row: dict) -> None:
    path.write_text(
        '<html><body><nav></nav><script id="fcmo-data" type="application/json">' +
        json.dumps({"records": [row]}) +
        '</script></body></html>',
        encoding="utf-8",
    )


def write_locale(root: Path, locale: str, row: dict) -> None:
    folder = root / locale
    folder.mkdir(parents=True, exist_ok=True)
    translated = {
        "title": f"[{locale}] {row['title']}",
        "summary": f"[{locale}] {row['summary']}",
        "why_it_matters": f"[{locale}] {row['why_it_matters']}",
        "claims": [{"text": f"[{locale}] {row['claims'][0]['text']}"}],
        "technical": {"strongest_baseline": f"[{locale}] {row['technical']['strongest_baseline']}"},
        "limitations": [f"[{locale}] {row['limitations'][0]}"],
        "contradictory_evidence": [],
        "evidence_gaps": [{"description": f"[{locale}] {row['evidence_gaps'][0]['description']}"}],
    }
    (folder / "part-01.json").write_text(
        json.dumps({"schema": "fcmo-curated-locale-part-v1", "locale": locale, "records": {RID: translated}}),
        encoding="utf-8",
    )


class AutonomousNewsroomTests(unittest.TestCase):
    def test_changed_existing_story_invalidates_translation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "release-src"
            site.mkdir()
            row = record()
            write_index(site / "index.html", row)
            i18n = root / "i18n"
            write_locale(i18n, "es-419", row)
            write_locale(i18n, "zh-Hans", row)
            manifest = root / "source-digests.json"
            manifest.write_text(
                json.dumps({"schema": "fcmo-translation-source-digests-v1", "records": {RID: "old-digest"}}),
                encoding="utf-8",
            )

            self.assertEqual(translation_freshness.invalidate(site, i18n, manifest), 0)
            for locale in ("es-419", "zh-Hans"):
                value = json.loads((i18n / locale / "part-01.json").read_text(encoding="utf-8"))
                self.assertNotIn(RID, value["records"])

    def test_visual_desk_offline_generates_original_safe_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release = root / "release-src"
            briefs = release / "data" / "briefs"
            briefs.mkdir(parents=True)
            (release / "data" / "media.json").write_text("[]\n", encoding="utf-8")
            (briefs / f"{RID}.json").write_text(json.dumps({"brief": record()}), encoding="utf-8")
            site = root / "site"
            site.mkdir()

            self.assertEqual(visual_desk.main(["--release-src", str(release), "--site", str(site), "--offline"]), 0)
            media = json.loads((release / "data" / "media.json").read_text(encoding="utf-8"))
            self.assertEqual(media[0]["mode"], "fcmo_explainer")
            self.assertFalse(media[0]["evidence_image"])
            asset = site / "assets" / "story-media" / f"{RID}.svg"
            self.assertTrue(asset.is_file())
            self.assertIn("not source evidence", asset.read_text(encoding="utf-8"))

    def test_story_layer_emits_three_static_locales_jsonld_and_news_sitemap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release = root / "release-src"
            briefs = release / "data" / "briefs"
            research = release / "data" / "public-research"
            briefs.mkdir(parents=True)
            research.mkdir(parents=True)
            row = record()
            (briefs / f"{RID}.json").write_text(json.dumps({"brief": row}), encoding="utf-8")
            (release / "data" / "media.json").write_text(json.dumps([{
                "id": RID, "mode": "fcmo_explainer", "sourced": False,
                "image_url": f"/FCMO-AI-Newsletter/assets/story-media/{RID}.svg",
                "credit": "FCMO AI Research Desk", "license": "FCMO original editorial graphic"
            }]), encoding="utf-8")
            (research / f"{RID}.json").write_text(json.dumps({
                "schema": "fcmo-public-research-receipt-v1", "id": RID,
                "related_public_sources": [{"url": "https://example.org/context"}]
            }), encoding="utf-8")
            write_index(release / "index.html", row)

            site = root / "site"
            (site / "data" / "i18n").mkdir(parents=True)
            write_locale(site / "data" / "i18n", "es-419", row)
            write_locale(site / "data" / "i18n", "zh-Hans", row)

            self.assertEqual(build_newsroom_surfaces.main(["--release-src", str(release), "--site", str(site)]), 0)
            for locale in ("en", "es", "zh-hans"):
                page = site / "news" / locale / f"{RID}.html"
                self.assertTrue(page.is_file())
                text = page.read_text(encoding="utf-8")
                self.assertIn("NewsArticle", text)
                self.assertIn("hreflang=", text)
                self.assertIn("FCMO AI Research Desk", text)
            self.assertTrue((site / "news-sitemap.xml").is_file())
            self.assertIn("FCMO WIRE", (release / "index.html").read_text(encoding="utf-8"))

    def test_airlock_quiet_delta_is_distinct_from_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus"
            (corpus / "developments").mkdir(parents=True)
            (corpus / "index.html").write_text("ok", encoding="utf-8")
            receipt = {
                "schema": "fcmo-newswire-airlock-v2", "state": "READY_FOR_PUBLICATION",
                "release_id": "newswire-test", "corpus_digest": "abc", "record_count": 1,
                "generated_at": NOW,
            }
            (corpus / "airlock.json").write_text(json.dumps(receipt), encoding="utf-8")

            release = root / "release-src"
            (release / "data" / "briefs").mkdir(parents=True)
            (release / "data" / "briefs" / f"{RID}.json").write_text(json.dumps({"brief": record()}), encoding="utf-8")
            (release / "data" / "media.json").write_text(json.dumps([{"id": RID}]), encoding="utf-8")
            site = root / "site"
            (site / "data" / "i18n").mkdir(parents=True)
            write_locale(site / "data" / "i18n", "es-419", record())
            write_locale(site / "data" / "i18n", "zh-Hans", record())
            (site / "data" / "stories.json").write_text(json.dumps([{"research_id": RID}]), encoding="utf-8")
            status = site / "data" / "newsroom-status.json"

            args = type("Args", (), {
                "corpus": corpus, "release_src": release, "site": site,
                "status": status, "max_age_hours": 36, "github_output": None,
            })()
            self.assertEqual(newsroom_receipt.preflight(args), 0)
            self.assertEqual(newsroom_receipt.finalize(args), 0)
            first = json.loads(status.read_text(encoding="utf-8"))
            self.assertEqual(first["state"], "PUBLIC_DELTA_READY")
            self.assertEqual(newsroom_receipt.finalize(args), 0)
            second = json.loads(status.read_text(encoding="utf-8"))
            self.assertEqual(second["state"], "NO_PUBLIC_DELTA_READY")

            missing_args = type("Args", (), {
                "corpus": root / "missing", "release_src": release, "site": site,
                "status": status, "max_age_hours": 36, "github_output": None,
            })()
            with self.assertRaises(ValueError):
                newsroom_receipt.preflight(missing_args)


if __name__ == "__main__":
    unittest.main()
