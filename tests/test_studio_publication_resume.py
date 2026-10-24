"""A halted publication says why, and its editors can resume it under the contract.

Halt reasons: infra, effect (any editor may resume: the observed state decides, the approved text is kept),
foreign_merge and merge_outside (integrity: only the reviewer resumes, with confirm=true, audited).
Every case drives the real Publisher and Workspace against the offline GitHub double; the HTTP route
is exercised over a loopback server.
"""
from contextlib import redirect_stderr, redirect_stdout
from http.client import HTTPConnection
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from studio.server import publish as publish_cli
from studio.server import publishing as P
from studio.server.http import Application, Server
from studio.server.storage import Store
from tests.test_studio_publish_robust import RobustBase
from tests.test_studio_storage import ROOT


class HaltSites(RobustBase):
    """Each place that sets halted records why."""

    def test_infra_halt_records_reason(self):
        self.approved(); self.publisher.advance(self.slug)
        pub = self.pub(); pub['payload']['infra_retries'] = P.INFRA_RETRIES
        self.publisher._infra(pub, P.Infra('gh lost'))
        data = self.pub()['payload']
        self.assertTrue(data['halted'])
        self.assertEqual(data['halt_reason'], 'infra')

    def test_effect_halt_records_reason(self):
        self.approved(); self.publisher.advance(self.slug)
        pub = self.pub(); data = pub['payload']
        data.update(intent='pushed', intent_at=self.now - 10000, effect_retries=P.INFRA_RETRIES)
        self.publisher._write(pub)
        self.publisher._effect(pub, 'pushed', lambda: False, lambda: None, lambda _: None)
        data = self.pub()['payload']
        self.assertTrue(data['halted'])
        self.assertEqual(data['halt_reason'], 'effect')

    def test_merge_outside_halt_records_reason(self):
        self.mock.merge_files = [{'filename': self.mock.piece_rel + '/piece.json'}, {'filename': 'base.txt'}]
        self.approved(); self.tick_until('merged'); self.publisher.advance(self.slug)
        data = self.pub()['payload']
        self.assertTrue(data['halted'])
        self.assertEqual(data['halt_reason'], 'merge_outside')

    def test_foreign_merge_halt_records_reason(self):
        self.approved(); self.tick_until('pr_open')
        number = self.pub()['payload']['pr_number']
        pr = self.mock.prs[number]
        pr.update(merged=True, merge_commit_sha='a' * 40); pr['head'] = dict(pr['head'], sha='0' * 40)
        self.publisher.advance(self.slug)
        data = self.pub()['payload']
        self.assertTrue(data['halted'])
        self.assertEqual(data['halt_reason'], 'foreign_merge')

    def test_public_status_exposes_halt_fields(self):
        self.approved(); self.tick_until('merged')
        status = self.publisher.public_status(self.slug)
        self.assertFalse(status['halted']); self.assertIsNone(status['halt_reason']); self.assertEqual(status['author'], 'javier')
        pub = self.pub(); pub['payload'].update(halted=True, unknown=True, halt_reason='effect'); self.publisher._write(pub)
        status = self.publisher.public_status(self.slug)
        self.assertTrue(status['halted']); self.assertEqual(status['halt_reason'], 'effect'); self.assertEqual(status['author'], 'javier')


class ResumeRules(RobustBase):
    def halt_directly(self, reason):
        self.approved()
        pub = self.pub(); pub['payload'].update(halted=True, unknown=True, halt_reason=reason); self.publisher._write(pub)

    def audit_actions(self):
        return [row[0] for row in self.store.db.execute('SELECT action FROM audit ORDER BY rowid').fetchall()]

    def test_not_halted_is_refused_with_409(self):
        self.approved()
        with self.assertRaises(P.Refused): self.publisher.resume(self.slug, 'matias')

    def test_infra_resume_continues_to_published_without_new_approval(self):
        self.approved(); self.tick_until('pr_open')
        pub = self.pub(); pub['payload']['infra_retries'] = P.INFRA_RETRIES
        self.publisher._infra(pub, P.Infra('gh down'))
        self.assertEqual(self.pub()['payload']['halt_reason'], 'infra')
        self.publisher.resume(self.slug, 'javier')  # the author may resume an infrastructure halt
        data = self.pub()['payload']
        self.assertFalse(data.get('halted')); self.assertNotIn('halt_reason', data); self.assertNotIn('infra_retries', data)
        self.run_to('published')
        self.assertEqual(self.mock.count('POST', '/reviews'), 1, 'resume must not ask for a second review')
        self.assertEqual(self.audit_actions().count('approve'), 1, 'resume must not ask for a new approval')
        self.assertIn('publication_resumed', self.audit_actions())

    def test_effect_resume_keeps_intent_and_never_repeats_an_observed_write(self):
        self.approved(); self.publisher.advance(self.slug)  # candidate: next step pushes the branch
        self.workspace.push(self.pub())  # the write happened, but its answer was lost
        pub = self.pub(); pub['payload'].update(intent='pushed', intent_at=self.now - 10000, effect_retries=P.INFRA_RETRIES)
        self.publisher._write(pub)
        self.publisher._effect(pub, 'pushed', lambda: False, lambda: None, lambda _: None)
        self.assertEqual(self.pub()['payload']['halt_reason'], 'effect')
        self.assertEqual(self.mock.count('POST', '/git/refs'), 1)
        self.publisher.resume(self.slug, 'matias')
        data = self.pub()['payload']
        self.assertEqual(data.get('intent'), 'pushed', 'the pending intent must survive the resume')
        self.assertNotIn('effect_retries', data)
        self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['state'], 'pushed')
        self.assertEqual(self.mock.count('POST', '/git/refs'), 1, 'the observed push must not be repeated')

    def test_integrity_author_is_forbidden_with_403(self):
        self.halt_directly('merge_outside')
        with self.assertRaises(P.Denied) as caught: self.publisher.resume(self.slug, 'javier', confirm=True)
        self.assertEqual(caught.exception.status, 403)
        self.assertTrue(self.pub()['payload']['halted'])

    def test_integrity_reviewer_without_confirm_is_400_and_stays_halted(self):
        self.halt_directly('merge_outside')
        with self.assertRaises(P.NeedsConfirm) as caught: self.publisher.resume(self.slug, 'matias')
        self.assertEqual(caught.exception.status, 400)
        self.assertTrue(self.pub()['payload']['halted'])

    def test_integrity_reviewer_with_confirm_continues_and_audits(self):
        self.mock.merge_files = [{'filename': self.mock.piece_rel + '/piece.json'}, {'filename': 'base.txt'}]
        self.approved(); self.tick_until('merged'); self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['payload']['halt_reason'], 'merge_outside')
        self.publisher.resume(self.slug, 'matias', confirm=True)
        data = self.pub()['payload']
        self.assertEqual(data['merge_diff'], 'accepted_by_reviewer')
        self.assertFalse(data.get('halted')); self.assertNotIn('halt_reason', data)
        self.assertEqual(self.pub()['state'], 'merged')
        self.run_to('published')
        self.assertEqual(self.audit_actions().count('publication_resume_confirmed'), 1)
        entry = self.store.db.execute("SELECT user, slug, detail_json FROM audit WHERE action='publication_resume_confirmed'").fetchone()
        self.assertEqual(entry[0], 'matias')
        self.assertNotIn('Private essay', entry[2])

    def test_foreign_merge_resume_adopts_the_pr_merge_sha(self):
        self.approved(); self.tick_until('pr_open')
        number = self.pub()['payload']['pr_number']
        pr = self.mock.prs[number]
        pr.update(merged=True, merge_commit_sha='a' * 40); pr['head'] = dict(pr['head'], sha='0' * 40)
        self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['payload']['halt_reason'], 'foreign_merge')
        with self.assertRaises(P.Denied): self.publisher.resume(self.slug, 'javier', confirm=True)
        with self.assertRaises(P.NeedsConfirm): self.publisher.resume(self.slug, 'matias')
        self.publisher.resume(self.slug, 'matias', confirm=True)
        data = self.pub()['payload']
        self.assertEqual(data['merge_sha'], 'a' * 40)
        self.assertEqual(data['merge_diff'], 'accepted_by_reviewer')
        self.assertEqual(self.pub()['state'], 'merged')
        self.assertFalse(data.get('halted'))
        self.assertIn('publication_resume_confirmed', self.audit_actions())


class ResumeHTTP(unittest.TestCase):
    def setUp(self):
        (ROOT / '_audit').mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / '_audit'); self.store = Store(Path(self.tmp.name))
        self.app = Application(self.store, 'https://studio.invalid:8447', 'fixture-session-key-' + 'b' * 32, ROOT)
        self.app.auth.add_user('javier', 'fixture-passphrase-1234'); self.app.auth.add_user('matias', 'fixture-passphrase-5678')
        self.server = Server(('127.0.0.1', 0), self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.halted = self.store.create('javier', 'essay', 'Halted essay', 'en')['slug']
        self.quiet = self.store.create('javier', 'essay', 'Quiet essay', 'en')['slug']
        payload = {'author': 'javier', 'author_name': 'Javier', 'reviewer': 'matias', 'halted': True, 'unknown': True,
                   'halt_reason': 'merge_outside', 'merge_diff': 'outside', 'merge_sha': 'b' * 40, 'timeline': [], 'urls': [],
                   'branch': 'studio/halted-1', 'approved_rev': 0, 'approved_at': '2026-10-24T00:00:00Z', 'piece_id': 'p-halted',
                   'languages': {}, 'provenance': {}, 'distribution': {'email': False}, 'created': 0, 'title': 'Halted essay'}
        self.store.db.execute('INSERT INTO publications(id,slug,kind,state,error_plain,payload_json) VALUES(?,?,?,?,?,?)',
                              ('pub-halted', self.halted, 'essay', 'merged', 'Lo que quedó publicado no coincide con lo aprobado.', json.dumps(payload, ensure_ascii=False)))
        self.store.db.commit()
        self.sessions = {}
        for user, password in (('javier', 'fixture-passphrase-1234'), ('matias', 'fixture-passphrase-5678')):
            status, data, headers = self.request('POST', '/api/login', {'user': user, 'password': password})
            self.assertEqual(status, 200)
            self.sessions[user] = (headers['Set-Cookie'].split(';')[0], data['csrf'])

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.store.close(); self.tmp.cleanup()

    def request(self, method, path, body=None, user=None):
        headers = {'Origin': self.app.origin, 'Content-Type': 'application/json'}
        if user: headers['Cookie'], headers['X-CSRF-Token'] = self.sessions[user]
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        conn.request(method, path, json.dumps(body).encode() if body is not None else None, headers)
        response = conn.getresponse(); status = response.status; received = dict(response.getheaders()); raw = response.read(); conn.close()
        return status, json.loads(raw), received

    def test_route_status_codes_and_success(self):
        route = '/api/pieces/%s/publication/resume'
        status, body, _ = self.request('POST', route % self.halted, {'confirm': True}, 'javier')
        self.assertEqual(status, 403, body)
        status, body, _ = self.request('POST', route % self.halted, {}, 'matias')
        self.assertEqual(status, 400, body)
        self.assertTrue(body.get('error_plain'))
        status, body, _ = self.request('POST', route % self.quiet, {'confirm': True}, 'matias')
        self.assertEqual(status, 409, body)
        self.assertIn('error_plain', body)
        status, body, _ = self.request('POST', route % self.halted, {'confirm': True}, 'matias')
        self.assertEqual(status, 200, body)
        self.assertFalse(body['halted']); self.assertIsNone(body['halt_reason']); self.assertEqual(body['author'], 'javier')
        status, body, _ = self.request('GET', '/api/pieces/%s/publication' % self.halted, None, 'javier')
        self.assertFalse(body['halted'])
        self.assertIn('publication_resume_confirmed', [row[0] for row in self.store.db.execute('SELECT action FROM audit').fetchall()])

    def test_foreign_merge_resume_github_error_is_plain_503_and_stays_halted(self):
        row = self.store.db.execute('SELECT payload_json FROM publications WHERE slug=?', (self.halted,)).fetchone()
        payload = json.loads(row[0]); payload.update(halt_reason='foreign_merge', pr_number=7)
        self.store.db.execute('UPDATE publications SET payload_json=? WHERE slug=?', (json.dumps(payload, ensure_ascii=False), self.halted))
        self.store.db.commit()
        route = '/api/pieces/%s/publication/resume'
        with patch.object(self.app.github, 'pr', side_effect=OSError('network down')):
            status, body, _ = self.request('POST', route % self.halted, {'confirm': True}, 'matias')
        self.assertEqual(status, 503, body)
        self.assertNotEqual(status, 500)
        self.assertIn('GitHub', body.get('error_plain', ''), 'the specific Infra message, not the generic 503')
        row = self.store.db.execute('SELECT payload_json FROM publications WHERE slug=?', (self.halted,)).fetchone()
        self.assertTrue(json.loads(row[0])['halted'])
        self.assertNotIn('publication_resume_confirmed', [r[0] for r in self.store.db.execute('SELECT action FROM audit').fetchall()])


class ReplayAndForeignMergeResume(RobustBase):
    def test_replay_branch_moved_outside_studio_is_refused_not_halted(self):
        self.approved(); self.tick_until('checks_green')
        pub = self.pub(); data = pub['payload']
        data['replay'] = {'old': 'd' * 40, 'new': 'e' * 40}
        self.mock.refs[data['branch']] = 'c' * 40  # neither the old nor the new head: changed outside Studio
        self.publisher._write(pub)
        self.publisher.advance(self.slug)
        pub = self.pub()
        self.assertFalse(pub['payload'].get('halted'), 'a moved public branch is a refusal, not a halt')
        self.assertEqual(pub['state'], 'failed')
        self.assertEqual(pub['error_plain'], 'La versión pública cambió; pide una nueva revisión.')
        self.assertEqual(self.store.piece(self.slug)['state'], 'changes_requested')

    def test_foreign_merge_resume_github_error_is_infra_and_stays_halted(self):
        self.approved(); self.tick_until('pr_open')
        number = self.pub()['payload']['pr_number']
        pr = self.mock.prs[number]
        pr.update(merged=True, merge_commit_sha='a' * 40); pr['head'] = dict(pr['head'], sha='0' * 40)
        self.publisher.advance(self.slug)
        self.assertEqual(self.pub()['payload']['halt_reason'], 'foreign_merge')
        with patch.object(self.github, 'pr', side_effect=OSError('network down')):
            with self.assertRaises(P.Infra) as caught: self.publisher.resume(self.slug, 'matias', confirm=True)
        self.assertEqual(caught.exception.status, 503)
        data = self.pub()['payload']
        self.assertTrue(data['halted']); self.assertEqual(data['halt_reason'], 'foreign_merge')
        self.assertNotIn('publication_resume_confirmed', [r[0] for r in self.store.db.execute('SELECT action FROM audit').fetchall()])


class DryRunFollowsTheFlow(RobustBase):
    """publish.py --dry-run mirrors advance(): confined diff instead of strict base equality, protection by mode."""

    def run_dry(self, mode, protected=True):
        env = {'STUDIO_DATA': str(self.store.data), 'STUDIO_ORIGIN': 'https://studio.invalid:8447',
               'STUDIO_SESSION_KEY': 'fixture-session-key-' + 'c' * 32, 'STUDIO_PROTECTION_MODE': mode}
        app = type('App', (), {})()
        app.publisher = self.publisher; app.github = self.github
        prepare = self.workspace.prepare
        def prepare_then_main_moves(pub):
            # Main moves after the candidate is built and before the check: the race a dry run must survive.
            result = prepare(pub); self.move_main(); return result
        out = io.StringIO()
        with patch.dict(os.environ, env), patch.object(publish_cli, 'Application', lambda *a, **k: app), \
                patch.object(publish_cli, 'Store', lambda *a, **k: self.store), \
                patch.object(self.workspace, 'prepare', prepare_then_main_moves), \
                patch.object(self.github, 'protected', return_value=protected), redirect_stdout(out), redirect_stderr(out):
            code = publish_cli.main(['--slug', self.slug, '--dry-run'])
        return code, out.getvalue()

    def test_dry_run_passes_on_a_moved_main_when_only_the_piece_differs(self):
        self.approved()
        code, out = self.run_dry('studio')
        self.assertEqual(code, 0, out)
        self.assertIn('Ensayo completo', out)

    def test_dry_run_in_github_mode_still_requires_protection(self):
        self.approved()
        code, out = self.run_dry('github', protected=False)
        self.assertEqual(code, 2)
        self.assertIn('protegida', out)


if __name__ == '__main__':
    unittest.main()
