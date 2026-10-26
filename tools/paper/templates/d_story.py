"""D story: a reading column beside its visible evidence ledger."""
from . import d_components as d
from .reader import layer, unknowns_box, LAYER_SCRIPT


def render(*, story, catalog, code, title, dek_text, beat_label, home_href,
           evidence, summary, why, technical, status_html, automation_html,
           byline, dates_line, plate_html, note_html, taxonomy_html,
           navigation_html, topic_nav_html, machine_html, title_class='', dek_full=''):
    st = catalog['strings']
    text = st['story']
    p = st['proof']
    argument = ''.join(f'<section><h2>{d.e(text[k])}</h2><p>{d.e(value)}</p></section>'
                       for k, value in [('what_changed',summary),('why_it_matters',why)] if value)
    tech = ''.join(f'<section><h3>{d.e(st["technical_field"].get(k,k))}</h3><p>{d.e(v)}</p></section>' for k,v in technical.items() if v)
    plate_block = f'<div class="d-story-plate">{plate_html}</div>' if plate_html else ''
    header = (f'<div class="story-cover d-story-cover"><header class="story-header"><div class="frame"><p class="d-kicker">'
              f'<a href="{d.e(home_href)}">{d.e(st["nav"]["today"])}</a> / {d.e(beat_label)} / {d.topic(story,catalog)}</p>'
              f'<h1>{d.e(title)}</h1><p class="story-dek">{d.e(dek_text)}</p>'
              f'{d.signals(story,catalog,evidence=evidence)}<p class="story-meta">{d.e(dates_line)}</p>{note_html}</div></header>'
              f'{plate_block}</div>')
    corrections = []
    for c in story.get('corrections', []):
        note = (c.get('text') or {}).get(code)
        if note:
            corrections.append(f'<p>{d.e(note)}</p>')
    correction_html = ''.join(corrections) or f'<p>{d.e(st["corrections_page"]["none"])}</p>'
    foot = (f'<section class="d-bone d-story-notes"><div class="frame"><div><h2 class="d-section">{d.e(text["corrections"])}</h2>{correction_html}</div>'
            f'<div><h2 class="d-section">{d.e(st["method"]["grades_title"])}</h2><p>{d.e(d.copy(catalog)["source_note"])}</p>{d.legend(catalog)}</div></div></section>')
    return (header + f'<div class="frame"><div class="d-story-disclosure">{d.e(byline)} · {automation_html}{status_html}</div>'
            f'<div class="d-story-reading"><div class="story-body d-story-argument">{argument}</div>'
            f'<aside class="d-story-ledger">{d.ledger(evidence,catalog)}</aside></div>'
            f'{d.claims_sources(story,evidence,catalog)}{unknowns_box(evidence,catalog)}'
            f'{d.section(d.copy(catalog)["timeline"])}{d.timeline(story,catalog)}'
            + ('<div class="layers">' + layer('technical',st['design']['technical_title'],st['design']['layer_r3'],f'<div id="technical">{tech}</div>',is_open=False) + '</div>' if technical else '')
            + f'{machine_html}<details class="d-story-taxonomy"><summary>{d.e(text["topics"])}</summary>{taxonomy_html}</details>'
            + f'<div class="story-after">{topic_nav_html}{navigation_html}</div></div>{foot}' + LAYER_SCRIPT)
