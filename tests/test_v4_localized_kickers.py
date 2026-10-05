"""Section kickers on FCMO AI pages read in the reader's language, from the curated catalogs."""

from __future__ import annotations

import html
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.paper.i18n import load_catalogs  # noqa: E402

STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))
ENGLISH_KICKER = re.compile(r"(?i)\b(archive|signal|operations)\b")
KICKER = re.compile(r'<(p|span|div|h[1-6])\b[^>]*class="[^"]*\bsection-kicker\b[^"]*"[^>]*>(.*?)</\1>', re.S)
MAIN = re.compile(r'<main\b.*?</main>', re.S)
DEVELOPING = re.compile(r'<section class="developing-well">.*?</section>', re.S)
HTML_LANG = re.compile(r'<html lang="([^"]+)"')
KEYS = ("archive", "signal", "operations")


def text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def kickers(fragment: str) -> list[str]:
    return [text(match.group(2)) for match in KICKER.finditer(fragment)]


class LocalizedKickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="newsletter-v4-kickers-")
        cls.out = Path(cls.temp.name) / "publish"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(STATUS),
             "--out", str(cls.out), "--base", BASE],
            cwd=ROOT, text=True, capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.catalogs = load_catalogs(ROOT)
        cls.routes = json.loads((cls.out / "data/routes.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def page(self, prefix: str, suffix: str) -> str:
        return (self.out / prefix / suffix / "index.html").read_text(encoding="utf-8")

    def expected(self, locale: str, key: str) -> str:
        return f'FCMO AI · {self.catalogs[locale]["strings"]["kicker"][key]}'

    def first_kicker(self, page: str) -> str:
        found = kickers(MAIN.search(page).group())
        self.assertTrue(found)
        return found[0]

    def edition_suffix(self, locale: str) -> str:
        editions = sorted(route["path"] for route in self.routes if route["kind"] == "edition" and route["locale"] == locale)
        self.assertTrue(editions)
        return editions[-1][len(dict(LOCALES)[locale]):]

    def test_catalog_values_are_curated_in_all_three_languages(self):
        english = self.catalogs["en"]["strings"]["kicker"]
        self.assertEqual(set(english), set(KEYS))
        for locale, _ in LOCALES:
            values = self.catalogs[locale]["strings"]["kicker"]
            self.assertEqual(set(values), set(KEYS), locale)
            for key in KEYS:
                with self.subTest(locale=locale, key=key):
                    self.assertTrue(values[key].strip())
                    if locale != "en":
                        self.assertNotEqual(values[key].casefold(), english[key].casefold())
                        self.assertIsNone(ENGLISH_KICKER.search(values[key]))

    def test_no_english_kicker_survives_in_spanish_or_chinese_pages(self):
        checked, problems = 0, []
        for path in sorted(self.out.rglob("*.html")):
            page = path.read_text(encoding="utf-8")
            lang = HTML_LANG.search(page)
            if not lang or lang.group(1) not in {"es-419", "zh-Hans"}:
                continue
            checked += 1
            problems += [f"{path.relative_to(self.out)}: {value}" for value in kickers(page) if ENGLISH_KICKER.search(value)]
        self.assertGreater(checked, 100)
        self.assertEqual(problems, [])

    def test_archive_status_and_developing_kickers_come_from_the_catalog(self):
        for locale, prefix in LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(self.first_kicker(self.page(prefix, "archive/")), self.expected(locale, "archive"))
                self.assertEqual(self.first_kicker(self.page(prefix, self.edition_suffix(locale))),
                                 self.expected(locale, "archive"))
                self.assertEqual(self.first_kicker(self.page(prefix, "status/")), self.expected(locale, "operations"))
                well = DEVELOPING.search(self.page(prefix, "diario/"))
                self.assertIsNotNone(well)
                self.assertEqual(kickers(well.group())[0], self.expected(locale, "signal"))

    def test_english_kickers_still_read_in_english(self):
        self.assertEqual(self.first_kicker(self.page("", "archive/")), "FCMO AI · archive")
        self.assertEqual(self.first_kicker(self.page("", self.edition_suffix("en"))), "FCMO AI · archive")
        self.assertEqual(self.first_kicker(self.page("", "status/")), "FCMO AI · operations")
        self.assertEqual(kickers(DEVELOPING.search(self.page("", "diario/")).group())[0], "FCMO AI · signal")

    def test_generator_has_no_hard_coded_english_kicker(self):
        hits = [str(path.relative_to(ROOT)) for path in (ROOT / "tools/paper").rglob("*.py")
                if re.search(r"FCMO AI · (archive|signal|operations)", path.read_text(encoding="utf-8"))]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
