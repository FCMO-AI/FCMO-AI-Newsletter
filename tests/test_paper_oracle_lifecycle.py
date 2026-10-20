import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from collections import Counter
from unittest.mock import patch

from tests.oraculos import verificar_paper as oracle
from tools.gates import run_all
from tools.gates.common import GateResult


class PaperOracleLifecycleTests(unittest.TestCase):
    def test_layout_keeps_every_route_and_both_viewports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / 'browser.cjs'
            visits = root / 'visits.jsonl'
            module.write_text('''const fs = require('node:fs');
let width;
const page = {
  setViewportSize: async vp => {width = vp.width},
  goto: async url => fs.appendFileSync(process.env.VISITS, JSON.stringify([new URL(url).pathname, width])+'\\n'),
  evaluate: async fn => {
    const source = String(fn);
    if (source.includes('document.fonts')) return true;
    if (source.includes("querySelectorAll('h1 a")) return [];
    return {height:50, lines:1, dekTop:200};
  }
};
exports.chromium = {launch: async () => ({newPage:async () => page, close:async () => {}})};
''')
            rows = [
                {'path': 'story/', 'kind': 'story', 'locale': 'en'},
                {'path': 'zh/story/', 'kind': 'story', 'locale': 'zh-Hans'},
                {'path': '', 'kind': 'front', 'locale': 'en'},
                {'path': 'es/', 'kind': 'front', 'locale': 'es-419'},
                {'path': 'zh/', 'kind': 'front', 'locale': 'zh-Hans'},
                {'path': 'zh/archive/', 'kind': 'archive', 'locale': 'zh-Hans'},
            ]
            routes = root / 'routes.json'
            routes.write_text(json.dumps(rows))
            result = subprocess.run(['node', '--input-type=commonjs', '-e', oracle.LAYOUT_BUDGETS,
                                     'http://fixture.invalid/', str(routes)],
                                    env={**os.environ, 'PLAYWRIGHT_MODULE': str(module), 'VISITS': str(visits)},
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = [('/' + row['path'], width) for row in rows for width in (1440, 390)
                        if row['kind'] in {'story', 'front'}]
            expected += [('/' + row['path'], width) for row in rows for width in (1440, 390)
                         if row['locale'] == 'zh-Hans']
            actual = [tuple(json.loads(line)) for line in visits.read_text().splitlines()]
            self.assertEqual(Counter(actual), Counter(expected))
            self.assertIn('Diseño:', result.stdout)

    def test_browser_closes_when_layout_setup_throws(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / 'browser.cjs'
            closed = root / 'closed'
            module.write_text('''const fs = require('node:fs');
exports.chromium = {launch: async () => ({
  newPage: async () => {throw new Error('fixture layout setup failure')},
  close: async () => {fs.writeFileSync(process.env.CLOSE_MARKER, 'closed')}
})};
''')
            routes = root / 'routes.json'
            routes.write_text(json.dumps([]))
            result = subprocess.run(['node', '--input-type=commonjs', '-e', oracle.LAYOUT_BUDGETS,
                                     'http://fixture.invalid/', str(routes)],
                                    env={**os.environ, 'PLAYWRIGHT_MODULE': str(module),
                                         'CLOSE_MARKER': str(closed)},
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn('fixture layout setup failure', result.stderr)
            self.assertTrue(closed.exists(), 'layout exception leaked the browser')

    def test_gate_announces_progress_before_starting_expensive_check(self):
        output = io.StringIO()
        def gate(root):
            self.assertIn('1/1', output.getvalue())
            return GateResult('FIXTURE', 1)
        with tempfile.TemporaryDirectory() as temporary, patch.object(run_all, 'GATES', (gate,)):
            with contextlib.redirect_stdout(output):
                self.assertEqual(run_all.main([temporary]), 0)
        self.assertIn('GATES PASS (1/1)', output.getvalue())
