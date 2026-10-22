"""Reader-design elements: evidence glyph, per-story data hero, status, disclosure, provenance, layers.

Everything here is derived from a story's own data; nothing is invented. Text crosses
``html.escape``. Shape and stroke carry the evidence grade and confidence, so they
survive greyscale and colour-blind reading; colour only reinforces.
"""

from __future__ import annotations

from html import escape
import re

from ..i18n import label, plural, truncate
from tools.publication_freshness import reader_status

# Confidence levels ordered by how much the record supports the claim: tick count.
CONFIDENCE_TICKS = {"confirmed": 5, "strongly_supported": 4, "supported": 3,
                    "supported_with_limits": 2, "claimed_unverified": 1}
GRADE_SHAPES = {"A": "solid", "B": "half", "C": "outline", "D": "dashed"}
KIND_ORDER = ("DEMONSTRATED", "INFERRED", "CLAIMED", "SPECULATIVE", "DISPUTED", "OTHER")
_CLAIMED_PREFIXES = ("VENDOR", "GOVERNMENT", "FIRST_PARTY", "PRIMARY_EXTRAORDINARY")
_SENTENCE = re.compile(r"(?<=[.!?。！？])(?:\s+(?=[A-Z0-9“\"'¿¡(\[])|(?<=[。！？]))")


def e(value: object) -> str:
    return escape(str(value), quote=True)


def design(catalog: dict) -> dict:
    return catalog["strings"]["design"]


def claim_kind(claim_label: object) -> str:
    """Fold the long claim vocabulary into the five proof kinds (never merging into a higher one)."""
    value = str(claim_label or "")
    if value in KIND_ORDER[:5]:
        return value
    if value.startswith("DEMONSTRATED"):
        return "DEMONSTRATED"
    if value.startswith(_CLAIMED_PREFIXES) or value.endswith("_CLAIM"):
        return "CLAIMED"
    if value == "COUNTERPOSITION":
        return "DISPUTED"
    return "OTHER"


def first_sentence(text: object, limit: int = 190) -> str:
    """The opening sentence of ``text``; shortened, never extended."""
    text = " ".join(str(text or "").split())
    if not text:
        return ""
    first = _SENTENCE.split(text, maxsplit=1)[0]
    return truncate(first, limit)


def evidence_glyph(story: dict, catalog: dict, *, size: str = "md") -> str:
    """Grade shape plus a five-tick confidence meter, with a text equivalent."""
    d = design(catalog)
    grade = str(story.get("evidence_class") or "")
    shape = GRADE_SHAPES.get(grade, "dashed")
    level = str(story.get("confidence") or "")
    ticks = CONFIDENCE_TICKS.get(level, 0)
    grade_text = label(catalog, "evidence_class", grade) or d["grade"]
    conf_text = label(catalog, "confidence", level) or catalog["strings"]["evidence_board"]["unrated"]
    parts = ['<rect x="1.5" y="1.5" width="21" height="21" rx="1" fill="none" stroke="currentColor" stroke-width="3"/>']
    if shape == "solid":
        parts = ['<rect x="1.5" y="1.5" width="21" height="21" rx="1" fill="currentColor" stroke="currentColor" stroke-width="3"/>']
    elif shape == "half":
        parts.append('<path d="M3 3 L21 21 L3 21 Z" fill="currentColor"/>')
    elif shape == "dashed":
        parts = ['<rect x="1.5" y="1.5" width="21" height="21" rx="1" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="3.5 3"/>']
    bars = []
    for index in range(5):
        height = 6 + index * 4
        x = 30 + index * 8
        y = 24 - height
        if index < ticks:
            bars.append(f'<rect x="{x}" y="{y}" width="5.5" height="{height}" fill="currentColor"/>')
        else:
            dash = ' stroke-dasharray="2 2"' if not ticks else ""
            bars.append(f'<rect x="{x + .75}" y="{y + .75}" width="4" height="{height - 1.5}" fill="none" stroke="currentColor" stroke-width="1.5"{dash}/>')
    text = f"{grade_text} · {conf_text}"
    return (f'<svg class="evidence-glyph evidence-glyph--{e(size)}" viewBox="0 0 72 24" role="img" aria-label="{e(text)}" '
            f'data-grade="{e(grade)}" data-ticks="{ticks}" focusable="false"><title>{e(text)}</title>{"".join(parts)}{"".join(bars)}</svg>')


def status_chip(status: dict, catalog: dict) -> str:
    """The edition state as a designed element: a shape, a word, and the date of the last edition."""
    d = design(catalog)
    state = str(reader_status(status).get("edition_state") or "DELAYED")
    text = d.get(f"state_{state}") or label(catalog, "edition_state", state) or state
    return f'<span class="status-chip" data-state="{e(state)}"><i aria-hidden="true"></i>{e(text)}</span>'


def automation_badge(status: dict, catalog: dict) -> str:
    """Disclosure that the text is machine-written, with the level of human review."""
    d = design(catalog)
    level = str(status.get("human_review") or "none")
    if level not in {"none", "sampled", "full"}:
        level = "none"
    return (f'<span class="automation-badge" data-human-review="{e(level)}"><i aria-hidden="true"></i>'
            f'{e(d["automation"])} · {e(d["review_" + level])}</span>')


def data_hero(story: dict, catalog: dict, *, evidence: dict | None = None) -> str:
    """A figure built from this story's own claims, sources and gaps (replaces the shared illustration)."""
    d = design(catalog)
    evidence = evidence if evidence is not None else (story.get("evidence") if isinstance(story.get("evidence"), dict) else {})
    claims = [c for c in (evidence.get("claims") or []) if isinstance(c, dict)]
    sources = story.get("sources") if isinstance(story.get("sources"), list) else []
    primary = sum(1 for s in sources if isinstance(s, dict) and s.get("primary"))
    gaps = len(evidence.get("gaps") or [])
    limits = len(evidence.get("limitations") or [])
    kinds = [claim_kind(c.get("label")) for c in claims]
    strip = "".join(f'<li class="dh-tile" data-kind="{kind}"><span class="visually-hidden">{e(d["kind_" + kind])}</span></li>'
                    for kind in kinds) or f'<li class="dh-tile dh-tile--empty" data-kind="OTHER"><span class="visually-hidden">{e(d["hero_none"])}</span></li>'
    legend = "".join(f'<li data-kind="{kind}"><i aria-hidden="true"></i><span>{e(d["kind_" + kind])}</span><b>{kinds.count(kind)}</b></li>'
                     for kind in KIND_ORDER if kinds.count(kind))
    figures = (f'<li><b>{len(claims)}</b><span>{e(d["hero_claims_n"])}</span></li>'
               f'<li><b>{primary}</b><span>{e(d["hero_sources"])}</span></li>'
               f'<li><b>{gaps}</b><span>{e(d["hero_gaps"])}</span></li>'
               f'<li><b>{limits}</b><span>{e(d["hero_limits"])}</span></li>')
    grade_text = label(catalog, "evidence_class", story.get("evidence_class"))
    return (f'<figure class="data-hero" data-claims="{len(claims)}" data-primary="{primary}" data-gaps="{gaps}" aria-label="{e(d["hero_title"])}">'
            f'<figcaption class="dh-head"><span class="dh-kicker">{e(d["hero_title"])}</span></figcaption>'
            f'<div class="dh-grade">{evidence_glyph(story, catalog, size="lg")}<span>{e(grade_text)}</span></div>'
            f'<p class="dh-label">{e(d["hero_claims"])}</p><ol class="dh-strip">{strip}</ol>'
            f'<ul class="dh-legend">{legend}</ul><ul class="dh-figures">{figures}</ul>'
            f'<p class="dh-note">{e(d["shape_note"])}</p></figure>')


def provenance_line(source: dict, catalog: dict) -> str:
    """``Original: author/org, "title", outlet, date · link`` using only the fields that are recorded."""
    d = design(catalog)
    who = source.get("author") or source.get("organization") or source.get("domain") or source.get("url", "")
    pieces = [f'<span translate="no" data-field="source-domain">{e(who)}</span>']
    title, outlet, date = source.get("title"), source.get("outlet"), source.get("published_at") or source.get("date")
    if title:
        pieces.append(f'“{e(title)}”')
    if outlet and outlet != who:
        pieces.append(f'<span translate="no">{e(outlet)}</span>')
    if date:
        pieces.append(f'<time>{e(date)}</time>')
    complete = bool(title and date)
    tail = "" if complete else f' <span class="prov-missing">({e(d["details_missing"])})</span>'
    link = f'<a href="{e(source.get("url", ""))}" rel="noopener noreferrer">{e(d["original_link"])}</a>'
    return (f'<p class="provenance" data-complete="{"yes" if complete else "no"}"><span class="prov-label">{e(d["original"])}:</span> '
            f'{", ".join(pieces)}{tail} · {link}</p>')


def primary_source(story: dict) -> dict | None:
    sources = [s for s in (story.get("sources") or []) if isinstance(s, dict) and s.get("url")]
    return next((s for s in sources if s.get("primary")), sources[0] if sources else None)


def brief(story: dict, catalog: dict, *, summary: object, why: object, evidence: dict) -> str:
    """R1: three short bullets, each the opening of text already on the page."""
    d = design(catalog)
    limits = evidence.get("limitations") or []
    gaps = evidence.get("gaps") or []
    unknown = ""
    for item in [*gaps, *limits]:
        text = item.get("description", "") if isinstance(item, dict) else item
        if text:
            unknown = first_sentence(text, 190)
            break
    items = [(d["happened"], first_sentence(summary)), (d["matters"], first_sentence(why)),
             (d["not_established"], unknown or d["none_recorded"])]
    rows = "".join(f'<li><span class="brief-key">{e(key)}</span><span class="brief-val">{e(text)}</span></li>' for key, text in items if text)
    return f'<div class="brief" role="group" aria-labelledby="brief-title"><h2 id="brief-title">{e(d["brief_title"])}</h2><ol>{rows}</ol></div>'


def reader_select(catalog: dict) -> str:
    """Summary / practitioner / researcher: only decides which layers start open."""
    d = design(catalog)
    modes = (("summary", d["mode_summary"]), ("practitioner", d["mode_practitioner"]), ("researcher", d["mode_researcher"]))
    buttons = "".join(f'<button type="button" data-mode="{k}" aria-pressed="{"true" if k == "summary" else "false"}">{e(v)}</button>' for k, v in modes)
    return (f'<div class="reader-select" hidden role="group" aria-label="{e(d["read_as"])}"><span class="rs-label">{e(d["read_as"])}</span>'
            f'<div class="rs-buttons">{buttons}</div><p class="rs-hint">{e(d["mode_hint"])}</p></div>')


LAYER_SCRIPT = r"""<script>(()=>{const root=document.querySelector('[data-layers]');if(!root)return;const sel=document.querySelector('.reader-select');if(!sel)return;
const open={summary:['argument','dossier'],practitioner:['argument','dossier'],researcher:['argument','dossier','technical']};
const apply=m=>{root.dataset.mode=m;document.querySelectorAll('details.layer').forEach(d=>{d.open=(open[m]||open.summary).includes(d.dataset.layer)});
sel.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===m)))};
let m='summary';try{m=localStorage.getItem('fcmo-reader-mode')||'summary'}catch(_){}if(!open[m])m='summary';sel.hidden=false;apply(m);
sel.addEventListener('click',ev=>{const b=ev.target.closest('button[data-mode]');if(!b)return;apply(b.dataset.mode);try{localStorage.setItem('fcmo-reader-mode',b.dataset.mode)}catch(_){}})})()</script>"""


def layer(kind: str, title: str, tag: str, inner: str, *, is_open: bool = True) -> str:
    """One collapsible reading layer. Open by default so the page reads fully without scripts."""
    if not inner:
        return ""
    return (f'<details class="layer" data-layer="{kind}"{" open" if is_open else ""}><summary><span class="layer-tag">{e(tag)}</span>'
            f'<span class="layer-title">{e(title)}</span></summary><div class="layer-body">{inner}</div></details>')


# ---------------------------------------------------------------------------
# c6 story layout (DIRECCION section 6). Pure functions over a story's own data and the
# UI catalog; every string comes from i18n/ui by key. Evidence classes are never colour
# alone: Shown = solid sample, Claimed = hatched sample, Not established = dashed sample,
# each always with its word.
#   claim kind DEMONSTRATED*            -> shown
#   claim kind CLAIMED*, VENDOR*, ...   -> claimed
#   INFERRED, SPECULATIVE, DISPUTED, other -> gap (not established: no source shows it)
# ---------------------------------------------------------------------------
PROOF_ORDER = ("shown", "claimed", "gap")
_PROOF_WORD_KEY = {"shown": "shown", "claimed": "claimed", "gap": "not_established"}
JUMP_ORDER = ("claims", "sources", "gaps", "limits", "technical")


def proof_class(claim_label: object) -> str:
    kind = claim_kind(claim_label)
    if kind == "DEMONSTRATED":
        return "shown"
    if kind == "CLAIMED" or str(claim_label or "").startswith("CLAIMED"):
        return "claimed"
    return "gap"


def proof_word(catalog: dict, cls: str) -> str:
    return catalog["strings"]["proof"][_PROOF_WORD_KEY[cls]]


def _fmt(template: str, **values: object) -> str:
    return template.format(**values)


def proof_counts(claims: list) -> dict:
    counts = {k: 0 for k in PROOF_ORDER}
    for claim in claims:
        if isinstance(claim, dict):
            counts[proof_class(claim.get("label"))] += 1
    return counts


def sample(cls: str) -> str:
    return f'<span class="sample sample-{cls}" aria-hidden="true"></span>'


def chip(cls: str, catalog: dict, *, count: int | None = None) -> str:
    word = proof_word(catalog, cls) + (f" {count}" if count is not None else "")
    return f'<span class="chip chip-{cls}">{sample(cls)}<span class="chip-word">{e(word)}</span></span>'


def _segments(claims: list, catalog: dict) -> str:
    rec = catalog["strings"]["record"]
    cells = []
    for index, claim in enumerate(c for c in claims if isinstance(c, dict)):
        cls = proof_class(claim.get("label"))
        cells.append(f'<span class="er-seg er-seg-{cls}" data-class="{cls}"></span>')
    if not cells:
        return f'<p class="er-none">{e(rec["none"])}</p>'
    counts = proof_counts(claims)
    text = _fmt(rec["bar_label"], shown=counts["shown"], claimed=counts["claimed"], not_established=counts["gap"])
    return f'<div class="er-bar" role="img" aria-label="{e(text)}">{"".join(cells)}</div>'


def _grade_plate(story: dict) -> str:
    return f'<span class="er-grade-plate" aria-hidden="true">{e(story.get("evidence_class") or "?")}</span>'


def _present_chips(claims: list, catalog: dict) -> str:
    counts = proof_counts(claims)
    return "".join(chip(cls, catalog, count=counts[cls]) for cls in PROOF_ORDER if counts[cls])


def story_signals(story: dict, catalog: dict, evidence: dict, *, status_html: str) -> str:
    """The compact Evidence Record: grade, one cell per claim, classes present, counts. Sits in the story cover."""
    claims = [c for c in (evidence.get("claims") or []) if isinstance(c, dict)]
    grade_text = label(catalog, "evidence_short", story.get("evidence_class")) or label(catalog, "evidence_class", story.get("evidence_class"))
    conf = label(catalog, "confidence", story.get("confidence"))
    sources = [s for s in (story.get("sources") or []) if isinstance(s, dict)]
    primary = sum(1 for s in sources if s.get("primary"))
    gaps = len(evidence.get("gaps") or [])
    return (f'<div class="story-signals"><span class="evrow-grade" aria-hidden="true">{e(story.get("evidence_class") or "?")}</span>'
            f'<span class="sig-text"><b>{e(grade_text)}</b>{" · " + e(conf) if conf else ""}</span>'
            f'{_segments(claims, catalog)}'
            f'<span class="evrow">{_present_chips(claims, catalog)}'
            f'<span>{e(plural(catalog, "primary_source", primary))}</span><span>{e(plural(catalog, "open_gap", gaps))}</span></span>{status_html}</div>')


def evidence_record(story: dict, catalog: dict, evidence: dict, *, jump_labels: dict) -> str:
    """The rail card (DIRECCION section 2): grade plate, segmented bar, legend, four counters, in-this-story list."""
    rec = catalog["strings"]["record"]
    claims = [c for c in (evidence.get("claims") or []) if isinstance(c, dict)]
    counts = proof_counts(claims)
    sources = [s for s in (story.get("sources") or []) if isinstance(s, dict)]
    primary = sum(1 for s in sources if s.get("primary"))
    gaps, limits = len(evidence.get("gaps") or []), len(evidence.get("limitations") or [])
    grade_text = label(catalog, "evidence_short", story.get("evidence_class")) or label(catalog, "evidence_class", story.get("evidence_class"))
    legend = "".join(f'<div><dt>{sample(cls)} {e(proof_word(catalog, cls))}</dt><dd>{counts[cls]}</dd></div>' for cls in PROOF_ORDER)
    nums = "".join(f'<div><b>{n}</b><span>{e(text)}</span></div>' for n, text in (
        (len(claims), rec["counter_claims"]), (primary, rec["counter_sources"]), (gaps, rec["counter_gaps"]), (limits, rec["counter_limits"])))
    toc = "".join(f'<li><a href="#{k}">{e(jump_labels[k])}</a></li>' for k in JUMP_ORDER if k in jump_labels)
    return (f'<div class="data-hero"><section class="er" aria-labelledby="er-title"><h2 id="er-title" class="er-title">{e(rec["title"])}</h2>'
            f'<div class="er-grade">{_grade_plate(story)}<div><b>{e(rec["grade"])} {e(story.get("evidence_class") or "")}</b><br>{e(grade_text)}</div></div>'
            f'{_segments(claims, catalog)}<dl class="er-legend">{legend}</dl><div class="er-counts">{nums}</div>'
            f'<h3 class="er-title">{e(rec["in_this_story"])}</h3><ul class="er-in-story">{toc}</ul></section></div>')


def brief20(story: dict, catalog: dict, *, summary: object, why: object, evidence: dict) -> str:
    """\"In 20 seconds\": what happened / why it matters / not established. The last cell is the dark one."""
    d = design(catalog)
    unknown = ""
    for item in [*(evidence.get("gaps") or []), *(evidence.get("limitations") or [])]:
        text = item.get("description", "") if isinstance(item, dict) else item
        if text:
            unknown = first_sentence(text, 190)
            break
    cells = [(d["happened"], first_sentence(summary), ""), (d["matters"], first_sentence(why), ""),
             (d["not_established"], unknown or d["none_recorded"], " read20-na")]
    rows = "".join(f'<li class="read20-cell{extra}"><b>{e(key)}</b><span class="brief-val">{e(text)}</span></li>' for key, text, extra in cells if text)
    return f'<div class="brief" role="group" aria-labelledby="brief-title"><h2 id="brief-title" class="visually-hidden">{e(d["brief_title"])}</h2><ol class="read20">{rows}</ol></div>'


def claim_ledger(evidence: dict, catalog: dict) -> str:
    """Always-open ledger: every claim with its class sample and word."""
    claims = [c for c in (evidence.get("claims") or []) if isinstance(c, dict)]
    st = catalog["strings"]
    items = []
    for claim in claims:
        cls = proof_class(claim.get("label"))
        detail = label(catalog, "claim_label", claim.get("label"),
                       fallback=label(catalog, "claim_label", f'{claim.get("label", "")}_{claim.get("qualifier", "")}'))
        gap = " chip-gap" if cls == "gap" else ""
        items.append(f'<li class="claim" data-kind="{e(claim_kind(claim.get("label")))}" data-class="{cls}"><div class="claim-class{gap}">{sample(cls)}'
                     f'<span><span class="chip-word">{e(proof_word(catalog, cls))}</span><br>{e(detail)}</span></div><p>{e(claim.get("text", ""))}</p></li>')
    body = f'<ul class="claims">{"".join(items)}</ul>' if items else f'<p>{e(st["record"]["none"])}</p>'
    return (f'<section id="claims" class="ledger" data-layer="dossier"><h2>{e(st["ledger"]["title"])}</h2>'
            f'<p class="ledger-intro">{e(st["ledger"]["intro"])}</p>{body}</section>')


def _bullets(values: list) -> str:
    return "".join(f'<li>{e(v.get("description", "") if isinstance(v, dict) else v)}</li>' for v in values)


def unknowns_box(evidence: dict, catalog: dict) -> str:
    """The oxblood «What we still don't know» box and the separate limits list."""
    st = catalog["strings"]
    gaps = evidence.get("gaps") or []
    limits = evidence.get("limitations") or []
    against = evidence.get("contradictory") or []
    out = [f'<aside id="gaps" class="unknowns" aria-labelledby="unknowns-title"><h2 id="unknowns-title" class="unknowns-title">{e(st["ledger"]["unknowns_title"])}</h2>'
           + (f'<ul>{_bullets(gaps)}</ul>' if gaps else f'<p>{e(st["design"]["none_recorded"])}</p>') + '</aside>']
    out.append(f'<section id="limits" class="limits"><h2>{e(st["ledger"]["limits_title"])}</h2>'
               + (f'<ul>{_bullets(limits)}</ul>' if limits else f'<p>{e(st["design"]["none_recorded"])}</p>') + '</section>')
    if against:
        out.append(f'<section class="against"><h2>{e(st["story"]["contradictory"])}</h2><ul>{_bullets(against)}</ul></section>')
    return "".join(out)


def sources_bar(story: dict, catalog: dict, *, automation_html: str, byline: str) -> str:
    """SOURCES strip under the headline: original source, byline, automation disclosure."""
    sb = catalog["strings"]["sources_bar"]
    src = primary_source(story)
    if src:
        who = src.get("author") or src.get("organization") or src.get("domain") or src.get("url", "")
        link = (f'<a href="{e(src.get("url", ""))}" rel="noopener noreferrer"><span translate="no">{e(who)}</span> ↗</a>')
        first = f'<span>{e(sb["original"])}: {link}</span>'
    else:
        first = ""
    return (f'<div class="srcbar"><div class="frame"><span class="rubric rubric-accent">{e(sb["title"])}</span> {first} '
            f'<span class="srcbar-by">{e(byline)}</span> {automation_html}</div></div>')


def jump_bar(catalog: dict, labels: dict) -> str:
    jb = catalog["strings"]["jump"]
    links = "".join(f'<a href="#{k}">{e(labels[k])}</a>' for k in JUMP_ORDER if k in labels)
    return f'<nav class="jumpbar" aria-label="{e(catalog["strings"]["a11y"]["jump_bar"])}"><div class="frame jumpbar-in">{links}</div></nav>'


def topic_pair(catalog: dict, topic: str, prev: tuple | None, nxt: tuple | None) -> str:
    """Previous/next inside a topic. Each tuple is (href, headline)."""
    sn = catalog["strings"]["story_nav"]
    cells = []
    for item, key in ((prev, "prev_in_topic"), (nxt, "next_in_topic")):
        if item:
            cells.append(f'<a href="{e(item[0])}" rel="{"prev" if key.startswith("prev") else "next"}"><span class="rubric">{e(_fmt(sn[key], topic=topic))}</span><b>{e(item[1])}</b></a>')
    if not cells:
        return ""
    return f'<nav class="pn" aria-label="{e(catalog["strings"]["a11y"]["topic_nav"])}">{"".join(cells)}</nav>'


def machine_strip(catalog: dict, *, json_href: str, cite_href: str, md_href: str) -> str:
    m = catalog["strings"]["machine"]
    return (f'<section class="mr" id="machine"><p class="rubric">{e(m["title"])}</p><p>{e(m["intro"])}</p>'
            f'<p><a href="{e(json_href)}">{e(m["record_json"])}</a> · <a href="{e(cite_href)}">{e(m["cite"])}</a> · '
            f'<a href="{e(md_href)}">Markdown</a> · <a href="#claims">{e(m["evidence_table"])}</a></p></section>')


def story_view(*, story: dict, catalog: dict, code: str, title: str, dek_text: str, beat_label: str, home_href: str,
               evidence: dict, summary: object, why: object, technical: dict, status_html: str,
               automation_html: str, byline: str, dates_line: str, plate_html: str, note_html: str,
               taxonomy_html: str, navigation_html: str, topic_nav_html: str, machine_html: str,
               title_class: str = "") -> str:
    """The whole story page body: cover, SOURCES, jump bar, reading grid with the Evidence Record rail."""
    st = catalog["strings"]
    jb = st["jump"]
    has_tech = bool(technical)
    labels = {"claims": jb["claims"], "sources": jb["sources"], "gaps": jb["gaps"], "limits": jb["limits"]}
    if has_tech:
        labels["technical"] = jb["technical"]
    d = design(catalog)
    argument = "".join(f'<section><h2>{e(st["story"][k])}</h2><p>{e(v)}</p></section>'
                       for k, v in (("what_changed", summary), ("why_it_matters", why)) if v)
    tech_html = "".join(f'<section><h3>{e(st["technical_field"].get(k, k))}</h3><p>{e(v)}</p></section>' for k, v in technical.items() if v)
    sources = [s for s in (story.get("sources") or []) if isinstance(s, dict)]
    src_items = "".join(f'<li>{provenance_line(s, catalog)}' + (f'<span class="prov-primary">{e(st["story"]["primary_source"])}</span>' if s.get("primary") else "") + '</li>' for s in sources)
    sources_html = f'<section id="sources"><h2>{e(st["story"]["sources"])}</h2><ol class="source-list">{src_items}</ol></section>' if src_items else f'<section id="sources"><h2>{e(st["story"]["sources"])}</h2></section>'
    crumbs = f'<nav class="crumbs" aria-label="{e(st["a11y"]["breadcrumbs"])}"><a href="{e(home_href)}">{e(st["nav"]["today"])}</a> / {e(beat_label)}</nav>'
    cover = (f'<header class="story-header story-cover surface-ink"><div class="frame story-cover-grid"><div class="sh-main">{crumbs}'
             f'<p class="story-kicker rubric rubric-accent">{e(beat_label)}</p><h1>{e(title)}</h1><p class="story-dek">{e(dek_text)}</p>'
             f'{story_signals(story, catalog, evidence, status_html=status_html)}'
             f'<p class="story-meta rubric">{e(dates_line)}</p>{note_html}</div>{plate_html}</div></header>')
    body = (brief20(story, catalog, summary=summary, why=why, evidence=evidence)
            + '<div class="layers" data-layers data-mode="summary">' + layer("argument", d["argument_title"], d["layer_r2"], argument)
            + '</div>' + claim_ledger(evidence, catalog) + unknowns_box(evidence, catalog) + sources_html
            + ('<div class="layers">' + layer("technical", d["technical_title"], d["layer_r3"], f'<div id="technical">{tech_html}</div>', is_open=False) + '</div>' if has_tech else "")
            + machine_html)
    rail = f'<aside class="read-rail story-aside">{evidence_record(story, catalog, evidence, jump_labels=labels)}{taxonomy_html}</aside>'
    return (cover + sources_bar(story, catalog, automation_html=automation_html, byline=byline) + jump_bar(catalog, labels)
            + f'<div class="frame read-layout"><div class="read-toc-slot"></div><div class="story-body">{body}</div>{rail}</div>'
            + f'<div class="frame story-after">{topic_nav_html}{navigation_html}</div>' + LAYER_SCRIPT)
