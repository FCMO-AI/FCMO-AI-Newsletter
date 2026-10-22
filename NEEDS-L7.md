# NEEDS from lane L7 (c6/L7)

Helpers I added in tools/paper/templates/pages.py, not yet called (their callers are outside my files):
- build.py (L9), corrections list (~line 755-767): replace the inline `<article class="correction">` with
  `pages.correction_row(catalog=catalog, title=..., note=..., date_iso=date, date_text=format_date(date, catalog),
  story_href=self._story_href(locale, story) (or the survivor/story page), correction_href=self._correction_href(locale, story),
  class_before=correction.get("class_before"), class_after=correction.get("class_after"), reason=...)`, and prefix the
  intro with `pages.corrections_intro(catalog, method_href=<method/>)`. The corpus has no before/after class fields today
  (4 corrections: kind, reason_code, text), so the class line prints only when both exist. Emitting them is a corpus/ingest need.
- build.py (L9), method page (`method_intro`, ~line 730): add `pages.method_order_section(catalog)` first. Text = `method.order_body`.
- build.py line ~798: suscribete title still reads "— fCMO + FCMO AI" (trips test_c6_one_fcmo); use "— FCMO AI". Also the
  404 and `subscription_tail` (newsletter.py, L6) still carry product wording.
- build.py: confirmed-state link now points to the front page (state_page no longer links to diario/).

Contract tension (not changed by me): tests/test_subscribe_v2.py asserts exactly two `subscribe-choice` items carrying the
configured product names ("Cartas de Javier", "FCMO AI Newsletter" from community/config/subscriptions.json) and
`ghost.membership == one_site`. I kept both green, so the block still lists two ways to follow, but under a single
heading "One publication. Follow it your way." with person-free descriptions. A cleaner single-text design needs the
integrator to approve a contract change to that test + config (rename product names, drop the person name).
tools/email_render.py (not mine) still brands the letter email "fCMO".
