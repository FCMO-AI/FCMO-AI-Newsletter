"""D archive and methodology; no wall clock, fabricated editions or example facts."""
import calendar
import re
from collections import Counter
from . import d_components as d
from ..i18n import field, format_date, headline, label, plural
from ..front_plan import evidence_class
from ..routes import href, story_path


FILTER_SCRIPT = """<script>(()=>{
const root=document.querySelector('[data-d-filters]');if(!root)return;
root.hidden=false;if(matchMedia('(max-width:760px)').matches)root.closest('details').open=false;
const rows=[...document.querySelectorAll('.archive-item')];
root.addEventListener('change',()=>{
 const idx=document.getElementById('story-index');if(idx&&root.querySelector('input:checked'))idx.open=true;
 const wanted={};root.querySelectorAll('input:checked').forEach(e=>(wanted[e.name]||=[]).push(e.value));
 rows.forEach(row=>{row.hidden=Object.entries(wanted).some(([key,values])=>{
 const actual=JSON.parse(row.getAttribute('data-d-'+key)||'[]');return !values.some(v=>actual.includes(v));
 });});
 document.querySelectorAll('.archive-day').forEach(day=>{day.hidden=![...day.querySelectorAll('.archive-item')].some(row=>!row.hidden)});
 const output=root.querySelector('output');output.textContent=rows.filter(row=>!row.hidden).length+' / '+rows.length;
});})();</script>"""


EDITIONS_SHOWN = 6


def count_html(text):
    head, sep, tail = str(text).partition(' ')
    return f'<i>{d.e(head)}</i><em>{d.e(sep + tail)}</em>' if sep else d.e(text)


def filters(stories, catalog):
    strings = catalog['strings']
    groups = []
    topics = Counter(t for s in stories for t in s.get('topics', []))
    organizations = Counter(o for s in stories for o in s.get('organizations', []))
    choices = [
        ('topics', strings['story']['topics'], [(t,label(catalog,'topic',t)) for t,n in topics.most_common() if label(catalog,'topic',t)][:8]),
        ('proof', strings['story']['evidence'], [(k,strings['proof'][k]) for k in ('shown','claimed','not_established')]),
        ('orgs', strings['story']['organizations'], [(o,o) for o,n in organizations.most_common(8)]),
    ]
    for group, title, values in choices:
        if not values:
            continue
        controls = ''.join(f'<label><input type="checkbox" name="{group}" value="{d.e(key)}">{d.sample(key.replace("_","-")) if group=="proof" else ""}<span>{d.e(text)}</span></label>' for key,text in values)
        groups.append(f'<fieldset><legend>{d.e(title)}</legend>{controls}</fieldset>')
    return (f'<details class="d-archive-filter-details" open><summary>{d.e(d.copy(catalog)["filters"])}</summary>'
            f'<form class="d-filters" data-d-filters hidden><p>{d.e(d.copy(catalog)["filter_scope"])}</p>{"".join(groups)}'
            '<output aria-live="polite"></output></form></details>')


def archive(*, dates, stories, locale, catalog, base, plate_html=""):
    counts = Counter(s['url_date'] for s in stories)
    months = sorted({day[:7] for day in dates}, reverse=True)
    sections = []
    for index, month in enumerate(months):
        year, number = map(int, month.split('-'))
        name = catalog['date']['patterns']['month_year'].format(month=catalog['date']['months'][number-1],year=year,month_number=number)
        days = []
        for week in calendar.Calendar(firstweekday=6).monthdayscalendar(year, number):
            for n in week:
                if not n:
                    days.append('<span class="d-calendar-blank" aria-hidden="true"></span>'); continue
                day = f'{month}-{n:02d}'
                if day in dates:
                    url = href(base,locale['path_prefix']+'edition/'+day+'/')
                    days.append(f'<a href="{d.e(url)}" data-edition-date="{day}" aria-label="{d.e(catalog["strings"]["archive"]["edition_title"].format(date=format_date(day,catalog)))}"><b>{n}</b><span>{count_html(plural(catalog,"story",counts[day]))}</span></a>')
                else:
                    days.append(f'<span class="d-calendar-empty"><b>{n}</b></span>')
        labels = ''.join(f'<span>{d.e(catalog["date"]["weekdays"][i])}</span>' for i in (6,0,1,2,3,4,5))
        sections.append(f'<details class="d-calendar-month"{" open" if index==0 else ""}><summary>{d.e(name)}</summary>'
                        f'<div class="d-calendar-week">{labels}</div><div class="d-calendar-grid">{"".join(days)}</div></details>')
    cp = d.copy(catalog)
    rows_visible, rows_more = [], []
    for index, day in enumerate(dates):
        values = [s for s in stories if s['url_date']==day]
        lead = values[0] if values else None
        title = headline(lead,locale['code'],catalog) if lead else catalog['strings']['archive']['empty']
        if len(values) <= 12:
            marks = ''.join(d.sample(evidence_class(s).replace('_','-')) for s in values)
        else:
            classes = Counter(evidence_class(s) for s in values)
            marks = ''.join(f'<span class="d-edition-count">{d.sample(k.replace("_","-"))}<span>{n}</span></span>' for k,n in classes.items())
        signals = []
        for story in values:
            signal = d.topic_signal(story, catalog)[1]
            if signal in ('foundry','living','intelligence') and signal not in signals:
                signals.append(signal)
        tops = ''.join(f'<i class="d-topic-signal d-topic-signal--{k}" aria-hidden="true"></i>' for k in ('foundry','living','intelligence') if k in signals)
        url = href(base,locale['path_prefix']+'edition/'+day+'/')
        row = (f'<li><time datetime="{day}">{d.e(format_date(day,catalog))}</time><span>{len(values)}</span><div class="d-edition-marks">{marks}</div>'
               f'<div class="d-edition-topics">{tops}</div><a class="d-edition-lead" href="{d.e(url)}">{d.e(title)}</a>'
               f'<a class="d-edition-open" href="{d.e(url)}">{d.e(cp["open_edition"])} →</a></li>')
        (rows_visible if index < EDITIONS_SHOWN else rows_more).append(row)
    head = (f'<div class="d-editions-head" aria-hidden="true"><span>{d.e(cp["col_date"])}</span><span>{d.e(cp["col_count"])}</span><span>{d.e(cp["col_evidence"])}</span>'
            f'<span>{d.e(cp["col_topics"])}</span><span>{d.e(cp["col_lead"])}</span></div>')
    more = (f'<details class="d-editions-more"><summary>{d.e(cp["older_editions"])} ({len(rows_more)})</summary>'
            f'<ol class="d-editions">{"".join(rows_more)}</ol></details>') if rows_more else ''
    plate_block = f'<div class="d-archive-plate">{plate_html}</div>' if plate_html else ""
    return (f'{plate_block}<section class="d-archive">'
            f'<div class="frame d-archive-grid"><aside>{filters(stories,catalog)}<p><a href="{d.e(href(base,locale["path_prefix"]+"search/"))}">{d.e(catalog["strings"]["search"]["hint"])}</a></p>'
            f'</aside><div><div class="d-calendar">{"".join(sections)}</div>'
            f'<p class="d-mono d-calendar-note">{d.e(cp["number_stories"])}</p>'
            f'{d.section(cp["editions"])}{head}<ol class="d-editions">{"".join(rows_visible)}</ol>{more}</div></div></section>')


def archive_band(catalog, *, rows, corrections_href, feeds):
    """R4 closing Bone band: the recent corrections log and the machine-readable feeds. Rows are real records."""
    cp = d.copy(catalog)
    items = ''.join(f'<li><time datetime="{d.e(r["iso"])}">{d.e(r["date"])}</time><div><b>{d.e(r["title"])}</b><span>{d.e(r["note"])}</span></div>'
                    f'<a href="{d.e(r["href"])}">{d.e(cp["view"])} →</a></li>' for r in rows)
    log = ''
    if items:
        log = (f'<div class="d-band-row"><h2>{d.e(cp["corr_log"])}</h2><p>{d.e(cp["corr_intro"])}</p>'
               f'<a href="{d.e(corrections_href)}">{d.e(cp["view_all"])} →</a></div><ul class="d-corr-log">{items}</ul>')
    links = ' / '.join(f'<a href="{d.e(u)}">{d.e(n)}</a>' for n, u in feeds)
    return (f'<section class="d-bone d-archive-band"><div class="frame">{log}'
            f'<div class="d-band-row d-band-feeds"><h2>{d.e(catalog["strings"]["feeds"]["title"])}</h2><p>{d.e(cp["feeds_intro"])}</p><span>{links}</span></div></div></section>')


NEGATION = re.compile(r"\b(not|no|nor|cannot|without|unclear|unknown|neither|n't)\b", re.I)


ATTRIBUTED = re.compile(r'\b(report|reports|claim|claims|says|state|states|announce|announces|describe|describes|according|authors?)\b', re.I)


def _svg_chart(cp):
    """Concept diagram: importance is one axis, evidence another. Static; no data points."""
    hatch = ''.join(f'<path d="M{x} 20l20-20"/>' for x in range(-20, 21, 5))
    return (f'<svg class="d-imp-chart" viewBox="-30 0 470 300" role="img" aria-label="{d.e(cp["imp_title"])}">'
            f'<title>{d.e(cp["imp_title"])}</title><desc>{d.e(cp["chart_note"])}</desc>'
            '<path class="ax" d="M80 20V250H420"/><path class="ax-head" d="M80 12l-5 10h10zM428 250l-10-5v10z"/>'
            '<path class="grid" d="M80 135H400M250 20V250"/>'
            '<rect class="m-dashed" x="130" y="52" width="26" height="26"/>'
            '<rect class="m-solid" x="350" y="76" width="26" height="26"/>'
            '<g transform="translate(180 168)"><rect class="m-hatch-box" width="22" height="22"/>'
            f'<svg width="22" height="22" viewBox="0 0 20 20" overflow="hidden" class="m-hatch">{hatch}</svg></g>'
            f'<text x="76" y="12" text-anchor="end" class="yl">{d.e(cp["axis_y_hi"])}</text><text x="76" y="236" text-anchor="end" class="yl">{d.e(cp["axis_y_lo"])}</text>'
            f'<text x="80" y="284">{d.e(cp["axis_x_lo"])}</text><text x="420" y="284" text-anchor="end">{d.e(cp["axis_x_hi"])}</text></svg>')


def _example(stories, label_name, catalog, locale, base, cp):
    """A real claim of this label from the highest-ranked stories that carry one. Nothing is composed."""
    best = None
    for story in stories[:400]:
        for position, item in enumerate(d.rows((story.get('evidence') or {}).get('claims'))):
            text = str(item.get('text') or '')
            # A NOT_ESTABLISHED claim is written as the thing the sources do not settle; without its negation
            # («does not establish…») it reads as an assertion, so only self-contained negations are quoted.
            if label_name == 'NOT_ESTABLISHED' and not NEGATION.search(text):
                continue
            # A CLAIMED example is quoted only when it names who claims it.
            if label_name == 'CLAIMED' and not ATTRIBUTED.search(text):
                continue
            if item.get('label') == label_name and 40 <= len(text) <= 140:
                shown = text
                if locale['code'] != 'en':
                    # Never English prose on a translated page: the story's own localized claim, same position.
                    local = field(story, locale['code'], 'evidence', {}) or {}
                    claims = d.rows(local.get('claims')) if isinstance(local, dict) else []
                    shown = str(claims[position].get('text') or '') if position < len(claims) else ''
                    if not shown:
                        continue
                best = (story, shown)
                break
        if best:
            break
    if not best:
        return f'<div class="method-example"><p class="d-mono">{d.e(cp["example"])}</p><p class="d-method-none">{d.e(cp["no_example"])}</p></div>'
    story, text = best
    _, signal = d.topic_signal(story, catalog)
    src = next((s for s in d.rows(story.get('sources')) if s.get('primary')), None) or next(iter(d.rows(story.get('sources'))), {})
    letter = story.get('evidence_class') if story.get('evidence_class') in ('A', 'B', 'C', 'D') else '?'
    where = ' · '.join(v for v in (src.get('domain') or src.get('organization'), (story.get('event_at') or '')[:10]) if v)
    return (f'<div class="method-example"><p class="d-mono">{d.e(cp["example"])}</p>'
            f'<h3><i class="d-topic-signal d-topic-signal--{signal}" aria-hidden="true"></i>'
            f'<a href="{d.e(href(base, story_path(locale, story)))}">{d.e(text)}</a></h3>'
            f'<p class="d-method-source d-mono">{d.e(cp["source"])} <b>{d.e(letter)}</b> <span>{d.e(where)}</span></p></div>')


def method(catalog, content, *, stories, locale, base, plate_html=''):
    st = catalog['strings']
    p = st['proof']
    cp = d.copy(catalog)
    panels = []
    for kind, raw in (('shown', 'DEMONSTRATED'), ('claimed', 'CLAIMED'), ('not_established', 'NOT_ESTABLISHED')):
        panels.append(f'<div>{d.sample(kind.replace("_","-"))}<h2>{d.e(p[kind])}</h2>'
                      f'<p class="d-mono d-method-short">{d.e(p[kind+"_desc"])}</p><p>{d.e(cp["class_long_"+kind])}</p>'
                      f'{_example(stories, raw, catalog, locale, base, cp)}</div>')
    title = (' ' if locale['code']!='zh-Hans' else '').join(p[key] for key in ('band_shown','band_claimed','band_not_established'))
    plate_block = f'<div class="d-method-plate">{plate_html}</div>' if plate_html else ""
    grade_cls = ' class="is-grade"'
    flow = ''.join(f'<li{grade_cls if i == 2 else ""}><b>{d.e(a)}</b><span>{d.e(b)}</span></li>' for i, (a, b) in enumerate(cp['flow']))
    reg = ''.join(f'<li><i class="d-topic-signal d-topic-signal--{k}" aria-hidden="true"></i><div><b>{d.e(n)}</b><span>{d.e(t)}</span></div></li>' for k, n, t in cp['reg'])
    grades = ''.join(f'<div><dt>{grade}</dt><dd>{d.e(label(catalog,"evidence_class",grade))}</dd></div>' for grade in ('A','B','C','D'))
    return (f'<article class="d-method"><header class="frame"><p class="d-kicker">{d.e(st["nav"]["method"])}</p><h1>{d.e(title)}</h1>'
            f'<p class="d-method-dek">{d.e(cp["method_dek"])}</p></header>'
            f'{plate_block}<section class="frame d-method-grades"><h2 class="d-mono-head">{d.e(cp["grades_kicker"])}</h2>'
            f'<p class="d-mono d-method-count">{d.e(cp["grades_count"].format(n=len(stories)))}</p>'
            f'<div class="d-method-classes">{"".join(panels)}</div></section>'
            f'<section class="method-steps"><div class="frame"><h2 class="d-mono-head">{d.e(cp["process"])}</h2><ol class="d-flow">{flow}</ol></div></section>'
            f'<div class="frame d-method-content">{content}</div>'
            f'<section class="frame d-method-grade-note"><h2>{d.e(st["method"]["grades_title"])}</h2>'
            f'<p>{d.e(cp["source_note"])}</p><dl>{grades}</dl></section>'
            f'<section class="d-bone d-importance"><div class="frame d-importance-grid"><div class="d-importance-copy"><p class="d-mono">{d.e(cp["imp_kicker"])}</p>'
            f'<h2>{d.e(cp["imp_title"])}</h2><p>{d.e(cp["imp_body"])}</p></div>'
            f'<figure>{_svg_chart(cp)}<figcaption>{d.e(cp["chart_note"])}</figcaption></figure>'
            f'<aside><p class="d-mono">{d.e(cp["registry"])}</p><ul class="d-registry">{reg}</ul></aside></div></section></article>')
