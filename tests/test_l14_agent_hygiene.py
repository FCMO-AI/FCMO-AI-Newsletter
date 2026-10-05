from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import build_newsroom_surfaces, ingest_corpus


class AgentHygieneSchemaTests(unittest.TestCase):
    def test_freshness_feed_sources_and_nine_localized_jsonld_pages_validate(self):
        from tools import validate_agent_hygiene

        now = "2026-10-04T12:00:00Z"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "news").mkdir()
            (root / "llms.txt").write_text(
                "<!-- generated_at: 2026-10-04T12:00:00Z; stale_after: 2026-10-06T12:00:00Z -->\n## Reading hierarchy (R0–R4)\n",
                encoding="utf-8",
            )
            (root / "llms-full.txt").write_text(
                "<!-- generated_at: 2026-10-04T12:00:00Z; stale_after: 2026-10-06T12:00:00Z -->\n## Reading hierarchy (R0–R4)\n",
                encoding="utf-8",
            )
            briefs = []
            for number in range(1, 4):
                rid = f"FCMO-00000000000{number}"
                source = f"https://primary.example.org/paper/{number}"
                brief = {
                    "id": rid,
                    "title": f"Research result {number}",
                    "summary": f"Summary {number}",
                    "source_urls": [source],
                    "last_verified_at": now,
                    "primary_desk": "evaluation_science",
                    "claims": [],
                }
                row = {
                    "id": rid, "title": brief["title"], "summary": brief["summary"],
                    "event_at": now, "human_url": f"https://example.org/news/{rid}.html",
                    "topics": [], "evidence": "A", "confidence": "supported", "importance": 5,
                }
                briefs.append((brief, row, source))
                citation_url, citation = build_newsroom_surfaces.citation_record(
                    brief, f"https://fcmo-ai.github.io/FCMO-AI-Newsletter/news/en/{rid}.html"
                )
                citation_path = root / "data" / "citations" / rid / f"{citation['version']}.json"
                citation_path.parent.mkdir(parents=True, exist_ok=True)
                citation_path.write_text(json.dumps(citation), encoding="utf-8")
                for locale, route in (("en", "en"), ("es-419", "es"), ("zh-Hans", "zh-hans")):
                    url = f"https://fcmo-ai.github.io/FCMO-AI-Newsletter/news/{route}/{rid}.html"
                    story = {"published_at": now, "modified_at": now, "event_at": now,
                             "story_type": "STANDARD", "public_research": {}}
                    html = build_newsroom_surfaces.article_html(
                        locale, brief, story,
                        {key: f"https://fcmo-ai.github.io/FCMO-AI-Newsletter/news/{route}/{rid}.html"
                         for key, route in (("en", "en"), ("es-419", "es"), ("zh-Hans", "zh-hans"))},
                    )
                    target = root / "news" / route / f"{rid}.html"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(html, encoding="utf-8")
            feed = {
                "version": "https://jsonfeed.org/version/1.1",
                "items": [ingest_corpus.feed_item(row, brief) for brief, row, _ in briefs],
            }
            (root / "feed.json").write_text(json.dumps(feed), encoding="utf-8")
            errors = validate_agent_hygiene.validate(root, expected_generated_at=now)
            self.assertEqual(errors, [], "\n".join(errors))

    def test_final_paper_build_passes_agent_hygiene_validator(self):
        from tools import validate_agent_hygiene

        repo = Path(__file__).resolve().parents[1]
        fixture = repo / "contracts" / "fixtures"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "publish"
            build = subprocess.run(
                [sys.executable, str(repo / "tools" / "paper" / "build.py"),
                 "--stories", str(fixture / "stories.v2.json"),
                 "--status", str(fixture / "newsroom-status.fresh.json"),
                 "--out", str(out), "--base", "/FCMO-AI-Newsletter/"],
                cwd=repo, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            errors = validate_agent_hygiene.validate(out)
            self.assertEqual(errors, [], "\n".join(errors))
            old_citation = next((out / "data" / "citations").rglob("*.json"))
            old_citation_rel = old_citation.relative_to(out)
            stories = json.loads((fixture / "stories.v2.json").read_text(encoding="utf-8"))
            stories["stories"][0]["summary"] += " A later correction updates the summary."
            revised_stories = Path(tmp) / "stories-revised.json"
            revised_stories.write_text(json.dumps(stories), encoding="utf-8")
            revised_out = Path(tmp) / "publish-revised"
            revised = subprocess.run(
                [sys.executable, str(repo / "tools" / "paper" / "build.py"),
                 "--stories", str(revised_stories),
                 "--status", str(fixture / "newsroom-status.fresh.json"),
                 "--out", str(revised_out), "--base", "/FCMO-AI-Newsletter/",
                 "--citation-history", str(out / "data" / "citations")],
                cwd=repo, text=True, capture_output=True,
            )
            self.assertEqual(revised.returncode, 0, revised.stdout + revised.stderr)
            self.assertTrue((revised_out / old_citation_rel).is_file(), "prior citation permalink must survive a rebuild")
            feed_path = out / "feed.json"
            feed = json.loads(feed_path.read_text(encoding="utf-8"))
            feed["items"][0]["external_url"] = "https://wrong.example/not-the-source"
            feed_path.write_text(json.dumps(feed), encoding="utf-8")
            errors = validate_agent_hygiene.validate(out)
            self.assertTrue(any("missing from JSON Feed" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
