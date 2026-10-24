"""Studio → Jarvis notices: review requested, published, stuck or uncertain publication.

Read-only over studio.sqlite (opened with mode=ro). Writes only into the Kyrion mensajeria
outbox (the durable queue Jarvis' gateway drains and re-validates) and into its own ledger
file. Each event is sent once: the ledger and the outbox/receipts check dedupe by a stable id.

Content is minimal by design: the piece title, the status, and https links. Never the body,
never tokens, never host paths.

Usage:
  python3 studio/host-ops/notify.py --data <STUDIO_DATA> --mensajeria <dir con outbox/ y receipts/> [--ledger FILE] [--sembrar | --enviar] [--json]

Dry run by default: prints what it would queue and writes nothing.
First run: `--sembrar` records every event that exists today in the ledger WITHOUT sending
anything, so the history never floods Telegram. `--enviar` refuses to run while the ledger
file does not exist (a lost ledger must be re-seeded, not replayed).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

STUCK_AFTER = timedelta(hours=2)
TERMINAL = frozenset({'published', 'failed', 'withdrawn'})
PERSONAS = ('javier', 'matias')
NAMES = {'javier': 'Javier', 'matias': 'Matías'}
TITLE_MAX = 120
URL_MAX = 300
DE = 'studio'
CANAL = 'telegram'
TURN_KEY = 'studio-notify'


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_at(value) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def plain(text, limit: int) -> str:
    """One line, no control characters, bounded."""
    cleaned = ' '.join(''.join(ch if ch.isprintable() else ' ' for ch in str(text)).split())
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1] + '…'


def safe_urls(raw) -> list[str]:
    urls = []
    for item in raw or []:
        value = item.get('url') if isinstance(item, dict) else item
        if not isinstance(value, str) or len(value) > URL_MAX:
            continue
        parts = urlsplit(value)
        if parts.scheme == 'https' and parts.netloc and not any(ch.isspace() for ch in value):
            urls.append(value)
    return urls


def open_readonly(db_path: Path) -> sqlite3.Connection:
    uri = f'file:{db_path}?mode=ro'
    connection = sqlite3.connect(uri, uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def piece_title(connection, slug: str) -> str:
    row = connection.execute('SELECT payload_json FROM pieces WHERE slug=?', (slug,)).fetchone()
    if row is None:
        return slug
    try:
        title = json.loads(row['payload_json'] or '{}').get('piece', {}).get('title')
    except (ValueError, AttributeError):
        title = None
    return plain(title or slug, TITLE_MAX)


def event(key: str, recipient: str, text: str) -> dict:
    digest = hashlib.sha256(f'{key}\0{recipient}'.encode()).hexdigest()[:32]
    return {'key': key, 'para': recipient, 'texto': text, 'id': digest}


def collect(connection, now: datetime) -> list[dict]:
    events: list[dict] = []
    for row in connection.execute("SELECT id, slug, author, reviewer FROM reviews WHERE state='requested' ORDER BY at, id"):
        title = piece_title(connection, row['slug'])
        requester = NAMES.get(row['author'], 'La otra persona')
        if row['reviewer'] in PERSONAS:
            events.append(event(f"review:{row['id']}", row['reviewer'],
                                f"Studio: {requester} pidió tu revisión de «{title}». Revísala en Studio."))
    for row in connection.execute('SELECT id, slug, state, payload_json FROM publications ORDER BY id'):
        try:
            data = json.loads(row['payload_json'] or '{}')
        except ValueError:
            data = {}
        title = plain(data.get('title') or piece_title(connection, row['slug']), TITLE_MAX)
        author = data.get('author')
        state = row['state']
        if state == 'published' and author in PERSONAS:
            links = ' '.join(safe_urls(data.get('urls')))
            suffix = f' {links}' if links else ''
            events.append(event(f"published:{row['id']}", author, f'Studio: «{title}» ya está publicado.{suffix}'))
            continue
        if state == 'uncertain' or data.get('unknown'):
            events.append(event(f"uncertain:{row['id']}", 'matias',
                                f'Studio: la publicación de «{title}» quedó incierta; no se confirma si llegó al sitio. Revisa Studio.'))
            continue
        if state in TERMINAL:
            continue
        timeline = data.get('timeline') or []
        last = parse_at(timeline[-1].get('at')) if timeline and isinstance(timeline[-1], dict) else None
        if last is not None and now - last > STUCK_AFTER:
            events.append(event(f"stuck:{row['id']}", 'matias',
                                f'Studio: la publicación de «{title}» lleva más de 2 h en «{plain(state, 40)}». Revisa Studio.'))
    return events


def load_ledger(path: Path) -> set[str]:
    try:
        return set(json.loads(path.read_text()).get('sent', []))
    except (FileNotFoundError, ValueError, AttributeError):
        return set()


def save_ledger(path: Path, sent: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump({'sent': sorted(sent)}, handle)
    os.replace(tmp, path)


def already_queued(root: Path, mid: str) -> bool:
    out, rec = root / 'outbox', root / 'receipts'
    return (out / f'{mid}.json').exists() or (out / f'{mid}.claim').exists() or (rec / f'{mid}.json').exists()


def enqueue(root: Path, item: dict, now_s: int) -> str:
    """Write one Kyrion mensajeria entry (same shape as the Caudal notices). Idempotent by id.

    `root` is the mensajeria directory that holds outbox/ and receipts/. It must already exist:
    Kyrion owns it, so this never creates it.
    """
    if not (root / 'outbox').is_dir() or not (root / 'receipts').is_dir():
        raise SystemExit(f'notify: no existe la cola de mensajería (outbox/ y receipts/) en {root}')
    if already_queued(root, item['id']):
        return 'duplicate'
    path = root / 'outbox' / f"{item['id']}.json"
    tmp = path.parent / (path.name + '.tmp')
    entry = {'de': DE, 'rol': 'member', 'canal_origen': DE, 'para': item['para'], 'canal': CANAL,
             'texto': item['texto'], 'id': item['id'], 'ts': now_s}
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as handle:
        json.dump(entry, handle, ensure_ascii=False)
    os.replace(tmp, path)
    return 'queued'


def run(data_dir: Path, mensajeria: Path, ledger: Path, enviar: bool, now: datetime | None = None,
        sembrar: bool = False) -> dict:
    db_path = data_dir / 'studio.sqlite'
    if not db_path.exists():
        raise SystemExit(f'notify: no existe la base de Studio en {data_dir}')
    if sembrar and enviar:
        raise SystemExit('notify: --sembrar y --enviar son excluyentes')
    if enviar and not ledger.exists():
        raise SystemExit(f'notify: no existe el ledger {ledger}; corre primero --sembrar para no reenviar el historial')
    now = now or utc_now()
    connection = open_readonly(db_path)
    try:
        events = collect(connection, now)
    finally:
        connection.close()
    sent = load_ledger(ledger)
    report = {'eventos': len(events), 'encolados': 0, 'ya_enviados': 0, 'sembrados': 0, 'enviar': enviar, 'detalle': []}
    now_s = int(now.timestamp())
    if sembrar:
        for item in events:
            if item['id'] not in sent:
                sent.add(item['id'])
                report['sembrados'] += 1
            else:
                report['ya_enviados'] += 1
        save_ledger(ledger, sent)
        return report
    for item in events:
        if item['id'] in sent:
            report['ya_enviados'] += 1
            continue
        if not enviar:
            report['detalle'].append({'para': item['para'], 'texto': item['texto'], 'accion': 'encolaria'})
            continue
        state = enqueue(mensajeria, item, now_s)
        sent.add(item['id'])
        if state == 'queued':
            report['encolados'] += 1
        report['detalle'].append({'para': item['para'], 'texto': item['texto'], 'accion': state})
    if enviar:
        save_ledger(ledger, sent)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Avisos de Studio a Jarvis (dry run por omisión).')
    parser.add_argument('--data', required=True, type=Path, help='directorio de datos de Studio (contiene studio.sqlite)')
    parser.add_argument('--mensajeria', required=True, type=Path, help='directorio mensajeria de Kyrion (contiene outbox/ y receipts/)')
    parser.add_argument('--ledger', type=Path, help='archivo de estado de los avisos enviados (omisión: ~/.local/state/fcmo-studio-notify/ledger.json)')
    parser.add_argument('--sembrar', action='store_true', help='marcar los eventos actuales como ya avisados, sin enviar nada (primera corrida)')
    parser.add_argument('--enviar', action='store_true', help='encolar de verdad; sin esto sólo muestra')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    ledger = args.ledger or Path.home() / '.local/state/fcmo-studio-notify/ledger.json'
    try:
        report = run(args.data, args.mensajeria, ledger, args.enviar, sembrar=args.sembrar)
    except sqlite3.Error as error:
        print(f'notify: base de Studio no legible ({type(error).__name__})', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        if args.sembrar:
            print(f"avisos (sembrado): {report['sembrados']} evento(s) marcados sin enviar, {report['ya_enviados']} ya estaban")
        elif args.enviar:
            print(f"avisos: {report['eventos']} evento(s), {report['encolados']} encolado(s), {report['ya_enviados']} ya enviado(s)")
        else:
            print(f"avisos (dry run): {report['eventos']} evento(s), {len(report['detalle'])} por encolar, {report['ya_enviados']} ya enviado(s)")
        for line in report['detalle']:
            print(f"  → {line['para']}: {line['texto']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
