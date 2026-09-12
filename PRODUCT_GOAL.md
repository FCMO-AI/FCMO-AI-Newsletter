# FCMO AI Newsletter — Canonical Product Goal

## Goal

Build and operate the **real production version** of FCMO AI Newsletter: an autonomous, current, evidence-first AI newspaper that reliably turns ARB research into a polished public publication without routine human intervention.

This is the default optimization target for all Newsletter-specific work. It is not a demo, test surface, launch mockup, historical showcase, or one-off publishing pipeline. The intended product is a dependable newspaper that can be trusted to keep running.

## Product success condition

The Newsletter is successful only when the whole reader-visible system works continuously:

`fresh ARB evidence -> publication-ready snapshot -> sanitized Airlock -> autonomous newsroom -> editorial Story layer -> EN/ES/ZH publication -> release gates -> production deploy -> live browser verification -> health monitoring`

A green intermediate step is not equivalent to product success. Repository state, generated files, CI, deployment, and the reader-visible website are separate layers and must be verified at the appropriate boundary.

## Operational standard

Prefer boring reliability over clever fragility.

The production system should be:

- **Autonomous:** normal daily operation must not require a person, ChatGPT scheduled task, manual dispatch, or ad-hoc repair.
- **Current:** when material AI news exists, the front page should strongly prefer developments from the current America/Mexico_City date or the immediately previous date.
- **Evidence-first:** freshness never upgrades weak evidence into fact. Verified, developing, signal, rumor, correction, and uncertainty states remain explicit.
- **Fail-closed:** if a publication boundary, privacy rule, localization contract, release gate, or deployment proof fails, keep the last known-good edition live rather than publishing an unsafe or broken candidate.
- **Reader-real:** success means the actual public website renders the intended current edition correctly, not merely that source files or build artifacts contain it.
- **Multilingual:** English, `es-419`, and `zh-Hans` remain first-class production editions with semantic parity and source-controlled publication behavior.
- **Deterministic where possible:** publication mechanics, selection rules, transforms, and deploy gates should be reproducible and inspectable rather than dependent on hidden manual judgment.
- **Recoverable:** failures must leave enough receipts and state to identify the exact broken stage and resume safely.
- **Historically honest:** old editions are immutable publication history; later evidence may update living dossiers without silently rewriting what was published.

## Freshness contract

The Newsletter is a newspaper, not merely a mirror of ARB's most exhaustively closed historical watermark.

Historical completeness and public-news freshness are separate concepts.

When material items exist:

- **Target:** the primary front-page lead is no more than 24 hours old.
- **Acceptable:** at least one material front-page item is no more than 48 hours old.
- **Freshness failure:** the newest visible material is older than 48 hours while ARB contains newer public-safe verified or clearly labeled developing/signal material that could legitimately be shown.

Editorial selection should first consider the current date and previous date, then fall back to older material only when the recent window contains nothing sufficiently material.

Freshness must never erase evidence distinctions. A newer but weaker item belongs in a clearly labeled developing/signal lane; an older strongly verified item may remain prominent when warranted. The goal is maximum useful recency **subject to evidence truth**, not recency at any cost.

## Two-speed publication model

The public product should support both:

1. **Verified lane** — high-confidence developments with stronger evidence and resolved core claims.
2. **Developing / signal lane** — material recent developments that are useful to readers but still carry open verification gaps.

This allows the newspaper to remain current without pretending that every same-day development has already completed ARB's deepest audit.

Weak evidence remains visibly weak evidence. Importance and freshness do not upgrade confidence.

## Daily autonomy contract

A healthy daily cycle should require no manual action:

1. ARB produces or advances a valid immutable publication-ready snapshot.
2. The Newswire Bridge authenticates read-only, proves lineage and seal validity, exports only sanitized bytes, and destroys private checkout state.
3. Newsletter ingests the corpus, preserves all accepted stories, imports curated locales, re-checks public evidence, resolves media, builds Story/editorial surfaces, freezes the release, and runs publication gates.
4. Production deployment runs only after the candidate passes.
5. A post-deploy oracle checks the actual public origin in a real browser, including the current lead and supported locales.
6. Production health records whether freshness, serving, and publication state are actually healthy.

If any stage fails, the previous known-good public edition remains live and the failed stage is the thing to repair.

## Freshness observability

Production health should distinguish at least these timestamps/ages:

- newest material research event available upstream;
- newest public-safe ARB item;
- current `PUBLICATION_READY` snapshot age;
- newest item in Newsletter `corpus/`;
- newest Story publication/event date;
- current front-page lead age;
- last successful newsroom refresh;
- last successful Pages deployment;
- last successful post-deploy live-browser verification.

A system that deploys successfully while serving stale news is **not healthy**.

## What does not count as completion

Do not call the product finished merely because:

- a workflow exists;
- a build is green;
- a file changed;
- a headline is present in HTML source;
- a deployment API returned success;
- one manual run worked once;
- an old verified story is visible while newer legitimate material is suppressed;
- the site looks correct in one locale or viewport;
- a scheduled job is configured but has not demonstrated unattended production cycles.

## Current strategic phase

The Newsletter is now in **production hardening and freshness convergence**.

The priority is not adding ornamental features. The priority is to prove and improve repeated unattended daily operation, current-day / previous-day editorial freshness, strong observability, fail-closed recovery, and reader-visible correctness.

Until those properties are demonstrated across repeated real cycles, all Newsletter-specific sessions should treat reliability, freshness, production truth, and autonomous operation as the dominant product objective.
