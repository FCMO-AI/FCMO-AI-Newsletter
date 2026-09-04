from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "translate_records.py"
SITE = ROOT / "release-src"
I18N = ROOT / "site" / "data" / "i18n"
CORPUS = ROOT / "_fixtures" / "corpus-2026-09-01"
LOCALES = ("es-419", "zh-Hans")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.apply_curated_i18n import _canonical_digest, _canonical_editorial, _taxonomy_values


def canonical_records(site: Path = SITE) -> dict[str, dict]:
    text = (site / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', text, re.S)
    return {row["id"]: row for row in json.loads(match.group(1))["records"]}


def canonical_ids() -> set[str]:
    return set(canonical_records())


class TranslateRecordsTests(unittest.TestCase):
    def run_tool(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        process_env = os.environ.copy()
        process_env.pop("ANTHROPIC_API_KEY", None)
        if env:
            process_env.update(env)
        process_env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            cwd=ROOT,
            env=process_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def remove_one_record_per_locale(self, root: Path) -> str:
        record_id = sorted(canonical_ids())[0]
        for locale in LOCALES:
            for path in sorted((root / locale).glob("part-*.json")):
                document = json.loads(path.read_text(encoding="utf-8"))
                if record_id in document["records"]:
                    del document["records"][record_id]
                    with path.open("w", encoding="utf-8", newline="\n") as handle:
                        handle.write(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n")
                    break
        return record_id

    def test_dry_run_names_only_missing_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "i18n"
            shutil.copytree(I18N, copied)
            removed = self.remove_one_record_per_locale(copied)
            result = self.run_tool("--i18n-dir", str(copied), "--dry-run", "--engine", "stub")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(removed, result.stdout)

    def test_stub_apply_is_deterministic_and_does_not_touch_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            shutil.copytree(I18N, first)
            shutil.copytree(I18N, second)
            ui_before = {locale: (first / locale / "ui.json").read_bytes() for locale in LOCALES}
            self.remove_one_record_per_locale(first)
            self.remove_one_record_per_locale(second)
            for copied in (first, second):
                result = self.run_tool("--i18n-dir", str(copied), "--apply", "--engine", "stub")
                self.assertEqual(result.returncode, 0, result.stderr)
            for locale in LOCALES:
                self.assertEqual(ui_before[locale], (first / locale / "ui.json").read_bytes())
                self.assertEqual(
                    sorted((first / locale).glob("part-*.json"))[3].read_bytes(),
                    sorted((second / locale).glob("part-*.json"))[3].read_bytes(),
                )

    def test_anthropic_without_credential_fails_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "i18n"
            shutil.copytree(I18N, copied)
            self.remove_one_record_per_locale(copied)
            before = {
                path: path.read_bytes()
                for path in copied.rglob("*.json")
            }
            result = self.run_tool("--i18n-dir", str(copied), "--apply", "--engine", "anthropic")
            self.assertEqual(result.returncode, 2)
            self.assertIn("ANTHROPIC_API_KEY", result.stderr)
            self.assertEqual(before, {path: path.read_bytes() for path in copied.rglob("*.json")})

    def test_stub_apply_refreshes_digest_and_missing_taxonomy_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            refreshed_site = temporary_root / "release-src"
            ingest = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "ingest_corpus.py"), "--corpus", str(CORPUS), "--out", str(refreshed_site)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(ingest.returncode, 0, ingest.stderr)
            copied = temporary_root / "i18n"
            shutil.copytree(I18N, copied)
            before = {
                locale: json.loads((copied / locale / "ui.json").read_text(encoding="utf-8"))
                for locale in LOCALES
            }
            result = self.run_tool(
                "--site", str(refreshed_site), "--i18n-dir", str(copied), "--apply", "--engine", "stub"
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            index_text = (refreshed_site / "index.html").read_text(encoding="utf-8")
            digest = _canonical_digest(_canonical_editorial(index_text))
            records = canonical_records(refreshed_site)
            taxonomy = _taxonomy_values(records)
            for locale in LOCALES:
                after = json.loads((copied / locale / "ui.json").read_text(encoding="utf-8"))
                self.assertEqual(after["canonical_record_count"], len(records))
                self.assertEqual(after["canonical_source_sha256"], digest)
                for key, value in before[locale]["ui"].items():
                    self.assertEqual(after["ui"][key], value)
                self.assertTrue(taxonomy <= set(after["ui"]))
                for value in taxonomy - set(before[locale]["ui"]):
                    self.assertNotEqual(after["ui"][value], value)
                for part in (copied / locale).glob("part-*.json"):
                    document = json.loads(part.read_text(encoding="utf-8"))
                    self.assertEqual(document["canonical_source_sha256"], digest)


if __name__ == "__main__":
    unittest.main()
