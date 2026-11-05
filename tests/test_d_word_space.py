"""Display words must never fuse (11-05: «Nolettershavebeenpublishedyet»).

Inter Tight's space is narrow at 700/900 and the display rules tighten letter-spacing; any display element that sets no
word-spacing floor (the empty-Letters <strong>, the evidence-map boxes) renders words almost touching. The HTML always had
the spaces, so only a rendered measurement sees it: a space must stay >= .195em wide wherever letter-spacing is negative.
A missing browser is a failure, never a skip (FCMO_REQUIRE_BROWSER)."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.paper.playwright_module import resolve_playwright_module, missing_playwright_message

ROOT = Path(__file__).resolve().parents[1]
CSS = Path(os.environ.get("D_CSS_ROOT") or ROOT / "site-src/assets")

PAGE = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<link rel="stylesheet" href="css/d/d-base.css"><link rel="stylesheet" href="css/d/d-front.css"></head>
<body class="d-site"><main class="d-front">
<section class="d-front-letters d-front-letters--empty"><a class="d-letters-card"><span class="d-letters-card-body">
<strong data-letters-empty>No letters have been published yet.</strong></span></a></section>
<h1 class="cover-title">Production Codex decisions and safety evaluation</h1>
<h3>OpenAI reports a safety evaluation gap with production decisions</h3>
<div class="d-map-node d-map-node--claim"><span class="d-map-row"><span class="d-map-text">OpenAI reports a safety evaluation gap</span></span></div>
</main></body></html>"""

PROBE = r"""
const {chromium}=require(process.argv[2]);
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1440,height:900}});
await pg.goto('file://'+process.argv[3]);await pg.evaluate(()=>document.fonts.ready);
const r=await pg.evaluate(()=>{const out=[];
 for(const e of document.querySelectorAll('h1,h3,strong,.d-map-text')){const cs=getComputedStyle(e);
  const m=t=>{const s=document.createElement('span');s.style.cssText='position:absolute;white-space:pre;visibility:hidden;font:'+cs.font+';letter-spacing:'+cs.letterSpacing+';word-spacing:'+cs.wordSpacing;s.textContent=t;e.appendChild(s);const x=s.getBoundingClientRect().width;s.remove();return x;};
  out.push([e.tagName+'.'+e.className,(m('ii ii')-m('iiii'))/parseFloat(cs.fontSize),cs.letterSpacing]);}
 return out;});
console.log(JSON.stringify(r));await b.close();})();
"""


class DisplayWordSpace(unittest.TestCase):
    def test_rendered_space_never_collapses(self):
        mod = resolve_playwright_module()
        if not mod:
            self.fail(missing_playwright_message())
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "css").symlink_to(CSS / "css")
            (tmp / "fonts").symlink_to(CSS / "fonts")
            (tmp / "assets").symlink_to(CSS)
            page = tmp / "p.html"
            page.write_text(PAGE.format(lang="en"))
            (tmp / "probe.cjs").write_text(PROBE)
            out = subprocess.run(["node", str(tmp / "probe.cjs"), mod, str(page)], capture_output=True, text=True, timeout=120)
            self.assertEqual(out.returncode, 0, out.stderr)
            rows = json.loads(out.stdout)
        self.assertGreaterEqual(len(rows), 4)
        for name, gap, ls in rows:
            self.assertGreaterEqual(gap, 0.195, f"{name} (letter-spacing {ls}) space is {gap:.3f}em: words fuse")


if __name__ == "__main__":
    unittest.main()
