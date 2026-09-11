#!/usr/bin/env python3
"""Render the Newsletter across physical viewport sizes and verify layout invariants.

This oracle guards the responsive failure classes fixed by the 2026-09-10 visual
maintenance passes: short desktop hero overflow, thumbnail/text collisions,
visible FCMO Wire navigation, accidental horizontal overflow, weakened editorial
hierarchy, an over-tall footer, and Front Page structures that stop behaving like
one composed desktop view. It uses a real Chromium-family browser plus the Python
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
    (1648, 900),
    (1920, 1080),
)
# Footnote: English remains the semantic source, but layout is a presentation
# contract shared by all three native editions. These extra cases specifically
# guard the longer Spanish hero observed in production plus Simplified Chinese.
LOCALIZED_HOME_CASES = (
    (1366, 768, "es-419"),
    (1648, 900, "es-419"),
    (1366, 768, "zh-Hans"),
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
    localized = json.dumps(
        [{"width": w, "height": h, "locale": locale} for w, h, locale in LOCALIZED_HOME_CASES]
    )
    return f"""<!doctype html><html><head><meta charset=\"utf-8\"><title>FCMO layout oracle</title></head>
<body><iframe id=\"frame\" style=\"border:0;display:block\"></iframe><pre id=\"fcmo-layout-result\">pending</pre>
<script>
const viewports={viewports};
const localizedHomeCases={localized};
const failures=[]; const cases=[];
const frame=document.getElementById('frame');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function overlap(a,b){{return a.left < b.right-0.5 && a.right > b.left+0.5 && a.top < b.bottom-0.5 && a.bottom > b.top+0.5;}}
function visible(el){{if(!el)return false;const s=el.ownerDocument.defaultView.getComputedStyle(el);const r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&r.width>0&&r.height>0;}}
function px(el,property){{return el?parseFloat(el.ownerDocument.defaultView.getComputedStyle(el)[property]||'0'):0;}}
async function load(width,height,route,locale='en'){{
  frame.style.width=width+'px'; frame.style.height=height+'px';
  await new Promise((resolve,reject)=>{{
    const timer=setTimeout(()=>reject(new Error('iframe timeout '+route+' '+locale+' '+width+'x'+height)),8000);
    frame.onload=()=>{{clearTimeout(timer);resolve();}};
    const language=locale==='en'?'':'&lang='+encodeURIComponent(locale);
    frame.src='index.html?layout-oracle='+Date.now()+language+'#/'+route;
  }});
  // Footnote: curated locale presentation is deterministic but executes after
  // initial DOM construction; this wait observes the post-localization layout.
  await sleep(340);
  return [frame.contentWindow,frame.contentDocument];
}}
function record(width,height,route,locale,doc,win){{
  const local=[];
  const metrics={{}};
  const root=doc.documentElement;
  if(root.scrollWidth > win.innerWidth + 2) local.push(`horizontal overflow ${{root.scrollWidth}}>${{win.innerWidth}}`);
  if(!doc.body || !doc.body.innerText.trim()) local.push('blank rendered body');

  if(route==='home'){{
    const hero=doc.querySelector('.hero');
    const heroTitle=doc.querySelector('.hero h1');
    const lead=doc.querySelector('.lead');
    const leadTitle=doc.querySelector('.lead-body h2');
    const frontGrid=doc.querySelector('.front-grid');
    const frontSection=frontGrid&&frontGrid.closest('.section');
    const frontHeading=frontSection&&frontSection.querySelector('.section-head h2');
    const footer=doc.querySelector('.footer');

    if(!hero) local.push('missing .hero');
    if(!lead) local.push('missing .lead');
    if(!frontGrid) local.push('missing .front-grid');
    if(!footer) local.push('missing .footer');

    if(hero) metrics.hero_height=Number(hero.getBoundingClientRect().height.toFixed(1));
    if(heroTitle) metrics.hero_title_px=Number(px(heroTitle,'fontSize').toFixed(1));
    if(lead) metrics.lead_height=Number(lead.getBoundingClientRect().height.toFixed(1));
    if(leadTitle) metrics.lead_title_px=Number(px(leadTitle,'fontSize').toFixed(1));
    if(frontSection) metrics.front_section_height=Number(frontSection.getBoundingClientRect().height.toFixed(1));
    if(footer) metrics.footer_height=Number(footer.getBoundingClientRect().height.toFixed(1));

    if(width>1080 && hero && hero.getBoundingClientRect().bottom > win.innerHeight + 2)
      local.push(`desktop hero exceeds first viewport: ${{hero.getBoundingClientRect().bottom.toFixed(1)}}>${{win.innerHeight}}`);

    /* [ORACLE-ER01] The 2026-09-10 follow-up explicitly restores cover authority.
       A relative floor catches a future height rule that quietly shrinks the hero
       back into the timid state seen in the production screenshot. */
    if(width>=1366 && heroTitle){{
      const minimum=Math.min(118,width*.078);
      if(px(heroTitle,'fontSize') < minimum)
        local.push(`hero title lost desktop authority: ${{px(heroTitle,'fontSize').toFixed(1)}}px < ${{minimum.toFixed(1)}}px`);
    }}

    /* [ORACLE-ER02] Same principle for the lead headline: preserve the stronger
       intimidating editorial scale while allowing the narrowest desktop regime
       to remain more conservative. */
    if(width>=1366 && leadTitle){{
      const minimum=Math.min(80,width*.052);
      if(px(leadTitle,'fontSize') < minimum)
        local.push(`lead headline lost editorial force: ${{px(leadTitle,'fontSize').toFixed(1)}}px < ${{minimum.toFixed(1)}}px`);
    }}

    if(!frontHeading || !frontHeading.textContent.trim()) local.push('missing Front Page heading');
    if(locale==='en' && frontHeading && frontHeading.textContent.replace(/\\s+/g,' ').trim()!=='What else matters now.')
      local.push('missing approved English Front Page heading');

    const wire=[...doc.querySelectorAll('a,button')].filter(x=>visible(x)&&/\\bFCMO\\s+Wire\\b/i.test(x.textContent||''));
    if(wire.length) local.push(`visible FCMO Wire controls: ${{wire.length}}`);

    for(const thumb of doc.querySelectorAll('.headline-stack .story-visual.thumb')){{
      const link=thumb.closest('a'); const text=link&&link.querySelector(':scope > span');
      if(text && overlap(thumb.getBoundingClientRect(),text.getBoundingClientRect())) local.push('Front Page thumbnail intersects headline text');
    }}

    /* [ORACLE-ER03] At wide desktop the Front Page must read as macro + secondary
       + three quick signals, not collapse back into three equally weighted columns. */
    if(width>=1280 && frontGrid){{
      const feature=frontGrid.querySelector(':scope > .front-story.feature');
      const secondary=frontGrid.querySelector(':scope > .front-story:not(.feature)');
      const stack=frontGrid.querySelector(':scope > .headline-stack');
      if(!feature||!secondary||!stack) local.push('Front Page editorial hierarchy is incomplete');
      else{{
        const f=feature.getBoundingClientRect(), s=secondary.getBoundingClientRect(), q=stack.getBoundingClientRect();
        if(!(f.left < s.left-8 && Math.abs(f.top-s.top)<4)) local.push('Front Page feature is not the dominant left story');
        if(q.top < s.bottom-2 || Math.abs(q.left-s.left)>4) local.push('Front Page quick-signal rail is not below the secondary story');
        if(Math.abs(f.bottom-q.bottom)>5) local.push('Front Page macro and right rail do not close on one baseline');
        const links=[...stack.querySelectorAll(':scope > a')];
        if(links.length!==3) local.push(`Front Page quick-signal rail expected 3 stories, found ${{links.length}}`);
        if(links.length===3){{
          const rects=links.map(x=>x.getBoundingClientRect());
          if(!(rects[0].left < rects[1].left-4 && rects[1].left < rects[2].left-4 && Math.abs(rects[0].top-rects[2].top)<4))
            local.push('Front Page quick signals are not a horizontal three-item rail');
        }}
      }}
    }}

    /* [ORACLE-ER04] A desktop section should behave as one designed view. This
       is intentionally scoped to standard >=1366px desktops; 720px-high narrow
       screens remain supported without forcing editorial copy to disappear. */
    if(width>=1366 && height>=768){{
      if(lead && lead.getBoundingClientRect().height > win.innerHeight + 8)
        local.push(`lead section no longer fits one desktop view: ${{lead.getBoundingClientRect().height.toFixed(1)}}>${{win.innerHeight+8}}`);
      if(frontSection && frontSection.getBoundingClientRect().height > win.innerHeight + 8)
        local.push(`Front Page section no longer fits one desktop view: ${{frontSection.getBoundingClientRect().height.toFixed(1)}}>${{win.innerHeight+8}}`);
    }}

    /* [ORACLE-ER05] Footer is deliberately a compact closing instrument. A hard
       desktop ceiling catches regression back to the former pseudo-hero footer. */
    if(width>1080 && footer){{
      const ceiling=Math.min(320,win.innerHeight*.42);
      if(footer.getBoundingClientRect().height > ceiling)
        local.push(`footer expanded beyond compact close: ${{footer.getBoundingClientRect().height.toFixed(1)}}>${{ceiling.toFixed(1)}}`);
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

  cases.push({{width,height,route,locale,metrics,failures:local}});
  failures.push(...local.map(x=>`${{route}}/${{locale}}/${{width}}x${{height}}: ${{x}}`));
}}
(async()=>{{
  try{{
    for(const vp of viewports){{
      let pair=await load(vp.width,vp.height,'home','en'); record(vp.width,vp.height,'home','en',pair[1],pair[0]);
      pair=await load(vp.width,vp.height,'chronology','en'); record(vp.width,vp.height,'chronology','en',pair[1],pair[0]);
    }}
    for(const item of localizedHomeCases){{
      const pair=await load(item.width,item.height,'home',item.locale);
      record(item.width,item.height,'home',item.locale,pair[1],pair[0]);
    }}
  }}catch(error){{failures.push(String(error&&error.stack||error));}}
  const result={{status:failures.length?'fail':'pass',viewports,localized_home_cases:localizedHomeCases,cases,route_viewport_checks:cases.length,overflow_failures:failures.filter(x=>x.includes('overflow')).length,blank_route_failures:failures.filter(x=>x.includes('blank')||x.includes('missing .hero')||x.includes('missing chronology')).length,javascript_failures:failures.some(x=>x.includes('Error:'))?1:0,failures}};
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
                        "--virtual-time-budget=28000",
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
                    timeout=55,
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
