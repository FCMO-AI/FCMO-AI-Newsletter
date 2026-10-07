#!/usr/bin/env python3
"""Dispatch reviewed published pieces using the existing provider/intent boundary."""
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if __package__ in (None, ''): sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.email_providers import LOCALES, create_provider
from tools.email_render import render_piece_email
from tools.email_piece_render import PREFIX, piece_url
from tools.email_listmonk import DeliveryError
from tools.email_intent import prepare_keys

SITE = 'https://fcmo-ai.github.io/FCMO-AI-Newsletter'


@dataclass(frozen=True)
class PieceEdition:
    piece: dict
    receipt: dict
    now: datetime
    # Reuse L27's seed selection and isolation checks, with a separate piece key.
    namespace: str = 'fcmo-diario'

    def key(self, locale):
        if locale not in LOCALES or self.namespace not in ('fcmo-diario', 'fcmo-diario-test'):
            raise ValueError('invalid_piece_email_locale_or_namespace')
        identity = self.piece.get('id', '')
        if not re.fullmatch(r'FCMO-P-[0-9a-f]{12}', identity): raise ValueError('invalid_piece_id')
        return ('fcmo-piece-test' if self.namespace == 'fcmo-diario-test' else 'fcmo-piece') + ':' + identity + ':' + locale

    def reason(self):
        if self.piece.get('schema') != 'fcmo-piece-v1': raise ValueError('invalid_piece_schema')
        if self.piece.get('status') != 'published': return 'piece_not_published'
        if self.piece.get('distribution', {}).get('email') is not True: return 'email_not_requested'
        published = datetime.fromisoformat(self.piece['first_published_at'].replace('Z', '+00:00'))
        if published.tzinfo is None: raise ValueError('piece_publication_timezone_required')
        if published > self.now: return 'piece_not_yet_published'
        return ''

    def locale_reason(self, locale):
        if self.piece.get('locales', {}).get(locale) != 'ready' or locale not in self.piece.get('docs', {}):
            return 'locale_not_ready'
        if self.piece.get('provenance', {}).get(locale, {}).get('human_reviewed') is not True:
            return 'human_review_required'
        return ''

    def sendable(self):
        return [] if self.reason() else [locale for locale in LOCALES if not self.locale_reason(locale)]

    def selected(self):
        if self.reason(): raise ValueError('piece_not_eligible')
        self.key('en')
        return self.piece

    def validate_locale(self, locale):
        self.selected()
        if locale not in LOCALES or self.locale_reason(locale): raise ValueError('piece_locale_not_reviewed_and_ready')

    def render(self, locale, **kwargs):
        self.validate_locale(locale)
        return render_piece_email(self.piece, locale=locale, **kwargs)

    def preflight(self):
        for locale in self.sendable():
            self.render(locale, postal_address='Preflight only', site_url=self.receipt.get('site_url', SITE))


def dispatch_piece(provider, edition, *, enabled, live_verified):
    if not enabled: return {'action': 'SKIP', 'reason': 'disabled'}
    if not live_verified: return {'action': 'SKIP', 'reason': 'not_verified'}
    reason = edition.reason()
    if reason: return {'action': 'SKIP', 'reason': reason}
    edition.preflight()
    ready = edition.sendable()
    if ready:
        prepare = getattr(provider, 'prepare_edition', None)
        if prepare: prepare(edition)
    outcomes = {}
    for locale in LOCALES:
        reason = edition.locale_reason(locale)
        if reason:
            outcomes[locale] = {'action': 'SKIP', 'reason': reason}
            continue
        try: outcomes[locale] = provider.send_edition(edition, locale, edition.key(locale))
        except DeliveryError:
            outcomes[locale] = {'action': 'BLOCKED', 'reason': 'provider_outcome_requires_reconcile'}
    action = ('BLOCKED' if any(row['action'] == 'BLOCKED' for row in outcomes.values()) else
              'QUEUED' if any(row['action'] == 'QUEUED' for row in outcomes.values()) else 'SKIP')
    return {'action': action, 'locales': outcomes}


def record_dispatch(records, edition, result):
    """Public projection; includes no prose, addresses, recipient IDs or secrets."""
    rows = {(r['piece_id'], r['locale']): dict(r) for r in records}
    for locale, outcome in result.get('locales', {}).items():
        key = edition.piece['id'], locale
        state = ('QUEUED' if outcome.get('id') is not None and outcome['action'] in ('SKIP', 'QUEUED') else
                 'BLOCKED_RECONCILE' if outcome['action'] == 'BLOCKED' else
                 'SKIPPED_UNREVIEWED' if outcome.get('reason') == 'human_review_required' else 'SKIPPED_NOT_READY')
        if rows.get(key, {}).get('state') == 'QUEUED' and state.startswith('SKIPPED'): continue
        rows[key] = {'piece_id': key[0], 'locale': locale, 'state': state,
                     'broadcast_id': outcome.get('id'), 'timestamp': edition.now.isoformat().replace('+00:00', 'Z')}
    return [rows[key] for key in sorted(rows)]


def collect(base_url, lkg_commit, *, fetch=None, git=None, verify=None):
    """Prove live docs equal the immutable LKG source, and reviewed web pages exist.

    Studio's paper build copies these public JSON files byte-for-byte. Discovery
    comes from LKG, never main's possibly newer drafts. No generic GREEN file can
    substitute for this production boundary.
    """
    from tools.email_live_receipt import collect as daily_collect
    from tools import verify_live_front_page
    get = fetch or verify_live_front_page.fetch
    verify = verify or daily_collect
    identity, _, _ = verify(base_url, lkg_commit, fetch=get)
    def git_read(*args):
        return subprocess.run(['git', *args], check=True, capture_output=True).stdout
    run = git or git_read
    paths = run('ls-tree', '-r', '--name-only', lkg_commit, '--', 'editorial/pieces').decode().splitlines()
    metadata = [path for path in paths if re.fullmatch(r'editorial/pieces/[a-z0-9]+(?:-[a-z0-9]+)*/piece\.json', path)]
    pieces, seen = [], set()
    base = base_url.rstrip('/') + '/'
    for path in sorted(metadata):
        raw = run('show', lkg_commit + ':' + path); piece = json.loads(raw)
        if piece.get('status') != 'published' or piece.get('distribution', {}).get('email') is not True: continue
        directory = path.rsplit('/', 1)[0]
        if directory.rsplit('/', 1)[1] != piece.get('slug'): raise ValueError('piece_directory_slug_mismatch')
        if get(base + path, 'piece-input') != raw: raise ValueError('live_piece_differs_from_lkg')
        piece['docs'] = {}
        for name, field in [('provenance.json', 'provenance'), ('sources.json', 'sources'), ('figures.json', 'figures')]:
            route = directory + '/' + name
            raw = run('show', lkg_commit + ':' + route)
            if get(base + route, 'piece-input') != raw: raise ValueError('live_piece_differs_from_lkg')
            piece[field] = json.loads(raw)
        for locale in LOCALES:
            route = directory + '/doc.' + locale + '.json'
            if route not in paths: continue
            raw = run('show', lkg_commit + ':' + route)
            if get(base + route, 'piece-input') != raw: raise ValueError('live_piece_differs_from_lkg')
            piece['docs'][locale] = json.loads(raw)
            if piece.get('locales', {}).get(locale) == 'ready' and piece['provenance'].get(locale, {}).get('human_reviewed') is True:
                page = get(piece_url(piece, locale, base_url) + 'index.html', 'piece-page').decode('utf-8')
                if f'data-piece-id="{piece["id"]}"' not in page or escape(piece['docs'][locale]['title']) not in page:
                    raise ValueError('live_piece_page_not_published')
        for fig in piece['figures'].values():
            if not re.fullmatch(r'figures/[A-Za-z0-9-]+\.webp', fig.get('file', '')):
                raise ValueError('invalid_piece_figure_path')
            route = directory + '/' + fig['file']
            if get(base + route, 'piece-figure') != run('show', lkg_commit + ':' + route):
                raise ValueError('live_piece_figure_differs_from_lkg')
        if piece.get('id') in seen: raise ValueError('duplicate_piece_id')
        seen.add(piece.get('id')); pieces.append(piece)
    # Refuse a deployment that changed in the middle of this collection.
    if json.loads(get(base + 'deployment-identity.json', 'piece-final')) != identity:
        raise ValueError('live_candidate_changed_during_piece_collection')
    return {'schema': 'fcmo-email-pieces-v1', 'identity': identity, 'site_url': base_url.rstrip('/'), 'pieces': pieces}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--collect', action='store_true'); mode.add_argument('--claim', action='store_true'); mode.add_argument('--send', action='store_true')
    parser.add_argument('--lkg-commit'); parser.add_argument('--base-url', default=SITE)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--intent', type=Path); parser.add_argument('--state', type=Path)
    args = parser.parse_args(argv)
    if os.environ.get('FCMO_EMAIL_ENABLED') != 'true':
        print('SKIP pieces disabled'); return 0
    try:
        if args.collect:
            bundle = collect(args.base_url, args.lkg_commit)
            args.bundle.parent.mkdir(parents=True, exist_ok=True)
            args.bundle.write_text(json.dumps(bundle, ensure_ascii=False) + '\n')
            print(f'PIECES VERIFIED count={len(bundle["pieces"])}'); return 0
        from tools.email_piece_state import StateStore
        bundle = json.loads(args.bundle.read_text())
        now = datetime.now(timezone.utc)
        namespace = os.environ.get('FCMO_EMAIL_NAMESPACE', 'fcmo-diario')
        env = dict(os.environ, FCMO_SITE_URL=bundle['site_url'])
        editions = [PieceEdition(p, {'site_url': bundle['site_url']}, now, namespace) for p in bundle['pieces']]
        for edition in editions: edition.preflight()
        keys = [e.key(locale) for e in editions for locale in e.sendable()]
        store = StateStore(env, source_commit=bundle['identity']['source_commit'])
        if args.claim:
            if keys:
                provider = create_provider(env)
                if namespace == 'fcmo-diario-test' and provider.name != 'kit': raise ValueError('seed_provider_not_configured')
                health = provider.health()
                for warning in health.get('warnings', []):
                    if warning == 'brevo_daily_cap_exceeded': print('WARNING brevo_daily_cap_exceeded')
            state, sha = store.read()
            prepare_keys(keys, [{'keys': state['keys']}], args.intent)
            state['keys'] = sorted(set(state['keys']) | set(keys))
            for edition in editions:
                known = {(r['piece_id'], r['locale']) for r in state['records']}
                for locale in edition.sendable():
                    if (edition.piece['id'], locale) not in known:
                        state['records'].append({'piece_id': edition.piece['id'], 'locale': locale,
                            'state': 'PENDING', 'broadcast_id': None,
                            'timestamp': now.isoformat().replace('+00:00', 'Z')})
                result = {'locales': {locale: {'action': 'SKIP', 'reason': edition.locale_reason(locale)}
                                      for locale in LOCALES if edition.locale_reason(locale)}}
                state['records'] = record_dispatch(state['records'], edition, result)
            # Durable public reservation precedes both artifact upload and POST.
            sha = store.write(state, sha)
            args.state.write_text(json.dumps({'state': state, 'sha': sha}))
            print(f'PIECE INTENT READY keys={len(keys)}'); return 0
        # Recheck LKG/live bytes immediately before any provider mutation.
        fresh = collect(bundle['site_url'], bundle['identity']['source_commit'])
        if fresh != bundle: raise ValueError('piece_bundle_changed_before_send')
        saved = json.loads(args.state.read_text()); state, sha = saved['state'], saved['sha']
        provider = create_provider(dict(env, FCMO_EMAIL_INTENT=str(args.intent)))
        failed = False
        try:
            for edition in editions:
                result = dispatch_piece(provider, edition, enabled=True, live_verified=True)
                failed |= result['action'] == 'BLOCKED'
                state['records'] = record_dispatch(state['records'], edition, result)
                for locale, outcome in result.get('locales', {}).items():
                    print(f'PIECE {edition.piece["id"]} {locale} {outcome["action"]} {outcome.get("reason", "")}')
                # Preserve each piece's observations even if a later one fails.
                sha = store.write(state, sha)
        finally:
            args.state.write_text(json.dumps({'state': state, 'sha': sha}))
        return 1 if failed else 0
    except (OSError, ValueError, KeyError, TypeError, DeliveryError, subprocess.CalledProcessError):
        print('ERROR piece_dispatch_failed_closed'); return 1


if __name__ == '__main__': sys.exit(main())
