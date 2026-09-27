#!/usr/bin/env python3
"""Render the three paper front pages at desktop/mobile before deployment."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tests" / "harness" / "browser"
SERVE = ROOT / "tests" / "harness" / "serve.py"
PLAYWRIGHT = Path("/srv/fcmo/agents/work/newsletter/browser/node_modules/playwright")

LAYOUT_BUDGETS = r'''const { createRequire } = require('node:module');
const requireFromRepo = createRequire(process.cwd() + '/__paper_oracle__.cjs');
const { chromium } = requireFromRepo(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.argv[1], rows = JSON.parse(require('node:fs').readFileSync(process.argv[2], 'utf8'));
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const failures = [];
  const storyRoutes = rows.filter(r => r.kind === 'story');
  for (const route of storyRoutes) {
    const url = new URL(route.path, base).href;
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      await page.setViewportSize(viewport);
      await page.goto(url, { waitUntil: 'load', timeout: 20000 });
      await page.evaluate(() => document.fonts?.ready.then(() => true));
      const result = await page.evaluate(() => {
        const h = document.querySelector('.story-header h1');
        const dek = document.querySelector('.story-header .story-dek');
        if (!h) return { missing: true };
        const rect = h.getBoundingClientRect(), cs = getComputedStyle(h);
        const lineHeight = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize);
        return { height: rect.height, lines: Math.ceil(rect.height / lineHeight - .01),
          dekTop: dek?.getBoundingClientRect().top ?? null, fontSize: parseFloat(cs.fontSize) };
      });
      if (result.missing) failures.push(`${route.path}: story h1 missing`);
      else if (viewport.width === 1440 && (result.lines > 4 || result.dekTop == null || result.dekTop >= 900))
        failures.push(`${route.path} desktop: lines=${result.lines} dekTop=${result.dekTop}`);
      else if (viewport.width === 390 && result.height > viewport.height * .45)
        failures.push(`${route.path} mobile: h1=${result.height.toFixed(1)}px > 45%`);
    }
  }
  const zhRoutes = rows.filter(r => r.locale === 'zh-Hans');
  if (!zhRoutes.some(r => r.path === 'zh/')) zhRoutes.unshift({path:'zh/', locale:'zh-Hans'});
  for (const route of zhRoutes) {
    const url = new URL(route.path, base).href;
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      await page.setViewportSize(viewport);
      await page.goto(url, { waitUntil: 'load', timeout: 20000 });
      const bad = await page.evaluate(() => [...document.querySelectorAll('h1 a,h2 a,h3 a')].flatMap(a => {
        const h = a.closest('h1,h2,h3'); if (!h) return [];
        const cs = getComputedStyle(h), lh = parseFloat(cs.lineHeight), fs = parseFloat(cs.fontSize);
        const rect = h.getBoundingClientRect();
        if (rect.height <= lh * 1.1) return [];
        return lh / fs >= 1.25 ? [] : [{text:h.innerText.slice(0,70), ratio:lh/fs}];
      }));
      for (const entry of bad) failures.push(`${route.path} ${viewport.width}px: CJK linked heading leading ${entry.ratio.toFixed(2)} ${entry.text}`);
    }
  }
  await browser.close();
  if (failures.length) { console.error(failures.join('\n')); process.exit(1); }
  console.log(`PASS story-layout budgets stories=${storyRoutes.length} zh-heading-pages=${zhRoutes.length} viewports=2`);
})().catch(e => { console.error(`BROWSER_UNAVAILABLE: ${e.message}`); process.exit(2); });'''


def run_check(name: str, urls: list[str], extra: list[str], env: dict[str, str]) -> None:
    command = ["node", str(HARNESS / name), *urls, "--viewport", "1440x900", "--viewport", "390x844", *extra]
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=420)
    if completed.returncode == 2:
        raise RuntimeError(completed.stderr.strip() or f"{name}: browser unavailable")
    if completed.returncode != 0:
        try: detail = json.dumps(json.loads(completed.stdout), ensure_ascii=False)[:4000]
        except ValueError: detail = (completed.stdout + completed.stderr)[-4000:]
        raise AssertionError(f"{name} failed: {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    if not args.root.is_dir(): raise SystemExit(f"PAPER ORACLE FAIL: not a directory: {args.root}")
    env = os.environ.copy(); env.setdefault("PLAYWRIGHT_MODULE", str(PLAYWRIGHT))
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--root", str(args.root.resolve()), "--base", "/FCMO-AI-Newsletter/", "--port", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        line = server.stdout.readline().strip() if server.stdout else ""
        if not line.startswith("SERVING "):
            error = server.stderr.read() if server.stderr else ""
            raise RuntimeError(f"static server did not start: {line} {error}".strip())
        base = line.split(maxsplit=1)[1]
        urls = [base, base + "es/", base + "zh/"]
        run_check("first_screen.mjs", urls, [], env)
        run_check("overflow.mjs", urls, [], env)
        # Font-size/accessibility baseline without adding axe-core as a dependency.
        # The full V4 axe run remains a release-level check once axe-core is provided.
        run_check("axe.mjs", urls, ["--no-axe", "--min-font", "12"], env)
        # The route list is passed as a file: all 447 routes exceed the kernel's per-variable limit (E2BIG).
        completed = subprocess.run(
            ["node", "--input-type=commonjs", "-e", LAYOUT_BUDGETS, base, str((args.root / "data" / "routes.json").resolve())],
            cwd=ROOT, env=env, text=True, capture_output=True, timeout=900,
        )
        if completed.returncode == 2:
            raise RuntimeError(completed.stderr.strip() or "layout budgets: browser unavailable")
        if completed.returncode != 0:
            raise AssertionError((completed.stdout + completed.stderr)[-6000:])
        print(completed.stdout.strip())
    except (AssertionError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"PAPER ORACLE FAIL: {exc}") from exc
    finally:
        server.terminate()
        try: server.wait(timeout=10)
        except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=10)
    print("PASS 3 locales x 2 viewports")
    return 0


if __name__ == "__main__": raise SystemExit(main())
