#!/usr/bin/env python3
"""Render the Newsletter across physical viewport sizes and verify layout invariants.

This oracle guards the responsive failure class fixed by the 2026-09-10 visual
maintenance pass: short desktop hero overflow, thumbnail/text collisions in the
Front Page and Chronology surfaces, visible FCMO Wire navigation, and accidental
horizontal overflow. It uses only a real Chromium-family browser plus the Python
standard library; no browser automation package is required.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BROWSER_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "msedge",
    "microsoft-edge",
    "microsoft-edge-stable",
)
VIEWPORTS = (
    (390, 844),
    (1152, 720),
    (1280, 720),
    (1366, 768),
    (1440, 900),
    (1920, 1080),
)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


def browser_path() -> str:
    """Resolve the same browser families accepted by the existing DOM oracle."""
    override = os.environ.get("FCMO_BROWSER")
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return str(candidate)
        resolved = shutil.which(override)
        if resolved:
            return resolved
        raise RuntimeError(f"FCMO_BROWSER does not resolve to an executable: {override}")
    for name in BROWSER_CANDIDATES:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise RuntimeError("no supported Chrome/Chromium/Edge browser found")


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def harness_html() -> str:
    """Return a same-origin iframe harness whose iframe dimensions are the viewport.

    Footnote: an iframe has its own CSS viewport, so width *and height* media
    queries execute exactly against the tested dimensions. The outer browser only
    coordinates the tests; it does not substitute a guessed layout calculation.
    """
    viewports = json.dumps([{"width": w, "height": h} for w, h in VIEWPORTS])
    return f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>FCMO layout oracle</title></head>
<body><iframe id=\"frame\" style=\"border:0;display:block\"></iframe><pre id=\"fcmo-layout-result\">pending</pre>
<script>
const viewports={viewports};
const failures=[]; const cases=[];
const frame=document.getElementById('frame');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function overlap(a,b){{return a.left < b.right-0.5 && a.right > b.left+0.5 && a.top < b.bottom-0.5 && a.bottom > b.top+0.5;}}
function visible(el){{if(!el)return false;const s=el.ownerDocument.defaultView.getComputedStyle(el);const r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&r.width>0&&r.height>0;}}
async function load(width,height,route){{
  frame.style.width=width+'px'; frame.style.height=height+'px';
  await new Promise((resolve,reject)=>{{
    const timer=setTimeout(()=>reject(new Error('iframe timeout '+route+' '+width+'x'+height)),8000);
    frame.onload=()=>{{clearTimeout(timer);resolve();}};
    frame.src='index.html?layout-oracle='+Date.now()+'#/'+route;
  }});
  await sleep(260);
  return [frame.contentWindow,frame.contentDocument];
}}
function record(width,height,route,doc,win){{
  const local=[];
  const root=doc.documentElement;
  if(root.scrollWidth > win.innerWidth + 2) local.push(`horizontal overflow ${{root.scrollWidth}}>${{win.innerWidth}}`);
  if(!doc.body || !doc.body.innerText.trim()) local.push('blank rendered body');

  if(route==='home'){{
    const hero=doc.querySelector('.hero');
    if(!hero) local.push('missing .hero');
    if(width>1080 && hero && hero.getBoundingClientRect().bottom > win.innerHeight + 2)
      local.push(`desktop hero exceeds first viewport: ${{hero.getBoundingClientRect().bottom.toFixed(1)}}>${{win.innerHeight}}`);

    const frontHeading=[...doc.querySelectorAll('.section-head h2')].find(x=>x.textContent.replace(/\\s+/g,' ').trim()==='What else matters now.');
    if(!frontHeading) local.push('missing approved Front Page heading');

    const wire=[...doc.querySelectorAll('a,button')].filter(x=>visible(x)&&/\\bFCMO\\s+Wire\\b/i.test(x.textContent||''));
    if(wire.length) local.push(`visible FCMO Wire controls: ${{wire.length}}`);

    for(const thumb of doc.querySelectorAll('.headline-stack .story-visual.thumb')){{
      const link=thumb.closest('a'); const text=link&&link.querySelector(':scope > span');
      if(text && overlap(thumb.getBoundingClientRect(),text.getBoundingClientRect())) local.push('Front Page thumbnail intersects headline text');
    }}
  }}

  if(route==='chronology'){{
    const cards=[...doc.querySelectorAll('.timeline-card')];
    if(!cards.length) local.push('missing chronology timeline cards');
    for(const card of cards){{
      const thumb=card.querySelector('.story-visual.thumb,.story-visual');
      const text=[...card.children].find(x=>!x.classList.contains('story-visual'));
      if(thumb&&text&&overlap(thumb.getBoundingClientRect(),text.getBoundingClientRect())) local.push('Chronology thumbnail intersects story text');
    }}
  }}

  cases.push({{width,height,route,failures:local}}); failures.push(...local.map(x=>`${{route}}/${{width}}x${{height}}: ${{x}}`));
}}
(async()=>{{
  try{{
    for(const vp of viewports){{
      let pair=await load(vp.width,vp.height,'home'); record(vp.width,vp.height,'home',pair[1],pair[0]);
      pair=await load(vp.width,vp.height,'chronology'); record(vp.width,vp.height,'chronology',pair[1],pair[0]);
    }}
  }}catch(error){{failures.push(String(error&&error.stack||error));}}
  const result={{status:failures.length?'fail':'pass',viewports,cases,route_viewport_checks:cases.length,overflow_failures:failures.filter(x=>x.includes('overflow')).length,blank_route_failures:failures.filter(x=>x.includes('blank')||x.includes('missing .hero')||x.includes('missing chronology')).length,javascript_failures:failures.some(x=>x.includes('Error:'))?1:0,failures}};
  document.getElementById('fcmo-layout-result').textContent=JSON.stringify(result);
}})();
</script></body></html>"""


def run(root: Path, json_out: Path | None) -> int:
    root = root.resolve()
    if not (root / "index.html").is_file():
        raise AssertionError(f"assembled tree has no index.html: {root}")
    browser = browser_path()
    harness = root / "__fcmo_layout_oracle__.html"
    harness.write_text(harness_html(), encoding="utf-8")
    try:
        with serve(root) as base:
            profile = Path(tempfile.mkdtemp(prefix="fcmo-layout-profile-"))
            try:
                completed = subprocess.run(
                    [
                        browser,
                        "--headless=new",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--disable-background-networking",
                        "--hide-scrollbars",
                        "--virtual-time-budget=22000",
                        "--window-size=2200,1400",
                        f"--user-data-dir={profile}",
                        "--dump-dom",
                        base + harness.name,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=45,
                )
            finally:
                shutil.rmtree(profile, ignore_errors=True)
        if completed.returncode != 0:
            raise AssertionError(f"browser exited {completed.returncode}: {completed.stderr[-3000:]}")
        match = re.search(r'<pre id="fcmo-layout-result">(.*?)</pre>', completed.stdout, re.S)
        if not match:
            raise AssertionError("layout harness returned no result payload")
        result = json.loads(html.unescape(match.group(1)))
        version = subprocess.run(
            [browser, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace"
        ).stdout.strip() or Path(browser).name
        result["browser"] = version
        if json_out:
            json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if result.get("status") != "pass":
            raise AssertionError("layout contract failures:\n- " + "\n- ".join(result.get("failures") or []))
        print(
            f"Layout browser oracle OK: {result['route_viewport_checks']} route/viewport renders; "
            f"widths={[v['width'] for v in result['viewports']]}; browser={version}"
        )
        return 0
    finally:
        harness.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("publish"))
    parser.add_argument("--json-out", type=Path, help="optional machine-readable QA receipt")
    args = parser.parse_args(argv)
    try:
        return run(args.root, args.json_out)
    except (OSError, RuntimeError, AssertionError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"Layout browser oracle FAILED: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
