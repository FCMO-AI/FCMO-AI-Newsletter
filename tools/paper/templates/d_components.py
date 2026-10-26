"""D / Libro de evidencias. Pure, localized components over the public record.

A source grade describes a source, never proof of a claim. The current story
schema has no claim-to-source edges: the diagram preserves two lists rather
than manufacturing a fully connected network.
"""
from html import escape
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from ..i18n import format_date, label, plural
from ..front_plan import evidence_class


def e(value):
    return escape(str(value if value is not None else ''), quote=True)


def rows(value):
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def proof_kind(raw):
    value = str(raw or '')
    if value.startswith('DEMONSTRATED') or value == 'SHOWN':
        return 'shown'
    if value.startswith(('CLAIMED', 'VENDOR', 'GOVERNMENT', 'FIRST_PARTY', 'PRIMARY_EXTRAORDINARY')) or value.endswith('_CLAIM'):
        return 'claimed'
    return 'not-established'


def sample(kind):
    # Actual strokes, not a decorative gradient. The grammar survives monochrome.
    kind = kind if kind in ('shown', 'claimed') else 'not-established'
    strokes = ''.join(f'<path d="M{x} 24l24-24"/>' for x in range(-24, 25, 5)) if kind == 'claimed' else ''
    return (f'<span class="d-sample d-claim--{kind}" aria-hidden="true">'
            f'<svg viewBox="0 0 24 24" focusable="false">{strokes}</svg></span>')


def claim(raw, catalog):
    kind = proof_kind(raw)
    word = catalog['strings']['proof'][kind.replace('-', '_')]
    return f'<span class="d-claim">{sample(kind)}<span>{e(word)}</span></span>'


def grade(story, catalog):
    letter = story.get('evidence_class')
    letter = letter if letter in ('A', 'B', 'C', 'D') else '?'
    text = label(catalog, 'evidence_short', letter) if letter != '?' else catalog['strings']['evidence_board']['unrated']
    return f'<span class="d-grade"><b>{letter}</b><span>{e(text)}</span></span>'


def stat(number, text):
    text = text.replace(str(number), "", 1).strip()
    return f'<span class="d-stat"><b>{e(number)}</b><span>{e(text)}</span></span>'


def signals(story, catalog, *, evidence=None):
    ev = evidence if isinstance(evidence, dict) else (story.get('evidence') or {})
    primary = sum(bool(s.get('primary')) for s in rows(story.get('sources')))
    gaps = len(ev.get('gaps') or [])
    kind = evidence_class(story)
    raw = {'shown': 'DEMONSTRATED', 'claimed': 'CLAIMED'}.get(kind, '')
    return (f'<div class="d-signals" data-evidence-class="{e(kind)}">{grade(story, catalog)}{claim(raw, catalog)}'
            f'{stat(primary, plural(catalog, "primary_source", primary))}'
            f'{stat(gaps, plural(catalog, "open_gap", gaps))}</div>')


def section(title, ident=''):
    return f'<h2 class="d-section"{f' id="{e(ident)}"' if ident else ""}>{e(title)}</h2>'


def legend(catalog):
    p = catalog['strings']['proof']
    items = ''.join(f'<div>{sample(k)}<div><b>{e(p[k.replace("-", "_")])}</b><p>{e(p[k.replace("-", "_") + "_desc"])}</p></div></div>'
                    for k in ('shown', 'claimed', 'not-established'))
    gap = '' if catalog.get('locale') == 'zh-Hans' else ' '
    title = gap.join(p[k] for k in ('band_shown', 'band_claimed', 'band_not_established'))
    return f'<section class="d-legend"><h2>{e(title)}</h2><div class="d-legend-items">{items}</div></section>'


def ledger(evidence, catalog):
    items = []
    for i, item in enumerate(rows(evidence.get('claims')), 1):
        items.append(f'<li data-ledger-item="{i}"><b class="d-number">{i:02d}</b><div>{claim(item.get("label"), catalog)}<p>{e(item.get("text"))}</p></div></li>')
    body = f'<ol>{"".join(items)}</ol>' if items else f'<p>{e(catalog["strings"]["record"]["none"])}</p>'
    return f'<section class="d-ledger" id="claims">{section(catalog["strings"]["ledger"]["title"])}{body}</section>'


def _source(source):
    url = str(source.get('url') or '')
    name = source.get('title') or source.get('organization') or source.get('domain') or url
    try:
        safe = urlsplit(url).scheme in ('https', 'http') and bool(urlsplit(url).netloc)
    except ValueError:
        safe = False
    link = f'<a href="{e(url)}" rel="noopener noreferrer">{e(name)} ↗</a>' if safe else e(name)
    attribution = []
    for value in (source.get('author'), source.get('organization'), source.get('outlet'),
                  source.get('published_at') or source.get('date')):
        if value and value != name and value not in attribution:
            attribution.append(value)
    return link + (f'<small>{e(" · ".join(attribution))}</small>' if attribution else '')


def claims_sources(story, evidence, catalog):
    st = catalog['strings']['story']
    claims = ''.join(f'<li><b>{i:02d}</b><span>{e(c.get("text"))}</span></li>' for i, c in enumerate(rows(evidence.get('claims')), 1))
    sources = ''.join(f'<li>{_source(s)}' + (f'<small>{e(st["primary_source"])}</small>' if s.get('primary') else '') + '</li>' for s in rows(story.get('sources')))
    if not claims and not sources:
        return ''
    return (f'<section class="d-claims-sources" id="sources">{section(st["sources"] + " / " + st["evidence"])}'
            f'<div><div><h3>{e(st["evidence"])}</h3><ol>{claims}</ol></div><div><h3>{e(st["sources"])}</h3><ol class="source-list">{sources}</ol></div></div></section>')


def evidence_map(story, catalog, *, evidence, title):
    """Sources, claims and open gaps; no undocumented claim/source edges.

    Nodes wrap rather than ellipsize. Row heights grow with their content, and
    the two-column grid keeps many sources and gaps from becoming a single chain.
    The full text is also present in the SVG's accessible description.
    """
    st = catalog['strings']['story']
    sources = rows(story.get('sources'))
    gaps = evidence.get('gaps') or []
    claims = rows(evidence.get('claims'))
    width, box, gutter = 600, 276, 24
    out = []
    def height(text):
        units = sum(2 if ord(c) > 255 else 1 for c in str(text))
        return 64 + math.ceil(units / 21) * 27
    def node(kind, x, y, text, head, h, w=box):
        return (f'<foreignObject data-node="{kind}" x="{x}" y="{y}" width="{w}" height="{h}">'
                f'<div xmlns="http://www.w3.org/1999/xhtml" class="d-map-node d-map-node--{kind}">'
                f'<b>{e(head)}</b><span>{e(text)}</span></div></foreignObject>')
    y = 10
    descriptions = []
    for start in range(0, len(sources), 2):
        chunk = sources[start:start+2]
        names = [src.get('title') or src.get('domain') or src.get('url') or '' for src in chunk]
        h = max(height(name) for name in names)
        for col, (src, name) in enumerate(zip(chunk, names)):
            x = gutter//2 + col*(box+gutter)
            out.append(node('source', x, y, name, st['primary_source'] if src.get('primary') else st['sources'], h))
            out.append(f'<path class="d-map-edge" d="M{x+box/2} {y+h}v16H300"/>')
            descriptions.append(name)
        y += h+32
    claim_top = y+16
    if sources:
        out.append(f'<path class="d-map-edge" d="M300 10V{claim_top}"/>')
    y = claim_top
    if claims:
        for start in range(0, len(claims), 2):
            chunk = claims[start:start+2]
            names = [item.get('text', '') for item in chunk]
            h = max(height(name) for name in names)
            for col, (item, name) in enumerate(zip(chunk, names)):
                kind = proof_kind(item.get('label'))
                word = catalog['strings']['proof'][kind.replace('-', '_')]
                x, w = (48, 504) if len(claims) == 1 else (gutter//2+col*(box+gutter), box)
                out.append(node('claim', x, y, name, word, h, w))
                descriptions.append(name)
            y += h+24
    else:
        # The headline is context, never a fabricated claim.
        h = height(title)
        out.append(node('story', 48, y, title, st['what_changed'], h, 504))
        y += h+24
    claim_bottom = y-24
    y += 16
    for start in range(0, len(gaps), 2):
        chunk = gaps[start:start+2]
        names = [g.get('description', '') if isinstance(g, dict) else str(g) for g in chunk]
        h = max(height(name) for name in names)
        for col, name in enumerate(names):
            x = gutter//2+col*(box+gutter)
            out.append(f'<path class="d-map-edge d-map-edge--gap" d="M300 {claim_bottom}V{y-16}H{x+box/2}V{y}"/>')
            out.append(node('gap', x, y, name, catalog['strings']['proof']['not_established'], h))
            descriptions.append(name)
        y += h+32
    # Edges precede nodes, so connectors never run over the readable record.
    edges = [n for n in out if n.startswith('<path')]
    nodes = [n for n in out if not n.startswith('<path')]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="d-evidence-map" viewBox="0 0 {width} {y}" role="img" aria-label="{e(st["evidence"])}">'
            f'<title>{e(title)}</title><desc>{e(" / ".join(descriptions))}</desc>{"".join(edges+nodes)}</svg>')


def timeline(story, catalog):
    values = []
    st = catalog['strings']['story']
    for key, label_key in (('event_at', 'event_date'), ('first_published_at', 'published'), ('updated_at', 'updated')):
        value = story.get(key)
        if not value or any(v[0] == value for v in values):
            continue
        text = st.get(label_key, catalog['strings']['status_page']['checked'])
        date = format_date(value, catalog, precision='day')
        values.append((value, text.format(date=date)))
    if not values:
        return ''
    items = ''.join(f'<li><time datetime="{e(value)}">{e(text)}</time></li>' for value, text in values)
    return f'<ol class="d-timeline">{items}</ol>'


_TOPIC_SIGNALS = json.loads((Path(__file__).resolve().parents[3] / 'design/tokens.json').read_text())['d']['topic_signals']


def topic(story, catalog):
    """True colors only on a small signal. Unmapped topics stay Stone."""
    labels = catalog.get('labels', {}).get('topic', {})
    key = next((t for t in story.get('topics', []) if t in labels), '')
    signal = _TOPIC_SIGNALS.get(key, 'stone')
    text = labels.get(key) or label(catalog, 'beat', story.get('beat'))
    return f'<span class="d-topic"><i class="d-topic-signal d-topic-signal--{signal}" aria-hidden="true"></i>{e(text)}</span>'


# D interface copy only. Editorial prose and all factual values come from records.
COPY = {
    'en': {'source_note': 'A source grade describes the source, not the truth of a claim.', 'timeline': 'Timeline', 'editions': 'Editions', 'filters': 'Filters', 'archive_intro': 'Every edition is a dated snapshot. Corrections are appended, never rewritten.', 'all': 'All', 'stories': 'Stories', 'filter_scope': 'Filter stories on this page', 'process': 'Our editorial process'},
    'es-419': {'source_note': 'El grado describe la fuente, no la veracidad de una afirmación.', 'timeline': 'Cronología', 'editions': 'Ediciones', 'filters': 'Filtros', 'archive_intro': 'Cada edición es un registro fechado. Las correcciones se añaden, nunca se reescriben.', 'all': 'Todos', 'stories': 'Historias', 'filter_scope': 'Filtrar las historias de esta página', 'process': 'Nuestro proceso editorial'},
    'zh-Hans': {'source_note': '来源评级描述的是来源，而非主张的真实性。', 'timeline': '时间线', 'editions': '各期刊物', 'filters': '筛选', 'archive_intro': '每期都是带有日期的记录。更正以追加方式保留，不会覆盖原文。', 'all': '全部', 'stories': '报道', 'filter_scope': '筛选本页报道', 'process': '编辑流程'},
}


def copy(catalog):
    return COPY[catalog['locale']]
