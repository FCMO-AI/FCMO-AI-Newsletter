"""The approved D front composition, fed by the existing editorial order."""
from . import d_components as d
from ..i18n import field, plural, label
from ..front_plan import evidence_class
from .. import d_plates
from ..i18n import visual_width
from .reader import rest_after, _SENTENCE

BRIEF_BUDGET = 230  # visual columns per brief cell (R4 cells run 4-6 short lines)


def whole_sentences(text, budget):
    """Leading whole sentences of ``text`` that fit ``budget`` columns; the first one is always kept whole."""
    parts = [x for x in _SENTENCE.split(' '.join(str(text or '').split())) if x]
    out = []
    for part in parts:
        if out and visual_width(' '.join(out + [part])) > budget:
            break
        out.append(part)
    return ' '.join(out)


def rank(stories, ctx):
    if not stories:
        return ''
    st = ctx.s['story']
    headings = ['#', ctx.s['nav']['topics'], st['evidence'], st['sources'], st['unknowns']]
    cp = d.copy(ctx.catalog)
    rows = []
    seen = ctx.__dict__.setdefault('d_plates', {})
    for i, story in enumerate(stories, 1):
        evidence = ctx.evidence(story)
        primary = sum(bool(s.get('primary')) for s in d.rows(story.get('sources')))
        gaps = len(evidence.get('gaps') or [])
        kind = {'shown': 'DEMONSTRATED', 'claimed': 'CLAIMED'}.get(evidence_class(story), '')
        art = d_plates.html(story, "16:10", ctx.s, ctx.base, seen, thumb=True) if story.get('media') else ''
        rows.append(f'<li data-story-id="{d.e(story["id"])}" data-evidence-class="{d.e(kind)}"><article class="d-rank-entry">'
                    f'<b class="d-rank-number" data-n="{i:02d}">{i}</b><a class="d-rank-art" href="{d.e(ctx.story_href(story))}" aria-hidden="true" tabindex="-1">{art}</a>'
                    f'<div class="d-rank-topic">{d.topic(story, ctx.catalog)}</div>'
                    f'<div class="d-rank-copy"><h3><a href="{d.e(ctx.story_href(story))}">{d.e(ctx.head(story))}</a></h3>'
                    f'<div class="d-rank-mobile-grade">{d.grade(story, ctx.catalog)}</div>'
                    f'<p class="d-rank-mobile-counts">{d.e(plural(ctx.catalog,"primary_source",primary))} · {d.e(plural(ctx.catalog,"open_gap",gaps))}</p></div>'
                    f'<div class="d-rank-proof">{d.claim(kind,ctx.catalog)}</div>'
                    f'<div class="d-rank-stat">{d.stat(primary,plural(ctx.catalog,"primary_source",primary))}</div>'
                    f'<div class="d-rank-stat">{d.stat(gaps,plural(ctx.catalog,"open_gap",gaps))}</div></article></li>')
    return (f'<section class="d-rank" id="board" aria-labelledby="board-title"><div class="frame">'
            f'<div class="d-section-head d-rank-title"><h2 class="d-section" id="board-title">{d.e(ctx.s["board"]["order_note"])}</h2>'
            f'<span class="d-rank-count">{d.e(plural(ctx.catalog,"edition_story",len(stories)))}</span></div>'
            f'<div class="d-rank-head" aria-hidden="true"><span>#</span><span>{d.e(cp["col_image"])}</span><span>{d.e(cp["col_topic"])}</span><span>{d.e(cp["col_story"])}</span><span>{d.e(st["evidence"])}</span><span>{d.e(st["sources"])}</span><span>{d.e(cp["col_gaps"])}</span></div>'
            f'<ol>{"".join(rows)}</ol></div></section>')


def cover(feature, story, ctx):
    title = d.e(feature['title'])
    evidence = ctx.evidence(story)
    text = ctx.s['design']
    cells = []
    # The twenty-second brief is derived, never composed from the mockup copy. Every cell closes on a whole sentence
    # (R4): the text is fitted by sentences, never cut mid-phrase with an ellipsis, and the block grows when the first
    # sentence is long. The complete text stays on the story page.
    gaps = [str(g.get('description', '') if isinstance(g, dict) else g) for g in evidence.get('gaps', [])]
    happened = rest_after(field(story, ctx.code, 'summary'), feature['dek'])
    for heading, value, budget in [(text['brief_title'], feature['dek'], BRIEF_BUDGET), (text['happened'], happened, BRIEF_BUDGET),
                                   (text['matters'], field(story, ctx.code, 'why_it_matters'), BRIEF_BUDGET),
                                   (text['not_established'], ' '.join(gaps[:1]) or text['none_recorded'], BRIEF_BUDGET)]:
        cells.append(f'<div><h2>{d.e(heading)}</h2><p>{d.e(whole_sentences(value, budget))}</p></div>')
    plate = d_plates.html(story, "16:9", ctx.s, ctx.base, ctx.__dict__.setdefault('d_plates', {})) if story.get("media") else ""
    plate_block = f'<div class="d-cover-plate">{plate}</div>' if plate else ""
    date = (f'<time datetime="{d.e(feature["datetime"])}">{d.e(feature["date"])}</time>'
            if feature.get('datetime') and feature.get('date') else '')
    return (f'<section class="landing-intro"><article class="landing-feature story-card" data-lead data-story-id="{d.e(story["id"])}">'
            f'{plate_block}'
            f'<div class="frame"><div class="d-cover-grid"><div class="d-cover-main">'
            f'<p class="d-kicker d-kicker--lead">FCMO AI · {d.e(ctx.s["cover"]["lead_kicker"].format(beat=feature["beat"]))}</p>'
            f'<h1 class="cover-title {d.e(feature["title_class"])}"><a href="{d.e(feature["href"])}">{title}</a></h1>'
            f'<p class="d-cover-dek">{d.e(feature["dek"])}</p>{d.signals_rich(story,ctx.catalog,evidence=evidence)}'
            f'<div class="d-cover-date">{date}</div><div class="cover-actions"><a class="btn" href="{d.e(feature["href"])}">{d.e(feature["cta"])}</a></div>'
            f'<div class="d-cover-disclosure">{feature["badge"]}</div></div>'
            f'<aside class="d-cover-map"><p class="d-kicker">{d.e(ctx.s["cover"]["evidence_glance"])}</p>'
            f'<div class="data-hero">{d.evidence_glance(story,ctx.catalog,evidence=evidence,title=feature["title"])}</div></aside></div>'
            f'<div class="d-brief">{"".join(cells)}</div></div></article></section>')


def follow(home, base, ctx, stories):
    from .subscribe import subscribe_block
    feeds = ''.join(f'<li><a href="{d.e(home+path)}">{name}</a></li>' for path,name in [('feed.xml','RSS'),('feed.atom','Atom'),('feed.json','JSON')])
    return (f'<section class="d-bone"><div class="frame d-follow"><div>{d.legend(ctx.catalog,stories=stories,method_href=home+"method/")}</div>'
            f'<div>{subscribe_block("all",ctx.code,base=base,path_prefix=ctx.locale["path_prefix"])}<ul class="feeds">{feeds}</ul></div></div></section>')
