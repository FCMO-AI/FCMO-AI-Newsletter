#!/usr/bin/env python3
"""Validate private configuration and emit minimal container environment files."""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from ops.email.bootstrap import read_env
from tools.email_listmonk import MailConfig


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('env',type=Path); p.add_argument('--write-state',type=Path)
    p.add_argument('--phase',choices=('install','active'),default='active')
    a=p.parse_args()
    if a.env.stat().st_mode & 0o077: raise ValueError('email.env must be mode 0600')
    env=read_env(a.env)
    # The first installation must precede creation of a Listmonk API token.
    # Placeholder auth is used only for validation and never sent to the app.
    config_env=dict(env)
    if a.phase=='install':
        config_env['LISTMONK_API_USER']=env.get('LISTMONK_API_USER') or 'pending'
        config_env['LISTMONK_API_KEY']='installation-only-placeholder'
    cfg=MailConfig.from_env(config_env)
    required=('POSTGRES_PASSWORD','SES_SMTP_USERNAME','SES_SMTP_PASSWORD',
              'FCMO_EMAIL_PRIVACY_CONTACT','FCMO_EMAIL_DISPATCH_TOKEN',
              'FCMO_EMAIL_BACKUP_RECIPIENT','SES_SMTP_HOST','FCMO_EMAIL_SES_TOPIC_ARN',
              'FCMO_EMAIL_PUBLIC_URL','FCMO_EMAIL_FROM','FCMO_EMAIL_POSTAL_ADDRESS','FCMO_EMAIL_CONSENT_KEY')
    if a.phase=='active':required+=('LISTMONK_API_USER','LISTMONK_API_KEY')
    for name in required:
        if not env.get(name) or 'REPLACE_' in env[name] or '\n' in env[name]:
            raise ValueError('missing configuration: '+name)
    if len(env['POSTGRES_PASSWORD'])<24 or len(env['FCMO_EMAIL_DISPATCH_TOKEN'])<32:
        raise ValueError('database and dispatch secrets are too short')
    if not env['SES_SMTP_HOST'].endswith('.amazonaws.com'):
        raise ValueError('production SMTP host must be Amazon SES')
    if env.get('FCMO_EMAIL_COMPLIANCE_READY')!='true':
        raise ValueError('complete privacy/processor prerequisites first')
    if a.write_state:
        a.write_state.mkdir(parents=True,exist_ok=True,mode=0o700)
        a.write_state.chmod(0o700)
        for filename,values in (
            ('db.env',{'POSTGRES_DB':'listmonk','POSTGRES_USER':'listmonk','POSTGRES_PASSWORD':env['POSTGRES_PASSWORD']}),
            ('app.env',{'LISTMONK_db__password':env['POSTGRES_PASSWORD']})):
            target=a.write_state/filename
            target.write_text(''.join(k+'='+v+'\n' for k,v in values.items()));target.chmod(0o600)
        static=a.write_state/'static/email-templates';static.mkdir(parents=True,exist_ok=True)
        source=(ROOT/'ops/email/static/email-templates/subscriber-optin.html').read_text()
        # Postal address is mandatory even in confirmation mail. Escape Go
        # delimiters as well as HTML; the address is public editorial data.
        from tools.email_render import email_escape
        source=source.replace('</body>', '<p>'+email_escape(cfg.postal_address)+'</p></body>')
        (static/'subscriber-optin.html').write_text(source)
    print('Private email configuration valid')


if __name__=='__main__':main()
