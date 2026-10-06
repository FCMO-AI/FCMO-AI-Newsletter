import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from http.server import HTTPServer
from unittest.mock import Mock

from tools.email_gateway import handler
from ops.email.dns_records import records


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.service=Mock()
        self.service.config.site_url='https://example.org'
        self.service.dispatch.return_value={'action':'QUEUED'}
        self.collector=Mock(return_value=({'candidate_id':'candidate'},b'{"stories":[]}',b'{}'))
        self.token='test-token-'+('x'*40)
        self.server=HTTPServer(('127.0.0.1',0),handler(self.service,self.token,collector=self.collector,lkg_reader=lambda:'a'*40,ses_topic_arn='arn:aws:sns:us-east-1:123456789012:email'))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.cleanup)
        self.url='http://127.0.0.1:'+str(self.server.server_port)

    def cleanup(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def post(self,path,payload,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        with urlopen(Request(self.url+path,data=json.dumps(payload).encode(),headers=headers),timeout=5) as r:return json.load(r)

    def test_unauthenticated_dispatch_cannot_touch_provider(self):
        with self.assertRaises(HTTPError) as ctx:self.post('/dispatch',{})
        self.assertEqual(ctx.exception.code,401);self.collector.assert_not_called();self.service.dispatch.assert_not_called()

    def test_moved_lkg_or_candidate_blocks_dispatch(self):
        for receipt in ({'source_commit':'b'*40,'candidate_id':'candidate'}, {'source_commit':'a'*40,'candidate_id':'other'}):
            with self.assertRaises(HTTPError) as ctx:self.post('/dispatch',receipt,self.token)
            self.assertEqual(ctx.exception.code,409)
        self.service.dispatch.assert_not_called()

    def test_dispatch_recollects_live_candidate_before_send(self):
        result=self.post('/dispatch',{'source_commit':'a'*40,'candidate_id':'candidate'},self.token)
        self.assertEqual(result['action'],'QUEUED')
        self.collector.assert_called_once_with('https://example.org','a'*40)
        self.assertTrue(self.service.dispatch.call_args.kwargs['live_verified'])

    def test_foreign_sns_topic_cannot_blocklist_readers(self):
        with self.assertRaises(HTTPError) as ctx:self.post('/webhooks/service/ses',{'TopicArn':'other'})
        self.assertEqual(ctx.exception.code,403)

    def test_unknown_admin_paths_are_closed(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.url+'/api/subscribers',timeout=5)
        self.assertEqual(ctx.exception.code,404)

    def test_dns_values_use_real_identity_tokens(self):
        tokens=['a'*32,'b'*32,'c'*32]
        actual=records('example.org','us-east-1',tokens,'mail.example.org','192.0.2.1')
        self.assertIn({'name':'bounce.example.org','type':'TXT','value':'v=spf1 include:amazonses.com ~all'},actual)
        self.assertIn({'name':'a'*32+'._domainkey.example.org','type':'CNAME','value':'a'*32+'.dkim.amazonses.com'},actual)
        with self.assertRaises(ValueError):records('example.org','us-east-1',[],'mail.example.org')


if __name__=='__main__':unittest.main()
