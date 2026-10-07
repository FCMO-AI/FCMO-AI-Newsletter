#!/usr/bin/env python3
"""Private encrypted backup; expire unconfirmed subscriptions and rate records."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime,timezone
from urllib.parse import urlencode
from contextlib import closing

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.email_listmonk import ListmonkClient,MailConfig


def main():
    os.umask(0o077)
    state=Path.home()/'.local/share/fcmo-email'
    backups=state/'backups';backups.mkdir(exist_ok=True,mode=0o700)
    client=ListmonkClient(MailConfig.from_env(os.environ))
    cutoff=int(time.time())-30*86400
    before=datetime.fromtimestamp(cutoff,timezone.utc).isoformat().replace('+00:00','Z')
    query=urlencode({'before_date':before})
    client.request('DELETE','maintenance/subscriptions/unconfirmed?'+query)
    client.request('DELETE','maintenance/subscribers/orphan?'+query)
    with closing(sqlite3.connect(state/'state.sqlite')) as db,db:
        db.execute('DELETE FROM consent WHERE at<?',(cutoff,))
    target=backups/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'.tar.age')
    # Snapshot campaign and subscriber state while holding the dispatch lease.
    import fcntl,tarfile
    with (state/'state.lock').open('a') as lock, tempfile.TemporaryDirectory(dir=state) as temp:
        fcntl.flock(lock,fcntl.LOCK_EX)
        p=Path(temp)
        with (p/'database.sql').open('wb') as output:
            subprocess.run(['podman','exec','fcmo-email-db','pg_dump','-U','listmonk','-d','listmonk'],stdout=output,check=True)
        with closing(sqlite3.connect(state/'state.sqlite')) as src, closing(sqlite3.connect(p/'state.sqlite')) as dst:
            src.backup(dst)
        with tarfile.open(p/'backup.tar','w') as archive:
            archive.add(p/'database.sql',arcname='database.sql');archive.add(p/'state.sqlite',arcname='state.sqlite')
        subprocess.run(['age','-r',os.environ['FCMO_EMAIL_BACKUP_RECIPIENT'],'-o',str(target)+'.partial',str(p/'backup.tar')],check=True)
        Path(str(target)+'.partial').replace(target)
    for old in backups.glob('*.tar.age'):
        if old.stat().st_mtime<cutoff: old.unlink()
    print('Encrypted email state backup saved; unconfirmed subscriptions expired.')


if __name__=='__main__':main()
