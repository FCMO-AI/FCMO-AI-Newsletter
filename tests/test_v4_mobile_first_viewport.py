"""Mobile first viewport: a phone reader sees the FCMO AI lead headline on the first screen of the locale front."""

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

from tools.paper.playwright_module import browser_unavailable  # noqa: E402

from tools.paper.i18n import format_date, load_catalogs  # noqa: E402
from tools.paper.playwright_module import resolve_playwright_module  # noqa: E402
from tools.paper.status_banner import render  # noqa: E402
from tests._browser import browser_available, skip_or_fail  # noqa: E402

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
        # CONTRACT-CHANGES.md #9: the phone block governs the first-screen truth signals of the single
        # header (top bar, bottom tabs) and must not style the retired two-product chrome.
        styled = set(re.findall(r"\.([a-z][a-z-]*)", self.block.split("{", 1)[1]))
        self.assertGreaterEqual(styled, {"status-banner", "corpus-freshness"})
        for later in re.findall(r"@media\(max-width:520px\)\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", self.paper[at + len(self.block):]):
            self.assertFalse(styled & set(re.findall(r"\.([a-z][a-z-]*)", later)) & {"status-banner", "corpus-freshness"}, later[:120])
        self.assertNotRegex(self.block, r"\.(site-header|brand-sub|main-nav|edition-line|zone-switch|footer-links|language-nav)\b")

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

    def test_final_mobile_chrome_uses_a_native_menu_with_44px_control(self):
        css = (ROOT / "site-src/assets/css/d/d-base.css").read_text()
        self.assertIn("@media(max-width:1000px){.d-nav .topnav,.d-nav .langsel{display:none}", css)
        self.assertIn(".d-menu{display:block;margin-left:auto}", css)
        self.assertIn(".d-menu summary{width:44px;min-height:44px;display:grid;place-items:center}", css)
        self.assertIn(".d-menu-links a{min-width:44px}", css)

    def test_story_prose_wraps_long_unbroken_text_without_story_specific_rules(self):
        rendered = self.module.render(json.loads(TOKENS.read_text(encoding="utf-8")))
        for css in (self.paper, rendered):
            self.assertRegex(css, r"\.story-body\{[^}]*overflow-wrap:anywhere")


class BuiltFrontChromeTests(unittest.TestCase):
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

    def test_front_has_one_header_native_menu_and_footer_corrections_in_every_locale(self):
        for code, prefix in LOCALES:
            top_nav = {f"{BASE}{prefix}{path}" for path in
                       ("", "letters/", "#topics", "archive/", "method/", "search/?focus=1")}
            with self.subTest(locale=code):
                page = (self.out / prefix / "index.html").read_text(encoding="utf-8")
                self.assertEqual(page.count("<header "), 1)
                header = page[page.index('<header class="topbar'):page.index("</header>")]
                self.assertNotIn('class="brand-sub"', page)
                self.assertNotIn('class="site-header"', page)
                nav = re.search(r'<nav class="topnav"[^>]*>(.*?)</nav>', header, re.S).group(1)
                self.assertEqual(set(re.findall(r'href="([^"]*)"', nav)), top_nav)
                menu = re.search(r'<details class="d-menu">(.*?)</details>', header, re.S).group(1)
                self.assertRegex(menu, r'<summary aria-label="[^"]+">')
                self.assertEqual(set(re.findall(r'<a href="([^"]*)"(?: aria-current="page")?>', menu)), top_nav)
                self.assertEqual(set(re.findall(r'<a href="([^"]+)" hreflang="([^"]+)"', menu)),
                                 {(f"{BASE}{p}", c) for c, p in LOCALES})
                self.assertNotIn('class="tabbar"', page)
                footer = re.search(r'<footer class="d-footer.*?</footer>', page, re.S).group()
                for path in ('corrections/', 'subscribe/'):
                    self.assertIn(f'href="{BASE}{prefix}{path}"', footer)
                for url in top_nav:
                    rel = url.removeprefix(BASE).split('#')[0].split('?')[0]
                    self.assertTrue((self.out / rel / 'index.html').is_file(), url)



class EvaluateRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = load("verificar_mobile_first_viewport_p5", ORACLE)

    @staticmethod
    def rect(top: float, bottom: float, left: float = 16, right: float = 374, visible: bool = True, **extra) -> dict:
        return {"top": top, "bottom": bottom, "left": left, "right": right, "height": bottom - top, "visible": visible, **extra}

    def healthy(self) -> dict:
        r = self.rect

        def mobile_for(prefix: str) -> dict:
            nav = [f"{BASE}{prefix}{path}" for path in ("", "letters/", "#topics", "archive/", "method/", "search/?focus=1")]
            menu_links = [{"href": href, **r(68 + 44*i, 112 + 44*i, 16, 200)} for i, href in enumerate(nav)]
            languages = [{"href": f"{BASE}{p}", "lang": code, **r(340, 384, 16+100*i, 100+100*i)}
                         for i, (code, p) in enumerate(LOCALES)]
            return {
                "h1": r(165, 273), "leadHref": f"{BASE}{prefix}2026/09/13/lead/", "zoneSwitch": 0,
                "languages": languages,
                "banner": {"state": "DELAYED", "clipped": False, **r(60, 82)},
                "freshness": {"clipped": False, **r(84, 113)},
                "topbar": {**r(0, 68, 0, 390), "items": [r(6, 50, 16, 120), r(6, 50, 200, 244), r(6, 50, 292, 336)]},
                "menu": {"summary": r(6, 50, 200, 244), "initiallyClosed": True, "opened": True,
                         "closed": True, "headlineTop": 165, "links": menu_links + languages},
                "headers": 1, "tabbarPresent": False,
                "footerLinks": [{"href": f"{BASE}{prefix}{p}", **r(950, 994)} for p in ("corrections/", "subscribe/")],
                "navLinks": [{"href": href, **r(0, 0, visible=False)} for href in nav],
                "topicsTarget": True,
                "visibleHrefs": nav,
                "scrollWidth": 390, "clientWidth": 390, "consoleErrors": [], "failedRequests": [],
            }

        def desktop_for(prefix: str) -> dict:
            nav = [f"{BASE}{prefix}{path}" for path in ("", "letters/", "#topics", "archive/", "method/", "search/?focus=1")]
            return {"zoneSwitch": 0, "brandmark": True, "freshnessLine": True, "tabbarVisible": False,
                    "topnav": {**r(0, 56, 160, 800), "links": [{"href": href, **r(6, 50, 160 + 100 * i, 250 + 100 * i)} for i, href in enumerate(nav)]},
                    "scrollWidth": 1440, "clientWidth": 1440, "consoleErrors": [], "failedRequests": []}

        page = {"scrollWidth": 390, "clientWidth": 390, "consoleErrors": [], "failedRequests": []}
        return {"mobile": {code: mobile_for(prefix) for code, prefix in LOCALES},
                "desktop": {code: desktop_for(prefix) for code, prefix in LOCALES},
                "pages": [{"kind": kind, "locale": code, **copy.deepcopy(page)} for code, _ in LOCALES for kind in ("landing", "story")]}

    def rules(self, measurements: dict) -> list[str]:
        return [violation.split(" ", 1)[0] for violation in self.oracle.evaluate(measurements)]

    def test_a_healthy_first_viewport_has_no_violation(self):
        self.assertEqual(self.oracle.evaluate(self.healthy()), [])
        edge = self.healthy()
        edge["mobile"]["en"]["h1"] = self.rect(460, 844)  # same first-screen budget without bottom tabs
        edge["mobile"]["en"]["menu"]["headlineTop"] = 460
        fresh = edge["mobile"]["es-419"]
        fresh["banner"] = {"state": "FRESH", "clipped": False, **self.rect(0, 0, visible=False)}
        edge["mobile"]["es-419"]["topbar"]["height"] = 56
        self.assertEqual(self.oracle.evaluate(edge), [])

    def test_every_rule_reports_its_own_violation(self):
        r = self.rect

        def mobile(key, value, code="zh-Hans"):
            return lambda m: m["mobile"][code].__setitem__(key, value)

        def en(key):
            return lambda change: (lambda m: change(m["mobile"]["en"][key]))

        def menu_link(index, **changes):
            return lambda m: m["mobile"]["es-419"]["menu"]["links"][index].update(changes)

        languages, banner, fresh, bar, menu = en("languages"), en("banner"), en("freshness"), en("topbar"), en("menu")
        cases = [
            ("h1-top", mobile("h1", r(461, 600))),
            ("h1-top", mobile("h1", None)),
            ("h1-bottom", mobile("h1", r(400, 845))),
            ("one-fcmo", mobile("zoneSwitch", 1)),
            ("one-fcmo", mobile("zoneSwitch", 2)),
            ("language-nav", languages(lambda a: a[2].update(right=391))),
            ("language-nav", languages(lambda a: a[0].update(visible=False))),
            ("language-nav", languages(lambda a: a.clear())),
            ("banner-above-h1", banner(lambda b: b.update(clipped=True))),
            ("banner-above-h1", banner(lambda b: b.update(visible=False))),
            ("banner-above-h1", banner(lambda b: b.update(bottom=166))),
            ("banner-above-h1", banner(lambda b: b.pop("state"))),
            ("banner-above-h1", banner(lambda b: b.update(right=391))),
            ("banner-above-h1", mobile("banner", None)),
            ("freshness-above-h1", fresh(lambda f: f.update(bottom=166))),
            ("freshness-above-h1", fresh(lambda f: f.update(clipped=True))),
            ("freshness-above-h1", fresh(lambda f: f.update(visible=False))),
            ("freshness-above-h1", fresh(lambda f: f.update(left=-1))),
            ("freshness-above-h1", mobile("freshness", None)),
            ("topbar-height", bar(lambda b: b.update(height=70))),
            ("topbar-height", bar(lambda b: b.update(visible=False))),
            ("topbar-row", bar(lambda b: b["items"][1].update(top=40, bottom=84))),
            ("topbar-row", bar(lambda b: b["items"][2].update(right=391))),
            ("topbar-row", bar(lambda b: b["items"].clear())),
            ("menu-usable", menu(lambda m: m["summary"].update(right=243))),
            ("menu-usable", menu(lambda m: m["summary"].update(height=43))),
            ("menu-usable", menu(lambda m: m.update(opened=False))),
            ("menu-usable", menu(lambda m: m.update(initiallyClosed=False))),
            ("menu-usable", menu_link(3, height=43)),
            ("menu-usable", menu_link(4, visible=False)),
            ("menu-usable", menu_link(0, href=f"{BASE}elsewhere/")),
            ("menu-usable", lambda m: m["mobile"]["es-419"]["menu"]["links"].pop()),
            ("menu-restored", menu(lambda m: m.update(closed=False))),
            ("menu-restored", menu(lambda m: m.update(headlineTop=166))),
            ("menu-restored", mobile("headers", 2)),
            ("menu-restored", mobile("tabbarPresent", True)),
            ("nav-reachable", lambda m: m["mobile"]["en"]["footerLinks"].pop(0)),
            ("nav-reachable", lambda m: m["mobile"]["en"]["visibleHrefs"].remove(f"{BASE}method/")),
            ("nav-reachable", lambda m: m["mobile"]["en"].update(topicsTarget=False)),
            ("nav-reachable", lambda m: m["mobile"]["en"]["navLinks"][0].update(href=f"{BASE}elsewhere/")),
            ("nav-reachable", lambda m: m["mobile"]["en"]["navLinks"].pop()),
            ("overflow", mobile("scrollWidth", 391)),
            ("overflow", lambda m: m["mobile"]["en"].pop("clientWidth")),
            ("console", lambda m: m["mobile"]["en"]["consoleErrors"].append("boom")),
            ("requests", lambda m: m["mobile"]["en"]["failedRequests"].append("x.css HTTP 404")),
            ("desktop-chrome", lambda m: m["desktop"]["es-419"].update(freshnessLine=False)),
            ("desktop-chrome", lambda m: m["desktop"]["en"].update(brandmark=False)),
            ("desktop-chrome", lambda m: m["desktop"]["zh-Hans"]["topnav"]["links"][1].update(visible=False)),
            ("desktop-chrome", lambda m: m["desktop"]["en"]["topnav"]["links"][4].update(top=60, bottom=90)),
            ("desktop-chrome", lambda m: m["desktop"]["en"].update(topnav=None)),
            ("desktop-chrome", lambda m: m["desktop"]["en"].update(tabbarVisible=True)),
            ("desktop-one-fcmo", lambda m: m["desktop"]["en"].update(zoneSwitch=2)),
            ("desktop-overflow", lambda m: m["desktop"]["es-419"].pop("scrollWidth")),
            ("desktop-overflow", lambda m: m["desktop"]["en"].update(scrollWidth=1441)),
            ("desktop-console", lambda m: m["desktop"]["en"]["consoleErrors"].append("boom")),
            ("desktop-console", lambda m: m["desktop"]["en"]["failedRequests"].append("x.js HTTP 404")),
            ("page-overflow", lambda m: m["pages"][4].pop("clientWidth")),
            ("page-overflow", lambda m: m["pages"][1].update(scrollWidth=400)),
            ("page-console", lambda m: m["pages"][2]["consoleErrors"].append("boom")),
            ("page-console", lambda m: m["pages"][3]["failedRequests"].append("x.png HTTP 404")),
            ("coverage", lambda m: m["pages"].pop()),
            ("coverage", lambda m: m["mobile"].pop("en")),
            ("coverage", lambda m: m["desktop"].pop("zh-Hans")),
        ]
        # Coupled measurements report both violations: headline movement after closing the menu,
        # or a language target that breaks both language access and menu usability.
        EXTRA = {0: ["h1-top", "menu-restored"],
                 1: ["h1-top", "banner-above-h1", "freshness-above-h1"],
                 2: ["h1-bottom", "menu-restored"],
                 5: ["language-nav", "menu-usable"], 6: ["language-nav", "menu-usable"]}
        seen = set()
        for index, (rule, mutate) in enumerate(cases):
            with self.subTest(case=index, rule=rule):
                measurements = self.healthy()
                mutate(measurements)
                found = self.rules(measurements)
                self.assertEqual(found, EXTRA.get(index, [rule]))
                seen.add(rule)
        self.assertEqual(seen, {"h1-top", "h1-bottom", "one-fcmo", "language-nav", "banner-above-h1", "freshness-above-h1",
                                "topbar-height", "topbar-row", "menu-usable", "menu-restored", "nav-reachable", "overflow",
                                "console", "requests", "desktop-chrome", "desktop-one-fcmo", "desktop-overflow",
                                "desktop-console", "page-overflow", "page-console", "coverage"})

    def test_the_h1_budget_is_460_px_and_a_missing_signal_is_a_violation(self):
        at_461 = self.healthy()
        at_461["mobile"]["en"]["h1"] = self.rect(461, 600)
        at_461["mobile"]["en"]["menu"]["headlineTop"] = 461
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
        # Without a cover headline nothing can be proven to sit above it.
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
        code, out, _ = self.run_main(healthy, (True, "GATES PASS (14/14)"))
        self.assertEqual(code, 0)
        self.assertIn("MOBILE FIRST VIEWPORT OK h1-top en=165px es-419=165px zh-Hans=165px", out)
        code, out, err = self.run_main(healthy, (False, "GATE FAIL [NO_FCMO_GROUP]"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("- gates: GATE FAIL [NO_FCMO_GROUP]", err)
        late = copy.deepcopy(healthy)
        late["mobile"]["es-419"]["h1"]["top"] = 461
        late["mobile"]["es-419"]["h1"]["bottom"] = 600
        code, out, err = self.run_main(late, (True, "GATES PASS (14/14)"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("MOBILE FIRST VIEWPORT FAIL h1-top en=165px es-419=461px zh-Hans=165px", err)

    def test_the_script_exits_1_with_browser_unavailable(self):
        result = subprocess.run([sys.executable, str(ORACLE), "--playwright-module", "/nonexistent/playwright/index.js"],
                                cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 1)
        self.assertIn("BROWSER_UNAVAILABLE", result.stdout + result.stderr)


class OracleInBrowserTests(unittest.TestCase):
    def test_the_real_build_passes_the_first_viewport_oracle(self):
        module = resolve_playwright_module()
        if not browser_available(module):
            skip_or_fail(self, "Playwright module does not resolve from this checkout")
        result = subprocess.run([sys.executable, str(ORACLE), "--playwright-module", module, "--print-measurements"],
                                cwd=ROOT, capture_output=True, text=True, timeout=2400)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("MOBILE FIRST VIEWPORT OK", result.stdout)
        measurements = json.loads(next(line for line in result.stdout.splitlines() if line.startswith("{")))
        for code, prefix in LOCALES:
            with self.subTest(locale=code):
                mobile = measurements["mobile"][code]
                # The keyboard-opened native menu exposes all six destinations and three languages;
                # closing it restores the page. The desktop nav stays hidden on phones.
                self.assertEqual([link["visible"] for link in mobile["navLinks"]], [False] * 6)
                self.assertEqual(len(mobile["menu"]["links"]), 9)
                self.assertTrue(all(link["visible"] for link in mobile["menu"]["links"]))
                self.assertTrue(mobile["menu"]["opened"])
                self.assertTrue(mobile["menu"]["closed"])
                self.assertEqual(mobile["headers"], 1)
                self.assertFalse(mobile["tabbarPresent"])
                self.assertEqual(mobile["zoneSwitch"], 0)
                self.assertTrue(mobile["topicsTarget"])
                self.assertFalse(mobile["banner"]["clipped"])
                self.assertFalse(mobile["freshness"]["clipped"])
                desktop = measurements["desktop"][code]
                self.assertEqual([link["visible"] for link in desktop["topnav"]["links"]], [True] * 6)
                self.assertFalse(desktop["tabbarVisible"])


class LongTokenDoesNotOverflowTests(unittest.TestCase):
    """A hash or URL with no spaces inside zh text must wrap, not scroll a 390px phone page sideways."""

    TOKEN = "378b42d18dabe0b9c4ced4e6f3670d93b52db08e" * 3
    MEASURE = r"""const { chromium } = require(process.argv[1]);
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.setContent(fs.readFileSync(process.argv[2], 'utf8'));
  const out = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth }));
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e); process.exit(3); });
"""

    def test_a_long_unbroken_token_in_zh_text_does_not_overflow_at_390(self):
        module = resolve_playwright_module()
        if not browser_available(module):
            skip_or_fail(self, "Playwright module does not resolve from this checkout")
        css = PAPER_CSS.read_text(encoding="utf-8")
        text = f"十月20日，llm-d发布了v1.0.0，标签指向提交{self.TOKEN}。版本说明将18个核心组件统一到v1.0.0。"
        page = (f'<!doctype html><html lang="zh-Hans"><meta charset="utf-8"><style>{css}</style><body>'
                '<main class="page-shell"><section class="card-row"><article class="story-card">'
                f'<h3><a href="#">标题</a></h3><p>{text}</p></article></section>'
                '<div class="archive-list"><article class="archive-item"><div class="archive-copy">'
                f'<h2>标题</h2><p>{text}</p></div></article></div>'
                f'<ul><li>{text}</li></ul></main></body></html>')
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / "page.html"
            source.write_text(page, encoding="utf-8")
            result = subprocess.run(["node", "-e", self.MEASURE, module, str(source)], cwd=name,
                                    capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        measured = json.loads(result.stdout)
        self.assertLessEqual(measured["scroll"], measured["client"],
                             f"a long unbroken token overflows a 390px phone page: {measured}")


if __name__ == "__main__":
    unittest.main()
