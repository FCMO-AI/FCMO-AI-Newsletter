# FCMO AI Newsletter — Autonomous Newsroom Contract

**Status:** production architecture  
**Relationship to ARB:** public clean-room consumer of a sanitized/declassified newswire  
**Canonical semantic language:** English  
**Native editions:** English, Latin American Spanish, Simplified Chinese

## 1. Mission

FCMO AI Newsletter is not a public mirror of the private AI Research Breakthroughs (ARB) repository. It is an autonomous public newspaper whose evidence seed comes through an intentionally narrow ARB publication airlock.

The newspaper should publish useful evidence and independently reconstructable public analysis while preserving FCMO's private hypotheses, experiments, downstream relevance, strategy and other internal alpha.

The production chain is:

`ARB research → privacy scrub → semantic declassification → allowlist airlock → content-addressed newswire receipt → Newsletter clean-room research → translation freshness + independent language review → visual desk → Story layer → release gates → Pages → live oracle`.

## 2. Trust zones

### Private ARB

ARB may know private projects, hypotheses, tests, scale-transfer warnings, strategic implications and operational state. None of those become public merely because they contain no obvious codename.

### Airlock

The airlock exports only positively allowlisted public evidence. Strategic research/engineering/policy implications are default-private. A fresh `airlock.json` receipt proves an airlock run occurred and gives the public payload a stable content-addressed `release_id`.

### Public clean room

Newsletter never clones or authenticates to private ARB. `tools/public_research_desk.py` receives only already-sanitized public dossiers plus public Internet access. Any additional public context is therefore reconstructable without private research state.

## 3. A dossier is not a Story

`release-src/data/briefs/<FCMO-ID>.json` remains the evidence-oriented public dossier.

`site/data/stories.json` is the newspaper Story layer. A Story carries a public headline/dek, publication/update times, news disposition, claims/evidence, baseline, caveats, open questions, primary sources, public-research receipt and visual provenance.

Current deterministic dispositions are:

- `LEAD` — verified/non-signal impact 8+;
- `STANDARD` — verified/non-signal impact 6–7;
- `BRIEF` — lower-impact public research worth retaining;
- `SIGNAL` — evidence D or weak/speculative confidence, visibly separate from verified reporting.

There is no fixed story quota. Quiet evidence days are allowed.

## 4. Editorial anatomy

Static Story pages expose recurring evidence-first sections:

- **What actually changed**;
- **Claim vs. evidence**;
- **Strongest baseline**;
- **The caveat that matters**;
- **What remains unknown**;
- **FCMO Lens** — public analysis derived from the sanitized/public evidence surface;
- **Primary sources**;
- **Further public context** discovered by the clean-room desk.

FCMO Lens must never be populated by copying private ARB strategic implication fields. If public analysis cannot be supported from intentionally exposed public evidence, it does not belong there.

## 5. Translation is a publication obligation

A new or materially changed story is not publishable until all three native editions are complete.

`tools/translation_freshness.py` tracks a digest of reader-facing canonical prose per stable FCMO ID. If an existing English dossier changes, the corresponding Spanish and Chinese overlays are invalidated and regenerated; stable IDs no longer imply stale translations are safe.

`tools/review_localizations.py` is independent of the translator. It applies deterministic number/ID/URL checks and an independent machine-language editorial review using MQM-style Critical/Major/Minor severity. Any Critical or Major error blocks publication. Review is explicitly machine review, not human review.

The runtime remains presentation-only: no page-view translation API exists.

## 6. Autonomous visual desk

`tools/visual_desk.py` resolves story media under a fail-safe rights policy:

1. inspect cited public source pages;
2. prefer a story-specific image only when both the image metadata and permissive reuse rights are machine-verifiable;
3. record source page, license URL, reuse basis and credit;
4. otherwise generate an original deterministic FCMO SVG explainer;
5. never treat generated editorial art as source evidence.

Ambiguous rights cause a safe original fallback, not a publication failure and not an unlicensed hotlink.

`release-src/data/media.json` is the media provenance surface.

## 7. Public research receipts

For each public dossier, `tools/public_research_desk.py` reopens cited public sources and searches for related scholarly context without access to ARB private state. Receipts live at:

`release-src/data/public-research/<FCMO-ID>.json`.

Receipts record exactly what was checked and explicitly avoid claiming exhaustive web coverage. Multiple derivative sources are not treated as independent confirmation merely because they are numerous.

## 8. Searchable multilingual newspaper surfaces

The newspaper emits static, indexable Story routes:

- `/news/en/<FCMO-ID>.html`;
- `/news/es/<FCMO-ID>.html`;
- `/news/zh-hans/<FCMO-ID>.html`.

The editorial locale remains `es-419`; the public search-language route/hreflang uses `es`. Story pages emit canonical links, `hreflang`, `x-default`, `NewsArticle` JSON-LD, organization byline and publication/update timestamps.

`news-sitemap.xml` contains the recent Google-News-style publication window rather than pretending every historical dossier is breaking news.

## 9. Operational truth and ACK states

The old behavior “corpus absent → green no-op” is forbidden.

A refresh first requires a fresh `fcmo-newswire-airlock-v2` receipt. Newsletter distinguishes:

- `PUBLIC_DELTA_PENDING` — fresh airlock content differs from prior accepted release;
- `NO_PUBLIC_DELTA` — airlock ran, but content identity is unchanged;
- `PUBLIC_DELTA_READY` — new content was ingested, researched, localized, reviewed, illustrated and gated; deployment still requires Pages;
- `NO_PUBLIC_DELTA_READY` — a healthy quiet cycle was rebuilt/gated; deployment still requires Pages;
- `BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE` — one-time public-side migration status; explicitly does **not** assert a fresh ARB delivery.

Missing or stale airlock input is an operational failure, not a quiet-news state.

`site/data/newsroom-status.json` is the downstream acknowledgement. It records release identity, counts and the fact that live deployment still needs independent proof.

## 10. Reality-grounded deployment proof

Pages continues to use the existing frozen-overlay, curated-localization, readiness-receipt and real-browser gates.

After deployment, `tools/verify_live_newsroom.py` fetches the actual production origin and requires:

- live release identity equals repository truth;
- Story count equals the committed Story layer;
- `/news/en/`, `/news/es/`, `/news/zh-hans/` are reachable;
- the latest Story exists in all three languages;
- `NewsArticle`, `hreflang` and the FCMO AI Research Desk byline are present;
- `news-sitemap.xml` is reachable;
- the main publication links into FCMO WIRE;
- an airlock-backed release is not stale.

A separate scheduled production-health workflow repeats this reality check. A green build alone is never proof that the newspaper is live.

## 11. Authentication boundary

ARB publication prefers a least-privilege GitHub App scoped to `FCMO-AI-Newsletter`. The legacy publisher token remains a migration fallback. Absence of both is a visible failure.

The public repository never authenticates back into ARB.

## 12. Corrections and future evolution

Research dossiers remain stable evidence identities. Material new evidence should update the same dossier/Story identity where appropriate; the existing correction and edition mechanisms remain authoritative rather than manufacturing a new story solely to refresh timestamps.

Future additions must preserve the trust-zone model. In particular, richer public analysis, media discovery or new model providers may improve the newsroom but may not receive private ARB state as a shortcut.
