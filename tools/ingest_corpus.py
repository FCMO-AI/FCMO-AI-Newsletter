#!/usr/bin/env python3
"""Regenerate the static FCMO AI Newsletter release from a corpus export."""
from __future__ import annotations

import argparse
import copy
import html
import json
import os
import re
import shutil
import sys
import tempfile
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


BASE_URL = "https://fcmo-ai.github.io/FCMO-AI-Newsletter/"
PUBLIC_ID = re.compile(r"FCMO-[0-9A-F]{12}")
DATA_SCRIPT = re.compile(
    r'(<script id="fcmo-data" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)
LLMS_SCAFFOLD = """# FCMO AI Newsletter

Evidence-first public AI research intelligence.

Canonical base: https://fcmo-ai.github.io/FCMO-AI-Newsletter/
Agent discovery: https://fcmo-ai.github.io/FCMO-AI-Newsletter/agent.json
Query contract: fcmo-agent-query-v2
Stable IDs: FCMO-<12 uppercase hex>

## Machine datasets
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/search.json — full-text corpus + publication-memory index
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/developments.json — canonical research index
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/briefs/<FCMO-ID>.json — full dossier, claims, technical regime, implications, limitations, gaps, sources, related work
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/relationships.json — explicit cross-brief relationship graph
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/publication-memory.json — published editions and research snapshots
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/editions/<YYYY-MM-DD>.json — frozen publication object for one date
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/topics.json — topic facets and brief IDs
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/organizations.json — organization facets and brief IDs
- https://fcmo-ai.github.io/FCMO-AI-Newsletter/data/media.json — story-image provenance and fallback state

## Query semantics
Search may be filtered by desk, evidence class, minimum impact, topic, organization, confidence and scope. Claims, confidence and importance are separate fields. Open evidence gaps, contradictory evidence and limitations must not be collapsed into headline confidence.

The human site exposes the equivalent browser-local API as window.FCMOAgent.query(spec).
"""


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def jsonl_bytes(values: list[Any]) -> bytes:
    return "".join(json.dumps(value, ensure_ascii=False) + "\n" for value in values).encode(
        "utf-8"
    )


def replace_arb(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("ARB", "FCMO AI")
    if isinstance(value, list):
        return [replace_arb(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_arb(item) for key, item in value.items()}
    return value


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def desk_name(desk: str) -> str:
    return desk.replace("_", " ").title()


def public_type(development_type: str) -> str:
    """Map ARB development classes to the site's single research collection."""
    if not development_type:
        raise ValueError("development has no development_type")
    return "research"


def public_record(brief: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": brief["id"],
        "title": brief["title"],
        "desk": desk_name(brief["primary_desk"]),
        "event_at": brief["event_at"],
        "evidence": brief["evidence_class"],
        "confidence": brief["confidence"],
        "importance": brief["importance_effective_score"],
        "tier": brief["importance_tier"],
        "summary": brief["summary"],
        "topics": brief["topics"],
        "organizations": brief["organizations"],
        "human_url": f"{BASE_URL}developments/{brief['id']}.html",
        "machine_url": f"{BASE_URL}data/briefs/{brief['id']}.json",
        "citation": {
            "id": brief["id"],
            "source": f"{BASE_URL}developments/{brief['id']}.html",
        },
    }


def fallback_media(identifier: str) -> dict[str, Any]:
    """Return the site-wide editorial image policy for an unsourced brief."""
    return {
        "id": identifier,
        "mode": "fcmo_fallback",
        "fallback": "fcmo-signal-portrait",
        "sourced": False,
        "reason": (
            "No first-party story image surfaced that was stronger than the "
            "FCMO editorial fallback."
        ),
    }


def additions_since_base(index: str, identifiers: list[str]) -> list[str]:
    """Find corpus records not yet represented by the release scaffold."""
    match = DATA_SCRIPT.search(index)
    if not match:
        raise ValueError("release-src/index.html has no fcmo-data script")
    try:
        existing = json.loads(match.group(2))
        existing_ids = {record["id"] for record in existing["records"]}
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("release-src/index.html has invalid fcmo-data records") from exc
    return [identifier for identifier in identifiers if identifier not in existing_ids]


def llms_index(records: list[dict[str, Any]]) -> str:
    """Render the corpus-derived index to the otherwise hand-authored guide."""
    lines = ["", "## Briefs"]
    for record in records:
        identifier = record["id"]
        lines.append(
            f"- {identifier} — {record['title']} "
            f"({record['machine_url']})"
        )
    return "\n".join(lines) + "\n"


class EditionParser(HTMLParser):
    """Extract the publication blocks from one corpus edition document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.story_depth = 0
        self.in_story = False
        self.capture: list[dict[str, Any]] = []
        self.list_stack: list[dict[str, Any]] = []
        self.events: list[tuple[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = dict(attrs)
        for item in self.capture:
            item["parts"].append(" ")
        if tag == "article" and "story" in (attributes.get("class") or "").split():
            if not self.in_story:
                self.in_story = True
                self.story_depth = 1
            else:
                self.story_depth += 1
            return
        if not self.in_story:
            return
        if tag in {"article", "section"}:
            self.story_depth += 1
        if tag in {"ul", "ol"}:
            self.list_stack.append({"items": []})
            return
        if tag == "li":
            if self.list_stack:
                self.capture.append({"tag": "li", "parts": [], "list": self.list_stack[-1]})
            return
        if tag == "blockquote":
            self.capture.append({"tag": tag, "parts": []})
            return
        if tag in {"p", "h1", "h2", "h3", "h4"}:
            if not any(item["tag"] == "blockquote" for item in self.capture):
                self.capture.append({"tag": tag, "parts": []})
            return
        if tag == "div" and "notice" in (attributes.get("class") or "").split():
            self.capture.append({"tag": "notice", "parts": []})

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        target_index = next(
            (
                index
                for index in range(len(self.capture) - 1, -1, -1)
                if (tag == "div" and self.capture[index]["tag"] == "notice")
                or self.capture[index]["tag"] == tag
            ),
            None,
        )
        for index, item in enumerate(self.capture):
            if target_index is None or index != target_index:
                item["parts"].append(" ")
        if tag in {"p", "h1", "h2", "h3", "h4", "blockquote", "li", "div"}:
            for index in range(len(self.capture) - 1, -1, -1):
                item = self.capture[index]
                if (tag == "div" and item["tag"] == "notice") or item["tag"] == tag:
                    self.capture.pop(index)
                    text = re.sub(r"\s+", " ", unescape("".join(item["parts"]))).strip()
                    if item["tag"] == "li":
                        item["list"]["items"].append(text)
                    elif item["tag"] != "h1":
                        self.events.append((item["tag"], text))
                    break
        if tag in {"ul", "ol"} and self.list_stack:
            current = self.list_stack.pop()
            self.events.append(("list", current["items"]))
        if tag == "article" and self.in_story:
            self.story_depth -= 1
            if self.story_depth == 0:
                self.in_story = False

    def handle_data(self, data: str) -> None:
        for item in self.capture:
            item["parts"].append(data)


def parse_edition(path: Path, canonical_ids: set[str]) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    parser = EditionParser()
    story = re.search(r'<article class="story">(.*?)</article>', source, re.DOTALL | re.IGNORECASE)
    parser.feed(f'<article class="story">{story.group(1) if story else ""}</article>')
    date = path.stem
    published = "Published daily briefing" in source
    events = parser.events
    related: list[str] = []
    for match in PUBLIC_ID.finditer(source):
        if match.group() in canonical_ids and match.group() not in related:
            related.append(match.group())

    if published:
        preamble: list[dict[str, Any]] = []
        sections: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for tag, value in events:
            value = replace_arb(value)
            if tag == "h3":
                current = {"title": value, "blocks": []}
                sections.append(current)
            elif current is None:
                if tag == "p" and not preamble:
                    preamble.append({"type": "p", "text": value})
                elif tag == "notice":
                    preamble.append({"type": "div", "text": value})
                elif tag == "h2":
                    preamble.append({"type": "heading", "text": value})
                elif tag == "blockquote":
                    preamble.append({"type": "blockquote", "text": value})
            elif tag == "h4":
                current["blocks"].append({"type": "h4", "text": value})
            elif tag == "p":
                current["blocks"].append({"type": "p", "text": value})
            elif tag == "list":
                current["blocks"].append(
                    {"type": "list", "items": [replace_arb(item) for item in value]}
                )
    else:
        preamble = [
            {"type": "div", "text": replace_arb(value)}
            for tag, value in events
            if tag == "notice"
        ]
        sections = []

    return {
        "date": date,
        "authority": "published_edition" if published else "research_snapshot",
        "published": published,
        "preamble": preamble,
        "sections": sections,
        "related_brief_ids": related,
    }


def section_summary(section: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in section["blocks"]:
        if block["type"] == "list":
            parts.extend(block["items"])
        else:
            parts.append(block["text"])
    return " ".join(parts)


def publication_documents(edition: dict[str, Any]) -> list[dict[str, Any]]:
    if not edition["published"]:
        return []
    date = edition["date"]
    desk = f"Published edition · {date}"
    result: list[dict[str, Any]] = []
    for number, section in enumerate(edition["sections"], 1):
        result.append(
            {
                "id": f"PUB-{date}-{number:02d}",
                "type": "edition",
                "title": section["title"],
                "summary": section_summary(section),
                "desk": desk,
                "date": date,
            }
        )
    return result


def search_research(record: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(record)
    result["kind"] = "research"
    result["search_text"] = (
        f"{record['title']} {record['summary']} "
        f"{json.dumps(brief, ensure_ascii=False)}"
    )
    return result


def search_document(document: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": document["id"],
        "kind": document["type"],
        "title": document["title"],
        "date": document["date"],
        "desk": document["desk"],
        "summary": document["summary"],
        "human_url": f"{BASE_URL}editions/{document['date']}.html",
        "machine_url": f"{BASE_URL}data/editions/{document['date']}.json",
        "search_text": (
            f"{document['title']} {document['summary']} {document['desk']}"
        ),
    }
    return result


def related_for(
    identifier: str,
    relationships: list[dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relationship in relationships:
        if relationship["source_id"] == identifier:
            other_id = relationship["target_id"]
        elif relationship["target_id"] == identifier:
            other_id = relationship["source_id"]
        else:
            continue
        item = copy.deepcopy(relationship)
        item["other"] = copy.deepcopy(records[other_id])
        result.append(item)
    return result


def redirect(path_kind: str, identifier: str, title: str) -> str:
    route = "brief" if path_kind == "development" else "edition"
    path = f"../index.html#/{route}/{identifier}"
    page_title = (
        f"{title} · FCMO AI Newsletter"
        if path_kind == "development"
        else f"Edition {identifier} · FCMO AI Newsletter"
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta http-equiv="refresh" content="0;url={path}">'
        f'<link rel="canonical" href="{path}">'
        '<meta name="robots" content="index,follow">'
        f"<title>{html.escape(page_title, quote=False)}</title>"
        "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23f2eee6'/%3E%3Ctext x='32' y='47' text-anchor='middle' font-family='Arial,sans-serif' font-size='48' font-weight='900' fill='%23FD5204'%3E%5E%3C/text%3E%3C/svg%3E\">"
        f"</head><body><main><p>Opening the canonical FCMO AI Newsletter record… <a href=\"{path}\">Continue</a>.</p></main></body></html>"
    )


def feed_item(record: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "url": record["human_url"],
        "title": record["title"],
        "content_text": record["summary"],
        "date_published": record["event_at"],
        "date_modified": brief["last_verified_at"],
        "tags": list(record["topics"]),
        "_fcmo_evidence_class": record["evidence"],
        "_fcmo_confidence": record["confidence"],
        "_fcmo_importance": record["importance"],
    }


def feed_xml(items: list[dict[str, Any]]) -> str:
    def esc(value: str) -> str:
        return html.escape(str(value), quote=False)

    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>',
        "<title>FCMO AI Newsletter</title>",
        "<description>Evidence-first intelligence on the AI frontier.</description>",
        f"<link>{BASE_URL}</link>",
    ]
    for item in items:
        chunks.append(
            "<item>"
            f"<guid isPermaLink=\"false\">{esc(item['id'])}</guid>"
            f"<title>{esc(item['title'])}</title>"
            f"<description>{esc(item['content_text'])}</description>"
            f"<link>{esc(item['url'])}</link>"
            f"<category>evidence:{esc(item['_fcmo_evidence_class'])}</category>"
            f"<category>importance:{item['_fcmo_importance']}/10</category>"
            "</item>"
        )
    chunks.append("</channel></rss>")
    return "".join(chunks)


def sitemap(ids: list[str], edition_dates: list[str]) -> str:
    urls = [BASE_URL, f"{BASE_URL}about.html", f"{BASE_URL}archive.html", f"{BASE_URL}search.html", f"{BASE_URL}topics.html", f"{BASE_URL}organizations.html", f"{BASE_URL}feeds.html"]
    urls.extend(f"{BASE_URL}developments/{identifier}.html" for identifier in ids)
    urls.extend(f"{BASE_URL}editions/{date}.html" for date in edition_dates)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    lines.extend(f"  <url><loc>{url}</loc></url>" for url in urls)
    lines.extend(["</urlset>", ""])
    return "\n".join(lines)


def facets(records: list[dict[str, Any]], field: str, label: str) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for record in records:
        for value in record[field]:
            groups.setdefault(value, []).append(record["id"])
    return [
        {label: value, "count": len(ids), "brief_ids": ids}
        for value, ids in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0].casefold()))
    ]


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data.decode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def build(corpus: Path, out: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    source_records = read_jsonl(corpus / "data" / "developments.jsonl")
    source_by_id = {record["id"]: replace_arb(record) for record in source_records}
    if len(source_by_id) != len(source_records):
        raise ValueError("developments.jsonl has duplicate development IDs")
    canonical_ids = set(source_by_id)
    ids = [record["id"] for record in source_records]
    briefs = {identifier: source_by_id[identifier] for identifier in ids}
    records = [public_record(briefs[identifier]) for identifier in ids]
    records_by_id = dict(zip(ids, records))

    relationships = replace_arb(read_jsonl(corpus / "data" / "relationships.jsonl"))
    editions = [
        parse_edition(path, canonical_ids)
        for path in sorted((corpus / "editions").glob("*.html"))
    ]
    editions_by_date = {edition["date"]: edition for edition in editions}
    publication = sorted(editions, key=lambda edition: edition["date"], reverse=True)
    documents = [
        document
        for edition in editions
        for document in publication_documents(edition)
    ]
    search = [
        search_research(records_by_id[identifier], briefs[identifier])
        for identifier in ids
    ] + [search_document(document) for document in documents]

    release_index = (repo / "release-src" / "index.html").read_text(encoding="utf-8")
    additions = additions_since_base(release_index, ids)
    agent = read_json(repo / "release-src" / "agent.json")
    agent["newly_ingested_brief_ids"] = additions
    agent["counts"] = {
        "briefs": len(records),
        "topics": len(facets(records, "topics", "topic")),
        "organizations": len(facets(records, "organizations", "organization")),
        "relationships": len(relationships),
    }
    topic_rows = facets(records, "topics", "topic")
    organization_rows = facets(records, "organizations", "organization")
    published = next((edition for edition in editions if edition["published"]), None)
    meta = {
        "count": len(records),
        "evidenceA": sum(record["evidence"] == "A" for record in records),
        "evidenceB": sum(record["evidence"] == "B" for record in records),
        "open_gaps": sum(
            sum(gap.get("state") == "open" for gap in briefs[identifier]["evidence_gaps"])
            for identifier in ids
        ),
        "relationships": len(relationships),
        "topics": len(topic_rows),
        "organizations": len(organization_rows),
        "published_edition": published["date"] if published else None,
        "publication_documents": len(documents),
    }
    embedded_records = []
    for identifier in ids:
        item = copy.deepcopy(briefs[identifier])
        item.update(
            {
                "type": public_type(item["development_type"]),
                "why": item["why_it_matters"],
                "desk": desk_name(item["primary_desk"]),
                "evidence": item["evidence_class"],
                "importance": item["importance_effective_score"],
                "tier": item["importance_tier"],
                "verified": item["last_verified_at"],
            }
        )
        embedded_records.append(item)
    embedded_briefs = {identifier: briefs[identifier] for identifier in sorted(ids)}
    embedded_relationships = copy.deepcopy(relationships)
    embedded_publication = copy.deepcopy(publication)
    embedded_data = {
        "records": embedded_records,
        "briefs": embedded_briefs,
        "relationships": embedded_relationships,
        "publication_memory": embedded_publication,
        "documents": documents,
        "meta": meta,
    }

    media_reference = read_json(repo / "release-src" / "data" / "media.json")
    media_by_id = {item["id"]: item for item in media_reference}
    media = [
        copy.deepcopy(media_by_id[identifier])
        if identifier in media_by_id
        else fallback_media(identifier)
        for identifier in ids
    ]

    manifest = {
        "schema": "fcmo-ai-newsletter-site-manifest-v1",
        "agent": agent,
        "corpus": {
            "count": len(records),
            "evidenceA": meta["evidenceA"],
            "evidenceB": meta["evidenceB"],
            "open_gaps": meta["open_gaps"],
            "relationships": len(relationships),
            "topics": len(topic_rows),
            "organizations": len(organization_rows),
            "published_edition": meta["published_edition"],
            "publication_documents": len(documents),
        },
    }
    index = release_index
    match = DATA_SCRIPT.search(index)
    if not match:
        raise ValueError("release-src/index.html has no fcmo-data script")
    index = index[: match.start(2)] + json.dumps(
        embedded_data, separators=(",", ":"), ensure_ascii=False
    ) + index[match.end(2) :]

    dev_jsonl = jsonl_bytes(records)
    search_jsonl = jsonl_bytes(search)
    feed = [feed_item(records_by_id[identifier], briefs[identifier]) for identifier in ids]
    edition_dates = [edition["date"] for edition in sorted(editions, key=lambda x: x["date"])]
    output: dict[str, bytes] = {
        "index.html": index.encode("utf-8"),
        "data/developments.json": json_bytes(records),
        "data/developments.jsonl": dev_jsonl,
        "data/search.json": json_bytes(search),
        "data/search.jsonl": search_jsonl,
        "data/topics.json": json_bytes(topic_rows),
        "data/organizations.json": json_bytes(organization_rows),
        "data/media.json": json_bytes(media) + b"\n",
        "data/relationships.json": json_bytes(relationships),
        "data/publication-memory.json": json_bytes(publication),
        "data/site-manifest.json": json_bytes(manifest),
        "feed.json": json_bytes({
            "version": "https://jsonfeed.org/version/1.1",
            "title": "FCMO AI Newsletter",
            "home_page_url": BASE_URL,
            "feed_url": f"{BASE_URL}feed.json",
            "description": "Evidence-first intelligence on the AI frontier.",
            "items": feed,
        }),
        "feed.xml": feed_xml(feed).encode("utf-8"),
        "sitemap.xml": sitemap(sorted(ids), edition_dates).encode("utf-8"),
        "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n".encode("utf-8"),
        "agent.json": json_bytes(agent),
        "llms.txt": (LLMS_SCAFFOLD + llms_index(records)).encode("utf-8"),
        "llms-full.txt": (
            LLMS_SCAFFOLD
            + llms_index(records)
            + "\n## Full query contract\n```json\n"
            + json.dumps(agent, ensure_ascii=False, indent=2)
            + "\n```\n\n## Canonical brief summaries (JSONL)\n"
            + dev_jsonl.decode("utf-8")
        ).encode("utf-8"),
        ".nojekyll": b"",
    }
    for identifier in ids:
        output[f"data/briefs/{identifier}.json"] = json_bytes(
            {
                "record": records_by_id[identifier],
                "brief": briefs[identifier],
                "related": related_for(identifier, relationships, records_by_id),
                "schema": "fcmo-public-brief-v1",
            }
        )
        output[f"developments/{identifier}.html"] = redirect(
            "development", identifier, records_by_id[identifier]["title"]
        ).encode("utf-8")
    for edition in editions:
        date = edition["date"]
        edition_json = copy.deepcopy(edition)
        edition_json["human_url"] = f"{BASE_URL}editions/{date}.html"
        edition_json["machine_url"] = f"{BASE_URL}data/editions/{date}.json"
        output[f"data/editions/{date}.json"] = json_bytes(edition_json)
        output[f"editions/{date}.html"] = redirect("edition", date, date).encode("utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=f"{out.name}-", dir=out.parent))
    try:
        for relative, data in output.items():
            atomic_write(stage / relative, data)
        if out.exists():
            if not out.is_dir() or out.is_symlink():
                raise ValueError(f"output is not a regular directory: {out}")
            shutil.rmtree(out)
        os.replace(stage, out)
        stage = None
        atomic_write(
            out.parent / f".{out.name}.agent-run.json",
            json_bytes({"newly_ingested_brief_ids": additions}),
        )
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    corpus = args.corpus.resolve()
    out = args.out.resolve()
    if not corpus.is_dir():
        raise SystemExit(f"corpus does not exist or is not a directory: {corpus}")
    try:
        build(corpus, out)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"corpus ingestion failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
