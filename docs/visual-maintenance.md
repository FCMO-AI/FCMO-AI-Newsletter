# Visual maintenance — 2026-09-10

This release line is a **bug fix and mild visual refinement**, not a rollback and not a redesign of the publication model.

The first pass improved desktop viewport use with width-and-height-aware sizing, repaired two local thumbnail collision contexts, preserved the existing mobile reading model, and removed the reader-facing **FCMO Wire** control from the public interface. The separate backend **FCMO Newswire Bridge** ingestion workflow remains intentionally unchanged.

A same-day editorial-rhythm follow-up responds to production screenshots rather than changing the product concept. On desktop it restores stronger cover and lead-headline authority, redistributes the lead columns so the larger headline does not simply make the section taller, makes **What else matters now.** structurally read as one macro story + one secondary story + three quick signals, and compacts the footer back into a closing instrument rather than a second hero. No story copy is hidden or line-clamped to obtain the fit.

The responsive override is owned by `site/assets/` because `release-src/` is regenerated atomically by the newsroom ingest path. Keeping presentation CSS in the durable public base prevents the fix from disappearing on the next corpus refresh while preserving the generator fixed-point oracle.

Browser QA covers `390×844`, `1152×720`, `1280×720`, `1366×768`, `1440×900`, `1648×900`, and `1920×1080`. The permanent `tests/oraculos/verificar_layout.py` oracle checks horizontal overflow, desktop hero containment, Front Page and Chronology thumbnail/text collisions, cover/lead type authority, compact-footer bounds, the wide-desktop Front Page hierarchy, single-view section fit on standard desktops, JavaScript/blank-route failures, and absence of the retired reader-facing FCMO Wire surface. It also renders representative `es-419` and `zh-Hans` home views so the English geometry cannot pass while a native edition breaks.

<!-- Footnote: this note is intentionally small and operational. Its purpose is to make intentional visual evolution legible to future maintainers so it is not mistaken for accidental drift or reverted as a regression. -->
