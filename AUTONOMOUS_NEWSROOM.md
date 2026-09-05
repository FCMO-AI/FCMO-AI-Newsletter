# FCMO AI Newsletter autonomous newsroom

FCMO AI Newsletter is a public newspaper backed by research intelligence, not a mirror of a private research repository.

## Trust model

Newsletter knows only:

- the sanitized/declassified `corpus/` release;
- its own public publication history;
- its own committed translations, media and public clean-room research;
- public web sources reached by the public newsroom.

It never authenticates to, clones or reads the private upstream research repository.

## Lifecycle

```text
sanitized corpus + release receipt
    -> airlock health/delta classification
    -> canonical public English ingest
    -> clean-room public web research
    -> translation pruning/generation
    -> independent language-editor review
    -> Story wire
    -> Visual Desk + rights gate
    -> localized routes / NewsArticle / sitemaps
    -> deterministic frozen overlay
    -> publication gates + browser oracle
    -> Pages deployment
    -> live-origin oracle
```

## Research dossier vs Story

A **research dossier** is the public evidence authority: claims, mechanism, demonstrated vs claimed result, evidence class, confidence, importance, baseline, limitations, contradictions, gaps and sources.

A **Story** is the newspaper projection. Its `disposition` can be:

- `LEAD`
- `STANDARD`
- `BRIEF`
- `SIGNAL`
- `DATABASE_ONLY`

Impact never upgrades evidence. A 10/10 weak signal remains a `SIGNAL`, not a verified lead.

The Story layer also records `CURRENT`, `CORRECTION`, `RETRACTION` or `SUPERSESSION` publication events from canonical status without rewriting the underlying evidence record.

## Clean-room research

`tools/public_research_desk.py` runs only for newly ingested public dossiers. It sends the sanitized dossier to a public-web research pass with server-side web search, asks for independent corroboration/contradiction and baseline/context checking, and rejects any returned source URL that did not actually occur in the search evidence.

The resulting records live under `site/data/newsroom-research/`. They contain no private upstream identifiers or control state.

Clean-room confidence is exposed separately. It cannot silently upgrade canonical evidence/confidence or change Story disposition.

## Translation

The three native locales remain English, Latin American Spanish and Simplified Chinese. Missing translations are generated before publication. An independent editorial review then binds a PASS to both the canonical-source digest and translation digest. Changing either invalidates that PASS.

## Visual Desk

The Visual Desk can discover candidate imagery but cannot publish a discovered image until reuse rights are proven. Unverified discoveries live only in `newsroom-work/`. If no approved image exists, it generates a local FCMO-owned evidence graphic.

See `MEDIA_POLICY.md`.

## Distribution surfaces

After Airlock-v2 activation the release also exposes:

- `data/stories.json`
- `data/newsroom-status.json`
- `data/news-articles.json`
- `site/data/newsroom-research/<FCMO-ID>.json` in the assembled public tree
- `/en/developments/<FCMO-ID>.html`
- `/es/developments/<FCMO-ID>.html`
- `/zh-hans/developments/<FCMO-ID>.html`
- `sitemap.xml`
- `news-sitemap.xml`
- the existing RSS/JSON feeds, agent API and dossier surfaces.

## Operational states

A fresh delivery is classified as either `PUBLIC_DELTA` or `NO_PUBLIC_DELTA`. Missing/stale receipts are transport starvation and fail red.

The final Pages job verifies the actual live origin against the expected `FCMO-NEWSWIRE-*` release identity. A successful deploy action without matching live bytes is not considered a successful newspaper release.
