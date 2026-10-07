"""A rebuilt Story set must refresh its field-level receipt before acknowledgement."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest

import yaml

from tests.test_localization_completeness import build_fixture, english_record, write_json
from tools import newsroom_receipt

ROOT = Path(__file__).resolve().parents[1]


class DailyTranslationReceipt(unittest.TestCase):
    def test_new_story_replaces_stale_receipt_and_reaches_ack_with_truthful_backlog(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/daily-refresh.yml').read_text())
        steps = workflow['jobs']['refresh']['steps']
        matches = [(i, step) for i, step in enumerate(steps)
                   if 'tools/mark_pending_localizations.py' in step.get('run', '')]
        self.assertEqual(len(matches), 1, 'refresh never regenerates translation-status.json')
        index, step = matches[0]
        build = next(i for i, s in enumerate(steps) if 'tools/build_newsroom_surfaces.py' in s.get('run', ''))
        ack = next(i for i, s in enumerate(steps) if 'newsroom_receipt.py finalize' in s.get('run', ''))
        self.assertLess(build, index)
        self.assertLess(index, ack)
        self.assertEqual(step['if'], "steps.preflight.outputs.path == 'rebuild'")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = english_record('FCMO-0C0DE0000001')
            corpus, site = build_fixture(root, [row], {})
            (corpus / 'developments').mkdir()
            (corpus / 'index.html').write_text('Synthetic public corpus')
            write_json(corpus / 'airlock.json', {
                'schema': 'fcmo-newswire-airlock-v2', 'state': 'READY_FOR_PUBLICATION',
                'release_id': 'newswire-test', 'corpus_digest': 'abc', 'record_count': 1,
                'generated_at': '2026-10-07T12:00:00Z',
            })
            release = root / 'release-src'
            write_json(release / 'data/briefs' / (row['id'] + '.json'), {'brief': row})
            write_json(release / 'data/media.json', [{'id': row['id']}])
            receipt = site / 'data/i18n/translation-status.json'
            write_json(receipt, {'schema': 'fcmo-translation-status-v2', 'canonical_story_count': 0})
            args = type('Args', (), {
                'corpus': corpus, 'release_src': release, 'site': site,
                'status': site / 'data/newsroom-status.json',
                'wire_status': root / 'missing-wire.json', 'now': '2026-10-07T12:00:00Z',
            })()
            with self.assertRaisesRegex(ValueError, 'story count mismatch'):
                newsroom_receipt.finalize(args)

            command = shlex.split(step['run'])
            command[0] = sys.executable
            command[1] = str(ROOT / command[1])
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(newsroom_receipt.finalize(args), 0)
            status = json.loads(args.status.read_text())
            self.assertEqual(status['canonical_story_count'], 1)
            self.assertEqual(status['translation_state'], 'DEGRADED_TRANSLATION_BACKLOG')
            self.assertEqual(status['pending_translation_ids'], [row['id']])
            for locale in ('es-419', 'zh-Hans'):
                self.assertEqual(status['translation'][locale]['complete'], 0)
                self.assertEqual(status['translation'][locale]['pending'], 1)


if __name__ == '__main__':
    unittest.main()
