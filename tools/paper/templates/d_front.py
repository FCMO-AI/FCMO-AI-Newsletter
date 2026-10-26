"""The approved D front composition, fed by the existing editorial order."""
from . import d_components as d
from ..i18n import field, plural, label
from ..front_plan import evidence_class


def rank(stories, ctx):
    if not stories:
        return ''
    st = ctx.s['story']
    headings = ['#', ctx.s['nav']['topics'], st['evidence'], st['sources'], st['unknowns']]
    rows = []
    for i, story in enumerate(stories, 1):
        evidence = ctx.evidence(story)
        primary = sum(bool(s.get('primary')) for s in d.rows(story.get('sources')))
        gaps = len(evidence.get('gaps') or [])
        kind = {'shown': 'DEMONSTRATED', 'claimed': 'CLAIMED'}.get(evidence_class(story), '')
        from .landing import _plate_html
        art = _plate_html(story, "16:10", ctx.s) if story.get('media') else ''
        rows.append(f'<li data-story-id="{d.e(story["id"])}" data-evidence-class="{d.e(kind)}"><article class="d-rank-entry">'
                    f'<b class="d-rank-number">{i:02d}</b><a class="d-rank-art" href="{d.e(ctx.story_href(story))}" aria-hidden="true" tabindex="-1">{art}</a>'
                    f'<div class="d-rank-topic">{d.topic(story, ctx.catalog)}</div>'
                    f'<div class="d-rank-copy"><h3><a href="{d.e(ctx.story_href(story))}">{d.e(ctx.head(story))}</a></h3>'
                    f'<div class="d-rank-mobile-grade">{d.grade(story, ctx.catalog)}</div>'
                    f'<p class="d-rank-mobile-counts">{d.e(plural(ctx.catalog,"primary_source",primary))} · {d.e(plural(ctx.catalog,"open_gap",gaps))}</p></div>'
                    f'<div class="d-rank-proof">{d.claim(kind,ctx.catalog)}</div>'
                    f'<div class="d-rank-stat">{d.stat(primary,plural(ctx.catalog,"primary_source",primary))}</div>'
                    f'<div class="d-rank-stat">{d.stat(gaps,plural(ctx.catalog,"open_gap",gaps))}</div></article></li>')
    return (f'<section class="d-rank" id="board" aria-labelledby="board-title"><div class="frame">'
            f'<h2 class="d-section" id="board-title">{d.e(ctx.s["board"]["order_note"])}</h2>'
            f'<div class="d-rank-head" aria-hidden="true"><span>#</span><span></span><span>{d.e(headings[1])}</span><span>{d.e(label(ctx.catalog,"format","news"))}</span><span>{d.e(st["evidence"])}</span><span>{d.e(st["sources"])}</span><span>{d.e(st["unknowns"])}</span></div>'
            f'<ol>{"".join(rows)}</ol></div></section>')


def cover(feature, story, ctx):
    from .landing import _plate_html
    title = d.e(feature['title'])
    evidence = ctx.evidence(story)
    text = ctx.s['design']
    cells = []
    # The twenty-second brief is derived, never composed from the mockup copy.
    gap_text = ' '.join(str(g.get('description', '') if isinstance(g, dict) else g) for g in evidence.get('gaps', []))
    for heading, value in [(text['brief_title'], feature['dek']), (text['happened'], field(story,ctx.code,'summary')),
                           (text['matters'], field(story,ctx.code,'why_it_matters')), (text['not_established'], gap_text or text['none_recorded'])]:
        cells.append(f'<div><h2>{d.e(heading)}</h2><p>{d.e(value)}</p></div>')
    plate = _plate_html(story,"16:9",ctx.s) if story.get("media") else ""
    plate_block = f'<div class="d-cover-plate">{plate}</div>' if plate else ""
    return (f'<section class="d-cover cover" data-lead data-story-id="{d.e(story["id"])}">'
            f'{plate_block}'
            f'<div class="frame"><div class="d-cover-grid"><div class="d-cover-main">'
            f'<p class="d-kicker d-kicker--lead">FCMO AI · {d.e(ctx.s["cover"]["lead_kicker"].format(beat=feature["beat"]))}</p>'
            f'<h1 class="cover-title {d.e(feature["title_class"])}"><a href="{d.e(feature["href"])}">{title}</a></h1>'
            f'<p class="d-cover-dek">{d.e(feature["dek"])}</p>{d.signals(story,ctx.catalog,evidence=evidence)}'
            f'<a class="d-button" href="{d.e(feature["href"])}">{d.e(feature["cta"])} <span aria-hidden="true">→</span></a>'
            f'<div class="d-cover-disclosure">{feature["badge"]}</div></div>'
            f'<aside class="d-cover-map"><p class="d-kicker">{d.e(ctx.s["cover"]["evidence_glance"])}</p>'
            f'<div class="data-hero">{d.evidence_map(story,ctx.catalog,evidence=evidence,title=feature["title"])}</div></aside></div>'
            f'<div class="d-brief">{"".join(cells)}</div></div></section>')


def follow(home, base, ctx):
    from .subscribe import subscribe_block
    feeds = ''.join(f'<li><a href="{d.e(home+path)}">{name}</a></li>' for path,name in [('feed.xml','RSS'),('feed.atom','Atom'),('feed.json','JSON')])
    return (f'<section class="d-bone"><div class="frame d-follow"><div>{d.legend(ctx.catalog)}</div>'
            f'<div>{subscribe_block("all",ctx.code,base=base,path_prefix=ctx.locale["path_prefix"])}<ul class="feeds">{feeds}</ul></div></div></section>')
