# FCMO AI Newsletter — Autonomous Newsroom Contract

**Status:** production architecture  
**Relationship to ARB:** public clean-room consumer of a sanitized/declassified newswire  
**Canonical semantic language:** English  
**Native editions:** English, Latin American Spanish, Simplified Chinese

## 1. Mission

FCMO AI Newsletter is not a public mirror of the private AI Research Breakthroughs (ARB) repository. It is an autonomous public newspaper whose evidence seed comes through an intentionally narrow ARB publication airlock.

The newspaper should publish useful evidence and independently reconstructable public analysis while preserving FCMO's private hypotheses, experiments, downstream relevance, strategy and other internal alpha.

The production chain is:

`ARB research + EN/ES/ZH editorial preparation → privacy scrub → semantic declassification → native-edition airlock → allowlisted content-addressed newswire receipt → Newsletter clean-room research → provider-free locale integrity → visual desk → Story layer → editorial discovery frontends → release gates → Pages → live oracle`.

## 2. Trust zones

### Private ARB

ARB may know private projects, hypotheses, tests, scale-transfer warnings, strategic implications and operational state. None of those become public merely because they contain no obvious codename.

ARB also owns the native-language editorial work for anything it chooses to publish. The research/publication agent that already understands the evidence prepares canonical English plus `es-419` and `zh-Hans` wording as one publication obligation. Language does not create a new declassification boundary: translated prose is screened under the same privacy rules as English.

### Airlock

The airlock exports only positively allowlisted public evidence and native-edition deltas that bind to the current declassified English source. Strategic research/engineering/policy implications are default-private. A fresh `airlock.json` receipt proves an airlock run occurred and gives the public payload a stable content-addressed `release_id`.

### Public clean room

Newsletter never clones or authenticates to private ARB. `tools/public_research_desk.py` receives only already-sanitized public dossiers plus public Internet access. Any additional public context is therefore reconstructable without private research state.

Newsletter never asks a model provider to translate or rewrite a story. It imports ARB-authored locale deltas, reconciles them against the declassified schema, validates high-value invariants, and fails closed on incomplete three-language coverage.

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

## 5. Three native editions are one publication obligation

A new or materially changed story is not publishable until all three native editions are complete.

ARB writes the two additional native editions before the airlock. Newsletter then:

1. imports `corpus/data/locales/es-419/records.json` and `zh-Hans/records.json` with `tools/sync_airlocked_locales.py`;
2. prunes any overlay path that no longer exists in the declassified schema with `tools/reconcile_locale_overlays.py`;
3. runs `tools/validate_localizations.py` to require exact story-ID parity, required reader-facing prose, compatible structure, exact number/FCMO-ID/URL preservation, basic Simplified-Chinese script sanity, and non-identical language editions;
4. records a provider-free integrity receipt with `editorial_owner: ARB publication agent`, `human_reviewed: false`, and `network_translation: false`.

Deterministic validation does not pretend to prove literary quality. Semantic fidelity is the responsibility of the ARB publication agent and remains auditable through source control. There is no downstream translation generator, no language-model review service, and no page-view generative fallback.

The runtime remains presentation-only.

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

## 8. Human and machine publication surfaces

The newspaper emits static, indexable Story routes:

- `/news/en/<FCMO-ID>.html`;
- `/news/es/<FCMO-ID>.html`;
- `/news/zh-hans/<FCMO-ID>.html`.

The editorial locale remains `es-419`; the public search-language route/hreflang uses `es`. Story pages emit canonical links, `hreflang`, `x-default`, `NewsArticle` JSON-LD, organization byline and publication/update timestamps.

`tools/build_editorial_frontends.py` additionally builds first-class public discovery surfaces for archive, search, topics, topic detail, organizations, organization detail, corrections, feeds, methodology, editorial policy, automation disclosure, accessibility, newsroom status, 404 handling and the `/news/` language gateway. `tools/finalize_editorial_frontends.py` binds those pages to real Story routes, canonical URLs, sitemap coverage and the final build manifest.

Machine-facing publication surfaces include RSS, JSON Feed, public search JSON, public development JSON/JSONL, Story JSON, general sitemap, news sitemap, `llms.txt`, `llms-full.txt` and `agent.json`.

Discovery frontends are generated **after** the frozen overlay is mounted on the Pages candidate. This ordering is a contract: otherwise older archive/search shells stored in the overlay could silently replace newer presentation code.

## 9. Operational truth and ACK states

The old behavior “corpus absent → green no-op” is forbidden.

A refresh first requires a fresh `fcmo-newswire-airlock-v2` receipt. Newsletter distinguishes:

- `PUBLIC_DELTA_PENDING` — fresh airlock content differs from prior accepted release;
- `NO_PUBLIC_DELTA` — airlock ran, but content identity is unchanged;
- `PUBLIC_DELTA_READY` — new content was ingested, native-edition parity validated, researched, illustrated, built and gated; deployment still requires Pages;
- `NO_PUBLIC_DELTA_READY` — a healthy quiet cycle was rebuilt/gated; deployment still requires Pages;
- `BOOTSTRAPPED_FROM_EXISTING_PUBLIC_RELEASE` — one-time public-side migration status; explicitly does **not** assert a fresh ARB delivery.

Missing or stale airlock input is an operational failure, not a quiet-news state.

`site/data/newsroom-status.json` is the downstream acknowledgement. It records release identity, counts and the fact that live deployment still needs independent proof.

## 10. Reality-grounded deployment proof

Pages uses the frozen-overlay, native-localization, readiness-receipt and real-browser gates, then regenerates discovery frontends on the exact assembled candidate before upload.

After deployment, `tools/verify_live_newsroom.py` fetches the actual production origin and requires, among other contracts:

- live release identity equals repository truth;
- Story count equals the committed Story layer;
- `/news/en/`, `/news/es/`, `/news/zh-hans/` and the three-language `/news/` gateway are reachable;
- the latest Story exists in all three languages;
- `NewsArticle`, `hreflang` and the FCMO AI Research Desk byline are present;
- archive/search/topics/organizations/corrections/feeds/methodology/editorial-policy/automation/accessibility/status are live as real frontends rather than shells;
- general and news sitemaps, feeds, `llms.txt`, `llms-full.txt` and `agent.json` are reachable;
- the main publication links into FCMO WIRE;
- an airlock-backed release is not stale.

A separate scheduled production-health workflow repeats this reality check. A green build alone is never proof that the newspaper is live.

## 11. Authentication boundary

ARB publication uses a least-privilege GitHub App installed only on `FCMO-AI-Newsletter`, with repository `Contents: read/write` and no broader organization authority. Each run mints a short-lived installation token, checks out the public sink with that machine identity, stages only `corpus/`, and pushes only that boundary.

There is no personal publisher token fallback. Missing GitHub App configuration is a visible operational failure, not permission to widen credentials or bypass the airlock.

The public repository never authenticates back into ARB.

## 12. Corrections and future evolution

Research dossiers remain stable evidence identities. Material new evidence should update the same dossier/Story identity where appropriate; the existing correction and edition mechanisms remain authoritative rather than manufacturing a new story solely to refresh timestamps.

Future additions must preserve the trust-zone model. In particular, richer public analysis or media discovery may improve the newsroom but may not receive private ARB state as a shortcut, and no downstream service may silently reintroduce a second translation pipeline.
