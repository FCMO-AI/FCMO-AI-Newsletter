from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools import (
    build_editorial_frontends,
    build_newsroom_surfaces,
    finalize_editorial_frontends,
    newsroom_receipt,
    sync_airlocked_locales,
    validate_localizations,
    visual_desk,
)


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
        "topics": ["agent-evaluation"],
        "organizations": ["Example Lab"],
    }


def write_index(path: Path, row: dict) -> None:
    path.write_text(
        '<html><body><nav></nav><script id="fcmo-data" type="application/json">' +
        json.dumps({"records": [row]}) +
        '</script></body></html>',
        encoding="utf-8",
    )


def translated_row(locale: str, row: dict) -> dict:
    if locale == "zh-Hans":
        return {
            "title": "合成公共研究结果",
            "summary": "一项公开测量结果提高了 12%。",
            "why_it_matters": "这改变了一个公开的工程权衡。",
            "claims": [{"text": "公开结果提高了 12%。"}],
            "technical": {"strongest_baseline": "此前的公开基线。"},
            "limitations": ["公开测试集较小。"],
            "contradictory_evidence": [],
            "evidence_gaps": [{"description": "独立复现仍待完成。"}],
        }
    return {
        "title": "Resultado sintético de investigación pública",
        "summary": "Un resultado público medido mejoró 12%.",
        "why_it_matters": "Cambia una disyuntiva pública de ingeniería.",
        "claims": [{"text": "El resultado público mejoró 12%."}],
        "technical": {"strongest_baseline": "La línea base pública anterior."},
        "limitations": ["Conjunto público de prueba pequeño."],
        "contradictory_evidence": [],
        "evidence_gaps": [{"description": "La reproducción independiente sigue pendiente."}],
    }


def write_locale(root: Path, locale: str, row: dict) -> None:
    folder = root / locale
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "part-01.json").write_text(
        json.dumps({
            "schema": "fcmo-curated-locale-part-v1",
            "locale": locale,
            "records": {RID: translated_row(locale, row)},
        }),
        encoding="utf-8",
    )


class AutonomousNewsroomTests(unittest.TestCase):
    def test_historical_native_editions_pass_truthful_provider_free_integrity_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "release-src"
            site.mkdir()
            row = record()
            write_index(site / "index.html", row)
            i18n = root / "i18n"
            write_locale(i18n, "es-419", row)
            write_locale(i18n, "zh-Hans", row)
            receipt = root / "integrity.json"

            self.assertEqual(validate_localizations.main([
                "--site", str(site), "--i18n-dir", str(i18n), "--receipt", str(receipt)
            ]), 0)
            value = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertIn("ARB publication agent", value["editorial_owner"])
            self.assertFalse(value["network_translation"])
            self.assertFalse(value["human_reviewed"])
            self.assertEqual(value["historical_structural_pairs"], 2)
            self.assertEqual(value["strict_airlock_pairs"], 0)

    def test_missing_upstream_native_edition_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "release-src"
            site.mkdir()
            row = record()
            write_index(site / "index.html", row)
            i18n = root / "i18n"
            write_locale(i18n, "es-419", row)
            (i18n / "zh-Hans").mkdir(parents=True)
            with self.assertRaisesRegex(SystemExit, "missing canonical ids"):
                validate_localizations.main(["--site", str(site), "--i18n-dir", str(i18n)])

    def test_airlocked_locale_delta_becomes_strict_generated_locale_part(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus"
            i18n = root / "i18n"
            site = root / "release-src"
            site.mkdir()
            row = record()
            write_index(site / "index.html", row)
            for locale in ("es-419", "zh-Hans"):
                incoming = corpus / "data" / "locales" / locale
                incoming.mkdir(parents=True, exist_ok=True)
                (incoming / "records.json").write_text(json.dumps({
                    "schema": "fcmo-airlocked-locale-delta-v1",
                    "locale": locale,
                    "canonical_locale": "en",
                    "records": {RID: translated_row(locale, row)},
                }), encoding="utf-8")
                (i18n / locale).mkdir(parents=True, exist_ok=True)

            self.assertEqual(sync_airlocked_locales.main([
                "--corpus", str(corpus), "--i18n-dir", str(i18n)
            ]), 0)
            for locale in ("es-419", "zh-Hans"):
                value = json.loads((i18n / locale / "part-airlock.json").read_text(encoding="utf-8"))
                self.assertIn(RID, value["records"])
            receipt = root / "integrity.json"
            self.assertEqual(validate_localizations.main([
                "--site", str(site), "--i18n-dir", str(i18n), "--receipt", str(receipt)
            ]), 0)
            value = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(value["strict_airlock_pairs"], 2)
            self.assertEqual(value["historical_structural_pairs"], 0)

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
            self.assertEqual(media[0]["rights_state"], "FCMO_OWNED")
            self.assertFalse(media[0]["evidence_image"])
            asset = site / "assets" / "story-media" / f"{RID}.svg"
            self.assertTrue(asset.is_file())
            self.assertIn("not source evidence", asset.read_text(encoding="utf-8"))

    def test_visual_desk_rejects_unverifiable_licensed_media_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp)
            bogus = [{
                "id": RID,
                "mode": "licensed_source",
                "sourced": True,
                "rights_state": "PERMISSIVE_LICENSE",
                "image_url": "https://example.org/image.jpg",
                "source_page": "https://example.org/story",
                "license_url": "https://example.org/terms",
                "reuse_basis": "someone said reuse is okay",
                "credit": "example.org",
            }]
            # Footnote: a populated rights receipt is not enough. The license URL
            # itself must match a machine-recognized permissive declaration.
            with self.assertRaisesRegex(ValueError, "recognized permissive"):
                visual_desk.validate_media_rows(bogus, {RID}, site)

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
                article = site / "news" / locale / f"{RID}.html"
                self.assertTrue(article.is_file())
                text = article.read_text(encoding="utf-8")
                self.assertIn("NewsArticle", text)
                self.assertIn("hreflang=", text)
                self.assertIn("FCMO AI Research Desk", text)
                self.assertIn('href="../../assets/newsroom.css"', text)
                self.assertNotIn("https://fcmo-ai.github.io/FCMO-AI-Newsletter/assets/newsroom.css", text)
            self.assertTrue((site / "news-sitemap.xml").is_file())
            self.assertTrue((site / "sitemap.xml").is_file())
            sitemap = (site / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn(f"/news/en/{RID}.html", sitemap)
            self.assertIn(f"/news/es/{RID}.html", sitemap)
            self.assertIn(f"/news/zh-hans/{RID}.html", sitemap)
            self.assertIn("FCMO WIRE", (release / "index.html").read_text(encoding="utf-8"))

    def test_editorial_frontends_cover_discovery_status_and_error_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            (site / "data").mkdir(parents=True)
            row = record()
            (site / "data" / "search.json").write_text(json.dumps([row]), encoding="utf-8")
            (site / "data" / "stories.json").write_text(json.dumps([{"research_id": RID}]), encoding="utf-8")
            (site / "data" / "corrections.json").write_text("[]", encoding="utf-8")
            (site / "data" / "newsroom-status.json").write_text(json.dumps({"release_id": "newswire-test"}), encoding="utf-8")

            self.assertEqual(build_editorial_frontends.main(["--site", str(site)]), 0)
            self.assertEqual(finalize_editorial_frontends.main(["--site", str(site)]), 0)
            for name in (
                "archive.html", "search.html", "topics.html", "organizations.html",
                "corrections.html", "feeds.html", "methodology.html", "editorial-policy.html",
                "automation.html", "accessibility.html", "status.html", "404.html",
            ):
                self.assertTrue((site / name).is_file(), name)
            self.assertTrue(any((site / "topics").glob("*.html")))
            self.assertTrue(any((site / "organizations").glob("*.html")))
            archive = (site / "archive.html").read_text(encoding="utf-8")
            self.assertIn(f"/news/en/{RID}.html", archive)
            self.assertNotIn("/news/en/STORY-", archive)

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
