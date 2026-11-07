"""D / Libro de evidencias: the Topics index and the heading of each topic page.

Everything printed comes from the live stories of the build: a topic is listed only when it has a page
(at least TOPIC_PAGE_MIN stories) and a catalogue name in the reader's language; counts, dates, titles and
evidence classes are read from those stories, never composed.
"""
from collections import Counter

from . import d_components as d
from .. import d_plates
from ..front_plan import evidence_class
from ..i18n import format_date, headline, label, plural
from ..routes import href

TOPIC_PAGE_MIN = 3   # build.py writes topic/<slug>/ only for topics with at least this many stories
FEATURED = 6          # per family: the busiest topics get a card with an image; the rest stay in the table
FAMILIES = ('foundry', 'living', 'intelligence')

COPY = {
    'en': {'latest': 'Latest story', 'family_all': 'All {family} topics', 'back': 'All topics', 'family_of': 'Family',
           'col_topic': 'Topic', 'col_stories': 'Stories', 'col_latest': 'Latest', 'col_evidence': 'Evidence',
           'jump': 'Topic families', 'in_family': '{topics} · {stories}', 'topics_stories': '{topics} · {stories}',
           'how': 'How to read FCMO AI', 'method': 'Method', 'note': 'A topic appears here once it has three or more published stories.'},
    'es-419': {'latest': 'Última historia', 'family_all': 'Todos los temas de {family}', 'back': 'Todos los temas', 'family_of': 'Familia',
               'col_topic': 'Tema', 'col_stories': 'Historias', 'col_latest': 'Reciente', 'col_evidence': 'Evidencia',
               'jump': 'Familias de temas', 'in_family': '{topics} · {stories}', 'topics_stories': '{topics} · {stories}',
               'how': 'Cómo leer FCMO AI', 'method': 'Método', 'note': 'Un tema aparece aquí cuando tiene tres o más historias publicadas.'},
    'zh-Hans': {'latest': '最新报道', 'family_all': '{family}的全部主题', 'back': '全部主题', 'family_of': '类别',
                'col_topic': '主题', 'col_stories': '报道', 'col_latest': '最新', 'col_evidence': '证据',
                'jump': '主题类别', 'in_family': '{topics} · {stories}', 'topics_stories': '{topics} · {stories}',
                'how': '如何阅读 FCMO AI', 'method': '方法', 'note': '主题发布三篇及以上报道后才会出现在这里。'},
}


def family_of(slug):
    return d._TOPIC_SIGNALS.get(slug) or d._topic_signal_fallback(slug)


def collect(stories, catalog):
    """One record per listed topic: name, family, count and its newest story (by event date)."""
    names = catalog.get('labels', {}).get('topic', {})
    counts = Counter(t for s in stories for t in set(s.get('topics') or []))
    newest = {}
    for s in stories:
        key = (s.get('event_at', ''), s['id'])
        for t in set(s.get('topics') or []):
            if t not in newest or key > (newest[t].get('event_at', ''), newest[t]['id']):
                newest[t] = s
    out = []
    for slug, n in counts.items():
        if n >= TOPIC_PAGE_MIN and slug in names:
            out.append({'slug': slug, 'name': names[slug], 'count': n, 'family': family_of(slug), 'latest': newest[slug]})
    out.sort(key=lambda r: (-r['count'], r['name'].casefold(), r['slug']))
    return out


def _signal(family, big=False):
    return f'<i class="d-topic-signal d-topic-signal--{family}{" d-tx-big" if big else ""}" aria-hidden="true"></i>'


def _family_name(catalog, family):
    return d.copy(catalog)[f'key_{family}_name']


def _proof(story, catalog):
    kind = evidence_class(story)
    word = catalog['strings']['proof'][kind]
    return f'<span class="d-claim">{d.sample(kind.replace("_", "-"))}<strong>{d.e(word)}</strong></span>'


def _when(story, catalog):
    return format_date(story['event_at'], catalog, precision=story.get('date_precision', 'day'))


def _time(story, catalog):
    return f'<time datetime="{d.e(story["event_at"])}">{d.e(_when(story, catalog))}</time>'


def topic_url(base, locale, slug):
    return href(base, locale['path_prefix'] + 'topic/' + slug + '/')


def _card(rec, *, catalog, locale, base, copy, story_href, seen):
    story = rec['latest']
    art = ''
    if story.get('media'):
        art = (f'<a class="d-tx-art" href="{d.e(story_href(story))}" tabindex="-1" aria-hidden="true">'
               f'{d_plates.html(story, "16:10", catalog["strings"], base, seen, thumb=True)}</a>')
    return (f'<li class="d-tx-card" data-topic="{d.e(rec["slug"])}" data-family="{rec["family"]}" data-count="{rec["count"]}">{art}'
            f'<div class="d-tx-card-body"><p class="d-tx-count"><b>{rec["count"]}</b><span>{d.e(plural(catalog, "story", rec["count"]).replace(str(rec["count"]), "", 1).strip())}</span></p>'
            f'<h3><a href="{d.e(topic_url(base, locale, rec["slug"]))}" translate="no">{d.e(rec["name"])}</a></h3>'
            f'<div class="d-tx-latest"><p class="d-tx-latest-label">{d.e(copy["latest"])} · {_time(story, catalog)}</p>'
            f'<a class="d-tx-latest-title" href="{d.e(story_href(story))}">{d.e(headline(story, locale["code"], catalog))}</a>'
            f'{_proof(story, catalog)}</div></div></li>')


def _row(rec, *, catalog, locale, base, story_href):
    story = rec['latest']
    return (f'<li class="d-tx-row" data-topic="{d.e(rec["slug"])}" data-family="{rec["family"]}" data-count="{rec["count"]}">'
            f'<a class="d-tx-row-name" href="{d.e(topic_url(base, locale, rec["slug"]))}" translate="no">{_signal(rec["family"])}<span>{d.e(rec["name"])}</span></a>'
            f'<span class="d-tx-row-count"><b>{rec["count"]}</b></span>'
            f'<span class="d-tx-row-when">{_time(story, catalog)}</span>'
            f'<span class="d-tx-row-proof">{_proof(story, catalog)}</span>'
            f'<a class="d-tx-row-title" href="{d.e(story_href(story))}">{d.e(headline(story, locale["code"], catalog))}</a></li>')


def index(records, stories, *, catalog, locale, base, story_href, method_href):
    """The /topic/ page body: header, family jump bar, one section per family, closing legend band."""
    strings = catalog['strings']
    copy = COPY[locale['code']]
    cp = d.copy(catalog)
    by_family = {f: [r for r in records if r['family'] == f] for f in FAMILIES}
    n_topics = len(records)
    slugs = {f: {r['slug'] for r in by_family[f]} for f in FAMILIES}
    # A story under topics of two families counts once in each family and once in the total.
    story_counts = {f: sum(1 for s in stories if slugs[f] & set(s.get('topics') or [])) for f in FAMILIES}
    n_stories = sum(1 for s in stories if any(slugs[f] & set(s.get('topics') or []) for f in FAMILIES))
    jump = ''.join(
        f'<a href="#{f}" class="d-tx-jump-{f}">{_signal(f)}<span><b>{d.e(_family_name(catalog, f))}</b>'
        f'<small>{d.e(plural(catalog, "topic", len(by_family[f])))}</small></span></a>'
        for f in FAMILIES if by_family[f])
    head = (f'<header class="d-page-header d-tx-head"><p class="section-kicker">FCMO AI · {d.e(strings["nav"]["topics"])}</p>'
            f'<h1 class="page-title d-page-title">{d.e(strings["topics"]["title"])}</h1><p>{d.e(strings["topics"]["dek"])}</p>'
            f'<ul class="archive-totals"><li><strong>{n_topics}</strong> {d.e(strings["stat"]["topics_label"])}</li>'
            f'<li><strong>{n_stories}</strong> {d.e(strings["stat"]["stories_label"])}</li></ul>'
            f'<p class="d-tx-note d-mono">{d.e(copy["note"])}</p>'
            f'<nav class="d-tx-jump" aria-label="{d.e(copy["jump"])}">{jump}</nav></header>')
    seen = {}
    sections = []
    for f in FAMILIES:
        recs = by_family[f]
        if not recs:
            continue
        name = _family_name(catalog, f)
        featured, rest = recs[:FEATURED], recs[FEATURED:]
        cards = ''.join(_card(r, catalog=catalog, locale=locale, base=base, copy=copy, story_href=story_href, seen=seen) for r in featured)
        table = ''
        if rest:
            col = (f'<div class="d-tx-rows-head" aria-hidden="true"><span>{d.e(copy["col_topic"])}</span><span>{d.e(copy["col_stories"])}</span>'
                   f'<span>{d.e(copy["col_latest"])}</span><span>{d.e(copy["col_evidence"])}</span><span>{d.e(cp["col_story"])}</span></div>')
            rows = ''.join(_row(r, catalog=catalog, locale=locale, base=base, story_href=story_href) for r in rest)
            table = (f'<details class="d-tx-more" open><summary>{d.e(copy["family_all"].format(family=name))} · {len(rest)}</summary>{col}<ol class="d-tx-rows">{rows}</ol></details>')
        sections.append(
            f'<section class="d-tx-family d-tx-family--{f}" id="{f}" aria-labelledby="{f}-title"><div class="frame">'
            f'<header class="d-tx-fhead">{_signal(f, True)}<div><h2 id="{f}-title">{d.e(name)}</h2><p>{d.e(cp["key_" + f])}</p></div>'
            f'<span class="d-mono">{d.e(plural(catalog, "topic", len(recs)))} · {d.e(plural(catalog, "story", story_counts[f]))}</span></header>'
            f'<ol class="d-tx-cards">{cards}</ol>{table}</div></section>')
    legend = d.legend(catalog)
    band = (f'<section class="d-bone d-tx-band"><div class="frame">{legend}'
            f'<p><a href="{d.e(method_href)}">{d.e(copy["method"])} →</a></p></div></section>')
    return head + '<div class="d-tx">' + ''.join(sections) + '</div>' + band


def header(rec, *, catalog, locale, base, index_href, orgs_total):
    """Heading of one topic page: family, name, count, newest date, and the way back to the index."""
    copy = COPY[locale['code']]
    strings = catalog['strings']
    family = rec['family']
    latest = rec['latest']
    return (f'<header class="d-page-header d-tx-topic-head d-tx-family--{family}"><nav class="d-tx-back"><a href="{d.e(index_href)}">← {d.e(copy["back"])}</a></nav>'
            f'<p class="section-kicker d-tx-fam">{_signal(family)}<a href="{d.e(index_href)}#{family}">{d.e(_family_name(catalog, family))}</a></p>'
            f'<h1 class="page-title d-page-title" translate="no">{d.e(rec["name"])}</h1>'
            f'<ul class="archive-totals"><li><strong>{rec["count"]}</strong> {d.e(strings["stat"]["stories_label"])}</li>'
            f'<li><strong>{orgs_total}</strong> {d.e(strings["stat"]["organizations_label"])}</li>'
            f'<li class="d-tx-latest-meta">{d.e(copy["latest"])} · {_time(latest, catalog)} {_proof(latest, catalog)}</li></ul></header>')
