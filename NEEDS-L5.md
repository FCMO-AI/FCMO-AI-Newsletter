# NEEDS from lane L5 (front page)

1. build.py (L9): pass the new context to the landing. Exact change, in `_front`, final `render_landing(...)` call:
   `..., feature=feature, front=front_context(order=order, base=self.base))` and import
   `front_context` next to `render` from `templates.landing` (both import branches). Without it the front shows only the cover (old contract kept).
2. paper.css (L1): delete legacy `.landing-*`, `.technical-*`, `.page-landing` rules (they restyle `section.landing-intro`, which tests/test_landing_feature.py requires). Add `text-decoration:none` for `.cover-title a, .wire-title a, .trio a, .topic-tiles a, .plate-card`; adapt `.data-hero` (inside `.cover-glance`) to the dark surface; `.cover-foot` needs no rule. Main must be full width on the landing (no `.page-shell` width cap).
3. plates (L8): `plate()` result should carry `motif` (agents|monitoring|security|reasoning|voice|neutral) next to `svg`; landing builds the alt from `plate.alt_*` keys. The wrapper div sets role=img, so the svg can be aria-hidden.
4. Method page (L7): item class rule is in `front_plan.evidence_class` (Shown only for confirmed/strongly_supported/supported; Claimed otherwise if rated or has claims; else Not established). Real order rule is `front_order`: 48 h freshness tranches, then eligibility, importance, recency; `method.order_body` ("importance first, recency second") does not match it, so L2/L7 should reword it.
5. subscribe (L7): `subscribe_block("all", code)` is embedded and prints its own heading and product copy; a headless variant is needed.
6. Contract conflict: tests/test_design_v2.py asserts landing `id="letters"`, `id="start-here"`, `id="technical"`, `diario/`, `cartas/`, `empieza/` links and `landing-record` (old two-product front). They contradict DIRECCION §4/§6; the integrator must update them with the L9 redirects. Not touched here.
7. First-screen oracle at 1440: lead h1 bottom is 901 with the OLD header (about 215 px); the L4 one-row header (56 px) should clear it. Re-run after L4 merges.
