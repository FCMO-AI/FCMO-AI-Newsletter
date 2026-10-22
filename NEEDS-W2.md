# NEEDS-W2 (lane W2, CSS cleanup; branch c6/W2 on c6/integration 356ca884b)

Outside W2 ownership, not done here:
1. design/build_css.py: legacy_alias_root() still emits --group-*/--ai-* inside the generated token region of paper.css. Nothing in the stylesheet references them now. Drop it in the owner's lane (the --check compares that region with token_region()).
2. design/build_css.py render(): the generator string still carries the old .landing-*/.technical-*/zone-switch rules (only its length check uses it). Remove them with item 1.
3. tools/paper/templates/landing.py still emits landing-intro, landing-feature, landing-record and landing-jump; their rules are kept. Delete them when L5 replaces the front markup.
4. build.py _story: the L6-wiring.patch paper.css hunk is applied here; its build.py hunk is not (L9 owns build.py).
5. Contract tests in tests/test_design_v2.py (W3): 9 failures remain, all contract assertions (diario/, cartas/, empieza/, suscribete/, page-front, language switch). Same count as the baseline.
6. Path: the brief names design/DESIGN_V2.md; the file lives at repo root DESIGN_V2.md and was updated there.

Decisions recorded:
- .page-shell takes the 1360 frame (--l-grid-max, --l-pad) instead of --page 80rem. The utility-bar/masthead/main-nav width rule is unchanged.
- .read-rail .data-hero keeps its dark ground. The L6 patch set background:none, which would have put bone text on bone.
- Off-palette literals in the hand-written CSS map to tokens: #C9C2B6 to var(--line), #5E5A53 to var(--muted), #CFC9BF to var(--chrome-text), #5D5953 to var(--line-strong); --ok/--warn/--bad to the status tokens.
- Story pages at 390 and 1440 were not re-screenshotted after the shell width change. Home at 390 and 1440 was checked (no overflow, no layout break). R1 reviews the rest.
