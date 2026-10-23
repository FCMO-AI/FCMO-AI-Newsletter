#!/usr/bin/env python3
"""Render the three paper front pages at desktop/mobile before deployment."""
from __future__ import annotations

import argparse
import json
import os
import select
import tempfile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module
from tools.release_process import run_command
HARNESS = ROOT / "tests" / "harness" / "browser"
SERVE = ROOT / "tests" / "harness" / "serve.py"

LAYOUT_BUDGETS = r'''const { createRequire } = require('node:module');
const requireFromRepo = createRequire(process.cwd() + '/__paper_oracle__.cjs');
const { chromium } = requireFromRepo(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.argv[1], rows = JSON.parse(require('node:fs').readFileSync(process.argv[2], 'utf8'));
(async () => {
  const browser = await chromium.launch();
  try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const evaluate = async (...args) => {
    let timer;
    try {
      return await Promise.race([page.evaluate(...args), new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('evaluation exceeded 20 s')), 20000);
      })]);
    } finally { clearTimeout(timer); }
  };
  let visited = 0;
  const progress = (kind, total) => {
    if (visited++ % 10 === 0) console.log(`Diseño: ${kind}; ruta ${visited}/${total}`);
  };
  const failures = [];
  const storyRoutes = rows.filter(r => r.kind === 'story');
  // Empty-set guard: a budget that matches no page proves nothing. A retired route kind must fail loudly, never print 0.
  if (!storyRoutes.length) failures.push('story-layout budget ran on 0 story pages (route kind retired or renamed?)');
  for (const route of storyRoutes) {
    progress('historias', storyRoutes.length);
    const url = new URL(route.path, base).href;
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      try {
        await page.setViewportSize(viewport);
        await page.goto(url, { waitUntil: 'load', timeout: 20000 });
        await evaluate(() => document.fonts?.ready.then(() => true));
        const result = await evaluate(() => {
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
      } catch (e) {
        failures.push(`${route.path} ${viewport.width}px: check error: ${e.message}`);
      }
    }
  }
  // c6: the locale root is the one front page (route kind 'landing'); the old 'front' kind no longer exists.
  const frontRoutes = rows.filter(r => r.kind === 'landing');
  const frontLocales = [...new Set(frontRoutes.map(r => r.locale))].sort();
  if (frontRoutes.length < 3 || frontLocales.length < 3)
    failures.push(`home-page budget ran on ${frontRoutes.length} landing pages in [${frontLocales.join(', ')}]; expected the front page of all 3 locales`);
  visited = 0;
  for (const route of frontRoutes) {
    progress('portadas', frontRoutes.length);
    const url = new URL(route.path, base).href;
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      try {
        await page.setViewportSize(viewport);
        await page.goto(url, { waitUntil: 'load', timeout: 20000 });
        await evaluate(() => document.fonts?.ready.then(() => true));
        const result = await evaluate(() => {
          const h = document.querySelector('.landing-feature h1');
          // The cover has no separate dek: its next line is the evidence row (grade, sources, gaps); it must be above 900 px.
          const dek = document.querySelector('.landing-feature .cover-dek') || document.querySelector('.landing-feature .cover-evrow');
          // An author-level display rule must never override the hidden attribute (stale banner on a FRESH edition).
          const shownHidden = [...document.querySelectorAll('[hidden]')].filter(e => getComputedStyle(e).display !== 'none')
            .map(e => e.className || e.tagName);
          if (shownHidden.length) return { shownHidden };
          if (!h) return { missing: true };
          const rect = h.getBoundingClientRect(), cs = getComputedStyle(h);
          const lineHeight = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize);
          return { height: rect.height, lines: Math.ceil(rect.height / lineHeight - .01),
            dekTop: dek?.getBoundingClientRect().top ?? null };
        });
        if (result.shownHidden) failures.push(`${route.path || '/'} ${viewport.width}px: hidden elements rendered: ${result.shownHidden.join(', ')}`);
        else if (result.missing) failures.push(`${route.path || '/'}: home hero h1 missing`);
        else if (viewport.width === 1440 && (result.lines > 4 || result.dekTop == null || result.dekTop >= 900))
          failures.push(`${route.path || '/'} desktop home hero: lines=${result.lines} dekTop=${result.dekTop}`);
        else if (viewport.width === 390 && result.height > viewport.height * .45)
          failures.push(`${route.path || '/'} mobile home hero: h1=${result.height.toFixed(1)}px > 45%`);
      } catch (e) {
        failures.push(`${route.path || '/'} ${viewport.width}px: home hero check error: ${e.message}`);
      }
    }
  }
  const zhRoutes = rows.filter(r => r.locale === 'zh-Hans');
  if (zhRoutes.length < 2) failures.push(`zh heading budget ran on ${zhRoutes.length} zh-Hans pages besides the front (route table lost its zh pages?)`);
  if (!zhRoutes.some(r => r.path === 'zh/')) zhRoutes.unshift({path:'zh/', locale:'zh-Hans'});
  visited = 0;
  for (const route of zhRoutes) {
    progress('encabezados chinos', zhRoutes.length);
    const url = new URL(route.path, base).href;
    for (const viewport of [{width:1440,height:900}, {width:390,height:844}]) {
      try {
        await page.setViewportSize(viewport);
        await page.goto(url, { waitUntil: 'load', timeout: 20000 });
        const bad = await evaluate(() => [...document.querySelectorAll('h1 a,h2 a,h3 a')].flatMap(a => {
          const h = a.closest('h1,h2,h3'); if (!h) return [];
          const cs = getComputedStyle(h), lh = parseFloat(cs.lineHeight), fs = parseFloat(cs.fontSize);
          const rect = h.getBoundingClientRect();
          if (rect.height <= lh * 1.1) return [];
          return lh / fs >= 1.25 ? [] : [{text:h.innerText.slice(0,70), ratio:lh/fs}];
        }));
        for (const entry of bad) failures.push(`${route.path} ${viewport.width}px: CJK linked heading leading ${entry.ratio.toFixed(2)} ${entry.text}`);
      } catch (e) {
        failures.push(`${route.path} ${viewport.width}px: CJK heading check error: ${e.message}`);
      }
    }
  }
  if (failures.length) { console.error(failures.join('\n')); process.exitCode = 1; return; }
  console.log(`PASS story-layout budgets stories=${storyRoutes.length} home-pages=${frontRoutes.length} zh-heading-pages=${zhRoutes.length} viewports=2`);
  } finally { await browser.close(); }
})().catch(e => { console.error(`BROWSER_UNAVAILABLE: ${e.message}`); process.exit(2); });'''


def run_check(name: str, urls: list[str], extra: list[str], env: dict[str, str]) -> None:
    command = ["node", str(HARNESS / name), *urls, "--viewport", "1440x900", "--viewport", "390x844", *extra]
    completed = run_command(command, cwd=ROOT, env=env, text=True, capture_output=True, timeout=420)
    if completed.returncode == 2:
        raise RuntimeError(completed.stderr.strip() or f"{name}: browser unavailable")
    if completed.returncode != 0:
        try: detail = json.dumps(json.loads(completed.stdout), ensure_ascii=False)[:4000]
        except ValueError: detail = (completed.stdout + completed.stderr)[-4000:]
        raise AssertionError(f"{name} failed: {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("root", type=Path); args = parser.parse_args(argv)
    if not args.root.is_dir(): raise SystemExit(f"PAPER ORACLE FAIL: not a directory: {args.root}")
    env = os.environ.copy()
    module = resolve_playwright_module()
    if not module:
        raise SystemExit(missing_playwright_message())
    env["PLAYWRIGHT_MODULE"] = module
    server_errors = tempfile.TemporaryFile(mode="w+t")
    server = subprocess.Popen(
        [sys.executable, str(SERVE), "--root", str(args.root.resolve()), "--base", "/FCMO-AI-Newsletter/", "--port", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=server_errors, text=True,
    )
    try:
        if not server.stdout or not select.select([server.stdout], [], [], 15)[0]:
            raise RuntimeError("el servidor no anunció su inicio dentro del límite de 15 s")
        line = server.stdout.readline().strip()
        if not line.startswith("SERVING "):
            server_errors.seek(0)
            error = server_errors.read(4000)
            raise RuntimeError(f"static server did not start: {line} {error}".strip())
        base = line.split(maxsplit=1)[1]
        urls = [base, base + "es/", base + "zh/"]
        run_check("first_screen.mjs", urls, [], env)
        run_check("overflow.mjs", urls, [], env)
        # Font-size/accessibility baseline without adding axe-core as a dependency.
        # The full V4 axe run remains a release-level check once axe-core is provided.
        run_check("axe.mjs", urls, ["--no-axe", "--min-font", "12"], env)
        # The route list is passed as a file: all 447 routes exceed the kernel's per-variable limit (E2BIG).
        completed = run_command(
            ["node", "--input-type=commonjs", "-e", LAYOUT_BUDGETS, base, str((args.root / "data" / "routes.json").resolve())],
            cwd=ROOT, env=env, text=True, timeout=1800,
        )
        if completed.returncode == 2:
            raise RuntimeError("layout budgets: navegador no disponible; consulte la salida anterior")
        if completed.returncode != 0:
            raise AssertionError("layout budgets: comprobación fallida; consulte la salida anterior")
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"PAPER ORACLE FAIL: tiempo agotado; límite de {exc.timeout} s") from exc
    except (AssertionError, OSError, RuntimeError) as exc:
        raise SystemExit(f"PAPER ORACLE FAIL: {exc}") from exc
    finally:
        try:
            server.terminate()
            try: server.wait(timeout=2)
            except subprocess.TimeoutExpired: pass
        finally:
            server.kill()
            server.wait()
            if server.stdout: server.stdout.close()
            server_errors.close()
    print("PASS 3 locales x 2 viewports")
    return 0


if __name__ == "__main__": raise SystemExit(main())
