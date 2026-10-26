"""Offline D browser battery and reproducible, bounded PNG captures.

python3 tests/test_d_visual.py --site /tmp/nl-d-core-fixture-site \
    --base /paper/ --capture design/d-libro/capturas/core

PLAYWRIGHT_MODULE must name an already installed Node Playwright module.
The browser receives local files through request interception; no server or
external network is used. A missing browser is an error, never a passing test.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import resolve_playwright_module, missing_playwright_message

KINDS = ('landing', 'story', 'archive', 'method', 'search', 'topic', 'about', 'corrections', 'status', 'legal', 'subscribe', 'letters')
WIDTHS = (1440, 390, 320)


def capture_jobs(routes):
    """One real route of every available type and locale, at each requested width."""
    result = []
    for locale in ('en', 'es-419', 'zh-Hans'):
        for kind in KINDS:
            row = next((r for r in routes if r['kind'] == kind and r['locale'] == locale and r.get('index', True)), None)
            if row:
                result.extend({'path': row['path'], 'kind': kind, 'locale': locale, 'width': width} for width in WIDTHS)
    return result


PROBE = r'''
const fs=require('node:fs'), path=require('node:path');
const {chromium}=require(process.argv[1]);
const [site,base,dest,jobs]=JSON.parse(process.argv[2]);
(async()=>{
 const browser=await chromium.launch({headless:true});
 const results=[];
 try {
  for(const job of jobs){
   const page=await browser.newPage({viewport:{width:job.width,height:1000},deviceScaleFactor:1});
   const errors=[],missing=[];
   page.on('pageerror',e=>errors.push(String(e)));
   await page.route('**/*',async route=>{
    const u=new URL(route.request().url());
    if(u.origin!=='https://d-preview.invalid'||!u.pathname.startsWith(base)){await route.abort();return;}
    const rel=decodeURIComponent(u.pathname.slice(base.length));
    let file=path.resolve(site,rel);
    if(!file.startsWith(path.resolve(site)+path.sep)&&file!==path.resolve(site)){await route.abort();return;}
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)){missing.push(u.pathname);await route.fulfill({status:404,body:''});return;}
    const type={'.html':'text/html','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.webp':'image/webp','.png':'image/png'}[path.extname(file)]||'application/octet-stream';
    await route.fulfill({body:fs.readFileSync(file),contentType:type});
   });
   await page.goto('https://d-preview.invalid'+base+job.path,{waitUntil:'networkidle'});
   await page.evaluate(()=>document.fonts.ready);
   const metrics=await page.evaluate(()=>({
    width:innerWidth,scroll:document.documentElement.scrollWidth,
    heading:document.querySelector('main h1')?.textContent,
    background:getComputedStyle(document.body).backgroundColor,
    font:getComputedStyle(document.querySelector('main h1')||document.body).fontFamily,
    nav:!!document.querySelector('.d-nav'),footer:!!document.querySelector('.d-footer'),
    touch:[...document.querySelectorAll('.d-nav a,.d-menu summary,.d-footer a,.search-box button,.search-box input')]
      .filter(e=>e.getBoundingClientRect().width&&e.getBoundingClientRect().height)
      .every(e=>e.getBoundingClientRect().height>=44)
   }));
   if(metrics.scroll>job.width+1)errors.push('horizontal overflow: '+metrics.scroll);
   if(!metrics.heading||!metrics.nav||!metrics.footer)errors.push('missing main heading, navigation or footer');
   if(job.width<=760&&!metrics.touch)errors.push('mobile control below 44px');
   if(job.width<1000){
    await page.locator('.d-menu summary').click();
    if(!(await page.locator('.d-menu-links').isVisible()))errors.push('menu did not open');
    await page.locator('.d-menu summary').click();
   }
   if(job.kind==='search'){
    const input=page.locator('[data-search-input]');
    await input.fill('agent');
    await page.locator('[data-search-form]').evaluate(f=>f.requestSubmit());
    await page.waitForTimeout(300);
    if(!(await page.locator('[data-search-results]').innerText()).trim())errors.push('search gave no state');
   }
   // Capture a bounded slice; reduce its height only when PNG bytes exceed 400 KB.
   // Nothing is scaled down: the artifact retains its exact CSS viewport width.
   const file=path.join(dest,job.locale+'-'+job.kind+'-'+job.width+'.png');
   let height=Math.min(await page.evaluate(()=>document.documentElement.scrollHeight),1900);
   let bytes;
   do {
    bytes=await page.screenshot({clip:{x:0,y:0,width:job.width,height},type:'png'});
    if(bytes.length<=400*1024)break;
    height=Math.floor(height*.75);
   }while(height>=400);
   if(bytes.length>400*1024)errors.push('capture exceeds 400 KB');
   fs.writeFileSync(file,bytes);
   if(missing.length)errors.push('missing assets: '+missing.join(', '));
   results.push({...job,metrics,errors,file,bytes:bytes.length});
   await page.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(dest,'battery.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify({cases:results.length,passed:results.filter(r=>!r.errors.length).length,failures:results.filter(r=>r.errors.length)}));
 if(results.some(r=>r.errors.length))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
'''


class CapturePlan(unittest.TestCase):
    def test_matrix_keeps_available_routes_without_inventing_missing_topics(self):
        rows = [{'kind':'landing','locale':'zh-Hans','path':'zh/'}, {'kind':'story','locale':'en','path':'2026/10/26/record/'}]
        jobs = capture_jobs(rows)
        self.assertEqual(len(jobs), 6)
        self.assertEqual({j['width'] for j in jobs}, {1440,390,320})
        self.assertEqual({j['path'] for j in jobs}, {'zh/','2026/10/26/record/'})

    def test_pending_and_private_routes_are_not_reported_as_published(self):
        jobs = capture_jobs([{'kind':'story','locale':'en','path':'pending/','index':False}])
        self.assertEqual(jobs, [])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site',type=Path,required=True)
    parser.add_argument('--base',default='/paper/')
    parser.add_argument('--capture',type=Path,required=True)
    args=parser.parse_args()
    module=resolve_playwright_module()
    if not module:
        print(missing_playwright_message(),file=sys.stderr)
        return 2
    routes=json.loads((args.site/'data/routes.json').read_text())
    args.capture.mkdir(parents=True,exist_ok=True)
    return subprocess.run(['node','-e',PROBE,module,json.dumps([str(args.site.resolve()),args.base,str(args.capture.resolve()),capture_jobs(routes)])],check=False).returncode


if __name__=='__main__':
    raise SystemExit(main())
