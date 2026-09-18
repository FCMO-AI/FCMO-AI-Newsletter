# Freshness supply coherence shadow experiment

**State:** NON_NORMATIVE / EVIDENCE_ONLY  
**Base:** Newsletter `cb5d74d7df483cea5083adcdf53b6172eee55372`

## Question

Newsletter production health can truthfully report that the Story layer is stale while
ARB has also published a newer sanitized daily edition. Those are not enough facts to
infer that Pages should have blocked a candidate.

The missing question is representational:

> does the newer public material have a stable Story identity and native-edition
> coverage that makes it even *representable* inside the current Story pipeline?

This experiment observes that cut without acquiring publication authority.

## Observer

`tools/freshness_supply_coherence.py` compares:

1. newest material Story age;
2. newest published sanitized edition and its publication age;
3. whether that edition is newer than Story supply;
4. whether its numbered signal sections bind to stable `FCMO-*` identities;
5. whether any bound identities exist in both native locale packs.

Possible states deliberately stop short of release eligibility:

- `STORY_SUPPLY_FRESH`;
- `STORY_STALE_UPSTREAM_PUBLICATION_UNKNOWN`;
- `STORY_STALE_NO_NEWER_RECENT_PUBLICATION`;
- `UPSTREAM_PUBLICATION_NEWER_UNBOUND`;
- `UPSTREAM_PUBLICATION_NEWER_BOUND_UNLOCALIZED`;
- `UPSTREAM_PUBLICATION_NEWER_BOUND_AND_LOCALIZED`;
- `UPSTREAM_PUBLICATION_NEWER_NO_SIGNAL_SECTIONS`.

Even `BOUND_AND_LOCALIZED` is not called eligible. Evidence class, materiality,
editorial authorization and other release law remain separate project-owned premises.

## Field hypothesis

On the base snapshot:

- the current material Story supply is roughly 60 hours old;
- ARB's sanitized 2026-09-17 published edition is much newer and is already present in
  `corpus/editions/` and `release-src/data/editions/`;
- that edition contains six numbered investigating/monitoring sections;
- the edition projection has no `related_brief_ids` for those six sections;
- ARB native-edition transport is keyed to canonical development identities, not these
  edition-section documents.

Therefore the expected field state is
`UPSTREAM_PUBLICATION_NEWER_UNBOUND`, not “fresh candidate available” and not “Pages
must block.”

## Why this matters to Proof Spine

This is a real coherent-cut boundary:

```text
downstream Story age
        +
upstream public publication age
        +
representation / native-edition admissibility
        ↓
truthful freshness diagnosis
```

A health red cannot be promoted into an action gate merely because the action is nearby.
The observer exists to stop that causal laundering while exposing the actual capability
gap if the field hypothesis survives execution.

No production workflow consumes this result. The experiment workflow has read-only
contents permission and uploads only the public-safe receipt.
