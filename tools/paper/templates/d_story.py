"""D story: a reading column beside its visible evidence ledger."""
import re
from . import d_components as d
from .reader import layer, unknowns_box, LAYER_SCRIPT, rest_after, first_sentence, _same


_SPLIT = re.compile(r'(?<=[。！？])|(?<![A-Z]\.)(?<=[.!?])\s+(?=[A-Z0-9“"¿¡(])')


def paragraphs(text, per=2):
    """Sentence pairs as paragraphs (R4 reads in short blocks); the words are exactly the record's."""
    parts = [x.strip() for x in _SPLIT.split(text or '') if x and x.strip()]
    sep = '' if text and re.search(r'[\u4e00-\u9fff]', text) else ' '
    return [sep.join(parts[i:i + per]) for i in range(0, len(parts), per)]


def opening(summary, header_dek, full_dek, catalog, with_more=False):
    """Keep the opening fact on phones and continue after the visible dek on desktop."""
    whole = ' '.join(str(summary or '').split())
    happened = rest_after(summary, full_dek or header_dek) if header_dek else whole
    if header_dek.endswith('…') and whole.startswith(header_dek[:-1]):
        # Preserve the rest of an over-budget sentence as well as later sentences.
        happened = whole[len(header_dek)-1:].lstrip()
    opener = header_dek if happened != whole else ''
    phone_only = bool(header_dek) and _same(first_sentence(summary,10_000),header_dek) and happened == whole
    paras = paragraphs(happened, per=1)
    shown, later = paras[:3], paras[3:]
    content = (f'<span class="brief-open">{d.e(opener)} </span>' if opener else '') + ' <i class="d-pb"></i>'.join(d.e(x) for x in shown)
    more = f'<div class="d-story-more">{"".join(f"<p>{d.e(x)}</p>" for x in later)}</div>' if later else ''
    html = (f'<ol class="d-story-opening"><li class="read20-cell{" read20-phone" if phone_only else ""}">'
            f'<b>{d.e(catalog["strings"]["design"]["happened"])}</b><span class="brief-val">{content}</span></li></ol>')
    return (html, more) if with_more else html + more


def render(*, story, catalog, code, title, dek_text, beat_label, home_href,
           evidence, summary, why, technical, status_html, automation_html,
           byline, dates_line, plate_html, note_html, taxonomy_html,
           navigation_html, topic_nav_html, machine_html, title_class='', dek_full=''):
    st = catalog['strings']
    text = st['story']
    p = st['proof']
    argument, more_html = opening(summary,dek_text,dek_full,catalog,with_more=True)
    if why:
        more_html += f'<section class="d-story-why"><h2>{d.e(text["why_it_matters"])}</h2>{"".join(f"<p>{d.e(x)}</p>" for x in paragraphs(why))}</section>'
    tech = ''.join(f'<section><h3>{d.e(st["technical_field"].get(k,k))}</h3><p>{d.e(v)}</p></section>' for k,v in technical.items() if v)
    plate_block = f'<div class="d-story-plate">{plate_html}</div>' if plate_html else ''
    header = (f'<div class="story-cover d-story-cover"><header class="story-header"><div class="frame"><p class="d-kicker">'
              f'<span><a href="{d.e(home_href)}">{d.e(st["nav"]["today"])}</a> / {d.e(beat_label)} / {d.topic(story,catalog)}</span><span class="d-story-dates">{d.e(dates_line)}</span></p>'
              f'<h1>{d.e(title)}</h1>'
              f'{d.signals(story,catalog,evidence=evidence)}<p class="story-dek">{d.e(dek_text)}</p>{note_html}</div></header>'
              f'{plate_block}</div>')
    corrections = []
    for c in story.get('corrections', []):
        note = (c.get('text') or {}).get(code)
        if note:
            corrections.append(f'<p>{d.e(note)}</p>')
        else:
            corrections.append(f'<p class="translation-note">{d.e(st["l10n"]["pending_title"])}</p>')
    correction_html = ''.join(corrections) or f'<p>{d.e(st["corrections_page"]["none"])}</p>'
    foot = (f'<section class="d-bone d-story-notes"><div class="frame"><div><h2 class="d-section">{d.e(text["corrections"])}</h2>{correction_html}</div>'
            f'<div><h2 class="d-section">{d.e(d.copy(catalog)["graded_title"])}</h2><p>{d.e(d.copy(catalog)["source_note"])}</p>{d.legend(catalog)}</div></div></section>')
    import html as _html
    m = re.search(r'</i>(.*?)</span>', status_html or '')
    state_text = _html.unescape(m.group(1)) if m else ''
    cont = f'<div class="d-story-continued">{more_html}</div>' if more_html else ''
    layers = ('<div class="layers">' + layer('technical',st['design']['technical_title'],st['design']['layer_r3'],f'<div id="technical">{tech}</div>',is_open=False) + '</div>' if technical else '')
    # R4 core: opening + ledger -> sources diagram -> timeline -> Bone band. The rest of the record is content, kept
    # reachable in one disclosure between the timeline and the band so it never pushes the core apart.
    extra = (f'{unknowns_box(evidence,catalog)}{layers}{machine_html}'
             f'<details class="d-story-taxonomy"><summary>{d.e(text["topics"])}</summary>{taxonomy_html}</details>'
             f'<div class="story-after">{topic_nav_html}{navigation_html}</div>')
    return (header + f'<div class="frame"><div class="d-story-disclosure">{d.e(byline)} · {automation_html}{status_html}</div>'
            f'<div class="d-story-reading"><div class="d-story-argument"><div class="story-body"><div class="brief">{argument}</div></div>{cont}</div>'
            f'<aside class="d-story-ledger">{d.ledger(evidence,catalog)}</aside></div>'
            f'<div class="data-hero">{d.claims_sources(story,evidence,catalog)}</div>'
            f'{d.section(d.copy(catalog)["timeline"])}{d.timeline(story,catalog,state_text)}'
            f'<details class="d-story-extra"><summary>{d.e(d.copy(catalog)["full_record"])}</summary>{extra}</details></div>{foot}' + LAYER_SCRIPT)
