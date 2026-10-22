"""C6 oracles: one FCMO (AI) across the built public site.

Campaign c6, DIRECCION §4 («Una sola FCMO (AI)») and §3 (raw slugs).
Every test here is named ``test_c6_*`` so the integration step can report
them apart. They are not skipped: on main they are expected to be RED, and
each red reason is listed in the failure message.
"""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = "/FCMO-AI-Newsletter/"

# DIRECCION §4: product-split wording that must not survive in built HTML.
FORBIDDEN_PRODUCT_STRINGS = (
    "fCMO /",
    "fCMO ·",
    "FCMO AI /",
    "fCMO +",
    "membership",
    "two publications",
)

# DIRECCION §4: old product routes become redirects, not pages.
OLD_PRODUCT_ROUTES = ("cartas/", "empieza/", "diario/")

REFRESH_RE = re.compile(r"""http-equiv=["']refresh["']""", re.IGNORECASE)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


class VisibleText(HTMLParser):
    """Collects text nodes of <body> outside script and style."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_body = False
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if self.in_body and not self.skip:
            self.parts.append(data)

    def text(self):
        return " ".join(self.parts)


def visible_text(html):
    parser = VisibleText()
    parser.feed(html)
    return parser.text()


def visible_text_nodes(html):
    parser = VisibleText()
    parser.feed(html)
    return [part.strip() for part in parser.parts if part.strip()]


# «membership» is ordinary prose inside story text (membership leakage, family membership); the retired
# product copy lives in the site chrome and pages, so story pages (dated routes) are not checked for it.
STORY_PAGE_RE = re.compile(r"^\d{4}/\d{2}/\d{2}/|/\d{4}/\d{2}/\d{2}/")


class OneFcmoBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="c6-one-fcmo-")
        cls.out = Path(cls.tmp.name) / "site"
        result = subprocess.run([
            sys.executable, str(ROOT / "tools/paper/build.py"),
            "--stories", str(ROOT / "site/data/stories.v2.json"),
            "--status", str(ROOT / "site/data/newsroom-status.json"),
            "--editorial", str(ROOT / "editorial"),
            "--out", str(cls.out), "--base", BASE,
        ], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.routes = json.loads((cls.out / "data/routes.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def sample_pages(self):
        """Home, story, archive, corrections and search for each locale."""
        pages = []
        for locale_prefix in ("", "es/", "zh/"):
            pages += [self.out / locale_prefix / "index.html",
                      self.out / locale_prefix / "archive/index.html",
                      self.out / locale_prefix / "corrections/index.html",
                      self.out / locale_prefix / "search/index.html"]
        for locale in ("en", "es-419", "zh-Hans"):
            story = next(r for r in self.routes if r["kind"] == "story" and r["locale"] == locale)
            pages.append(self.out / story["path"] / "index.html")
        return [p for p in pages if p.exists()]


class TestC6OneFcmo(OneFcmoBuild):
    def test_c6_no_split_product_strings(self):
        """RED on main: DIRECCION §4 split labels such as 'fCMO /' and 'FCMO AI /', and 'membership'."""
        hits = []
        for page in sorted(self.out.rglob("*.html")):
            source = page.read_text(encoding="utf-8", errors="replace").lower()
            is_story = bool(STORY_PAGE_RE.search(page.relative_to(self.out).as_posix()))
            for needle in FORBIDDEN_PRODUCT_STRINGS:
                if is_story and needle == "membership":
                    continue
                if needle.lower() in source:
                    hits.append(f"{page.relative_to(self.out)}: {needle!r}")
        self.assertFalse(
            hits,
            "product-split strings still in built HTML (%d hits, first 25):\n%s"
            % (len(hits), "\n".join(hits[:25])),
        )

    def test_c6_no_raw_topic_slugs_in_visible_text(self):
        """RED on main: topic slugs such as recursive-self-improvement shown as text (DIRECCION §3)."""
        # Hyphenated topic slugs only: single words such as «agents» are also prose.
        slugs = sorted(p.name for p in (self.out / "topic").iterdir() if p.is_dir() and "-" in p.name)
        self.assertTrue(slugs, "no hyphenated topic directories were built")
        # A raw slug is a text node that is only the slug (a chip or label). A slug inside a
        # headline or sentence, such as «post-training», is ordinary prose.
        slug_set = {slug.lower() for slug in slugs}
        hits = []
        for page in self.sample_pages():
            for node in visible_text_nodes(page.read_text(encoding="utf-8", errors="replace")):
                if node.lower() in slug_set:
                    hits.append(f"{page.relative_to(self.out)}: {node!r}")
                    break
        self.assertFalse(
            hits,
            "raw topic slugs shown as visible text on %d sampled pages:\n%s" % (len(hits), "\n".join(hits[:25])),
        )

    def test_c6_old_product_routes_redirect(self):
        """RED on main: cartas/, empieza/ and diario/ still render full pages, not redirects (DIRECCION §4)."""
        standing = []
        for route in OLD_PRODUCT_ROUTES:
            page = self.out / route / "index.html"
            if not page.exists():
                standing.append(f"{route}: missing (must redirect, not vanish)")
            elif not REFRESH_RE.search(page.read_text(encoding="utf-8", errors="replace")):
                standing.append(f"{route}: still a standalone page, no redirect")
        self.assertFalse(standing, "old product routes still standalone:\n" + "\n".join(standing))

    def test_c6_one_wordmark_text_on_home(self):
        """RED on main while the home still carries product kickers; GREEN once one wordmark remains."""
        home = visible_text((self.out / "index.html").read_text(encoding="utf-8"))
        self.assertIn("FCMO AI", home)
        leftovers = [s for s in ("fCMO", "Follow both sides") if s in home]
        self.assertFalse(leftovers, "product-split leftovers on the home page: %s" % leftovers)


if __name__ == "__main__":
    unittest.main()
