"""Round-3 fixes: the SOURCES bar lists every source, and the search tab really focuses the field."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.paper.i18n import load_catalogs  # noqa: E402
from tools.paper.templates.reader import sources_bar  # noqa: E402

SOURCES = [
    {"url": "https://example.org/a", "domain": "example.org", "primary": False},
    {"url": "https://example.net/b", "domain": "example.net", "primary": True},
    {"url": "https://example.com/c", "domain": "example.com", "primary": False},
]


class SourcesBarTests(unittest.TestCase):
    def test_every_source_is_linked_primary_first_in_three_locales(self):
        for code, catalog in load_catalogs(ROOT).items():
            with self.subTest(locale=code):
                bar = sources_bar({"sources": SOURCES}, catalog, automation_html="", byline="x")
                self.assertLess(bar.index("example.net"), bar.index("example.org"))
                for host in ("example.net", "example.org", "example.com"):
                    self.assertIn(host, bar)
                self.assertNotIn('href="#sources"', bar)

    def test_long_lists_link_to_the_full_list(self):
        many = [{"url": f"https://h{i}.example/x", "domain": f"h{i}.example", "primary": i == 0} for i in range(7)]
        for code, catalog in load_catalogs(ROOT).items():
            with self.subTest(locale=code):
                bar = sources_bar({"sources": many}, catalog, automation_html="", byline="x")
                self.assertIn('href="#sources"', bar)
                self.assertIn("7", bar)
                self.assertNotIn("h5.example", bar)


class SearchFocusTests(unittest.TestCase):
    def test_focus_runs_after_the_field_exists(self):
        source = (ROOT / "tools/paper/build.py").read_text(encoding="utf-8")
        self.assertIn("addEventListener('DOMContentLoaded',()=>{if(/[?&]focus=1", source)
        self.assertIn("f.addEventListener('input'", source)


class PublishedAssetsTests(unittest.TestCase):
    def test_shipped_stylesheet_has_no_trace_of_the_retired_products(self):
        css = (ROOT / "site-src/assets/css/paper.css").read_text(encoding="utf-8")
        for needle in ("Javier", "fCMO", "zone-switch", "brand-sub"):
            self.assertNotIn(needle, css)


if __name__ == "__main__":
    unittest.main()
