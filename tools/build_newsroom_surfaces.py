#!/usr/bin/env python3
"""Build the autonomous public Story layer and multilingual news surfaces.

Research dossiers remain the evidence archive. This layer turns the same
sanitized public evidence into newspaper-shaped Story objects and static,
indexable EN/ES/ZH pages without importing any private ARB reasoning.

Story publication time is distinct from research-event time. A dossier entering the
public Story layer for the first time is genuinely a newly published newspaper story;
quiet rebuilds preserve that publication timestamp, while a material canonical dossier
revision advances ``modified_at``. The underlying event/research verification times
remain explicit and are never rewritten to manufacture freshness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
import re
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

try:
    from tools import story_layer
except ImportError:  # executed as tools/build_newsroom_surfaces.py
    import story_layer  # type: ignore

BASE = "https://fcmo-ai.github.io/FCMO-AI-Newsletter"
NEWSROOM_STYLESHEET = "../../assets/newsroom.css"
LOCALES = {
    "en": {"slug": "en", "hreflang": "en", "name": "English"},
    "es-419": {"slug": "es", "hreflang": "es", "name": "Español"},
    "zh-Hans": {"slug": "zh-hans", "hreflang": "zh-Hans", "name": "简体中文"},
}
LABELS = {
    "en": {"latest":"Latest","what_changed":"What actually changed","evidence":"Claim vs. evidence","baseline":"Strongest baseline","caveat":"The caveat that matters","unknown":"What remains unknown","lens":"FCMO Lens","sources":"Primary sources","context":"Further public context","method":"Autonomously researched and edited from cited public evidence. English is the canonical semantic edition.","back":"FCMO AI Newsletter"},
    "es-419": {"latest":"Últimas","what_changed":"Qué cambió realmente","evidence":"Afirmación vs. evidencia","baseline":"Baseline más fuerte","caveat":"La salvedad que importa","unknown":"Qué sigue sin saberse","lens":"Lente FCMO","sources":"Fuentes primarias","context":"Contexto público adicional","method":"Investigado y editado de forma autónoma a partir de evidencia pública citada. El inglés es la edición semántica canónica.","back":"FCMO AI Newsletter"},
    "zh-Hans": {"latest":"最新","what_changed":"真正发生了什么变化","evidence":"主张与证据","baseline":"最强基线","caveat":"最重要的限制","unknown":"仍然未知的部分","lens":"FCMO 视角","sources":"主要来源","context":"更多公开背景","method":"基于所引公开证据进行自主研究与编辑。英语版是语义上的权威版本。","back":"FCMO AI Newsletter"},
}
CLAIM_LABELS = {
    "es-419": {"DEMONSTRATED":"DEMOSTRADO","CLAIMED":"AFIRMADO","INFERRED":"INFERIDO","SPECULATIVE":"ESPECULATIVO","DISPUTED":"DISPUTADO"},
    "zh-Hans": {"DEMONSTRATED":"已证实","CLAIMED":"声称","INFERRED":"推断","SPECULATIVE":"推测","DISPUTED":"有争议"},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_briefs(root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for path in sorted((root / "data" / "briefs").glob("FCMO-*.json")):
        obj = read_json(path)
        brief = obj.get("brief")
        if isinstance(brief, dict):
            result[brief["id"]] = brief
    return result


def load_locale_records(i18n_root: Path, locale: str) -> dict[str, dict[str, Any]]:
    if locale == "en":
        return {}
    result: dict[str, dict[str, Any]] = {}
    for path in sorted((i18n_root / locale).glob("part-*.json")):
        obj = read_json(path)
        rows = obj.get("records") or {}
        if not isinstance(rows, dict):
            raise SystemExit(f"{path}: locale records missing")
        result.update(rows)
    return result


def merge_overlay(source: Any, overlay: Any) -> Any:
    if isinstance(source, dict) and isinstance(overlay, dict):
        result = copy.deepcopy(source)
        for key, value in overlay.items():
            if key in result:
                result[key] = merge_overlay(result[key], value)
        return result
    if isinstance(source, list) and isinstance(overlay, list):
        result = copy.deepcopy(source)
        for index, value in enumerate(overlay[:len(result)]):
            result[index] = merge_overlay(result[index], value)
        return result
    return copy.deepcopy(overlay)


def parse_dt(value: str | None) -> datetime:
    text = str(value or "").replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def disposition(brief: dict[str, Any]) -> str:
    evidence = str(brief.get("evidence_class") or "")
    score = int(brief.get("importance_effective_score") or brief.get("importance_score") or 0)
    confidence = str(brief.get("confidence") or "")
    if evidence == "D" or confidence in {"weak_signal", "speculation"}:
        return "SIGNAL"
    if score >= 8:
        return "LEAD"
    if score >= 6:
        return "STANDARD"
    return "BRIEF"


def canonical_signature(brief: dict[str, Any]) -> str:
    # This intentionally excludes downstream research receipts/media. It changes only
    # when the publication-safe canonical dossier itself changes.
    return hashlib.sha256(json.dumps(brief, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def story_object(brief: dict[str, Any], research: dict[str, Any] | None, media: dict[str, Any] | None,
                 previous: dict[str, Any] | None, now: str, first_published: str | None = None) -> dict[str, Any]:
    signature = canonical_signature(brief)
    research_verified = str(brief.get("last_verified_at") or brief.get("recorded_at") or brief.get("event_at") or "")
    if previous:
        published = str(previous.get("published_at") or now)
        previous_sig = str(previous.get("canonical_signature") or "")
        # Migration compatibility: older Story objects had no signature and used
        # last_verified_at directly as modified_at. If that equals the current
        # research verification time, the dossier is unchanged and must not be re-dated.
        unchanged = previous_sig == signature or (
            not previous_sig and str(previous.get("modified_at") or "") == research_verified
        )
        modified = str(previous.get("modified_at") or published) if unchanged else now
    else:
        published = modified = now
    if first_published:
        # The first-publication ledger is the only source of publication time: a
        # story that left the previous stories.json and came back keeps its date.
        published = first_published
        if parse_dt(modified) < parse_dt(published):
            modified = published
    return {
        "story_id": f"STORY-{brief['id'][5:]}",
        "research_id": brief["id"],
        "headline": brief.get("title"),
        "dek": brief.get("summary"),
        "story_type": disposition(brief),
        "published_at": published,
        "modified_at": modified,
        "event_at": brief.get("event_at"),
        "research_verified_at": research_verified,
        "canonical_signature": signature,
        "news_value": {"importance": brief.get("importance_effective_score") or brief.get("importance_score"), "evidence": brief.get("evidence_class"), "confidence": brief.get("confidence")},
        "what_changed": brief.get("summary"),
        "why_it_matters": brief.get("why_it_matters"),
        "claims": brief.get("claims") or [],
        "technical": brief.get("technical") or {},
        "limitations": brief.get("limitations") or [],
        "contradictory_evidence": brief.get("contradictory_evidence") or [],
        "evidence_gaps": brief.get("evidence_gaps") or [],
        "sources": brief.get("source_urls") or [],
        "public_research": research or {},
        "media": media or {},
    }


def safe(value: Any) -> str:
    return html.escape(str(value or ""))


def list_html(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{safe(x)}</li>" for x in items if x) + "</ul>" if items else "<p>—</p>"


def source_links(urls: list[str]) -> str:
    rows = [f'<li><a href="{safe(url)}" rel="noopener noreferrer">{safe(url)}</a></li>' for url in urls if str(url).startswith(("http://", "https://"))]
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p>—</p>"


def citation_record(brief: dict[str, Any], canonical_story_url: str) -> tuple[str, dict[str, Any]]:
    """Create an immutable citation snapshot addressed by its payload digest."""
    sources = [url for url in brief.get("source_urls") or []
               if isinstance(url, str) and url.startswith(("https://", "http://"))]
    payload = {
        "schema": "fcmo-versioned-citation-v1",
        "id": brief["id"],
        "canonical_story_url": canonical_story_url,
        "headline": str(brief.get("title") or ""),
        "summary": str(brief.get("summary") or ""),
        "source_urls": sources,
    }
    version = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    citation_url = f"{BASE}/data/citations/{brief['id']}/{version}.json"
    return citation_url, {**payload, "version": version}


def article_html(locale: str, brief: dict[str, Any], story: dict[str, Any], all_links: dict[str, str], citation_url: str | None = None) -> str:
    label = LABELS[locale]
    media = story.get("media") or {}
    image = media.get("image_url")
    if isinstance(image, str) and image.startswith("/"):
        image = BASE + image.removeprefix("/FCMO-AI-Newsletter")
    elif isinstance(image, str) and not image.startswith("http"):
        image = f"{BASE}/{image.lstrip('/')}"
    claims = []
    claim_map = CLAIM_LABELS.get(locale, {})
    for claim in brief.get("claims") or []:
        if isinstance(claim, dict):
            claims.append(f"<li><strong>{safe(claim_map.get(str(claim.get('label')), str(claim.get('label') or '')))}</strong> — {safe(claim.get('text'))}</li>")
    technical = brief.get("technical") or {}
    caveats = list(brief.get("limitations") or []) + list(brief.get("contradictory_evidence") or [])
    gaps = [str(x.get("description") or "") for x in brief.get("evidence_gaps") or [] if isinstance(x, dict)]
    research = story.get("public_research") or {}
    context_urls = [str(x.get("url") or "") for x in research.get("related_public_sources") or [] if isinstance(x, dict) and x.get("url")]
    url = all_links[locale]
    sources = [source for source in brief.get("source_urls") or [] if isinstance(source, str) and source.startswith(("https://", "http://"))]
    citation_url = citation_url or citation_record(brief, all_links["en"])[0]
    ld = {"@context":"https://schema.org","@type":"NewsArticle","identifier":brief.get("id"),"headline":brief.get("title"),"description":brief.get("summary"),"datePublished":story.get("published_at"),"dateModified":story.get("modified_at"),"inLanguage":locale,"mainEntityOfPage":url,"citation":citation_url,"isBasedOn":sources,"author":{"@type":"Organization","name":"FCMO AI Research Desk"},"publisher":{"@type":"Organization","name":"FCMO AI Newsletter","url":BASE+"/"}}
    if image: ld["image"] = [image]
    alternates = "\n".join(f'<link rel="alternate" hreflang="{LOCALES[key]["hreflang"]}" href="{safe(href)}">' for key, href in all_links.items()) + f'\n<link rel="alternate" hreflang="x-default" href="{safe(all_links["en"])}">'
    return f'''<!doctype html><html lang="{safe(locale)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe(brief.get("title"))} · FCMO AI Newsletter</title><meta name="description" content="{safe(brief.get("summary"))}"><link rel="canonical" href="{safe(url)}">{alternates}<link rel="stylesheet" href="{NEWSROOM_STYLESHEET}"><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace('</','<\\/')}</script></head><body><header class="wire-head"><a href="{BASE}/">{safe(label["back"])}</a><span>FCMO WIRE</span></header><main class="story"><div class="kicker">{safe(story["story_type"])} · {safe(brief.get("primary_desk","research")).replace("_"," ")}</div><h1>{safe(brief.get("title"))}</h1><p class="dek">{safe(brief.get("summary"))}</p><p class="byline">FCMO AI Research Desk · Published {safe(story.get("published_at"))} · Research event {safe(story.get("event_at"))}</p><p class="method">{safe(label["method"])}</p>{f'<figure><img src="{safe(image)}" alt="{safe(brief.get("title"))}"><figcaption>{safe(media.get("credit"))} · {safe(media.get("license"))}</figcaption></figure>' if image else ''}<section><h2>{safe(label["what_changed"])}</h2><p>{safe(brief.get("summary"))}</p></section><section><h2>{safe(label["evidence"])}</h2><ul>{''.join(claims)}</ul></section><section><h2>{safe(label["baseline"])}</h2><p>{safe(technical.get("strongest_baseline"))}</p></section><section><h2>{safe(label["caveat"])}</h2>{list_html([str(x) for x in caveats])}</section><section><h2>{safe(label["unknown"])}</h2>{list_html(gaps)}</section><section><h2>{safe(label["lens"])}</h2><p>{safe(brief.get("why_it_matters"))}</p></section><section><h2>{safe(label["sources"])}</h2>{source_links([str(x) for x in brief.get("source_urls") or []])}</section><section><h2>{safe(label["context"])}</h2>{source_links(context_urls)}</section></main></body></html>'''


def index_html(locale: str, stories: list[tuple[dict[str, Any], str]]) -> str:
    label=LABELS[locale]
    cards="".join(f'<article><div class="kicker">{safe(story["story_type"])}</div><h2><a href="{safe(href)}">{safe(story["headline"])}</a></h2><p>{safe(story["dek"])}</p><small>Published {safe(story["published_at"])}</small></article>' for story,href in stories)
    return f'<!doctype html><html lang="{safe(locale)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FCMO WIRE · {safe(label["latest"])}</title><link rel="stylesheet" href="{NEWSROOM_STYLESHEET}"></head><body><header class="wire-head"><a href="{BASE}/">FCMO AI Newsletter</a><span>FCMO WIRE</span></header><main class="story"><h1>{safe(label["latest"])}</h1><p class="method">{safe(label["method"])}</p><div class="cards">{cards}</div></main></body></html>'


def write_css(site: Path) -> None:
    css="""*{box-sizing:border-box}body{margin:0;background:#0b0b0c;color:#f5f5f3;font-family:Inter,Arial,sans-serif}.wire-head{display:flex;justify-content:space-between;padding:22px 5vw;border-bottom:1px solid #333;letter-spacing:.12em}.wire-head a{color:#fff;text-decoration:none}.wire-head span,.kicker{color:#fd5204}.story{max-width:980px;margin:0 auto;padding:64px 28px 100px}.story h1{font-size:clamp(2.7rem,7vw,5.9rem);line-height:.94;margin:.3em 0}.story h2{font-size:1.5rem;margin-top:2.7em}.dek{font-size:1.35rem;line-height:1.55;color:#d1d1d4}.byline,.method,small{color:#9e9ea3}.method{border-left:3px solid #fd5204;padding-left:16px}.story p,.story li{line-height:1.65}.story a{color:#ff7b42}.story figure{margin:42px 0}.story img{width:100%;max-height:560px;object-fit:cover;background:#151517}.story figcaption{font-size:.85rem;color:#999}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}.cards article{padding:22px;border:1px solid #333}.cards h2{margin:.35em 0}.cards a{color:#fff;text-decoration:none}"""
    (site/"assets").mkdir(parents=True,exist_ok=True); (site/"assets"/"newsroom.css").write_text(css,encoding="utf-8")


def inject_wire_link(root: Path) -> None:
    for path in root.glob("*.html"):
        text=path.read_text(encoding="utf-8")
        link=f'<a data-fcmo-wire-link="true" href="{BASE}/news/">FCMO WIRE</a>'
        if "data-fcmo-wire-link" not in text and "</body>" in text: text=text.replace("</body>",f'<div style="position:fixed;right:18px;bottom:18px">{link}</div></body>',1)
        path.write_text(text,encoding="utf-8")


def news_sitemap(site: Path,pages:list[dict[str,Any]]) -> None:
    register_namespace("","http://www.sitemaps.org/schemas/sitemap/0.9"); register_namespace("news","http://www.google.com/schemas/sitemap-news/0.9")
    root=Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"); cutoff=datetime.now(timezone.utc)-timedelta(days=2)
    for page in pages:
        if parse_dt(page["published_at"])<cutoff and parse_dt(page["modified_at"])<cutoff: continue
        node=SubElement(root,"{http://www.sitemaps.org/schemas/sitemap/0.9}url"); SubElement(node,"{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text=page["url"]
        news=SubElement(node,"{http://www.google.com/schemas/sitemap-news/0.9}news"); pub=SubElement(news,"{http://www.google.com/schemas/sitemap-news/0.9}publication")
        SubElement(pub,"{http://www.google.com/schemas/sitemap-news/0.9}name").text="FCMO AI Newsletter"; SubElement(pub,"{http://www.google.com/schemas/sitemap-news/0.9}language").text=page["language"]; SubElement(news,"{http://www.google.com/schemas/sitemap-news/0.9}publication_date").text=page["published_at"]; SubElement(news,"{http://www.google.com/schemas/sitemap-news/0.9}title").text=page["headline"]
    ElementTree(root).write(site/"news-sitemap.xml",encoding="utf-8",xml_declaration=True)


def standard_sitemap(site:Path,pages:list[dict[str,Any]]) -> None:
    register_namespace("","http://www.sitemaps.org/schemas/sitemap/0.9"); root=Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
    entries=[(BASE+"/",None)]+[(f"{BASE}/news/{m['slug']}/",None) for m in LOCALES.values()]+[(p["url"],p.get("modified_at")) for p in pages]; seen=set()
    for url,modified in entries:
        if url in seen: continue
        seen.add(url); node=SubElement(root,"{http://www.sitemaps.org/schemas/sitemap/0.9}url"); SubElement(node,"{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text=url
        if modified: SubElement(node,"{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod").text=str(modified)[:10]
    ElementTree(root).write(site/"sitemap.xml",encoding="utf-8",xml_declaration=True)


NOTICE_LABELS = {
    "en": {"withdrawn": "This story was withdrawn", "merged": "This story was merged into another report",
           "original": "Original headline", "current": "Read the current story", "correction": "Correction",
           "ledger": "Corrections ledger"},
    "es-419": {"withdrawn": "Esta historia fue retirada", "merged": "Esta historia se integró en otra nota",
               "original": "Titular original", "current": "Leer la historia vigente", "correction": "Corrección",
               "ledger": "Registro de correcciones"},
    "zh-Hans": {"withdrawn": "本文已撤回", "merged": "本文已并入另一篇报道", "original": "原标题",
                "current": "阅读现行报道", "correction": "更正", "ledger": "更正记录"},
}


def build_story_layer(corpus: Path, site: Path, repo: Path | None, now: str) -> dict[str, Any] | None:
    """stories.v2 for the corpus, or None when it cannot be built (legacy pages still ship)."""
    if not (corpus / "data" / "developments.jsonl").is_file():
        return None
    try:
        inputs = story_layer.StoryInputs(corpus, repo, site, site / "data" / "i18n", now)
        return story_layer.build_stories(inputs)
    except Exception as exc:  # the v2 layer is additive in Paso 1; never take the news down
        print(f"ALERT STORY_LAYER_FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def notice_html(locale: str, story: dict[str, Any], links: dict[str, str], survivor: str | None) -> str:
    """Public notice that replaces the page of a withdrawn or merged story."""
    label = NOTICE_LABELS[locale]
    fix = story["corrections"][-1] if story["corrections"] else {"text": {}, "at": story["updated_at"]}
    text = fix["text"].get(locale)
    text_lang = locale if text else "en"
    text = text or fix["text"].get("en", "")
    heading = label["merged"] if story["status"] == "merged" else label["withdrawn"]
    canonical = survivor or links[locale]
    alternates = "".join(f'<link rel="alternate" hreflang="{safe(LOCALES[k]["hreflang"])}" href="{safe(v)}">' for k, v in links.items())
    current = f'<p><a href="{safe(survivor)}">{safe(label["current"])}</a></p>' if survivor else ""
    return (f'<!doctype html><html lang="{safe(locale)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{safe(heading)} · FCMO AI Newsletter</title><meta name="robots" content="noindex,follow"><link rel="canonical" href="{safe(canonical)}">{alternates}'
            f'<link rel="stylesheet" href="{NEWSROOM_STYLESHEET}"></head><body><header class="wire-head"><a href="{BASE}/">{safe(LABELS[locale]["back"])}</a><span>FCMO WIRE</span></header>'
            f'<main class="story" data-fcmo-story-status="{safe(story["status"])}"><div class="kicker">{safe(label["correction"])} · <time datetime="{safe(fix["at"])}">{safe(fix["at"][:10])}</time></div>'
            f'<h1>{safe(heading)}</h1><p class="dek" lang="{safe(text_lang)}">{safe(text)}</p>{current}'
            + (f'<p class="byline">{safe(label["original"])}: <span lang="en">{safe(story["title"])}</span></p>' if story["title"] else "")
            + f'<p class="method"><a href="{BASE}/corrections.html">{safe(label["ledger"])}</a></p></main></body></html>')


def corrections_ledger(document: dict[str, Any]) -> list[dict[str, Any]]:
    """site/data/corrections.json rows (read by build_editorial_frontends.py), newest first."""
    rows = []
    kinds = {"withdrawal": "Withdrawn", "merge": "Merged", "reinstatement": "Reinstated", "correction": "Corrected", "update": "Updated"}
    for story in document["stories"]:
        for fix in story["corrections"]:
            rows.append({
                "date": fix["at"][:10],
                "modified_at": fix["at"],
                "story_id": story["id"],
                "kind": fix["kind"],
                "reason_code": fix["reason_code"],
                "title": f'{kinds.get(fix["kind"], "Corrected")}: {story["title"] or story["id"]}',
                "story_title": story["title"],
                "summary": fix["text"].get("en", ""),
                "text": fix["text"],
                "merged_into": story.get("merged_into"),
                "url": f"{BASE}/news/en/{story['id']}.html",
            })
    return sorted(rows, key=lambda r: (r["modified_at"], r["story_id"]), reverse=True)


def _original_title(site: Path, rid: str, previous: list[Any]) -> str:
    """Last known headline of an id: corrections ledger, else its English article page."""
    for row in previous:
        if isinstance(row, dict) and row.get("story_id") == rid and isinstance(row.get("story_title"), str):
            return row["story_title"]
    page = site / "news" / "en" / f"{rid}.html"
    text = page.read_text(encoding="utf-8", errors="replace") if page.is_file() else ""
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
    if match and "data-fcmo-story-status" not in text:
        return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
    return ""


def tombstone_stories(corpus: Path, site: Path, document: dict[str, Any]) -> list[dict[str, Any]]:
    """Notice-only stories for active tombstones the v2 layer could not rebuild (no record,
    no git history, no previous stories.v2): the withdrawal still reaches readers."""
    known = {s["id"] for s in document["stories"]}
    ledger = story_layer.load_ledger(corpus)["entries"]
    active, _ = story_layer.tombstone_index(story_layer.load_tombstones(corpus))
    previous = read_json(site / "data" / "corrections.json") if (site / "data" / "corrections.json").is_file() else []
    out = []
    for rid, tomb in sorted(active.items()):
        published = rid in ledger or any((site / "news" / m["slug"] / f"{rid}.html").is_file() for m in LOCALES.values())
        if rid in known or not published:
            continue
        merged = tomb.get("action") == "superseded" and tomb.get("superseded_by") in known
        fix = story_layer.correction(tomb["withdrawn_at"], "merge" if merged else "withdrawal", tomb["reason_code"], tomb["correction"])
        story = {"id": rid, "status": "merged" if merged else "withdrawn", "title": _original_title(site, rid, previous if isinstance(previous, list) else []),
                 "corrections": [fix], "updated_at": fix["at"]}
        if merged:
            story["merged_into"] = tomb["superseded_by"]
        out.append(story)
    return out


def write_story_layer_outputs(site: Path, document: dict[str, Any], corpus: Path | None = None) -> int:
    """stories.v2.json, corrections.json and the notice pages of withdrawn and merged ids."""
    try:
        extra = tombstone_stories(corpus, site, document) if corpus is not None else []
    except Exception as exc:  # additive in Paso 1: notices from the v2 document still ship
        print(f"ALERT TOMBSTONE_NOTICES_FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
        extra = []
    (site / "data").mkdir(parents=True, exist_ok=True)
    story_layer.write_json_atomic(site / "data" / "stories.v2.json", document)
    story_layer.write_json_atomic(site / "data" / "corrections.json",
                                  corrections_ledger({"stories": document["stories"] + extra}))
    notices = 0
    for story in document["stories"] + extra:
        if story["status"] == "live":
            continue
        rid = story["id"]
        # The release gates allow no developments/ dossier outside the published index
        # (apply_final_release.py, verify_release.py, release-validate.yml).
        (site / "developments" / f"{rid}.html").unlink(missing_ok=True)
        links = {key: f"{BASE}/news/{value['slug']}/{rid}.html" for key, value in LOCALES.items()}
        for locale, meta in LOCALES.items():
            target = story.get("merged_into")
            survivor = f"{BASE}/news/{meta['slug']}/{target}.html" if target else None
            folder = site / "news" / meta["slug"]
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"{rid}.html").write_text(notice_html(locale, story, links, survivor), encoding="utf-8")
            notices += 1
    return notices


def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--release-src",type=Path,default=Path("release-src")); parser.add_argument("--site",type=Path,default=Path("site"))
    parser.add_argument("--corpus",type=Path,help="corpus for the v2 story layer (default: <release-src>/../corpus)"); parser.add_argument("--now",help="ISO 8601 clock override (else FCMO_NOW, else the real clock)"); args=parser.parse_args(argv)
    briefs=load_briefs(args.release_src); media_rows=read_json(args.release_src/"data"/"media.json"); media={r.get("id"):r for r in media_rows if isinstance(r,dict)}
    research_dir=args.release_src/"data"/"public-research"; research={p.stem:read_json(p) for p in research_dir.glob("FCMO-*.json")} if research_dir.exists() else {}
    overlays={locale:load_locale_records(args.site/"data"/"i18n",locale) for locale in LOCALES}
    previous_rows=[]
    previous_path=args.site/"data"/"stories.json"
    if previous_path.is_file():
        try: previous_rows=read_json(previous_path)
        except Exception: previous_rows=[]
    previous={str(r.get("research_id") or ""):r for r in previous_rows if isinstance(r,dict)} if isinstance(previous_rows,list) else {}
    now=story_layer.resolve_now(args.now) if (args.now or os.environ.get("FCMO_NOW")) else datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    repo=args.release_src.resolve().parent; corpus=args.corpus if args.corpus is not None else repo/"corpus"
    v2=build_story_layer(corpus,args.site,repo if (repo/".git").exists() else None,story_layer.resolve_now(args.now))
    first_published={s["id"]:s["first_published_at"] for s in v2["stories"]} if v2 else {}
    stories={rid:story_object(brief,research.get(rid),media.get(rid),previous.get(rid),now,first_published.get(rid)) for rid,brief in briefs.items()}
    ordered_ids=sorted(stories,key=lambda rid:(parse_dt(stories[rid]["modified_at"]),parse_dt(stories[rid]["published_at"]),int(stories[rid]["news_value"]["importance"] or 0),rid),reverse=True)
    (args.site/"data").mkdir(parents=True,exist_ok=True); (args.site/"data"/"stories.json").write_text(json.dumps([stories[r] for r in ordered_ids],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_css(args.site); inject_wire_link(args.release_src); pages=[]
    citations: dict[str, tuple[str, dict[str, Any]]] = {
        rid: citation_record(brief, f"{BASE}/news/en/{rid}.html") for rid, brief in briefs.items()
    }
    for citation_url, citation in citations.values():
        target = args.site / "data" / "citations" / citation["id"] / f"{citation['version']}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(citation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for locale,meta in LOCALES.items():
        folder=args.site/"news"/meta["slug"]; folder.mkdir(parents=True,exist_ok=True); localized_cards=[]
        for rid in ordered_ids:
            brief=merge_overlay(briefs[rid],overlays[locale].get(rid,{})); story=copy.deepcopy(stories[rid]); story["headline"]=brief.get("title"); story["dek"]=brief.get("summary")
            links={key:f"{BASE}/news/{value['slug']}/{rid}.html" for key,value in LOCALES.items()}; url=links[locale]; (folder/f"{rid}.html").write_text(article_html(locale,brief,story,links,citations[rid][0]),encoding="utf-8"); localized_cards.append((story,url)); pages.append({"url":url,"language":meta["hreflang"],"headline":str(brief.get("title") or ""),"published_at":str(story.get("published_at") or ""),"modified_at":str(story.get("modified_at") or "")})
        (folder/"index.html").write_text(index_html(locale,localized_cards),encoding="utf-8")
    (args.site/"news").mkdir(exist_ok=True); (args.site/"news"/"index.html").write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=en/"><script>location.replace("en/"+location.search+location.hash)</script>',encoding="utf-8")
    notices=write_story_layer_outputs(args.site,v2,corpus) if v2 else 0
    news_sitemap(args.site,pages); standard_sitemap(args.site,pages); print(f"newsroom surfaces OK; stories={len(stories)}; localized_pages={len(pages)}; newly_published={sum(1 for rid in stories if rid not in previous)}; notices={notices}; story_layer={'v2' if v2 else 'unavailable'}"); return 0


if __name__=="__main__": raise SystemExit(main())
