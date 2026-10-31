"""D / Libro de evidencias. Pure, localized components over the public record.

A source grade describes a source, never proof of a claim. The current story
schema has no claim-to-source edges: the diagram preserves two lists rather
than manufacturing a fully connected network.
"""
from html import escape
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlsplit

from ..i18n import format_date, label, plural
from ..front_plan import evidence_class, class_counts


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
    return f'<span class="d-claim">{sample(kind)}<strong>{e(word)}</strong></span>'


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


def signals_rich(story, catalog, *, evidence=None):
    """Cover variant (R4): each signal carries a sans value over a mono caption."""
    ev = evidence if isinstance(evidence, dict) else (story.get('evidence') or {})
    cp = copy(catalog)
    st = catalog['strings']
    primary = sum(bool(s.get('primary')) for s in rows(story.get('sources')))
    gaps = len(ev.get('gaps') or [])
    kind = evidence_class(story)
    raw = {'shown': 'DEMONSTRATED', 'claimed': 'CLAIMED'}.get(kind, '')
    pk = proof_kind(raw)
    letter = story.get('evidence_class')
    letter = letter if letter in ('A', 'B', 'C', 'D') else '?'
    text = label(catalog, 'evidence_short', letter) if letter != '?' else st['evidence_board']['unrated']
    word = st['proof'][pk.replace('-', '_')]
    def noun(key, n):
        return plural(catalog, key, n).replace(str(n), '', 1).strip()
    return (f'<div class="d-signals d-signals--rich" data-evidence-class="{e(kind)}">'
            f'<span class="d-sig"><b class="d-sig-grade">{e(letter)}</b><span class="d-sig-text"><span>{e(text)}</span><small>{e(cp["source_grade"])}</small></span></span>'
            f'<span class="d-sig">{sample(pk)}<span class="d-sig-text"><strong>{e(word)}</strong><small>{e(cp["claim_status"])}</small></span></span>'
            f'<span class="d-sig"><b class="d-sig-num">{primary}</b><span class="d-sig-text"><span>{e(noun("primary_source", primary))}</span><small>{e(st["story"]["sources"])}</small></span></span>'
            f'<span class="d-sig"><b class="d-sig-num">{gaps}</b><span class="d-sig-text"><span>{e(noun("open_gap", gaps))}</span><small>{e(st["proof"]["not_established"])}</small></span></span></div>')


def section(title, ident=''):
    return f'<h2 class="d-section"{f' id="{e(ident)}"' if ident else ""}>{e(title)}</h2>'


def legend(catalog, *, stories=None, method_href=''):
    p = catalog['strings']['proof']
    items = ''.join(f'<div>{sample(k)}<div><b>{e(p[k.replace("-", "_")])}</b><p>{e(p[k.replace("-", "_") + "_desc"])}</p></div></div>'
                    for k in ('shown', 'claimed', 'not-established'))
    gap = '' if catalog.get('locale') == 'zh-Hans' else ' '
    title = gap.join(p[k] for k in ('band_shown', 'band_claimed', 'band_not_established'))
    if stories is not None:
        counts = class_counts(stories)
        cells = ''.join(f'<div><b>{e(p[k])} · {e(plural(catalog,"story",counts[k]))}</b>'
                        f'{sample(k.replace("_","-"))}<p>{e(p[k+"_desc"])}</p></div>'
                        for k in ('shown','claimed','not_established'))
        totals = (len(stories), len({t for s in stories for t in s.get('topics',[])}),
                  len({o for s in stories for o in s.get('organizations',[])}))
        nums = ''.join(f'<li>{n}<span>{e(catalog["strings"]["stat"][k+"_label"])}</span></li>'
                       for n,k in zip(totals,('stories','topics','organizations')))
        return (f'<section class="method-band" id="method-band"><div class="d-legend"><h2>{e(title)}</h2>'
                f'<div class="band-trio">{cells}</div><p class="band-note">{e(p["count_note"])}</p>'
                f'<ul class="band-counts">{nums}</ul>'
                f'<a href="{e(method_href)}">{e(catalog["strings"]["board"]["how_ordered"])}</a></div></section>')
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
    """R4 «Sources and claims»: claims at the left (short, the full text is in the ledger), sources and
    open gaps (dashed) at the right. The schema has no claim-to-source edges, so no individual edge is drawn."""
    st = catalog['strings']['story']
    claims = ''.join(f'<li><b>{i:02d}</b><span class="d-clamp">{e(c.get("text"))}</span></li>' for i, c in enumerate(rows(evidence.get('claims')), 1))
    letter = story.get('evidence_class')
    mark = f'<b class="d-src-grade">{e(letter)}</b>' if letter in ('A', 'B', 'C', 'D') else ''
    sources = ''.join(f'<li class="d-src">{_source(s)}' + (f'<small>{mark}{e(st["primary_source"])}</small>' if s.get('primary') else '') + '</li>' for s in rows(story.get('sources')))
    gaps = ''.join(f'<li class="d-gap"><span class="d-clamp">{e(g.get("description", "") if isinstance(g, dict) else g)}</span></li>' for g in (evidence.get('gaps') or []))
    if not claims and not sources:
        return ''
    return (f'<section class="d-claims-sources" id="sources">{section(st["sources"] + " / " + st["evidence"])}'
            f'<div><div><h3>{e(st["evidence"])}</h3><ol>{claims}</ol></div><div><h3>{e(st["sources"])}</h3><ol class="source-list">{sources}{gaps}</ol></div></div></section>')


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


def evidence_glance(story, catalog, *, evidence, title, max_sources=2, max_gaps=2):
    """Front-page map in the approved R4 form: a few short boxes joined by lines.

    primary source(s) -> the headline claim (never a fabricated claim) -> open gaps (dashed).
    Boxes have fixed heights and clamp their text; what does not fit is counted, never dropped silently
    (the full record is on the story page and in the SVG description). Nothing is invented: no source,
    gap or date appears unless it is in the data.
    """
    st = catalog['strings']['story']
    sources = rows(story.get('sources'))
    primaries = [s for s in sources if s.get('primary')] or sources
    shown_sources = primaries[:max_sources]
    gaps = [g.get('description', '') if isinstance(g, dict) else str(g) for g in (evidence.get('gaps') or [])]
    shown_gaps = gaps[:max_gaps]
    W, G = 600, 20
    out, desc, y = [], [], 4
    letter = story.get('evidence_class')
    letter = letter if letter in ('A', 'B', 'C', 'D') else ''
    def box(kind, x, y, w, h, head, text, foot='', mark=''):
        inner = (f'<b>{e(head)}</b>' + (f'<span class="d-map-row">{mark}<span class="d-map-text">{e(text)}</span></span>' if text else '')
                 + (f'<i>{e(foot)}</i>' if foot else ''))
        return (f'<foreignObject data-node="{kind}" x="{x}" y="{y}" width="{w}" height="{h}">'
                f'<div xmlns="http://www.w3.org/1999/xhtml" class="d-map-node d-map-node--{kind}">{inner}</div></foreignObject>')
    n = len(shown_sources)
    sw = 340 if n == 1 else (W - G) // 2
    sh = 124
    xs = []
    for i, src in enumerate(shown_sources):
        x = (W - sw) // 2 if n == 1 else i * (sw + G)
        name = src.get('title') or src.get('domain') or src.get('url') or ''
        mark = f'<b class="d-map-grade">{e(letter)}</b>' if letter else ''
        out.append(box('source', x, y, sw, sh, st['primary_source'] if src.get('primary') else st['sources'], name, mark=mark))
        desc.append(name); xs.append(x + sw // 2)
    if n:
        y += sh
    extra = len(primaries) - n
    claim_y = y + (34 if n else 0)
    ch = 150
    head = title
    claim_x, claim_w = 40, W - 80
    if n:
        edges = ''.join(f'M{x} {y}V{y+17}' for x in xs)
        out.append(f'<path class="d-map-edge" d="{edges}M{xs[0]} {y+17}H{xs[-1]}M{W//2} {y+17}V{claim_y}"/>')
    out.append(box('claim', claim_x, claim_y, claim_w, ch, '', head))
    desc.insert(0, title)
    y = claim_y + ch
    gy = y + 38
    if shown_gaps:
        gw = 340 if len(shown_gaps) == 1 else (W - G) // 2
        gxs = []
        gh = 196
        for i, text in enumerate(shown_gaps):
            x = (W - gw) // 2 if len(shown_gaps) == 1 else i * (gw + G)
            out.append(box('gap', x, gy, gw, gh, plural(catalog, 'open_gap_noun', 1),
                           text, foot=catalog['strings']['proof']['not_established']))
            desc.append(text); gxs.append(x + gw // 2)
        edges = ''.join(f'M{x} {gy-17}V{gy}' for x in gxs)
        out.append(f'<path class="d-map-edge d-map-edge--gap" d="M{W//2} {y}V{gy-17}{"M%d %d" % (gxs[0], gy-17)}H{gxs[-1]}{edges}"/>')
        y = gy + gh
    notes = []
    if extra > 0:
        notes.append(plural(catalog, 'primary_source', extra))
    if len(gaps) > len(shown_gaps):
        notes.append(plural(catalog, 'open_gap', len(gaps) - len(shown_gaps)))
    if notes:
        out.append(f'<foreignObject x="0" y="{y+8}" width="{W}" height="28"><div xmlns="http://www.w3.org/1999/xhtml" class="d-map-more">+ {e(" · + ".join(notes))}</div></foreignObject>')
        y += 40
    edges = [o for o in out if o.startswith('<path')]
    nodes = [o for o in out if not o.startswith('<path')]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="d-evidence-map d-evidence-glance" viewBox="0 0 {W} {y+4}" role="img" aria-label="{e(st["evidence"])}">'
            f'<title>{e(title)}</title><desc>{e(" / ".join(desc))}</desc>{"".join(edges+nodes)}</svg>')


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


def _topic_signal_fallback(key):
    """Unmapped topics: keyword family, then a stable hash, so the column keeps R4's colour per topic."""
    if not key:
        return 'stone'
    for words, signal in ((('infra', 'chip', 'hardware', 'compute', 'cloud', 'energy', 'data'), 'foundry'),
                          (('polic', 'govern', 'regul', 'law', 'society', 'robot', 'health', 'bio', 'education', 'work'), 'living'),
                          (('agent', 'model', 'eval', 'safety', 'secur', 'research', 'reason', 'learning', 'align'), 'intelligence')):
        if any(w in key for w in words):
            return signal
    return ('foundry', 'living', 'intelligence')[int.from_bytes(hashlib.sha256(key.encode()).digest()[:2], 'big') % 3]


def topic_signal(story, catalog):
    labels = catalog.get('labels', {}).get('topic', {})
    key = next((t for t in story.get('topics', []) if t in labels), '')
    return key, _TOPIC_SIGNALS.get(key) or _topic_signal_fallback(key or next(iter(story.get('topics', [])), ''))


def topic(story, catalog):
    """True colors only on a small signal. Unmapped topics stay Stone."""
    labels = catalog.get('labels', {}).get('topic', {})
    key, signal = topic_signal(story, catalog)
    text = labels.get(key) or label(catalog, 'beat', story.get('beat'))
    return f'<span class="d-topic"><i class="d-topic-signal d-topic-signal--{signal}" aria-hidden="true"></i>{e(text)}</span>'


# D interface copy only. Editorial prose and all factual values come from records.
COPY = {
    'en': {'source_note': 'A source grade describes the source, not the truth of a claim.', 'timeline': 'Timeline', 'editions': 'Editions', 'filters': 'Filters', 'archive_intro': 'Every edition is a dated snapshot. Corrections are appended, never rewritten.', 'all': 'All', 'stories': 'Stories', 'filter_scope': 'Filter stories on this page', 'process': 'Our editorial process', 'col_image': 'Image', 'col_topic': 'Topic', 'col_story': 'Story', 'col_gaps': 'Gaps', 'source_grade': 'Source grade', 'claim_status': 'Claim status'},
    'es-419': {'source_note': 'El grado describe la fuente, no la veracidad de una afirmación.', 'timeline': 'Cronología', 'editions': 'Ediciones', 'filters': 'Filtros', 'archive_intro': 'Cada edición es un registro fechado. Las correcciones se añaden, nunca se reescriben.', 'all': 'Todos', 'stories': 'Historias', 'filter_scope': 'Filtrar las historias de esta página', 'process': 'Nuestro proceso editorial', 'col_image': 'Imagen', 'col_topic': 'Tema', 'col_story': 'Historia', 'col_gaps': 'Huecos', 'source_grade': 'Grado de la fuente', 'claim_status': 'Estado de la afirmación'},
    'zh-Hans': {'source_note': '来源评级描述的是来源，而非主张的真实性。', 'timeline': '时间线', 'editions': '各期刊物', 'filters': '筛选', 'archive_intro': '每期都是带有日期的记录。更正以追加方式保留，不会覆盖原文。', 'all': '全部', 'stories': '报道', 'filter_scope': '筛选本页报道', 'process': '编辑流程', 'col_image': '图片', 'col_topic': '主题', 'col_story': '报道', 'col_gaps': '空白', 'source_grade': '来源评级', 'claim_status': '主张状态'},
}

# Method page copy (R4 «Cómo trabajamos»).
_METHOD_COPY = {'en': {'method_dek': 'How an automated research desk separates evidence from importance.', 'grades_kicker': 'Three grades of evidence', 'grades_count': 'Across {n} published stories.', 'class_long_shown': 'A claim is Shown when it is supported by primary, verifiable evidence such as official documents, datasets or direct statements. The source is traceable and available to the reader.', 'class_long_claimed': 'A claim is Claimed when it is based on secondary sources, statements or reports that have not yet been independently verified.', 'class_long_not_established': 'A claim is Not established when available evidence is insufficient, contradictory or not independently reproduced.', 'example': 'Example', 'source': 'Source', 'no_example': 'No claim of this grade in the current record.', 'flow': (('Sources', 'We collect and track'), ('Claims', 'We extract and normalize'), ('Evidence grade', 'We assess and label'), ('Importance', 'We judge significance'), ('Edition', 'We curate and publish')), 'imp_kicker': 'Importance and evidence', 'imp_title': 'Importance is not confidence.', 'imp_body': 'A claim can be highly important and still be unverified. Evidence tells us how well a claim is supported. Importance tells us why it matters.', 'axis_y_hi': 'Higher importance', 'axis_y_lo': 'Lower importance', 'axis_x_lo': 'Lower evidence', 'axis_x_hi': 'Higher evidence', 'chart_note': 'Illustration of the idea, not a measurement.', 'registry': 'Topic registry', 'reg': (('foundry', 'Foundry', 'Compute, infrastructure, hardware.'), ('living', 'Living', 'Biology, society, policy.'), ('intelligence', 'Intelligence', 'Models, agents, research.'))}, 'es-419': {'method_dek': 'Cómo una redacción de investigación automatizada separa la evidencia de la importancia.', 'grades_kicker': 'Tres grados de evidencia', 'grades_count': 'Sobre {n} historias publicadas.', 'class_long_shown': 'Una afirmación es Demostrada cuando la respaldan evidencias primarias y verificables, como documentos oficiales, conjuntos de datos o declaraciones directas. La fuente es rastreable y está al alcance del lector.', 'class_long_claimed': 'Una afirmación es Afirmada cuando se basa en fuentes secundarias, declaraciones o informes que aún no se han verificado de forma independiente.', 'class_long_not_established': 'Una afirmación está No establecida cuando la evidencia disponible es insuficiente, contradictoria o no se ha reproducido de forma independiente.', 'example': 'Ejemplo', 'source': 'Fuente', 'no_example': 'Ninguna afirmación de este grado en el registro actual.', 'flow': (('Fuentes', 'Reunimos y seguimos'), ('Afirmaciones', 'Extraemos y normalizamos'), ('Grado de evidencia', 'Evaluamos y etiquetamos'), ('Importancia', 'Juzgamos la relevancia'), ('Edición', 'Curamos y publicamos')), 'imp_kicker': 'Importancia y evidencia', 'imp_title': 'Importancia no es confianza.', 'imp_body': 'Una afirmación puede ser muy importante y seguir sin verificarse. La evidencia dice qué tan bien está respaldada. La importancia dice por qué importa.', 'axis_y_hi': 'Mayor importancia', 'axis_y_lo': 'Menor importancia', 'axis_x_lo': 'Menos evidencia', 'axis_x_hi': 'Más evidencia', 'chart_note': 'Ilustración de la idea, no una medición.', 'registry': 'Registro de temas', 'reg': (('foundry', 'Foundry', 'Cómputo, infraestructura, hardware.'), ('living', 'Living', 'Biología, sociedad, políticas.'), ('intelligence', 'Intelligence', 'Modelos, agentes, investigación.'))}, 'zh-Hans': {'method_dek': '自动化研究编辑部如何把证据与重要性区分开来。', 'grades_kicker': '证据的三个等级', 'grades_count': '基于 {n} 篇已发布报道。', 'class_long_shown': '当主张有一手、可核查的证据支持时，即为“已展示”，例如官方文件、数据集或直接表态。来源可追溯，读者可自行查阅。', 'class_long_claimed': '当主张基于尚未经独立核实的二手来源、声明或报告时，即为“仅声称”。', 'class_long_not_established': '当现有证据不足、相互矛盾或未经独立复现时，该主张“尚未确立”。', 'example': '示例', 'source': '来源', 'no_example': '当前记录中没有该等级的主张。', 'flow': (('来源', '收集并跟踪'), ('主张', '提取并规范化'), ('证据等级', '评估并标注'), ('重要性', '判断意义'), ('版次', '筛选并发布')), 'imp_kicker': '重要性与证据', 'imp_title': '重要不等于可信。', 'imp_body': '一项主张可能非常重要，却仍未经证实。证据说明主张得到多大程度的支持；重要性说明它为什么值得关注。', 'axis_y_hi': '重要性更高', 'axis_y_lo': '重要性更低', 'axis_x_lo': '证据更少', 'axis_x_hi': '证据更多', 'chart_note': '仅为概念示意，并非测量数据。', 'registry': '主题登记', 'reg': (('foundry', 'Foundry', '算力、基础设施、硬件。'), ('living', 'Living', '生物、社会、政策。'), ('intelligence', 'Intelligence', '模型、智能体、研究。'))}}
_METHOD_COPY_ARCHIVE = {'en': {'col_date': 'Date', 'col_count': '#', 'col_evidence': 'Evidence (by story)', 'col_topics': 'Topics', 'col_lead': 'Lead', 'open_edition': 'Open edition', 'older_editions': 'Older editions', 'story_index': 'Story index', 'story_index_note': 'All {n} stories, newest first. Filters apply here.', 'corr_log': 'Corrections log', 'corr_intro': 'Recent corrections and clarifications to published editions.', 'view_all': 'View all corrections', 'view': 'View', 'feeds_intro': 'Machine-readable feeds of all editions, corrections and metadata.', 'number_stories': 'Number = stories', 'withdrawn': 'Withdrawn'}, 'es-419': {'col_date': 'Fecha', 'col_count': '#', 'col_evidence': 'Evidencia (por historia)', 'col_topics': 'Temas', 'col_lead': 'Portada', 'open_edition': 'Abrir edición', 'older_editions': 'Ediciones anteriores', 'story_index': 'Índice de historias', 'story_index_note': 'Las {n} historias, de la más reciente a la más antigua. Los filtros se aplican aquí.', 'corr_log': 'Registro de correcciones', 'corr_intro': 'Correcciones y aclaraciones recientes a las ediciones publicadas.', 'view_all': 'Ver todas las correcciones', 'view': 'Ver', 'feeds_intro': 'Canales legibles por máquina de todas las ediciones, correcciones y metadatos.', 'number_stories': 'Número = historias', 'withdrawn': 'Retirada'}, 'zh-Hans': {'col_date': '日期', 'col_count': '#', 'col_evidence': '证据（按报道）', 'col_topics': '主题', 'col_lead': '头条', 'open_edition': '打开本期', 'older_editions': '更早各期', 'story_index': '报道索引', 'story_index_note': '全部 {n} 篇报道，由新到旧。筛选作用于此处。', 'corr_log': '更正记录', 'corr_intro': '对已发布各期的近期更正与说明。', 'view_all': '查看全部更正', 'view': '查看', 'feeds_intro': '所有各期、更正与元数据的机器可读订阅源。', 'number_stories': '数字 = 报道数', 'withdrawn': '已撤回'}}
for _loc, _vals in _METHOD_COPY_ARCHIVE.items():
    COPY[_loc].update(_vals)
for _loc, _vals in _METHOD_COPY.items():
    COPY[_loc].update(_vals)


def copy(catalog):
    return COPY[catalog['locale']]
