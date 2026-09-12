# FCMO AI Newsletter — agent operating contract

## Parent doctrine

Before material work, read **`FCMO_AGI_ENGINEERING_OPERATIONS_STANDARD.md`**. It is the universal parent doctrine for agent behavior in this repository. For user-facing communication, the delegated v1 discipline is pinned locally at **`COMMUNICATION_SURFACE_INTELLIGENCE_STANDARD.md`**.

In the pinned v1 text, **Prime Directive** is shorthand for Section 0's governing aim: seek the maximum justified real outcome under reality, legitimate authority, evidence, consequence, actual capability, and real constraints. It creates no extra publication authority.

This contract adapts FCMO v1 to the Newsletter without replacing the publication system that already works.

## Canonical product objective

Read and obey **`PRODUCT_GOAL.md`**. It defines the Newsletter-specific target for this repository and future Newsletter work: operate the real production newspaper, not a demo or one-off pipeline. Reliability, autonomous daily operation, reader-visible production truth, evidence integrity, current-day / previous-day freshness, fail-closed recovery, and repeated end-to-end proof take priority over ornamental features.

A build, commit, configured schedule, or deployment response is not sufficient evidence of product success when the promised outcome is the live newspaper. The reader-visible production surface and its freshness must be verified at the appropriate boundary.

## Required orientation

Read the smallest relevant set, starting with:

1. `FCMO_AGI_ENGINEERING_OPERATIONS_STANDARD.md`;
2. `PRODUCT_GOAL.md` — canonical production/reliability/freshness objective;
3. `COMMUNICATION_SURFACE_INTELLIGENCE_STANDARD.md` when user-facing communication or publication copy is in scope;
4. `README.md` — product/publication identity and build model;
5. `HANDOFF.md` — current operational truth, verified defects/fixes, test commands, and known traps;
6. `PUBLICATION_POLICY.md` — public/private boundary;
7. `LOCALIZATION.md` when reader-facing language or translation is in scope;
8. `LEGAL_REQUIREMENTS.md`, `ATTRIBUTION.md`, `CONTENT_LICENSE.md`, and `COPYRIGHT.md` when legal/attribution/licensing surfaces are touched;
9. `READY_TO_PUBLISH.md` and `release-overlay/final/manifest.json` for release identity;
10. relevant tests, workflows, generator code, and the actual rendered publication for the work at hand.

Do not reread every document merely because it exists. Retrieve deeper context when the task actually needs it.

## Local doctrine that remains binding

The FCMO parent does **not** replace these proven Newsletter mechanisms:

- deterministic, fail-closed publication;
- sanitized ARB → Newsletter release boundary;
- no raw/private ARB material in the public repository or publication;
- English as canonical semantic source with curated `es-419` and `zh-Hans` source-controlled presentation;
- no silent page-view machine translation;
- release-overlay/hash integrity and the established six-gate release verification;
- legal, copyright, attribution, privacy, and public-surface rules;
- final-form browser/DOM inspection for visual and localization claims;
- existing generator/oracle lessons recorded in `HANDOFF.md`.

A privacy, localization, legal, or release-integrity gate must not be weakened merely to make deployment green.

## How FCMO v1 changes behavior here

- Challenge a weak implementation method when a materially better one exists, but do not manufacture publication authority or bypass policy.
- Prefer the **most supported causal change**. A correct fix may be broader than the reported symptom; unrelated redesign still has to earn its release risk.
- Treat tests as evidence, not reality by status. When the promised result is visual or user-facing, render and inspect the actual publication.
- Use Practical Mode for routine maintenance. Use Frontier Mode only when a strategic publication, research-interface, or architecture problem justifies it.
- Resolve ordinary technical uncertainty autonomously through code inspection, controlled tests, browser inspection, and reproducible experiments before escalating to a human.
- Preserve exact evidence boundaries: build success does not imply deployment success; generated translation does not imply curated approval; an attempted external effect is not confirmed state.

## Completion

A change is done when the promised public/software outcome is verified at the appropriate layer, repository truth is coherent, and no required release/security/localization/legal gate remains unresolved.

For Newsletter product work, also apply the stronger completion standard in `PRODUCT_GOAL.md`: repeated autonomous operation, freshness, and reader-visible production correctness are first-class properties, not optional polish.

If an external prerequisite such as a secret, organization billing, or platform permission is unavailable, complete every blocker-independent lane, state the exact boundary, and leave a continuation-ready handoff.

## Communication

Follow the pinned `COMMUNICATION_SURFACE_INTELLIGENCE_STANDARD.md`. Keep internal tools, debug traces, and orchestration off the user-facing surface. Report the real outcome, decisive evidence, and any material remaining boundary. Public copy should follow the product's own editorial voice rather than sounding like an agent-control protocol.
