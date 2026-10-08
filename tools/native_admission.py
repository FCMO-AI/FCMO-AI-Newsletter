"""One strict native-edition admission decision for ingest and the Story layer.

Received source and rejected overlays remain in corpus, so a later valid airlock
automatically clears a hold. No translation or inferred importance is performed.
"""
import json
from pathlib import Path

try:
    from tools.validate_localizations import LOCALES, effective_overlays_details, is_complete, pair_status, load_locale_details
except ImportError:
    from validate_localizations import LOCALES, effective_overlays_details, is_complete, pair_status, load_locale_details


def native_holds(corpus: Path, records: list[dict], i18n_dir: Path, *, incoming: bool = True) -> dict[str, str]:
    holds: dict[str, list[str]] = {}
    for locale in LOCALES:
        rows, strict, provenance, _ = (effective_overlays_details(locale, i18n_dir, corpus) if incoming
                                       else load_locale_details(i18n_dir, locale))
        for source in records:
            rid = source['id']
            status = pair_status(source, rows.get(rid), locale, strict=rid in strict, provenance=provenance.get(rid))
            if not is_complete(status):
                reason = (status.get('failure') or {}).get('gate') or status['state']
                holds.setdefault(rid, []).append(f'{locale}:{reason}')
    return {rid: 'NATIVE_EDITION:' + ','.join(reasons) for rid, reasons in holds.items()}


def published_sources(release_src: Path) -> dict[str, dict]:
    """The exact English versions in the composed publication, including carries."""
    return {path.stem: json.loads(path.read_text(encoding='utf-8'))['brief']
            for path in (release_src / 'data/briefs').glob('FCMO-*.json')}


def select_native(corpus: Path, records: list[dict], i18n_dir: Path,
                  previous: dict[str, dict] | None = None):
    holds = native_holds(corpus, records, i18n_dir)
    old = [row for rid, row in (previous or {}).items() if rid in holds]
    unsafe_old = native_holds(corpus, old, i18n_dir, incoming=False)
    carried = {row['id']: row for row in old if row['id'] not in unsafe_old}
    selected = [carried[row['id']] if row['id'] in carried else row
                for row in records if row['id'] not in holds or row['id'] in carried]
    return selected, holds, set(carried)
