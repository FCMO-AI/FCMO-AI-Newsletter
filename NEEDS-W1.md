# NEEDS-W1 (wiring lane)

## For lane W2 (site-src/assets/css/paper.css)
Apply the CSS hunk of the L6 wiring patch ("c6 L6 story wiring" block, appended to paper.css) plus the L5 CSS items (drop legacy .landing-*, .technical-*, .page-landing, .page-shell width rules; text-decoration:none on link cards; dark-surface .data-hero; full-width main on landing). Measured with the hunk applied (not committed here): sources/brief-20s now pass at 390 for most pages, but at 390 'In 20 seconds' still ends at ~880-970 px (limit 844) in all 3 locales; axe color-contrast on home (all locales, 1-3 nodes at 390 and 1440) and the story hatching test (tests.test_c6_design_contract.test_c6_only_claimed_is_hatched: INFERRED, DISPUTED and unrated are hatched) are CSS.
Also: first-screen oracle fails at 1440 for /es/: lead h1 bottom 901 px vs 900.

## For lane L4 (layout.py)
axe serious label-content-name-mismatch (2 nodes per page, every locale): language switch links show 'ES' / '中文' but aria-label is 'Español' / '简体中文'; the accessible name must contain the visible text.

## For lane L2 / copy (i18n)
method.order_body (en/es-419/zh-Hans) still says importance first, recency second; front_order is 48 h tranches, then eligibility, importance, recency.

## Integrator
- Gate NO_MACHINE_PATHS fails on tracked NEEDS-L6.md (contains a server path). Remove or sanitize it before the gates can be green; gates 12-14 could not be reached.
- tests/test_c6_one_fcmo: test_c6_no_split_product_strings flags the word 'membership' in two story bodies ('membership inference' is real prose from the corpus); test_c6_no_raw_topic_slugs flags 'post-training' and 'long-context' as slugs but they are ordinary words in headlines. Both are oracle false positives; only the oracle owner can narrow them (anchored to topic chips/cards).
- Old-contract tests that now fail by design (DIRECCION section 4/6; not weakened here): test_v3_integration (route kind 'front' gone), test_paper_editorial_depth.test_front_method_and_status... (front-ledger on a front page that is now a redirect/landing), test_essay_build (es/cartas/ is a redirect stub), test_subscription_journey.test_real_builder_emits_subscription_states... ('site-header' class renamed by the c6 shell).
- tools/email_piece_render.py (not owned) still prints 'fCMO · <paper name>' as the letter-mail brand (line with letter-spacing:.14em), and tests/test_subscribe_v2.test_letter_preview asserts 'fCMO' in that HTML. Needs an approved contract change (test + email_piece_render). tools/paper/templates/essay.py:114 still brands by author ('fCMO / Javier', 'FCMO AI / Matias').
- Corpus has no class_before/class_after fields on corrections, so no class line prints (by design in pages.correction_row).
