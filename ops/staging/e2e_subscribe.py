#!/usr/bin/env python3
"""Local Ghost/Mailpit subscription proof. Fails closed on every uncertain UI/API result."""
from __future__ import annotations

import json
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.email_dispatch import GhostClient  # noqa: E402
from tools.paper.templates.subscribe import subscription_config  # noqa: E402

STATE = Path(__file__).resolve().parent / '.state'
GHOST = 'http://127.0.0.1:2368'
MAILPIT = 'http://127.0.0.1:8025'


class SignupLink(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == 'a' and values.get('data-ghost-portal') == 'signup' and values.get('href'):
            self.links.append(values['href'])


def json_get(url: str) -> dict:
    with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=10) as response:
        return json.load(response)


def create_newsletters(client: GhostClient, config: dict) -> None:
    existing = client._request('GET', 'newsletters/?limit=all').get('newsletters', [])
    by_slug = {item['slug']: item for item in existing}
    wanted = {product['slug'] for product in config['products'].values()}
    for product in config['products'].values():
        if product['slug'] not in by_slug:
            client._request('POST', 'newsletters/', {'newsletters': [{
                'name': product['name'], 'slug': product['slug'], 'description': product['brand'] + ' · ' + product['author'],
                'status': 'active', 'visibility': 'members', 'subscribe_on_signup': False,
                'sender_name': product['brand'], 'sender_email': 'staging@localhost',
            }]})
    current = client._request('GET', 'newsletters/?limit=all').get('newsletters', [])
    for item in current:
        if item['slug'] not in wanted and item.get('status') == 'active':
            client._request('PUT', f"newsletters/{item['id']}/", {'newsletters': [{
                'id': item['id'], 'updated_at': item['updated_at'], 'status': 'inactive',
            }]})
    active = client._request('GET', 'newsletters/?limit=all').get('newsletters', [])
    assert {item['slug'] for item in active if item.get('status') == 'active'} == wanted, active


def run_browser(operation: str, url: str, email: str, names: list[str] = ()) -> None:
    env = dict(os.environ, STAGING_BROWSER_PROFILE=str(STATE / ('browser-' + email.split('@', 1)[0])))
    subprocess.run(['node', str(Path(__file__).with_name('portal_probe.mjs')), operation, url, email, ','.join(names)],
                   env=env, check=True, timeout=90)


def wait_mail(email: str, seen: set[str], timeout: int = 45) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        payload = json_get(MAILPIT + '/api/v1/messages?limit=50')
        for message in payload.get('messages', []):
            mid = message.get('ID')
            recipients = [row.get('Address') for row in message.get('To', [])]
            if mid in seen or email not in recipients:
                continue
            seen.add(mid)
            body = json_get(MAILPIT + '/api/v1/message/' + quote(mid))
            content = body.get('HTML') or body.get('Text') or ''
            links = re.findall(r'https?://[^\s"<>]+', content.replace('&amp;', '&'))
            for link in links:
                if 'magic' in link or 'token=' in link:
                    return link.rstrip(').,')
        time.sleep(1)
    raise AssertionError(f'no confirmation link for {email}')


def member_newsletters(client: GhostClient, email: str) -> tuple[str, set[str]]:
    response = client._request('GET', 'members/?limit=all&include=newsletters&filter=email:' + quote(email, safe=''))
    members = response.get('members', [])
    assert len(members) == 1, f'expected one member for {email}, got {len(members)}'
    member = members[0]
    return member['id'], {item['slug'] for item in member.get('newsletters', [])}


def main() -> int:
    STATE.mkdir(exist_ok=True)
    key_file = STATE / 'admin-api-key'
    if not key_file.exists():
        raise RuntimeError('Create a Ghost custom integration and save its Admin API key in ops/staging/.state/admin-api-key')
    if key_file.stat().st_mode & 0o077:
        raise RuntimeError('admin-api-key must be mode 600')
    config = subscription_config()
    client = GhostClient(GHOST, key_file.read_text().strip())
    create_newsletters(client, config)
    build_out = STATE / 'site'
    env = dict(os.environ, GHOST_URL=GHOST)
    subprocess.run([sys.executable, str(ROOT / 'tools/paper/build.py'), '--stories', str(ROOT / 'tests/fixtures/stories.v2.json'),
                    '--status', str(ROOT / 'tests/fixtures/newsroom-status.fresh.json'), '--out', str(build_out),
                    '--base', '/FCMO-AI-Newsletter/'], env=env, cwd=ROOT, check=True)
    site = build_out / 'es/suscribete/index.html'
    rendered = site.read_text()
    assert 'data-subscribe-state="active"' in rendered, 'site did not activate signup'
    links = SignupLink()
    links.feed(rendered)
    assert links.links == [GHOST + '/#/portal/signup'], f'unexpected site signup link: {links.links}'
    seen: set[str] = set()
    names = {key: product['name'] for key, product in config['products'].items()}
    for chosen in ({'letter'}, {'paper'}, {'letter', 'paper'}):
        email = 'staging-' + '-'.join(sorted(chosen)) + '@localhost'
        run_browser('signup', links.links[0], email, [names[key] for key in chosen])
        link = wait_mail(email, seen)
        run_browser('confirm', link, email)
        member_id, selected = member_newsletters(client, email)
        expected = {config['products'][key]['slug'] for key in chosen}
        assert selected == expected, f'{email}: expected {expected}, got {selected}'
        run_browser('unsubscribe', GHOST + '/#/portal/account', email, [names[key] for key in chosen])
        after_id, selected = member_newsletters(client, email)
        assert after_id == member_id and not selected, f'{email}: unsubscribe left {selected}'
        print('PASS', sorted(chosen), 'confirmed and unsubscribed')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'FAIL {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
