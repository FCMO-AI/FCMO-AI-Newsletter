import copy
from pathlib import Path
import tempfile
import unittest
from studio.server import issues
from studio.server.storage import Store, Conflict, git
from studio.server.publishing import GitHub, Publisher
from tests.harness.mock_github import MockGitHub
from tests.test_studio_storage import ROOT
from tests.test_studio_publish import MockWorkspace

ISSUE = {'schema': 'fcmo-issue-v1', 'id': '2026-10-04-fixture', 'date': '2026-10-04',
         'title': {'en': 'Today', 'es-419': 'Hoy', 'zh-Hans': '今天'},
         'note': {'en': 'A note', 'es-419': 'Una nota', 'zh-Hans': '编者注'},
         'slots': [{'slot': 'lead', 'ref': 'FCMO-123456789ABC'}]}

class Issues(unittest.TestCase):
    def test_issue_versions_conflicts_and_published_tree(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '_audit') as temporary, MockGitHub() as mock:
            root = Path(temporary); store = Store(root / 'data')
            try:
                created = issues.create(store, 'matias', copy.deepcopy(ISSUE)); value = ISSUE['id']
                self.assertEqual(created['issue'], ISSUE)
                store.checkpoint(value, 'matias', 'First edition')
                edited = copy.deepcopy(ISSUE); edited['note']['en'] = 'A new note'
                self.assertEqual(issues.save(store, value, 'matias', 0, edited)['rev'], 1)
                with self.assertRaises(Conflict): issues.save(store, value, 'matias', 0, ISSUE)
                self.assertEqual(len(store.versions(value)), 1)
                remote = root / 'remote'; remote.mkdir(); git(remote, 'init', '-q', '-b', 'main')
                git(remote, '-c', 'user.name=Codex', '-c', 'user.email=noreply@openai.com', 'commit', '--allow-empty', '-qm', 'Base')
                git(store.data / 'clone', 'remote', 'set-url', 'origin', str(remote))
                github = GitHub({'javier': 'fixture-javier', 'matias': 'fixture-matias'}, mock.url, live_base=mock.url + '/live/')
                workspace = MockWorkspace(store, github, ['python3', '-c', 'raise SystemExit(0)'])
                publisher = Publisher(store, github, workspace, lambda value: [{'ok': True}])
                publisher.request(value, 'matias'); publisher.approve(value, 'javier'); mock.live_id = value
                for _ in range(10): publisher.advance(value)
                self.assertEqual(publisher.get(value)['state'], 'published')
                self.assertEqual(mock.pushes[0]['paths'], ['editorial/issues/' + value + '.json'])
                self.assertEqual(mock.pushes[0]['actor'], 'matias')
                self.assertIn('/cartas/ediciones/' + value + '/', publisher.get(value)['payload']['urls'][0]['url'])
            finally: store.close()
    def test_upstream_text_cannot_be_stored_in_slot(self):
        bad = copy.deepcopy(ISSUE); bad['slots'][0]['text'] = 'Rewritten brief'
        with self.assertRaises(ValueError): issues.validate_issue(bad)
