#!/usr/bin/env python3
"""Real Listmonk + temporary PostgreSQL + SMTP sink. No external delivery.

Download the checksum-verified release binary separately. This test uses only
loopback listeners, synthetic readers, and the committed public edition.
"""
import argparse
import base64
import email
from email import policy
import html
from http.server import HTTPServer
import json
import os
from pathlib import Path
import re
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from ops.email.bootstrap import configure
from tools.email_dispatch import parse_timestamp
from tools.email_gateway import handler
from tools.email_listmonk import MailConfig,ListmonkClient,DiarioService,DeliveryError


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]


class Sink(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 localhost offline SMTP\r\n')
        recipients=[]
        while True:
            line=self.rfile.readline(8192)
            if not line:break
            verb=line.split(None,1)[0].upper()
            if verb in (b'EHLO',b'HELO'):self.wfile.write(b'250-localhost\r\n250 SIZE 10000000\r\n')
            elif verb==b'RCPT':
                recipients.append(line.decode().strip());self.wfile.write(b'250 OK\r\n')
            elif verb==b'DATA':
                self.wfile.write(b'354 End with dot\r\n');raw=[]
                while True:
                    data=self.rfile.readline(1000000)
                    if data in (b'.\r\n',b'') :break
                    raw.append(data[1:] if data.startswith(b'..') else data)
                self.server.messages.append((recipients[:],email.message_from_bytes(b''.join(raw),policy=policy.default)))
                recipients=[];self.wfile.write(b'250 accepted offline\r\n')
            elif verb==b'QUIT':self.wfile.write(b'221 bye\r\n');break
            else:self.wfile.write(b'250 OK\r\n')


def wait_for(predicate, timeout=30):
    start=time.monotonic()
    while time.monotonic()-start<timeout:
        try:
            result=predicate()
            if result:return result
        except (OSError,ValueError,DeliveryError):pass
        time.sleep(.1)
    raise AssertionError('offline condition timed out')


def http(url, data=None, headers=None):
    req=urllib.request.Request(url,data=data,headers=headers or {})
    with urllib.request.urlopen(req,timeout=15) as r:return r.read().decode()


def body(message):
    part=message.get_body(preferencelist=('html',))
    return part.get_content() if part else message.get_content()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listmonk',type=Path,required=True)
    parser.add_argument('--pg-bin',type=Path,default=Path('/usr/lib/postgresql/17/bin'))
    parser.add_argument('--out',type=Path,default=ROOT/'reports/email-preview')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    servers=[];app=None;pg_started=False
    with tempfile.TemporaryDirectory(prefix='fcmo-email-offline-') as temp:
        temp=Path(temp); pgport,appport,gatewayport=port(),port(),port()
        pgdata=temp/'pgdata'
        try:
            subprocess.run([str(args.pg_bin/'initdb'),'-D',str(pgdata),'-A','trust','-U','listmonk'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
            subprocess.run([str(args.pg_bin/'pg_ctl'),'-D',str(pgdata),'-l',str(temp/'postgres.log'),'-o',f'-h 127.0.0.1 -p {pgport} -k {temp}','-w','start'],stdout=subprocess.DEVNULL,check=True)
            pg_started=True
            subprocess.run([str(args.pg_bin/'createdb'),'-h','127.0.0.1','-p',str(pgport),'-U','listmonk','listmonk'],check=True)
            config=temp/'config.toml'
            config.write_text(f'[app]\naddress="127.0.0.1:{appport}"\n[db]\nhost="127.0.0.1"\nport={pgport}\nuser="listmonk"\npassword="offline"\ndatabase="listmonk"\nssl_mode="disable"\n')
            env=dict(os.environ,LISTMONK_ADMIN_USER='offline-admin',LISTMONK_ADMIN_PASSWORD='offline-password',LISTMONK_ADMIN_API_USER='offline-api')
            install=subprocess.run([str(args.listmonk),'--config',str(config),'--install','--yes'],env=env,capture_output=True,check=True)
            key=re.search(r'export LISTMONK_ADMIN_API_TOKEN="([^"]+)"',install.stderr.decode()).group(1)
            # No update lookup is needed in this provider-free test.
            subprocess.run([str(args.pg_bin/'psql'),'-h','127.0.0.1','-p',str(pgport),'-U','listmonk','-d','listmonk','-c',"UPDATE settings SET value='false'::jsonb WHERE key='app.check_updates'"],stdout=subprocess.DEVNULL,check=True)
            app=subprocess.Popen([str(args.listmonk),'--config',str(config),'--static-dir',str(ROOT/'ops/email/static')],stdout=(temp/'app.log').open('w'),stderr=subprocess.STDOUT)
            cfg=MailConfig(f'http://127.0.0.1:{appport}','offline-api',key,f'http://127.0.0.1:{appport}',
                           'FCMO AI Newsletter <daily@example.org>','Offline preview — postal address required before activation',
                           'https://fcmo-ai.github.io/FCMO-AI-Newsletter','offline-consent-key-'+('x'*32))
            client=ListmonkClient(cfg)
            wait_for(lambda:client.request('GET','settings'))
            smtp=socketserver.ThreadingTCPServer(('127.0.0.1',0),Sink);smtp.messages=[];servers.append(smtp)
            threading.Thread(target=smtp.serve_forever,daemon=True).start()
            lists=configure(client,{'SES_SMTP_HOST':'127.0.0.1','SES_SMTP_PORT':str(smtp.server_address[1])},offline=True)
            service=DiarioService(cfg,temp/'state.sqlite',client=client)
            gateway=HTTPServer(('127.0.0.1',gatewayport),handler(service,'offline-dispatch-token-'+('x'*32)))
            servers.append(gateway);threading.Thread(target=gateway.serve_forever,daemon=True).start()
            base=f'http://127.0.0.1:{gatewayport}'
            for locale in lists:
                data=urllib.parse.urlencode({'email':locale+'@example.org','locale':locale,'consent':'yes'}).encode()
                try:
                    response=http(base+'/subscribe',data,{'Content-Type':'application/x-www-form-urlencoded'})
                except urllib.error.HTTPError:
                    service.subscribe(locale+'@example.org',locale,True,'127.0.0.1',parse_timestamp('2026-10-05T23:02:05Z'))
                    raise
                assert 'confirm' in response.lower() or locale=='zh-Hans'
            wait_for(lambda:len(smtp.messages)==3)
            def readers():
                return [s for s in client.request('GET','subscribers?per_page=all')['results'] if s['email'].lower() in [locale.lower()+'@example.org' for locale in lists]]
            subscribers=readers()
            assert len(subscribers)==3
            for sub in subscribers:
                assert sub['lists'][0]['subscription_status']=='unconfirmed'
            data=urllib.parse.urlencode({'email':'pending@example.org','locale':'en','consent':'yes'}).encode()
            http(base+'/subscribe',data,{'Content-Type':'application/x-www-form-urlencoded'})
            wait_for(lambda:len(smtp.messages)==4)
            # A single-opt-in campaign or preconfirmation is never used.
            stories=json.loads((ROOT/'site/data/stories.v2.json').read_text())
            status=json.loads((ROOT/'site/data/newsroom-status.json').read_text())
            from tools.email_dispatch import eligibility
            now=parse_timestamp(status['generated_at']) if 'generated_at' in status else parse_timestamp(status['edition_date']+'T23:02:05Z')
            decision=eligibility(stories,status,live_verified=True,now=now)
            assert decision.action=='SEND',decision.reason
            for _,msg in smtp.messages[:]:
                if 'pending@example.org' in str(msg['To']):continue
                link=html.unescape(re.search(r'href="([^"]+/subscription/optin/[^"]+)"',body(msg)).group(1))
                http(link)
                current=next(s for s in readers() if s['uuid'] in link)
                assert current['lists'][0]['subscription_status']=='unconfirmed'
                separator='&' if '?' in link else '?'
                http(link+separator+'confirm=true',b'confirm=true',{'Content-Type':'application/x-www-form-urlencoded'})
            assert all(s['lists'][0]['subscription_status']=='confirmed' for s in readers())
            first=service.dispatch(stories,status,live_verified=True,now=now)
            assert first['action']=='QUEUED',first
            wait_for(lambda:len(smtp.messages)==7)
            service=DiarioService(cfg,temp/'state.sqlite',client=client)
            assert service.dispatch(stories,status,live_verified=True,now=now)['action']=='SKIP'
            time.sleep(.2);assert len(smtp.messages)==7
            delivered=[]
            for recipients,msg in smtp.messages[4:]:
                locale=next(v for v in lists if v.lower()+'@example.org' in str(msg['To']).lower())
                assert msg['List-Unsubscribe-Post']=='List-Unsubscribe=One-Click'
                unsub=str(msg['List-Unsubscribe']).strip('<>')
                content=body(msg)
                assert content.lower().count('<!doctype html>')==1
                expected_lang={'en':'en','es-419':'es-MX','zh-Hans':'zh-Hans'}[locale]
                assert '<html lang="'+expected_lang+'"' in content
                assert unsub in html.unescape(content)
                assert '{{ UnsubscribeURL }}' not in content
                assert '/px.png' not in content and '@TrackLink' not in content
                # Save the actual post-template message, using a clearly fake
                # recipient token and stable preview URL rather than real PII.
                preview=re.sub(r'http://127\.0\.0\.1:\d+/subscription/[^"\s<>?]+', 'https://mail.example.org/subscription/preview/reader',content)
                (args.out/(status['edition_date']+'-'+locale+'.html')).write_text(preview)
                text=msg.get_body(preferencelist=('plain',))
                if text:(args.out/(status['edition_date']+'-'+locale+'.txt')).write_text(text.get_content().replace(unsub,'https://mail.example.org/subscription/preview/reader'))
                http(unsub,b'List-Unsubscribe=One-Click',{'Content-Type':'application/x-www-form-urlencoded'})
                delivered.append(locale)
            assert all(s['lists'][0]['subscription_status']=='unsubscribed' for s in readers())
            assert not any('pending@example.org' in str(msg['To']) for _,msg in smtp.messages[4:])
            # The provider's native authenticated bounce hook must suppress
            # hard bounces and complaints independently of unsubscribe state.
            auth='Basic '+base64.b64encode(('offline-api:'+key).encode()).decode()
            for kind,reader in zip(('hard','complaint'),readers()[:2]):
                http(cfg.listmonk_url+'/webhooks/bounce',json.dumps({'subscriber_uuid':reader['uuid'],'type':kind,'source':'offline-provider'}).encode(),{'Content-Type':'application/json','Authorization':auth})
            wait_for(lambda:sum(s['status']=='blocklisted' for s in readers())==2)
            # An unsigned SNS event is rejected by the actual provider handler.
            try:
                http(cfg.listmonk_url+'/webhooks/service/ses',b'{"Type":"Notification"}',{'Content-Type':'text/plain','X-Amz-Sns-Message-Type':'Notification'})
                raise AssertionError('unsigned SNS accepted')
            except urllib.error.HTTPError as exc:assert exc.code==400
            # API age format is checked against the pinned binary too.
            client.request('DELETE','maintenance/subscriptions/unconfirmed?before_date=2026-09-05T00%3A00%3A00Z')
            from ops.email.offline_backup import prove_backup
            prove_backup(args.pg_bin,pgport,temp/'state.sqlite',args.out)
            proof={'status':'PASS','edition':status['edition_date'],'listmonk':'6.2.0','double_optin':True,
                   'confirmed_readers':3,'smtp_confirmation_messages':4,'smtp_diario_messages':3,
                   'unconfirmed_diario_messages':0,'bounce_and_complaint_suppressions':2,'unsigned_sns_rejected':True,
                   'restart_duplicate_messages':0,'one_click_unsubscribe':3,'locales':sorted(delivered),
                   'provider':'loopback SMTP sink','production_delivery':'not attempted'}
            (args.out/'offline-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
            print(json.dumps(proof,sort_keys=True))
        except Exception:
            if (temp/'app.log').exists():
                # Offline-only diagnostics; no real provider credentials here.
                print((temp/'app.log').read_text()[-5000:],file=sys.stderr)
            raise
        finally:
            for server in servers:server.shutdown();server.server_close()
            if app:app.terminate();app.wait(timeout=15)
            if pg_started:subprocess.run([str(args.pg_bin/'pg_ctl'),'-D',str(pgdata),'-m','fast','-w','stop'],stdout=subprocess.DEVNULL,check=True)


if __name__=='__main__':main()
