# Agent and machine interfaces

FCMO AI Newsletter publishes a static, language-aware agent layer alongside its HTML publication. All public records are generated from the sanitized story corpus and carry stable identifiers, canonical URLs, dates, locale labels and the available release receipt digests.

## Discovery

- `/agent.json` keeps the original `fcmo-agent-discovery-v2` fields and `fcmo-agent-query-v2` query vocabulary. It adds the FCMO Group / FCMO AI brand zones, API endpoints, per-language LLM indexes, licensing, release provenance, cadence, corrections and contact routes.
- `/llms.txt` follows the llmstxt.org structure. Each published locale has its own file and matching `/llms-full.txt`.
- Historical original datasets remain under `/data/` as a compatibility snapshot. `/data/briefs/` retains the two original dossiers retired from the current corpus, and the original agent discovery/LLM files are kept in `release-src/data/public-research/agent-reference/` as reproducible source material. The current static API is authoritative for the current built corpus.
- `/api/v1/index.json` indexes stories, editions, topics, organizations, corrections and search. Each resource has a corresponding JSON Schema under `/api/v1/schema/`; `/api/v1/openapi.json` describes static GET operations.
- Story and edition HTML pages advertise adjacent Markdown plus JSON alternates. Story pages also contain `NewsArticle` JSON-LD and correction notes when present.

## Static MCP server

Run `node tools/agent/mcp/server.mjs --base https://fcmo-ai.github.io/FCMO-AI-Newsletter/`. It exposes `search`, `get_story`, `get_edition`, `list_topics` and `latest` over the public static API. For offline use against a built directory, add `--root /path/to/site`; tests use this mode and make no network requests.

## Provenance and rights

`provenance` records the sanitized Airlock release ID, record count, corpus digest and story payload digest reported by the newsroom receipt. Original editorial work is CC BY 4.0 only where FCMO has authority to license it; third-party material, marks and other rights remain outside that grant. Corrections link to the public ledger and remain attached to the affected story.

No extra `/.well-known/` declaration is emitted: this static publication has no applicable agent-discovery well-known standard, and it has no verified security contact suitable for RFC 9116 `security.txt`.
