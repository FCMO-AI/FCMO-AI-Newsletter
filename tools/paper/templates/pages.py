"""Page-level semantic templates."""

from __future__ import annotations

from collections import Counter
from html import escape

from ..front_plan import evidence_class as item_class
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


def archive_page(title: str, intro: str, items: str, *, kicker: str, title_html: str | None = None,
                 context: str = "", navigation: str = "") -> str:
    rendered_title = title_html if title_html is not None else e(title)
    return f'<header><p class="section-kicker">FCMO AI · {e(kicker)}</p><h1 class="page-title">{rendered_title}</h1><p>{e(intro)}</p>{context}</header>{navigation}<div class="archive-list">{items}</div>'


def status_page(title: str, cards: str, detail: str, *, kicker: str) -> str:
    return f'<header><p class="section-kicker">FCMO AI · {e(kicker)}</p><h1 class="page-title">{e(title)}</h1></header><div class="status-grid">{cards}</div>{detail}'


def simple_page(title: str, body: str, *, kicker: str = "FCMO AI") -> str:
    return f'<article class="story-body"><header><p class="section-kicker">{e(kicker)}</p><h1 class="page-title">{e(title)}</h1></header>{body}</article>'


def _class_word(catalog: dict, value: object) -> str:
    """Evidence-class word for a correction. Reads ``strings.proof``; unknown classes fall back to the catalog label."""
    proof = catalog["strings"]["proof"]
    key = {"DEMONSTRATED": "shown", "SHOWN": "shown", "CLAIMED": "claimed",
           "NOT_ESTABLISHED": "not_established"}.get(str(value).upper())
    return str(proof[key]) if key else label(catalog, "evidence_class", value)


def class_chip(catalog: dict, klass: str) -> str:
    """Evidence class as sample + word (never colour alone); ``klass`` is shown / claimed / not_established."""
    sample = {"shown": "shown", "claimed": "claimed", "not_established": "gap"}.get(klass, "gap")
    word = catalog["strings"]["proof"].get(klass, klass)
    return (f'<span class="chip chip-{sample}"><span class="sample sample-{sample}" aria-hidden="true"></span>'
            f'<span class="chip-word"><strong>{e(word)}</strong></span></span>')


def class_line(story: dict, catalog: dict, *, grade: bool = True, counts: bool = True) -> str:
    """One evidence line for a list row: the class chip, the grade only when asked, then primary sources and gaps."""
    parts = [class_chip(catalog, item_class(story))]
    if grade and story.get("evidence_class"):
        parts.append(f'<span class="grade-note">{e(label(catalog, "evidence_class", story.get("evidence_class")))}</span>')
    if counts:
        facts = evidence_counts(story)
        parts.append(f'<span>{e(plural(catalog, "primary_source", facts["primary"]))}</span>')
        parts.append(f'<span>{e(plural(catalog, "open_gap", facts["gaps"]))}</span>')
    return f'<p class="evrow list-evrow" data-evidence-class="{e(item_class(story))}">{"".join(parts)}</p>'


def archive_day(day_id: str, heading: str, rows: str) -> str:
    return f'<section class="archive-day" id="{e(day_id)}"><h2 class="archive-day-head">{e(heading)}</h2>{rows}</section>'


def archive_jump(catalog: dict, days: list[tuple[str, str]]) -> str:
    """Jump links to the days present on this page (day id, short label); only worth showing for several days."""
    if len(days) < 3:
        return ""
    links = "".join(f'<a href="#{e(day_id)}">{e(text)}</a>' for day_id, text in days[:16])
    return f'<nav class="archive-jump" aria-label="{e(catalog["strings"]["archive"]["jump"])}"><span>{e(catalog["strings"]["archive"]["jump"])}</span>{links}</nav>'


def archive_pager(catalog: dict, *, number: int, pages: int, newer: str = "", older: str = "") -> str:
    """Pager under the list: newer link, where you are, older link (links are ready-made anchors)."""
    if pages <= 1:
        return ""
    status = f'<span class="archive-pager-status">{e(catalog["strings"]["archive"]["page_of"].format(n=number, total=pages))}</span>'
    return (f'<nav class="archive-pager" data-pagination aria-label="{e(catalog["strings"]["archive"]["pager"])}">'
            f'{newer}{status}{older}</nav>')


def correction_row(*, catalog: dict, title: str, note: str, date_iso: str, date_text: str,
                   story_href: str, correction_href: str, class_before: object = None,
                   class_after: object = None, reason: str = "", title_lang: str = "",
                   kind_text: str = "", lead_in: str = "") -> str:
    """One entry of the corrections list: the story title first, then kind and date, the note and the class before/after.

    The class line is printed only when both classes are recorded; when they are
    equal (or only the current one is known) it says the class did not change.
    Nothing is inferred: absent data prints no class claim at all.
    """
    ui = catalog["strings"]["corrections_ui"]
    line = ""
    if class_before and class_after:
        before, after = _class_word(catalog, class_before), _class_word(catalog, class_after)
        text = (ui["class_unchanged"] if str(class_before) == str(class_after)
                else ui["class_change"].format(before=before, after=after))
        line = (f'<p class="correction-class" data-class-before="{e(class_before)}" data-class-after="{e(class_after)}">'
                f'{e(text)}</p>')
    why = f'<p class="correction-reason"><strong>{e(ui["reason"])}</strong> {e(reason)}</p>' if reason else ""
    kind = f'<span class="correction-kind">{e(kind_text)}</span> · ' if kind_text else ""
    lead = f'<p class="correction-lead">{e(lead_in)}</p>' if lead_in else ""
    return (f'<article class="correction">{lead}'
            f'<h2><a href="{e(correction_href)}"{f' lang="{e(title_lang)}"' if title_lang else ""}>{e(title)}</a></h2>'
            f'<p class="correction-meta">{kind}<time datetime="{e(date_iso)}">'
            f'{e(ui["corrected_on"].format(date=date_text))}</time></p><p>{e(note)}</p>{why}{line}'
            f'<p class="correction-links"><a class="correction-story" href="{e(story_href)}">{e(ui["story_link"])}</a></p></article>')


def corrections_intro(catalog: dict, *, method_href: str) -> str:
    page = catalog["strings"]["corrections_page"]
    return (f'<p>{e(page["intro"])}</p>'
            f'<p><a class="correction-method" href="{e(method_href)}">{e(page["method_link"])}</a></p>')


def method_order_section(catalog: dict) -> str:
    """How the front page is ordered; the text is the single definition (``method.order_body``)."""
    method = catalog["strings"]["method"]
    return (f'<section class="method-order" id="order"><h2>{e(method["order_title"])}</h2>'
            f'<p>{e(method["order_body"])}</p></section>')
