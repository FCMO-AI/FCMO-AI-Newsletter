#!/usr/bin/env python3
"""Browser oracle for campaign c6 (DIRECCION §3, §5, §9): what a reader sees.

    python3 tests/oraculos/verificar_c6.py <built-site-dir>

For each locale (en, es-419, zh-Hans) at 390 and 1440 px, on the home page and
on the first story, it checks in a real Chromium:

* horizontal overflow is 0 px (every page);
* axe-core reports 0 serious or critical violations (every page);
* at 820, 1100 and 1440 px (tablet and desktop top bar, M1): the top bar and its
  inner frame do not overflow their box, the «FCMO AI» wordmark renders on one
  line, and the Subscribe CTA (.btn-cta) is visible and is what a click reaches;
* on the landing page at 1440 px, synthetic leads of 30..84 display units (Latin,
  and Han on zh-Hans) are put into the hero h1 with the class the build's own
  _title_class assigns; the h1 stays within 4 lines and the next line
  (.cover-dek or .cover-evrow) starts above 900 px (same budget as verificar_paper);
* at 390 x 844, on the story: the evidence class and the first external source
  link start within the first 844 px (no scroll needed);
* at 390 x 844, on the story: the last line of «In 20 seconds» («Not established»)
  is fully inside the first screen and is not covered by a fixed or sticky
  element such as a bottom tab bar.
* at 390 x 844, on the home: the «Not established» line of the 20-second receipt
  ends within the first 780 px, above the bottom tab bar (DIRECCION §6; VERDICT-r2 A2′).

Measurement runs in Node Playwright (module from PLAYWRIGHT_MODULE or the repo
resolver). The axe-core script comes from AXE_CORE_PATH. A missing browser or
missing axe is a failure (BROWSER_UNAVAILABLE / AXE_UNAVAILABLE), never a pass.
Each failed check prints one FAIL line; exit status is 1 if any failed.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module  # noqa: E402

BASE = "/FCMO-AI-Newsletter/"
LOCALE_PREFIX = {"en": "", "es-419": "es/", "zh-Hans": "zh/"}
FIRST_SCREEN_390 = 844
# DIRECCION §6: the bottom tab bar starts at 780 px on a 390 x 844 screen.
HOME_LINE_LIMIT_390 = 780
WIDTHS = (390, 820, 1100, 1440)
TOPBAR_MIN_WIDTH = 768  # below this the CTA lives in the bottom tab bar
HERO_MAX_LINES = 4
HERO_NEXT_LINE_LIMIT = 900
# Target display widths (build units) probed on the landing hero; the class
# boundaries of _title_class fall inside this range.
HERO_UNITS = (30, 38, 46, 55, 58, 70, 84)

NODE_SCRIPT = r"""
const fs = require('fs');
const [,, pwModule, axePath, plan, origin] = process.argv;
const { chromium } = require(pwModule);
const jobs = JSON.parse(fs.readFileSync(plan, 'utf-8'));
const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

async function measureHero(browser, job) {
  const ctx = await browser.newContext({ viewport: { width: job.width, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(origin + job.url, { waitUntil: 'load', timeout: 60000 });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  job.results = [];
  for (const probe of job.probes) {
    const r = await page.evaluate((probe) => {
      const h = document.querySelector('.landing-feature h1');
      if (!h) return { missing: true };
      const a = h.querySelector('a');
      (a || h).textContent = probe.text;
      // Keep every other class (cover-title ...); swap only the title-* size class.
      [...h.classList].filter((c) => c.startsWith('title-')).forEach((c) => h.classList.remove(c));
      h.classList.add(probe.cls);
      const dek = document.querySelector('.landing-feature .cover-dek') || document.querySelector('.landing-feature .cover-evrow');
      const rect = h.getBoundingClientRect(), cs = getComputedStyle(h);
      const lineHeight = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize);
      return { lines: Math.ceil(rect.height / lineHeight - 0.01), dekTop: dek ? dek.getBoundingClientRect().top : null };
    }, probe);
    job.results.push({ ...probe, ...r });
  }
  await ctx.close();
  return job;
}

async function measure(browser, job) {
  if (job.probes) return measureHero(browser, job);
  const ctx = await browser.newContext({ viewport: { width: job.width, height: job.width === 390 ? 844 : 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(origin + job.url, { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(600);
  const result = await page.evaluate(() => {
    const rect = (el) => { const r = el.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right }; };
    const out = { overflowPx: document.documentElement.scrollWidth - window.innerWidth };
    const sig = document.querySelector('.sig-text, .story-signals');
    const src = [...document.querySelectorAll('main a[href^="http"]')].find((a) => !a.href.includes('fcmo-ai.github.io'));
    const bar = document.querySelector('.topbar');
    if (bar) {
      const inner = bar.querySelector('.topbar-in') || bar;
      const mark = bar.querySelector('.brandmark');
      const cta = bar.querySelector('.btn-cta');
      // Visual lines of the wordmark's text: distinct vertical positions of its text rects.
      const textLines = (el) => {
        const tops = new Set();
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        for (let n = walker.nextNode(); n; n = walker.nextNode()) {
          if (!n.textContent.trim()) continue;
          const range = document.createRange();
          range.selectNodeContents(n);
          for (const r of range.getClientRects()) if (r.width > 0 && r.height > 0) tops.add(Math.round(r.top));
        }
        return tops.size;
      };
      const lh = (el) =>parseFloat(getComputedStyle(el).lineHeight) || parseFloat(getComputedStyle(el).fontSize);
      let ctaHit = false;
      let ctaRect = null;
      if (cta) {
        const r = cta.getBoundingClientRect();
        ctaRect = rect(cta);
        const hit = document.elementFromPoint(Math.min(Math.max(r.left + r.width / 2, 0), window.innerWidth - 1), Math.min(Math.max(r.top + r.height / 2, 0), window.innerHeight - 1));
        ctaHit = !!hit && cta.contains(hit);
        const cs = getComputedStyle(cta);
        ctaRect.shown = cs.display !== 'none' && cs.visibility !== 'hidden' && Number(cs.opacity) > 0;
      }
      out.topbar = {
        // scrollWidth can read 0 when an ancestor clips (the page hides document overflow),
        // so also judge geometry: no child of the bar may end past the viewport or the frame.
        barOverflow: Math.max(bar.scrollWidth - bar.clientWidth,
          Math.round(Math.max(...[...inner.children].map((c) => c.getBoundingClientRect().right)) - window.innerWidth)),
        innerOverflow: Math.max(inner.scrollWidth - inner.clientWidth,
          Math.round(Math.max(...[...inner.children].map((c) => c.getBoundingClientRect().right)) - inner.getBoundingClientRect().right)),
        barHeight: bar.getBoundingClientRect().height,
        mark: mark ? { ...rect(mark), lineHeight: lh(mark), textLines: textLines(mark), whiteSpace: getComputedStyle(mark).whiteSpace } : null,
        cta: ctaRect, ctaHit,
      };
    }
    out.signals = sig ? rect(sig) : null;
    out.firstExternalSource = src ? rect(src) : null;
    const na = document.querySelector('.receipt-na');
    out.receiptNa = na ? rect(na) : null;
    const items = document.querySelectorAll('.brief li');
    const last = items.length ? items[items.length - 1] : null;
    out.briefLast = last ? rect(last) : null;
    if (last) {
      const r = last.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = Math.min(r.top + r.height / 2, window.innerHeight - 1);
      const hit = document.elementFromPoint(cx, cy);
      out.briefHitInside = !!hit && last.contains(hit);
      out.briefHitTag = hit ? (hit.className || hit.tagName).toString().slice(0, 80) : null;
    }
    return out;
  });
  await page.addScriptTag({ path: axePath });
  result.axe = await page.evaluate(async (tags) => {
    const r = await window.axe.run(document, { runOnly: { type: 'tag', values: tags } });
    return r.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
      .map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
  }, AXE_TAGS);
  await ctx.close();
  return { ...job, ...result };
}

(async () => {
  const browser = await chromium.launch();
  const out = [];
  for (const job of jobs) out.push(await measure(browser, job));
  await browser.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String(e && e.stack || e)); process.exit(3); });
"""


def build_plan(out_dir: Path) -> list[dict]:
    routes = json.loads((out_dir / "data/routes.json").read_text(encoding="utf-8"))
    jobs = []
    for locale, prefix in LOCALE_PREFIX.items():
        story = next(r for r in routes if r["kind"] == "story" and r["locale"] == locale)
        for width in WIDTHS:
            jobs.append({"locale": locale, "width": width, "route": "home", "url": BASE + prefix})
            jobs.append({"locale": locale, "width": width, "route": "story", "url": BASE + story["path"].lstrip("/")})
        jobs.append({"locale": locale, "width": 1440, "route": "hero", "url": BASE + prefix,
                     "probes": hero_probes(locale)})
    return jobs


_LATIN_WORDS = ("regulators", "approve", "the", "first", "open", "model", "audit", "for", "grid",
                "storage", "markets", "after", "review", "of", "cost", "data", "chips")
_HAN = "监管机构批准首个开放模型审计电网储能市场评估成本数据芯片"


def _units(text: str, locale_code: str) -> float:
    """Display width as the build counts it. Only sizes the probe text: the class
    comes from the build's own _title_class, never from thresholds copied here."""
    import unicodedata
    total = 0.0
    for ch in text:
        if locale_code == "zh-Hans" and unicodedata.east_asian_width(ch) in {"W", "F"}:
            total += 1.7
        elif ch.isalnum():
            total += 0.55
        else:
            total += 0.35
    return total


def synthetic_lead(units: int, locale_code: str) -> str:
    """Smallest realistic-looking lead whose build width reaches `units`."""
    text = ""
    i = 0
    while _units(text, locale_code) < units:
        if locale_code == "zh-Hans":
            text += _HAN[i % len(_HAN)]
        else:
            text += ("" if not text else " ") + _LATIN_WORDS[(i * 5) % len(_LATIN_WORDS)]
        i += 1
    return text


def hero_probes(locale_code: str) -> list[dict]:
    from tools.paper.build import PaperBuilder
    probes = []
    for units in HERO_UNITS:
        text = synthetic_lead(units, locale_code)
        probes.append({"units": units, "text": text,
                       "cls": PaperBuilder._title_class(text, locale_code, hero=True)})
    return probes


def evaluate_topbar(job: dict) -> list[str]:
    """Pure judgement of the top bar at tablet and desktop widths (M1)."""
    tag = f"{job['locale']} {job['width']}px {job['route']}"
    bar = job.get("topbar")
    if job["width"] < TOPBAR_MIN_WIDTH:
        return []
    if not bar:
        return [f"FAIL topbar {tag}: no .topbar in the page"]
    problems = []
    if bar["barOverflow"] > 0 or bar["innerOverflow"] > 0:
        problems.append(f"FAIL topbar-overflow {tag}: bar overflows its box by {max(bar['barOverflow'], bar['innerOverflow'])}px")
    mark = bar.get("mark")
    if not mark:
        problems.append(f"FAIL wordmark {tag}: no .brandmark in the top bar")
    elif mark["textLines"] != 1:
        problems.append(f"FAIL wordmark {tag}: wordmark renders on {mark['textLines']} lines, expected 1")
    cta = bar.get("cta")
    if not cta or not cta.get("shown") or cta["right"] <= cta["left"] or cta["bottom"] <= cta["top"]:
        problems.append(f"FAIL subscribe-cta {tag}: .btn-cta is missing or not rendered")
    elif cta["left"] < 0 or cta["right"] > job["width"] or not bar.get("ctaHit"):
        problems.append(f"FAIL subscribe-cta {tag}: .btn-cta is clipped, off screen or covered (left={round(cta['left'])}, right={round(cta['right'])})")
    return problems


def evaluate_hero(job: dict) -> list[str]:
    """Pure judgement of the synthetic landing-hero probes."""
    problems = []
    for res in job.get("results", []):
        tag = f"{job['locale']} hero {res['units']}u {res['cls']}"
        if res.get("missing"):
            problems.append(f"FAIL hero {tag}: .landing-feature h1 missing")
        elif res["lines"] > HERO_MAX_LINES or res["dekTop"] is None or res["dekTop"] >= HERO_NEXT_LINE_LIMIT:
            problems.append(f"FAIL hero {tag}: lines={res['lines']} (max {HERO_MAX_LINES}), next line top={res['dekTop']} (limit {HERO_NEXT_LINE_LIMIT}px)")
    return problems


def evaluate(job: dict) -> list[str]:
    """Pure judgement over one measurement. Returns one message per broken rule."""
    if job["route"] == "hero":
        return evaluate_hero(job)
    tag = f"{job['locale']} {job['width']}px {job['route']}"
    problems = evaluate_topbar(job)
    if job["overflowPx"] != 0:
        problems.append(f"FAIL overflow {tag}: {job['overflowPx']}px horizontal overflow")
    for violation in job["axe"]:
        problems.append(f"FAIL axe {tag}: {violation['impact']} {violation['id']} ({violation['nodes']} nodes)")
    if job["route"] == "home" and job["width"] == 390:
        line = job.get("receiptNa")
        if not line:
            problems.append(f"FAIL home-20s {tag}: no 'Not established' line in the 20-second receipt")
        elif line["bottom"] > HOME_LINE_LIMIT_390:
            problems.append(f"FAIL home-20s {tag}: 'Not established' line ends at {round(line['bottom'])}px, limit {HOME_LINE_LIMIT_390}px (above the tab bar)")
    if job["route"] == "story" and job["width"] == 390:
        signals, source = job.get("signals"), job.get("firstExternalSource")
        if not signals or signals["bottom"] > FIRST_SCREEN_390:
            problems.append(f"FAIL evidence-class {tag}: class line ends at {signals and round(signals['bottom'])}px, above-the-fold limit is {FIRST_SCREEN_390}px")
        if not source or source["top"] > FIRST_SCREEN_390:
            problems.append(f"FAIL sources {tag}: first source link starts at {source and round(source['top'])}px, limit {FIRST_SCREEN_390}px")
        last = job.get("briefLast")
        if not last or last["bottom"] > FIRST_SCREEN_390:
            problems.append(f"FAIL brief-20s {tag}: last line of 'In 20 seconds' ends at {last and round(last['bottom'])}px, limit {FIRST_SCREEN_390}px")
        elif not job.get("briefHitInside"):
            problems.append(f"FAIL brief-20s {tag}: last line covered by {job.get('briefHitTag')!r} (fixed or sticky overlay)")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    out_dir = Path(argv[1]).resolve()
    pw = resolve_playwright_module()
    if not pw:
        print(missing_playwright_message())
        return 2
    axe = os.environ.get("AXE_CORE_PATH", "")
    if not axe or not Path(axe).is_file():
        print("AXE_UNAVAILABLE: set AXE_CORE_PATH to axe.min.js (axe-core 4.14.0)")
        return 2
    if not shutil.which("node"):
        print("BROWSER_UNAVAILABLE: node not on PATH")
        return 2

    serve = subprocess.Popen(
        [sys.executable, str(ROOT / "tests/harness/serve.py"), "--root", str(out_dir), "--base", BASE, "--port", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        first = serve.stdout.readline()
        match = re.search(r"127\.0\.0\.1:(\d+)", first)
        if not match:
            print("BROWSER_UNAVAILABLE: local server did not start: " + first.strip())
            return 2
        origin = f"http://127.0.0.1:{match.group(1)}"
        jobs = build_plan(out_dir)
        with tempfile.TemporaryDirectory(prefix="c6-verificar-") as tmp:
            plan = Path(tmp) / "plan.json"
            plan.write_text(json.dumps(jobs), encoding="utf-8")
            run = subprocess.run(
                ["node", "-", pw, axe, str(plan), origin],
                input=NODE_SCRIPT, text=True, capture_output=True, timeout=900,
            )
        if run.returncode != 0:
            print("BROWSER_UNAVAILABLE: measurement failed\n" + run.stderr[-2000:])
            return 2
        measurements = json.loads(run.stdout)
    finally:
        serve.terminate()

    failures = []
    for job in measurements:
        failures += evaluate(job)
    pages = [m for m in measurements if m["route"] != "hero"]
    heroes = [m for m in measurements if m["route"] == "hero"]
    probes = sum(len(m.get("results", [])) for m in heroes)
    classes = sorted({r["cls"] for m in heroes for r in m.get("results", [])})
    if len(classes) < 3:
        failures.append(f"FAIL hero probes cover only {classes}: the lengths no longer span the title-class change")
    for line in failures:
        print(line)
    if failures:
        print(f"FAIL c6 browser oracle: {len(failures)} problem(s) over {len(pages)} pages and {probes} hero probes")
        return 1
    print(f"PASS c6 browser oracle: {len(pages)} pages (3 locales x {len(WIDTHS)} widths {'/'.join(map(str, WIDTHS))} x home+story; "
          f"top bar checked at >= {TOPBAR_MIN_WIDTH}px) + {probes} synthetic hero probes (classes {', '.join(classes)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
