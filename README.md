# FCMO AI Newsletter

**What actually matters in AI — carefully researched and curated by FCMO.**

**Publication:** https://fcmo-ai.github.io/FCMO-AI-Newsletter/

FCMO AI Newsletter is an evidence-conscious publication and public research corpus covering important developments across artificial intelligence research, models, systems, hardware, robotics, policy, and the broader AI ecosystem.

The publication separates evidence quality, confidence, limitations, contradictions, and potential importance rather than treating every headline as equally established. It is designed for quick human reading while preserving enough structured context for deeper research and software-agent use.

## Public publication model

The release is deterministic and fail-closed:

- `site/` is the checked-in public base tree.
- `release-overlay/final/` is the frozen, hash-verified Signal Field v4.1 English canonical release payload.
- `tools/apply_final_release.py` reconstructs the exact canonical publication candidate, validates its hashes and public-data contract, scans for credential/privacy leaks and unsafe remote executable dependencies, and writes a deterministic build manifest.
- `tools/apply_curated_i18n.py` validates the committed curated locale packs and applies native Spanish and Simplified Chinese presentation only after the canonical English release passes its integrity gate.
- `.github/workflows/pages.yml` assembles that validated candidate into `publish/` and deploys only that directory to GitHub Pages.
- A failed release or localization validation prevents deployment rather than publishing a partial, drifted, or machine-translated edition.
- No private research workspace, private credentials, or non-public operational state is required to build the public release.

`data/relationships.json` and `data/relationships.jsonl` are equivalent public surfaces: the JSON is an array and the JSONL is one identical object per line.
They must contain the same objects in the same order; clients may choose either representation.

The release identity and final publication checklist are recorded in `READY_TO_PUBLISH.md` and `release-overlay/final/manifest.json`.

## Native languages

FCMO AI Newsletter natively supports exactly three publication languages:

- **English (`en`)** — canonical semantic source;
- **Latin American Spanish (`es-419`)** — curated, source-controlled translation;
- **Simplified Chinese (`zh-Hans`)** — curated, source-controlled translation.

Every current public news record has a committed Spanish and Chinese translation of its reader-facing title, summary, and editorial consequence. The selector resolves an explicit `?lang=` request first, then a saved manual choice, then browser language, with English as the final fallback.

The site does **not** call a translation service or generative model at page-view time. Missing translations are release defects rather than permission to silently machine-translate. English remains directly selectable as the authority-bearing source. The deeper technical/evidence record can therefore preserve its canonical wording and identifiers even when the reader is using a curated translated edition.

The complete source-control, curation, provenance, and validation contract is documented in [`LOCALIZATION.md`](LOCALIZATION.md).

## Human and agent surfaces

The Signal Field interface provides the front page, research library, desks, editions, chronology, topics, organizations, search, and deep dossiers.

The same sanitized public corpus is exposed in machine-readable form through stable `FCMO-<12 uppercase hex>` identifiers, per-brief JSON dossiers, indexes, feeds, publication memory, relationship data, `agent.json`, `llms.txt`, and `llms-full.txt`.

Potential impact and confidence are deliberately separate: a spectacular claim can be important *if true* while still being weakly supported, and an incremental result can be extremely well established without being field-changing.

## FCMO AI leadership and attribution

FCMO AI material uses contribution-based attribution. Organizational rank does not substitute for authorship.

For FCMO AI projects and publications, the canonical public order is:

1. **Matías Peña Szőke** — Director, FCMO AI / Head of AI & Technology.
2. **Javier Castellanos Peña** — Founder, FCMO Group.

FCMO Group is the broader project and public-facing umbrella brand. Javier's founder role is recognized at that level; it does not imply authorship of FCMO AI work he did not materially create or acquire rights to.

The titles above are functional public-facing descriptions rather than representations of formally appointed corporate offices while FCMO is not a separate legal entity.

See `ATTRIBUTION.md` for the canonical attribution rules used by this repository and its generated publication.

## Licensing and legal scaffold

This repository uses a mixed-license model so software and editorial material are treated appropriately:

- **Software code:** MIT License — see `LICENSE`. The default repository notice is `Copyright (c) 2026 Matías Peña Szőke and contributors`.
- **Original FCMO AI editorial content:** Creative Commons Attribution 4.0 International (CC BY 4.0) when the project has authority to license it and no more specific notice applies — see `CONTENT_LICENSE.md`.
- **Third-party material:** remains subject to its original copyright, license, trademark, and other applicable rights.
- **FCMO branding:** the FCMO Group, FCMO AI, and FCMO AI Newsletter names, logos, and visual identity are not licensed for reuse merely because repository code or editorial text is openly licensed.

The website legal/disclosure scaffold is defined in `LEGAL_REQUIREMENTS.md`, with baseline public-language templates in `legal/PRIVACY.md` and `legal/DISCLAIMER.md`.

Generated editions expose compact links for About, Feeds & data, Privacy, License, and Disclaimer. Primary and authoritative source links are provided from the relevant research pages and editions.
