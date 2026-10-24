import importlib.util
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('studio_notify', ROOT / 'studio' / 'host-ops' / 'notify.py')
notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notify)

# Same column layout as studio/server/storage.py (pieces, reviews, publications).
SCHEMA = '''
CREATE TABLE pieces(slug TEXT PRIMARY KEY, kind TEXT, author TEXT, state TEXT, locale_states_json TEXT, cursor_json TEXT, lock_user TEXT, lock_at REAL, head_rev INTEGER, payload_json TEXT, saved_at REAL, saved_by TEXT);
CREATE TABLE reviews(id TEXT PRIMARY KEY, slug TEXT, rev INTEGER, author TEXT, reviewer TEXT, state TEXT, at TEXT, note TEXT);
CREATE TABLE publications(id TEXT PRIMARY KEY, slug TEXT, kind TEXT, state TEXT, pr_number INTEGER, head_sha TEXT, merge_sha TEXT, pages_run INTEGER, live_checked_at TEXT, error_plain TEXT, payload_json TEXT);
'''

NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
SECRET_BODY = 'CUERPO-SECRETO-NO-DEBE-SALIR-7731'


def iso(delta: timedelta) -> str:
    return (NOW - delta).isoformat(timespec='seconds').replace('+00:00', 'Z')


class Fixture:
    """A temporary Studio data dir and Kyrion mensajeria dir, both owned by the test."""

    def __init__(self, test: unittest.TestCase):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name) / 'studio-data'
        self.data.mkdir()
        self.mensajeria = Path(self.tmp.name) / 'mensajeria'
        (self.mensajeria / 'outbox').mkdir(parents=True)
        (self.mensajeria / 'receipts').mkdir()
        self.ledger = Path(self.tmp.name) / 'state' / 'ledger.json'
        self.db = sqlite3.connect(self.data / 'studio.sqlite')
        self.db.executescript(SCHEMA)

    def piece(self, slug: str, title: str, body: str = SECRET_BODY):
        payload = {'piece': {'title': title, 'status': 'draft'}, 'docs': {'es': {'title': title, 'body': body}}}
        self.db.execute('INSERT INTO pieces(slug,kind,author,state,payload_json) VALUES(?,?,?,?,?)',
                        (slug, 'essay', 'javier', 'in_review', json.dumps(payload)))

    def review(self, ident: str, slug: str, state: str, reviewer: str = 'matias', author: str = 'javier'):
        self.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?)', (ident, slug, 1, author, reviewer, state, iso(timedelta(0)), ''))

    def publication(self, ident: str, slug: str, state: str, data: dict):
        self.db.execute('INSERT INTO publications(id,slug,kind,state,error_plain,payload_json) VALUES(?,?,?,?,?,?)',
                        (ident, slug, 'essay', state, '', json.dumps(data)))

    def commit(self):
        self.db.commit()
        self.db.close()

    def queued(self):
        return sorted((self.mensajeria / 'outbox').glob('*.json'))

    def entries(self):
        return [json.loads(path.read_text()) for path in self.queued()]


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(self)

    def run_once(self, enviar=True):
        return notify.run(self.fx.data, self.fx.mensajeria, self.fx.ledger, enviar, now=NOW)

    def test_review_requested_goes_once_to_the_reviewer_and_is_idempotent(self):
        self.fx.piece('ensayo-uno', 'Ensayo uno')
        self.fx.review('rev-1', 'ensayo-uno', 'requested')
        self.fx.commit()
        first = self.run_once()
        second = self.run_once()
        third = self.run_once()
        self.assertEqual((first['eventos'], first['encolados']), (1, 1))
        self.assertEqual((second['encolados'], second['ya_enviados']), (0, 1))
        self.assertEqual((third['encolados'], third['ya_enviados']), (0, 1))
        entries = self.fx.entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['para'], 'matias')
        self.assertIn('Javier pidió tu revisión de «Ensayo uno»', entries[0]['texto'])

    def test_published_notice_goes_to_author_with_https_links_only(self):
        self.fx.piece('ensayo-dos', 'Ensayo dos')
        self.fx.publication('pub-1', 'ensayo-dos', 'published', {
            'title': 'Ensayo dos', 'author': 'javier',
            'urls': ['https://example.org/en/ensayo-dos', 'http://insecure.example/x', {'url': 'https://example.org/es/ensayo-dos/'}, 'javascript:alert(1)'],
        })
        self.fx.commit()
        self.run_once()
        self.run_once()
        entries = self.fx.entries()
        self.assertEqual([e['para'] for e in entries], ['javier'])
        self.assertIn('https://example.org/en/ensayo-dos', entries[0]['texto'])
        self.assertIn('https://example.org/es/ensayo-dos/', entries[0]['texto'])
        self.assertNotIn('insecure', entries[0]['texto'])
        self.assertNotIn('javascript', entries[0]['texto'])

    def test_stuck_publication_over_two_hours_alerts_matias_once(self):
        self.fx.piece('ensayo-tres', 'Ensayo tres')
        stale = {'title': 'Ensayo tres', 'author': 'javier', 'timeline': [{'state': 'approved', 'at': iso(timedelta(hours=3))}]}
        self.fx.publication('pub-stuck', 'ensayo-tres', 'pushed', stale)
        self.fx.commit()
        self.run_once()
        self.run_once()
        entries = self.fx.entries()
        self.assertEqual([e['para'] for e in entries], ['matias'])
        self.assertIn('más de 2 h', entries[0]['texto'])

    def test_recent_publication_is_not_stuck(self):
        self.fx.piece('ensayo-cuatro', 'Ensayo cuatro')
        fresh = {'title': 'Ensayo cuatro', 'author': 'javier', 'timeline': [{'state': 'approved', 'at': iso(timedelta(minutes=40))}]}
        self.fx.publication('pub-fresh', 'ensayo-cuatro', 'pushed', fresh)
        self.fx.commit()
        report = self.run_once()
        self.assertEqual(report['eventos'], 0)
        self.assertEqual(self.fx.queued(), [])

    def test_failed_or_withdrawn_publications_are_not_stuck(self):
        self.fx.piece('ensayo-cinco', 'Ensayo cinco')
        old = [{'state': 'approved', 'at': iso(timedelta(hours=9))}]
        self.fx.publication('pub-failed', 'ensayo-cinco', 'failed', {'title': 'Ensayo cinco', 'timeline': old})
        self.fx.publication('pub-withdrawn', 'ensayo-cinco', 'withdrawn', {'title': 'Ensayo cinco', 'timeline': old})
        self.fx.commit()
        self.assertEqual(self.run_once()['eventos'], 0)

    def test_uncertain_publication_alerts_matias(self):
        self.fx.piece('ensayo-seis', 'Ensayo seis')
        self.fx.publication('pub-unc', 'ensayo-seis', 'deployed_unverified', {'title': 'Ensayo seis', 'author': 'javier', 'unknown': True})
        self.fx.commit()
        self.run_once()
        entries = self.fx.entries()
        self.assertEqual([e['para'] for e in entries], ['matias'])
        self.assertIn('quedó incierta', entries[0]['texto'])

    def test_dry_run_writes_nothing_and_names_what_it_would_queue(self):
        self.fx.piece('ensayo-siete', 'Ensayo siete')
        self.fx.review('rev-7', 'ensayo-siete', 'requested')
        self.fx.commit()
        report = self.run_once(enviar=False)
        self.assertEqual(report['detalle'][0]['accion'], 'encolaria')
        self.assertEqual(self.fx.queued(), [])
        self.assertFalse(self.fx.ledger.exists())

    def test_body_text_never_leaves_the_database(self):
        self.fx.piece('ensayo-ocho', 'Ensayo ocho')
        self.fx.review('rev-8', 'ensayo-ocho', 'requested')
        self.fx.commit()
        self.run_once()
        for path in self.fx.queued():
            self.assertNotIn(SECRET_BODY, path.read_text())
        self.assertNotIn(SECRET_BODY, self.fx.ledger.read_text())

    def test_title_is_one_plain_bounded_line(self):
        self.fx.piece('ensayo-nueve', 'Línea uno\nLínea dos\t' + 'x' * 300)
        self.fx.review('rev-9', 'ensayo-nueve', 'requested')
        self.fx.commit()
        self.run_once()
        text = self.fx.entries()[0]['texto']
        self.assertNotIn('\n', text)
        self.assertNotIn('\t', text)
        self.assertLess(len(text), 220)

    def test_entry_has_the_mensajeria_shape_and_private_permissions(self):
        self.fx.piece('ensayo-diez', 'Ensayo diez')
        self.fx.review('rev-10', 'ensayo-diez', 'requested')
        self.fx.commit()
        self.run_once()
        path = self.fx.queued()[0]
        entry = json.loads(path.read_text())
        self.assertEqual(entry['de'], 'studio')
        self.assertEqual(entry['canal'], 'telegram')
        self.assertEqual(entry['id'], path.stem)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_existing_outbox_or_receipt_entry_is_not_queued_twice(self):
        self.fx.piece('ensayo-once', 'Ensayo once')
        self.fx.review('rev-11', 'ensayo-once', 'requested')
        self.fx.commit()
        connection = notify.open_readonly(self.fx.data / 'studio.sqlite')
        try:
            item = notify.collect(connection, NOW)[0]
        finally:
            connection.close()
        (self.fx.mensajeria / 'receipts' / f"{item['id']}.json").write_text('{"status":"delivered"}')
        report = self.run_once()
        self.assertEqual(report['encolados'], 0)
        self.assertEqual(self.fx.queued(), [])

    def test_connection_is_read_only(self):
        self.fx.piece('ensayo-doce', 'Ensayo doce')
        self.fx.commit()
        connection = notify.open_readonly(self.fx.data / 'studio.sqlite')
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("INSERT INTO reviews VALUES('x','y',1,'a','b','requested','t','')")
        finally:
            connection.close()

    def test_missing_mensajeria_queue_is_refused_not_created(self):
        self.fx.piece('ensayo-trece', 'Ensayo trece')
        self.fx.review('rev-13', 'ensayo-trece', 'requested')
        self.fx.commit()
        for child in ('outbox', 'receipts'):
            (self.fx.mensajeria / child).rmdir()
        with self.assertRaises(SystemExit):
            self.run_once()
        self.assertFalse((self.fx.mensajeria / 'outbox').exists())

    def test_missing_database_is_a_named_failure(self):
        empty = Path(self.fx.tmp.name) / 'empty'
        empty.mkdir()
        with self.assertRaises(SystemExit) as raised:
            notify.run(empty, self.fx.mensajeria, self.fx.ledger, False, now=NOW)
        self.assertIn('no existe la base de Studio', str(raised.exception))


if __name__ == '__main__':
    unittest.main()
