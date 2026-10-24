"""C6 design contract oracles (campaign c6, DIRECCION §5 and §3).

Named ``test_c6_*`` so the integration step reports them separately. Not
skipped: on main they are expected RED with the reasons listed in each
failure message. Layout checks that need a browser (20-second line above the
tabs, sources inside 844 px at 390 px, axe) live in tests/oraculos/verificar_c6.py.
"""

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
BASE = "/FCMO-AI-Newsletter/"

from tools.paper.i18n import headline, load_catalogs  # noqa: E402

# DIRECCION §5: evidence classes. Hatching is reserved for «Claimed» only.
HATCHED_FORBIDDEN_KINDS = ("INFERRED", "DISPUTED", "unrated", "SPECULATIVE")
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
VERIFIED_WORD_RE = re.compile(r"verified|verificad|核实|验证", re.IGNORECASE)
NEGATED_VERIFIED_RE = re.compile(r"not verified|sin verificar|未经|unverified|no verificad|未(?:经)?(?:核实|验证)", re.IGNORECASE)
LEDGER_MAP_RE = re.compile(r"const open=(\{.*?\});", re.DOTALL)


class DesignContractTokens(unittest.TestCase):
    def test_c6_tokens_have_oxblood_for_not_established(self):
        """RED on main: DIRECCION §5 adds `oxblood` for «Not established» (contrast ≥4.5:1 on bone); absent today."""
        tokens = json.loads((ROOT / "design/tokens.json").read_text(encoding="utf-8"))
        self.assertIn("oxblood", tokens["color"], "design/tokens.json has no oxblood color for Not established")

    def test_c6_tokens_drop_product_brand_colors(self):
        """RED on main: DIRECCION §5 removes brands.group and brands.ai, product colours that split the brand."""
        tokens = json.loads((ROOT / "design/tokens.json").read_text(encoding="utf-8"))
        brands = tokens.get("brands", {})
        present = sorted(name for name in ("group", "ai") if name in brands)
        self.assertFalse(present, "product brand palettes still in tokens: %s" % present)


class DesignContractCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "site-src/assets/css/paper.css").read_text(encoding="utf-8")
        cls.rules = [(sel.strip(), body) for sel, body in RULE_RE.findall(cls.css)]

    def test_c6_only_claimed_is_hatched(self):
        """RED on main: the striped pattern marks INFERRED, DISPUTED and unrated, not Claimed (DIRECCION §5: «Rayado = Claimed»)."""
        hatched = [sel for sel, body in self.rules if "repeating-linear-gradient" in body]
        wrong = [sel for sel in hatched if any(kind in sel for kind in HATCHED_FORBIDDEN_KINDS)]
        claimed = [sel for sel in hatched if "CLAIMED" in sel.upper()]
        messages = []
        if wrong:
            messages.append("hatching applied to non-Claimed classes: " + " | ".join(wrong[:6]))
        if not claimed:
            messages.append("no hatched selector for CLAIMED (the only class that must be striped)")
        self.assertFalse(messages, "; ".join(messages))


class DesignContractBuilt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="c6-design-")
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

    def story_pages(self):
        pages = []
        for locale in ("en", "es-419", "zh-Hans"):
            for row in [r for r in self.routes if r["kind"] == "story" and r["locale"] == locale][:2]:
                pages.append(self.out / row["path"] / "index.html")
        return pages

    def test_c6_evidence_ledger_open_in_summary(self):
        """RED on main: DIRECCION §3/§5 want the evidence book visible with 0 clicks; the summary mode opens only «argument»."""
        closed = []
        for page in self.story_pages():
            source = page.read_text(encoding="utf-8", errors="replace")
            match = LEDGER_MAP_RE.search(source)
            if not match:
                closed.append(f"{page.relative_to(self.out)}: no reader mode map found")
                continue
            summary = re.search(r"summary:\s*\[([^\]]*)\]", match.group(1))
            if not summary or "dossier" not in summary.group(1):
                closed.append(f"{page.relative_to(self.out)}: summary mode keeps the dossier closed")
        self.assertFalse(closed, "evidence ledger closed by default on %d pages:\n%s" % (len(closed), "\n".join(closed[:10])))

    def test_c6_no_verified_heading_for_unverified_items(self):
        """Guard: no heading the design writes may say «verified» (DIRECCION §3, «Recently verified»).

        Story headlines are the newsroom's words about the subject (e.g. «machine-checked proofs»), not a claim
        by the design, so headings that are exactly a story headline are out of scope; every other heading is in.
        """
        catalogs = load_catalogs(ROOT)
        stories = json.loads((ROOT / "site/data/stories.v2.json").read_text(encoding="utf-8"))["stories"]
        headlines = {headline(story, code, catalog) for story in stories for code, catalog in catalogs.items()}
        pages = [self.out / prefix / "index.html" for prefix in ("", "es", "zh")]
        for locale in ("en", "es-419", "zh-Hans"):
            pages += [self.out / row["path"] / "index.html"
                      for row in [r for r in self.routes if r["kind"] == "story" and r["locale"] == locale][:20]]
        bad = []
        for page in pages:
            for text in verified_chrome_headings(page.read_text(encoding="utf-8", errors="replace"), headlines):
                bad.append(f"{page.relative_to(self.out)}: {text[:80]!r}")
        self.assertFalse(bad, "verified-as-heading on claimed material:\n" + "\n".join(bad[:10]))


class VerifiedHeadingGuard(unittest.TestCase):
    """The guard above must stay able to go red on chrome while ignoring the newsroom's own headlines."""

    def test_chrome_headings_that_say_verified_are_flagged(self):
        for heading in ("<h2>Recently verified</h2>", "<h2 class=\"x\">Verificado recientemente</h2>",
                        "<h3>最近核实</h3>", "<h1><a href=\"#\">Verified facts</a></h1>"):
            with self.subTest(heading=heading):
                self.assertEqual(len(verified_chrome_headings(heading, set())), 1)

    def test_negated_wording_and_story_headlines_are_not_flagged(self):
        headline_text = "Anthropic y OSS-Fuzz: pruebas verificadas por máquina"
        page = (f"<h1>{html.escape(headline_text)}</h1><h2>Claimed, not verified</h2><h2>Sin verificar</h2>"
                f"<h3><a href=\"/s/\">{html.escape(headline_text)}</a></h3>")
        self.assertEqual(verified_chrome_headings(page, {headline_text}), [])
        # The same words outside a story headline are chrome, and are flagged.
        self.assertEqual(verified_chrome_headings(page.replace("<h1>", "<h1>Earlier: "), {headline_text}),
                         ["Earlier: " + headline_text])


def verified_chrome_headings(source, story_headlines):
    """Heading texts that say «verified» without negation and are not exactly a story headline."""
    flagged = []
    for heading in HEADING_RE.findall(source):
        text = html.unescape(strip_tags(heading))
        if text in story_headlines:
            continue
        if VERIFIED_WORD_RE.search(text) and not NEGATED_VERIFIED_RE.search(text):
            flagged.append(text)
    return flagged


def strip_tags(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip()


if __name__ == "__main__":
    unittest.main()
