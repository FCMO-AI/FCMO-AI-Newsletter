#!/usr/bin/env python3
"""Restore today's private-content-free send intents, then prepare a new snapshot.

The snapshot MUST be uploaded successfully before dispatch. A previous intent
with no matching provider broadcast blocks recreation, including a lost POST.
"""
import argparse
import io
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date

if __package__ in (None,''): sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.email_listmonk import NoRedirect
from tools.email_providers import LOCALES

LIMIT = 2_000_000

def read_json(response):
    raw = response.read(LIMIT+1)
    if len(raw)>LIMIT: raise ValueError('github_response_too_large')
    return json.loads(raw)


def restore(repository, token, edition_date, namespace='fcmo-diario'):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository) or not token:
        raise ValueError('github_artifact_read_configuration_required')
    root = 'https://api.github.com/repos/'+repository+'/actions/artifacts'
    opener = urllib.request.build_opener(NoRedirect)
    def get(url):
        req = urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'FCMO-Email-Intent'})
        return opener.open(req,timeout=30)
    documents = []
    prefix = ('email-test-intent-' if namespace=='fcmo-diario-test' else 'email-intent-')+edition_date+'-'
    for page in range(1,1001):
        with get(root+f'?per_page=100&page={page}') as response: doc = read_json(response)
        artifacts = doc.get('artifacts')
        if not isinstance(artifacts,list): raise ValueError('invalid_artifact_listing')
        for artifact in artifacts:
            if not artifact['name'].startswith(prefix): continue
            if artifact.get('expired'): raise ValueError('current_day_intent_expired')
            artifact_id = artifact['id']
            if not isinstance(artifact_id,int): raise ValueError('invalid_artifact_id')
            try:
                response = get(root+'/'+str(artifact_id)+'/zip')
            except urllib.error.HTTPError as exc:
                if exc.code!=302: raise
                location = exc.headers.get('Location','')
                parts = urllib.parse.urlsplit(location)
                if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:
                    raise ValueError('invalid_signed_artifact_location')
                # Signed storage URL receives no GitHub authorization header.
                response = opener.open(urllib.request.Request(location),timeout=30)
            with response: raw = response.read(LIMIT+1)
            if len(raw)>LIMIT: raise ValueError('intent_artifact_too_large')
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                files = archive.infolist()
                if len(files)!=1 or files[0].filename!='email-intent.json' or files[0].file_size>LIMIT:
                    raise ValueError('invalid_intent_archive')
                documents.append(json.loads(archive.read(files[0])))
        if len(artifacts)<100: return documents
    raise ValueError('artifact_page_limit')


def prepare(edition_date, previous, out, namespace='fcmo-diario'):
    date.fromisoformat(edition_date)
    if namespace not in ('fcmo-diario','fcmo-diario-test'): raise ValueError('invalid_email_namespace')
    keys = [namespace+':'+edition_date+':'+locale for locale in LOCALES]
    prior = set()
    for document in previous:
        if document.get('keys')!=keys: raise ValueError('invalid_prior_intent')
        prior.update(document['keys'])
    out = Path(out)
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    out.write_text(json.dumps({'schema':'fcmo-email-intent-v1','keys':keys,'previous':sorted(prior)},sort_keys=True)+'\n')
    out.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    try:
        edition_date = json.loads(args.status.read_text())['edition_date']
        namespace = os.environ.get('FCMO_EMAIL_NAMESPACE','fcmo-diario')
        documents = restore(os.environ.get('GITHUB_REPOSITORY',''),os.environ.get('GH_TOKEN',''),edition_date,namespace)
        prepare(edition_date,documents,args.out,namespace)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile):
        print('ERROR email_intent_restore_failed'); return 1
    # Date is the only output; the workflow uses it in the artifact name.
    print(edition_date); return 0

if __name__=='__main__': sys.exit(main())
