# A3 integration needs

These changes are outside WP-A3 ownership and were not made here.

1. **WP-A4 / `pages.yml`: wire the OG stage into the publication build.** Run
   `tools/paper/og_image.py` into a temporary directory, then pass that directory
   to `tools/paper/build.py --og-source <dir>`. The SSG copies the validated cards
   to `publish/og/` and emits their PNG URLs in OG and JSON-LD metadata. Without
   this flag it deliberately keeps the existing local explainer as a valid
   fallback image.
2. **WP-C1 / approved legal copy:** provide the finalized locale content owned by
   `site-src/content/legal/**` and align its file interface with the SSG during
   integration. Until then, the generated privacy, license, and disclaimer routes
   state that approved legal copy is pending, and subscription remains inactive.
3. **Integration runner with browser/socket permission:** run the A3c PNG command,
   the browser harness, and the required `shot.mjs` matrix. This sandbox refuses
   both loopback sockets and Chromium startup, so no defensible screenshot sheet
   can be produced here. The operator visual decision O-14 therefore remains open.
