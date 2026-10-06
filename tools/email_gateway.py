#!/usr/bin/env python3
"""Loopback HTTP service behind the email Caddy allowlist."""
from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

if __package__ in (None, ''): sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.email_listmonk import DiarioService, DeliveryError, MailConfig, NoRedirect
from tools.email_live_receipt import collect

ROOT = Path(__file__).resolve().parents[1]
MESSAGES = {
    'en': ('Check your inbox', 'Confirm your subscription using the link in your email. You can unsubscribe in every edition.', 'Subscription unavailable', 'Please check your details or try again later.'),
    'es-419': ('Revisa tu correo', 'Confirma tu suscripción con el enlace del correo. Puedes darte de baja en cada edición.', 'Suscripción no disponible', 'Revisa tus datos o inténtalo más tarde.'),
    'zh-Hans': ('请查收邮件', '请通过邮件中的链接确认订阅。每期邮件都提供退订链接。', '暂时无法订阅', '请检查信息或稍后再试。'),
}


def live_lkg():
    url = 'https://api.github.com/repos/fcmo-ai/FCMO-AI-Newsletter/git/ref/tags/lkg'
    req = urllib.request.Request(url, headers={'Accept':'application/vnd.github+json','User-Agent':'FCMO-Email'})
    with urllib.request.build_opener(NoRedirect).open(req, timeout=20) as r:
        obj = json.loads(r.read(100000))['object']
    # Pages promotes a lightweight tag. Unexpected tag types fail closed.
    if obj.get('type') != 'commit' or not re.fullmatch('[0-9a-f]{40}', obj.get('sha','')):
        raise ValueError('invalid_live_lkg')
    return obj['sha']


def handler(service, dispatch_token, *, collector=collect, lkg_reader=live_lkg, privacy_contact='', ses_topic_arn=''):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # no subscriber data or URL tokens in logs

        def reply(self, status, body, content_type='application/json'):
            raw = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type+'; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers(); self.wfile.write(raw)

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path)
            if path.path == '/healthz': return self.reply(200, '{"status":"ok"}')
            if path.path != '/privacy': return self.reply(404, '{}')
            locale = urllib.parse.parse_qs(path.query).get('locale',['en'])[0]
            locale = locale if locale in MESSAGES else 'en'
            sections = json.loads((ROOT/'legal/email-privacy.json').read_text())[locale]
            body = ''.join('<p>'+escape(v)+'</p>' for v in sections)
            body += '<p>'+escape(service.config.postal_address)+'</p><p>'+escape(privacy_contact)+'</p>'
            return self.reply(200, '<!doctype html><html lang="'+locale+'"><meta charset="utf-8"><title>FCMO AI · Privacy</title><body><h1>FCMO AI</h1>'+body+'</body></html>', 'text/html')

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            try:
                self.connection.settimeout(15)
                length = int(self.headers.get('Content-Length','0'))
                if length <= 0 or length > (262144 if path=='/webhooks/service/ses' else 8192): return self.reply(413, '{}')
                if path == '/webhooks/service/ses':
                    raw = self.rfile.read(length)
                    doc = json.loads(raw)
                    if not ses_topic_arn or doc.get('TopicArn') != ses_topic_arn:
                        return self.reply(403,'{}')
                    # Topic allowlist plus Listmonk's SNS signature verification.
                    req = urllib.request.Request(service.config.listmonk_url+'/webhooks/service/ses',
                        data=raw,method='POST',headers={'Content-Type':'text/plain',
                        'X-Amz-Sns-Message-Type':self.headers.get('X-Amz-Sns-Message-Type','')})
                    with urllib.request.build_opener(NoRedirect).open(req,timeout=25) as r:
                        response = r.read(8192)
                    return self.reply(200,response.decode())
                if path == '/dispatch':
                    supplied = self.headers.get('Authorization','')
                    if not hmac.compare_digest(supplied, 'Bearer '+dispatch_token):
                        return self.reply(401, '{}')
                    if self.headers.get_content_type() != 'application/json': return self.reply(415,'{}')
                    doc = json.loads(self.rfile.read(length))
                    commit = doc.get('source_commit')
                    if not isinstance(commit,str) or commit != lkg_reader():
                        return self.reply(409, '{"error":"lkg_changed"}')
                    identity, stories, status = collector(service.config.site_url,commit)
                    if identity.get('candidate_id') != doc.get('candidate_id'):
                        return self.reply(409, '{"error":"candidate_changed"}')
                    outcome = service.dispatch(json.loads(stories),json.loads(status),live_verified=True,now=datetime.now(timezone.utc),locale=doc.get('locale'))
                    return self.reply(200,json.dumps(outcome))
                if path != '/subscribe': return self.reply(404,'{}')
                if self.headers.get_content_type() != 'application/x-www-form-urlencoded': return self.reply(415,'{}')
                form = urllib.parse.parse_qs(self.rfile.read(length).decode(), max_num_fields=8)
                locale = form.get('locale',['en'])[0]
                copy = MESSAGES.get(locale, MESSAGES['en'])
                if form.get('website',[''])[0]: raise ValueError('honeypot')
                # Caddy replaces this header from the TCP peer; no arbitrary
                # forwarded chain is trusted. Direct access is loopback only.
                ip = self.headers.get('X-Real-IP', self.client_address[0])
                service.subscribe(form.get('email',[''])[0],locale,form.get('consent',[''])[0]=='yes',ip,datetime.now(timezone.utc))
                html = '<!doctype html><html lang="'+escape(locale)+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+copy[0]+'</title><body><h1>'+copy[0]+'</h1><p>'+copy[1]+'</p></body></html>'
                return self.reply(200,html,'text/html')
            except (ValueError, DeliveryError, OSError, KeyError, TypeError):
                if path == '/subscribe':
                    locale = locals().get('locale','en'); copy = MESSAGES.get(locale,MESSAGES['en'])
                    return self.reply(503,'<!doctype html><meta charset="utf-8"><h1>'+copy[2]+'</h1><p>'+copy[3]+'</p>','text/html')
                return self.reply(503,'{"error":"email_boundary_failed"}')
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=9010)
    parser.add_argument('--state',type=Path,required=True)
    args = parser.parse_args()
    config = MailConfig.from_env(os.environ)
    token = os.environ['FCMO_EMAIL_DISPATCH_TOKEN']
    contact = os.environ['FCMO_EMAIL_PRIVACY_CONTACT']
    topic = os.environ['FCMO_EMAIL_SES_TOPIC_ARN']
    if len(token)<32 or not contact.strip(): raise ValueError('missing dispatch token or privacy contact')
    service = DiarioService(config,args.state)
    if os.environ.get('FCMO_EMAIL_COMPLIANCE_READY') != 'true': raise ValueError('email compliance prerequisites incomplete')
    HTTPServer(('127.0.0.1',args.port),handler(service,token,privacy_contact=contact,ses_topic_arn=topic)).serve_forever()


if __name__ == '__main__': main()
