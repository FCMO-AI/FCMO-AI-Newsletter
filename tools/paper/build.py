#!/usr/bin/env python3
"""Build the FCMO AI newspaper as locale-specific static HTML."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import shutil
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.paper import community, feeds, redirects, search_index, sitemaps
    from tools.agent import build as agent_layer
    from tools.paper.i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, story_locale, truncate
    from tools.paper.routes import absolute, beat_path, edition_path, href, org_path, output_path, story_path, topic_path
    from tools.paper.status_banner import render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from tools.paper.templates import archive_page, document, front_page, simple_page, status_page, story_page
    from tools.paper.templates.pages import story_card
else:
    from . import community, feeds, redirects, search_index, sitemaps
    from tools.agent import build as agent_layer
    from .i18n import dek, field, format_date, headline, is_complete, label, load_catalogs, story_locale, truncate
    from .routes import absolute, beat_path, edition_path, href, org_path, output_path, story_path, topic_path
    from .status_banner import render as render_banner
    from tools.visual_desk import write_localized_story_graphics
    from .templates import archive_page, document, front_page, simple_page, status_page, story_page
    from .templates.pages import story_card

ROOT = Path(__file__).resolve().parents[2]
BEATS = ("technology", "business", "policy", "society", "research")

SEARCH_JS = r'''(()=>{const f=document.querySelector('[data-search-form]'),q=document.querySelector('[data-search-input]'),o=document.querySelector('[data-search-results]');if(!f)return;let rows;const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));f.addEventListener('submit',async e=>{e.preventDefault();let term=q.value.trim().toLocaleLowerCase();if(!term)return;if(!rows){o.textContent=o.dataset.loading;rows=await fetch(f.dataset.index).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).catch(()=>[])}let hits=rows.filter(x=>[x.h,x.d,x.b,...x.o,...x.t].join(' ').toLocaleLowerCase().includes(term)).slice(0,30);o.innerHTML=hits.length?hits.map(x=>`<article class="story-card"><span class="card-meta">${esc(x.b)}</span><h2><a href="${esc(x.u)}">${esc(x.h)}</a></h2><p>${esc(x.d)}</p></article>`).join(''):`<p>${esc(o.dataset.empty.replace('{query}',term))}</p>`})})()'''


def esc(value: object) -> str:
    return escape(str(value), quote=True)


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
                 og_source: Path | None = None) -> None:
        self.stories_path = stories_path
        self.status_path = status_path
        self.payload = json.loads(stories_path.read_text(encoding="utf-8"))
        self.status = json.loads(status_path.read_text(encoding="utf-8"))
        self.config = json.loads((ROOT / "config" / "site.json").read_text(encoding="utf-8"))
        self.catalogs = load_catalogs(ROOT)
        self.stories = self.payload["stories"]
        self.live = [story for story in self.stories if story.get("status") == "live"]
        self.out = out
        self.base = "/" + base.strip("/") + "/" if base.strip("/") else "/"
        self.base_url = self.config["base_url"]
        self.og_source = og_source
        self.cartas = community.fetch_cartas(os.environ.get("GHOST_CONTENT_URL"), os.environ.get("GHOST_CONTENT_API_KEY"))
        self.portal_url = os.environ.get("GHOST_PORTAL_URL")
        self.routes: list[dict] = []
        self.page_count = 0

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
            status_banner=render_banner(self.status, self.catalogs[locale["code"]], base=self.base, locale=locale) if status else "",
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
        return story_card(
            story, href=self._story_href(locale, story), headline=headline(story, locale["code"], catalog),
            dek=truncate(dek(story, locale["code"], catalog), 190), beat=label(catalog, "beat", story.get("beat")),
            date=format_date(story["event_at"], catalog, precision=story.get("date_precision", "day")), level=level,
        )

    def _front(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        ranked = sorted(self.live, key=lambda s: (bool(s.get("front_page_eligible")), s.get("importance", 0), s.get("event_at", ""), s["id"]), reverse=True)
        if not ranked:
            body = simple_page(strings["archive"]["empty"], "")
            self._write_page(locale=locale, suffix="", title=strings["site"]["name"], description=strings["site"]["description"], body=body, kind="front")
            return
        first, rest = ranked[0], ranked[1:]
        hero = first.get("media") or {}
        hero_path = self._story_media_url(first, locale)
        hero_alt = (hero.get("alt") or {}).get(locale["code"], "")
        lead_title = headline(first, locale["code"], catalog)
        lead_class = self._title_class(lead_title, locale["code"])
        lead = f'''<article class="lead"><p class="story-kicker">{esc(strings["front"]["lead"])} · {esc(label(catalog,"beat",first.get("beat")))}</p><h1 class="{lead_class}"><a href="{esc(self._story_href(locale,first))}">{esc(lead_title)}</a></h1><p class="lead-dek">{esc(dek(first,locale["code"],catalog))}</p><p class="story-meta">{esc(format_date(first["event_at"],catalog,precision=first.get("date_precision","day")))}</p><figure class="hero"><img src="{esc(hero_path)}" alt="{esc(hero_alt)}" width="1200" height="630"><figcaption>{esc(strings["story"]["image_credit"].format(credit=hero.get("credit","FCMO AI")))}</figcaption></figure></article>'''
        top_values = rest[:4]
        top = f'<h2>{esc(strings["front"]["top_stories"])}</h2>' + "".join(self._card(story, locale, 3) for story in top_values)
        essential_values = ranked[:5]
        essentials = f'<div><p class="section-kicker">FCMO AI · {esc(strings["front"]["essentials"])}</p><h2>{esc(strings["front"]["essentials"])}</h2></div><ol>' + "".join(f'<li><a href="{esc(self._story_href(locale,s))}">{esc(headline(s,locale["code"],catalog))}</a></li>' for s in essential_values) + "</ol>"
        sections = []
        for beat in BEATS:
            values = [s for s in ranked if s.get("beat") == beat][:3]
            if not values:
                continue
            beat_label = label(catalog, "beat", beat)
            sections.append(f'<section class="beat-section"><div class="section-head"><div><p class="section-kicker">{esc(beat_label)}</p><h2>{esc(beat_label)}</h2></div><a href="{esc(href(self.base,beat_path(locale,beat)))}">{esc(strings["front"]["see_all"])}</a></div><div class="card-row">{"".join(self._card(s,locale,3) for s in values)}</div></section>')
        developing_values = [s for s in ranked if s.get("confidence") not in {"confirmed", "strongly_supported"}][:2]
        developing = ""
        if developing_values:
            developing = f'<section class="developing-well"><div class="section-head"><div><p class="section-kicker">FCMO AI · signal</p><h2>{esc(strings["front"]["developing"])}</h2></div></div><div class="card-row">{"".join(self._card(s,locale,3) for s in developing_values)}</div></section>'
        cartas = community.render_cartas(self.cartas, locale["code"])
        subscribe, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url)
        dates = sorted({s["url_date"] for s in self.live}, reverse=True)[:6]
        editions = f'<section class="beat-section"><div class="section-head"><h2>{esc(strings["front"]["editions"])}</h2><a href="{esc(href(self.base,locale["path_prefix"]+"archive/"))}">{esc(strings["nav"]["archive"])}</a></div><div class="card-row">' + "".join(f'<article class="story-card"><h3><a href="{esc(href(self.base,edition_path(locale,date)))}">{esc(strings["archive"]["edition_title"].format(date=format_date(date+"T12:00:00Z",catalog)))}</a></h3></article>' for date in dates) + "</div></section>"
        body = front_page(lead=lead, top=top, essentials=essentials, beats="".join(sections), developing=developing, subscribe=subscribe, cartas=cartas, editions=editions)
        body = community.without_empty_cartas_slot(body, cartas)
        self._write_page(locale=locale, suffix="", title=f'{strings["site"]["name"]} — {strings["site"]["tagline"]}', description=strings["site"]["description"], body=body, kind="front", og_image=self._media_url(first, locale), extra_head=subscribe_script)

    def _localized_evidence(self, story: dict, locale: dict) -> dict:
        if locale["code"] == "en":
            return story.get("evidence") or {}
        value = field(story, locale["code"], "evidence", {})
        return value if isinstance(value, dict) else {}

    def _story(self, story: dict, locale: dict) -> None:
        code = locale["code"]
        catalog = self.catalogs[code]
        strings = catalog["strings"]
        complete = is_complete(story, code)
        title = headline(story, code, catalog) if complete else strings["l10n"]["pending_title"]
        description = truncate(dek(story, code, catalog))
        suffix = story_path({**locale, "path_prefix": ""}, story)
        event = format_date(story["event_at"], catalog, precision=story.get("date_precision", "day"))
        published = format_date(story["first_published_at"], catalog, precision="minute")
        title_class = self._title_class(title, code)
        header = f'<header class="story-header"><p class="story-kicker">{esc(label(catalog,"beat",story.get("beat")))}</p><h1>{esc(title)}</h1><p class="story-dek">{esc(description)}</p><p class="story-meta">{esc(strings["story"]["byline"])} · {esc(strings["story"]["event_date"].format(date=event))} · {esc(strings["story"]["published"].format(date=published))}</p></header>'
        if code != "en" and story_locale(story, code).get("state") == "MACHINE_REVIEWED":
            english = self._story_href(self.config["locales"][0], story)
            note = (f'<p class="translation-note" role="note">{esc(strings["l10n"]["desk_note"])} '
                    f'<a href="{esc(english)}" lang="en" hreflang="en">English original</a></p>')
            header = header.replace("</header>", note + "</header>")
        if not complete:
            notice = strings["l10n"]["pending_partial"] if (field(story, code, "headline") or field(story, code, "title")) else strings["l10n"]["pending_notice"]
            english = self._story_href(self.config["locales"][0], story)
            partial = self._pending_fields(story, locale)
            body = f'<section class="pending-panel"><p class="section-kicker">{esc(strings["l10n"]["pending_title"])}</p><p>{esc(notice)}</p><a class="button" href="{esc(english)}" hreflang="en" lang="en">{esc(strings["l10n"]["read_original"])}</a></section>{partial}'
            aside = self._facts(story, locale)
        else:
            evidence = self._localized_evidence(story, locale)
            sections = []
            for heading_key, value in (("what_changed", field(story, code, "summary")), ("why_it_matters", field(story, code, "why_it_matters"))):
                if value:
                    sections.append(f'<section><h2>{esc(strings["story"][heading_key])}</h2><p>{esc(value)}</p></section>')
            claims = evidence.get("claims") or []
            if claims:
                items = []
                for claim in claims:
                    claim_label = label(catalog, "claim_label", claim.get("label"), fallback=label(catalog, "claim_label", f'{claim.get("label","")}_{claim.get("qualifier","")}', fallback=""))
                    items.append(f'<li><span class="evidence-label">{esc(claim_label)}</span>{esc(claim.get("text",""))}</li>')
                sections.append(f'<section><h2>{esc(strings["story"]["evidence"])}</h2><ol class="evidence-list">{"".join(items)}</ol></section>')
            for heading_key, evidence_key in (("limitations", "limitations"), ("unknowns", "gaps"), ("contradictory", "contradictory")):
                values = evidence.get(evidence_key) or []
                if values:
                    lis = "".join(f'<li>{esc(v.get("description","") if isinstance(v,dict) else v)}</li>' for v in values)
                    sections.append(f'<section><h2>{esc(strings["story"][heading_key])}</h2><ul>{lis}</ul></section>')
            technical = field(story, code, "technical", {})
            if isinstance(technical, dict) and technical:
                details = "".join(f'<section><h3>{esc(strings["technical_field"].get(key,key))}</h3><p>{esc(value)}</p></section>' for key, value in technical.items() if value)
                sections.append(f'<section class="developing-well"><h2>{esc(strings["story"]["technical"])}</h2>{details}</section>')
            sources = story.get("sources") or []
            if sources:
                links = "".join(f'<li><a href="{esc(src["url"])}" rel="noopener noreferrer"><span translate="no" data-field="source-domain">{esc(src.get("domain") or src["url"])}</span></a>{" · "+esc(strings["story"]["primary_source"]) if src.get("primary") else ""}</li>' for src in sources)
                sections.append(f'<section><h2>{esc(strings["story"]["sources"])}</h2><ol class="source-list">{links}</ol></section>')
            body = "".join(sections)
            aside = self._facts(story, locale)
        page = story_page(header=header, body=body, aside=aside)
        page = page.replace('<article class="story-layout">', f'<article class="story-layout {title_class}">', 1)
        story_url = absolute(self.base_url, locale["path_prefix"] + suffix)
        image = self._media_url(story, locale)
        structured = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": title, "description": description, "datePublished": story["first_published_at"], "dateModified": story["updated_at"], "mainEntityOfPage": story_url, "image": [image], "author": {"@type": "Organization", "name": "FCMO AI Research Desk"}, "publisher": {"@type": "Organization", "name": "FCMO AI"}}
        if story.get("corrections"):
            structured["correction"] = [c.get("note") or c.get("reason") or c.get("kind", "Correction") for c in story["corrections"]]
        story_api = absolute(self.base_url, f"api/v1/stories/{story['id']}.json")
        story_md = absolute(self.base_url, locale["path_prefix"] + suffix.rstrip("/") + ".md")
        self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=description, body=page, kind="story", story=story, og_image=image, json_ld=structured,
                         machine_alternates=[("text/markdown", story_md), ("application/json", story_api)])

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
        topics = ", ".join(story.get("topics") or [])
        orgs = ", ".join(story.get("organizations") or [])
        return f'<dl>{facts}</dl>' + (f'<p><strong>{esc(strings["organizations"])}</strong><br><span translate="no" data-field="organizations">{esc(orgs)}</span></p>' if orgs else "") + (f'<p><strong>{esc(strings["topics"])}</strong><br>{esc(topics)}</p>' if topics else "")

    def _listing(self, *, locale: dict, suffix: str, title: str, stories: list[dict], kind: str,
                 title_html: str | None = None) -> None:
        catalog = self.catalogs[locale["code"]]
        items = "".join(f'<article class="archive-item"><time datetime="{esc(story["event_at"])}">{esc(format_date(story["event_at"],catalog,precision=story.get("date_precision","day")))}</time><h2><a href="{esc(self._story_href(locale,story))}">{esc(headline(story,locale["code"],catalog))}</a></h2><p>{esc(truncate(dek(story,locale["code"],catalog),220))}</p></article>' for story in stories)
        body = archive_page(title, catalog["strings"]["site"]["description"], items or f'<p>{esc(catalog["strings"]["archive"]["empty"])}</p>', title_html=title_html)
        resources = None
        if kind == "edition":
            date = suffix.strip("/").split("/")[-1]
            resources = [("text/markdown", absolute(self.base_url, locale["path_prefix"] + f"edition/{date}.md")),
                         ("application/json", absolute(self.base_url, f"api/v1/editions/{date}.json"))]
        self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=title, body=body, kind=kind, machine_alternates=resources)

    def _status(self, locale: dict) -> None:
        catalog = self.catalogs[locale["code"]]
        strings = catalog["strings"]
        state = label(catalog, "edition_state", self.status["edition_state"])
        last = format_date(self.status["last_edition_at"], catalog, precision="minute")
        checked = format_date(self.status["status_updated_at"], catalog, precision="minute")
        cards = f'<article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["edition"])}</span><strong>{esc(state)}</strong><p>{esc(strings["status_page"]["last_edition"].format(date=last))}</p></article><article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["translation"])}</span>'
        for code, counts in self.status.get("translation", {}).items():
            cards += f'<strong>{esc(catalog["strings"]["lang"].get(code,code))}</strong><p>{esc(strings["status_page"]["translation_counts"].format(**counts))}</p>'
        reason = label(catalog, "edition_reason", self.status.get("edition_reason"), fallback=state)
        cards += f'</article><article class="status-card"><span class="eyebrow">{esc(strings["status_page"]["checked"].format(date=checked))}</span><strong>{esc(label(catalog,"source_mode","MAIN",fallback="FCMO AI"))}</strong><p>{esc(reason)}</p></article>'
        body = status_page(strings["status_page"]["title"], cards, "")
        self._write_page(locale=locale, suffix="status/", title=f'{strings["status_page"]["title"]} — FCMO AI', description=strings["edition"]["delayed"].format(date=last), body=body, kind="status")

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
        pages = [
            ("about/", s["nav"]["about"], f'<p>{esc(s["site"]["description"])}</p><p>{esc(s["footer"]["automated_notice"])}</p>', "about"),
            ("method/", s["nav"]["method"], f'<p>{esc(s["footer"]["automated_notice"])}</p><p>{esc(s["story"]["evidence"])} · {esc(s["story"]["limitations"])} · {esc(s["story"]["unknowns"])}</p>', "method"),
            ("feeds/", s["feeds"]["title"], f'<p>{esc(s["feeds"]["intro"])}</p><ul>{feed_links}</ul>', "feeds"),
            ("agenda/", s["nav"]["agenda"], f'<p>{esc(s["archive"]["empty"])}</p><p><a href="{esc(href(self.base,locale["path_prefix"]+"agenda.ics"))}">iCalendar</a></p>', "agenda"),
            ("autores/mesa-fcmo-ai/", s["story"]["byline"].split("·")[0].strip(), f'<p>{esc(s["story"]["byline"])}</p><p>{esc(s["footer"]["automated_notice"])}</p>', "author"),
        ]
        corrections = [correction for story in self.stories for correction in story.get("corrections", [])]
        corr_body = f'<p>{esc(s["corrections_page"]["intro"])}</p>' + ("<ul>" + "".join(f'<li>{esc(c.get("note") or c.get("reason") or c.get("kind", ""))}</li>' for c in corrections) + "</ul>" if corrections else f'<p>{esc(s["corrections_page"]["none"])}</p>')
        pages.append(("corrections/", s["corrections_page"]["title"], corr_body, "corrections"))
        pending = {"en": "This document awaits the approved legal copy. Subscription remains inactive.", "es-419": "Este documento espera el texto legal aprobado. La suscripción permanece inactiva.", "zh-Hans": "本文件仍待核准的法律文本。订阅功能尚未启用。"}[locale["code"]]
        for suffix, title in (("privacy/",s["footer"]["privacy"]),("license/",s["footer"]["license"]),("disclaimer/",s["footer"]["disclaimer"])):
            pages.append((suffix, title, f'<p>{esc(pending)}</p>', "legal"))
        for suffix, title, content, kind in pages:
            self._write_page(locale=locale, suffix=suffix, title=f"{title} — FCMO AI", description=truncate(content.replace("<p>", " ").replace("</p>", " ")), body=simple_page(title, content), kind=kind)
        subscribe, subscribe_script = community.render_subscribe(locale_code=locale["code"], path_prefix=locale["path_prefix"], base=self.base, portal_url=self.portal_url, page=True)
        subscribe_title = community.subscribe_page_title(locale["code"], self.portal_url)
        self._write_page(locale=locale, suffix="suscribete/", title=f"{subscribe_title} — FCMO AI", description=community.COPY[locale["code"]]["promise"], body=f'<article class="story-body">{subscribe}</article>', kind="subscribe", extra_head=subscribe_script)

    def _404(self) -> None:
        blocks = []
        for locale in self.config["locales"]:
            strings = self.catalogs[locale["code"]]["strings"]["errors"]
            blocks.append(f'<section lang="{esc(locale["html_lang"])}"><h2>{esc(strings["not_found_title"])}</h2><p>{esc(strings["not_found_body"])}</p><a href="{esc(href(self.base,locale["path_prefix"]))}">{esc(strings["not_found_home"])}</a></section>')
        html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><link rel="icon" href="' + esc(href(self.base,"assets/pwa/favicon.svg")) + '" type="image/svg+xml"><link rel="apple-touch-icon" href="' + esc(href(self.base,"assets/pwa/icons/icon-192.svg")) + '"><link rel="stylesheet" href="' + esc(href(self.base,"assets/css/paper.css")) + '"><title>404 · FCMO AI</title></head><body><main class="page-shell not-found"><p class="brand">[^] FCMO AI</p>' + "".join(blocks) + '</main><script>(()=>{let p=location.pathname,s=p.includes("/es/")?"es-419":p.includes("/zh/")?"zh-Hans":"en";document.documentElement.lang=s;document.querySelector(`[lang="${s}"]`)?.scrollIntoView()})()</script></body></html>'
        (self.out / "404.html").write_text(html, encoding="utf-8")

    def build(self) -> int:
        resolved = self.out.resolve()
        if resolved in {Path("/").resolve(), ROOT.resolve(), Path.cwd().resolve()}:
            raise ValueError(f"refusing unsafe --out {resolved}")
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        shutil.copytree(ROOT / "site-src" / "assets", self.out / "assets", dirs_exist_ok=True)
        # Retain the original public agent datasets as compatibility surfaces.
        shutil.copytree(ROOT / "release-src" / "data", self.out / "data", dirs_exist_ok=True)
        self._copy_story_media()
        write_localized_story_graphics(self.stories, self.catalogs, self.out / "assets" / "story-media")
        if self.og_source is not None:
            if not self.og_source.is_dir():
                raise ValueError(f"--og-source is not a directory: {self.og_source}")
            shutil.copytree(self.og_source, self.out / "og")
        (self.out / "assets" / "js").mkdir(parents=True, exist_ok=True)
        (self.out / "assets" / "js" / "search.js").write_text(SEARCH_JS, encoding="utf-8")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {self.base_url.rstrip('/')}/sitemap.xml\n", encoding="utf-8")
        ranked = sorted(self.live, key=lambda s: (s.get("event_at", ""), s["id"]), reverse=True)
        topic_counts = Counter(topic for story in self.live for topic in story.get("topics", []))
        org_counts = Counter(org for story in self.live for org in story.get("organizations", []))
        for locale in self.config["locales"]:
            catalog = self.catalogs[locale["code"]]
            self._front(locale)
            for story in self.live:
                self._story(story, locale)
            self._listing(locale=locale, suffix="archive/", title=catalog["strings"]["archive"]["title"], stories=ranked, kind="archive")
            for date in sorted({s["url_date"] for s in self.live}, reverse=True):
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
            search_index.build(self.live, locale=locale, catalog=catalog, base=self.base, out=self.out / locale["path_prefix"] / "data" / "search.json")
        self._404()
        feed_paths = feeds.write_all(self.stories, locales=self.config["locales"], catalogs=self.catalogs, base_url=self.base_url, out=self.out)
        redirect_paths = redirects.build(self.stories, locales=self.config["locales"], base=self.base, out=self.out, legacy_root=ROOT / "site")
        sitemaps.write(self.routes, out=self.out, generated_at=self.payload["generated_at"])
        agent_layer.build(stories=self.live, all_stories=self.stories, locales=self.config["locales"],
                          catalogs=self.catalogs, status=self.status, base_url=self.base_url,
                          base=self.base, out=self.out, root=ROOT)
        (self.out / "data").mkdir(exist_ok=True)
        (self.out / "data" / "routes.json").write_text(json.dumps(self.routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(self.stories_path, self.out / "data" / "stories.v2.json")
        shutil.copyfile(self.status_path, self.out / "data" / "newsroom-status.json")
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
    parser.add_argument("--og-source", type=Path, help="cards produced by og_image.py; copied to publish/og")
    args = parser.parse_args(argv)
    try:
        PaperBuilder(stories_path=args.stories, status_path=args.status, out=args.out, base=args.base, og_source=args.og_source).build()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"paper build FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
