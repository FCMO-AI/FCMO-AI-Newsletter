# FCMO AI Newsletter media policy

## Principle

A discoverable image is not automatically a publishable image.

The autonomous Visual Desk may inspect cited public source pages for candidate visuals, but discovery or Open Graph metadata alone never proves reuse rights. A candidate crosses into the publication only when its reuse basis is machine-verifiable under the rules in `tools/visual_desk.py`. Otherwise the desk publishes an original FCMO explainer instead.

## Publication order

For a story-specific visual, prefer:

1. a source visual carrying a machine-verifiable permissive Creative Commons or public-domain declaration;
2. an FCMO-owned explanatory chart or diagram derived from public facts;
3. a deterministic FCMO-owned editorial graphic.

The newspaper must not hotlink or republish an attractive third-party image merely because a public page, search result, or social metadata exposed it.

## Rights receipt

Every row written to `release-src/data/media.json` must use one of the current publication modes:

- `licensed_source` — `sourced=true`, `rights_state=PERMISSIVE_LICENSE`, plus `image_url`, `source_page`, `license_url`, `reuse_basis`, and `credit`. The `license_url` itself must match a recognized permissive Creative Commons/public-domain declaration.
- `fcmo_explainer` — `sourced=false`, `generated=true`, `rights_state=FCMO_OWNED`, `evidence_image=false`, and a local asset under `site/assets/story-media/`.

`tools/visual_desk.py` validates the complete media set before replacing the canonical media manifest. The IDs must match the current brief IDs exactly; duplicate, missing, unsupported, or unverifiable rows fail closed.

## Existing media

There is no autonomous legacy allowlist. Historical media without the current verifiable contract is not grandfathered into new publication runs: the desk must rediscover a valid permissive license or replace the image with an FCMO-owned explainer. This keeps migration debt from becoming a permanent approval mechanism.

## FCMO-owned fallback

When no rights-proven source image exists, the Visual Desk generates a deterministic local SVG that communicates the story title, desk, evidence class and impact score.

The generated SVG is algorithmic editorial design, **not documentary evidence**. Its public record states `evidence_image=false`. If a future generative-image system is introduced, its provenance must be explicit and it must never depict a synthetic event or person as if the asset were source evidence.

## Failure semantics

A media-rights failure changes the visual choice, not the factual publication. The correct recovery is to use FCMO-owned explanatory media, never to weaken the rights gate.

<!-- Footnote: this policy deliberately documents the schema currently enforced by visual_desk.py rather than reviving the superseded PR #13 legacy modes/allowlist. That keeps documentation and executable truth aligned. -->
