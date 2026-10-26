"""D archive and methodology; no wall clock, fabricated editions or example facts."""
import calendar
from collections import Counter
from . import d_components as d
from ..i18n import format_date, headline, label, plural
from ..front_plan import evidence_class
from ..routes import href, story_path


FILTER_SCRIPT = """<script>(()=>{
const root=document.querySelector('[data-d-filters]');if(!root)return;
root.hidden=false;if(matchMedia('(max-width:760px)').matches)root.closest('details').open=false;
const rows=[...document.querySelectorAll('.archive-item')];
root.addEventListener('change',()=>{
 const wanted={};root.querySelectorAll('input:checked').forEach(e=>(wanted[e.name]||=[]).push(e.value));
 rows.forEach(row=>{row.hidden=Object.entries(wanted).some(([key,values])=>{
 const actual=JSON.parse(row.getAttribute('data-d-'+key)||'[]');return !values.some(v=>actual.includes(v));
 });});
 document.querySelectorAll('.archive-day').forEach(day=>{day.hidden=![...day.querySelectorAll('.archive-item')].some(row=>!row.hidden)});
 const output=root.querySelector('output');output.textContent=rows.filter(row=>!row.hidden).length+' / '+rows.length;
});})();</script>"""


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
        controls = ''.join(f'<label><input type="checkbox" name="{group}" value="{d.e(key)}"><span>{d.e(text)}</span></label>' for key,text in values)
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
                    days.append(f'<a href="{d.e(url)}" data-edition-date="{day}" aria-label="{d.e(catalog["strings"]["archive"]["edition_title"].format(date=format_date(day,catalog)))}"><b>{n}</b><span>{d.e(plural(catalog,"story",counts[day]))}</span></a>')
                else:
                    days.append(f'<span class="d-calendar-empty"><b>{n}</b></span>')
        labels = ''.join(f'<span>{d.e(catalog["date"]["weekdays"][i])}</span>' for i in (6,0,1,2,3,4,5))
        sections.append(f'<details class="d-calendar-month"{" open" if index==0 else ""}><summary>{d.e(name)}</summary>'
                        f'<div class="d-calendar-week">{labels}</div><div class="d-calendar-grid">{"".join(days)}</div></details>')
    editions = []
    for day in dates:
        values = [s for s in stories if s['url_date']==day]
        lead = values[0] if values else None
        title = headline(lead,locale['code'],catalog) if lead else catalog['strings']['archive']['empty']
        if len(values) <= 12:
            marks = ''.join(d.sample(evidence_class(s).replace('_','-')) for s in values)
        else:
            classes = Counter(evidence_class(s) for s in values)
            marks = ''.join(f'<span class="d-edition-count">{d.sample(k.replace("_","-"))}<span>{n}</span></span>' for k,n in classes.items())
        url = href(base,locale['path_prefix']+'edition/'+day+'/')
        editions.append(f'<li><time datetime="{day}">{d.e(format_date(day,catalog))}</time><span>{len(values)}</span><div class="d-edition-marks">{marks}</div><a href="{d.e(url)}">{d.e(title)} →</a></li>')
    plate_block = f'<div class="d-archive-plate">{plate_html}</div>' if plate_html else ""
    return (f'<section class="d-archive"><p class="frame d-archive-intro">{d.e(d.copy(catalog)["archive_intro"])}</p>'
            f'{plate_block}<div class="frame d-archive-grid"><aside>{filters(stories,catalog)}<p><a href="{d.e(href(base,locale["path_prefix"]+"search/"))}">{d.e(catalog["strings"]["search"]["hint"])}</a></p>'
            f'{d.legend(catalog)}</aside><div><div class="d-calendar">{"".join(sections)}</div>'
            f'{d.section(d.copy(catalog)["editions"])}<ol class="d-editions">{"".join(editions)}</ol></div></div></section>')


def method(catalog, content, *, stories, locale, base, plate_html=''):
    st = catalog['strings']
    p = st['proof']
    panels = []
    for kind in ('shown','claimed','not_established'):
        sample = next((s for s in stories if evidence_class(s)==kind),None)
        example = ''
        if sample:
            example = (f'<article class="d-method-example"><h3><a href="{d.e(href(base,story_path(locale,sample)))}">{d.e(headline(sample,locale["code"],catalog))}</a></h3>'
                       f'{d.grade(sample,catalog)}</article>')
        panels.append(f'<div>{d.sample(kind.replace("_","-"))}<h2>{d.e(p[kind])}</h2><p>{d.e(p[kind+"_desc"])}</p>{example}</div>')
    title = (' ' if locale['code']!='zh-Hans' else '').join(p[key] for key in ('band_shown','band_claimed','band_not_established'))
    plate_block = f'<div class="d-method-plate">{plate_html}</div>' if plate_html else ""
    return (f'<article class="d-method"><header class="frame"><p class="d-kicker">{d.e(st["nav"]["method"])}</p><h1>{d.e(title)}</h1>'
            f'<p class="d-method-dek">{d.e(st["site"]["description"])}</p></header>'
            f'{plate_block}<section class="frame">{d.section(st["method"]["classes_title"])}'
            f'<div class="d-method-classes">{"".join(panels)}</div></section>'
            f'<div class="frame d-method-content">{content}</div>'
            f'<section class="d-bone"><div class="frame d-method-grade-note"><h2>{d.e(st["method"]["grades_title"])}</h2>'
            f'<p>{d.e(d.copy(catalog)["source_note"])}</p><dl>'
            + ''.join(f'<div><dt>{grade}</dt><dd>{d.e(label(catalog,"evidence_class",grade))}</dd></div>' for grade in ('A','B','C','D'))
            + '</dl></div></section></article>')
