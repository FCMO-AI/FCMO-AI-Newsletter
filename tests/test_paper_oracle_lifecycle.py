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
                {'path': '', 'kind': 'landing', 'locale': 'en'},
                {'path': 'es/', 'kind': 'landing', 'locale': 'es-419'},
                {'path': 'zh/', 'kind': 'landing', 'locale': 'zh-Hans'},
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
                        if row['kind'] in {'story', 'landing'}]
            expected += [('/' + row['path'], width) for row in rows for width in (1440, 390)
                         if row['locale'] == 'zh-Hans']
            actual = [tuple(json.loads(line)) for line in visits.read_text().splitlines()]
            self.assertEqual(Counter(actual), Counter(expected))
            self.assertIn('Diseño:', result.stdout)

    # Per-page state mock: each page keeps its own viewport and url and yields to the event loop between calls,
    # so a pool that shared state between routes would corrupt the visit set.
    POOL_MODULE = '''const fs = require('node:fs');
const tick = () => new Promise(r => setTimeout(r, 2));
exports.chromium = {launch: async () => ({newPage: async () => {
  let width, path;
  return {
    setViewportSize: async vp => {await tick(); width = vp.width},
    goto: async url => {await tick(); path = new URL(url).pathname; fs.appendFileSync(process.env.VISITS, JSON.stringify([path, width])+'\\n')},
    evaluate: async fn => {
      await tick();
      const source = String(fn);
      if (source.includes('document.fonts')) return true;
      if (source.includes("querySelectorAll('h1 a")) return [];
      return {height:50, lines: path === process.env.BAD_PATH ? 9 : 1, dekTop:200};
    }
  };
}, close: async () => {}})};
'''

    def _run_pool(self, concurrency, bad_path=''):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'browser.cjs').write_text(self.POOL_MODULE)
            rows = [{'path': f'story-{i}/', 'kind': 'story', 'locale': 'en'} for i in range(12)]
            rows += [{'path': f'zh/story-{i}/', 'kind': 'story', 'locale': 'zh-Hans'} for i in range(5)]
            rows += [{'path': '', 'kind': 'landing', 'locale': 'en'},
                     {'path': 'es/', 'kind': 'landing', 'locale': 'es-419'},
                     {'path': 'zh/', 'kind': 'landing', 'locale': 'zh-Hans'}]
            (root / 'routes.json').write_text(json.dumps(rows))
            result = subprocess.run(['node', '--input-type=commonjs', '-e', oracle.LAYOUT_BUDGETS,
                                     'http://fixture.invalid/', str(root / 'routes.json')],
                                    env={**os.environ, 'PLAYWRIGHT_MODULE': str(root / 'browser.cjs'),
                                         'VISITS': str(root / 'visits.jsonl'), 'BAD_PATH': bad_path,
                                         'LAYOUT_BUDGETS_CONCURRENCY': str(concurrency)},
                                    capture_output=True, text=True, timeout=30)
            visits = root / 'visits.jsonl'
            actual = [tuple(json.loads(line)) for line in visits.read_text().splitlines()] if visits.exists() else []
            return result, Counter(actual)

    def test_concurrency_does_not_change_the_visit_set(self):
        serial, serial_visits = self._run_pool(1)
        pooled, pooled_visits = self._run_pool(4)
        self.assertEqual(serial.returncode, 0, serial.stderr)
        self.assertEqual(pooled.returncode, 0, pooled.stderr)
        # 12 stories + 5 zh stories + 3 landing at two widths, plus the zh set (5 stories, zh/) at two widths again.
        self.assertEqual(sum(pooled_visits.values()), (12 + 5 + 3 + 5 + 1) * 2)
        self.assertEqual(pooled_visits, serial_visits)
        self.assertIn('stories=17', pooled.stdout)

    def test_violation_on_any_route_fails_under_concurrency(self):
        for bad in ('story-7/', 'zh/story-3/', 'es/'):
            with self.subTest(bad=bad):
                result, visits = self._run_pool(4, bad_path='/' + bad)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(bad + ' desktop', result.stderr)
                self.assertNotIn('PASS', result.stdout)
                self.assertEqual(sum(visits.values()), (12 + 5 + 3 + 5 + 1) * 2)

    CRASH_MODULE = '''const fs = require('node:fs');
const tick = () => new Promise(r => setTimeout(r, 2));
let crashedOnce = false;
exports.chromium = {launch: async () => ({newPage: async () => {
  let width, path, dead = false;
  const guard = () => {if (dead) throw new Error('Target crashed')};
  return {
    close: async () => {},
    setViewportSize: async vp => {guard(); await tick(); width = vp.width},
    goto: async url => {
      guard(); await tick(); path = new URL(url).pathname;
      if (path === '/story-4/' && (process.env.ALWAYS === '1' || !crashedOnce)) {crashedOnce = true; dead = true; throw new Error('Page crashed')}
      fs.appendFileSync(process.env.VISITS, JSON.stringify([path, width])+'\\n');
    },
    evaluate: async fn => {
      guard(); await tick();
      const source = String(fn);
      if (source.includes('document.fonts')) return true;
      if (source.includes("querySelectorAll('h1 a")) return [];
      return {height:50, lines:1, dekTop:200};
    }
  };
}, close: async () => {}})};
'''

    def _run_crashing(self, always):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'browser.cjs').write_text(self.CRASH_MODULE)
            rows = [{'path': f'story-{i}/', 'kind': 'story', 'locale': 'en'} for i in range(10)]
            rows += [{'path': 'zh/story/', 'kind': 'story', 'locale': 'zh-Hans'}]
            rows += [{'path': p, 'kind': 'landing', 'locale': l} for p, l in (('', 'en'), ('es/', 'es-419'), ('zh/', 'zh-Hans'))]
            (root / 'routes.json').write_text(json.dumps(rows))
            result = subprocess.run(['node', '--input-type=commonjs', '-e', oracle.LAYOUT_BUDGETS,
                                     'http://fixture.invalid/', str(root / 'routes.json')],
                                    env={**os.environ, 'PLAYWRIGHT_MODULE': str(root / 'browser.cjs'),
                                         'VISITS': str(root / 'v.jsonl'), 'ALWAYS': '1' if always else '0',
                                         'LAYOUT_BUDGETS_CONCURRENCY': '3'},
                                    capture_output=True, text=True, timeout=30)
            visits = root / 'v.jsonl'
            return result, Counter(tuple(json.loads(l)) for l in visits.read_text().splitlines())

    def test_crashed_page_is_replaced_and_its_route_measured_again(self):
        result, visits = self._run_crashing(always=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(visits[('/story-4/', 1440)], 1)
        self.assertEqual(visits[('/story-4/', 390)], 1)
        self.assertEqual(sum(visits.values()), (11 + 3 + 2) * 2)  # 11 stories, 3 landing, 2 zh pages, two widths each

    def test_route_that_keeps_crashing_still_fails_the_run(self):
        result, _ = self._run_crashing(always=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('story-4/', result.stderr)

    def test_violations_are_reported_in_route_order_under_concurrency(self):
        # Every story is bad: the order of the reported lines must not depend on which page finished first.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'browser.cjs').write_text(self.POOL_MODULE.replace("path === process.env.BAD_PATH", "path.startsWith('/story-')"))
            rows = [{'path': f'story-{i}/', 'kind': 'story', 'locale': 'en'} for i in range(10)]
            rows += [{'path': p, 'kind': 'landing', 'locale': l} for p, l in (('', 'en'), ('es/', 'es-419'), ('zh/', 'zh-Hans'))]
            rows += [{'path': 'zh/a/', 'kind': 'story', 'locale': 'zh-Hans'}]
            (root / 'routes.json').write_text(json.dumps(rows))
            outputs = []
            for _ in range(3):
                result = subprocess.run(['node', '--input-type=commonjs', '-e', oracle.LAYOUT_BUDGETS,
                                         'http://fixture.invalid/', str(root / 'routes.json')],
                                        env={**os.environ, 'PLAYWRIGHT_MODULE': str(root / 'browser.cjs'),
                                             'VISITS': str(root / 'v.jsonl'), 'LAYOUT_BUDGETS_CONCURRENCY': '4'},
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 1)
                outputs.append(result.stderr)
            paths = [line.split()[0] for line in outputs[0].splitlines()]
            self.assertEqual(paths, [f'story-{i}/' for i in range(10)])
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])

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
