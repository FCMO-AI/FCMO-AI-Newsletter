#!/usr/bin/env python3
"""Stream private audience records into age; only ciphertext reaches disk/artifacts."""
import argparse
from contextlib import suppress
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.email_providers import create_provider
from tools.email_listmonk import DeliveryError


def encrypted_backup(provider, recipient, out):
    if not recipient or not recipient.startswith(('age1','ssh-ed25519 ','ssh-rsa ')):
        raise ValueError('age_public_recipient_required')
    out = Path(out)
    if out.suffix != '.age': raise ValueError('ciphertext_output_must_end_in_age')
    if out.exists(): raise ValueError('backup_already_exists')
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temporary = out.with_name(out.name+'.partial')
    proc = None
    try:
        with temporary.open('xb') as ciphertext:
            temporary.chmod(0o600)
            proc = subprocess.Popen(['age','--recipient',recipient],stdin=subprocess.PIPE,stdout=ciphertext,stderr=subprocess.DEVNULL)
            header = {'schema':'fcmo-email-export-v1','provider':provider.name,
                      'exported_at':datetime.now(timezone.utc).isoformat()}
            raw = json.dumps(header)[:-1]+',"subscribers":['
            proc.stdin.write(raw.encode())
            first = True
            for record in provider.list_subscribers():
                proc.stdin.write(('' if first else ',').encode())
                proc.stdin.write(json.dumps(record,ensure_ascii=False).encode())
                first = False
            proc.stdin.write(b']}'); proc.stdin.close()
            if proc.wait(timeout=60)!=0: raise DeliveryError('backup_encryption_failed')
            ciphertext.flush(); os.fsync(ciphertext.fileno())
        temporary.rename(out)
    except Exception:
        if proc is not None:
            if proc.stdin and not proc.stdin.closed:
                with suppress(BrokenPipeError): proc.stdin.close()
            if proc.poll() is None: proc.kill()
            proc.wait()
        temporary.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    try:
        encrypted_backup(create_provider(os.environ),os.environ.get('FCMO_EMAIL_BACKUP_AGE_RECIPIENT',''),args.out)
    except (OSError,ValueError,DeliveryError,subprocess.SubprocessError):
        print('ERROR encrypted_backup_failed'); return 1
    print('ENCRYPTED backup ready'); return 0

if __name__=='__main__': sys.exit(main())
