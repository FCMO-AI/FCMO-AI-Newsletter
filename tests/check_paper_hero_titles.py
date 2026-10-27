"""Real-font hero regressions: python3 tests/check_paper_hero_titles.py publish.

Needs the same installed Playwright/Chromium as verificar_paper.py. Requests
are fulfilled from the candidate directory, without sockets or external I/O.
Missing Chromium fails this command; it is never a skipped unit test.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.paper.build import PaperBuilder
from tools.paper.playwright_module import missing_playwright_message, resolve_playwright_module
from test_paper_hero_titles import LONG_HERO_PROBES


SCRIPT = r"""
const fs = require('node:fs'), path = require('node:path');
const { chromium } = require(process.argv[1]);
const root = path.resolve(process.argv[2]);
const probes = JSON.parse(fs.readFileSync(0, 'utf8'));
const base = '/FCMO-AI-Newsletter/';
const types = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript',
  '.json':'application/json', '.woff2':'font/woff2', '.svg':'image/svg+xml'};
(async () => {
  const browser = await chromium.launch();
  let failures = 0;
  try {
    const page = await browser.newPage();
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== 'http://paper.invalid' || !url.pathname.startsWith(base))
        return route.abort();
      let rel = decodeURIComponent(url.pathname.slice(base.length));
      if (!rel || rel.endsWith('/')) rel += 'index.html';
      const file = path.resolve(root, rel);
      if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile())
        return route.abort();
      await route.fulfill({body: fs.readFileSync(file), contentType: types[path.extname(file)] || 'application/octet-stream'});
    });
    for (const probe of probes) {
      for (const width of [1440, 390]) {
        await page.setViewportSize({width, height: width === 390 ? 844 : 900});
        await page.goto('http://paper.invalid' + base + probe.prefix, {waitUntil:'load'});
        const result = await page.evaluate(async probe => {
          const h = document.querySelector('.landing-feature h1');
          if (!h) throw new Error('hero ausente');
          h.querySelector('a').textContent = probe.text;
          [...h.classList].filter(c => c.startsWith('title-')).forEach(c => h.classList.remove(c));
          h.classList.add(probe.cls);
          await document.fonts.ready;
          const r = h.getBoundingClientRect(), s = getComputedStyle(h);
          const next = document.querySelector('.landing-feature .cover-dek, .landing-feature .cover-evrow');
          return {lines: Math.ceil(r.height / parseFloat(s.lineHeight) - .01), height: r.height,
            fontSize: s.fontSize, column: r.width, text: h.textContent,
            nextTop: next?.getBoundingClientRect().top ?? null,
            overflow: document.documentElement.scrollWidth - innerWidth};
        }, probe);
        const ok = result.text === probe.text && result.overflow <= 0 &&
          (width === 1440 ? result.lines <= 4 && result.nextTop !== null && result.nextTop < 900 :
            result.height <= 844 * .45);
        if (!ok) failures++;
        console.log(JSON.stringify({ok, locale:probe.locale, chars:probe.text.length, cls:probe.cls, width, ...result}));
      }
    }
  } finally { await browser.close(); }
  process.exitCode = failures ? 1 : 0;
})().catch(e => {console.error(e); process.exitCode = 1;});
"""


def main():
    module = resolve_playwright_module()
    if not module:
        print(missing_playwright_message(), file=sys.stderr)
        return 1
    prefixes = {"en": "", "es-419": "es/", "zh-Hans": "zh/"}
    probes = [{"locale": code, "prefix": prefixes[code], "text": title,
               "cls": PaperBuilder._title_class(title, code, hero=True)}
              for code, title in LONG_HERO_PROBES]
    return subprocess.run(["node", "-e", SCRIPT, module, str(Path(sys.argv[1]).resolve())],
                          input=json.dumps(probes), text=True, cwd=ROOT, timeout=120).returncode


if __name__ == "__main__":
    raise SystemExit(main())
