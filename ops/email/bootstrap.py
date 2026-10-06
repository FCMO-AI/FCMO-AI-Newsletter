#!/usr/bin/env python3
"""Configure SES transport and governed lists. No newsletter is sent here."""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.email_listmonk import LOCALES, MailConfig, ListmonkClient,DeliveryError,TEMPLATE_NAME,TEMPLATE_BODY


def read_env(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        name,value = line.split('=',1)
        if not name.replace('_','').isalnum(): raise ValueError('invalid environment key')
        parsed = shlex.split(value)
        values[name] = parsed[0] if len(parsed)==1 else value
    return values


def configure(client, env, *, offline=False):
    cfg = client.config
    if not offline and env.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true':
        raise ValueError('postal address, rights contact, processor agreements and transfer safeguards must be ready')
    settings = client.request('GET','settings')
    templates = client.request('GET','templates')
    if not any(v['name']==TEMPLATE_NAME for v in templates):
        client.request('POST','templates',{'name':TEMPLATE_NAME,'type':'campaign','body':TEMPLATE_BODY})
    client.campaign_template()
    settings.update({
        'app.site_name':'FCMO AI Diario', 'app.root_url':cfg.public_url,
        'app.from_email':cfg.from_email, 'app.lang':'es',
        'app.enable_public_subscription_page':True, 'app.enable_public_archive':False,
        'app.show_optin_page':True, 'app.send_optin_confirmation':True,
        'privacy.individual_tracking':False, 'privacy.disable_tracking':True,
        'privacy.unsubscribe_header':True, 'privacy.allow_blocklist':True,
        'privacy.allow_export':True, 'privacy.allow_wipe':True,
        'privacy.allow_preferences':True, 'privacy.record_optin_ip':False,
        'privacy.exportable':['profile','subscriptions'],
        'app.concurrency':2, 'app.message_rate':int(env.get('FCMO_EMAIL_RATE','2')),
        'app.max_send_errors':10,
        'bounce.enabled':True, 'bounce.webhooks_enabled':True, 'bounce.ses_enabled':True,
        'bounce.actions':{'soft':{'count':3,'action':'blocklist'}, 'hard':{'count':1,'action':'blocklist'}, 'complaint':{'count':1,'action':'blocklist'}},
        'smtp':[{'name':'ses', 'enabled':True,'host':env['SES_SMTP_HOST'],'port':int(env.get('SES_SMTP_PORT','587')),
                 'auth_protocol':'none' if offline else 'login','username':env.get('SES_SMTP_USERNAME',''),
                 'password':env.get('SES_SMTP_PASSWORD',''), 'tls_type':'none' if offline else 'STARTTLS',
                 'tls_skip_verify':False,'max_conns':2,'max_msg_retries':0,'msg_retry_delay':'1s',
                 'idle_timeout':'15s','wait_timeout':'10s','email_headers':[]}],
    })
    lists = client.request('GET','lists?per_page=all')['results']
    for locale in LOCALES:
        name = 'diario-'+locale
        matches = [v for v in lists if v['name']==name]
        if not matches:
            client.request('POST','lists',{'name':name,'type':'public','optin':'double','tags':['fcmo-diario',locale],'description':'FCMO AI Diario · '+locale})
        elif len(matches)!=1 or matches[0]['type']!='public' or matches[0]['optin']!='double':
            raise ValueError('existing list requires manual reconciliation')
    running = client.request('GET','campaigns?status=running&per_page=all')['results']
    if running: raise ValueError('pause running campaigns before changing transport')
    client.request('PUT','settings',settings)
    # Pinned Listmonk starts its settings-triggered reload after 500 ms.
    # Wait past that boundary, then observe stable reads across the restart.
    time.sleep(1)
    stable=0;deadline=time.monotonic()+30
    while stable<5 and time.monotonic()<deadline:
        try:
            observed=client.request('GET','settings');client.lists();stable+=1
        except DeliveryError:stable=0
        time.sleep(.4)
    if stable<5:raise ValueError('Listmonk did not stabilize after settings reload')
    for key in ('privacy.disable_tracking','privacy.unsubscribe_header','bounce.ses_enabled','app.send_optin_confirmation'):
        if observed.get(key) is not True: raise ValueError('settings observation failed: '+key)
    return client.lists()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path,default=Path('/etc/fcmo/secrets/email.env'))
    args = parser.parse_args()
    env = dict(os.environ, **read_env(args.env_file))
    lists = configure(ListmonkClient(MailConfig.from_env(env)),env)
    print('Email configured and observed; double-opt-in locale lists: '+', '.join(lists))


if __name__=='__main__': main()
