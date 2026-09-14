#!/usr/bin/env python3
"""Print the exact DOM nodes responsible for 390px homepage overflow.

Diagnostic-only oracle: it never weakens publication gates and never returns a
failure merely because overflow exists. It runs immediately before the strict
layout oracle so a failed production candidate leaves actionable evidence.
"""
from __future__ import annotations

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

BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)


def browser() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override and (shutil.which(override) or Path(override).is_file()):
        return shutil.which(override) or override
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("mobile overflow diagnostic: no Chromium browser")


def main() -> int:
    root = Path("publish").resolve()
    harness = root / "__fcmo_mobile_overflow_diag__.html"
    harness.write_text(r'''<!doctype html><meta charset="utf-8">
<iframe id="f" style="width:390px;height:844px;border:0"></iframe><pre id="out">pending</pre>
<script>
const f=document.getElementById('f');
f.onload=()=>setTimeout(()=>{
  const d=f.contentDocument,w=f.contentWindow, vw=w.innerWidth;
  const offenders=[];
  for(const el of d.querySelectorAll('*')){
    const r=el.getBoundingClientRect(), s=w.getComputedStyle(el);
    if(r.right>vw+2 || r.left<-2 || el.scrollWidth>Math.max(el.clientWidth+2, vw+2)){
      offenders.push({
        tag:el.tagName.toLowerCase(), id:el.id||'', cls:String(el.className||'').slice(0,180),
        left:+r.left.toFixed(1), right:+r.right.toFixed(1), width:+r.width.toFixed(1),
        clientWidth:el.clientWidth, scrollWidth:el.scrollWidth,
        position:s.position, display:s.display, minWidth:s.minWidth, cssWidth:s.width,
        whiteSpace:s.whiteSpace, transform:s.transform,
        text:(el.textContent||'').replace(/\s+/g,' ').trim().slice(0,120)
      });
    }
  }
  offenders.sort((a,b)=>Math.max(b.right,b.scrollWidth)-Math.max(a.right,a.scrollWidth));
  document.getElementById('out').textContent=JSON.stringify({viewport:vw,rootScroll:d.documentElement.scrollWidth,offenders:offenders.slice(0,30)});
},700);
f.src='index.html?overflow-diag='+Date.now()+'#/home';
</script>''', encoding="utf-8")
    profile = Path(tempfile.mkdtemp(prefix="fcmo-overflow-diag-"))
    try:
        with serve(root) as base:
            proc = subprocess.run([
                browser(), "--headless=new", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--virtual-time-budget=5000",
                "--window-size=900,1100", f"--user-data-dir={profile}",
                "--dump-dom", base + harness.name,
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        match = re.search(r'<pre id="out">(.*?)</pre>', proc.stdout, re.S)
        if not match:
            print("MOBILE OVERFLOW DIAGNOSTIC unavailable")
            return 0
        payload = json.loads(html.unescape(match.group(1)))
        print("MOBILE OVERFLOW DIAGNOSTIC " + json.dumps(payload, ensure_ascii=False))
        return 0
    finally:
        harness.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
