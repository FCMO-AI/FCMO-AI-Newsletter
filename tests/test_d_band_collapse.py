"""Browser guard: no Bone band may collapse into hairline text columns.

At phone and tablet widths the legend band and Subscriptions once sat side by side and the legend broke into
one- or two-letter columns. There is no horizontal overflow in that failure, so the overflow checks never see
it. This test measures the lines themselves: any text node of 12+ characters inside a Bone band whose widest
line is under 60 px has collapsed. A missing browser is a failure (BROWSER_UNAVAILABLE), never a skip.
"""
from __future__ import annotations

import http.server
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.paper.playwright_module import resolve_playwright_module, missing_playwright_message  # noqa: E402

PROBE = r'''
const {chromium}=require(process.argv[1]);
const [origin,paths,widths]=JSON.parse(process.argv[2]);
(async()=>{
 const b=await chromium.launch({headless:true}); const bad=[];
 for(const w of widths) for(const p of paths){
  const pg=await b.newPage({viewport:{width:w,height:900}});
  await pg.goto(origin+p,{waitUntil:'networkidle'});
  const found=await pg.evaluate(()=>{
   const out=[];
   for(const band of document.querySelectorAll('.d-bone')){
    const it=document.createTreeWalker(band,NodeFilter.SHOW_TEXT);
    for(let n=it.nextNode();n;n=it.nextNode()){
     const t=n.textContent.trim(); if(t.length<12) continue;
     const par=n.parentElement; if(!par||par.closest('[hidden]')||getComputedStyle(par).display==='none') continue;
     const r=document.createRange(); r.selectNodeContents(n);
     const ws=[...r.getClientRects()].filter(x=>x.width>0&&x.height>4).map(x=>x.width);
     if(ws.length&&Math.max(...ws)<60) out.push(t.slice(0,40)+' ('+Math.round(Math.max(...ws))+'px)');
    }
   }
   return out;});
  for(const f of found) bad.push(w+' '+p+' '+f);
  await pg.close();
 }
 await b.close(); console.log(JSON.stringify(bad));
})();
'''


class BandCollapseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = resolve_playwright_module()
        cls.tmp = tempfile.TemporaryDirectory(prefix='d-band-')
        out = Path(cls.tmp.name)
        r = subprocess.run([sys.executable, 'tools/paper/build.py', '--stories', 'site/data/stories.v2.json',
                            '--status', 'site/data/newsroom-status.json', '--editorial', 'editorial',
                            '--out', str(out), '--base', '/'], cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-800:])
        cls.out = out
        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a, **k):
                pass
        handler = partial(Quiet, directory=str(out))
        cls.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.tmp.cleanup()

    def test_bone_bands_never_collapse_to_hairline_columns(self):
        self.assertTrue(self.module, missing_playwright_message())
        routes = json.loads((self.out / 'data/routes.json').read_text())
        paths = ['/', '/es/', '/zh/']
        story = next((r['path'] for r in routes if r['kind'] == 'story' and r['locale'] == 'en' and r.get('index', True)), None)
        if story:
            paths.append('/' + story.lstrip('/'))
        port = self.httpd.server_address[1]
        r = subprocess.run(['node', '-e', PROBE, self.module, json.dumps([f'http://127.0.0.1:{port}', paths, [390, 1000]])],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, 'BROWSER_UNAVAILABLE: ' + r.stderr[-400:])
        self.assertEqual(json.loads(r.stdout.strip().splitlines()[-1]), [])


if __name__ == '__main__':
    unittest.main()
