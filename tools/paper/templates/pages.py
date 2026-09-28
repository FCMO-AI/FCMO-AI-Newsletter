"""Page-level semantic templates."""

from __future__ import annotations

from collections import Counter
from html import escape

from ..i18n import label, plural

# The five base claim families keep full weight on the board; finer labels stay
# separate (never merged into a family) but read as the long tail.
CLAIM_FAMILIES = ("DEMONSTRATED", "CLAIMED", "INFERRED", "SPECULATIVE", "DISPUTED")


def e(value: object) -> str:
    return escape(str(value), quote=True)


def _raw(value: object) -> str:
    return "" if value is None else str(value)


def evidence_counts(story: dict) -> dict:
    """Corpus evidence facts for one story; absent evidence or sources count as zero."""
    evidence = story.get("evidence") if isinstance(story.get("evidence"), dict) else {}
    sources = story.get("sources") if isinstance(story.get("sources"), list) else []
    claims = evidence.get("claims") if isinstance(evidence.get("claims"), list) else []
    gaps = evidence.get("gaps") if isinstance(evidence.get("gaps"), list) else []
    return {
        "primary": sum(1 for source in sources if isinstance(source, dict) and source.get("primary")),
        "gaps": len(gaps),
        "claims": len(claims),
        "labels": [(claim.get("label") if isinstance(claim, dict) else None) or "UNLABELED" for claim in claims],
    }


def confidence_key(story: dict, catalog: dict) -> str:
    value = story.get("confidence")
    return str(value) if value is not None and str(value) in catalog.get("labels", {}).get("confidence", {}) else "unrated"


def _confidence_text(key: str, catalog: dict) -> str:
    return catalog["strings"]["evidence_board"]["unrated"] if key == "unrated" else label(catalog, "confidence", key)


def evidence_strip(story: dict, catalog: dict) -> str:
    counts = evidence_counts(story)
    level = confidence_key(story, catalog)
    grade = label(catalog, "evidence_class", story.get("evidence_class"))
    parts = [f'<span class="evidence-grade">{e(grade)}</span>'] if grade else []
    parts.append(f'<span class="evidence-level" data-level="{e(level)}">{e(_confidence_text(level, catalog))}</span>')
    parts.append(f'<span>{e(plural(catalog, "primary_source", counts["primary"]))}</span>')
    parts.append(f'<span>{e(plural(catalog, "open_gap", counts["gaps"]))}</span>')
    return (f'<p class="evidence-strip" data-evidence-class="{e(_raw(story.get("evidence_class")))}" '
            f'data-confidence="{e(_raw(story.get("confidence")))}" data-primary-sources="{counts["primary"]}" '
            f'data-open-gaps="{counts["gaps"]}" data-claims="{counts["claims"]}">'
            + '<span class="evidence-sep" aria-hidden="true"> · </span>'.join(parts) + '</p>')


def _figure(catalog: dict, key: str, count: int) -> str:
    before, _, after = plural(catalog, key, count).partition(str(count))
    return f'<li>{e(before)}<strong>{count}</strong><span>{e(after.strip())}</span></li>'


def evidence_board(stories: list[dict], catalog: dict, *, method_href: str = "") -> str:
    """Aggregate the corpus evidence of every live story, without inventing a grade."""
    strings = catalog["strings"]["evidence_board"]
    counts = [evidence_counts(story) for story in stories]
    primary = sum(item["primary"] for item in counts)
    gaps = sum(item["gaps"] for item in counts)
    claims = Counter(value for item in counts for value in item["labels"])
    total_claims = sum(claims.values())
    levels = Counter(confidence_key(story, catalog) for story in stories)
    order = [*catalog.get("labels", {}).get("confidence", {}), "unrated"]
    segments = [(key, levels[key]) for key in order if levels[key] >= 1]
    bar = "".join(f'<span class="evidence-seg" data-segment="{e(key)}" data-count="{count}" style="flex-grow:{count}"></span>'
                  for key, count in segments)
    legend = "".join(f'<li data-legend="{e(key)}"><span class="evidence-swatch" aria-hidden="true"></span>'
                     f'<span>{e(_confidence_text(key, catalog))}</span><strong>{count}</strong></li>' for key, count in segments)
    catalog_labels = list(catalog.get("labels", {}).get("claim_label", {}))
    ranked = sorted(claims, key=lambda value: (value == "UNLABELED", value not in catalog_labels,
                                               catalog_labels.index(value) if value in catalog_labels else 0, value))
    claim_items = []
    for value in ranked:
        count = claims[value]
        text = (strings["unlabeled"] if value == "UNLABELED"
                else label(catalog, "claim_label", value) or strings["uncatalogued"])
        tail = "" if value in CLAIM_FAMILIES else " evidence-claim--tail"
        share = round(100 * count / total_claims, 1) if total_claims else 0
        claim_items.append(f'<li><span class="evidence-claim{tail}" data-claim-label="{e(value)}" data-count="{count}" '
                           f'style="--share:{share}%"><strong>{count}</strong> <span>{e(text)}</span></span></li>')
    method = f'<a class="evidence-method" href="{e(method_href)}">{e(strings["method"])}</a>' if method_href else ""
    return (f'<section id="evidence-board" class="evidence-board" data-stories="{len(stories)}" '
            f'data-primary-sources="{primary}" data-open-gaps="{gaps}" data-claims="{total_claims}" '
            f'aria-labelledby="evidence-board-title">'
            f'<div class="evidence-board-head"><p class="section-kicker">FCMO AI · {e(catalog["strings"]["story"]["evidence"])}</p>'
            f'<h2 id="evidence-board-title">{e(strings["title"])}</h2><p class="evidence-board-dek">{e(strings["dek"])}</p>{method}</div>'
            f'<ul class="evidence-figures">{_figure(catalog, "live_story", len(stories))}'
            f'{_figure(catalog, "primary_source", primary)}{_figure(catalog, "open_gap", gaps)}</ul>'
            f'<div class="evidence-confidence"><h3>{e(strings["confidence_heading"])}</h3>'
            f'<div class="evidence-bar" aria-hidden="true">{bar}</div><ol class="evidence-legend">{legend}</ol></div>'
            f'<div class="evidence-claims"><h3>{e(strings["claims_heading"])} · {e(plural(catalog, "claim", total_claims))}</h3>'
            f'<ul>{"".join(claim_items)}</ul></div></section>')


def story_card(story: dict, *, href: str, headline: str, dek: str, beat: str, date: str, level: int = 2,
               context: str = "", evidence: str = "") -> str:
    heading = max(2, min(level, 3))
    return f'''<article class="story-card" data-story-id="{e(story.get('id', ''))}"><span class="card-meta">{e(beat)} · {e(date)} · {e(context)}</span><h{heading}><a href="{e(href)}">{e(headline)}</a></h{heading}><p>{e(dek)}</p>{evidence}</article>'''


def front_page(*, lead: str, top: str, essentials: str, beats: str, developing: str,
               subscribe: str, cartas: str, editions: str, signal: str = "", board: str = "") -> str:
    return f'''<div class="front-grid">{lead}<aside class="top-stories">{top}</aside></div>{signal}{board}
<section class="essentials">{essentials}</section>{beats}{developing}
<div class="front-tail"><div class="slot" data-slot="cartas"><!-- slot:cartas -->{cartas}</div><div class="slot" data-slot="subscribe"><!-- slot:subscribe -->{subscribe}</div></div>{editions}'''


def story_page(*, header: str, body: str, aside: str, hero: str = "", navigation: str = "") -> str:
    return f'<article class="story-layout">{header}<div class="story-body">{hero}{body}{navigation}</div><aside class="story-aside">{aside}</aside></article>'


def archive_page(title: str, intro: str, items: str, *, title_html: str | None = None,
                 context: str = "", navigation: str = "") -> str:
    rendered_title = title_html if title_html is not None else e(title)
    return f'<header><p class="section-kicker">FCMO AI · archive</p><h1 class="page-title">{rendered_title}</h1><p>{e(intro)}</p>{context}</header>{navigation}<div class="archive-list">{items}</div>'


def status_page(title: str, cards: str, detail: str) -> str:
    return f'<header><p class="section-kicker">FCMO AI · operations</p><h1 class="page-title">{e(title)}</h1></header><div class="status-grid">{cards}</div>{detail}'


def simple_page(title: str, body: str, *, kicker: str = "FCMO AI") -> str:
    return f'<article class="story-body"><header><p class="section-kicker">{e(kicker)}</p><h1 class="page-title">{e(title)}</h1></header>{body}</article>'
