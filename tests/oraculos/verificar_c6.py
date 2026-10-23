#!/usr/bin/env python3
"""Browser oracle for campaign c6 (DIRECCION §3, §5, §9): what a reader sees.

    python3 tests/oraculos/verificar_c6.py <built-site-dir>

For each locale (en, es-419, zh-Hans) at 390 and 1440 px, on the home page and
on the first story, it checks in a real Chromium:

* horizontal overflow is 0 px (every page);
* axe-core reports 0 serious or critical violations (every page);
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

NODE_SCRIPT = r"""
const fs = require('fs');
const [,, pwModule, axePath, plan, origin] = process.argv;
const { chromium } = require(pwModule);
const jobs = JSON.parse(fs.readFileSync(plan, 'utf-8'));
const AXE_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

async function measure(browser, job) {
  const ctx = await browser.newContext({ viewport: { width: job.width, height: job.width === 390 ? 844 : 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.goto(origin + job.url, { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(600);
  const result = await page.evaluate(() => {
    const rect = (el) => { const r = el.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right }; };
    const out = { overflowPx: document.documentElement.scrollWidth - window.innerWidth };
    const sig = document.querySelector('.sig-text, .story-signals');
    const src = [...document.querySelectorAll('main a[href^="http"]')].find((a) => !a.href.includes('fcmo-ai.github.io'));
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
        for width in (390, 1440):
            jobs.append({"locale": locale, "width": width, "route": "home", "url": BASE + prefix})
            jobs.append({"locale": locale, "width": width, "route": "story", "url": BASE + story["path"].lstrip("/")})
    return jobs


def evaluate(job: dict) -> list[str]:
    """Pure judgement over one measurement. Returns one message per broken rule."""
    tag = f"{job['locale']} {job['width']}px {job['route']}"
    problems = []
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
    for line in failures:
        print(line)
    checked = len(measurements)
    if failures:
        print(f"FAIL c6 browser oracle: {len(failures)} problem(s) over {checked} pages")
        return 1
    print(f"PASS c6 browser oracle: {checked} pages (3 locales x 2 widths x home+story)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
