from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.gates import no_machine_paths, run_all
from tools.gates.common import GateFailure, canonical_story_path


class PublicationGateTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "publish"
        (self.root / "data").mkdir(parents=True)
        self.story = {
            "id": "FCMO-AAAAAAAAAAAA", "slug": "safe-story", "url_date": "2026-09-26",
            "status": "live", "title": "A safe story", "headline": "A safe story headline",
            "dek": "A sufficiently descriptive deck for the safe story.",
            "summary": "A sufficiently complete summary for publication.",
            "why_it_matters": "A sufficiently complete explanation of why it matters.",
            "importance_rationale": "The rationale is explicit and evidence bounded.",
            "technical": {"result": "Public artifact"},
            "l10n": {
                "es-419": self.locale("Una historia segura", "Un resumen completo para publicación.", "Importa por la evidencia pública."),
                "zh-Hans": self.locale("一则可靠报道", "这是一份可发布的完整摘要。", "公开证据说明了它的重要性。"),
            },
        }
        self.write_tree()

    @staticmethod
    def locale(title, summary, why):
        return {
            "state": "NATIVE_ARB", "missing": [],
            "fields": {
                "title": title, "headline": title, "dek": summary, "summary": summary,
                "why_it_matters": why, "importance_rationale": why,
                "technical": {"result": summary},
                "evidence": {"claims": [{"text": summary}], "limitations": [], "gaps": [], "contradictory": []},
            },
            "provenance": {key: "arb" for key in ("title", "headline", "dek", "summary", "why_it_matters", "importance_rationale", "technical", "evidence")},
        }

    def write_tree(self):
        document = {"schema": "fcmo-stories-v2", "stories": [self.story]}
        (self.root / "data" / "stories.v2.json").write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        (self.root / "data" / "glossary.json").write_text(Path("i18n/glossary.yml").read_text(encoding="utf-8"), encoding="utf-8")
        homes = {
            "index.html": '<html lang="en"><head><link rel="canonical" href="https://fcmo-ai.github.io/FCMO-AI-Newsletter/"></head><main><article data-lead><h1>Safe story</h1></article></main></html>',
            "es/index.html": '<html lang="es-419"><main><article data-lead><h1>Historia segura</h1></article></main></html>',
            "zh/index.html": '<html lang="zh-Hans"><main><article data-lead><h1>可靠报道</h1></article></main></html>',
        }
        for route, text in homes.items(): self.put(route, text)
        bodies = {
            "en": "This report explains the public evidence and its important limitations.",
            "es-419": "Esta nota explica la evidencia pública y sus límites importantes.",
            "zh-Hans": "本报道解释公开证据及其重要限制。",
        }
        for locale in bodies:
            route = canonical_story_path(self.story, locale)
            self.put(route, f'<html lang="{locale}"><main data-story-id="{self.story["id"]}"><h1>{self.story["l10n"].get(locale, {}).get("fields", {}).get("title", self.story["title"])}</h1><p>{bodies[locale]}</p></main></html>')

    def put(self, route: str, text: str):
        path = self.root / route; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")

    def assert_gate(self, code: str):
        with self.assertRaises(GateFailure) as caught: run_all.run(self.root)
        self.assertEqual(caught.exception.code, code, caught.exception)

    def test_machine_path_gate_rejects_injected_tracked_file(self):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        injected = repo / "operator-note.txt"
        injected.write_text("path=" + "/srv/" + "fcmo/worktree", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "operator-note.txt"], check=True)
        with self.assertRaises(GateFailure) as caught:
            no_machine_paths.check_repo(repo)
        self.assertEqual(caught.exception.code, "NO_MACHINE_PATHS")
        self.assertIn("operator-note.txt", caught.exception.problems[0])

    def test_clean_tree_passes_all_gates(self):
        results = run_all.run(self.root)
        self.assertEqual([result.code for result in results], [gate.__module__.rsplit(".", 1)[-1].upper() for gate in run_all.GATES])

    def test_generator_output_can_prove_story_parity_from_routes_manifest(self):
        routes = []
        for locale in ("en", "es-419", "zh-Hans"):
            route = canonical_story_path(self.story, locale)
            routes.append({"kind": "story", "story_id": self.story["id"], "locale": locale,
                           "path": route.removesuffix("index.html")})
        (self.root / "data/routes.json").write_text(json.dumps(routes), encoding="utf-8")
        (self.root / "data/stories.v2.json").unlink()
        results = run_all.run(self.root)
        locale = next(result for result in results if result.code == "LOCALE_COMPLETE")
        self.assertTrue(locale.warnings)

    def test_orphan_route_fails_named_gate(self):
        self.put("2026/09/25/orphan/index.html", '<html><main data-story-id="FCMO-BBBBBBBBBBBB">orphan</main></html>')
        self.assert_gate("ID_SET_EQUALITY")

    def test_english_prose_in_spanish_fails_named_gate(self):
        route = canonical_story_path(self.story, "es-419")
        self.put(route, f'<html lang="es-419"><main data-story-id="{self.story["id"]}"><p>This is an English sentence that should never appear in the Spanish edition.</p></main></html>')
        self.assert_gate("ENGLISH_LEAK")

    def test_english_text_in_graphic_referenced_by_chinese_page_fails_named_gate(self):
        self.put("assets/story-media/FCMO-AAAAAAAAAAAA-zh-Hans.svg",
                 '<svg xmlns="http://www.w3.org/2000/svg"><text>ARCHITECTURES SCALING</text>'
                 '<text>This is the full English headline with a useful release today.</text></svg>')
        self.put("zh/index.html", '<html lang="zh-Hans"><body><img src="/FCMO-AI-Newsletter/assets/story-media/FCMO-AAAAAAAAAAAA-zh-Hans.svg" alt=""></body></html>')
        self.assert_gate("ENGLISH_LEAK")

    def test_translate_no_product_name_in_local_graphic_uses_structured_name_rule(self):
        self.put("assets/story-media/product-zh-Hans.svg",
                 '<svg xmlns="http://www.w3.org/2000/svg"><text translate="no" data-field="products">'
                 'University of Science and Technology of China</text></svg>')
        self.put("zh/index.html", '<html lang="zh-Hans"><body><img src="/FCMO-AI-Newsletter/assets/story-media/product-zh-Hans.svg" alt=""></body></html>')
        run_all.run(self.root)

    def test_structured_organization_name_is_not_an_english_leak(self):
        route = canonical_story_path(self.story, "es-419")
        self.put(route, f'<html lang="es-419"><main data-story-id="{self.story["id"]}"><h1>Historia segura</h1><p>Organizaciones <span translate="no" data-field="organizations">University of Science and Technology of China</span></p></main></html>')
        run_all.run(self.root)

    def test_translate_no_does_not_hide_english_prose_outside_exact_structured_fields(self):
        route = canonical_story_path(self.story, "es-419")
        self.put(route, f'<html lang="es-419"><main data-story-id="{self.story["id"]}"><p><span translate="no" data-field="summary">This is English prose that remains a release defect.</span></p></main></html>')
        self.assert_gate("ENGLISH_LEAK")

    def test_visible_internal_id_fails_named_gate(self):
        self.put("index.html", '<html><head><title>FCMO-AAAAAAAAAAAA</title></head><body><h1>FCMO-AAAAAAAAAAAA</h1></body></html>')
        self.assert_gate("INTERNAL_ID")

    def test_internal_story_id_attribute_is_not_reader_copy(self):
        results = run_all.run(self.root)
        self.assertIn("INTERNAL_ID", [result.code for result in results])

    def test_remote_script_fails_named_gate(self):
        self.put("es/index.html", '<html lang="es-419"><script src="https://example.org/app.js"></script></html>')
        self.assert_gate("REMOTE_SCRIPT")

    def test_missing_base_path_asset_fails_named_gate(self):
        self.put("index.html", '<html><head><link rel="canonical" href="https://fcmo-ai.github.io/FCMO-AI-Newsletter/"></head><body><img src="/FCMO-AI-Newsletter/assets/missing.svg" alt=""></body></html>')
        self.assert_gate("BROKEN_REFERENCE")

    def test_missing_absolute_same_site_asset_fails_named_gate(self):
        self.put("index.html", '<html><head><link rel="canonical" href="https://fcmo-ai.github.io/FCMO-AI-Newsletter/"></head>'
                 '<body><img src="https://fcmo-ai.github.io/FCMO-AI-Newsletter/assets/missing.svg" alt=""></body></html>')
        self.assert_gate("BROKEN_REFERENCE")

    def test_base_path_asset_resolves_inside_candidate(self):
        self.put("assets/present.svg", "<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>")
        self.put("index.html", '<html><head><link rel="canonical" href="https://fcmo-ai.github.io/FCMO-AI-Newsletter/"></head><body><img src="/FCMO-AI-Newsletter/assets/present.svg" alt=""></body></html>')
        run_all.run(self.root)

    def test_personal_mailbox_fails_named_gate(self):
        self.put("privacy/index.html", "<html><p>write to person@" + "g" + "mail.com</p></html>")
        self.assert_gate("PERSONAL_MAILBOX")

    def test_unresolved_binding_fails_named_gate(self):
        path = self.root / "index.html"
        path.write_text(path.read_text() + '<span data-binding="—">—</span>', encoding="utf-8")
        self.assert_gate("BINDING_COMPLETE")

    def test_unexpanded_format_field_fails_named_gate(self):
        path = self.root / "index.html"
        path.write_text(path.read_text() + "<dt>Confidence: {level}</dt>", encoding="utf-8")
        self.assert_gate("BINDING_COMPLETE")

    def test_two_megabyte_page_fails_named_gate(self):
        self.put("large/index.html", "<html><p>" + "x" * 2_000_000 + "</p></html>")
        self.assert_gate("SIZE_BUDGET")

    def test_glossary_conflict_in_machine_field_fails_named_gate(self):
        self.story["l10n"]["es-419"]["fields"]["summary"] = "El post-entrenamiento aparece como término rechazado."
        self.story["l10n"]["es-419"]["provenance"]["summary"] = "machine"
        self.write_tree()
        self.assert_gate("GLOSSARY_CONSISTENCY")

    def test_pending_locale_requires_visible_notice(self):
        self.story["l10n"]["es-419"] = {"state": "PENDING", "missing": ["summary"], "fields": {}, "provenance": {}}
        self.write_tree()
        self.assert_gate("LOCALE_COMPLETE")


if __name__ == "__main__": unittest.main()
