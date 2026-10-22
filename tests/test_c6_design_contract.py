"""C6 design contract oracles (campaign c6, DIRECCION §5 and §3).

Named ``test_c6_*`` so the integration step reports them separately. Not
skipped: on main they are expected RED with the reasons listed in each
failure message. Layout checks that need a browser (20-second line above the
tabs, sources inside 844 px at 390 px, axe) live in tests/oraculos/verificar_c6.py.
"""

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = "/FCMO-AI-Newsletter/"

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
        """Guard: no heading may say «verified» for an item that is only claimed (DIRECCION §3, «Recently verified»)."""
        bad = []
        for page in self.story_pages() + [self.out / "index.html"]:
            source = page.read_text(encoding="utf-8", errors="replace")
            for heading in HEADING_RE.findall(source):
                text = strip_tags(heading)
                if VERIFIED_WORD_RE.search(text) and not NEGATED_VERIFIED_RE.search(text):
                    bad.append(f"{page.relative_to(self.out)}: {text[:80]!r}")
        self.assertFalse(bad, "verified-as-heading on claimed material:\n" + "\n".join(bad[:10]))


def strip_tags(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip()


if __name__ == "__main__":
    unittest.main()
