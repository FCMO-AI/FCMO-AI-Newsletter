# FCMO AI Newsletter — prelaunch integration baseline

This branch is the integration point for the final prelaunch publication experience. It must not be treated as launch approval. `main` and the GitHub Pages deployment remain gated until an explicit release decision.

## Product model

FCMO AI Newsletter is both:

1. a fast, human-readable evidence-first AI publication; and
2. a persistent research record that humans and software agents can inspect deeply without reconstructing meaning from presentation markup.

The public experience therefore has three layers:

- **Front page / Signal Field:** editorial prioritization and visual orientation over the current corpus.
- **Research memory:** dossiers, desks, topics, organizations, chronology, frozen editions, related work, corrections and open evidence gaps.
- **Machine surface:** stable `FCMO-<12 uppercase hex>` identifiers, deterministic static data files, per-brief dossiers and a browser-local query interface.

## Canonical visual direction

The final prelaunch direction is the **Signal Field** system:

- warm ivory field;
- near-black typography and rules;
- sparse FCMO orange as the active signal color;
- mixed sans/serif editorial typography;
- generous negative space;
- structurally distinct pages rather than one repeated card template;
- dark treatment reserved for deep inspection / machine-oriented surfaces rather than the whole publication;
- relevant first-party, paper or project imagery when it genuinely adds information, with an embedded FCMO editorial fallback when a suitable source image is absent or fails to load.

The caret mark remains part of the FCMO AI visual language.

## Epistemic contract

The publication must preserve these as separate concepts:

- claim label (`DEMONSTRATED`, `CLAIMED`, `INFERRED`);
- evidence class;
- confidence/support state;
- importance/consequence if true;
- limitations;
- contradictory evidence;
- open evidence gaps.

A visually prominent or potentially important item must never be presented as better verified merely because its possible consequence is large.

Frozen publication editions are also distinct from the broader research chronology. A development date does not imply that FCMO published an edition on that date.

## Machine contract

The recovered final machine surface supports stable IDs and deterministic queries over the same sanitized public state used by the human publication. The final prelaunch bundle includes:

- `agent.json`;
- `llms.txt` and `llms-full.txt`;
- `data/site-manifest.json`;
- `data/developments.json` and `.jsonl`;
- `data/search.json` and `.jsonl`;
- `data/briefs/<FCMO-ID>.json`;
- `data/relationships.json`;
- `data/publication-memory.json`;
- `data/editions/<YYYY-MM-DD>.json`;
- `data/topics.json`;
- `data/organizations.json`;
- `data/media.json`;
- JSON Feed and RSS.

The browser workbench is a convenience layer over static public data, not a hidden server API. Non-browser agents should prefer the file-backed objects.

## Recovered QA receipts

Two late prelaunch lines were recovered:

### Full interactive publication bundle

- 22 canonical research briefs.
- 11 publication routes audited at desktop and mobile sizes.
- All 22 briefs audited at desktop and mobile sizes.
- 66 browser renders total.
- 0 route-overflow failures.
- 0 brief failures.
- 0 JavaScript errors.
- Agent query surface passed search, gap, brief, schema, stats, resolve, source, filtered-search, projection and document tests.
- 43-file deployable static bundle passed privacy scanning, JSON/JSONL parsing and RSS validation.

### Final Signal Field v4 visual candidate

- 22 canonical records and 6 publication documents.
- 31 routes tested across 1440×1000 and 390×844.
- 62 route/viewport checks.
- 0 JavaScript failures.
- 0 document-overflow failures.
- No visible text below the 9px audit threshold.
- Manual desktop/mobile review covered all major routes and all 22 briefs.
- Story-media policy in this final pass: 14 vetted real/source-preferred selections and 8 embedded editorial fallbacks, with deterministic fallback on remote-image failure.
- Final visual QA status: PASS.

## Integration rule

The final publication should combine the **Signal Field v4 visual candidate** with the **full interactive machine/data contract**. Do not regress to the older all-dark cyan/violet presentation layer, and do not throw away the richer machine surface merely because the later visual pass is more refined.

Before `main` can be considered release-ready:

1. synchronize the final Signal Field document into the deployable `site/` tree;
2. synchronize the recovered machine/data bundle;
3. update the Pages build/validation workflow so it validates the final Signal Field contract rather than re-theming it into the older dark presentation;
4. reconcile remote sourced-story imagery with the privacy and publication validation rules;
5. rerun route, mobile, JavaScript, data-integrity, privacy and feed validation on the repository-built artifact;
6. present the resulting candidate for explicit launch approval.

No merge to `main`, public visibility change, or go-live step is implied by work on this branch.