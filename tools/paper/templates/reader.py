"""Reader-design elements: evidence glyph, per-story data hero, status, disclosure, provenance, layers.

Everything here is derived from a story's own data; nothing is invented. Text crosses
``html.escape``. Shape and stroke carry the evidence grade and confidence, so they
survive greyscale and colour-blind reading; colour only reinforces.
"""

from __future__ import annotations

from html import escape
import re

from ..i18n import label, plural, truncate

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
    state = str(status.get("edition_state") or "DELAYED")
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
const open={summary:['argument'],practitioner:['argument','dossier'],researcher:['dossier','technical']};
const apply=m=>{root.dataset.mode=m;root.querySelectorAll('details.layer').forEach(d=>{d.open=(open[m]||open.summary).includes(d.dataset.layer)});
sel.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===m)))};
let m='summary';try{m=localStorage.getItem('fcmo-reader-mode')||'summary'}catch(_){}if(!open[m])m='summary';sel.hidden=false;apply(m);
sel.addEventListener('click',ev=>{const b=ev.target.closest('button[data-mode]');if(!b)return;apply(b.dataset.mode);try{localStorage.setItem('fcmo-reader-mode',b.dataset.mode)}catch(_){}})})()</script>"""


def layer(kind: str, title: str, tag: str, inner: str) -> str:
    """One collapsible reading layer. Open by default so the page reads fully without scripts."""
    if not inner:
        return ""
    return (f'<details class="layer" data-layer="{kind}" open><summary><span class="layer-tag">{e(tag)}</span>'
            f'<span class="layer-title">{e(title)}</span></summary><div class="layer-body">{inner}</div></details>')
