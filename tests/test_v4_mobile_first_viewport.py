"""Mobile first viewport: a phone reader sees the FCMO AI lead headline on the first screen of /diario/."""

from __future__ import annotations

import contextlib
import copy
import html
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.paper.i18n import format_date, load_catalogs  # noqa: E402
from tools.paper.playwright_module import resolve_playwright_module  # noqa: E402
from tools.paper.status_banner import render  # noqa: E402

ORACLE = ROOT / "tests/oraculos/verificar_mobile_first_viewport.py"
BUILD_CSS = ROOT / "design/build_css.py"
PAPER_CSS = ROOT / "site-src/assets/css/paper.css"
TOKENS = ROOT / "design/tokens.json"
STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))
TRANSPORT_DOWN = {
    "en": "Today's edition is delayed. Last edition: {date}. Our news feed is not reaching us.",
    "es-419": "La edición de hoy está retrasada. Última edición: {date}. No estamos recibiendo nuestro flujo de noticias.",
    "zh-Hans": "今日版推迟发布。上一期：{date}。我们暂时收不到新闻数据流。",
}
REPEATED_INSTRUCTION = {"en": "see the system status page", "es-419": "consulta la página de estado",
                        "zh-Hans": "请查看系统状态页面"}
# The other edition strings, as they were before this pass; they must not move.
UNCHANGED = {
    "en": {"delayed": "Today's edition is delayed. Last edition: {date}.",
           "quiet": "No material changes since {date}; the system keeps checking sources.",
           "fresh": "Updated {date}", "stale_page": "This page may be out of date: its last update was {date}.",
           "status_link": "See the system status"},
    "es-419": {"delayed": "La edición de hoy está retrasada. Última edición: {date}.",
               "quiet": "Sin cambios materiales desde el {date}; el sistema sigue verificando las fuentes.",
               "fresh": "Actualizado el {date}",
               "stale_page": "Esta página podría estar desactualizada: su última actualización fue el {date}.",
               "status_link": "Ver el estado del sistema"},
    "zh-Hans": {"delayed": "今日版推迟发布。上一期：{date}。", "quiet": "自 {date} 以来没有实质性变化；系统仍在持续核查来源。",
                "fresh": "更新于 {date}", "stale_page": "本页面可能已过时：最后更新于 {date}。", "status_link": "查看系统状态"},
}
NAV_PATHS = ("", "cartas/", "empieza/", "comunidad/", "diario/", "archive/", "search/", "suscribete/")
STATUS_ROW = {"edition_state": "TRANSPORT_DOWN", "last_edition_at": "2026-09-23T11:32:15Z",
              "status_updated_at": "2026-09-27T00:54:13Z", "quiet_since": "2026-09-22T08:00:00Z"}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TransportDownCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogs = load_catalogs(ROOT)

    def banner(self, state: str, code: str) -> str:
        prefix = dict(LOCALES)[code]
        return render(dict(STATUS_ROW, edition_state=state), self.catalogs[code], base=BASE,
                      locale={"code": code, "path_prefix": prefix})

    def test_transport_down_says_the_fact_once_in_every_locale(self):
        for code, fact in TRANSPORT_DOWN.items():
            with self.subTest(locale=code):
                self.assertEqual(self.catalogs[code]["strings"]["edition"]["transport_down"], fact)
                self.assertNotIn(REPEATED_INSTRUCTION[code], self.catalogs[code]["strings"]["edition"]["transport_down"])

    def test_transport_down_banner_is_the_fact_then_one_status_link(self):
        for code, prefix in LOCALES:
            with self.subTest(locale=code):
                catalog = self.catalogs[code]
                date = format_date(STATUS_ROW["last_edition_at"], catalog, precision="minute")
                link = catalog["strings"]["edition"]["status_link"]
                out = self.banner("TRANSPORT_DOWN", code)
                self.assertEqual(out, (
                    '<div class="status-banner" data-edition-state="TRANSPORT_DOWN" data-edition-at="2026-09-23T11:32:15Z">'
                    f'<!-- slot:banner -->{TRANSPORT_DOWN[code].format(date=date)} '
                    f'<a href="{BASE}{prefix}status/">{html.escape(link)}</a></div>'))
                self.assertEqual(re.findall(r'<a href="([^"]*)"', out), [f"{BASE}{prefix}status/"])
                self.assertNotIn(REPEATED_INSTRUCTION[code], out)

    def test_delayed_quiet_and_fresh_are_untouched(self):
        en = {
            "FRESH": '<p class="edition-update">Updated September 23, 2026</p><div class="status-banner" hidden data-edition-state="FRESH" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->This page may be out of date: its last update was September 23, 2026. <a href="/FCMO-AI-Newsletter/status/">See the system status</a></div>',
            "QUIET": '<div class="status-banner" data-edition-state="QUIET" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->No material changes since September 22, 2026; the system keeps checking sources.</div>',
            "DELAYED": '<div class="status-banner" data-edition-state="DELAYED" data-edition-at="2026-09-23T11:32:15Z"><!-- slot:banner -->Today\'s edition is delayed. Last edition: September 23, 2026. <a href="/FCMO-AI-Newsletter/status/">See the system status</a></div>',
        }
        for state, literal in en.items():
            with self.subTest(state=state):
                self.assertEqual(self.banner(state, "en"), literal)
        for code, strings in UNCHANGED.items():
            for key, value in strings.items():
                with self.subTest(locale=code, key=key):
                    self.assertEqual(self.catalogs[code]["strings"]["edition"][key], value)


class CompactChromeCssTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load("build_css_p5", BUILD_CSS)
        cls.block = cls.module.MOBILE_FIRST_VIEWPORT_CSS
        cls.paper = PAPER_CSS.read_text(encoding="utf-8")

    def test_generator_output_carries_the_block_and_paper_css_carries_it_verbatim(self):
        rendered = self.module.render(json.loads(TOKENS.read_text(encoding="utf-8")))
        self.assertTrue(rendered.endswith(self.block))
        self.assertEqual(self.paper.count(self.block), 1)
        self.assertLess(len(self.block.encode("utf-8")), 1536)

    def test_block_is_phone_only_and_wins_over_the_earlier_phone_blocks(self):
        self.assertTrue(self.block.startswith("/* v4 p5 mobile first viewport */\n@media(max-width:520px){"))
        self.assertEqual(self.block.count("@media"), 1)
        at = self.paper.index(self.block)
        self.assertGreater(at, self.paper.rindex("@media(max-width:520px){", 0, at))
        # Every class the block styles: no phone block after it may style them again.
        styled = set(re.findall(r"\.([a-z][a-z-]*)", self.block.split("{", 1)[1]))
        self.assertGreaterEqual(styled, {"edition-line", "brand-sub", "breadcrumbs", "masthead", "brand", "main-nav",
                                         "status-banner", "corpus-freshness"})
        for later in re.findall(r"@media\(max-width:520px\)\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", self.paper[at + len(self.block):]):
            self.assertEqual(styled & set(re.findall(r"\.([a-z][a-z-]*)", later)), set(), later[:120])
        for rule in (".edition-line,.brand-sub,.page-front .breadcrumbs{display:none}",
                     ".site-header .masthead{padding:.5rem 0}", ".site-header .masthead .brand{font-size:2.4rem}",
                     ".main-nav{flex-wrap:nowrap;"):
            self.assertIn(rule, self.block)

    def test_block_uses_only_existing_tokens_and_never_hides_the_truth_signals(self):
        self.assertNotIn("!important", self.block)
        defined = set(re.findall(r"(--[a-z0-9-]+):", self.paper.replace(self.block, "")))
        used = set(re.findall(r"var\((--[a-z0-9-]+)\)", self.block))
        self.assertTrue(used)
        self.assertLessEqual(used, defined)
        self.assertEqual(re.findall(r"(--[a-z0-9-]+):", self.block), [])
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", self.block.split("{", 1)[1]):
            if "status-banner" in selector.split(",")[-1].split("+")[-1] or "corpus-freshness" in selector:
                self.assertNotRegex(body, r"display:none|visibility:hidden|overflow:hidden|max-height|clip|line-clamp")


class BuiltDiarioChromeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name) / "site"
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(STATUS),
             "--out", str(cls.out), "--base", BASE], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_diario_html_keeps_every_header_element_and_the_same_nav_destinations(self):
        for code, prefix in LOCALES:
            with self.subTest(locale=code):
                page = (self.out / prefix / "diario/index.html").read_text(encoding="utf-8")
                header = page[page.index('<header class="site-header">'):page.index("</header>")]
                self.assertEqual(header.count('<span class="edition-line">'), 1)
                self.assertEqual(header.count('<span class="brand-sub">'), 1)
                self.assertEqual(page.count('<nav class="breadcrumbs"'), 1)
                nav = re.search(r'<nav class="main-nav"[^>]*>(.*?)</nav>', header, re.S).group(1)
                self.assertEqual(set(re.findall(r'href="([^"]*)"', nav)), {f"{BASE}{prefix}{path}" for path in NAV_PATHS})


class EvaluateRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = load("verificar_mobile_first_viewport_p5", ORACLE)

    @staticmethod
    def rect(top: float, bottom: float, left: float = 16, right: float = 374, visible: bool = True, **extra) -> dict:
        return {"top": top, "bottom": bottom, "left": left, "right": right, "height": bottom - top, "visible": visible, **extra}

    def healthy(self) -> dict:
        r = self.rect
        nav_hrefs = [f"{BASE}{path}" for path in NAV_PATHS]
        shown = {"empieza/", "comunidad/", "archive/", "search/", "suscribete/"}
        mobile = {
            "h1": r(400, 570), "leadHref": f"{BASE}2026/09/13/lead/",
            "zones": [r(85, 169, 16, 195), r(85, 169, 195, 374)],
            "languages": [r(10, 31, 16, 70), r(10, 31, 160, 230), r(10, 31, 300, 374)],
            "banner": {"state": "TRANSPORT_DOWN", "clipped": False, **r(223, 306)},
            "freshness": {"clipped": False, **r(306, 346)},
            "nav": {**r(170, 214), "links": [{"href": href, **r(170, 214, visible=href[len(BASE):] in shown)}
                                             for href in nav_hrefs]},
            "headerHrefs": [f"{BASE}", f"{BASE}cartas/", f"{BASE}diario/", *[f"{BASE}{p}" for p in sorted(shown)]],
            "scrollWidth": 390, "clientWidth": 390, "consoleErrors": [], "failedRequests": [],
        }
        desktop = {"editionLine": True, "brandSub": True, "breadcrumbs": True, "scrollWidth": 1440, "clientWidth": 1440,
                   "consoleErrors": [], "failedRequests": []}
        page = {"scrollWidth": 390, "clientWidth": 390, "consoleErrors": [], "failedRequests": []}
        codes = [code for code, _ in LOCALES]
        return {"mobile": {code: copy.deepcopy(mobile) for code in codes},
                "desktop": {code: copy.deepcopy(desktop) for code in codes},
                "pages": [{"kind": kind, "locale": code, **copy.deepcopy(page)} for code in codes for kind in ("landing", "story")]}

    def rules(self, measurements: dict) -> list[str]:
        return [violation.split(" ", 1)[0] for violation in self.oracle.evaluate(measurements)]

    def test_a_healthy_first_viewport_has_no_violation(self):
        self.assertEqual(self.oracle.evaluate(self.healthy()), [])
        edge = self.healthy()
        edge["mobile"]["en"]["h1"] = self.rect(460, 844)
        edge["mobile"]["en"]["nav"]["links"][2]["top"] = 172
        fresh = edge["mobile"]["es-419"]
        fresh["banner"] = {"state": "FRESH", "clipped": False, **self.rect(0, 0, visible=False)}
        self.assertEqual(self.oracle.evaluate(edge), [])

    def test_every_rule_reports_its_own_violation(self):
        r = self.rect

        def mobile(key, value):
            return lambda m: m["mobile"]["zh-Hans"].__setitem__(key, value)

        def nav_link(index, **changes):
            return lambda m: m["mobile"]["es-419"]["nav"]["links"][index].update(changes)

        def en(key):
            return lambda change: (lambda m: change(m["mobile"]["en"][key]))

        zones, languages, banner, fresh, nav = en("zones"), en("languages"), en("banner"), en("freshness"), en("nav")
        cases = [
            ("h1-top", mobile("h1", r(461, 600))),
            ("h1-bottom", mobile("h1", r(400, 845))),
            ("zone-switch", zones(lambda z: z[1].update(bottom=845))),
            ("zone-switch", zones(lambda z: z[0].update(visible=False))),
            ("zone-switch", zones(lambda z: z[0].update(top=-1))),
            ("zone-switch", zones(lambda z: z[0].update(left=-1))),
            ("zone-switch", zones(lambda z: z.append(dict(z[1])))),
            ("zone-switch", zones(lambda z: z.pop())),
            ("language-nav", languages(lambda a: a[2].update(right=391))),
            ("language-nav", languages(lambda a: a[0].update(visible=False))),
            ("language-nav", languages(lambda a: a.clear())),
            ("banner-above-h1", banner(lambda b: b.update(clipped=True))),
            ("banner-above-h1", banner(lambda b: b.update(visible=False))),
            ("banner-above-h1", banner(lambda b: b.update(bottom=401))),
            ("banner-above-h1", banner(lambda b: b.pop("state"))),
            ("banner-above-h1", mobile("banner", None)),
            ("freshness-above-h1", fresh(lambda f: f.update(bottom=401))),
            ("freshness-above-h1", fresh(lambda f: f.update(clipped=True))),
            ("freshness-above-h1", fresh(lambda f: f.update(visible=False))),
            ("freshness-above-h1", mobile("freshness", None)),
            ("nav-height", nav(lambda n: n.update(height=49))),
            ("nav-height", nav(lambda n: n.update(visible=False))),
            ("nav-row", nav_link(3, top=173)),
            ("nav-row", nav_link(7, right=391)),
            ("nav-row", nav_link(2, left=-1)),
            ("nav-reachable", lambda m: m["mobile"]["en"]["headerHrefs"].remove(f"{BASE}cartas/")),
            ("nav-reachable", nav_link(0, href=f"{BASE}elsewhere/")),
            ("overflow", mobile("scrollWidth", 391)),
            ("overflow", lambda m: m["mobile"]["en"].pop("clientWidth")),
            ("banner-above-h1", banner(lambda b: b.update(right=391))),
            ("freshness-above-h1", fresh(lambda f: f.update(left=-1))),
            ("desktop-overflow", lambda m: m["desktop"]["es-419"].pop("scrollWidth")),
            ("page-overflow", lambda m: m["pages"][4].pop("clientWidth")),
            ("console", lambda m: m["mobile"]["en"]["consoleErrors"].append("boom")),
            ("requests", lambda m: m["mobile"]["en"]["failedRequests"].append("x.css HTTP 404")),
            ("desktop-chrome", lambda m: m["desktop"]["es-419"].update(breadcrumbs=False)),
            ("desktop-chrome", lambda m: m["desktop"]["en"].update(editionLine=False)),
            ("desktop-chrome", lambda m: m["desktop"]["zh-Hans"].update(brandSub=False)),
            ("desktop-overflow", lambda m: m["desktop"]["en"].update(scrollWidth=1441)),
            ("desktop-console", lambda m: m["desktop"]["en"]["consoleErrors"].append("boom")),
            ("desktop-console", lambda m: m["desktop"]["en"]["failedRequests"].append("x.js HTTP 404")),
            ("page-overflow", lambda m: m["pages"][1].update(scrollWidth=400)),
            ("page-console", lambda m: m["pages"][2]["consoleErrors"].append("boom")),
            ("page-console", lambda m: m["pages"][3]["failedRequests"].append("x.png HTTP 404")),
            ("coverage", lambda m: m["pages"].pop()),
            ("coverage", lambda m: m["mobile"].pop("en")),
            ("coverage", lambda m: m["desktop"].pop("zh-Hans")),
        ]
        seen = set()
        for index, (rule, mutate) in enumerate(cases):
            with self.subTest(case=index, rule=rule):
                measurements = self.healthy()
                mutate(measurements)
                self.assertEqual(self.rules(measurements), [rule])
                seen.add(rule)
        self.assertEqual(seen, {"h1-top", "h1-bottom", "zone-switch", "language-nav", "banner-above-h1",
                                "freshness-above-h1", "nav-height", "nav-row", "nav-reachable", "overflow", "console",
                                "requests", "desktop-chrome", "desktop-overflow", "desktop-console", "page-overflow",
                                "page-console", "coverage"})

    def test_the_h1_budget_is_460_px_and_a_missing_signal_is_a_violation(self):
        at_461 = self.healthy()
        at_461["mobile"]["en"]["h1"] = self.rect(461, 600)
        violations = self.oracle.evaluate(at_461)
        self.assertEqual(len(violations), 1)
        self.assertIn("461px", violations[0])
        hidden = self.healthy()
        hidden["mobile"]["en"]["freshness"]["visible"] = False
        hidden["mobile"]["es-419"]["banner"]["visible"] = False
        self.assertEqual(self.rules(hidden), ["freshness-above-h1", "banner-above-h1"])
        self.assertIn("coverage", self.rules({"mobile": {}, "desktop": {}, "pages": []}))
        missing = self.healthy()
        missing["mobile"]["zh-Hans"]["h1"] = None
        # Without a lead h1 nothing can be proven to sit above it.
        self.assertEqual(self.rules(missing), ["h1-top", "banner-above-h1", "freshness-above-h1"])


class OracleBrowserGateTests(unittest.TestCase):
    def test_a_missing_playwright_module_fails_before_building(self):
        oracle = load("verificar_mobile_first_viewport_gate", ORACLE)
        stdout = io.StringIO()
        with mock.patch.object(oracle, "build_site", side_effect=AssertionError("built")) as build, \
                contextlib.redirect_stdout(stdout):
            code = oracle.main(["--playwright-module", "/nonexistent/playwright/index.js"])
        self.assertEqual(code, 1)
        self.assertIn("BROWSER_UNAVAILABLE", stdout.getvalue())
        build.assert_not_called()

    def run_main(self, measurements: dict, gates: tuple[bool, str]) -> tuple[int, str, str]:
        oracle = load("verificar_mobile_first_viewport_main", ORACLE)
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(oracle, "module_loads", return_value=True), \
                mock.patch.object(oracle, "build_site"), \
                mock.patch.object(oracle, "measure", return_value=measurements), \
                mock.patch.object(oracle, "gates", return_value=gates), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = oracle.main(["--playwright-module", "/any/playwright/index.js"])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_main_passes_only_when_the_rules_and_the_gates_pass(self):
        healthy = EvaluateRulesTests("test_a_healthy_first_viewport_has_no_violation").healthy()
        code, out, _ = self.run_main(healthy, (True, "GATES PASS (13/13)"))
        self.assertEqual(code, 0)
        self.assertIn("MOBILE FIRST VIEWPORT OK h1-top en=400px es-419=400px zh-Hans=400px", out)
        code, out, err = self.run_main(healthy, (False, "GATE FAIL [NO_FCMO_GROUP]"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("- gates: GATE FAIL [NO_FCMO_GROUP]", err)
        late = copy.deepcopy(healthy)
        late["mobile"]["es-419"]["h1"]["top"] = 461
        code, out, err = self.run_main(late, (True, "GATES PASS (13/13)"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("MOBILE FIRST VIEWPORT FAIL h1-top en=400px es-419=461px zh-Hans=400px", err)

    def test_the_script_exits_1_with_browser_unavailable(self):
        result = subprocess.run([sys.executable, str(ORACLE), "--playwright-module", "/nonexistent/playwright/index.js"],
                                cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 1)
        self.assertIn("BROWSER_UNAVAILABLE", result.stdout + result.stderr)


class OracleInBrowserTests(unittest.TestCase):
    def test_the_real_build_passes_the_first_viewport_oracle(self):
        module = resolve_playwright_module()
        if not module:
            self.skipTest("Playwright module does not resolve from this checkout")
        result = subprocess.run([sys.executable, str(ORACLE), "--playwright-module", module, "--print-measurements"],
                                cwd=ROOT, capture_output=True, text=True, timeout=900)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MOBILE FIRST VIEWPORT OK", result.stdout)
        measurements = json.loads(next(line for line in result.stdout.splitlines() if line.startswith("{")))
        for code, prefix in LOCALES:
            with self.subTest(locale=code):
                mobile = measurements["mobile"][code]
                links = mobile["nav"]["links"]
                # The probe must see what CSS hides: three nav links hidden, five shown, and only visible,
                # non-language header links (logo, two doors, five nav links) offered as ways to reach them.
                self.assertEqual([link["visible"] for link in links], [False, False, True, True, False, True, True, True])
                self.assertEqual(len(mobile["headerHrefs"]), 8)
                self.assertFalse(mobile["banner"]["clipped"])
                self.assertFalse(mobile["freshness"]["clipped"])


if __name__ == "__main__":
    unittest.main()
