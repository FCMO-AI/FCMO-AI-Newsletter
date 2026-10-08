"""Publication prepares a current receipt, then independently checks its tree."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml

from ops import publish
from tools import build_ready_receipt as receipt

ROOT = Path(__file__).resolve().parents[1]


class ReadyReceiptPipelineTests(unittest.TestCase):
    def test_pages_regenerates_before_the_unchanged_integrity_gate(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/pages.yml').read_text())
        steps = workflow['jobs']['build']['steps']
        generator = [i for i, step in enumerate(steps)
                     if step.get('run', '').strip() == 'python3 tools/build_ready_receipt.py']
        self.assertEqual(len(generator), 1, 'Deploy checks a receipt it never regenerates')
        gate = next(i for i, step in enumerate(steps)
                    if step.get('run', '').strip() == 'python3 tools/verify_release.py')
        self.assertLess(generator[0], gate)
        self.assertNotIn('if', steps[generator[0]])
        self.assertNotIn('continue-on-error', steps[generator[0]])

    def test_refresh_receipts_both_rebuild_and_status_before_committing(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/daily-refresh.yml').read_text())
        steps = workflow['jobs']['refresh']['steps']
        generators = [(i, step) for i, step in enumerate(steps)
                      if 'python tools/build_ready_receipt.py' in step.get('run', '')]
        self.assertEqual(len(generators), 1, 'Refresh leaves READY_TO_PUBLISH.md stale')
        index, step = generators[0]
        for mode in ('finalize', 'status'):
            writer = next(i for i, s in enumerate(steps)
                          if f'newsroom_receipt.py {mode} --' in s.get('run', ''))
            self.assertLess(writer, index)
        self.assertEqual(step['if'], "steps.preflight.outputs.path == 'rebuild' || steps.preflight.outputs.path == 'status'")
        self.assertEqual(step['run'].splitlines(), [
            'python tools/build_ready_receipt.py',
            'python tools/build_ready_receipt.py --check',
        ])
        commit = next(i for i, s in enumerate(steps) if 'git add -A --' in s.get('run', ''))
        self.assertLess(index, commit)

    def test_local_check_prepares_a_receipt_before_the_integrity_gate(self):
        observed = []
        def run(command, **kwargs):
            observed.append(command)
            return mock.Mock(returncode=0)
        with mock.patch.object(publish.subprocess, 'run', side_effect=run):
            self.assertEqual(publish.main(['--check', '--out', '/tmp/receipt-test']), 0)
        generator = [i for i, cmd in enumerate(observed) if cmd[1:] == ['tools/build_ready_receipt.py']]
        self.assertEqual(len(generator), 1, 'ops/publish.py --check trusts a stale committed receipt')
        gate = next(i for i, cmd in enumerate(observed) if cmd[1:] == ['tools/verify_release.py'])
        self.assertLess(generator[0], gate)

    def test_frozen_snapshot_prepares_stale_receipt_and_gate_still_rejects_later_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / 'candidate'
            data = candidate / 'data'
            data.mkdir(parents=True)
            stories = root / 'stories.json'
            status = root / 'status.json'
            stories.write_text(json.dumps({'schema': 'fcmo-stories-v2', 'release_id': 'newswire-test',
                                          'generated_at': '2026-10-07T22:00:00Z', 'stories': []}))
            status.write_text(json.dumps({'schema': 'fcmo-newsroom-status-v2',
                                         'edition_date': '2026-10-07', 'edition_state': 'FRESH'}))
            (data / 'stories.v2.json').write_bytes(stories.read_bytes())
            (data / 'newsroom-status.json').write_bytes(status.read_bytes())
            routes = data / 'routes.json'
            routes.write_text('[{"kind":"front","locale":"en"}]')
            rendered = candidate / 'index.html'
            rendered.write_text('before code change')
            output = root / 'READY_TO_PUBLISH.md'
            measure = lambda: receipt.measure_candidate(candidate, stories, status)
            output.write_text(receipt.render_receipt(measure()))
            # Code/merge changes rendered bytes; health/status changes status and lastmod.
            rendered.write_text('after code change')
            routes.write_text('[{"kind":"front","locale":"en","lastmod":"2026-10-08"}]')
            status.write_text(status.read_text().replace('FRESH', 'DELAYED'))
            (data / 'newsroom-status.json').write_bytes(status.read_bytes())

            class FinishedIntegrity(Exception):
                pass

            def step(_root, *args):
                if args == ('tools/build_ready_receipt.py',):
                    receipt.main([])
                elif args == ('tools/verify_release.py',):
                    receipt.main(['--check'])
                else:
                    raise FinishedIntegrity

            with mock.patch.object(receipt, 'RECEIPT_PATH', output), \
                    mock.patch.object(receipt, 'measured_values', side_effect=measure):
                with self.assertRaisesRegex(SystemExit, 'ready receipt check FAILED'):
                    receipt.main(['--check'])
                with mock.patch.object(publish, 'step', side_effect=step):
                    with self.assertRaises(FinishedIntegrity):
                        publish.build_and_check(root, candidate, 'frozen-source-commit')
                accepted = output.read_bytes()
                receipt.main([])
                self.assertEqual(accepted, output.read_bytes(), 'receipt must be deterministic')
                rendered.write_text('changed after receipt generation')
                with self.assertRaisesRegex(SystemExit, 'candidate_sha256'):
                    receipt.main(['--check'])
                self.assertEqual(accepted, output.read_bytes(), '--check must never repair drift')


if __name__ == '__main__':
    unittest.main()
