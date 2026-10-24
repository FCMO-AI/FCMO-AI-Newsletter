"""The measured dogfood world: fake GitHub behaviours (Pages queue, gate, bot, lazy mergeability, refusals)
and the run.py items that score them. Real bare git; every clock is passed in, so nothing waits."""
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from studio.dogfood import fake_gh
from studio.dogfood import run

PAGES = {'pages_run_s': 4.0, 'pages_cancel_in_progress': True}


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class MeasuredWorld(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        seed = self.root / 'seed'
        seed.mkdir()
        git('init', '-q', '-b', 'main', cwd=seed)
        self.commit(seed, 'base')
        git('clone', '-q', '--bare', str(seed), str(self.root / 'origin.git'))
        self.origin = self.root / 'origin.git'
        self.saved_env = os.environ.get('DOGFOOD_ROOT')
        os.environ['DOGFOOD_ROOT'] = str(self.root)

    def tearDown(self):
        if self.saved_env is None: os.environ.pop('DOGFOOD_ROOT', None)
        else: os.environ['DOGFOOD_ROOT'] = self.saved_env
        self.tmp.cleanup()

    def commit(self, work, message, name='x.txt', text='x'):
        (work / name).write_text(text)
        git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'add', '-A', cwd=work)
        git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-m', message, cwd=work)
        return git('rev-parse', 'HEAD', cwd=work)

    def branch(self, name, text='piece', red=False):
        """A review branch cut from the current main, pushed to the bare origin. Returns its head sha."""
        work = self.root / ('w-' + name.replace('/', '-'))
        git('clone', '-q', str(self.origin), str(work))
        git('checkout', '-q', '-b', name, cwd=work)
        sha = self.commit(work, 'branch ' + name, name='piece.txt', text=text + (' ' + fake_gh.CONTENT_RED if red else ''))
        git('push', '-q', 'origin', name, cwd=work)
        return sha

    def main(self):
        return git('--git-dir', str(self.origin), 'rev-parse', 'refs/heads/main')

    def pr(self, branch, number=1, reviews=()):
        return {'number': number, 'head': {'ref': branch, 'sha': fake_gh.ref(self.root, branch)}, 'user': {'login': 'a'},
                'merged': False, 'reviews': list(reviews)}


class PagesQueue(MeasuredWorld):
    def test_pending_run_is_replaced_before_it_starts(self):
        s = {}
        fake_gh.enqueue_run(s, 'a', 0); fake_gh.tick_pages(self.root, s, 0, PAGES | {'pages_cancel_in_progress': False})
        fake_gh.enqueue_run(s, 'b', 1); fake_gh.enqueue_run(s, 'c', 1.5)
        status = {r['head_sha']: (r['status'], r['conclusion']) for r in s['pages']}
        self.assertEqual(status['a'], ('in_progress', None))
        self.assertEqual(status['b'], ('completed', 'cancelled'))
        self.assertEqual(status['c'], ('queued', None))
        fake_gh.tick_pages(self.root, s, 2, PAGES | {'pages_cancel_in_progress': False})
        self.assertEqual([r['status'] for r in s['pages']], ['in_progress', 'completed', 'queued'])
        fake_gh.tick_pages(self.root, s, 4, PAGES | {'pages_cancel_in_progress': False})
        self.assertEqual(s['pages'][0]['conclusion'], 'success')
        self.assertEqual(s['pages'][2]['status'], 'in_progress')

    def test_cancel_in_progress_cancels_the_run_for_the_merge(self):
        s = {}
        fake_gh.enqueue_run(s, 'merge', 0); fake_gh.tick_pages(self.root, s, 0, PAGES)
        fake_gh.enqueue_run(s, 'later', 1); fake_gh.tick_pages(self.root, s, 1, PAGES)
        self.assertEqual((s['pages'][0]['head_sha'], s['pages'][0]['conclusion']), ('merge', 'cancelled'))
        self.assertEqual(s['pages'][1]['status'], 'in_progress')
        fake_gh.tick_pages(self.root, s, 4.9, PAGES)
        self.assertEqual(s['pages'][1]['status'], 'in_progress')
        fake_gh.tick_pages(self.root, s, 5, PAGES)
        self.assertEqual((s['pages'][1]['head_sha'], s['pages'][1]['conclusion']), ('later', 'success'))

    def test_seventy_minute_deploy_compressed_to_seven_seconds(self):
        s = {}
        world = {'pages_run_s': 7.0}
        fake_gh.enqueue_run(s, 'merge', 0); fake_gh.tick_pages(self.root, s, 0, world)
        fake_gh.tick_pages(self.root, s, 6.9, world)
        self.assertEqual(s['pages'][0]['status'], 'in_progress')
        fake_gh.tick_pages(self.root, s, 7, world)
        self.assertEqual(s['pages'][0]['conclusion'], 'success')

    def test_pages_run_without_merge_serves_nothing_new(self):
        s = {}
        fake_gh.enqueue_run(s, 'x', 0); fake_gh.tick_pages(self.root, s, 0, PAGES | {'pages_run_s': 0})
        fake_gh.tick_pages(self.root, s, 0, PAGES | {'pages_run_s': 0})
        self.assertEqual(s['pages'][0]['conclusion'], 'success')
        self.assertFalse((self.root / 'served').exists())


class Gate(MeasuredWorld):
    def test_new_head_cancels_the_gate_still_running_for_an_older_head(self):
        first = self.branch('studio/one', 'one'); second = self.branch('studio/two', 'two')
        s = {}
        fake_gh.world_check(self.root, s, first, 0, {'gate_s': 5})
        self.assertEqual(s['gate'][first]['status'], 'in_progress')
        pending = fake_gh.world_check(self.root, s, second, 1, {'gate_s': 5})
        self.assertEqual(s['gate'][first]['conclusion'], 'cancelled')
        self.assertEqual(pending['check_runs'][0]['status'], 'in_progress')

    def test_content_red_gate_fails_without_a_build(self):
        red = self.branch('studio/red', 'red', red=True)
        s = {}
        fake_gh.world_check(self.root, s, red, 0, {'gate_s': 1})
        done = fake_gh.world_check(self.root, s, red, 2, {'gate_s': 1})
        self.assertEqual(done['check_runs'][0]['conclusion'], 'failure')
        self.assertEqual(s.get('checked', []), [])


class Mergeability(MeasuredWorld):
    def test_lazy_after_main_moves_then_behind_until_replayed(self):
        head = self.branch('studio/p')
        s = {'prs': {'1': self.pr('studio/p')}}
        world = {'lazy_mergeable_s': 2, 'behind': True}
        fake_gh.note_main_moved(s, self.main(), 100)
        unknown = fake_gh.pr_view(self.root, s, s['prs']['1'], 100.5, world)
        self.assertIsNone(unknown['mergeable'])
        self.assertEqual(unknown['mergeable_state'], 'unknown')
        fake_gh.save_state(self.root, s)
        fake_gh.bot_commit(self.root, 1, now=200)  # moves main: the PR head no longer contains it
        s = fake_gh.load_state(self.root)
        behind = fake_gh.pr_view(self.root, s, s['prs']['1'], 205, world)
        self.assertEqual((behind['mergeable'], behind['mergeable_state']), (True, 'behind'))
        self.assertEqual(behind['head']['sha'], head)
        clean = fake_gh.pr_view(self.root, s, s['prs']['1'], 205, {'lazy_mergeable_s': 2})
        self.assertEqual(clean['mergeable_state'], 'clean')

    def test_refused_merge_is_visible_as_unknown_then_clears(self):
        self.branch('studio/m')
        s = {'prs': {'1': self.pr('studio/m', reviews=[{'state': 'APPROVED'}])}}
        world = {'merge_refusals': 1, 'lazy_mergeable_s': 3}
        head = fake_gh.ref(self.root, 'studio/m')
        with self.assertRaises(fake_gh.GhError) as refused:
            fake_gh.world_merge(self.root, s, s['prs']['1'], head, 100, world)
        self.assertEqual(refused.exception.code, 405)
        self.assertEqual((s['refusals_done'], s['refusals_left']), (1, 0))
        self.assertIsNone(fake_gh.pr_view(self.root, s, s['prs']['1'], 101, world)['mergeable'])
        self.assertTrue(fake_gh.pr_view(self.root, s, s['prs']['1'], 104, world)['mergeable'])

    def test_write_world_drops_a_stale_refusal_count(self):
        s = {'refusals_left': 0, 'refusals_done': 1}
        fake_gh.save_state(self.root, s)
        fake_gh.write_world(self.root, {'merge_refusals': 1})
        self.assertNotIn('refusals_left', fake_gh.load_state(self.root))
        self.assertEqual(fake_gh.world_config(self.root), {'merge_refusals': 1})


class Bot(MeasuredWorld):
    def test_bot_moves_main_three_times_with_files_outside_pieces(self):
        before = self.main()
        s = {}
        fake_gh.save_state(self.root, s)
        for number in (1, 2, 3):
            fake_gh.bot_commit(self.root, number, now=float(number))
        self.assertEqual(git('--git-dir', str(self.origin), 'rev-list', '--count', before + '..main'), '3')
        self.assertEqual(git('--git-dir', str(self.origin), 'ls-tree', '--name-only', 'main', 'bot/'), 'bot/tick-1.txt\nbot/tick-2.txt\nbot/tick-3.txt')
        self.assertEqual(len(fake_gh.load_state(self.root)['main_moves']), 3)


class RunScoresWorld(unittest.TestCase):
    def test_expected_total_counts_the_world_items(self):
        self.assertEqual(len(run.WORLD_ITEMS), 7)
        self.assertEqual(len(set(run.WORLD_ITEMS)), 7)
        self.assertEqual(run.Journey.expected_total(False, None), run.BASE_ITEMS + 7)
        self.assertEqual(run.Journey.expected_total(True, None), run.BASE_ITEMS + 7 + 8)
        self.assertEqual(run.Journey.expected_total(True, '1'), run.BASE_ITEMS + 7 + 9)

    def test_close_reports_every_world_item_in_the_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journey = run.Journey(root)
            for name in run.WORLD_ITEMS: journey.score(name, True)
            saved = os.environ.pop('DOGFOOD_CAPTURES', None)
            try:
                with contextlib.redirect_stdout(io.StringIO()): journey.close()
            finally:
                if saved is not None: os.environ['DOGFOOD_CAPTURES'] = saved
            summary = json.loads((root / 'summary.json').read_text())
            self.assertEqual(summary['passed'], 7)
            self.assertFalse(summary['completed'])
            self.assertEqual(summary['total'], run.Journey.expected_total(False, None))


if __name__ == '__main__':
    unittest.main()
