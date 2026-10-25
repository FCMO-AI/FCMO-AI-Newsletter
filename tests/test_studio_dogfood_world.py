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
        (seed / 'ops').mkdir()
        (seed / 'ops' / 'publish.py').write_text('raise SystemExit(0)\n')  # the stub build the fake's merge runs
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
        # A content-red piece carries the marker in its own publication path: the gate searches nothing else.
        if red: (work / 'editorial' / 'pieces' / 'red').mkdir(parents=True)
        sha = self.commit(work, 'branch ' + name, name='editorial/pieces/red/en.json' if red else 'piece.txt',
                          text=text + (' ' + fake_gh.CONTENT_RED if red else ''))
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


class GateSearchesOnlyThePiece(MeasuredWorld):
    def test_marker_outside_the_piece_files_is_not_content_red(self):
        # The published repo is a copy of the whole repo, harness included: a marker there is not the piece's text.
        work = self.root / 'w-harness'
        git('clone', '-q', str(self.origin), str(work))
        (work / 'studio').mkdir()
        sha = self.commit(work, 'harness copy', name='studio/harness.py', text='# ' + fake_gh.CONTENT_RED + '\n')
        git('push', '-q', 'origin', 'HEAD:main', cwd=work)
        self.assertEqual(fake_gh.gate_conclusion(self.root, {'checked': [sha]}, sha), 'success')

    def test_marker_in_the_piece_files_is_content_red(self):
        work = self.root / 'w-piece'
        git('clone', '-q', str(self.origin), str(work))
        (work / 'editorial' / 'pieces' / 'p').mkdir(parents=True)
        sha = self.commit(work, 'piece', name='editorial/pieces/p/en.json', text='{"t": "' + fake_gh.CONTENT_RED + '"}')
        git('push', '-q', 'origin', 'HEAD:main', cwd=work)
        self.assertEqual(fake_gh.gate_conclusion(self.root, {'checked': [sha]}, sha), 'failure')

    def test_the_harness_never_contains_its_own_marker_literal(self):
        for module in (fake_gh, run):
            self.assertNotIn(fake_gh.CONTENT_RED, Path(module.__file__).read_text(), module.__name__)
        self.assertNotIn(fake_gh.CONTENT_RED, Path(__file__).read_text())


class BotAfterMerge(MeasuredWorld):
    def merge(self, world):
        git('clone', '-q', str(self.origin), str(self.root / 'merged'))
        self.branch('studio/p')
        s = {'prs': {'1': self.pr('studio/p', reviews=[{'state': 'APPROVED'}])}}
        fake_gh.world_merge(self.root, s, s['prs']['1'], fake_gh.ref(self.root, 'studio/p'), 100.0, world)
        return s

    def test_later_commit_replaces_the_merge_run_atomically(self):
        s = self.merge(PAGES | {'bot_after_merge': 7})
        self.assertNotEqual(s['later_sha'], s['merge_sha'])
        self.assertEqual(self.main(), s['later_sha'])
        self.assertEqual([(r['head_sha'], r['conclusion']) for r in s['pages']][0], (s['merge_sha'], 'cancelled'))
        fake_gh.tick_pages(self.root, s, 100.0, PAGES)
        self.assertEqual([r['status'] for r in s['pages']], ['completed', 'in_progress'])
        self.assertEqual(s['pages'][1]['head_sha'], s['later_sha'])
        fake_gh.tick_pages(self.root, s, 104.0, PAGES)
        self.assertEqual((s['pages'][1]['conclusion'], (self.root / 'served').exists()), ('success', True))

    def test_without_the_knob_the_merge_run_deploys(self):
        s = self.merge(PAGES)
        self.assertNotIn('later_sha', s)
        fake_gh.tick_pages(self.root, s, 100.0, PAGES)
        self.assertEqual((s['pages'][0]['head_sha'], s['pages'][0]['status']), (s['merge_sha'], 'in_progress'))


class BehindIsRefused(MeasuredWorld):
    WORLD = {'behind': True}

    def test_a_pr_behind_main_is_reported_behind_and_cannot_merge_until_replayed(self):
        git('clone', '-q', str(self.origin), str(self.root / 'merged'))
        self.branch('studio/old')
        s = {'prs': {'1': self.pr('studio/old', reviews=[{'state': 'APPROVED'}])}}
        fake_gh.save_state(self.root, s)
        fake_gh.bot_commit(self.root, 1, now=50.0)
        s = fake_gh.load_state(self.root)
        view = fake_gh.pr_view(self.root, s, s['prs']['1'], 100.0, self.WORLD)
        self.assertEqual((view['mergeable'], view['mergeable_state']), (True, 'behind'))
        with self.assertRaises(fake_gh.GhError) as refused:
            fake_gh.world_merge(self.root, s, s['prs']['1'], fake_gh.ref(self.root, 'studio/old'), 100.0, self.WORLD)
        self.assertEqual(refused.exception.code, 405)
        self.assertEqual(s['behind_refusals'], 1)
        self.assertFalse(s['prs']['1']['merged'])
        # Replayed: a head cut from the moved main merges, and the fake records how often main moved before the merge.
        self.branch('studio/new', 'new')
        s['prs']['2'] = self.pr('studio/new', number=2, reviews=[{'state': 'APPROVED'}])
        fake_gh.world_merge(self.root, s, s['prs']['2'], fake_gh.ref(self.root, 'studio/new'), 101.0, self.WORLD)
        self.assertEqual(s['moves_before_merge'], 1)
        self.assertTrue(s['prs']['2']['merged'])


class BotAfterGate(MeasuredWorld):
    def test_main_moves_inside_the_call_that_turns_the_gate_green_and_only_n_times(self):
        first = self.branch('studio/one', 'one')
        s = {'checked': [first]}
        world = {'gate_s': 0, 'bot_after_gate': 1, 'bot_gate_tick': 900, 'behind': True}
        before = self.main()
        done = fake_gh.world_check(self.root, s, first, 10, world)
        self.assertEqual(done['check_runs'][0]['conclusion'], 'success')
        self.assertNotEqual(self.main(), before)
        self.assertEqual(s['gate_bot_done'], 1)
        s['prs'] = {'1': self.pr('studio/one')}
        # The head the gate approved is now behind main: a merge needs the approved bytes replayed on the new main.
        self.assertEqual(fake_gh.pr_view(self.root, s, s['prs']['1'], 20, world)['mergeable_state'], 'behind')
        moved = self.main()
        fake_gh.world_check(self.root, s, first, 11, world)  # a second read of the same gate moves nothing
        self.assertEqual(self.main(), moved)
        second = self.branch('studio/two', 'two'); s['checked'].append(second)
        fake_gh.world_check(self.root, s, second, 12, world)
        self.assertEqual((self.main(), s['gate_bot_done']), (moved, 1))  # N = 1 move in total
        self.assertEqual(len(s['main_moves']), 1)

    def test_a_new_world_restarts_the_count(self):
        fake_gh.save_state(self.root, {'gate_bot_done': 2})
        fake_gh.write_world(self.root, {'bot_after_gate': 2})
        self.assertNotIn('gate_bot_done', fake_gh.load_state(self.root))


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

    def test_content_red_piece_renders_and_passes_the_fidelity_check_in_every_locale(self):
        # Causes that kept item 6 from running: a 503 preview (the en text lost the «42» of es-419 and zh-Hans: numeric token
        # mismatch in the renderer) and then a red fidelity check (the marker is a brand-like name and must be in every locale).
        from studio.translation import validate_translation
        from tools.paper import essays
        def doc(loc):
            text = run.Journey.body_text(loc, fake_gh.CONTENT_RED)
            return {'schema': 'fcmo-essay-doc-v1', 'locale': loc, 'title': 'T', 'dek': 'D',
                    'blocks': [{'id': 'b-01234567', 'type': 'p', 'content': [{'t': 'text', 'v': text}], 'attrs': {}}], 'footnotes': {}}
        docs = {loc: doc(loc) for loc in run.Journey.BODY}
        for loc, text in ((loc, d['blocks'][0]['content'][0]['v']) for loc, d in docs.items()):
            self.assertIn(fake_gh.CONTENT_RED, text, loc)
        for loc in ('es-419', 'zh-Hans'):
            self.assertEqual(essays._tokens(docs[loc]), essays._tokens(docs['en']), loc)
            validate_translation(docs['en'], docs[loc], loc)  # raises TranslationError when a name or number changed
        # The marker and the clean body differ only by the marker: nothing else moved.
        self.assertEqual(run.Journey.body_text('en').rstrip('.'), run.Journey.body_text('en', fake_gh.CONTENT_RED).split(' and ')[0])

    def test_only_world_counts_setup_plus_world_items(self):
        self.assertEqual(run.Journey.expected_total(False, None, 'world'), run.SETUP_ITEMS + 7)

    def test_a_red_item_is_scored_and_never_aborts(self):
        with tempfile.TemporaryDirectory() as tmp:
            journey = run.Journey(Path(tmp))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(journey.score('first', False))
                self.assertTrue(journey.score('second', True))
            self.assertEqual([s['ok'] for s in journey.scores], [False, True])

    def test_close_reports_every_world_item_in_the_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journey = run.Journey(root)
            with contextlib.redirect_stdout(io.StringIO()):
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
