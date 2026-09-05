# FCMO AI Newsletter media policy

## Principle

A discoverable image is not automatically a publishable image.

The autonomous Visual Desk may search public source pages for candidate visuals, but discovery alone never proves reuse rights. Unverified candidates remain in the ephemeral `newsroom-work/` quarantine and are never staged by the refresh workflow.

## Publication order

For a story-specific visual, prefer:

1. a first-party figure or press asset with an explicit compatible reuse license;
2. CC BY / CC0 / public-domain material with the required attribution;
3. an FCMO-owned explanatory chart/diagram derived from public facts;
4. a deterministic FCMO-owned editorial graphic.

The newspaper must not hotlink or republish an attractive third-party image merely because it appeared in search or Open Graph metadata.

## Rights receipt

New externally sourced imagery must state a recognized `rights_state`, credit and license URL. The current accepted states are:

- `CC_BY`
- `CC0`
- `PUBLIC_DOMAIN`
- `FIRST_PARTY_REUSE_LICENSE`
- `FCMO_OWNED`

Existing sourced imagery predating this contract is frozen in `config/media_legacy_allowlist.json` for migration only. The autonomous Visual Desk must never add a new ID to that list. Those historical decisions should be re-audited independently over time rather than treated as evidence for future reuse.

## FCMO-owned fallback

When no rights-proven story image exists, `tools/build_visual_desk.py` generates a deterministic local SVG that communicates the story title, desk, evidence class and impact score. This is preferable to publishing an unlicensed image and more informative than a generic stock fallback.

The generated SVG is algorithmic editorial design, not simulated photographic evidence. If a future generative-image system is used, its records must state that provenance explicitly and must never depict a synthetic event/person as documentary evidence.

## Fail-closed rule

`tools/validate_media_rights.py` blocks any new sourced asset without an approved rights state. A rights failure changes the visual choice, not the factual publication: use FCMO-owned explanatory media instead of weakening the rights gate.
