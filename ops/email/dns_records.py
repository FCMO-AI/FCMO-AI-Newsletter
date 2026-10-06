#!/usr/bin/env python3
"""Emit exact DNS records from the operator's real SES identity response."""
import argparse
import ipaddress
import json
from pathlib import Path
import re


def records(domain, region, tokens, email_host, public_ip=None):
    if not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}',domain): raise ValueError('invalid domain')
    if not re.fullmatch(r'[a-z]{2}-[a-z]+-\d',region): raise ValueError('invalid region')
    if len(tokens)!=3 or any(not re.fullmatch('[a-z0-9]{16,64}',v) for v in tokens):
        raise ValueError('three real Easy DKIM tokens are required; do not invent these')
    result=[{'name':'bounce.'+domain,'type':'TXT','value':'v=spf1 include:amazonses.com ~all'},
            {'name':'bounce.'+domain,'type':'MX','priority':10,'value':'feedback-smtp.'+region+'.amazonses.com'},
            {'name':'_dmarc.'+domain,'type':'TXT','value':'v=DMARC1; p=none; adkim=r; aspf=r; pct=100'}]
    result += [{'name':v+'._domainkey.'+domain,'type':'CNAME','value':v+'.dkim.amazonses.com'} for v in tokens]
    if public_ip:
        address=ipaddress.ip_address(public_ip)
        result.append({'name':email_host,'type':'AAAA' if address.version==6 else 'A','value':str(address)})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--domain',required=True);p.add_argument('--region',default='us-east-1')
    p.add_argument('--identity-json',type=Path,required=True)
    p.add_argument('--email-host',required=True);p.add_argument('--public-ip')
    p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    doc=json.loads(a.identity_json.read_text())
    output=records(a.domain,a.region,doc['DkimAttributes']['Tokens'],a.email_host,a.public_ip)
    a.out.write_text(json.dumps(output,indent=2)+'\n')
    print('Exact account-specific DNS records written to '+str(a.out))


if __name__=='__main__':main()
