# Website legal, privacy, and publication requirements

This file is a publication contract for generated FCMO AI Newsletter editions. It defines the minimum public legal/disclosure surface and release boundary that must be preserved when `site/` is regenerated.

## Public-only publication boundary

This repository is a publication destination, not a working research environment. `site/` may contain only material intentionally prepared for public distribution.

A release must fail closed if validation is incomplete or uncertain. A failed release must leave the last known-good public site unchanged rather than publishing a partial build, fallback tree, or unreviewed source material.

Public releases must not contain operational credentials, private keys, personal mailbox addresses, private workspace paths, non-public project context, private source-control ancestry, or implementation metadata that is unnecessary for readers.

The public repository must not require a credential capable of reading a private research system. Publishing credentials, if used, should be narrowly scoped to writing this public repository only.

## Required public pages

Every complete public edition must expose clear links to:

- About / editorial method
- Feeds and public machine-readable data
- Privacy
- License
- Disclaimer
- Corrections

The information must remain easy to find from the publication navigation or footer.

## Required FCMO AI attribution

For FCMO AI leadership/direction sections, use this public order:

1. **Matías Peña Szőke** — Director, FCMO AI / Head of AI & Technology.
2. **Javier Castellanos Peña** — Founder, FCMO Group.

The site must not imply that Javier Castellanos Peña is an author of FCMO AI material solely because he founded the broader FCMO Group. Specific article or project bylines must follow actual contribution and rights rather than leadership ordering.

The functional titles above must not be presented as formally appointed corporate offices while FCMO is not a separate legal entity.

## Default public identity

The publication should identify itself as **FCMO AI Newsletter**, brought to readers by the FCMO Group. Internal research-system names, internal source-control identifiers, and operational publication mechanics are not part of the reader-facing identity.

## License presentation

The public License page must distinguish at least these categories:

- repository/software code: MIT License under the repository `LICENSE` notice;
- licensable original FCMO AI editorial content: CC BY 4.0 unless a more specific notice applies;
- third-party material: governed by its original rights and licenses;
- FCMO branding: not automatically licensed for reuse as a source identifier by the software or editorial-content licenses.

The public site must not claim that FCMO Group owns material merely because it is published under the FCMO brand.

## About-page identity

The About page should explain the editorial method without exposing private implementation details. It may describe evidence classes, confidence, importance, corrections, sources, and deterministic publication behavior, but it should not expose private workspace names, internal repository ancestry, internal control files, run state, or private operational paths.

## Privacy

The site should remain privacy-conscious by default. The generated pages must not intentionally add first-party advertising trackers, behavioral analytics, account systems, subscription forms, comments, cookies, or embedded third-party media without first updating `legal/PRIVACY.md` and the generated public privacy notice.

Hosting and network providers may process routine request metadata under their own policies. The publication must not promise that infrastructure-level logging does not exist when that cannot be guaranteed.

## Editorial transparency

Potential importance, evidence quality, and confidence must remain conceptually separate. Preliminary or disputed findings should not be presented as confirmed merely because their possible impact is large.

Material limitations, contradictions, uncertainty, and corrections should remain visible when they affect interpretation. Historical editions are snapshots and should not be silently rewritten to erase substantive changes in assessment.

## Sources and third-party rights

Where practical, research coverage should link to primary or otherwise authoritative sources. External links do not imply endorsement, sponsorship, partnership, or affiliation.

Third-party papers, articles, quotations, images, datasets, logos, trademarks, and other referenced material remain subject to their original rights and terms. Publication must not imply that the newsletter's open-content license grants rights it does not own.

## Release verification

Before the repository is made public or a new site snapshot is published, verify at minimum that:

1. the generated site is complete and internal links resolve;
2. only expected public paths and file types are present;
3. no symlinks, source-control metadata, credentials, personal mailbox addresses, or workspace paths are present in `site/`;
4. machine-readable JSON and JSONL files parse successfully;
5. required legal and disclosure pages exist;
6. public research pages use the public FCMO identifier namespace rather than an internal source-system namespace;
7. the public repository has no read path back into a private research system;
8. the public git history contains only intentionally public material and public-safe author metadata.

If any check is uncertain, do not publish.
