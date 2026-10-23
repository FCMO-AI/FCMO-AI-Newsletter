#!/usr/bin/env python3
"""Build the FCMO AI newspaper as locale-specific static HTML."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
from html import escape
import json
import os
from pathlib import Path
import shutil
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.paper import community, essays, feeds, redirects, search_index, sitemaps
    from tools.paper.freshness import corpus_freshness
    from tools.paper.front_order import front_order
    from tools.paper.front_plan import front_plan
    from tools.paper import front_plan as plan_mod
    from tools.agent import build as agent_layer
    from tools.paper.i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, plural, story_locale, truncate
    from tools.paper.routes import slugify, absolute, beat_path, edition_path, href, issue_path, org_path, output_path, piece_path, story_path, topic_path
    from tools.paper.status_banner import freshness_attributes, freshness_sentence, render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from tools.paper.templates import archive_page, document, front_page, simple_page, status_page, story_page
    from tools.paper.templates.pages import (archive_day, archive_jump, archive_pager, class_chip, class_line, correction_row, corrections_intro,
                                             evidence_board, evidence_strip, method_order_section, story_card)
    from tools.paper.templates.landing import front_context, render as render_landing
    from tools.paper.templates.reader import (LAYER_SCRIPT, automation_badge, brief, claim_kind, data_hero, evidence_glyph,
                                              first_sentence, layer, primary_source, provenance_line, reader_select, status_chip, story_view, topic_pair, machine_strip)
    from tools.paper.templates.newsletter import render as render_newsletter, subscription_tail
    from tools.paper.routes import TECHNICAL_FRONT
else:
    from . import community, essays, feeds, redirects, search_index, sitemaps
    from .freshness import corpus_freshness
    from .front_order import front_order
    from .front_plan import front_plan
    from . import front_plan as plan_mod
    from tools.agent import build as agent_layer
    from .i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, plural, story_locale, truncate
    from .routes import slugify, absolute, beat_path, edition_path, href, issue_path, org_path, output_path, piece_path, story_path, topic_path
    from .status_banner import freshness_attributes, freshness_sentence, render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from .templates import archive_page, document, front_page, simple_page, status_page, story_page
    from .templates.pages import (archive_day, archive_jump, archive_pager, class_chip, class_line, correction_row, corrections_intro,
                                  evidence_board, evidence_strip, method_order_section, story_card)
    from .templates.landing import front_context, render as render_landing
    from .templates.reader import (LAYER_SCRIPT, automation_badge, brief, claim_kind, data_hero, evidence_glyph,
                                   first_sentence, layer, primary_source, provenance_line, reader_select, status_chip, story_view, topic_pair, machine_strip)
    from .templates.newsletter import render as render_newsletter, subscription_tail
    from .routes import TECHNICAL_FRONT

ROOT = Path(__file__).resolve().parents[2]
from tools.publication_freshness import publication_status, reader_status
BEATS = ("technology", "business", "policy", "society", "research")
LISTING_PAGE_SIZE = 100

SEARCH_JS = r'''(()=>{const f=document.querySelector('[data-search-form]'),q=document.querySelector('[data-search-input]'),o=document.querySelector('[data-search-results]');if(!f)return;const sg=document.querySelector('[data-search-suggest]');let rows,pending,serial=0;const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const lang=()=>(document.documentElement||{}).lang||'';const cut=(t,n=/^zh/i.test(lang())?100:220)=>{if(t.length<=n)return t;let e=0;try{for(const g of new Intl.Segmenter(lang()||undefined,{granularity:'word'}).segment(t)){if(g.index+g.segment.length>n)break;e=g.index+g.segment.length}}catch{e=Math.max(t.lastIndexOf(' ',n),0)}return t.slice(0,e||n).replace(/[\s,;:.\u3001\u3002\uff0c\uff1b\uff1a!?\uff01\uff1f-]+$/,'')+'\u2026'};const suggest=on=>{if(sg)sg.hidden=!on};const go=async value=>{const run=++serial,term=String(value).trim().toLocaleLowerCase();if(!term){o.innerHTML='';suggest(true);return}if(!rows){o.textContent=o.dataset.loading;try{pending??=Promise.all((f.dataset.shards?JSON.parse(f.dataset.shards):[f.dataset.index]).map(url=>fetch(url).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}))).then(parts=>parts.flat());rows=await pending}catch{pending=undefined;if(run===serial)o.textContent=o.dataset.error;return}}if(run!==serial)return;try{const u=new URL(location.href);u.searchParams.set('q',String(value).trim());history.replaceState(null,'',u)}catch{}const all=rows.filter(x=>[x.h,x.d,x.b,...x.o,...x.t,x.search_text||''].join(' ').toLocaleLowerCase().includes(term)),hits=all.slice(0,30);suggest(!hits.length);const tpl=all.length===1?o.dataset.resultsOne:all.length>hits.length?o.dataset.resultsMore:o.dataset.resultsFor,head=hits.length&&tpl?`<p class="search-count">${esc(tpl.replace('{count}',()=>all.length).replace('{shown}',()=>hits.length).replace('{query}',()=>String(value).trim()))}</p>`:'';o.innerHTML=hits.length?head+hits.map(x=>`<article class="story-card"><span class="card-meta">${esc(x.b)}${x.f?' · '+esc(x.f):''}</span><h2><a href="${esc(x.u)}">${esc(x.h)}</a></h2><p>${esc(cut(x.d))}</p>${x.w?`<p class="evrow list-evrow"><span class="chip chip-${esc(x.k||'gap')}"><span class="sample sample-${esc(x.k||'gap')}" aria-hidden="true"></span><span class="chip-word"><strong>${esc(x.w)}</strong></span></span></p>`:''}</article>`).join(''):`<p>${esc(o.dataset.empty.replace('{query}',term))}</p>`};f.addEventListener('submit',e=>{e.preventDefault();return go(q.value)});f.addEventListener('input',()=>go(q.value));try{const init=new URLSearchParams(location.search).get('q');if(init){q.value=init;go(init)}}catch{}})()'''


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def copy_public_tree(source: Path, target: Path) -> None:
    """Copy file bytes and directory shape only; host ACLs, xattrs and modes are not publication data."""
    for directory, _, files in os.walk(source, followlinks=True):
        relative = Path(directory).relative_to(source)
        (target / relative).mkdir(parents=True, exist_ok=True)
        for name in files:
            shutil.copyfile(Path(directory) / name, target / relative / name)




# A jump link that targets something inside a closed <details> (the technical layer) must open it.
JUMP_OPEN_SCRIPT = ('<script>(()=>{const o=()=>{const t=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));'
                    'const d=t&&t.closest("details");if(d){d.open=true;t.scrollIntoView()}};'
                    'addEventListener("hashchange",o);document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("a[href^=\'#\']");'
                    'if(a)setTimeout(o,0)});o()})()</script>')


class PaperBuilder:
    def __init__(self, *, stories_path: Path, status_path: Path, out: Path, base: str,
                 editorial_path: Path | None = None, og_source: Path | None = None,
                 citation_history: Path | None = None) -> None:
        self.stories_path = stories_path
        self.status_path = status_path
        self.payload = json.loads(stories_path.read_text(encoding="utf-8"))
        self.status = json.loads(status_path.read_text(encoding="utf-8"))
        self.config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
        self.catalogs = load_catalogs(ROOT)
        self.stories = self.payload["stories"]
        self.live = [story for story in self.stories if story.get("status") == "live"]
        self.edition_dates = sorted(set(self.payload.get("published_edition_dates", [])) | {story["url_date"] for story in self.live}, reverse=True)
        self.freshness = corpus_freshness(self.live, self.status.get("status_updated_at"))
        self.status["publication_status"] = publication_status(self.freshness, self.status, stories=self.stories)
        self.out = out
        self.base = "/" + base.strip("/") + "/" if base.strip("/") else "/"
        self.base_url = self.config["base_url"]
        self.og_source = og_source
        self.editorial_path = editorial_path or ROOT / "editorial"
        self.editorial_pieces, self.editorial_issues = essays.load_editorial(self.editorial_path)
        self.citation_history = citation_history or (ROOT / "site" / "data" / "citations")
        self.cartas = community.fetch_cartas(os.environ.get("GHOST_CONTENT_URL"), os.environ.get("GHOST_CONTENT_API_KEY"))
        self.portal_url = os.environ.get("GHOST_PORTAL_URL")
        self.routes: list[dict] = []
        self.page_count = 0

    def _editorial_routes(self, locale: dict) -> None:
        code = locale["code"]
        prefix = locale["path_prefix"]
        by_id = {piece["id"]: piece for piece in self.editorial_pieces}
        stories_by_id = {story["id"]: story for story in self.live}
        # Public source data accompanies the build so PIECE_VALID can independently
        # re-read exactly what the renderer consumed.
        for piece in self.editorial_pieces:
            title, description, body = essays.render_piece(piece, code, base=self.base, locale_info=locale,
                                                            locales=self.config["locales"], catalog=self.catalogs[code])
            slug = piece["slug"]
            suffix = piece_path({"path_prefix": ""}, piece)
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=description,
                             body=body, kind="essay", status=True,
                             index=(piece["status"] == "published" and piece["locales"][code] == "ready"))
        for issue in self.editorial_issues:
            title, description, body = essays.render_issue(issue, code, by_id, stories_by_id,
                                                           base=self.base, catalog=self.catalogs[code])
            suffix = issue_path({"path_prefix": ""}, issue)
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=description,
                             body=body, kind="issue", index=True)
        # Issue and piece links are represented in every locale's discovery index;
        # pending translations intentionally do not leak source prose.

    def _alternates(self, suffix: str) -> list[tuple[str, str]]:
        values = [(loc["hreflang"], absolute(self.base_url, loc["path_prefix"] + suffix)) for loc in self.config["locales"]]
        default = next(loc for loc in self.config["locales"] if loc["code"] == self.config["x_default_locale"])
        values.append(("x-default", absolute(self.base_url, default["path_prefix"] + suffix)))
        return values

    def _header_search(self, locale: dict, suffix: str) -> str:
        """Header search field (type, Enter): a progressive enhancement injected by a tiny script on every page but search itself."""
        if suffix == "search/":
            return ""
        strings = self.catalogs[locale["code"]]["strings"]
        action = href(self.base, locale["path_prefix"] + "search/")
        return (f'<script defer src="{esc(href(self.base, "assets/js/header-search.js"))}" data-action="{esc(action)}" '
                f'data-label="{esc(strings["a11y"]["search_label"])}" data-placeholder="{esc(strings["search"]["title"])}"></script>')

    def _write_page(self, *, locale: dict, suffix: str, title: str, description: str, body: str,
                    kind: str, story: dict | None = None, og_image: str | None = None,
                    json_ld: dict | None = None, extra_head: str = "", status: bool = True,
                    index: bool = True, alternates: bool = True,
                    machine_alternates: list[tuple[str, str]] | None = None) -> None:
        route = locale["path_prefix"] + suffix
        canonical = absolute(self.base_url, route)
        alts = self._alternates(suffix) if alternates else [(locale["hreflang"], canonical)]
        html = document(
            locale=locale, catalog=self.catalogs[locale["code"]], config=self.config,
            base=self.base, path=suffix, title=title, description=description, body=body,
            canonical=canonical, alternates=alts, og_image=og_image, page_type="article" if story else "website",
            status_banner=render_banner(self.status, self.catalogs[locale["code"]], base=self.base, locale=locale, freshness=self.freshness) if status else "",
            json_ld=json_ld, extra_head=extra_head + self._header_search(locale, suffix), body_class=f"page-{kind}",
            story_id=story["id"] if story else None, machine_alternates=machine_alternates,
        )
        target = output_path(self.out, route)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        lastmod = story["updated_at"] if story else self.status["status_updated_at"]
        record = {"url": canonical, "path": route, "kind": kind, "locale": locale["code"], "lastmod": lastmod, "alternates": alts, "index": index}
        if story:
            record.update({"story_id": story["id"], "published": story["first_published_at"], "title": headline(story, locale["code"], self.catalogs[locale["code"]])})
        self.routes.append(record)
        self.page_count += 1

    def _story_href(self, locale: dict, story: dict) -> str:
        return href(self.base, story_path(locale, story))

    def _correction_href(self, locale: dict, story: dict) -> str:
        return href(self.base, locale["path_prefix"] + "corrections/story/" + story["slug"] + "/")

    def _media_url(self, story: dict, locale: dict | None = None) -> str:
        if self.og_source is not None and locale is not None:
            return absolute(self.base_url, f'og/{locale["code"]}/{story["id"]}.png')
        return absolute(self.base_url, self._story_media_path(story, locale))

    def _story_media_url(self, story: dict, locale: dict | None = None) -> str:
        return href(self.base, self._story_media_path(story, locale))

    @staticmethod
    def _story_media_path(story: dict, locale: dict | None = None) -> str:
        media = story.get("media") or {}
        local = str(media.get("local_path") or "assets/explainers/research.svg").lstrip("/")
        if locale and locale["code"] in {"es-419", "zh-Hans"} and media.get("kind") == "explainer":
            local = f'assets/story-media/{story["id"]}-{locale["code"]}.svg'
        return local

    @staticmethod
    def _title_class(title: str, locale_code: str, hero: bool = False) -> str:
        """Estimate display width with wider weights for CJK glyphs."""
        import unicodedata
        width = 0.0
        for char in title:
            if locale_code == "zh-Hans" and unicodedata.east_asian_width(char) in {"W", "F"}:
                width += 1.7
            elif char.isalnum():
                width += 0.55
            else:
                width += 0.35
        # The 65-unit cutoff is calibrated from the measured five-line Spanish
        # titles (82.8–92.4 units) and the 1040px story header at 51.84px compact
        # type. It leaves room for four lines before titles take the smaller step.
        if width > 65:
            return "title-extra-compact"
        if width > 58:
            return "title-compact"
        # The landing hero is a ~694px column at 66px (title-medium), not the 1040px story header the cutoffs above
        # were calibrated on: an 84-character Spanish lead (43 units) wrapped to five lines there. Hence the earlier step.
        if width > (38 if hero else 46):
            return "title-large"
        if width > 34:
            return "title-medium"
        return "title-short"

    def _card(self, story: dict, locale: dict, level: int = 2) -> str:
        catalog = self.catalogs[locale["code"]]
        context = label(catalog, "evidence_class", story.get("evidence_class"))
        return story_card(
            story, href=self._story_href(locale, story), headline=headline(story, locale["code"], catalog),
            dek=truncate(dek(story, locale["code"], catalog), 190), beat=label(catalog, "beat", story.get("beat")),
            date=format_date(story["event_at"], catalog, precision=story.get("date_precision", "day")), level=level,
            context=context, evidence=evidence_strip(story, catalog),
        )

    def _record_card(self, story: dict, locale: dict) -> str:
        """A compact card for reading lists on the subscribe pages: the evidence class once."""
        catalog = self.catalogs[locale["code"]]
        code = locale["code"]
        date = format_date(story["event_at"], catalog, precision=story.get("date_precision", "day"))
        return (f'<article class="story-card" data-story-id="{esc(story["id"])}"><span class="card-meta">{esc(label(catalog, "beat", story.get("beat")))} · {esc(date)}</span>'
                f'<h3><a href="{esc(self._story_href(locale, story))}">{esc(headline(story, code, catalog))}</a></h3>'
                f'<p>{esc(truncate(dek(story, code, catalog), 190))}</p>{class_line(story, catalog, grade=False)}</article>')

    @staticmethod
    def _story_rank(story: dict) -> tuple:
        return (story.get("importance", 0), story.get("event_at", ""), story.get("id", ""))

    def _related_stories(self, story: dict, *, limit: int = 3) -> list[tuple[dict, str]]:
        """Find useful adjacent reading from shared public topics, organizations and beat."""
        topics = set(story.get("topics") or [])
        organizations = set(story.get("organizations") or [])
        candidates = []
        for candidate in self.live:
            if candidate["id"] == story["id"]:
                continue
            shared_topics = topics & set(candidate.get("topics") or [])
            shared_orgs = organizations & set(candidate.get("organizations") or [])
            same_beat = bool(story.get("beat") and story.get("beat") == candidate.get("beat"))
            score = 3 * len(shared_topics) + 2 * len(shared_orgs) + int(same_beat)
            if score:
                reason = next(iter(sorted(shared_topics)), "") or next(iter(sorted(shared_orgs)), "") or "same-beat"
                candidates.append((score, self._story_rank(candidate), candidate, reason))
        candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
        return [(candidate, reason) for _, _, candidate, reason in candidates[:limit]]

    def _correction_story_href(self, locale: dict, story: dict) -> str:
        """Where a correction's story link lands: the live story, its live survivor, else the correction notice."""
        if story.get("status") == "live":
            return self._story_href(locale, story)
        survivor = next((s for s in self.stories if s["id"] == story.get("merged_into")), None)
        if survivor and survivor.get("status") == "live":
            return self._story_href(locale, survivor)
        return self._correction_href(locale, story)

    @staticmethod
    def _related_reason(reason: str, item: dict, catalog: dict) -> str:
        """Visible reason on a related card: a catalogue topic label, an organisation name or the beat; never a raw slug."""
        beat = label(catalog, "beat", item.get("beat"))
        if reason == "same-beat":
            return beat
        if reason in (item.get("organizations") or []):
            return reason
        return label(catalog, "topic", slugify(reason), fallback="") or beat

    def _story_navigation(self, story: dict, locale: dict) -> str:
        strings = self.catalogs[locale["code"]]["strings"]
        # Newer/Older walk only the stories that share a topic with this one (an organization when it has no topic),
        # so the neighbour is always about the same subject; each direction is one story, hence the singular labels.
        # A story alone on its subject falls back to the whole live sequence, so no story page is a dead end.
        topics = set(story.get("topics") or [])
        field_name, mine = ("topics", topics) if topics else ("organizations", set(story.get("organizations") or []))
        order = lambda item: (item.get("url_date", ""), *self._story_rank(item))  # noqa: E731
        sequence = sorted((item for item in self.live if item["id"] == story["id"] or (mine and mine & set(item.get(field_name) or []))),
                          key=order, reverse=True)
        if len(sequence) < 2:
            sequence = sorted(self.live, key=order, reverse=True)
        position = next((i for i, item in enumerate(sequence) if item["id"] == story["id"]), -1)
        neighbors = []
        if position >= 0:
            if position > 0:
                neighbors.append((strings["archive"]["newer_one"], sequence[position - 1], "next"))
            if position + 1 < len(sequence):
                neighbors.append((strings["archive"]["older_one"], sequence[position + 1], "previous"))
        edition_links = "".join(
            f'<a rel="{rel}" href="{esc(self._story_href(locale, item))}"><span class="card-meta">{esc(format_date(item["event_at"], self.catalogs[locale["code"]], precision=item.get("date_precision", "day")))}</span><strong>{esc(direction)}</strong><span>{esc(headline(item, locale["code"], self.catalogs[locale["code"]]))}</span></a>'
            for direction, item, rel in neighbors
        )
        related = self._related_stories(story)
        related_cards = "".join(
            f'<article class="story-card"><span class="card-meta" translate="no">{esc(self._related_reason(reason, item, self.catalogs[locale["code"]]))}</span><h3><a href="{esc(self._story_href(locale, item))}">{esc(headline(item, locale["code"], self.catalogs[locale["code"]]))}</a></h3><p>{esc(truncate(dek(item, locale["code"], self.catalogs[locale["code"]]), 160))}</p></article>'
            for item, reason in related
        )
        parts = []
        if edition_links:
            parts.append(f'<nav class="edition-neighbors" aria-label="{esc(strings["story"]["related"])}">{edition_links}</nav>')
        if related_cards:
            parts.append(f'<section class="related-reading"><h2>{esc(strings["story"]["related"])}</h2><div class="card-row">{related_cards}</div></section>')
        return "".join(parts)

    @staticmethod
    def _plate_html(story: dict, catalog: dict, ratio: str = "16:10") -> str:
        """Procedural, text-free plate for the cover; the alt names the motif, never the content."""
        from tools.paper.plates import plate as make_plate
        pl = make_plate(story["id"], list(story.get("topics") or []), ratio)
        motif = pl.get("motif") or "neutral"
        strings = catalog["strings"]["plate"]
        motif_text = strings.get("motif_" + motif, "")
        alt = strings["alt_decorative"] if motif == "neutral" or not motif_text else strings["alt_motif"].format(motif=motif_text)
        return f'<div class="plate" data-ratio="{esc(ratio)}" role="img" aria-label="{esc(alt)}">{pl["svg"]}</div>'

    def _topic_pair(self, story: dict, locale: dict) -> str:
        counts = Counter(t for item in self.live for t in set(item.get("topics") or []))
        topic = next((t for t in story.get("topics") or [] if counts[t] >= 3), "")
        if not topic:
            return ""
        catalog = self.catalogs[locale["code"]]
        seq = sorted((i for i in self.live if topic in (i.get("topics") or [])), key=lambda i: (i.get("event_at", ""), i["id"]))
        pos = next(n for n, i in enumerate(seq) if i["id"] == story["id"])
        make = lambda i: (self._story_href(locale, i), headline(i, locale["code"], catalog))
        name = label(catalog, "topic", slugify(topic), fallback="")
        if not name:
            return ""
        return topic_pair(catalog, name, make(seq[pos - 1]) if pos > 0 else None, make(seq[pos + 1]) if pos + 1 < len(seq) else None)

    def _machine_strip(self, story: dict, locale: dict, catalog: dict) -> str:
        suffix = story_path({**locale, "path_prefix": ""}, story)
        return machine_strip(catalog, json_href=absolute(self.base_url, f"api/v1/stories/{story['id']}.json"),
                             cite_href=self._citation_permalink(story),
                             md_href=absolute(self.base_url, locale["path_prefix"] + suffix.rstrip("/") + ".md"))

    def _citation_permalink(self, story: dict) -> str:
        english = next(locale for locale in self.config["locales"] if locale["code"] == "en")
        canonical_story_url = absolute(self.base_url, english["path_prefix"] + story_path(english, story))
        sources = self._source_urls(story)
        payload = {"schema": "fcmo-versioned-citation-v1", "id": story["id"],
                   "canonical_story_url": canonical_story_url,
                   "headline": headline(story, "en", self.catalogs["en"]),
                   "summary": str(story.get("summary") or ""), "source_urls": sources}
        version = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        record = {**payload, "version": version}
        target = self.out / "data" / "citations" / story["id"] / f"{version}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return absolute(self.base_url, f"data/citations/{story['id']}/{version}.json")

    @staticmethod
    def _source_urls(story: dict) -> list[str]:
        rows = [source for source in story.get("sources") or [] if isinstance(source, dict)
                and isinstance(source.get("url"), str) and source["url"].startswith(("https://", "http://"))]
        rows.sort(key=lambda source: (not bool(source.get("primary")), str(source.get("url"))))
        return [source["url"] for source in rows]

    def _topic_links(self, locale: dict, *, exclude_topic: str = "", exclude_org: str = "", limit: int = 5) -> str:
        """Link into co-occurring topics and organizations using the live corpus."""
        if not hasattr(self, "_taxonomy_neighbors"):
            # Membership counts are per story, even if a field repeats a name.
            # Keep first encounter order for equal count/casefold sort keys.
            counts = {field: Counter(value for story in self.live for value in set(story.get(field) or []))
                      for field in ("topics", "organizations")}
            unique = {}
            for story in self.live:
                for field, route in (("topics", "topic"), ("organizations", "org")):
                    for value in story.get(field, []):
                        count = counts[field][value]
                        if field == "topics" and count < 3:
                            continue
                        unique.setdefault((value, route), (count, value, slugify(value), route))
            self._taxonomy_neighbors = sorted(unique.values(), key=lambda row: (-row[0], row[1].casefold()))
        selected = []
        for count, value, slug, route in self._taxonomy_neighbors:
            excluded = exclude_topic if route == "topic" else exclude_org
            if value == excluded or slug == excluded:
                continue
            selected.append((count, value, slug, route))
        links = "".join(f'<li><a href="{esc(href(self.base, locale["path_prefix"] + route + "/" + slug + "/"))}" translate="no">{esc(value)}</a><span>{count}</span></li>'
                        for count, value, slug, route in selected[:limit])
        return f'<nav class="taxonomy-neighbors"><h2>{esc(self.catalogs[locale["code"]]["strings"]["front"]["see_all"])}</h2><ul>{links}</ul></nav>' if links else ""

    def _edition_card(self, date: str, locale: dict) -> str:
        """One recent edition: its date, how many live stories it holds and the story that leads it."""
        catalog = self.catalogs[locale["code"]]
        stories = [story for story in self.live if story.get("url_date") == date]
        lead = front_order(stories)[0] if stories else None
        title = catalog["strings"]["archive"]["edition_title"].format(date=format_date(date + "T12:00:00Z", catalog))
        lead_copy = (f'<a href="{esc(self._story_href(locale,lead))}">{esc(headline(lead,locale["code"],catalog))}</a>'
                     if lead else esc(catalog["strings"]["archive"]["empty"]))
        return (f'<article class="story-card edition-card"><h3><a href="{esc(href(self.base,edition_path(locale,date)))}">{esc(title)}</a></h3>'
                f'<p class="edition-count">{esc(plural(catalog, "edition_story", len(stories)))}</p>'
                f'<p class="edition-lead">{lead_copy}</p></article>')

    def _front(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        order = front_order(self.live)
        stats = (len(self.live), len({topic for story in self.live for topic in story.get("topics", [])}),
                 len({org for story in self.live for org in story.get("organizations", [])}))
        if not order:
            landing = render_landing(locale=locale, home=href(self.base, locale["path_prefix"]), technical=href(self.base, locale["path_prefix"]+TECHNICAL_FRONT), about=href(self.base, locale["path_prefix"]+"about/"), subscribe=href(self.base, locale["path_prefix"]+"suscribete/"), lead="", top="", cartas=community.render_cartas(self.cartas, locale["code"]), stats=stats)
            _, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url)
            self._write_page(locale=locale, suffix="", title="FCMO AI", description="FCMO AI: evidence-first news, research and applied AI strategy.", body=landing, kind="landing", extra_head=subscribe_script, machine_alternates=[("text/plain", href(self.base, "llms.txt")), ("application/json", href(self.base, "agent.json"))])
            return
        plan = front_plan(order, BEATS)
        first = plan["lead"]
        lead_title = headline(first, locale["code"], catalog)
        lead_class = self._title_class(lead_title, locale["code"], hero=True)
        dz = strings["design"]
        lead_evidence = first.get("evidence") if isinstance(first.get("evidence"), dict) else {}
        local_evidence = self._localized_evidence(first, locale)
        feature = {
            "label": dz["lead"],
            "beat": label(catalog, "beat", first.get("beat")),
            "title": lead_title,
            "title_class": lead_class,
            "href": self._story_href(locale, first),
            "dek": truncate(dek(first, locale["code"], catalog), 170),
            "glyph": evidence_glyph(first, catalog),
            "grade": label(catalog, "evidence_class", first.get("evidence_class")),
            "confidence": label(catalog, "confidence", first.get("confidence")),
            "status": status_chip(self.status, catalog),
            "badge": automation_badge(self.status, catalog),
            "hero": data_hero(first, catalog, evidence=lead_evidence),
            "brief": brief(first, catalog, summary=field(first, locale["code"], "summary"), why=field(first, locale["code"], "why_it_matters"), evidence=local_evidence),
            "datetime": first["event_at"],
            "date": format_date(first["event_at"], catalog, precision=first.get("date_precision", "day")),
            "cta": dz["read_story"],
            "status_href": href(self.base, locale["path_prefix"] + "status/"),
            "status_label": dz["see_status"],
        }
        lead = f'''<article class="lead"><p class="story-kicker">{esc(strings["front"]["lead"])} · {esc(label(catalog,"beat",first.get("beat")))}</p><h1 class="{lead_class}"><a href="{esc(self._story_href(locale,first))}">{esc(lead_title)}</a></h1><p class="lead-dek">{esc(dek(first,locale["code"],catalog))}</p><p class="story-meta">{esc(format_date(first["event_at"],catalog,precision=first.get("date_precision","day")))}</p>{evidence_strip(first, catalog)}{feature["hero"]}</article>'''
        top = f'<h2>{esc(strings["front"]["top_stories"])}</h2>' + "".join(self._card(story, locale, 3) for story in plan["top"])
        essentials = f'<div><p class="section-kicker">FCMO AI · {esc(strings["front"]["essentials"])}</p><h2>{esc(strings["front"]["essentials"])}</h2></div><ol>' + "".join(f'<li data-story-id="{esc(s["id"])}"><a href="{esc(self._story_href(locale,s))}">{esc(headline(s,locale["code"],catalog))}</a></li>' for s in plan["essentials"]) + "</ol>"
        sections = []
        for beat, values in plan["beats"].items():
            beat_label = label(catalog, "beat", beat)
            sections.append(f'<section class="beat-section"><div class="section-head"><div><p class="section-kicker">{esc(beat_label)}</p><h2>{esc(beat_label)}</h2></div><a href="{esc(href(self.base,beat_path(locale,beat)))}">{esc(strings["front"]["see_all"])}</a></div><div class="card-row">{"".join(self._card(s,locale,3) for s in values)}</div></section>')
        developing = ""
        if plan["developing"]:
            developing = f'<section class="developing-well"><div class="section-head"><div><p class="section-kicker">FCMO AI · {esc(strings["kicker"]["signal"])}</p><h2>{esc(strings["front"]["developing"])}</h2></div></div><div class="card-row">{"".join(self._card(s,locale,3) for s in plan["developing"])}</div></section>'
        cartas = getattr(self, "_editorial_shelf", {}).get(locale["code"], community.render_cartas(self.cartas, locale["code"]))
        subscribe, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url)
        dates = self.edition_dates[:6]
        editions = f'<section class="beat-section"><div class="section-head"><h2>{esc(strings["front"]["editions"])}</h2><a href="{esc(href(self.base,locale["path_prefix"]+"archive/"))}">{esc(strings["nav"]["archive"])}</a></div><div class="card-row">' + "".join(self._edition_card(date, locale) for date in dates) + "</div></section>"
        nouns = {
            "en": ("live stories", "topics", "organizations"),
            "es-419": ("historias activas", "temas", "organizaciones"),
            "zh-Hans": ("篇在刊报道", "个主题", "家机构"),
        }[locale["code"]]
        topic_count = len({topic for item in self.live for topic in item.get("topics", [])})
        org_count = len({org for item in self.live for org in item.get("organizations", [])})
        signal = (f'<section class="front-ledger" aria-label="{esc(strings["site"]["name"])}">'
                  f'<p class="section-kicker">{esc(strings["site"]["tagline"])}</p>'
                  f'<ul><li><strong>{len(self.live)}</strong> {esc(nouns[0])}</li>'
                  f'<li><strong>{topic_count}</strong> {esc(nouns[1])}</li>'
                  f'<li><strong>{org_count}</strong> {esc(nouns[2])}</li></ul></section>')
        board = evidence_board(self.live, catalog, method_href=href(self.base, locale["path_prefix"] + "method/"))
        body = front_page(lead=lead, top=top, essentials=essentials, beats="".join(sections), developing=developing, subscribe=subscribe, cartas=cartas, editions=editions, signal=signal, board=board)
        body = community.without_empty_cartas_slot(body, cartas)
        landing = render_landing(locale=locale, home=href(self.base, locale["path_prefix"]), technical=href(self.base, locale["path_prefix"]+TECHNICAL_FRONT), about=href(self.base, locale["path_prefix"]+"about/"), subscribe=href(self.base, locale["path_prefix"]+"suscribete/"), lead=lead, top=top, cartas=cartas, stats=stats, feature=feature, front=front_context(order=order, base=self.base))
        self._write_page(locale=locale, suffix="", title="FCMO AI", description="FCMO AI: evidence-first news, research and applied AI strategy.", body=landing, kind="landing", og_image=self._media_url(first, locale), extra_head=subscribe_script, machine_alternates=[("text/plain", href(self.base, "llms.txt")), ("application/json", href(self.base, "agent.json"))])

    def _newsletter_pages(self, locale: dict) -> None:
        # One publication (DIRECCION section 4): comunidad/ had no live content, so like cartas/ it forwards to the
        # front page. It is written as a stub, never as a route, so it stays out of the sitemap and the route index.
        target = href(self.base, locale["path_prefix"])
        path = self.out / locale["path_prefix"] / "comunidad" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(redirects.stub(target, self.base), encoding="utf-8")

    def _localized_evidence(self, story: dict, locale: dict) -> dict:
        if locale["code"] == "en":
            return story.get("evidence") or {}
        value = field(story, locale["code"], "evidence", {})
        if not isinstance(value, dict):
            return {}
        # Locale packs carry prose; evidence codes remain canonical and are
        # displayed only through this edition's catalog.
        canonical = (story.get("evidence") or {}).get("claims") or []
        claims = []
        for index, claim in enumerate(value.get("claims") or []):
            codes = {key: canonical[index][key] for key in ("label", "qualifier")
                     if index < len(canonical) and key in canonical[index]}
            claims.append({**claim, **codes})
        return {**value, "claims": claims}

    def _story(self, story: dict, locale: dict) -> None:
        code = locale["code"]
        catalog = self.catalogs[code]
        strings = catalog["strings"]
        if story.get("status") in {"withdrawn", "merged"} and story.get("corrections"):
            self._correction_notice(story, locale)
            return
        complete = is_complete(story, code, catalog=catalog)
        title = headline(story, code, catalog) if complete else strings["l10n"]["pending_title"]
        description = truncate(dek(story, code, catalog))
        suffix = story_path({**locale, "path_prefix": ""}, story)
        event = format_date(story["event_at"], catalog, precision=story.get("date_precision", "day"))
        published = format_date(story["first_published_at"], catalog, precision="minute")
        title_class = self._title_class(title, code)
        note = ""
        if code != "en" and story_locale(story, code).get("state") == "MACHINE_REVIEWED":
            english = self._story_href(self.config["locales"][0], story)
            note = (f'<p class="translation-note" role="note">{esc(strings["l10n"]["desk_note"])} '
                    f'<a href="{esc(english)}" lang="{esc(code)}" hreflang="en">{esc(strings["l10n"]["read_original"])}</a></p>')
        dz = strings["design"]
        grade_text = label(catalog, "evidence_class", story.get("evidence_class"))
        conf_text = label(catalog, "confidence", story.get("confidence"))
        signals = (f'<div class="story-signals">{evidence_glyph(story, catalog)}<span class="sig-text"><b>{esc(grade_text)}</b>'
                   f'{" · " + esc(conf_text) if conf_text else ""}</span>{status_chip(self.status, catalog)}</div>')
        original = primary_source(story)
        provenance = provenance_line(original, catalog) if original else ""
        header = (f'<header class="story-header"><div class="sh-main"><p class="story-kicker">{esc(label(catalog,"beat",story.get("beat")))}</p><h1>{esc(title)}</h1>'
                  f'<p class="story-dek">{esc(description)}</p>{signals}'
                  f'<p class="story-meta">{esc(strings["story"]["byline"])} · {esc(strings["story"]["event_date"].format(date=event))} · {esc(strings["story"]["published"].format(date=published))}</p>'
                  f'<p class="story-disclosure">{automation_badge(self.status, catalog)}</p>{provenance}{note}</div></header>')
        hero_figure = data_hero(story, catalog, evidence=story.get("evidence") if isinstance(story.get("evidence"), dict) else {})
        if not complete:
            notice = strings["l10n"]["pending_partial"] if (field(story, code, "headline") or field(story, code, "title")) else strings["l10n"]["pending_notice"]
            english = self._story_href(self.config["locales"][0], story)
            partial = self._pending_fields(story, locale)
            body = f'<section class="pending-panel"><p class="section-kicker">{esc(strings["l10n"]["pending_title"])}</p><p>{esc(notice)}</p><a class="button" href="{esc(english)}" hreflang="en" lang="en">{esc(strings["l10n"]["read_original"])}</a></section>{partial}'
            aside = self._facts(story, locale)
        else:
            evidence = self._localized_evidence(story, locale)
            argument, dossier, technical_layer = [], [], []
            for heading_key, value in (("what_changed", field(story, code, "summary")), ("why_it_matters", field(story, code, "why_it_matters"))):
                if value:
                    argument.append(f'<section><h2>{esc(strings["story"][heading_key])}</h2><p>{esc(value)}</p></section>')
            claims = evidence.get("claims") or []
            if claims:
                items = []
                for claim in claims:
                    claim_label = label(catalog, "claim_label", claim.get("label"), fallback=label(catalog, "claim_label", f'{claim.get("label","")}_{claim.get("qualifier","")}', fallback=""))
                    items.append(f'<li data-kind="{esc(claim_kind(claim.get("label")))}"><span class="evidence-label">{esc(claim_label)}</span>{esc(claim.get("text",""))}</li>')
                dossier.append(f'<section><h2>{esc(strings["story"]["evidence"])}</h2><ol class="evidence-list">{"".join(items)}</ol></section>')
            for heading_key, evidence_key in (("limitations", "limitations"), ("unknowns", "gaps"), ("contradictory", "contradictory")):
                values = evidence.get(evidence_key) or []
                if values:
                    lis = "".join(f'<li>{esc(v.get("description","") if isinstance(v,dict) else v)}</li>' for v in values)
                    dossier.append(f'<section><h2>{esc(strings["story"][heading_key])}</h2><ul>{lis}</ul></section>')
            technical = field(story, code, "technical", {})
            if isinstance(technical, dict) and technical:
                details = "".join(f'<section><h3>{esc(strings["technical_field"].get(key,key))}</h3><p>{esc(value)}</p></section>' for key, value in technical.items() if value)
                technical_layer.append(f'<section class="developing-well"><h2>{esc(strings["story"]["technical"])}</h2>{details}</section>')
            sources = story.get("sources") or []
            if sources:
                links = "".join(f'<li>{provenance_line(src, catalog)}{"<span class=\"prov-primary\">" + esc(strings["story"]["primary_source"]) + "</span>" if src.get("primary") else ""}</li>' for src in sources)
                dossier.append(f'<section><h2>{esc(strings["story"]["sources"])}</h2><ol class="source-list">{links}</ol></section>')
            body = ""
            aside = ""
            technical_fields = field(story, code, "technical", {})
            technical_fields = technical_fields if isinstance(technical_fields, dict) else {}
            topic_nav = self._topic_pair(story, locale)
            c6_page = story_view(
                story=story, catalog=catalog, code=code, title=title, dek_text=description,
                beat_label=label(catalog, "beat", story.get("beat")), home_href=href(self.base, locale["path_prefix"]),
                evidence=evidence, summary=field(story, code, "summary"), why=field(story, code, "why_it_matters"),
                technical=technical_fields, status_html=status_chip(self.status, catalog),
                automation_html=automation_badge(self.status, catalog), byline=strings["story"]["byline"],
                dates_line=f'{strings["story"]["event_date"].format(date=event)} · {strings["story"]["published"].format(date=published)}',
                plate_html=self._plate_html(story, catalog), note_html=note, taxonomy_html=self._facts(story, locale),
                navigation_html=self._story_navigation(story, locale), topic_nav_html=topic_nav,
                machine_html=self._machine_strip(story, locale, catalog))
        hero = ""
        if complete:
            page = f'<article class="story-layout">{c6_page}</article>' + JUMP_OPEN_SCRIPT
        else:
            page = story_page(header=header, body=body, aside=hero_figure + aside, hero=hero, navigation=self._story_navigation(story, locale))
        page = page.replace('<article class="story-layout">', f'<article class="story-layout {title_class}">', 1)
        story_url = absolute(self.base_url, locale["path_prefix"] + suffix)
        image = self._media_url(story, locale)
        sources = self._source_urls(story)
        structured = {"@context": "https://schema.org", "@type": "NewsArticle", "identifier": story["id"], "headline": title, "description": description, "datePublished": story["first_published_at"], "dateModified": story["updated_at"], "inLanguage": locale["code"], "mainEntityOfPage": story_url, "citation": self._citation_permalink(story), "isBasedOn": sources, "image": [image], "author": {"@type": "Organization", "name": "FCMO AI Research Desk"}, "publisher": {"@type": "Organization", "name": "FCMO AI"}}
        if story.get("corrections"):
            structured["correction"] = [c.get("note") or c.get("reason") or c.get("kind", "Correction") for c in story["corrections"]]
        story_api = absolute(self.base_url, f"api/v1/stories/{story['id']}.json")
        story_md = absolute(self.base_url, locale["path_prefix"] + suffix.rstrip("/") + ".md")
        self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=description, body=page, kind="story", story=story, og_image=image, json_ld=structured,
                         machine_alternates=[("text/markdown", story_md), ("application/json", story_api)])

    def _correction_title(self, story: dict, locale: dict) -> tuple[str, str]:
        """(title, lead-in) for a correction in this locale, never English and never a translation placeholder.

        Order: the story's own localized title; for a merge, the localized title of the story it was merged into
        (the lead-in says so); otherwise a plain description of what it was (kind and publication date)."""
        code = locale["code"]
        catalog = self.catalogs[code]
        ui = catalog["strings"]["corrections_ui"]
        own = field(story, code, "headline") or field(story, code, "title")
        if own:
            return str(own), ""
        survivor = next((item for item in self.stories if item["id"] == story.get("merged_into")), None)
        if survivor is None:
            survivor = next((item for item in self.stories if any(r.get("id") == item["id"] and r.get("type") == "duplicate_of"
                                                                   for r in story.get("related") or [] if isinstance(r, dict))), None)
        if survivor is not None:
            name = field(survivor, code, "headline") or field(survivor, code, "title")
            if name:
                return str(name), ui["merged_into"]
        kind = (story.get("corrections") or [{}])[-1].get("kind")
        base = ui.get("untitled_" + str(kind)) or ui["untitled_default"]
        published = story.get("first_published_at") or story.get("event_at")
        return (f'{base} · {ui["published_on"].format(date=format_date(published, catalog))}' if published else base), ""

    def _correction_notice(self, story: dict, locale: dict) -> None:
        code = locale["code"]
        catalog = self.catalogs[code]
        strings = catalog["strings"]
        fix = story["corrections"][-1]
        text = fix.get("text") or {}
        notice = text.get(code) or strings["l10n"]["pending_notice"]
        kind = label(catalog, "correction_kind", fix.get("kind"), fallback=strings["story"]["corrections"])
        title, lead_in = self._correction_title(story, locale)
        body = (f'<p class="story-kicker">{esc(kind)} · '
                f'<time datetime="{esc(fix.get("at", ""))}">{esc(format_date(fix["at"], catalog))}</time></p>'
                f'<p class="story-dek">{esc(notice)}</p>')
        if story.get("merged_into"):
            survivor = next((item for item in self.stories if item["id"] == story["merged_into"]), None)
            if survivor is not None and survivor.get("status") == "live":
                body += (f'<p class="correction-current"><a href="{esc(self._story_href(locale, survivor))}">'
                         f'{esc(strings["story"]["read_merged"])}: '
                         f'{esc(headline(survivor, code, catalog))}</a></p>')
        suffix = "corrections/story/" + story["slug"] + "/"
        self._write_page(locale=locale, suffix=suffix, title=f"{title} — {kind}", description=notice,
                         body=simple_page(title, body), kind="correction", index=False)

    def _pending_fields(self, story: dict, locale: dict) -> str:
        """Render only prose already present in an incomplete native edition."""
        code = locale["code"]
        fields = story_locale(story, code).get("fields") or {}
        if not isinstance(fields, dict):
            return ""
        strings = self.catalogs[code]["strings"]
        sections: list[str] = []
        native_title = fields.get("headline") or fields.get("title")
        if native_title:
            sections.append(f'<section data-field="title"><h2>{esc(native_title)}</h2></section>')
        if fields.get("dek"):
            sections.append(f'<section data-field="dek"><p class="story-dek">{esc(fields["dek"])}</p></section>')
        for key, heading in (("summary", "what_changed"), ("why_it_matters", "why_it_matters"),
                             ("importance_rationale", "importance_rationale")):
            if fields.get(key):
                sections.append(f'<section data-field="{key}"><h2>{esc(strings["story"][heading])}</h2><p>{esc(fields[key])}</p></section>')
        technical = fields.get("technical")
        if isinstance(technical, dict) and technical:
            details = "".join(
                f'<section><h3>{esc(strings["technical_field"].get(key, key))}</h3><p>{esc(value)}</p></section>'
                for key, value in technical.items() if value
            )
            sections.append(f'<section class="developing-well" data-field="technical"><h2>{esc(strings["story"]["technical"])}</h2>{details}</section>')
        evidence = fields.get("evidence")
        if isinstance(evidence, dict) and evidence:
            parts: list[str] = []
            claims = evidence.get("claims") or []
            if claims:
                parts.append("<ol class=\"evidence-list\">" + "".join(
                    f'<li>{esc(item.get("text", "") if isinstance(item, dict) else item)}</li>' for item in claims
                ) + "</ol>")
            for key, heading in (("limitations", "limitations"), ("gaps", "unknowns"), ("contradictory", "contradictory")):
                values = evidence.get(key) or []
                if values:
                    parts.append(f'<h3>{esc(strings["story"][heading])}</h3><ul>' + "".join(
                        f'<li>{esc(item.get("description", "") if isinstance(item, dict) else item)}</li>' for item in values
                    ) + "</ul>")
            if parts:
                sections.append(f'<section data-field="evidence"><h2>{esc(strings["story"]["evidence"])}</h2>{"".join(parts)}</section>')
        return "".join(sections)

    def _facts(self, story: dict, locale: dict) -> str:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]["story"]
        confidence_heading = strings["confidence"].split("{level}", 1)[0].rstrip(" :：")
        values = [
            (strings["development_type"], label(catalog, "development_type", story.get("development_type"))),
            (strings["evidence"], label(catalog, "evidence_class", story.get("evidence_class"))),
            (confidence_heading, label(catalog, "confidence", story.get("confidence"))),
        ]
        facts = "".join(f'<div class="fact"><dt>{esc(key)}</dt><dd>{esc(value)}</dd></div>' for key, value in values if value)
        topic_items = []
        for topic in story.get("topics") or []:
            name = label(catalog, "topic", slugify(topic), fallback="")
            if not name:
                continue  # never print a raw slug: no catalogue label, no chip
            label_html = f'<span data-field="topics">{esc(name)}</span>'
            if sum(topic in (item.get("topics") or []) for item in self.live) >= 3:
                label_html = f'<a href="{esc(href(self.base, locale["path_prefix"] + "topic/" + slugify(topic) + "/"))}">{label_html}</a>'
            topic_items.append(f'<li>{label_html}</li>')
        topics = "".join(topic_items)
        return (f'<dl>{facts}</dl>'
                + (f'<section class="story-taxonomy"><h2>{esc(strings["topics"])}</h2><ul>{topics}</ul></section>' if topics else ""))

    def _listing(self, *, locale: dict, suffix: str, title: str, stories: list[dict], kind: str,
                 title_html: str | None = None) -> None:
        catalog = self.catalogs[locale["code"]]
        topics = {value for item in stories for value in item.get("topics", [])}
        orgs = {value for item in stories for value in item.get("organizations", [])}
        labels = {"en": ("stories", "topics", "organizations"), "es-419": ("historias", "temas", "organizaciones"), "zh-Hans": ("篇报道", "个主题", "家机构")}[locale["code"]]
        context = (f'<ul class="archive-totals"><li><strong>{len(stories)}</strong> {labels[0]}</li>'
                   f'<li><strong>{len(topics)}</strong> {labels[1]}</li><li><strong>{len(orgs)}</strong> {labels[2]}</li></ul>')
        navigation = ""
        if kind == "edition":
            dates = self.edition_dates
            date = suffix.strip("/").split("/")[-1]
            index = dates.index(date) if date in dates else -1
            links = []
            if index >= 0 and index + 1 < len(dates):
                older = dates[index + 1] if index + 1 < len(dates) else None
                if older:
                    links.append(f'<a rel="next" href="{esc(href(self.base, locale["path_prefix"] + "edition/" + older + "/"))}">{esc(catalog["strings"]["archive"]["older"])} · {esc(older)}</a>')
            if index > 0:
                newer = dates[index - 1]
                links.append(f'<a rel="prev" href="{esc(href(self.base, locale["path_prefix"] + "edition/" + newer + "/"))}">{esc(catalog["strings"]["archive"]["newer"])} · {esc(newer)}</a>')
            navigation = f'<nav class="edition-neighbors" aria-label="{esc(catalog["strings"]["front"]["editions"])}">{"".join(links)}</nav>' if links else ""
        elif kind == "topic":
            navigation = self._topic_links(locale, exclude_topic=suffix.strip("/").split("/")[-1])
        elif kind == "org":
            navigation = self._topic_links(locale, exclude_org=suffix.strip("/").split("/")[-1])
        resources = None
        if kind == "edition":
            date = suffix.strip("/").split("/")[-1]
            resources = [("text/markdown", absolute(self.base_url, locale["path_prefix"] + f"edition/{date}.md")),
                         ("application/json", absolute(self.base_url, f"api/v1/editions/{date}.json"))]
        pages = max(1, (len(stories) + LISTING_PAGE_SIZE - 1) // LISTING_PAGE_SIZE)
        def page_path(number):
            return suffix if number == 1 else suffix + f"page/{number}/"
        strings = catalog["strings"]
        for number in range(1, pages + 1):
            start = (number - 1) * LISTING_PAGE_SIZE
            chunk = stories[start:start + LISTING_PAGE_SIZE]
            # The grade is only worth a word per row when the page mixes grades; otherwise the class carries the row.
            grades = Counter(item.get("evidence_class") for item in chunk if item.get("evidence_class"))
            usual = grades.most_common(1)[0][0] if grades else None
            usual_note = (f'<p class="archive-grade-note">{esc(strings["archive"]["grade_default"].format(grade=label(catalog, "evidence_class", usual)))}</p>'
                          if usual else "")
            groups: list[tuple[str, str, list[str]]] = []
            for story in chunk:
                when = format_date(story["event_at"], catalog, precision=story.get("date_precision", "day"))
                if not groups or groups[-1][1] != when:
                    groups.append((f"d-{story['event_at'][:10]}", when, []))
                story_url = esc(self._story_href(locale, story))
                groups[-1][2].append(
                    f'<article class="archive-item" data-story-id="{esc(story["id"])}"><time class="visually-hidden" datetime="{esc(story["event_at"])}">{esc(when)}</time>'
                    f'<a class="archive-art" href="{story_url}" aria-hidden="true" tabindex="-1"><img src="{esc(self._story_media_url(story, locale))}" alt="" width="320" height="180" loading="lazy"></a>'
                    f'<div class="archive-copy"><p class="archive-meta">{esc(label(catalog, "beat", story.get("beat")))} · {esc(label(catalog, "format", plan_mod.story_format(story)))}</p>'
                    f'<h3><a href="{story_url}">{esc(headline(story, locale["code"], catalog))}</a></h3>'
                    f'<p>{esc(truncate(dek(story, locale["code"], catalog), 220))}</p>{class_line(story, catalog, grade=bool(story.get("evidence_class")) and story.get("evidence_class") != usual)}</div></article>')
            seen_ids: set[str] = set()
            day_html = []
            for day_id, when, rows in groups:
                while day_id in seen_ids:
                    day_id += "x"
                seen_ids.add(day_id)
                day_html.append((day_id, when, archive_day(day_id, when, "".join(rows))))
            items = "".join(html for _, _, html in day_html)
            jump = archive_jump(catalog, [(day_id, when) for day_id, when, _ in day_html])
            newer = older = ""
            if number > 1:
                newer = f'<a rel="prev" href="{esc(href(self.base, locale["path_prefix"] + page_path(number - 1)))}">← {esc(strings["archive"]["newer"])}</a>'
            if number < pages:
                older = f'<a rel="next" href="{esc(href(self.base, locale["path_prefix"] + page_path(number + 1)))}">{esc(strings["archive"]["older"])} →</a>'
            paging = archive_pager(catalog, number=number, pages=pages, newer=newer, older=older)
            body = archive_page(title, strings["site"]["description"], items or f'<p>{esc(strings["archive"]["empty"])}</p>', kicker=strings["kicker"]["archive"], title_html=title_html, context=context + usual_note, navigation=navigation + jump) + paging
            page_title = title if number == 1 else f"{title} · {number}/{pages}"
            self._write_page(locale=locale, suffix=page_path(number), title=f"{page_title} — FCMO AI", description=title, body=body, kind=kind, machine_alternates=resources)

    def _status(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        visible_status = reader_status(self.status)
        state = label(catalog, "edition_state", visible_status["edition_state"])
        last = format_date(visible_status["last_edition_at"], catalog, precision="minute")
        checked = format_date(self.status["status_updated_at"], catalog, precision="minute")
        cards = f'<article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["edition"])}</span><strong>{esc(state)}</strong><p>{esc(strings["status_page"]["last_edition"].format(date=last))}</p></article>'
        fresh = self.freshness
        fresh_label = label(catalog, "freshness_state", fresh["state"])
        fresh_sentence = freshness_sentence(fresh, catalog)
        lead_attributes = "".join(f' {name}="{esc(fresh[key])}"' for name, key in (("data-lead-id", "lead_id"), ("data-lead-at", "lead_at")) if fresh[key] is not None)
        cards += (f'<article class="status-card status-freshness"{freshness_attributes(fresh)}{lead_attributes}><span class="eyebrow">{esc(strings["status_page"]["freshness"])}</span>'
                  f'<strong>{esc(fresh_label)}</strong><p>{esc(fresh_sentence)}</p>{self._freshness_lead(locale)}</article>')
        cards += f'<article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["translation"])}</span>'
        for code, counts in self.status.get("translation", {}).items():
            cards += f'<strong>{esc(catalog["strings"]["lang"].get(code,code))}</strong><p>{esc(strings["status_page"]["translation_counts"].format(**counts))}</p>'
        reason = label(catalog, "edition_reason", visible_status.get("edition_reason"), fallback=state)
        cards += f'</article><article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["checked"].format(date=checked))}</span><strong>{esc(label(catalog,"source_mode","MAIN",fallback="FCMO AI"))}</strong><p>{esc(reason)}</p></article>'
        counts = {
            "en": ("Stories in this edition", "editions", "topics", "organizations"),
            "es-419": ("Historias en esta edición", "ediciones", "temas", "organizaciones"),
            "zh-Hans": ("本期报道", "期", "个主题", "家机构"),
        }[locale["code"]]
        live_count = int(self.status.get("live_story_count", len(self.live)))
        topic_count = len({topic for item in self.live for topic in item.get("topics", [])})
        org_count = len({org for item in self.live for org in item.get("organizations", [])})
        cards += (f'<article class="status-card"><span class="eyebrow">{esc(counts[0])}</span><strong>{live_count}</strong>'
                  f'<p>{len({item.get("url_date") for item in self.live})} {counts[1]} · {topic_count} {counts[2]} · {org_count} {counts[3]}</p></article>')
        body = status_page(strings["status_page"]["title"], cards, "", kicker=strings["kicker"]["operations"])
        self._write_page(locale=locale, suffix="status/", title=f'{strings["status_page"]["title"]} — FCMO AI', description=f"{fresh_label} · {fresh_sentence}", body=body, kind="status",
                         machine_alternates=[("application/json", absolute(self.base_url, "status.json"))])

    def _freshness_lead(self, locale: dict) -> str:
        """The front-page lead's age against the newest story, linked to the lead."""
        fresh, catalog = self.freshness, self.catalogs[locale["code"]]
        lead = front_order(self.live)[0] if self.live else None
        if lead is None or fresh["lead_at"] is None or fresh["lead_gap_days"] is None:
            return ""
        strings = catalog["strings"]["freshness"]
        template = strings["lead"] if fresh["lead_gap_days"] >= 1 else strings["lead_same_day"]
        values = {"date": format_date(fresh["lead_at"], catalog, precision="day"),
                  "gap": plural(catalog, "freshness_day", fresh["lead_gap_days"])}
        link = f'<a href="{esc(self._story_href(locale, lead))}">{esc(headline(lead, locale["code"], catalog))}</a>'
        return '<p class="freshness-lead">' + link.join(esc(part.format(**values)) for part in template.split("{headline}")) + "</p>"

    def _search(self, locale: dict, shards: list[Path]) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        index_url = href(self.base, locale["path_prefix"] + "data/search.json")
        shard_urls = [href(self.base, path.relative_to(self.out).as_posix()) for path in shards]
        ranked = sorted(self.live, key=lambda story: (story.get("event_at", ""), story["id"]), reverse=True)
        topic_counts = Counter(value for story in self.live for value in set(story.get("topics") or []))
        topic_items = []
        for value, count in sorted(topic_counts.items(), key=lambda row: (-row[1], row[0].casefold())):
            name = label(catalog, "topic", slugify(value), fallback="")
            if count < 3 or not name:
                continue
            topic_items.append(f'<li><a href="{esc(href(self.base, locale["path_prefix"] + "topic/" + slugify(value) + "/"))}">{esc(name)}</a><span>{count}</span></li>')
        recent = "".join(f'<li><a href="{esc(self._story_href(locale, story))}">{esc(headline(story, locale["code"], catalog))}</a>'
                         f'<span>{esc(format_date(story["event_at"], catalog, precision=story.get("date_precision", "day")))}</span></li>' for story in ranked[:5])
        suggest = (f'<div class="search-suggest" data-search-suggest><p class="search-hint">{esc(strings["search"]["hint"])}</p>'
                   + (f'<section><h2>{esc(strings["search"]["suggest_topics"])}</h2><ul class="search-topics">{"".join(topic_items[:12])}</ul></section>' if topic_items else "")
                   + (f'<section><h2>{esc(strings["search"]["suggest_recent"])}</h2><ul class="search-recent">{recent}</ul></section>' if recent else "")
                   + '</div>')
        body = simple_page(strings["search"]["title"], f'<form class="search-box" role="search" data-search-form data-index="{esc(index_url)}" data-shards="{esc(json.dumps(shard_urls))}"><label class="visually-hidden" for="q">{esc(strings["a11y"]["search_label"])}</label><input id="q" type="search" name="q" autocomplete="off" data-search-input placeholder="{esc(strings["search"]["placeholder"])}"><button class="button" type="submit">{esc(strings["nav"]["search"])}</button></form><div class="search-results" data-search-results data-loading="{esc(strings["search"]["loading"])}" data-error="{esc(strings["search"]["error"])}" data-empty="{esc(strings["search"]["no_results"])}" data-results-for="{esc(strings["search"]["results_for"])}" data-results-one="{esc(strings["search"]["results_for_one"])}" data-results-more="{esc(strings["search"]["results_for_more"])}" aria-live="polite"></div>{suggest}<noscript><p>{esc(strings["search"]["needs_js"])}</p></noscript>')
        # Tab link search/?focus=1 puts the caret in the field; ?q= runs the query on arrival.
        script = (f'<script defer src="{esc(href(self.base,"assets/js/search.js"))}"></script>'
                  "<script>addEventListener('DOMContentLoaded',()=>{if(/[?&]focus=1(&|$)/.test(location.search)){document.querySelector('[data-search-input]')?.focus()}})</script>")
        self._write_page(locale=locale, suffix="search/", title=f'{strings["search"]["title"]} — FCMO AI', description=strings["search"]["placeholder"], body=body, kind="search", extra_head=script)

    def _simple_pages(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        s = catalog["strings"]
        feed_links = "".join(f'<li><a href="{esc(href(self.base,locale["path_prefix"]+"feed."+ext))}">{esc(name)}</a></li>' for ext, name in (("xml",s["feeds"]["rss"]),("atom",s["feeds"]["atom"]),("json",s["feeds"]["json"])))
        live_count = len(self.live)
        topic_count = len({value for item in self.live for value in item.get("topics", [])})
        org_count = len({value for item in self.live for value in item.get("organizations", [])})
        localized_method = {
            "en": {
                "intro": "The daily paper turns public research and reporting into a traceable account of what changed, what the evidence supports, and what remains unresolved.",
                "steps": ("Select public developments", "Separate claims from demonstrated results", "Keep limitations and unknowns visible", "Publish only complete native editions after deterministic checks"),
                "scope": "Coverage follows the evidence in each source. A paper announcement is not an independent replication, and a claimed result is labelled as a claim.",
                "story_count": "published stories",
            },
            "es-419": {
                "intro": "El diario convierte investigación y cobertura pública en un registro trazable de qué cambió, qué respalda la evidencia y qué sigue sin resolverse.",
                "steps": ("Seleccionar desarrollos públicos", "Separar afirmaciones de resultados demostrados", "Mantener visibles las limitaciones y preguntas abiertas", "Publicar ediciones nativas completas tras verificaciones deterministas"),
                "scope": "La cobertura sigue la evidencia de cada fuente. El anuncio de un artículo no equivale a una replicación independiente y los resultados declarados se identifican como afirmaciones.",
                "story_count": "historias publicadas",
            },
            "zh-Hans": {
                "intro": "每日简报将公开研究与报道整理为可追溯记录，说明发生了什么变化、证据支持什么，以及哪些问题仍未解决。",
                "steps": ("筛选公开进展", "区分主张与已展示结果", "明确保留局限和未知问题", "通过确定性检查后发布完整的原生语言版本"),
                "scope": "报道范围依据各来源中的证据。论文发布公告不等于独立复现，声称的结果会明确标注为主张。",
                "story_count": "篇已发布报道",
            },
        }[locale["code"]]
        ranked = sorted(self.live, key=self._story_rank, reverse=True)
        sample = ranked[0] if ranked else None
        method_intro = (method_order_section(catalog)
                        + f'<p class="method-intro">{esc(localized_method["intro"])}</p>'
                        f'<ul class="archive-totals"><li><strong>{live_count}</strong> {esc(localized_method["story_count"])}</li>'
                        f'<li><strong>{topic_count}</strong> {esc(s["story"]["topics"])}</li><li><strong>{org_count}</strong> {esc(s["story"]["organizations"])}</li></ul>'
                        f'<section class="method-steps"><h2>{esc(s["story"]["evidence"])}</h2><ol>'
                        + "".join(f'<li>{esc(step)}</li>' for step in localized_method["steps"])
                        + f'</ol><p>{esc(localized_method["scope"])}</p></section>')
        if sample:
            method_intro += (f'<section class="method-example"><p class="section-kicker">{esc(label(catalog, "beat", sample.get("beat")))}</p>'
                             f'<h2><a href="{esc(self._story_href(locale, sample))}">{esc(headline(sample, locale["code"], catalog))}</a></h2>'
                             f'<p>{esc(truncate(dek(sample, locale["code"], catalog), 220))}</p>'
                             f'<p>{esc(s["story"]["evidence"])} · {esc(label(catalog, "evidence_class", sample.get("evidence_class")))} · '
                             f'{esc(s["story"]["confidence"].format(level=label(catalog, "confidence", sample.get("confidence"))))}</p></section>')
        pages = [
            ("about/", s["nav"]["about"], f'<p>{esc(s["site"]["description"])}</p><p>{esc(s["footer"]["automated_notice"])}</p>', "about"),
            ("method/", s["nav"]["method"], method_intro, "method"),
            ("feeds/", s["feeds"]["title"], f'<p>{esc(s["feeds"]["intro"])}</p><ul>{feed_links}</ul>', "feeds"),
            ("agenda/", s["nav"]["agenda"], f'<p>{esc(s["archive"]["empty"])}</p><p><a href="{esc(href(self.base,locale["path_prefix"]+"agenda.ics"))}">iCalendar</a></p>', "agenda"),
            ("autores/mesa-fcmo-ai/", s["story"]["byline"].split("·")[0].strip(), f'<p>{esc(s["story"]["byline"])}</p><p>{esc(s["footer"]["automated_notice"])}</p>', "author"),
        ]
        corrections = sorted(
            ((story, correction) for story in self.stories for correction in story.get("corrections", [])),
            key=lambda item: item[1].get("at", ""), reverse=True)
        correction_rows = []
        for story, correction in corrections:
            text = correction.get("text") or {}
            note = text.get(locale["code"]) or s["l10n"]["pending_notice"]
            title, lead_in = self._correction_title(story, locale)
            date = correction.get("at") or story.get("updated_at")
            correction_rows.append(correction_row(
                catalog=catalog, title=title, title_lang="", note=note, date_iso=date, date_text=format_date(date, catalog),
                story_href=self._correction_story_href(locale, story), correction_href=self._correction_href(locale, story),
                class_before=correction.get("class_before"), class_after=correction.get("class_after"),
                reason=(correction.get("reason") or "") if isinstance(correction.get("reason"), str) else "",
                kind_text=label(catalog, "correction_kind", correction.get("kind"), fallback=s["story"]["corrections"]), lead_in=lead_in))
        corr_body = corrections_intro(catalog, method_href=href(self.base, locale["path_prefix"] + "method/")) + (
            "".join(correction_rows) if correction_rows else f'<p>{esc(s["corrections_page"]["none"])}</p>')
        pages.append(("corrections/", s["corrections_page"]["title"], corr_body, "corrections"))
        pending = {"en": "This document awaits the approved legal copy. Subscription remains inactive.", "es-419": "Este documento espera el texto legal aprobado. La suscripción permanece inactiva.", "zh-Hans": "本文件仍待核准的法律文本。订阅功能尚未启用。"}[locale["code"]]
        for suffix, title in (("privacy/",s["footer"]["privacy"]),("license/",s["footer"]["license"]),("disclaimer/",s["footer"]["disclaimer"])):
            if suffix == 'privacy/':
                from tools.email_providers import privacy_notice_file
                notice_file = privacy_notice_file(os.environ)
                notice = json.loads((ROOT/'legal'/notice_file).read_text(encoding='utf-8'))[locale['code']]
                content = ''.join('<p>'+esc(part)+'</p>' for part in notice)
                from tools.email_providers import signup_form
                form = None
                if os.environ.get('FCMO_EMAIL_ENABLED') != 'false':
                    try:
                        form = signup_form(os.environ,locale['code'])
                    except ValueError:
                        pass
                if form:
                    privacy_label = {'en':'Complete email privacy notice','es-419':'Aviso integral del correo','zh-Hans':'完整邮件隐私声明'}[locale['code']]
                    content += f'<p><a href="{esc(form.privacy_url)}">{privacy_label}</a></p>'
                else:
                    content += '<p>'+esc({'en':'Email signup is currently inactive.','es-419':'La suscripción por correo está inactiva.','zh-Hans':'邮件订阅当前尚未启用。'}[locale['code']])+'</p>'
            else:
                content = f'<p>{esc(pending)}</p>'
            pages.append((suffix, title, content, "legal"))
        for suffix, title, content, kind in pages:
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=truncate(content.replace("<p>", " ").replace("</p>", " ")), body=simple_page(title, content), kind=kind)
        subscribe, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url, page=True)
        recent = sorted(self.live, key=lambda story: (story.get("event_at", ""), story["id"]), reverse=True)[:3]
        cards = "".join(self._record_card(story, locale) for story in recent)
        tail = subscription_tail(locale=locale["code"], root=href(self.base, locale["path_prefix"]),
                                 technical=href(self.base, locale["path_prefix"]), cards=cards)
        # Kit redirect surfaces are deterministic templates, never subscriber receipts.
        from tools.paper.templates.subscription_states import COPY, state_page
        copy = COPY[locale['code']]
        self._write_page(locale=locale, suffix='subscribe/', title=copy['title'], description=copy['lede'],
                         body=f'<article class="story-body">{subscribe}</article>{tail}', kind='subscribe', extra_head=subscribe_script)
        for suffix, state, title_key in (('subscribe/check-inbox/', 'pending', 'pending'), ('subscribed/', 'confirmed', 'done'), ('unsubscribed/', 'unsubscribed', 'unsub')):
            body = state_page(locale['code'], state, self.base)
            self._write_page(locale=locale, suffix=suffix, title=copy[title_key], description=copy[title_key], body=body,
                             kind='subscribe', index=False, extra_head='<meta name="robots" content="noindex">' + subscribe_script)

    def _404(self) -> None:
        """One 404 page for every locale, rendered through the shared document chrome."""
        en = self.config["locales"][0]
        blocks = []
        for locale in self.config["locales"]:
            strings = self.catalogs[locale["code"]]["strings"]["errors"]
            home = href(self.base, locale["path_prefix"])
            search = href(self.base, locale["path_prefix"] + "search/")
            search_label = {"en": "Search", "es-419": "Buscar", "zh-Hans": "搜索"}[locale["code"]]
            blocks.append(f'<section lang="{esc(locale["html_lang"])}"><h1>{esc(strings["not_found_title"])}</h1><p>{esc(strings["not_found_body"])}</p><div class="landing-jump"><a href="{esc(home)}">{esc(strings["not_found_home"])}</a><a href="{esc(search)}">{esc(search_label)}</a></div></section>')
        # Same switch as before: the script picks the locale section from the URL prefix.
        locale_script = ('<script>(()=>{let p=location.pathname,l=p.includes("/es/")?"es-419":p.includes("/zh/")?"zh-Hans":"en";'
                         'document.documentElement.lang=l;document.documentElement.dataset.errorLocale=l})()</script>')
        html = document(
            locale=en, catalog=self.catalogs[en["code"]], config=self.config, base=self.base, path="",
            title="404 · FCMO AI", description="The page you asked for does not exist or has moved.",
            body='<div class="not-found">' + "".join(blocks) + '</div>',
            canonical=absolute(self.base_url, "404.html"), alternates=[],
            extra_head='<meta name="robots" content="noindex">' + locale_script,
        )
        (self.out / "404.html").write_text(html, encoding="utf-8")

    def build(self) -> int:
        resolved = self.out.resolve()
        if resolved in {Path("/").resolve(), ROOT.resolve(), Path.cwd().resolve()}:
            raise ValueError(f"refusing unsafe --out {resolved}")
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        copy_public_tree(ROOT / "site-src" / "assets", self.out / "assets")
        # Retain the original public agent datasets as compatibility surfaces.
        copy_public_tree(ROOT / "release-src" / "data", self.out / "data")
        # Citation versions are content-addressed and append-only across deployments.
        if self.citation_history.is_dir():
            copy_public_tree(self.citation_history, self.out / "data" / "citations")
        self._copy_story_media()
        essays.write_public_source(self.editorial_path, self.out, self.editorial_pieces, self.editorial_issues)
        write_localized_story_graphics(self.stories, self.catalogs, self.out / "assets" / "story-media")
        if self.og_source is not None:
            if not self.og_source.is_dir():
                raise ValueError(f"--og-source is not a directory: {self.og_source}")
            copy_public_tree(self.og_source, self.out / "og")
        (self.out / "assets" / "js").mkdir(parents=True, exist_ok=True)
        (self.out / "assets" / "js" / "search.js").write_text(SEARCH_JS, encoding="utf-8")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {self.base_url.rstrip('/')}/sitemap.xml\n", encoding="utf-8")
        ranked = sorted(self.live, key=lambda s: (s.get("event_at", ""), s["id"]), reverse=True)
        topic_counts = Counter(topic for story in self.live for topic in story.get("topics", []))
        org_counts = Counter(org for story in self.live for org in story.get("organizations", []))
        for locale in self.config["locales"]:
            catalog = self.catalogs[locale["code"]]
            self._editorial_routes(locale)
            if not hasattr(self, "_editorial_shelf"): self._editorial_shelf = {}
            self._editorial_shelf[locale["code"]] = "".join(part for part in (
                essays.render_shelf(self.editorial_pieces, locale["code"], base=self.base),
                essays.render_issue_shelf(self.editorial_issues, locale["code"], base=self.base),
                community.render_cartas(self.cartas, locale["code"])) if part)
            self._front(locale)
            self._newsletter_pages(locale)
            for story in self.live:
                self._story(story, locale)
            for story in self.stories:
                if story not in self.live and story.get("status") in {"withdrawn", "merged"} and story.get("corrections"):
                    self._story(story, locale)
            self._listing(locale=locale, suffix="archive/", title=catalog["strings"]["archive"]["title"], stories=ranked, kind="archive")
            for date in self.edition_dates:
                values = [s for s in ranked if s["url_date"] == date]
                title = catalog["strings"]["archive"]["edition_title"].format(date=format_date(date+"T12:00:00Z",catalog))
                self._listing(locale=locale, suffix=f"edition/{date}/", title=title, stories=values, kind="edition")
            for beat in BEATS:
                self._listing(locale=locale, suffix=f"beat/{beat}/", title=label(catalog,"beat",beat), stories=[s for s in ranked if s.get("beat")==beat], kind="beat")
            for topic, count in sorted(topic_counts.items()):
                if count >= 3:
                    self._listing(locale=locale, suffix=f"topic/{slugify(topic)}/", title=catalog["strings"]["archive"]["topic_title"].format(topic=topic), stories=[s for s in ranked if topic in s.get("topics",[])], kind="topic")
            for organization in sorted(org_counts):
                template = catalog["strings"]["archive"]["org_title"]
                before, marker, after = template.partition("{organization}")
                title = template.format(organization=organization)
                title_html = (
                    f'{esc(before)}<span translate="no" data-field="organizations">{esc(organization)}</span>{esc(after)}'
                    if marker else None
                )
                self._listing(locale=locale, suffix=f"org/{slugify(organization)}/", title=title,
                              title_html=title_html,
                              stories=[s for s in ranked if organization in s.get("organizations",[])], kind="org")
            self._status(locale)
            self._simple_pages(locale)
            editorial_rows = essays.piece_search_rows(self.editorial_pieces, locale["code"], base=self.base)
            shards = search_index.build(self.live, locale=locale, catalog=catalog, base=self.base,
                                        out=self.out / locale["path_prefix"] / "data" / "search.json",
                                        extra_rows=editorial_rows)
            self._search(locale, shards)
        self._404()
        feed_paths = feeds.write_all(self.stories, locales=self.config["locales"], catalogs=self.catalogs, base_url=self.base_url, out=self.out)
        essays.write_feeds(self.editorial_pieces, locales=self.config["locales"], base_url=self.base_url, out=self.out)
        redirect_paths = redirects.build(self.stories, published_edition_dates=self.edition_dates, locales=self.config["locales"], base=self.base, out=self.out, legacy_root=ROOT / "site")
        sitemaps.write(self.routes, out=self.out, generated_at=self.payload["generated_at"])
        agent_layer.build(published_edition_dates=self.edition_dates, stories=self.live, all_stories=self.stories, locales=self.config["locales"],
                          catalogs=self.catalogs, status=self.status, base_url=self.base_url,
                          base=self.base, out=self.out, root=ROOT)
        for locale in self.config["locales"]:
            code, prefix = locale["code"], locale["path_prefix"]
            rows = essays.feed_items(self.editorial_pieces, code, base_url=self.base_url)
            path = self.out / prefix / "llms.txt"
            if path.exists() and rows:
                addition = "\n## Human essays and letters\n\n" + "\n".join(f"- [{row['title']}]({row['url']}) — {row['dek']}" for row in rows) + "\n"
                path.write_text(path.read_text(encoding="utf-8") + addition, encoding="utf-8")
            full = self.out / prefix / "llms-full.txt"
            if full.exists():
                chunks = []
                for piece in self.editorial_pieces:
                    if piece["status"] == "published" and piece["locales"][code] == "ready" and code in piece["docs"]:
                        doc = piece["docs"][code]
                        chunks.extend([f"# {doc['title']}", "", doc["dek"], ""])
                        chunks.extend(essays.essay_doc.text_of(block.get("content", [])) for block in doc["blocks"])
                        chunks.append("")
                if chunks: full.write_text(full.read_text(encoding="utf-8") + "\n## Human essays and letters\n\n" + "\n".join(chunks), encoding="utf-8")
            for issue in self.editorial_issues:
                title, description, body = essays.render_issue(issue, code, {p["id"]: p for p in self.editorial_pieces}, {s["id"]: s for s in self.live}, base=self.base, catalog=self.catalogs[code])
                # Issue discovery is included in routes/sitemap; prose is linked from its page.
        (self.out / "data").mkdir(exist_ok=True)
        (self.out / "data" / "routes.json").write_text(json.dumps(self.routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(self.stories_path, self.out / "data" / "stories.v2.json")
        shutil.copyfile(self.status_path, self.out / "data" / "newsroom-status.json")
        (self.out / "status.json").write_text(json.dumps(self.status["publication_status"],
                                                      indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        js_size = sum(path.stat().st_size for path in self.out.rglob("*.js"))
        if js_size > 30 * 1024:
            raise ValueError(f"JavaScript budget exceeded: {js_size}")
        print(f"routes={self.page_count} feeds={len(feed_paths)} redirects={len(redirect_paths)} js_bytes={js_size}")
        return self.page_count

    def _copy_story_media(self) -> None:
        source_root = (ROOT / "site").resolve()
        out_root = self.out.resolve()
        for story in self.stories:
            local = str((story.get("media") or {}).get("local_path") or "").strip().lstrip("/")
            if not local:
                continue
            source = (source_root / local).resolve()
            target = (out_root / local).resolve()
            if source_root not in source.parents or out_root not in target.parents:
                raise ValueError(f"unsafe story media path: {local}")
            if target.is_file():
                continue
            if not source.is_file():
                raise ValueError(f"referenced story media is missing: site/{local}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stories", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base", default="/")
    parser.add_argument("--editorial", type=Path, default=ROOT / "editorial")
    parser.add_argument("--og-source", type=Path, help="cards produced by og_image.py; copied to publish/og")
    parser.add_argument("--citation-history", type=Path, help="prior content-addressed citations to retain (default: site/data/citations)")
    args = parser.parse_args(argv)
    try:
        PaperBuilder(stories_path=args.stories, status_path=args.status, editorial_path=args.editorial, out=args.out, base=args.base, og_source=args.og_source, citation_history=args.citation_history).build()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"paper build FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
