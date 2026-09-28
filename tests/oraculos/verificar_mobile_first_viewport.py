#!/usr/bin/env python3
"""Verify that a phone reader sees the FCMO AI lead headline on the first screen of /diario/.

The oracle builds this checkout into a temporary directory, serves it under the
publication base path, measures it in a real Chromium through Playwright and
runs the deterministic publication gates over the same build. Measurement and
judgement are separate: ``evaluate(measurements)`` is a pure function that
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
  const result = await page.evaluate(probe);
  await context.close();
  return { url, ...result, consoleErrors, failedRequests };
}

const COMMON = () => ({ scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth });

const MOBILE_PROBE = () => {
  const visible = el => !!el && (el.checkVisibility ? el.checkVisibility({ visibilityProperty: true }) : el.getClientRects().length > 0);
  const box = el => { const r = el.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, height: r.height, visible: visible(el) }; };
  const whole = el => ({ ...box(el), clipped: el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1 });
  const h1 = document.querySelector('.lead h1');
  const banner = document.querySelector('.status-banner');
  const freshness = document.querySelector('.corpus-freshness');
  const header = document.querySelector('.site-header');
  const nav = document.querySelector('.site-header .main-nav');
  const lead = h1 && h1.querySelector('a');
  return {
    h1: h1 && visible(h1) ? box(h1) : null,
    leadHref: lead ? lead.getAttribute('href') : null,
    zones: [...document.querySelectorAll('.zone-switch a')].map(box),
    languages: [...document.querySelectorAll('.language-nav a')].map(box),
    banner: banner ? { state: banner.getAttribute('data-edition-state'), ...whole(banner) } : null,
    freshness: freshness ? whole(freshness) : null,
    nav: nav ? { ...box(nav), links: [...nav.querySelectorAll('a')].map(a => ({ href: a.getAttribute('href'), ...box(a) })) } : null,
    // Language links point at the current page, so they never count as another way to reach a nav destination.
    headerHrefs: header ? [...header.querySelectorAll('a')].filter(a => visible(a) && !a.closest('.language-nav')).map(a => a.getAttribute('href')) : [],
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
  };
};

const DESKTOP_PROBE = () => {
  const visible = sel => { const el = document.querySelector(sel); return !!el && (el.checkVisibility ? el.checkVisibility({ visibilityProperty: true }) : el.getClientRects().length > 0); };
  const h1 = document.querySelector('.lead h1');
  return { editionLine: visible('.edition-line'), brandSub: visible('.brand-sub'), breadcrumbs: visible('.breadcrumbs'),
    h1Top: h1 ? h1.getBoundingClientRect().top : null,
    scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth };
};

(async () => {
  let browser;
  try { browser = await chromium.launch(); }
  catch (e) { console.error(`BROWSER_UNAVAILABLE: ${e.message}`); process.exit(2); }
  const out = { mobile: {}, desktop: {}, pages: [] };
  try {
    for (const [code, prefix] of locales) {
      const diario = new URL(prefix + 'diario/', base).href;
      out.mobile[code] = await visit(browser, MOBILE, diario, MOBILE_PROBE);
      out.desktop[code] = await visit(browser, DESKTOP, diario, DESKTOP_PROBE);
      out.pages.push({ kind: 'landing', locale: code, ...await visit(browser, MOBILE, new URL(prefix, base).href, COMMON) });
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


def evaluate(measurements: dict) -> list[str]:
    """Return one violation per broken first-viewport rule; an empty list means the rules hold."""
    violations: list[str] = []
    mobile, desktop = measurements.get("mobile") or {}, measurements.get("desktop") or {}
    pages = measurements.get("pages") or []
    for code, _prefix in LOCALES:
        where = f"{code} 390x844 /diario/"
        m = mobile.get(code)
        if not m:
            violations.append(f"coverage {where}: not measured")
        else:
            h1 = m.get("h1")
            if h1 is None:
                violations.append(f"h1-top {where}: lead h1 missing or hidden")
            else:
                if h1["top"] > H1_TOP_MAX:
                    violations.append(f"h1-top {where}: top {_px(h1['top'])} > {H1_TOP_MAX}px")
                if h1["bottom"] > MOBILE["height"]:
                    violations.append(f"h1-bottom {where}: bottom {_px(h1['bottom'])} > {MOBILE['height']}px")
            zones = m.get("zones") or []
            if len(zones) != 2 or not all(_inside(z, MOBILE) for z in zones):
                violations.append(f"zone-switch {where}: both doors must fit whole in the first viewport ({len(zones)} found)")
            languages = m.get("languages") or []
            if not languages or not all(_inside(a, MOBILE) for a in languages):
                violations.append(f"language-nav {where}: every language link must fit whole in the first viewport")
            top = h1["top"] if h1 else None
            banner = m.get("banner")
            if banner is None or not banner.get("state"):
                violations.append(f"banner-above-h1 {where}: status banner missing")
            elif banner["state"] != "FRESH" and (not _inside(banner, MOBILE) or banner.get("clipped")
                                                 or top is None or banner["bottom"] > top):
                violations.append(f"banner-above-h1 {where}: {banner['state']} banner must show whole above the lead h1")
            fresh = m.get("freshness")
            if fresh is None or not _inside(fresh, MOBILE) or fresh.get("clipped") or top is None or fresh["bottom"] > top:
                violations.append(f"freshness-above-h1 {where}: corpus freshness line must show whole above the lead h1")
            nav = m.get("nav")
            shown = [a for a in (nav or {}).get("links", []) if a.get("visible")]
            if nav is None or not nav.get("visible") or nav["height"] > NAV_HEIGHT_MAX:
                height = _px(nav["height"]) if nav else "missing"
                violations.append(f"nav-height {where}: main nav {height} > {NAV_HEIGHT_MAX}px")
            if (not shown or max(a["top"] for a in shown) - min(a["top"] for a in shown) > ROW_TOLERANCE
                    or any(a["left"] < 0 or a["right"] > MOBILE["width"] for a in shown)):
                violations.append(f"nav-row {where}: visible main-nav links must share one row (±{ROW_TOLERANCE}px) inside the viewport")
            reachable = set(m.get("headerHrefs") or [])
            lost = sorted({a["href"] for a in (nav or {}).get("links", [])} - reachable)
            if nav is None or lost:
                violations.append(f"nav-reachable {where}: nav destinations without a visible header link: {lost}")
            if _overflows(m):
                violations.append(f"overflow {where}: scrollWidth {m.get('scrollWidth')} > clientWidth {m.get('clientWidth')}")
            if m.get("consoleErrors"):
                violations.append(f"console {where}: {m['consoleErrors'][:3]}")
            if m.get("failedRequests"):
                violations.append(f"requests {where}: {m['failedRequests'][:3]}")
        where = f"{code} 1440x900 /diario/"
        d = desktop.get(code)
        if not d:
            violations.append(f"coverage {where}: not measured")
        else:
            hidden = [name for key, name in (("editionLine", ".edition-line"), ("brandSub", ".brand-sub"),
                                             ("breadcrumbs", ".breadcrumbs")) if not d.get(key)]
            if hidden:
                violations.append(f"desktop-chrome {where}: hidden at desktop: {hidden}")
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
         json.dumps(DESKTOP)], cwd=temp, env=env, text=True, capture_output=True, timeout=900, check=False)
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
