#!/usr/bin/env python3
"""Verify that a phone reader sees the FCMO AI lead headline on the first screen of the locale front.

The oracle builds this checkout into a temporary directory, serves it under the
publication base path, measures it in a real Chromium through Playwright and
runs the deterministic publication gates over the same build. Measurement and
judgement are separate (the front is the locale root; ``diario/`` is only a redirect stub since c6): ``evaluate(measurements)`` is a pure function that
returns one violation per broken first-viewport rule, so the rules can be tested
without a browser. A missing browser is a failure (``BROWSER_UNAVAILABLE``),
never a pass or a skip.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module  # noqa: E402

STORIES = ROOT / "site/data/stories.v2.json"
STATUS = ROOT / "site/data/newsroom-status.json"
BASE = "/FCMO-AI-Newsletter/"
LOCALES = (("en", ""), ("es-419", "es/"), ("zh-Hans", "zh/"))
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}
H1_TOP_MAX = 460
H1_TOP_TARGET = 420
NAV_HEIGHT_MAX = 48
# The c6 top bar is one row at the design token --l-bar (56px); it is the single header, so it gets its own budget.
BAR_HEIGHT_MAX = 56
NAV_PATHS = ("", "#topics", "archive/", "search/?focus=1", "corrections/", "method/")
TAB_PATHS = ("", "archive/", "search/?focus=1", "corrections/", "subscribe/")
ROW_TOLERANCE = 2
PAGE_KINDS = ("landing", "story")

MEASURE = r'''const { chromium } = require(process.argv[1]);
const base = process.argv[2], locales = JSON.parse(process.argv[3]);
const MOBILE = JSON.parse(process.argv[4]), DESKTOP = JSON.parse(process.argv[5]);

async function visit(browser, viewport, url, probe) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const consoleErrors = [], failedRequests = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push(String(e && e.message || e)));
  page.on('requestfailed', r => failedRequests.push(`${r.url()} ${r.failure() ? r.failure().errorText : ''}`.trim()));
  page.on('response', r => { if (r.status() >= 400) failedRequests.push(`${r.url()} HTTP ${r.status()}`); });
  await page.goto(url, { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(() => document.fonts ? document.fonts.ready.then(() => true) : true);
  const result = await page.evaluate(`(${probe.toString()})((${HELPERS.toString()})())`);
  await context.close();
  return { url, ...result, consoleErrors, failedRequests };
}

const COMMON = () => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth });

// page.evaluate serializes a function alone, so the shared helpers travel as a factory handed to each probe.
const HELPERS = () => {
  const VISIBLE = el => !!el && (el.checkVisibility ? el.checkVisibility({ visibilityProperty: true }) : el.getClientRects().length > 0);
  const BOX = el => { const r = el.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, height: r.height, visible: VISIBLE(el) }; };
  // An inline element has no scroll or client size of its own: it is clipped when the block that holds it is.
  const WHOLE = el => { const host = getComputedStyle(el).display === 'inline' && el.parentElement ? el.parentElement : el;
    return { ...BOX(el), clipped: host.scrollHeight > host.clientHeight + 1 || host.scrollWidth > host.clientWidth + 1 }; };
  const LINKS = el => el ? [...el.querySelectorAll('a')].map(a => ({ href: a.getAttribute('href'), ...BOX(a) })) : [];
  return { VISIBLE, BOX, WHOLE, LINKS };
};

const MOBILE_PROBE = H => {
  const { VISIBLE, BOX, WHOLE, LINKS } = H;
  const h1 = document.querySelector('.landing-feature h1, .cover h1');
  const lead = h1 && h1.querySelector('a');
  const banner = document.querySelector('.status-banner');
  const freshness = document.querySelector('.corpus-freshness');
  const topbar = document.querySelector('.topbar');
  const topnav = document.querySelector('.topbar .topnav');
  const tabbar = document.querySelector('.tabbar');
  const na = document.querySelector('.receipt-na');
  const shown = [...document.querySelectorAll('.topbar a, .tabbar a, .footbar a')].filter(a => VISIBLE(a) && !a.closest('.langsel'));
  return {
    h1: h1 && VISIBLE(h1) ? BOX(h1) : null,
    leadHref: lead ? lead.getAttribute('href') : null,
    zoneSwitch: document.querySelectorAll('.zone-switch').length,
    languages: [...document.querySelectorAll('.langsel a')].map(BOX),
    banner: banner ? { state: banner.getAttribute('data-edition-state'), ...WHOLE(banner) } : null,
    freshness: freshness ? WHOLE(freshness) : null,
    topbar: topbar ? { ...BOX(topbar), items: [...topbar.querySelectorAll('.brandmark, .langsel a')].filter(VISIBLE).map(BOX) } : null,
    tabbar: tabbar ? { ...BOX(tabbar), links: LINKS(tabbar) } : null,
    receiptNa: na && VISIBLE(na) ? BOX(na) : null,
    navLinks: LINKS(topnav),
    // Language links point at the current page, so they never count as another way to reach a nav destination.
    topicsTarget: !!document.getElementById('topics') && VISIBLE(document.getElementById('topics')),
    visibleHrefs: shown.map(a => a.getAttribute('href')),
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
  };
};

const DESKTOP_PROBE = H => {
  const { VISIBLE, BOX, LINKS } = H;
  const one = sel => document.querySelector(sel);
  const topnav = one('.topbar .topnav'), tabbar = one('.tabbar');
  return {
    zoneSwitch: document.querySelectorAll('.zone-switch').length,
    brandmark: VISIBLE(one('.topbar .brandmark')),
    freshnessLine: VISIBLE(one('.corpus-freshness')),
    topnav: topnav ? { ...BOX(topnav), links: LINKS(topnav) } : null,
    tabbarVisible: VISIBLE(tabbar),
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
  };
};

(async () => {
  let browser;
  try { browser = await chromium.launch(); }
  catch (e) { console.error(`BROWSER_UNAVAILABLE: ${e.message}`); process.exit(2); }
  const out = { mobile: {}, desktop: {}, pages: [] };
  try {
    for (const [code, prefix] of locales) {
      const front = new URL(prefix, base).href;
      out.mobile[code] = await visit(browser, MOBILE, front, MOBILE_PROBE);
      out.desktop[code] = await visit(browser, DESKTOP, front, DESKTOP_PROBE);
      out.pages.push({ kind: 'landing', locale: code, ...await visit(browser, MOBILE, front, COMMON) });
      const story = out.mobile[code].leadHref;
      if (story) out.pages.push({ kind: 'story', locale: code, ...await visit(browser, MOBILE, new URL(story, base).href, COMMON) });
    }
  } finally { await browser.close(); }
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(`MEASURE ERROR: ${e.stack || e}`); process.exit(1); });'''


def _inside(rect: dict, viewport: dict) -> bool:
    return (rect.get("visible", False) and rect["top"] >= 0 and rect["left"] >= 0
            and rect["bottom"] <= viewport["height"] and rect["right"] <= viewport["width"])


def _overflows(measured: dict) -> bool:
    """A page overflows sideways, or cannot prove it does not because a width is missing."""
    width, client = measured.get("scrollWidth"), measured.get("clientWidth")
    return not isinstance(width, (int, float)) or not isinstance(client, (int, float)) or width > client


def _px(value: float) -> str:
    return f"{value:.0f}px"


def _hrefs(prefix: str, paths: tuple[str, ...]) -> set[str]:
    return {f"{BASE}{prefix}{path}" for path in paths}


def _one_row(rects: list[dict]) -> bool:
    """All boxes share one row: vertical centres within ROW_TOLERANCE."""
    centres = [(r["top"] + r["bottom"]) / 2 for r in rects]
    return bool(centres) and max(centres) - min(centres) <= ROW_TOLERANCE


def evaluate(measurements: dict) -> list[str]:
    """Return one violation per broken first-viewport rule; an empty list means the rules hold."""
    violations: list[str] = []
    mobile, desktop = measurements.get("mobile") or {}, measurements.get("desktop") or {}
    pages = measurements.get("pages") or []
    for code, prefix in LOCALES:
        where = f"{code} 390x844 front"
        m = mobile.get(code)
        if not m:
            violations.append(f"coverage {where}: not measured")
        else:
            h1 = m.get("h1")
            if h1 is None:
                violations.append(f"h1-top {where}: cover headline missing or hidden")
            else:
                if h1["top"] > H1_TOP_MAX:
                    violations.append(f"h1-top {where}: top {_px(h1['top'])} > {H1_TOP_MAX}px")
                if h1["bottom"] > MOBILE["height"]:
                    violations.append(f"h1-bottom {where}: bottom {_px(h1['bottom'])} > {MOBILE['height']}px")
            if m.get("zoneSwitch") != 0:
                violations.append(f"one-fcmo {where}: .zone-switch product doors must be absent ({m.get('zoneSwitch')} found)")
            languages = m.get("languages") or []
            if not languages or not all(_inside(a, MOBILE) for a in languages):
                violations.append(f"language-nav {where}: every language link must fit whole in the first viewport")
            top = h1["top"] if h1 else None
            banner = m.get("banner")
            if banner is None or not banner.get("state"):
                violations.append(f"banner-above-h1 {where}: status banner missing")
            elif banner["state"] != "FRESH" and (not _inside(banner, MOBILE) or banner.get("clipped")
                                                 or top is None or banner["bottom"] > top):
                violations.append(f"banner-above-h1 {where}: {banner['state']} banner must show whole above the cover headline")
            fresh = m.get("freshness")
            if (fresh is None or not _inside(fresh, MOBILE) or fresh.get("clipped") or top is None or fresh["bottom"] > top):
                violations.append(f"freshness-above-h1 {where}: corpus freshness line must show whole above the cover headline")
            bar = m.get("topbar")
            if bar is None or not bar.get("visible") or bar["height"] > BAR_HEIGHT_MAX:
                height = _px(bar["height"]) if bar else "missing"
                violations.append(f"topbar-height {where}: top bar {height} > {BAR_HEIGHT_MAX}px")
            items = (bar or {}).get("items") or []
            if (not items or not _one_row(items) or any(i["left"] < 0 or i["right"] > MOBILE["width"]
                                                         or i["top"] < bar["top"] - ROW_TOLERANCE
                                                         or i["bottom"] > bar["bottom"] + ROW_TOLERANCE for i in items)):
                violations.append(f"topbar-row {where}: brand and language links must share one row inside the top bar")
            tabs = m.get("tabbar")
            links = (tabs or {}).get("links") or []
            if (tabs is None or not tabs.get("visible") or not _inside(tabs, MOBILE) or len(links) != len(TAB_PATHS)
                    or not all(a.get("visible") for a in links) or not _one_row(links)):
                violations.append(f"tabbar-row {where}: the bottom tab bar must be visible, inside the viewport, one row of {len(TAB_PATHS)} links")
            elif set(a["href"] for a in links) != _hrefs(prefix, TAB_PATHS):
                violations.append(f"tabbar-row {where}: tab destinations differ from {sorted(_hrefs(prefix, TAB_PATHS))}")
            na = m.get("receiptNa")
            if tabs is not None and tabs.get("visible"):
                if h1 is not None and h1["bottom"] > tabs["top"]:
                    violations.append(f"tabbar-clear {where}: tab bar (top {_px(tabs['top'])}) covers the cover headline (bottom {_px(h1['bottom'])})")
                if na is None or na["bottom"] > tabs["top"]:
                    where_na = "missing" if na is None else f"bottom {_px(na['bottom'])}"
                    violations.append(f"tabbar-clear {where}: the 20-second «Not established» line must end above the tab bar ({where_na})")
            nav = m.get("navLinks") or []
            reachable = set(m.get("visibleHrefs") or [])
            # «Topics» is an in-page anchor to the front's own topics section: phones reach it by that section being present
            # and visible (the tab bar holds five reader actions), every other destination needs a visible link.
            anchors = {a["href"] for a in nav if "#" in a["href"]}
            lost = sorted({a["href"] for a in nav} - reachable - (anchors if m.get("topicsTarget") else set()))
            if set(a["href"] for a in nav) != _hrefs(prefix, NAV_PATHS) or lost:
                violations.append(f"nav-reachable {where}: nav destinations without a visible link: {lost or 'nav incomplete'}")
            if _overflows(m):
                violations.append(f"overflow {where}: scrollWidth {m.get('scrollWidth')} > clientWidth {m.get('clientWidth')}")
            if m.get("consoleErrors"):
                violations.append(f"console {where}: {m['consoleErrors'][:3]}")
            if m.get("failedRequests"):
                violations.append(f"requests {where}: {m['failedRequests'][:3]}")
        where = f"{code} 1440x900 front"
        d = desktop.get(code)
        if not d:
            violations.append(f"coverage {where}: not measured")
        else:
            # c6 equivalents of the retired edition-line / brand-sub / breadcrumbs: the freshness line (what the edition
            # says about itself), the FCMO AI brandmark (the single brand line) and the six-link top nav (the way around).
            nav = d.get("topnav") or {}
            shown = [a for a in nav.get("links", []) if a.get("visible")]
            hidden = [name for ok, name in ((d.get("freshnessLine"), ".corpus-freshness"), (d.get("brandmark"), ".brandmark"),
                                            (not d.get("tabbarVisible", True), ".tabbar (must be hidden)"),
                                            (nav.get("visible") and len(shown) == len(NAV_PATHS)
                                             and {a["href"] for a in shown} == _hrefs(prefix, NAV_PATHS)
                                             and _one_row(shown), ".topnav")) if not ok]
            if hidden:
                violations.append(f"desktop-chrome {where}: hidden or incomplete at desktop: {hidden}")
            if d.get("zoneSwitch") != 0:
                violations.append(f"desktop-one-fcmo {where}: .zone-switch product doors must be absent ({d.get('zoneSwitch')} found)")
            if _overflows(d):
                violations.append(f"desktop-overflow {where}: scrollWidth {d.get('scrollWidth')} > clientWidth {d.get('clientWidth')}")
            if d.get("consoleErrors") or d.get("failedRequests"):
                violations.append(f"desktop-console {where}: {(d.get('consoleErrors') or []) + (d.get('failedRequests') or [])}"[:400])
        for kind in PAGE_KINDS:
            where = f"{code} 390x844 {kind}"
            page = next((p for p in pages if p.get("kind") == kind and p.get("locale") == code), None)
            if page is None:
                violations.append(f"coverage {where}: not measured")
                continue
            if _overflows(page):
                violations.append(f"page-overflow {where}: scrollWidth {page.get('scrollWidth')} > clientWidth {page.get('clientWidth')}")
            if page.get("consoleErrors") or page.get("failedRequests"):
                violations.append(f"page-console {where}: {(page.get('consoleErrors') or []) + (page.get('failedRequests') or [])}"[:400])
    return violations


def tops(measurements: dict) -> str:
    parts = []
    for code, _prefix in LOCALES:
        h1 = ((measurements.get("mobile") or {}).get(code) or {}).get("h1")
        parts.append(f"{code}={h1['top']:.0f}px" if h1 else f"{code}=missing")
    return " ".join(parts)


def module_loads(module: str) -> bool:
    node = shutil.which("node")
    if not node:
        return False
    try:
        result = subprocess.run([node, "-e", "require(process.argv[1])", module],
                                capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def build_site(out: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/paper/build.py"), "--stories", str(STORIES), "--status", str(STATUS),
         "--out", str(out), "--base", BASE], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"build failed: {(result.stdout + result.stderr)[-2000:]}")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}{BASE}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def measure(module: str, base: str, temp: Path) -> dict:
    env = dict(os.environ, TMPDIR=str(temp), TMP=str(temp), TEMP=str(temp))
    completed = subprocess.run(
        ["node", "--input-type=commonjs", "-e", MEASURE, module, base, json.dumps(LOCALES), json.dumps(MOBILE),
         json.dumps(DESKTOP)], cwd=temp, env=env, text=True, capture_output=True, timeout=1800, check=False)
    if completed.returncode == 2:
        raise BrowserUnavailable(completed.stderr.strip())
    if completed.returncode:
        raise RuntimeError(f"measurement failed: {(completed.stdout + completed.stderr)[-3000:]}")
    return json.loads(completed.stdout)


def gates(out: Path) -> tuple[bool, str]:
    completed = subprocess.run([sys.executable, str(ROOT / "tools/gates/run_all.py"), str(out)],
                               cwd=ROOT, text=True, capture_output=True, check=False)
    lines = (completed.stdout + completed.stderr).strip().splitlines()
    summary = next((line for line in reversed(lines) if line.startswith("GATES PASS")), None)
    return completed.returncode == 0 and summary is not None, summary or "\n".join(lines[-12:])


class BrowserUnavailable(RuntimeError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--playwright-module", help="path to the Node Playwright module (default: resolved)")
    parser.add_argument("--print-measurements", action="store_true", help="also print the raw measurements as JSON")
    args = parser.parse_args(argv)
    module = args.playwright_module or resolve_playwright_module()
    if not module or not module_loads(module):
        print(f"{missing_playwright_message()} (module: {module or 'unresolved'})")
        return 1
    with tempfile.TemporaryDirectory(prefix="fcmo-mobile-first-") as name:
        temp = Path(name)
        out = temp / BASE.strip("/")
        try:
            build_site(out)
            with serve(temp) as base:
                measurements = measure(module, base, temp)
        except BrowserUnavailable as exc:
            print(f"{missing_playwright_message()} ({exc})")
            return 1
        except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            print(f"MOBILE FIRST VIEWPORT FAIL: {exc}", file=sys.stderr)
            return 1
        violations = evaluate(measurements)
        passed, summary = gates(out)
        if not passed:
            violations.append(f"gates: {summary}")
    if args.print_measurements:
        print(json.dumps(measurements, ensure_ascii=False, sort_keys=True))
    if violations:
        print(f"MOBILE FIRST VIEWPORT FAIL h1-top {tops(measurements)}", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1
    print(f"MOBILE FIRST VIEWPORT OK h1-top {tops(measurements)} (target <={H1_TOP_TARGET}px, max <={H1_TOP_MAX}px); {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
