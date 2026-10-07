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
    from tools.agent import build as agent_layer
    from tools.paper.i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, plural, story_locale, truncate
    from tools.paper.routes import absolute, beat_path, edition_path, href, issue_path, org_path, output_path, piece_path, story_path, topic_path
    from tools.paper.status_banner import freshness_attributes, freshness_sentence, render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from tools.paper.templates import archive_page, document, front_page, simple_page, status_page, story_page
    from tools.paper.templates.pages import evidence_board, evidence_strip, story_card
    from tools.paper.templates.landing import render as render_landing
    from tools.paper.templates.reader import (LAYER_SCRIPT, automation_badge, brief, claim_kind, data_hero, evidence_glyph,
                                              first_sentence, layer, primary_source, provenance_line, reader_select, status_chip)
    from tools.paper.templates.newsletter import render as render_newsletter, subscription_tail
    from tools.paper.routes import TECHNICAL_FRONT
else:
    from . import community, essays, feeds, redirects, search_index, sitemaps
    from .freshness import corpus_freshness
    from .front_order import front_order
    from .front_plan import front_plan
    from tools.agent import build as agent_layer
    from .i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, plural, story_locale, truncate
    from .routes import absolute, beat_path, edition_path, href, issue_path, org_path, output_path, piece_path, story_path, topic_path
    from .status_banner import freshness_attributes, freshness_sentence, render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from .templates import archive_page, document, front_page, simple_page, status_page, story_page
    from .templates.pages import evidence_board, evidence_strip, story_card
    from .templates.landing import render as render_landing
    from .templates.reader import (LAYER_SCRIPT, automation_badge, brief, claim_kind, data_hero, evidence_glyph,
                                   first_sentence, layer, primary_source, provenance_line, reader_select, status_chip)
    from .templates.newsletter import render as render_newsletter, subscription_tail
    from .routes import TECHNICAL_FRONT

ROOT = Path(__file__).resolve().parents[2]
from tools.publication_freshness import publication_status, reader_status
BEATS = ("technology", "business", "policy", "society", "research")

SEARCH_JS = r'''(()=>{const f=document.querySelector('[data-search-form]'),q=document.querySelector('[data-search-input]'),o=document.querySelector('[data-search-results]');if(!f)return;let rows;const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));f.addEventListener('submit',async e=>{e.preventDefault();let term=q.value.trim().toLocaleLowerCase();if(!term)return;if(!rows){o.textContent=o.dataset.loading;rows=await fetch(f.dataset.index).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).catch(()=>[])}let hits=rows.filter(x=>[x.h,x.d,x.b,...x.o,...x.t].join(' ').toLocaleLowerCase().includes(term)).slice(0,30);o.innerHTML=hits.length?hits.map(x=>`<article class="story-card"><span class="card-meta">${esc(x.b)}</span><h2><a href="${esc(x.u)}">${esc(x.h)}</a></h2><p>${esc(x.d)}</p></article>`).join(''):`<p>${esc(o.dataset.empty.replace('{query}',term))}</p>`})})()'''


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def copy_public_tree(source: Path, target: Path) -> None:
    """Copy file bytes and directory shape only; host ACLs, xattrs and modes are not publication data."""
    for directory, _, files in os.walk(source, followlinks=True):
        relative = Path(directory).relative_to(source)
        (target / relative).mkdir(parents=True, exist_ok=True)
        for name in files:
            shutil.copyfile(Path(directory) / name, target / relative / name)


def slugify(value: str) -> str:
    value = value.casefold().strip()
    chars = []
    for char in value:
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "item"


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
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — fCMO", description=description,
                             body=body, kind="essay", status=True,
                             index=(piece["status"] == "published" and piece["locales"][code] == "ready"))
        for issue in self.editorial_issues:
            title, description, body = essays.render_issue(issue, code, by_id, stories_by_id,
                                                           base=self.base, catalog=self.catalogs[code])
            suffix = issue_path({"path_prefix": ""}, issue)
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — fCMO", description=description,
                             body=body, kind="issue", index=True)
        # Issue and piece links are represented in every locale's discovery index;
        # pending translations intentionally do not leak source prose.

    def _alternates(self, suffix: str) -> list[tuple[str, str]]:
        values = [(loc["hreflang"], absolute(self.base_url, loc["path_prefix"] + suffix)) for loc in self.config["locales"]]
        default = next(loc for loc in self.config["locales"] if loc["code"] == self.config["x_default_locale"])
        values.append(("x-default", absolute(self.base_url, default["path_prefix"] + suffix)))
        return values

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
            json_ld=json_ld, extra_head=extra_head, body_class=f"page-{kind}",
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
    def _title_class(title: str, locale_code: str) -> str:
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
        if width > 46:
            return "title-large"
        if width > 34:
            return "title-medium"
        return "title-short"

    def _card(self, story: dict, locale: dict, level: int = 2) -> str:
        catalog = self.catalogs[locale["code"]]
        context = f'{self.catalogs[locale["code"]]["strings"]["story"]["importance"].format(score=story.get("importance", 0))}'
        return story_card(
            story, href=self._story_href(locale, story), headline=headline(story, locale["code"], catalog),
            dek=truncate(dek(story, locale["code"], catalog), 190), beat=label(catalog, "beat", story.get("beat")),
            date=format_date(story["event_at"], catalog, precision=story.get("date_precision", "day")), level=level,
            context=context, evidence=evidence_strip(story, catalog),
        )

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

    def _story_navigation(self, story: dict, locale: dict) -> str:
        strings = self.catalogs[locale["code"]]["strings"]
        sequence = sorted(self.live, key=lambda item: (item.get("url_date", ""), *self._story_rank(item)), reverse=True)
        position = next((i for i, item in enumerate(sequence) if item["id"] == story["id"]), -1)
        neighbors = []
        if position >= 0:
            if position > 0:
                neighbors.append((strings["archive"]["newer"], sequence[position - 1], "next"))
            if position + 1 < len(sequence):
                neighbors.append((strings["archive"]["older"], sequence[position + 1], "previous"))
        edition_links = "".join(
            f'<a rel="{rel}" href="{esc(self._story_href(locale, item))}"><span class="card-meta">{esc(label(self.catalogs[locale["code"]], "beat", item.get("beat")))}</span><strong>{esc(direction)}</strong><span>{esc(headline(item, locale["code"], self.catalogs[locale["code"]]))}</span></a>'
            for direction, item, rel in neighbors
        )
        related = self._related_stories(story)
        related_cards = "".join(
            f'<article class="story-card"><span class="card-meta" translate="no">{esc(label(self.catalogs[locale["code"]], "beat", item.get("beat")) if reason == "same-beat" else reason)}</span><h3><a href="{esc(self._story_href(locale, item))}">{esc(headline(item, locale["code"], self.catalogs[locale["code"]]))}</a></h3><p>{esc(truncate(dek(item, locale["code"], self.catalogs[locale["code"]]), 160))}</p></article>'
            for item, reason in related
        )
        parts = []
        if edition_links:
            parts.append(f'<nav class="edition-neighbors" aria-label="{esc(strings["story"]["related"])}">{edition_links}</nav>')
        if related_cards:
            parts.append(f'<section class="related-reading"><h2>{esc(strings["story"]["related"])}</h2><div class="card-row">{related_cards}</div></section>')
        return "".join(parts)

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
        anchors: list[tuple[int, str, str]] = []
        for story in self.live:
            topics = [value for value in story.get("topics", []) if value != exclude_topic and slugify(value) != exclude_topic]
            orgs = [value for value in story.get("organizations", []) if value != exclude_org and slugify(value) != exclude_org]
            for value in topics:
                count = sum(value in (other.get("topics") or []) for other in self.live)
                if count >= 3:
                    anchors.append((count, value, href(self.base, locale["path_prefix"] + "topic/" + slugify(value) + "/")))
            for value in orgs:
                anchors.append((sum(value in (other.get("organizations") or []) for other in self.live), value,
                                href(self.base, locale["path_prefix"] + "org/" + slugify(value) + "/")))
        unique: dict[tuple[str, str], int] = {}
        for count, value, url in anchors:
            unique[(value, url)] = max(count, unique.get((value, url), 0))
        selected = sorted(((count, value, url) for (value, url), count in unique.items()),
                          key=lambda row: (-row[0], row[1].casefold()))[:limit]
        links = "".join(f'<li><a href="{esc(url)}" translate="no">{esc(value)}</a><span>{count}</span></li>'
                        for count, value, url in selected)
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
            body = simple_page(strings["archive"]["empty"], "")
            self._write_page(locale=locale, suffix=TECHNICAL_FRONT, title=strings["site"]["name"], description=strings["site"]["description"], body=body, kind="front")
            landing = render_landing(locale=locale, home=href(self.base, locale["path_prefix"]), technical=href(self.base, locale["path_prefix"]+TECHNICAL_FRONT), about=href(self.base, locale["path_prefix"]+"about/"), subscribe=href(self.base, locale["path_prefix"]+"suscribete/"), lead="", top="", cartas=community.render_cartas(self.cartas, locale["code"]), stats=stats)
            _, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url)
            self._write_page(locale=locale, suffix="", title="FCMO", description="FCMO: Javier's fCMO letters and the FCMO AI technical daily", body=landing, kind="landing", extra_head=subscribe_script, machine_alternates=[("text/plain", href(self.base, "llms.txt")), ("application/json", href(self.base, "agent.json"))])
            return
        plan = front_plan(order, BEATS)
        first = plan["lead"]
        lead_title = headline(first, locale["code"], catalog)
        lead_class = self._title_class(lead_title, locale["code"])
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
        self._write_page(locale=locale, suffix=TECHNICAL_FRONT, title=f'{strings["site"]["name"]} — {strings["site"]["tagline"]}', description=strings["site"]["description"], body=body, kind="front", og_image=self._media_url(first, locale), extra_head=subscribe_script)
        landing = render_landing(locale=locale, home=href(self.base, locale["path_prefix"]), technical=href(self.base, locale["path_prefix"]+TECHNICAL_FRONT), about=href(self.base, locale["path_prefix"]+"about/"), subscribe=href(self.base, locale["path_prefix"]+"suscribete/"), lead=lead, top=top, cartas=cartas, stats=stats, feature=feature)
        self._write_page(locale=locale, suffix="", title="FCMO", description="FCMO: Javier's fCMO letters and the FCMO AI technical daily", body=landing, kind="landing", og_image=self._media_url(first, locale), extra_head=subscribe_script, machine_alternates=[("text/plain", href(self.base, "llms.txt")), ("application/json", href(self.base, "agent.json"))])

    def _newsletter_pages(self, locale: dict) -> None:
        ranked = sorted(self.live, key=lambda s: (s.get("event_at", ""), s["id"]), reverse=True)
        cards = "".join(self._card(story, locale, 3) for story in ranked[:3])
        topic_counts = Counter(topic for story in self.live for topic in story.get("topics", []))
        topics = [(name, count, slugify(name)) for name, count in topic_counts.most_common() if count >= 3][:8]
        root = href(self.base, locale["path_prefix"])
        technical = href(self.base, locale["path_prefix"] + TECHNICAL_FRONT)
        cartas = getattr(self, "_editorial_shelf", {}).get(locale["code"], community.render_cartas(self.cartas, locale["code"]))
        for kind, suffix in (("letters", "cartas/"), ("guide", "empieza/"), ("community", "comunidad/")):
            title, description, body = render_newsletter(kind, locale=locale["code"], root=root,
                                                          technical=technical, cards=cards, cartas=cartas, topics=topics)
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — fCMO", description=description,
                             body=body, kind=kind)

    def _localized_evidence(self, story: dict, locale: dict) -> dict:
        if locale["code"] == "en":
            return story.get("evidence") or {}
        value = field(story, locale["code"], "evidence", {})
        return value if isinstance(value, dict) else {}

    def _story(self, story: dict, locale: dict) -> None:
        code = locale["code"]
        catalog = self.catalogs[code]
        strings = catalog["strings"]
        if story.get("status") in {"withdrawn", "merged"} and story.get("corrections"):
            self._correction_notice(story, locale)
            return
        complete = is_complete(story, code)
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
                    f'<a href="{esc(english)}" lang="en" hreflang="en">English original</a></p>')
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
            body = (brief(story, catalog, summary=field(story, code, "summary"), why=field(story, code, "why_it_matters"), evidence=evidence)
                    + reader_select(catalog)
                    + '<div class="layers" data-layers data-mode="summary">'
                    + layer("argument", dz["argument_title"], dz["layer_r2"], "".join(argument))
                    + layer("dossier", dz["dossier_title"], dz["layer_r4"], "".join(dossier))
                    + layer("technical", dz["technical_title"], dz["layer_r3"], "".join(technical_layer))
                    + '</div>' + LAYER_SCRIPT)
            aside = self._facts(story, locale)
        hero = ""
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

    def _correction_notice(self, story: dict, locale: dict) -> None:
        code = locale["code"]
        catalog = self.catalogs[code]
        strings = catalog["strings"]
        fix = story["corrections"][-1]
        text = fix.get("text") or {}
        notice = text.get(code) or text.get("en") or strings["story"].get(story["status"], "")
        kind = label(catalog, "correction_kind", fix.get("kind"), fallback=story["status"].title())
        title = headline(story, code, catalog)
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
            (strings["importance_rationale"], strings["importance"].format(score=story.get("importance", ""))),
            (strings["evidence"], label(catalog, "evidence_class", story.get("evidence_class"))),
            (confidence_heading, label(catalog, "confidence", story.get("confidence"))),
        ]
        facts = "".join(f'<div class="fact"><dt>{esc(key)}</dt><dd>{esc(value)}</dd></div>' for key, value in values if value)
        topic_items = []
        for topic in story.get("topics") or []:
            label_html = f'<span translate="no" data-field="topics">{esc(topic)}</span>'
            if sum(topic in (item.get("topics") or []) for item in self.live) >= 3:
                label_html = f'<a href="{esc(href(self.base, locale["path_prefix"] + "topic/" + slugify(topic) + "/"))}" translate="no">{label_html}</a>'
            topic_items.append(f'<li>{label_html}</li>')
        topics = "".join(topic_items)
        orgs = "".join(f'<li><a href="{esc(href(self.base, locale["path_prefix"] + "org/" + slugify(org) + "/"))}" translate="no"><span translate="no" data-field="organizations">{esc(org)}</span></a></li>' for org in story.get("organizations") or [])
        return (f'<dl>{facts}</dl>'
                + (f'<section class="story-taxonomy"><h2>{esc(strings["organizations"])}</h2><ul>{orgs}</ul></section>' if orgs else "")
                + (f'<section class="story-taxonomy"><h2>{esc(strings["topics"])}</h2><ul>{topics}</ul></section>' if topics else ""))

    def _listing(self, *, locale: dict, suffix: str, title: str, stories: list[dict], kind: str,
                 title_html: str | None = None) -> None:
        catalog = self.catalogs[locale["code"]]
        items = "".join(f'<article class="archive-item" data-story-id="{esc(story["id"])}"><time datetime="{esc(story["event_at"])}">{esc(format_date(story["event_at"],catalog,precision=story.get("date_precision","day")))}</time><a class="archive-art" href="{esc(self._story_href(locale,story))}" aria-hidden="true" tabindex="-1"><img src="{esc(self._story_media_url(story, locale))}" alt="" width="320" height="180" loading="lazy"></a><div class="archive-copy"><h2><a href="{esc(self._story_href(locale,story))}">{esc(headline(story,locale["code"],catalog))}</a></h2><p>{esc(truncate(dek(story,locale["code"],catalog),220))}</p><p class="archive-meta">{esc(label(catalog, "beat", story.get("beat")))} · {esc(catalog["strings"]["story"]["importance"].format(score=story.get("importance", 0)))}</p>{evidence_strip(story, catalog)}</div></article>' for story in stories)
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
        body = archive_page(title, catalog["strings"]["site"]["description"], items or f'<p>{esc(catalog["strings"]["archive"]["empty"])}</p>', kicker=catalog["strings"]["kicker"]["archive"], title_html=title_html, context=context, navigation=navigation)
        resources = None
        if kind == "edition":
            date = suffix.strip("/").split("/")[-1]
            resources = [("text/markdown", absolute(self.base_url, locale["path_prefix"] + f"edition/{date}.md")),
                         ("application/json", absolute(self.base_url, f"api/v1/editions/{date}.json"))]
        self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=title, body=body, kind=kind, machine_alternates=resources)

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

    def _search(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        index_url = href(self.base, locale["path_prefix"] + "data/search.json")
        body = simple_page(strings["search"]["title"], f'<form class="search-box" data-search-form data-index="{esc(index_url)}"><label class="visually-hidden" for="q">{esc(strings["a11y"]["search_label"])}</label><input id="q" type="search" data-search-input placeholder="{esc(strings["search"]["placeholder"])}"><button class="button" type="submit">{esc(strings["nav"]["search"])}</button></form><div class="search-results" data-search-results data-loading="{esc(strings["search"]["loading"])}" data-empty="{esc(strings["search"]["no_results"])}" aria-live="polite"></div><noscript><p>{esc(strings["search"]["needs_js"])}</p></noscript>')
        script = f'<script defer src="{esc(href(self.base,"assets/js/search.js"))}"></script>'
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
        method_intro = (f'<p class="method-intro">{esc(localized_method["intro"])}</p>'
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
            note = text.get(locale["code"]) or text.get("en") or ""
            title = headline(story, locale["code"], catalog)
            date = correction.get("at") or story.get("updated_at")
            correction_rows.append(
                f'<article class="correction">'
                f'<time datetime="{esc(date)}">{esc(format_date(date, catalog))}</time>'
                f'<h2><a href="{esc(self._correction_href(locale, story))}">{esc(title)}</a></h2>'
                f'<p>{esc(note)}</p></article>')
        corr_body = f'<p>{esc(s["corrections_page"]["intro"])}</p>' + (
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
        subscribe_title = community.subscribe_page_title(locale["code"], self.portal_url)
        recent = sorted(self.live, key=lambda story: (story.get("event_at", ""), story["id"]), reverse=True)[:3]
        cards = "".join(self._card(story, locale, 3) for story in recent)
        tail = subscription_tail(locale=locale["code"], root=href(self.base, locale["path_prefix"]),
                                 technical=href(self.base, locale["path_prefix"] + TECHNICAL_FRONT), cards=cards)
        self._write_page(locale=locale, suffix="suscribete/", title=f"{subscribe_title} — fCMO + FCMO AI", description=community.COPY[locale["code"]]["promise"], body=f'<article class="story-body">{subscribe}</article>{tail}', kind="subscribe", extra_head=subscribe_script)

    def _404(self) -> None:
        blocks = []
        for locale in self.config["locales"]:
            strings = self.catalogs[locale["code"]]["strings"]["errors"]
            home = href(self.base, locale["path_prefix"])
            technical = href(self.base, locale["path_prefix"]+TECHNICAL_FRONT)
            search = href(self.base, locale["path_prefix"]+"search/")
            search_label = {"en": "Search", "es-419": "Buscar", "zh-Hans": "搜索"}[locale["code"]]
            blocks.append(f'<section lang="{esc(locale["html_lang"])}"><p class="section-kicker">FCMO / FCMO AI</p><h2>{esc(strings["not_found_title"])}</h2><p>{esc(strings["not_found_body"])}</p><div class="landing-jump"><a href="{esc(home)}">{esc(strings["not_found_home"])}</a><a href="{esc(technical)}">FCMO AI Diario</a><a href="{esc(search)}">{esc(search_label)}</a></div></section>')
        html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><script>(()=>{let p=location.pathname,l=p.includes("/es/")?"es-419":p.includes("/zh/")?"zh-Hans":"en";document.documentElement.lang=l;document.documentElement.dataset.errorLocale=l})()</script><link rel="icon" href="' + esc(href(self.base,"assets/pwa/favicon.svg")) + '" type="image/svg+xml"><link rel="apple-touch-icon" href="' + esc(href(self.base,"assets/pwa/icons/icon-192.svg")) + '"><link rel="stylesheet" href="' + esc(href(self.base,"assets/css/paper.css")) + '"><title>404 · FCMO</title></head><body><a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="masthead"><a class="brand" href="' + esc(href(self.base,"")) + '">FCMO</a><span class="brand-sub">fCMO + FCMO AI</span></div></header><main id="main" class="page-shell not-found"><h1>404</h1>' + "".join(blocks) + '</main><footer class="site-footer"><div class="footer-inner"><div class="footer-brand">FCMO · fCMO · FCMO AI</div></div></footer></body></html>'
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
            self._search(locale)
            self._simple_pages(locale)
            search_size = search_index.build(self.live, locale=locale, catalog=catalog, base=self.base, out=self.out / locale["path_prefix"] / "data" / "search.json")
            editorial_rows = essays.piece_search_rows(self.editorial_pieces, locale["code"], base=self.base)
            search_path = self.out / locale["path_prefix"] / "data" / "search.json"
            current = json.loads(search_path.read_text(encoding="utf-8"))
            current.extend(editorial_rows)
            encoded = json.dumps(current, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(encoded) > search_index.LIMIT: raise ValueError(f"search index exceeds {search_index.LIMIT} bytes for {locale['code']}: {len(encoded)}")
            search_path.write_bytes(encoded)
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
