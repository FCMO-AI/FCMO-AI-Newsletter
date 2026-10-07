# CR — isolate generator proof from committed release drift

**Date:** 2026-10-07  
**Scope:** `test_generador_deriva_y_crece` and the composed newsroom generator oracle.

## Problem

The old newsroom adapter compared the current sanitized corpus with the checked-in
`release-src/` tree and required downstream briefs, media receipts, and editions
to be present there. The Publication Desk can update `corpus/` on `main` before
the newsroom's next composition run updates `release-src/`. A merge-result CI
run therefore failed on a valid intermediate repository state, including the
Oct 7 corpus edition, even though the generator itself could produce it.

Refreshing `release-src/` in a PR only chased that moving target and changed
publication artifacts owned by the newsroom workflow.

## Change

The oracle now copies the checkout into a temporary repository, uses that
checkout's current sanitized corpus as its test corpus, and generates a fresh
`release-src/` baseline there at test time. The established oracle then checks
that the generator is idempotent, preserves prior stories, grows all discovery
surfaces for a synthetic story, and publishes/enumerates a synthetic next-day
edition. The edition fixture date is computed from the newest edition instead
of relying on a fixed historical date.

The proof no longer reads or compares against committed `release-src/`, search
indexes, publication memory, sitemap, `llms*.txt`, or release-overlay parts.
This keeps the generator behavior check independent from publication cadence
while retaining real current-corpus input and the growth/idempotence contract.

## Verification boundary

The separate repository publication and release checks continue to validate
their own inputs. This CR only changes the generator regression oracle; it does
not claim that an uncomposed corpus has already reached the reader-visible site.
