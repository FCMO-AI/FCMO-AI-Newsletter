from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import shutil

from tools.paper.i18n import dek, field, headline
from tools.paper.routes import absolute, story_path


def _dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _localized(story: dict, locale: str, key: str, catalog: dict) -> str:
    return headline(story, locale, catalog) if key == "title" else dek(story, locale, catalog)


def _schema(name: str, properties: dict, required: list[str]) -> dict:
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"https://fcmo-ai.github.io/FCMO-AI-Newsletter/api/v1/schema/{name}.schema.json", "title": name, "type": "object", "required": required, "properties": properties, "additionalProperties": True}


def _schemas() -> dict[str, dict]:
    strp = {"type": "string"}
    arrstr = {"type": "array", "items": strp}
    provenance = {"type": "object", "required": ["release_id", "corpus_digest", "stories_sha256"], "properties": {"release_id": strp, "corpus_digest": strp, "stories_sha256": strp}}
    record = {"id": strp, "canonical_url": {"type": "string", "format": "uri"}, "language": strp, "event_date": strp, "published_at": strp, "updated_at": strp, "provenance": provenance}
    return {
        "index": _schema("index", {"schema": strp, "canonical_url": strp, "generated_at": strp, "stories": arrstr, "editions": arrstr, "topics": arrstr, "organizations": arrstr, "corrections": strp, "search_index": strp}, ["schema", "canonical_url", "generated_at", "stories", "editions", "topics", "organizations", "corrections", "search_index"]),
        "story": _schema("story", {**record, "title": strp, "dek": strp, "summary": strp, "why_it_matters": strp, "desk": strp, "kind": strp, "importance": {"type": "integer"}, "topics": arrstr, "organizations": arrstr, "confidence": strp, "evidence": strp, "evidence_details": {"type": "object"}, "technical": {"type": "object"}, "sources": {"type": "array"}, "corrections": {"type": "array"}}, ["id", "canonical_url", "language", "event_date", "published_at", "updated_at", "provenance", "title", "summary"]),
        "edition": _schema("edition", {**record, "stories": arrstr}, ["id", "canonical_url", "language", "event_date", "published_at", "updated_at", "provenance", "stories"]),
        "topic": _schema("topic", {**record, "slug": strp, "title": strp, "stories": arrstr}, ["id", "canonical_url", "language", "event_date", "published_at", "updated_at", "provenance", "slug", "title", "stories"]),
        "organization": _schema("organization", {**record, "slug": strp, "title": strp, "stories": arrstr}, ["id", "canonical_url", "language", "event_date", "published_at", "updated_at", "provenance", "slug", "title", "stories"]),
        "corrections": _schema("corrections", {"schema": strp, "canonical_url": strp, "language": strp, "generated_at": strp, "provenance": provenance, "items": {"type": "array"}}, ["schema", "canonical_url", "language", "generated_at", "provenance", "items"]),
        "search-index": _schema("search-index", {"schema": strp, "canonical_url": strp, "language": strp, "generated_at": strp, "provenance": provenance, "items": {"type": "array"}}, ["schema", "canonical_url", "language", "generated_at", "provenance", "items"]),
        "openapi": _schema("openapi", {"openapi": {"type": "string", "enum": ["3.1.0"]}, "info": {"type": "object"}, "servers": {"type": "array"}, "paths": {"type": "object"}}, ["openapi", "info", "servers", "paths"]),
    }


def _story_record(story: dict, catalogs: dict, base_url: str, status: dict) -> dict:
    catalog = catalogs["en"]
    route = story_path({"path_prefix": ""}, story)
    return {"id": story["id"], "canonical_url": absolute(base_url, route), "language": "en",
            "event_date": story["event_at"], "published_at": story["first_published_at"], "updated_at": story["updated_at"],
            "title": _localized(story, "en", "title", catalog), "dek": story.get("dek", ""), "summary": story.get("summary", ""), "why_it_matters": story.get("why_it_matters", ""),
            "desk": story.get("desk") or story.get("beat", ""), "kind": story.get("kind", ""), "importance": story.get("importance", 0), "topics": story.get("topics", []), "organizations": story.get("organizations", []),
            "confidence": story.get("confidence", ""), "evidence": story.get("evidence_class", ""),
            "evidence_details": story.get("evidence", {}), "technical": story.get("technical", {}), "sources": story.get("sources", []),
            "corrections": story.get("corrections", []), "provenance": {"release_id": status.get("release_id", ""), "corpus_digest": status.get("corpus_digest", ""), "stories_sha256": status.get("stories_sha256", "")}}


def _markdown_story(story: dict, locale: dict, catalog: dict, base_url: str, status: dict) -> str:
    title = headline(story, locale["code"], catalog)
    summary = dek(story, locale["code"], catalog)
    url = absolute(base_url, locale["path_prefix"] + story_path({"path_prefix": ""}, story))
    code = locale["code"]
    sections = [f"# {title}", "", summary, ""]
    for key, heading in (("summary", "What changed"), ("why_it_matters", "Why it matters")):
        value = field(story, code, key, "")
        if value: sections.extend([f"## {heading}", "", str(value), ""])
    evidence = story.get("evidence", {}) if code == "en" else field(story, code, "evidence", {})
    if isinstance(evidence, dict):
        claims = evidence.get("claims") or []
        if claims:
            sections.extend(["## Evidence claims", ""])
            sections.extend(f"- **{claim.get('label', 'Claim')}**: {claim.get('text', '')}" for claim in claims)
            sections.append("")
        for key, heading in (("limitations", "Limitations"), ("gaps", "Open questions"), ("contradictory", "Contradictory evidence")):
            values = evidence.get(key) or []
            if values:
                sections.extend([f"## {heading}", ""])
                sections.extend(f"- {item.get('description', '') if isinstance(item, dict) else item}" for item in values)
                sections.append("")
    technical = field(story, code, "technical", {})
    if isinstance(technical, dict) and technical:
        sections.extend(["## Technical details", ""])
        sections.extend(f"- **{key}**: {value}" for key, value in technical.items() if value)
        sections.append("")
    if story.get("corrections"):
        sections.extend(["## Corrections", ""])
        sections.extend(f"- {item.get('note') or item.get('reason') or item.get('kind', '')}" for item in story["corrections"])
        sections.append("")
    if story.get("sources"):
        sections.extend(["## Sources", ""])
        sections.extend(f"- [{source.get('domain') or source['url']}]({source['url']})" for source in story["sources"])
        sections.append("")
    sections.extend(["## Record", "", f"- Stable ID: `{story['id']}`", f"- Canonical URL: {url}", f"- Language: `{code}`", f"- Event date: {story['event_at']}", f"- Published: {story['first_published_at']}", f"- Updated: {story['updated_at']}", f"- Evidence: `{story.get('evidence_class', '')}`; confidence: `{story.get('confidence', '')}`", f"- Topics: {', '.join(story.get('topics', []))}", f"- Organizations: {', '.join(story.get('organizations', []))}", f"- Provenance receipt: `{status.get('release_id', '')}`; corpus digest `{status.get('corpus_digest', '')}`", ""])
    return "\n".join(sections)


def build(*, stories: list[dict], all_stories: list[dict], locales: list[dict], catalogs: dict,
          status: dict, base_url: str, base: str, out: Path, root: Path) -> None:
    api = out / "api/v1"
    old = json.loads((root / "scaffold/agent.json").read_text(encoding="utf-8"))
    # Keep the two original dossiers that the current canonical corpus has
    # retired, so the old public brief URLs remain available to existing agents.
    reference = root / "tools/agent/reference"
    reference_agent = json.loads((reference / "agent.json").read_text(encoding="utf-8"))
    for legacy_brief in (reference / "briefs").glob("FCMO-*.json"):
        target = out / "data/briefs" / legacy_brief.name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(legacy_brief, target)
    canonical = base_url
    records = {s["id"]: _story_record(s, catalogs, base_url, status) for s in stories}
    dates = sorted({s["url_date"] for s in stories}, reverse=True)
    topic_values = sorted({t for s in stories for t in s.get("topics", [])})
    org_values = sorted({o for s in stories for o in s.get("organizations", [])})
    records_by_date = {d: [s for s in stories if s["url_date"] == d] for d in dates}
    for sid, record in records.items():
        _dump(api / "stories" / f"{sid}.json", record)
    for day, values in records_by_date.items():
        _dump(api / "editions" / f"{day}.json", {"id": day, "canonical_url": absolute(base_url, f"edition/{day}/"), "language": "en", "event_date": day, "published_at": min(s["first_published_at"] for s in values), "updated_at": max(s["updated_at"] for s in values), "stories": [s["id"] for s in values], "provenance": {"release_id": status.get("release_id", ""), "corpus_digest": status.get("corpus_digest", ""), "stories_sha256": status.get("stories_sha256", "")}})
    def slug(text: str) -> str:
        return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.casefold())).strip("-") or "item"
    for kind, values in (("topics", topic_values), ("organizations", org_values)):
        for title in values:
            ids = [s["id"] for s in stories if title in s.get(kind, [])]
            key = slug(title)
            canonical_route = f"topic/{key}/" if kind == "topics" else f"org/{key}/"
            canonical = absolute(base_url, canonical_route) if kind == "organizations" else absolute(base_url, f"api/v1/topics/{key}.json")
            _dump(api / kind / f"{key}.json", {"id": key, "slug": key, "title": title, "canonical_url": canonical, "language": "en", "event_date": max(s["event_at"] for s in stories if s["id"] in ids), "published_at": min(s["first_published_at"] for s in stories if s["id"] in ids), "updated_at": max(s["updated_at"] for s in stories if s["id"] in ids), "stories": ids, "provenance": {"release_id": status.get("release_id", ""), "corpus_digest": status.get("corpus_digest", ""), "stories_sha256": status.get("stories_sha256", "")}})
    corrections = []
    for story in all_stories:
        if not story.get("corrections"):
            continue
        record = records.get(story["id"]) or _story_record(story, catalogs, base_url, status)
        correction = {"story_id": story["id"], "canonical_url": absolute(base_url, f"api/v1/corrections.json#{story['id']}"), "language": "en", "event_date": story["event_at"], "published_at": story["first_published_at"], "updated_at": story["updated_at"], "title": record["title"], "items": story["corrections"], "provenance": record["provenance"]}
        if story["id"] in records:
            correction["story_url"] = record["canonical_url"]
        corrections.append(correction)
    correction_doc = {"schema": "fcmo-agent-api-v1", "canonical_url": absolute(base_url, "corrections/"), "language": "en", "generated_at": status.get("status_updated_at", ""), "items": corrections, "provenance": {"release_id": status.get("release_id", ""), "corpus_digest": status.get("corpus_digest", ""), "stories_sha256": status.get("stories_sha256", "")}}
    _dump(api / "corrections.json", correction_doc)
    search_items = [{"id": r["id"], "title": r["title"], "summary": r["summary"], "url": r["canonical_url"], "canonical_url": r["canonical_url"], "language": r["language"], "event_date": r["event_date"], "published_at": r["published_at"], "updated_at": r["updated_at"], "topics": r["topics"], "organizations": r["organizations"], "confidence": r["confidence"], "evidence": r["evidence"], "importance": r["importance"], "provenance": r["provenance"]} for r in records.values()]
    index = {"schema": "fcmo-agent-api-v1", "canonical_url": absolute(base_url, "api/v1/"), "language": "en", "generated_at": status.get("status_updated_at", ""), "event_date": max((s["event_at"] for s in stories), default=""), "published_at": min((s["first_published_at"] for s in stories), default=""), "updated_at": max((s["updated_at"] for s in stories), default=""), "provenance": correction_doc["provenance"], "stories": [absolute(base_url, f"api/v1/stories/{sid}.json") for sid in records], "editions": [absolute(base_url, f"api/v1/editions/{d}.json") for d in dates], "topics": [absolute(base_url, f"api/v1/topics/{slug(t)}.json") for t in topic_values], "organizations": [absolute(base_url, f"api/v1/organizations/{slug(o)}.json") for o in org_values], "corrections": absolute(base_url, "api/v1/corrections.json"), "search_index": absolute(base_url, "api/v1/search-index.json")}
    _dump(api / "search-index.json", {"schema": "fcmo-agent-api-v1", "canonical_url": absolute(base_url, "api/v1/search-index.json"), "language": "en", "generated_at": status.get("status_updated_at", ""), "event_date": index["event_date"], "published_at": index["published_at"], "updated_at": index["updated_at"], "items": search_items, "provenance": correction_doc["provenance"]})
    _dump(api / "index.json", index)
    for name, schema in _schemas().items():
        _dump(api / "schema" / f"{name}.schema.json", schema)
    def get_op(operation_id: str, description: str, schema_name: str, parameter: tuple[str, str] | None = None) -> dict:
        operation = {"operationId": operation_id, "responses": {"200": {"description": description, "content": {"application/json": {"schema": {"$ref": f"./schema/{schema_name}.schema.json"}}}}}}
        if parameter:
            operation["parameters"] = [{"name": parameter[0], "in": "path", "required": True, "schema": {"type": "string", "format": parameter[1]}}]
        return {"get": operation}
    paths = {"/index.json": get_op("index", "Static API index", "index"),
             "/stories/{id}.json": get_op("getStory", "Story record", "story", ("id", "FCMO stable ID")),
             "/editions/{date}.json": get_op("getEdition", "Edition record", "edition", ("date", "date")),
             "/topics/{slug}.json": get_op("getTopic", "Topic record", "topic", ("slug", "slug")),
             "/organizations/{slug}.json": get_op("getOrganization", "Organization record", "organization", ("slug", "slug")),
             "/corrections.json": get_op("getCorrections", "Corrections ledger", "corrections"),
             "/search-index.json": get_op("getSearchIndex", "Search corpus", "search-index")}
    openapi = {"openapi": "3.1.0", "info": {"title": "FCMO AI Newsletter Static Agent API", "version": "1.0.0"}, "servers": [{"url": absolute(base_url, "api/v1/")}], "paths": paths}
    _dump(api / "openapi.json", openapi)
    (api / "index.html").write_text(f'<!doctype html><meta charset="utf-8"><link rel="icon" href="{base.rstrip("/")}/assets/pwa/favicon.svg" type="image/svg+xml"><title>FCMO AI Newsletter API v1</title><h1>Static API v1</h1><p><a href="index.json">API index</a> · <a href="openapi.json">OpenAPI 3.1</a> · <a href="schema/index.schema.json">Index schema</a></p>\n', encoding="utf-8")
    # RFC 9116 security.txt is emitted only when the publication has a verified security contact.
    for locale in locales:
        code, prefix = locale["code"], locale["path_prefix"]
        base_path = out / prefix
        llms = ["# FCMO AI Newsletter", "", "> Evidence-first AI research, reporting and practical context from FCMO AI, under the FCMO Group. The technical daily paper is FCMO AI; the reader newsletter and Javier-led letters belong to FCMO Group.", "", f"Canonical base: {base_url}", f"Language: {code}", "", "## Start here", f"- [Home]({absolute(base_url, prefix)})", f"- [Method and evidence policy]({absolute(base_url, prefix + 'method/')})", f"- [Corrections]({absolute(base_url, prefix + 'corrections/')})", f"- [Agent discovery]({absolute(base_url, 'agent.json')})", f"- [Static API index]({absolute(base_url, 'api/v1/index.json')})", f"- [Complete machine-readable edition]({absolute(base_url, prefix + 'llms-full.txt')})", "", "## Machine-readable data", f"- [Search index]({absolute(base_url, 'api/v1/search-index.json')})", f"- [OpenAPI 3.1]({absolute(base_url, 'api/v1/openapi.json')})", f"- [Stories]({absolute(base_url, 'api/v1/index.json')})", f"- [Corrections ledger]({absolute(base_url, 'api/v1/corrections.json')})", f"- [Original research dossiers, compatibility snapshot]({absolute(base_url, 'data/developments.json')})", f"- [Search corpus and publication memory, compatibility snapshot]({absolute(base_url, 'data/search.json')})", f"- [Per-brief dossiers, compatibility snapshot]({absolute(base_url, 'data/briefs/<FCMO-ID>.json')})", f"- [Relationships]({absolute(base_url, 'data/relationships.json')})", f"- [Edition memory]({absolute(base_url, 'data/publication-memory.json')})", f"- [Topics]({absolute(base_url, 'data/topics.json')})", f"- [Organizations]({absolute(base_url, 'data/organizations.json')})", f"- [Media provenance]({absolute(base_url, 'data/media.json')})", "", "## Query semantics", "Search supports query, scope, desk, evidence, confidence, importance, topic, organization, dates, open gaps, sort, projected fields and result limit. Keep claim labels, evidence class, confidence, importance, limitations, contradictions and open evidence gaps distinct.", "", "## Publication policies", "- Original editorial material is CC BY 4.0 only where FCMO has authority to license it; third-party material and marks retain their own rights.", "- Corrections are recorded against the affected story with correction notes and updated dates.", "- Evidence, confidence, limitations, contradictions and open gaps remain distinct; do not treat importance as confidence.", ""]
        (base_path / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
        full = list(llms)
        full.extend(["## Stories", ""])
        for story in stories:
            story_md = _markdown_story(story, locale, catalogs[code], base_url, status)
            full.extend([story_md, ""])
            rel = locale["path_prefix"] + story_path({"path_prefix": ""}, story).rstrip("/") + ".md"
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(story_md, encoding="utf-8")
        for day, values in records_by_date.items():
            title = f"Edition {day}"
            lines = [f"# {title}", "", f"Canonical URL: {absolute(base_url, locale['path_prefix'] + f'edition/{day}/')}", f"Language: `{code}`", f"Edition date: {day}", f"Provenance receipt: `{status.get('release_id', '')}`; corpus digest `{status.get('corpus_digest', '')}`", ""]
            for story in values:
                lines.append(f"- [{headline(story, code, catalogs[code])}]({absolute(base_url, locale['path_prefix'] + story_path({'path_prefix': ''}, story))}) — {dek(story, code, catalogs[code])}")
            md = "\n".join(lines) + "\n"
            target = out / locale["path_prefix"] / "edition" / f"{day}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(md, encoding="utf-8")
            full.extend([md, ""])
        (base_path / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")
    legacy_llms = (reference / "llms.txt").read_text(encoding="utf-8")
    llms_path = out / "llms.txt"
    llms_path.write_text(llms_path.read_text(encoding="utf-8") + "\n## Original agent index\n\nCompatibility copy of the original publication's agent index, retained so existing consumers keep its complete brief listing and query guidance.\n\n" + "\n".join(legacy_llms.splitlines()[1:]) + "\n", encoding="utf-8")
    legacy_full = (reference / "llms-full.txt").read_text(encoding="utf-8")
    full_path = out / "llms-full.txt"
    full_path.write_text(full_path.read_text(encoding="utf-8") + "\n## Original agent corpus snapshot\n\nThe following material preserves the previous agent-layer publication as a dated compatibility reference. Current story records above come from this build's validated corpus.\n\n" + "\n".join(legacy_full.splitlines()[1:]) + "\n", encoding="utf-8")
    # Preserve legacy discovery contract and datasets while adding current routes.
    agent = dict(old)
    agent.update({"publication": {"name": "FCMO AI Newsletter", "description": "Evidence-first public AI research and technical daily paper.", "brands": {"umbrella": "FCMO Group", "technical_paper": "FCMO AI", "newsletter": "FCMO Group", "newsletter_voice": "Javier Castellanos Peña"}, "zones": ["FCMO Group landing", "FCMO Group Newsletter", "FCMO AI technical paper"]}, "base_url": base_url, "language_routes": {l["code"]: absolute(base_url, l["path_prefix"]) for l in locales}, "endpoints": {**old["endpoints"], "api_index": absolute(base_url, "api/v1/index.json"), "openapi": absolute(base_url, "api/v1/openapi.json"), "stories": absolute(base_url, "api/v1/stories/{id}.json"), "editions_v1": absolute(base_url, "api/v1/editions/{date}.json"), "topics_v1": absolute(base_url, "api/v1/topics/{slug}.json"), "organizations_v1": absolute(base_url, "api/v1/organizations/{slug}.json"), "corrections_v1": absolute(base_url, "api/v1/corrections.json"), "search_index_v1": absolute(base_url, "api/v1/search-index.json"), "license": "https://creativecommons.org/licenses/by/4.0/", "provenance": absolute(base_url, "data/newsroom-status.json"), "corrections_policy": absolute(base_url, "corrections/")}, "license": {"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/", "scope": "Original editorial content FCMO has authority to license; excludes third-party works and trademarks."}, "provenance": {"airlock_release_id": status.get("release_id"), "airlock_record_count": status.get("airlock_record_count"), "corpus_digest": status.get("corpus_digest"), "stories_sha256": status.get("stories_sha256"), "receipt_url": absolute(base_url, "data/newsroom-status.json")}, "update_cadence": {"upstream": "Daily ARB airlock; expected activation at 06:00 America/Mexico_City and bridge at 07:10 America/Mexico_City", "publication": "After validated sanitized corpus and release gates"}, "corrections_policy": "Corrections are disclosed on the corrections page and attached to affected story records; material changes update modified dates.", "contact": {"corrections": absolute(base_url, "corrections/"), "publisher": absolute(base_url, "about/")}, "counts": {"briefs": len(stories), "topics": len(topic_values), "organizations": len(org_values), "relationships": len(json.loads((out / "data/relationships.json").read_text(encoding="utf-8")))}, "newly_ingested_brief_ids": []})
    agent["legacy_compatibility"] = {"counts": reference_agent.get("counts", {}), "original_agent_contract": reference_agent.get("schema")}
    agent["llms_by_locale"] = {l["code"]: {"llms": absolute(base_url, l["path_prefix"] + "llms.txt"), "llms_full": absolute(base_url, l["path_prefix"] + "llms-full.txt")} for l in locales}
    agent["endpoints"]["schemas"] = {name: absolute(base_url, f"api/v1/schema/{name}.schema.json") for name in _schemas()}
    agent["endpoints"]["search"] = absolute(base_url, "api/v1/search-index.json")
    agent["query_types"]["search"]["offline_source"] = "api/v1/search-index.json"
    _dump(out / "agent.json", agent)
