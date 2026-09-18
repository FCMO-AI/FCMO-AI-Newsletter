#!/usr/bin/env python3
"""Fail closed when autonomous Newsletter surfaces drift from the public corpus.

This oracle covers failure modes that generic overflow checks miss: the lead status
rail intersecting the headline, Signal Field falling back to all-time historical
importance, Chronology hiding newer publication activity, and Research Library
presenting an older sort as if it were current.
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

BROWSERS=("google-chrome","google-chrome-stable","chromium","chromium-browser","msedge","microsoft-edge")

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,_format,*_args):
        pass

@contextmanager
def serve(root: Path):
    handler=lambda *a,**kw: QuietHandler(*a,directory=str(root),**kw)
    server=ThreadingHTTPServer(("127.0.0.1",0),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try: yield f"http://127.0.0.1:{server.server_port}/"
    finally: server.shutdown();server.server_close();thread.join(timeout=3)

def browser_path()->str:
    override=os.environ.get("FCMO_BROWSER")
    if override:
        return shutil.which(override) or override
    for name in BROWSERS:
        found=shutil.which(name)
        if found:return found
    raise RuntimeError("no supported Chromium-family browser found")

def harness()->str:
    return r'''<!doctype html><meta charset="utf-8"><iframe id="f" style="border:0;width:768px;height:1100px"></iframe><pre id="r">pending</pre><script>
const f=document.getElementById('f'),fail=[];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const overlap=(a,b)=>a.left<b.right-.5&&a.right>b.left+.5&&a.top<b.bottom-.5&&a.bottom>b.top+.5;
const load=route=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('timeout '+route)),8000);f.onload=()=>{clearTimeout(timer);setTimeout(resolve,380)};f.src='index.html?surface-oracle='+Date.now()+'#/'+route});
function data(doc){return JSON.parse(doc.getElementById('fcmo-data').textContent)}
function latestEdition(D){return [...(D.publication_memory||[])].filter(x=>x.published&&x.date).sort((a,b)=>String(b.date).localeCompare(String(a.date)))[0]?.date||''}
function activity(r){return Math.max(Date.parse(r.last_verified_at||'')||0,Date.parse(r.event_at||'')||0)}
(async()=>{try{
 await load('home');let d=f.contentDocument,w=f.contentWindow,D=data(d),latest=latestEdition(D);
 let editionStamp=d.querySelector('.issue-stamp strong');
 if(!editionStamp)fail.push('home missing published-edition stamp');else if(editionStamp.textContent.trim()!==latest)fail.push(`home published-edition stamp ${editionStamp.textContent.trim()||'missing'} != ${latest}`);
 let rail=d.querySelector('.lead-rail'),title=d.querySelector('.lead-body h2');
 if(!rail||!title)fail.push('home missing lead rail/title');else if(overlap(rail.getBoundingClientRect(),title.getBoundingClientRect()))fail.push('lead status rail intersects headline at 768px');
 let plot=d.querySelector('#plot');if(!plot)fail.push('missing Signal Field');else{
   if(plot.dataset.fcmoFreshness!=='recent-public')fail.push('Signal Field lacks recent-public freshness contract');
   if(plot.dataset.fcmoLatestPublication!==latest)fail.push(`Signal Field edition ${plot.dataset.fcmoLatestPublication||'missing'} != ${latest}`);
   const nodes=[...plot.querySelectorAll('.signal-node')];if(nodes.length!==10)fail.push(`Signal Field expected 10 nodes, found ${nodes.length}`);
   const anchor=Date.parse(latest+'T23:59:59Z');const recent=nodes.filter(n=>anchor-Date.parse((n.dataset.fcmoActivity||'1970-01-01')+'T00:00:00Z')<=21*86400000);
   if(recent.length<6)fail.push(`Signal Field current window too stale: ${recent.length}/10 within 21 days`);
 }
 await load('chronology');d=f.contentDocument;D=data(d);latest=latestEdition(D);
 let clock=d.querySelector('[data-fcmo-publication-activity]');if(!clock)fail.push('Chronology missing publication activity clock');else if(clock.dataset.fcmoPublicationActivity!==latest)fail.push(`Chronology latest activity ${clock.dataset.fcmoPublicationActivity} != ${latest}`);
 if(!d.querySelector('[data-fcmo-origin-chronology="true"]'))fail.push('Chronology lost original-development clock');
 await load('research');d=f.contentDocument;D=data(d);latest=latestEdition(D);await sleep(80);
 let list=d.querySelector('#rlist'),sort=d.querySelector('#rsort'),banner=d.querySelector('.fcmo-library-clock');
 if(!list||list.dataset.fcmoLibrarySort!=='latest-verified')fail.push('Research Library is not on latest-verified contract');
 if(!sort||sort.value!=='newest')fail.push('Research Library default sort is not newest/latest verified');
 if(!banner||banner.dataset.fcmoLibraryEdition!==latest)fail.push('Research Library current-edition marker is stale');
 const expected=[...(D.records||[])].sort((a,b)=>activity(b)-activity(a)||Number(b.importance||0)-Number(a.importance||0)||String(a.id).localeCompare(String(b.id)))[0]?.id;
 const first=(d.querySelector('#rlist a[href*="FCMO-"]')?.getAttribute('href')||'').match(/FCMO-[A-Z0-9]+/)?.[0];
 if(expected&&first!==expected)fail.push(`Research Library first item ${first||'missing'} != latest activity ${expected}`);
 const result={status:fail.length?'fail':'pass',latest_publication:latest,failures:fail};document.getElementById('r').textContent=JSON.stringify(result)
}catch(e){document.getElementById('r').textContent=JSON.stringify({status:'fail',failures:[String(e&&e.stack||e)]})}})();
</script>'''

def main()->int:
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("site",nargs="?",type=Path,default=Path("publish"));args=ap.parse_args();root=args.site.resolve()
    if not (root/"index.html").is_file():raise SystemExit(f"surface freshness refused: missing {root/'index.html'}")
    h=root/"__fcmo_surface_oracle__.html";h.write_text(harness(),encoding="utf-8")
    try:
        with serve(root) as base:
            profile=Path(tempfile.mkdtemp(prefix="fcmo-surface-oracle-"))
            try:
                cp=subprocess.run([browser_path(),"--headless=new","--no-sandbox","--disable-gpu","--disable-dev-shm-usage","--disable-background-networking","--hide-scrollbars","--virtual-time-budget=18000","--window-size=1400,1200",f"--user-data-dir={profile}","--dump-dom",base+h.name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace",timeout=40)
            finally: shutil.rmtree(profile,ignore_errors=True)
        if cp.returncode:raise AssertionError(f"browser exited {cp.returncode}: {cp.stderr[-1800:]}")
        m=re.search(r'<pre id="r">(.*?)</pre>',cp.stdout,re.S)
        if not m:raise AssertionError("surface oracle returned no result")
        result=json.loads(html.unescape(m.group(1)))
        if result.get("status")!="pass":raise AssertionError("surface freshness failures:\n- "+"\n- ".join(result.get("failures",[])))
        print(f"surface freshness OK: publication {result['latest_publication']}; geometry + Signal Field + Chronology + Library green")
        return 0
    finally:
        h.unlink(missing_ok=True)

if __name__=="__main__":raise SystemExit(main())
