#!/usr/bin/env python3
"""Browser QA for editorial routes and durable visual-regression contracts."""
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

BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
VIEWPORTS = ((390, 844), (768, 1024), (1440, 900))
ROUTES = (
    ("home", "index.html#/home"),
    ("archive", "archive.html"),
    ("search", "search.html"),
    ("topics", "topics.html"),
    ("organizations", "organizations.html"),
    ("status", "status.html"),
)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        pass

    def translate_path(self, path: str) -> str:
        """Serve the production BASE_PATH from the local candidate root."""
        prefix = "/FCMO-AI-Newsletter"
        if path == prefix or path.startswith(prefix + "/"):
            path = path[len(prefix):] or "/"
        return super().translate_path(path)


@contextmanager
def serve(root: Path):
    handler = lambda *args, **kwargs: Quiet(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def browser_path() -> str:
    override = os.environ.get("FCMO_BROWSER")
    if override and (shutil.which(override) or Path(override).is_file()):
        return shutil.which(override) or override
    for name in BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("editorial layout oracle: no Chromium browser found")


def harness_html() -> str:
    cases = [{"name": name, "url": url} for name, url in ROUTES]
    viewports = [{"width": width, "height": height} for width, height in VIEWPORTS]
    return f"""<!doctype html><meta charset="utf-8">
<title>FCMO editorial visual oracle</title>
<iframe id="frame" style="border:0;display:block"></iframe>
<pre id="result">pending</pre>
<script>
const routes={json.dumps(cases)};
const viewports={json.dumps(viewports)};
const frame=document.getElementById('frame');
const failures=[], measurements=[];

function wait(ms){{return new Promise(resolve=>setTimeout(resolve,ms));}}
function rgbaAlpha(value){{
  const m=String(value||'').match(/rgba?\\([^)]*[,\\s]([0-9.]+)\\s*\\)$/);
  return String(value||'').startsWith('rgba') && m ? Number(m[1]) : 1;
}}
function inside(inner,outer,tol=2){{
  return inner.left>=outer.left-tol && inner.right<=outer.right+tol &&
         inner.top>=outer.top-tol && inner.bottom<=outer.bottom+tol;
}}
async function load(route,vp){{
  frame.style.width=vp.width+'px';
  frame.style.height=vp.height+'px';
  frame.src=route.url+(route.url.includes('?')?'&':'?')+'qa='+Date.now();
  await new Promise((resolve,reject)=>{{
    const timer=setTimeout(()=>reject(new Error('load timeout '+route.name)),5000);
    frame.onload=()=>{{clearTimeout(timer);resolve();}};
  }});
  await wait(route.name==='home'?700:180);
  return [frame.contentDocument,frame.contentWindow];
}}
function inspect(route,vp,doc,win){{
  const local=[], metrics={{}};
  const root=doc.documentElement;
  const body=doc.body;
  metrics.innerWidth=win.innerWidth;
  metrics.scrollWidth=Math.max(root.scrollWidth,body?body.scrollWidth:0);
  if(metrics.scrollWidth>win.innerWidth+2)
    local.push('horizontal overflow '+metrics.scrollWidth+'>'+win.innerWidth);

  if(!body || !body.innerText.trim()) local.push('blank rendered body');

  if(route.name==='home'){{
    const topbar=doc.querySelector('.topbar');
    if(!topbar) local.push('missing .topbar');
    else{{
      const style=win.getComputedStyle(topbar);
      metrics.topbarPosition=style.position;
      metrics.topbarBackground=style.backgroundColor;
      if(vp.width<=1080 && ['sticky','fixed'].includes(style.position))
        local.push('tablet/mobile topbar remains sticky/fixed');
      if(rgbaAlpha(style.backgroundColor)<0.98)
        local.push('topbar background remains translucent');
    }}
  }} else {{
    const main=doc.querySelector('main');
    const title=doc.querySelector('.page-head h1');
    const nav=doc.querySelector('.mast nav');
    if(!main) local.push('missing main');
    if(!title) local.push('missing page title');
    if(!nav) local.push('missing publication nav');

    if(title){{
      const tr=title.getBoundingClientRect();
      metrics.titleWidth=Number(tr.width.toFixed(1));
      if(tr.right>win.innerWidth+2 || tr.left<-2)
        local.push('page title escapes viewport');
    }}

    if(nav){{
      const nr=nav.getBoundingClientRect();
      metrics.navScrollWidth=nav.scrollWidth;
      metrics.navClientWidth=nav.clientWidth;
      if(nav.scrollWidth>nav.clientWidth+2)
        local.push('publication nav requires horizontal scrolling');
      if(vp.width<=560){{
        const display=win.getComputedStyle(nav).display;
        metrics.mobileNavDisplay=display;
        if(display!=='grid') local.push('mobile publication nav is not the durable grid');
        for(const link of nav.querySelectorAll('a')){{
          if(!inside(link.getBoundingClientRect(),nr,2))
            local.push('mobile nav link escapes nav bounds');
        }}
      }}
    }}

    for(const signal of doc.querySelectorAll('.signal')){{
      const sr=signal.getBoundingClientRect();
      if(sr.height>36) local.push('status/evidence pill stretched vertically');
    }}

    if(route.name==='search'){{
      const input=doc.querySelector('.search-tool input');
      if(!input) local.push('missing search input');
      else{{
        const cs=win.getComputedStyle(input);
        const canvas=doc.createElement('canvas');
        const ctx=canvas.getContext('2d');
        ctx.font=cs.font || (cs.fontSize+' '+cs.fontFamily);
        const placeholderWidth=ctx.measureText(input.getAttribute('placeholder')||'').width;
        metrics.placeholderWidth=Number(placeholderWidth.toFixed(1));
        metrics.searchInputWidth=input.clientWidth;
        if(vp.width<=560 && placeholderWidth>input.clientWidth-6)
          local.push('mobile search placeholder is visibly clipped');
      }}
    }}

    if(route.name==='status'){{
      for(const strong of doc.querySelectorAll('.status-grid strong')){{
        const r=strong.getBoundingClientRect();
        const parent=strong.parentElement.getBoundingClientRect();
        if(r.right>parent.right+2) local.push('status value escapes its cell');
      }}
    }}
  }}

  const row={{route:route.name,width:vp.width,height:vp.height,metrics,failures:local}};
  measurements.push(row);
  failures.push(...local.map(x=>route.name+'/'+vp.width+'x'+vp.height+': '+x));
}}

(async()=>{{
  try{{
    for(const vp of viewports){{
      for(const route of routes){{
        const [doc,win]=await load(route,vp);
        inspect(route,vp,doc,win);
      }}
    }}
  }}catch(error){{failures.push(String(error&&error.stack||error));}}
  document.getElementById('result').textContent=JSON.stringify({{
    status:failures.length?'fail':'pass',
    checks:measurements.length,
    measurements,
    failures
  }});
}})();
</script>"""


def run(root: Path, json_out: Path | None) -> int:
    root = root.resolve()
    if not (root / "index.html").is_file():
        raise AssertionError(f"assembled tree has no index.html: {root}")
    browser = browser_path()
    harness = root / "__fcmo_editorial_visual_oracle__.html"
    harness.write_text(harness_html(), encoding="utf-8")
    try:
        with serve(root) as base:
            profile = Path(tempfile.mkdtemp(prefix="fcmo-editorial-qa-"))
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
                        "--virtual-time-budget=18000",
                        "--window-size=1800,1200",
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
            raise AssertionError(f"browser exited {completed.returncode}: {completed.stderr[-2500:]}")
        match = re.search(r'<pre id="result">(.*?)</pre>', completed.stdout, re.S)
        if not match:
            raise AssertionError("editorial visual harness returned no result payload")
        result = json.loads(html.unescape(match.group(1)))
        if json_out:
            json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if result.get("status") != "pass":
            raise AssertionError("editorial visual failures:\n- " + "\n- ".join(result.get("failures") or []))
        print(f"Editorial visual oracle OK: {result['checks']} route/viewport renders")
        return 0
    finally:
        harness.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("publish"))
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        return run(args.root, args.json_out)
    except (OSError, RuntimeError, AssertionError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"Editorial visual oracle FAILED: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
