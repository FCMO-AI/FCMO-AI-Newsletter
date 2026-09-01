# FCMO AI Newsletter

**What actually matters in AI — carefully researched and curated by FCMO.**

This repository hosts the public FCMO AI Newsletter: a readable, evidence-conscious view of important developments across artificial intelligence research, models, systems, hardware, robotics, policy, and the broader AI ecosystem.

The publication is generated deterministically as static files. Public articles distinguish evidence quality, confidence, limitations, contradictions, and potential importance rather than treating every headline as equally established.

## Public publication model

- `site/` contains the generated public newsletter.
- GitHub Pages serves only the contents of `site/`.
- Publication is fail-closed: if a generated edition does not pass its publication checks, the last known-good public site remains unchanged.
- This repository contains public publication material only. It is not an internal research workspace.

## Editorial principles

FCMO AI Newsletter aims to be useful both to technically sophisticated readers and to curious readers who simply want to understand what is changing in AI and why it matters.

Potential impact and confidence are deliberately separated: a spectacular claim can be important *if true* while still being weakly supported, and an incremental result can be extremely well established without being field-changing.

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
