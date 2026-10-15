"""Localization defects 1-6 logged by the publication desk (w14 nl-l10n-quality).

(1) singular/plural agreement, (2) region labels, (3) correction headings of non-live
stories, (4) English importance terms in the desk packs, (5) the gate must not be
false-green on embedded English, tier terms or scales, (6) MiMo-V2.6 magnitudes.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import validate_localizations as vl  # noqa: E402
from tools.paper import i18n as paper_i18n  # noqa: E402
from tools.paper.templates import landing  # noqa: E402

LOCALES = ("es-419", "zh-Hans")
CATALOGS = {code: json.loads((ROOT / "i18n/ui" / f"{code}.json").read_text(encoding="utf-8"))
            for code in ("en", "es-419", "zh-Hans")}
STORIES = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))["stories"]
MIMO = "FCMO-1BFA9A5A6560"


def checks():
    from tools import localization_checks  # absent before this change: the tests go red
    return localization_checks


def effective(locale: str):
    return vl.effective_overlays_details(locale, ROOT / "site/data/i18n", ROOT / "corpus")


class SingularPluralAgreement(unittest.TestCase):  # defect 1
    def test_front_ledger_nouns_agree_with_count_one(self):
        for code, expected in (("en", "1 story"), ("es-419", "1 historia")):
            self.assertEqual(paper_i18n.plural(CATALOGS[code], "story", 1), expected)
            self.assertEqual(paper_i18n.noun(CATALOGS[code], "story", 1), expected.split(" ", 1)[1])
            self.assertNotEqual(paper_i18n.noun(CATALOGS[code], "story", 2), paper_i18n.noun(CATALOGS[code], "story", 1))

    def test_landing_record_uses_singular_for_one(self):
        for code, singular in (("en", "story"), ("es-419", "historia")):
            html = landing.render(locale={"code": code}, home="/", technical="/t/", about="/a/", subscribe="/s/",
                                  lead="", top="", cartas="x", stats=(1, 1, 1), catalog=CATALOGS[code])
            self.assertIn(f"1 <small>{singular}</small>", html)
            self.assertNotIn("1 <small>stories</small>", html)
            self.assertNotIn("1 <small>historias</small>", html)

    def test_builder_has_no_hardcoded_plural_noun_tuples(self):
        source = (ROOT / "tools/paper/build.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r'"live stories",\s*"topics"')
        self.assertIn("noun(", source)


class RegionLabels(unittest.TestCase):  # defect 2
    def test_every_region_in_the_corpus_has_a_label_in_every_catalog(self):
        regions = set()
        for line in (ROOT / "corpus/data/developments.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                regions.update(json.loads(line).get("regions") or [])
        self.assertIn("Global", regions)
        for code, catalog in CATALOGS.items():
            missing = sorted(r for r in regions if r not in catalog["labels"]["region"])
            self.assertEqual(missing, [], f"{code} lacks region labels")


class CorrectionHeadings(unittest.TestCase):  # defect 3
    def test_non_live_stories_have_translated_headings(self):
        gone = [s for s in STORIES if s["status"] != "live"]
        self.assertEqual(len(gone), 3)
        for story in gone:
            for code in LOCALES:
                text = paper_i18n.headline(story, code, CATALOGS[code])
                self.assertNotEqual(text, CATALOGS[code]["strings"]["l10n"]["pending_title"], story["id"])
                self.assertNotEqual(text, story["title"], f"{story['id']} {code} still shows English")

    def test_translated_headings_keep_figures(self):
        by_id = {s["id"]: s for s in STORIES}
        for code in LOCALES:
            self.assertIn("26%", paper_i18n.headline(by_id["FCMO-FDBE3D996243"], code, CATALOGS[code]))
            self.assertIn("$12.9B", paper_i18n.headline(by_id["FCMO-EEF757F0D806"], code, CATALOGS[code]))


class DeskPacksHaveNoEnglishTiers(unittest.TestCase):  # defect 4
    def test_no_english_importance_term_in_any_effective_overlay(self):
        found = []
        for code in LOCALES:
            rows, _, _, _ = effective(code)
            for rid, row in rows.items():
                for path, text in vl.prose_leaves({k: v for k, v in row.items() if k in vl.V2_PROSE_KEYS}):
                    if checks().english_tier_terms(text):
                        found.append((code, rid, vl.path_text(path)))
        self.assertEqual(found, [])


class GateIsNotFalseGreen(unittest.TestCase):  # defect 5
    SOURCE = {"title": "Lab ships model", "summary": "The lab trained the model on 360 billion tokens for about $2.6 million."}

    def status(self, overlay, locale="es-419", source=None):
        source = source or self.SOURCE
        meta = {"origin": "arb", "at": "2026-10-14T00:00:00Z", "human_reviewed": False, "network_translation": False}
        prov = {key: {**meta, **binding} for key, binding in vl.source_binding(source, overlay).items()}
        return vl.pair_status(source, overlay, locale, strict=True, provenance=prov)

    def test_good_translation_passes(self):
        ok = {"title": "Laboratorio lanza modelo", "summary": "El laboratorio entrenó el modelo con 360 mil millones de tokens por unos US$2.6 millones."}
        self.assertIn(self.status(ok)["state"], vl.COMPLETE_STATES)

    def test_dropped_scale_fails(self):
        bad = {"title": "Laboratorio lanza modelo", "summary": "El laboratorio entrenó el modelo con 360 de tokens por unos US$2.6 millones."}
        st = self.status(bad)
        self.assertEqual(st["state"], "FAILED", st)

    def test_wrong_scale_fails(self):
        bad = {"title": "Laboratorio lanza modelo", "summary": "El laboratorio entrenó el modelo con 360 millones de tokens por unos US$2.6 millones."}
        self.assertEqual(self.status(bad)["state"], "FAILED")

    def test_zh_dropped_scale_fails(self):
        bad = {"title": "实验室发布模型", "summary": "该实验室使用 360 token 训练了模型，成本约为 2.6百万美元。"}
        self.assertEqual(self.status(bad, "zh-Hans")["state"], "FAILED")

    def test_english_tier_term_fails(self):
        src = {"title": "Lab ships model", "summary": "A short summary of the model.", "importance_rationale": "Very major if confirmed."}
        bad = {"title": "Laboratorio lanza modelo", "summary": "Un resumen breve del modelo.", "importance_rationale": "Sería Very major si se confirma."}
        self.assertEqual(self.status(bad, source=src)["state"], "FAILED")

    def test_embedded_english_sentence_fails(self):
        spanish = ("El laboratorio entrenó el modelo con una mezcla de datos públicos y sintéticos, y describió "
                   "la arquitectura, el proceso de evaluación, los resultados en pruebas de razonamiento y las "
                   "limitaciones conocidas de la versión inicial que se publicó para investigadores externos.")
        bad = {"title": "Laboratorio lanza modelo",
               "summary": spanish + " The lab said that the model was trained on 360 billion tokens and that it will be released."}
        st = self.status(bad)
        self.assertEqual(st["state"], "FAILED", st)
        self.assertEqual(st["failure"]["gate"], "ENGLISH_LEAK")

    def test_magnitude_helpers(self):
        c = checks()
        self.assertEqual(c.magnitude_errors("2.7 billion tokens", "2.7 mil millones de tokens", "es-419"), [])
        self.assertTrue(c.magnitude_errors("2.7 billion tokens", "2.7 millones de tokens", "es-419"))
        self.assertTrue(c.magnitude_errors("27 billion active", "激活 27 个参数", "zh-Hans"))
        self.assertEqual(c.magnitude_errors("29-121M parameters", "29-121M parámetros", "es-419"), [])
        self.assertEqual(c.english_tier_terms("Es notable y de minorías"), [])
        self.assertEqual(c.english_tier_terms("Esto es Very major"), ["Very major"])


class MimoMagnitudes(unittest.TestCase):  # defect 6
    def test_mimo_scales_in_both_locales(self):
        es, _, _, _ = effective("es-419")
        zh, _, _, _ = effective("zh-Hans")
        es_text = json.dumps(es[MIMO], ensure_ascii=False)
        zh_text = json.dumps(zh[MIMO], ensure_ascii=False)
        self.assertNotRegex(es_text, r"2\.7[–-]3\.7 millones")
        self.assertRegex(es_text, r"2\.7[–-]3\.7 mil millones")
        self.assertNotRegex(zh_text, r"2\.7[–-]3\.7个")
        self.assertRegex(zh_text, r"2\.7[–-]3\.7十亿")

    def test_no_english_scale_words_remain_in_any_effective_overlay(self):
        left = []
        for code in LOCALES:
            rows, _, _, _ = effective(code)
            for rid, row in rows.items():
                for _, text in vl.prose_leaves({k: v for k, v in row.items() if k in vl.V2_PROSE_KEYS}):
                    left += [(code, rid, u) for u in checks().untranslated_scales(text, code)]
        self.assertEqual(left, [])

    def test_every_effective_overlay_passes_the_strict_gate(self):
        story_src = vl.load_corpus_canonical(ROOT / "corpus")
        bad = []
        for code in LOCALES:
            rows, strict, prov, _ = effective(code)
            for rid, row in rows.items():
                if rid not in story_src:
                    continue
                st = vl.pair_status(story_src[rid], row, code, strict=rid in strict, provenance=prov.get(rid))
                if st["state"] == "FAILED":
                    bad.append((code, rid, st.get("failure")))
        self.assertEqual(bad, [])

    def test_corrections_go_inert_when_upstream_changes(self):
        rows = {"X": {"summary": "texto nuevo de ARB"}}
        prov = {}
        applied = vl.apply_corrections(rows, prov, {"X": {"summary": {
            "upstream_sha256": vl.stable_digest("texto viejo"), "source_sha256": "s", "value": "corregido",
            "at": "2026-10-14T00:00:00Z", "reason": "r"}}})
        self.assertEqual(applied, [])
        self.assertEqual(rows["X"]["summary"], "texto nuevo de ARB")


if __name__ == "__main__":
    unittest.main()
