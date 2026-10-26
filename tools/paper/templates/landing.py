"""FCMO AI front page (c6): cover, board, method band, wire, topics, trio and subscription.

One publication, one flow. Every string comes from ``i18n/ui`` by key; the
cover and every item carry their evidence class as a word plus a sample, never
colour alone. ``render`` keeps its old keyword contract; the sections after the
cover need ``front`` (see ``front_context`` in this module).
"""

from html import escape

from tools.paper import front_plan as plan_mod
from tools.paper.i18n import _catalog, dek, field, headline, label, plural, truncate
from tools.paper.routes import href as route_href, slugify, story_path, topic_path
from .reader import first_sentence
from .subscribe import subscribe_block

try:  # L8 ships tools/paper/plates.py; until then a neutral, text-free stub with the same contract.
    from tools.paper.plates import plate as _plate
except ImportError:  # pragma: no cover - exercised until the plates module is merged
    def _plate(story_id: str, topic_ids, ratio: str, variant: int = 0) -> dict:
        seed = sum(ord(c) for c in str(story_id))
        width, height = (800, 500) if ratio == "16:10" else (800, 450)
        bars = "".join(
            f'<rect x="{-20 + ((seed * (i + 3) + j * 97) % 600)}" y="{40 + i * 52}" width="{50 + ((seed + i * 31 + j * 17) % 120)}" '
            f'height="16" rx="2" fill="#F2EFE8" opacity="{(0.08, 0.14, 0.22)[(seed + i + j) % 3]}"/>'
            for i in range(8) for j in range(4))
        mark = f'<rect x="{80 + seed % 500}" y="{40 + (seed % 8) * 52}" width="110" height="16" rx="2" fill="#F05A28"/>'
        svg = (f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
               f'<rect width="{width}" height="{height}" fill="#14110F"/>{bars}{mark}</svg>')
        return {"svg": svg, "alt": "Decorative plate", "motif": "neutral"}


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _plate_family(story: dict) -> str:
    try:
        from tools.paper.plates import choose_motif
    except ImportError:  # pragma: no cover
        return "neutral"
    return choose_motif(list(story.get("topics") or []))


def _plate_html(story: dict, ratio: str, strings: dict, seen: list | None = None) -> str:
    # The first circular plate on a page keeps its rings; later ones take the non-circular drawing, by slot order.
    variant = 0
    if seen is not None and _plate_family(story) in ("monitoring", "neutral"):
        variant = 1 if seen else 0
        seen.append(1)
    plate = _plate(story["id"], list(story.get("topics") or []), ratio, variant=variant)
    motif = plate.get("motif") or "neutral"
    motif_text = strings["plate"].get("motif_" + motif, "")
    alt = (strings["plate"]["alt_decorative"] if motif == "neutral" or not motif_text
           else strings["plate"]["alt_motif"].format(motif=motif_text))
    return f'<div class="plate" data-ratio="{_e(ratio)}" role="img" aria-label="{_e(alt)}">{plate["svg"]}</div>'


class _Ctx:
    """Per-render lookups: catalog, locale and the routes that need them."""

    def __init__(self, locale: dict, base: str) -> None:
        self.locale = locale
        self.code = locale["code"]
        self.catalog = _catalog(self.code)
        self.s = self.catalog["strings"]
        self.base = base
        self.topic_labels = self.catalog.get("labels", {}).get("topic", {})
        self.rings_seen: list = []

    def story_href(self, story: dict) -> str:
        return route_href(self.base, story_path(self.locale, story))

    def topic_href(self, topic: str) -> str:
        return route_href(self.base, topic_path(self.locale, slugify(topic)))

    def topic_label(self, story: dict) -> str:
        for topic in story.get("topics") or []:
            if topic in self.topic_labels:
                return self.topic_labels[topic]
        return ""

    def head(self, story: dict) -> str:
        return headline(story, self.code, self.catalog)

    def format_label(self, story: dict) -> str:
        return label(self.catalog, "format", plan_mod.story_format(story))

    def evidence(self, story: dict) -> dict:
        value = story.get("evidence") if self.code == "en" else field(story, self.code, "evidence", {})
        if not isinstance(value, dict):
            return {}
        canonical = (story.get("evidence") or {}).get("claims") or []
        return {**value, "claims": [{**claim, **({key: canonical[i][key] for key in ("label", "qualifier") if key in canonical[i]} if i < len(canonical) else {})}
                                      for i, claim in enumerate(value.get("claims") or [])]}



def _counts(story: dict) -> tuple[int, int]:
    sources = story.get("sources") if isinstance(story.get("sources"), list) else []
    evidence = story.get("evidence") if isinstance(story.get("evidence"), dict) else {}
    gaps = evidence.get("gaps") if isinstance(evidence.get("gaps"), list) else []
    return sum(1 for s in sources if isinstance(s, dict) and s.get("primary")), len(gaps)


_SAMPLE = {"shown": "shown", "claimed": "claimed", "not_established": "gap"}


def _chip(klass: str, ctx: _Ctx) -> str:
    kind = _SAMPLE[klass]
    from .d_components import sample as proof_sample
    glyph = proof_sample(klass.replace('_', '-')).replace('class="d-sample', 'class="sample d-sample')
    return f'<span class="chip chip-{kind}">{glyph}<span class="chip-word"><strong>{_e(ctx.s["proof"][klass])}</strong></span></span>'



def _grade(story: dict, ctx: _Ctx) -> str:
    """The lettered grade plate with its short name, so the grade is on the first screen of the cover."""
    letter = story.get("evidence_class")
    if letter not in ("A", "B", "C", "D"):
        return ""
    name = label(ctx.catalog, "evidence_short", letter)
    return (f'<span class="cover-grade"><span class="evrow-grade" aria-hidden="true">{letter}</span>'
            f'<span class="cover-grade-name">{_e(name)}</span></span>')


def _evrow(story: dict, ctx: _Ctx, *, cls: str = "evrow", tag: str = "p", grade: bool = False) -> str:
    klass = plan_mod.evidence_class(story)
    primary, gaps = _counts(story)
    return (f'<{tag} class="{cls}" data-evidence-class="{_e(klass)}">{_grade(story, ctx) if grade else ""}{_chip(klass, ctx)}'
            f'<span>{_e(plural(ctx.catalog, "primary_source", primary))}</span>'
            f'<span>{_e(plural(ctx.catalog, "open_gap", gaps))}</span></{tag}>')


def _receipt(story: dict, feature: dict, ctx: _Ctx) -> str:
    d = ctx.s["design"]
    evidence = ctx.evidence(story)
    gaps = [g.get("description") for g in (evidence.get("gaps") or []) if isinstance(g, dict) and g.get("description")]
    limits = [x for x in (evidence.get("limitations") or []) if isinstance(x, str) and x]
    unknown = first_sentence(gaps[0] if gaps else (limits[0] if limits else d["none_recorded"]), 360)
    why = first_sentence(field(story, ctx.code, "why_it_matters"), 360)
    rows = f'<div><dt>{_e(d["happened"])}</dt><dd>{_e(first_sentence(feature["dek"], 360))}</dd></div>'
    if why:
        rows += f'<div><dt>{_e(d["matters"])}</dt><dd>{_e(why)}</dd></div>'
    rows += f'<div class="receipt-na"><dt>{_e(d["not_established"])}</dt><dd>{_e(unknown)}</dd></div>'
    return f'<div class="receipt"><p class="receipt-title">{_e(d["brief_title"])}</p><dl>{rows}</dl></div>'


def _cover(feature: dict, story: dict | None, ctx: _Ctx | None, record: str) -> str:
    kicker = f'FCMO AI · {feature["label"]} · {feature["beat"]}'
    # The edition state is stated once, in the banner at the top of the page; the cover keeps only the automation disclosure.
    foot = f'<div class="cover-foot">{feature["badge"]}</div>'
    if ctx and story:
        kicker = "FCMO AI · " + ctx.s["cover"]["lead_kicker"].format(beat=feature["beat"])
        signals = _evrow(story, ctx, cls="evrow cover-evrow", tag="div", grade=True)
        glance = ctx.s["cover"]["evidence_glance"]
        side = f'<div class="cover-side">{_plate_html(story, "16:10", ctx.s, ctx.rings_seen)}{_receipt(story, feature, ctx)}</div>'
        glance_html = f'<div class="cover-glance" aria-label="{_e(glance)}">{feature["hero"]}</div>'
    else:
        confidence = f' · {_e(feature["confidence"])}' if feature["confidence"] else ""
        signals = (f'<div class="cover-dek">{_e(feature["dek"])}</div>'
                   f'<div class="evrow"><span class="chip-word"><strong>{_e(feature["grade"])}</strong></span>{confidence}</div>')
        side = f'<div class="cover-side">{foot}</div>'
        glance_html = feature["hero"]
    # Divs, not <p>, inside the card: the legacy ``.story-card p`` rule would grey them out on the dark cover.
    card = (
        '<article class="landing-feature story-card" data-lead><div class="cover-grid">'
        '<div class="cover-main">'
        f'<div class="rubric rubric-accent">{_e(kicker)}</div>'
        f'<h1 class="cover-title {_e(feature["title_class"])}"><a href="{_e(feature["href"])}">{_e(feature["title"])}</a></h1>'
        f'{signals}'
        f'<div class="rubric cover-date"><time datetime="{_e(feature["datetime"])}">{_e(feature["date"])}</time></div>'
        f'<div class="cover-actions"><a class="btn" href="{_e(feature["href"])}">{_e(feature["cta"])} <span aria-hidden="true">↗</span></a></div>'
        f'{foot if ctx and story else ""}'
        '</div>'
        f'{side}'
        f'</div>{glance_html}</article>'
    )
    return (f'<section class="landing-intro" aria-label="{_e(feature["label"])}"><div class="cover surface-ink">'
            f'<div class="frame">{card}</div></div>{record}</section>')


def _board(stories: list[dict], ctx: _Ctx) -> str:
    if not stories:
        return ""
    cards = []
    for index, story in enumerate(stories):
        wide = index == 0
        ident = f'bt-{_e(story["id"])}'
        meta = f'{_e(ctx.format_label(story))} · {_e(story["event_at"][:10])}'
        link = ctx.story_href(story)
        cards.append(
            f'<article class="plate-card{" plate-card-wide" if wide else ""}" aria-labelledby="{ident}" data-story-id="{_e(story["id"])}">'
            f'<a href="{_e(link)}" tabindex="-1" aria-hidden="true">{_plate_html(story, "16:9" if wide else "16:10", ctx.s, ctx.rings_seen)}</a>'
            f'<div class="plate-card-body"><p class="rubric">{meta}</p>'
            f'<h3 class="plate-card-title" id="{ident}"><a href="{_e(link)}">{_e(ctx.head(story))}</a></h3>'
            f'<p class="plate-card-dek">{_e(truncate(dek(story, ctx.code, ctx.catalog), 150))}</p>'
            f'{_evrow(story, ctx)}</div></article>')
    return (f'<section class="block surface-bone" id="board" aria-labelledby="board-title"><div class="frame">'
            f'<div class="block-head"><div><p class="rubric rubric-accent">FCMO AI</p>'
            f'<h2 class="block-title" id="board-title">{_e(ctx.s["board"]["order_note"])}</h2></div></div>'
            f'<div class="board">{"".join(cards)}</div></div></section>')


def _band(stories: list[dict], ctx: _Ctx, method_href: str) -> str:
    p = ctx.s["proof"]
    counts = plan_mod.class_counts(stories)
    topics = len({t for s in stories for t in s.get("topics", [])})
    orgs = len({o for s in stories for o in s.get("organizations", [])})
    trio = "".join(
        f'<div><b>{_e(p[key])} · {_e(plural(ctx.catalog, "story", counts[key]))}</b>{_e(p[key + "_desc"])}</div>'
        for key in ("shown", "claimed", "not_established"))
    stat = ctx.s["stat"]
    nums = (f'<li>{len(stories)}<span>{_e(stat["stories_label"])}</span></li>'
            f'<li>{topics}<span>{_e(stat["topics_label"])}</span></li>'
            f'<li>{orgs}<span>{_e(stat["organizations_label"])}</span></li>')
    gap = "" if ctx.code == "zh-Hans" else " "
    title = f'<em>{_e(p["band_shown"])}</em>{gap}{_e(p["band_claimed"])}{gap}{_e(p["band_not_established"])}'
    return (f'<section class="method-band" id="method-band" aria-labelledby="band-title"><div class="frame">'
            f'<p class="rubric">{_e(ctx.s["trio"]["method_title"])}</p>'
            f'<h2 class="method-band-title" id="band-title">{title}</h2>'
            f'<p class="cover-dek">{_e(p["band_lead"])}</p>'
            f'<div class="band-trio">{trio}</div><p class="band-note">{_e(p["count_note"])}</p><ul class="band-counts">{nums}</ul>'
            f'<p class="cover-actions"><a class="btn" href="{_e(method_href)}">{_e(ctx.s["board"]["how_ordered"])} →</a></p>'
            f'</div></section>')


_FILTER_SCRIPT = (
    "<script>(function(){var nav=document.querySelector('[data-format-filter]');if(!nav)return;"
    "var rows=document.querySelectorAll('.wire-row');nav.addEventListener('click',function(ev){"
    "var a=ev.target.closest('a[data-format]');if(!a)return;ev.preventDefault();"
    "nav.querySelectorAll('a').forEach(function(x){x.removeAttribute('aria-current')});"
    "a.setAttribute('aria-current','true');var f=a.getAttribute('data-format');"
    "rows.forEach(function(r){r.hidden=f!=='all'&&r.getAttribute('data-format')!==f})})})();</script>")


def _wire(stories: list[dict], ctx: _Ctx) -> str:
    if not stories:
        return ""
    present = [f for f in plan_mod.FORMATS if any(plan_mod.story_format(s) == f for s in stories)]
    chips = ""
    if len(present) > 1:
        fm = ctx.s["formats"]
        links = f'<a href="#earlier" data-format="all" aria-current="true">{_e(fm["all"])}</a>' + "".join(
            f'<a href="#earlier" data-format="{f}">{_e(fm[f + "_plural"])}</a>' for f in present)
        chips = f'<nav class="format-filter" data-format-filter aria-label="{_e(ctx.s["a11y"]["format_filter"])}">{links}</nav>'
    rows = []
    # The wire follows the plan order (importance); the section dek says so, because the dates are not monotonic.
    for story in stories:
        rows.append(
            f'<li class="wire-row" data-format="{plan_mod.story_format(story)}" data-story-id="{_e(story["id"])}">'
            f'<time class="wire-date rubric" datetime="{_e(story["event_at"])}">{_e(story["event_at"][:10])}</time>'
            f'<span class="wire-format rubric">{_e(ctx.format_label(story))}</span>'
            f'<div><h3 class="wire-title"><a href="{_e(ctx.story_href(story))}">{_e(ctx.head(story))}</a></h3>'
            f'{_evrow(story, ctx, cls="wire-meta evrow")}</div>'
            f'<span class="wire-topic rubric">{_e(ctx.topic_label(story))}</span></li>')
    return (f'<section class="block surface-bone" id="earlier" aria-labelledby="earlier-title"><div class="frame">'
            f'<div class="block-head"><div><p class="rubric rubric-accent">{_e(ctx.s["wire"]["title"])}</p>'
            f'<h2 class="block-title" id="earlier-title">{_e(ctx.s["earlier"]["title"])}</h2>'
            f'<p>{_e(ctx.s["earlier"]["dek"])}</p></div></div>{chips}'
            f'<ol class="wire" aria-label="{_e(ctx.s["a11y"]["wire_table"])}">{"".join(rows)}</ol></div></section>'
            f'{_FILTER_SCRIPT if chips else ""}')


TOPIC_PAGE_MIN = 3  # build.py writes topic/<slug>/ only for topics with at least this many stories


def _topics(stories: list[dict], ctx: _Ctx) -> str:
    tiles = "".join(
        f'<li><a href="{_e(ctx.topic_href(topic))}"><b>{_e(ctx.topic_labels[topic])}</b>'
        f'<span class="rubric">{_e(plural(ctx.catalog, "story", count))}</span></a></li>'
        for topic, count in plan_mod.topic_counts(stories, ctx.topic_labels) if count >= TOPIC_PAGE_MIN)  # a tile only for a topic that has a page
    if not tiles:
        return ""
    return (f'<section class="block surface-bone" id="topics" aria-labelledby="topics-title"><div class="frame">'
            f'<div class="block-head"><div><h2 class="block-title" id="topics-title">{_e(ctx.s["topics"]["title"])}</h2>'
            f'<p>{_e(ctx.s["topics"]["dek"])}</p></div></div><ul class="topic-tiles">{tiles}</ul></div></section>')


def _trio(home: str, ctx: _Ctx) -> str:
    t = ctx.s["trio"]
    cells = "".join(
        f'<a href="{_e(home + path)}"><b>{_e(t[key + "_title"])}</b><p>{_e(t[key + "_body"])}</p>'
        f'<p class="rubric rubric-accent">{_e(t[key + "_link"])} →</p></a>'
        for key, path in (("corrections", "corrections/"), ("method", "method/"), ("status", "status/")))
    return f'<section class="block surface-bone" id="trio"><div class="frame"><div class="trio">{cells}</div></div></section>'


def _subscribe(home: str, base: str, ctx: _Ctx) -> str:
    u = ctx.s["subscribe_ui"]
    feeds = "".join(f'<li><a href="{_e(url)}">{_e(name)}</a></li>' for name, url in (
        ("RSS", home + "feed.xml"), ("Atom", home + "feed.atom"), ("JSON", home + "feed.json"),
        (u["llms"], base + "llms.txt")))
    return (f'<section class="block surface-bone" id="follow" aria-labelledby="follow-title"><div class="frame subscribe-block">'
            f'<div><p class="rubric rubric-accent">{_e(u["way_title"])}</p><h2 id="follow-title">{_e(u["headline"])}</h2>'
            f'<p>{_e(u["body"])}</p><p class="rubric">{_e(u["by_feed"])} · {_e(u["for_agents"])}</p>'
            f'<ul class="feeds">{feeds}</ul></div><div>{subscribe_block("all", ctx.code)}</div></div></section>')


def front_context(*, order: list[dict], base: str) -> dict:
    """What the build hands to ``render``: the full ``front_order`` list and the site base."""
    return {"order": order, "base": base}


def render(*, locale: dict, home: str, technical: str, about: str, subscribe: str,
           lead: str, top: str, cartas: str, stats: tuple[int, int, int] = (0, 0, 0),
           feature: dict | None = None, front: dict | None = None) -> str:
    s = _catalog(locale["code"])["strings"]
    stat = s["stat"]
    record = (f'<div class="landing-record" aria-label="{_e(stat["stories_label"])}">'
              f'<strong>{stats[0]} <small>{_e(stat["stories_label"])}</small></strong>'
              f'<strong>{stats[1]} <small>{_e(stat["topics_label"])}</small></strong>'
              f'<strong>{stats[2]} <small>{_e(stat["organizations_label"])}</small></strong></div>')
    if not feature:
        return (f'<div class="landing"><section class="landing-intro" aria-labelledby="landing-title">'
                f'<p class="rubric rubric-accent">FCMO AI</p><h1 id="landing-title">{_e(s["brand"]["motto"])}</h1>'
                f'{record}</section></div>')
    if not front:
        return f'<div class="landing">{_cover(feature, None, None, record)}</div>'
    base = front["base"] if front["base"].endswith("/") else front["base"] + "/"
    ctx = _Ctx(locale, base)
    order = front["order"]
    slots = plan_mod.landing_slots(order)
    from . import d_front
    letters = f'<section class="frame d-front-letters">{cartas}</section>' if cartas else ''
    return '<div class="landing d-front">' + "".join([
        d_front.cover(feature, slots["cover"], ctx),
        d_front.rank(([slots["cover"]] if slots["cover"] else []) + slots["board"], ctx),
        letters,
        _wire(slots["wire"], ctx),
        _topics(order, ctx),
        d_front.follow(home, base, ctx, order),
    ]) + "</div>"
