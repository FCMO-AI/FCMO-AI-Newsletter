#!/usr/bin/env python3
"""Exercise real encrypted backup against the integration's private native DB.

Only the container execution boundary and maintenance API are substituted.
The dump, SQLite snapshot, archive, age encryption and decryption are real.
"""
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from unittest.mock import patch

from ops.email import maintenance


def prove_backup(pg_bin, pgport, journal, out):
    calls = []
    class FakeProvider:
        def __init__(self, config): pass
        def request(self, method, path):
            calls.append((method, path)); return True

    real_run = subprocess.run
    with tempfile.TemporaryDirectory(prefix='fcmo-email-backup-proof-') as folder:
        temp = Path(folder)
        state = temp/'.local/share/fcmo-email'; state.mkdir(parents=True)
        shutil.copyfile(journal, state/'state.sqlite')
        with sqlite3.connect(state/'state.sqlite') as db:
            before = db.execute('SELECT name,phase,campaign_id,digest FROM dispatch ORDER BY name').fetchall()
            assert len(before) == 3
            db.execute("INSERT INTO consent VALUES ('expired','expired','en',0,'offline',0)")
        keys = real_run(['age-keygen'], capture_output=True, check=True)
        keyfile = temp/'key'; keyfile.write_bytes(keys.stdout); keyfile.chmod(0o600)
        recipient = real_run(['age-keygen','-y',str(keyfile)], capture_output=True, check=True).stdout.decode().strip()
        env = dict(LISTMONK_URL='http://127.0.0.1:9000', LISTMONK_API_USER='offline',
                   LISTMONK_API_KEY='offline', FCMO_EMAIL_PUBLIC_URL='https://mail.example.org',
                   FCMO_EMAIL_FROM='offline@example.org', FCMO_EMAIL_POSTAL_ADDRESS='Offline preview',
                   FCMO_EMAIL_CONSENT_KEY='x'*32, FCMO_EMAIL_BACKUP_RECIPIENT=recipient)
        def native_dump(argv, **kwargs):
            if argv[:3] == ['podman','exec','fcmo-email-db']:
                argv = [str(pg_bin/'pg_dump'),'-h','127.0.0.1','-p',str(pgport),'-U','listmonk','-d','listmonk']
            return real_run(argv, **kwargs)
        with patch.object(Path,'home',return_value=temp), patch.dict(os.environ,env), \
             patch.object(maintenance,'ListmonkClient',FakeProvider), \
             patch.object(maintenance.subprocess,'run',native_dump):
            maintenance.main()
        backups = list((state/'backups').glob('*.tar.age')); assert len(backups) == 1
        data = real_run(['age','-d','-i',str(keyfile),str(backups[0])],capture_output=True,check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            assert sorted(archive.getnames()) == ['database.sql','state.sqlite']
            assert b'PostgreSQL database dump' in archive.extractfile('database.sql').read()
            restored = temp/'journal'; restored.write_bytes(archive.extractfile('state.sqlite').read())
        with sqlite3.connect(restored) as db:
            assert db.execute('SELECT name,phase,campaign_id,digest FROM dispatch ORDER BY name').fetchall() == before
            assert db.execute('SELECT COUNT(*) FROM consent WHERE at=0').fetchone()[0] == 0
        assert not list(state.glob('tmp*')) and not list((state/'backups').glob('*.partial'))
        assert len(calls) == 2 and all(m=='DELETE' and 'before_date=' in p for m,p in calls)
        proof = dict(status='PASS',postgres_dump='native PostgreSQL 17',
                     container_boundary='substituted native pg_dump; rootless Podman unavailable',
                     maintenance_provider='fake API',encryption='age real encryption and decryption',
                     journal_preserved=True,expired_consent_purged=True,
                     cleartext_temporary_archive_removed=True,production_data='none')
        (out/'backup-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
        return proof
