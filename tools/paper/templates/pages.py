"""Page-level semantic templates."""

from __future__ import annotations

from html import escape


def e(value: object) -> str:
    return escape(str(value), quote=True)


def story_card(story: dict, *, href: str, headline: str, dek: str, beat: str, date: str, level: int = 2) -> str:
    heading = max(2, min(level, 3))
    return f'''<article class="story-card"><span class="card-meta">{e(beat)} · {e(date)}</span><h{heading}><a href="{e(href)}">{e(headline)}</a></h{heading}><p>{e(dek)}</p></article>'''


def front_page(*, lead: str, top: str, essentials: str, beats: str, developing: str,
               subscribe: str, cartas: str, editions: str) -> str:
    return f'''<div class="front-grid">{lead}<aside class="top-stories">{top}</aside></div>
<section class="essentials">{essentials}</section>{beats}{developing}
<div class="front-tail"><div class="slot" data-slot="cartas"><!-- slot:cartas -->{cartas}</div><div class="slot" data-slot="subscribe"><!-- slot:subscribe -->{subscribe}</div></div>{editions}'''


def story_page(*, header: str, body: str, aside: str) -> str:
    return f'<article class="story-layout">{header}<div class="story-body">{body}</div><aside class="story-aside">{aside}</aside></article>'


def archive_page(title: str, intro: str, items: str) -> str:
    return f'<header><p class="section-kicker">FCMO AI · archive</p><h1 class="page-title">{e(title)}</h1><p>{e(intro)}</p></header><div class="archive-list">{items}</div>'


def status_page(title: str, cards: str, detail: str) -> str:
    return f'<header><p class="section-kicker">FCMO AI · operations</p><h1 class="page-title">{e(title)}</h1></header><div class="status-grid">{cards}</div>{detail}'


def simple_page(title: str, body: str, *, kicker: str = "FCMO AI") -> str:
    return f'<article class="story-body"><header><p class="section-kicker">{e(kicker)}</p><h1 class="page-title">{e(title)}</h1></header>{body}</article>'
