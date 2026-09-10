# Visual maintenance — 2026-09-10

This release is a **bug fix and mild visual refinement**, not a rollback and not a redesign of the publication model.

It improves desktop viewport use with width-and-height-aware sizing, repairs two local thumbnail collision contexts, preserves the existing mobile reading model, and removes the reader-facing **FCMO Wire** control from the public interface. The separate backend **FCMO Newswire Bridge** ingestion workflow is intentionally unchanged.

The responsive override is owned by `site/assets/` because `release-src/` is regenerated atomically by the newsroom ingest path. Keeping presentation CSS in the durable public base prevents the fix from disappearing on the next corpus refresh while preserving the generator fixed-point oracle.

Browser QA covers `390×844`, `1152×720`, `1280×720`, `1366×768`, `1440×900`, and `1920×1080`. The permanent `tests/oraculos/verificar_layout.py` oracle checks horizontal overflow, desktop hero containment, Front Page and Chronology thumbnail/text collisions, expected reader copy, JavaScript/blank-route failures, and absence of the retired reader-facing FCMO Wire surface.

<!-- Footnote: this note is intentionally small and operational. Its purpose is to make the change legible to future maintainers so the new layout is not mistaken for accidental drift or reverted as a regression. -->
