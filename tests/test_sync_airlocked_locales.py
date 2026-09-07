from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import sync_airlocked_locales

RID = "FCMO-A1B2C3D4E5F6"


class SyncAirlockedLocalesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.i18n = self.root / "i18n"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _seed(self, locale: str) -> None:
        self._write_json(
            self.i18n / locale / "part-01.json",
            {
                "schema": sync_airlocked_locales.PART_SCHEMA,
                "locale": locale,
                "canonical_locale": "en",
                "records": {
                    RID: {
                        "title": "Título histórico",
                        "summary": "Resumen histórico",
                        "why_it_matters": "Importancia histórica",
                        "why": "Explicación completa ya curada",
                        "technical": {
                            "mechanism": "Mecanismo ya curado",
                            "reproducibility": "Reproducibilidad ya curada",
                        },
                    }
                },
            },
        )
        self._write_json(
            self.corpus / "data" / "locales" / locale / "records.json",
            {
                "schema": sync_airlocked_locales.SCHEMA,
                "locale": locale,
                "records": {
                    RID: {
                        "title": "Título actualizado",
                        "summary": "Resumen actualizado",
                        "technical": {"mechanism": "Mecanismo actualizado"},
                    }
                },
            },
        )

    def test_sparse_refresh_promotes_without_erasing_complete_prose(self) -> None:
        for locale in sync_airlocked_locales.LOCALES:
            self._seed(locale)
        self.assertEqual(
            sync_airlocked_locales.main([
                "--corpus", str(self.corpus),
                "--i18n-dir", str(self.i18n),
            ]),
            0,
        )
        for locale in sync_airlocked_locales.LOCALES:
            historical = json.loads((self.i18n / locale / "part-01.json").read_text(encoding="utf-8"))
            self.assertNotIn(RID, historical["records"])
            airlock = json.loads((self.i18n / locale / "part-airlock.json").read_text(encoding="utf-8"))
            row = airlock["records"][RID]
            self.assertEqual(row["title"], "Título actualizado")
            self.assertEqual(row["summary"], "Resumen actualizado")
            self.assertEqual(row["why"], "Explicación completa ya curada")
            self.assertEqual(row["why_it_matters"], "Importancia histórica")
            self.assertEqual(row["technical"]["mechanism"], "Mecanismo actualizado")
            self.assertEqual(row["technical"]["reproducibility"], "Reproducibilidad ya curada")

    def test_lists_replace_atomically_instead_of_merging_by_index(self) -> None:
        base = {"limitations": ["A", "B"], "technical": {"mechanism": "old", "regime": "kept"}}
        delta = {"limitations": ["C"], "technical": {"mechanism": "new"}}
        merged = sync_airlocked_locales.merge_overlay(base, delta)
        self.assertEqual(merged["limitations"], ["C"])
        self.assertEqual(merged["technical"], {"mechanism": "new", "regime": "kept"})


if __name__ == "__main__":
    unittest.main()
