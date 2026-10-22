"""Plates: deterministic, text-free procedural SVG with a real motif-topic table and 3-language alt."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from tools.paper import og_image, plates

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("en", "es-419", "zh-Hans")
SAMPLE = {
    "agents": ["coding-agents"],
    "monitoring": ["agent-evaluation"],
    "security": ["agent-security"],
    "reasoning": ["chain-of-thought"],
    "voice": ["speech-models"],
    "neutral": ["kv-cache"],
}


class PlateTests(unittest.TestCase):
    def test_same_id_same_svg_and_different_ids_differ(self):
        a = plates.plate("FCMO-AAAA", ["agents"], "16:10", "en")
        self.assertEqual(a, plates.plate("FCMO-AAAA", ["agents"], "16:10", "en"))
        self.assertNotEqual(a["svg"], plates.plate("FCMO-BBBB", ["agents"], "16:10", "en")["svg"])

    def test_no_text_nodes_and_valid_xml_in_every_motif_and_slot(self):
        for motif, topics in SAMPLE.items():
            for ratio, (w, h) in plates.SLOTS.items():
                result = plates.plate("FCMO-TEST", topics, ratio, "en")
                self.assertEqual(result["motif"], motif)
                root = ET.fromstring(result["svg"])
                tags = {el.tag.rsplit("}", 1)[-1] for el in root.iter()}
                self.assertNotIn("text", tags)
                self.assertNotIn("tspan", tags)
                self.assertNotIn("foreignObject", tags)
                self.assertNotIn("image", tags)
                self.assertNotIn("script", tags)
                self.assertNotIn("title", tags)
                self.assertEqual(root.get("viewBox"), f"0 0 {w} {h}")
                self.assertLess(len(result["svg"]), 4500, (motif, ratio))
                self.assertFalse([k for el in root.iter() for k in el.attrib if k == "id"], "ids would collide when a plate repeats")

    def test_motif_table_is_complete(self):
        self.assertEqual(set(plates.MOTIF_TOPICS) | {"neutral"}, set(plates.MOTIFS))
        for motif, topics in SAMPLE.items():
            self.assertEqual(plates.choose_motif(topics), motif)
        self.assertEqual(plates.choose_motif([]), "neutral")
        self.assertEqual(plates.choose_motif(None), "neutral")
        # a specific motif outranks the generic agents motif; among specifics the earlier topic weighs more
        self.assertEqual(plates.choose_motif(["agents", "agent-security"]), "security")
        self.assertEqual(plates.choose_motif(["speech", "agent-evaluation"]), "voice")
        self.assertEqual(plates.choose_motif(["agent-evaluation", "speech"]), "monitoring")

    def test_no_false_motif_from_substrings(self):
        for topic in ("kv-cache", "quantization", "data-centres", "china", "open-weights", "arctic-ice", "tooling-costs"):
            self.assertEqual(plates.choose_motif([topic]), "neutral", topic)

    def test_alt_in_three_languages_matches_the_catalog(self):
        for motif in plates.MOTIFS:
            alt = plates.plate("X", SAMPLE[motif], "16:9")["alt"]
            self.assertEqual(set(alt), set(LOCALES))
            for locale in LOCALES:
                ui = json.loads((ROOT / "i18n" / "ui" / f"{locale}.json").read_text(encoding="utf-8"))["strings"]["plate"]
                if motif == "neutral":
                    self.assertEqual(alt[locale], ui["alt_decorative"])
                else:
                    self.assertIn(ui[f"motif_{motif}"], alt[locale])
                self.assertTrue(alt[locale].strip())
        self.assertEqual(len({plates.plate("X", ["kv-cache"], "16:9")["alt"][l] for l in LOCALES}), 3)

    def test_locale_embeds_the_label_and_default_is_hidden(self):
        labelled = plates.plate("X", ["voice"], "16:10", "zh-Hans")
        self.assertIn('role="img"', labelled["svg"])
        self.assertIn(f'aria-label="{labelled["alt"]["zh-Hans"]}"', labelled["svg"])
        self.assertIn('aria-hidden="true"', plates.plate("X", ["voice"], "16:10")["svg"])
        with self.assertRaises(ValueError):
            plates.plate("X", [], "4:3")
        with self.assertRaises(ValueError):
            plates.plate("X", [], "16:9", "fr")

    def test_one_ember_family_only(self):
        for motif, topics in SAMPLE.items():
            svg = plates.plate("X", topics, "16:10")["svg"]
            colours = {c.upper() for c in __import__("re").findall(r"#[0-9a-fA-F]{6}", svg)}
            self.assertLessEqual(colours, {"#0D0D0F", "#17171B", "#F2EFE8", "#F05A28"}, motif)
            self.assertIn("#F05A28", colours, motif)


class OgCardTests(unittest.TestCase):
    def test_template_has_no_headline_or_dek_slot(self):
        template = (ROOT / "tools" / "paper" / "og_card.html").read_text(encoding="utf-8")
        for slot in ("{{HEADLINE}}", "{{DEK}}", "{{SIZE}}"):
            self.assertNotIn(slot, template)
        self.assertIn("{{PLATE}}", template)

    def test_card_does_not_bake_the_headline(self):
        story = {"id": "FCMO-TESTCARD", "event_at": "2026-10-21", "evidence_class": "A", "beat": "research",
                 "topics": ["agent-security"], "title": "A very distinctive headline xyzzy",
                 "dek": "A very distinctive dek plugh", "l10n": {}}
        config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
        catalogs = og_image.load_catalogs(ROOT)
        template = (ROOT / "tools" / "paper" / "og_card.html").read_text(encoding="utf-8")
        for locale in config["locales"]:
            html = og_image._card(template, story=story, locale=locale, catalog=catalogs[locale["code"]])
            self.assertNotIn("xyzzy", html)
            self.assertNotIn("plugh", html)
            self.assertNotIn("{{", html)
            self.assertIn('data-motif="security"', html)
            self.assertIn("FCMO AI", html)


if __name__ == "__main__":
    unittest.main()
