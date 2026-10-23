# FCMO publication design v2 (c6, single palette)

This is the shared visual, navigation and palette contract for FCMO AI, the company's news and strategy service. FCMO and fCMO are one identity (see `identity/README.md` in the Agent Hub). The site presents one publication, FCMO AI: no product zones, no separate letters or technical sections, no second palette. Routes, feeds and the 404 follow `tools/paper/routes.py` and `tools/paper/redirects.py`.

## One palette

Every colour comes from `design/tokens.json`. `design/build_css.py` writes the token region at the top of `site-src/assets/css/paper.css`; the hand-written stylesheet uses no other colour value.

| Role | Token | Hex | Use |
| --- | --- | --- | --- |
| Reading ground | `bone` | `#F2EFE8` | Page background and all body text on light surfaces. |
| Paper | `paper` | `#FBF9F4` | Raised panels on bone (search, pending states). |
| Ink | `ink` | `#0A0A0A` | Text, rules, the solid evidence sample, dark surfaces. |
| Ink soft | `ink_soft` | `#34322F` | Secondary body text. |
| Muted | `muted` | `#5E5A53` | Metadata and captions (AA on bone). |
| Line | `line` / `line_strong` | `#C9C2B6` / `#80786D` | Hairlines and dividers. |
| Mêtis | `metis` | `#F05A28` | Signal only: the symbol, focus ring, method band, kickers on ink. Never body text on bone. |
| Mêtis text | `metis_text` | `#A9340E` | Mêtis used as text on bone (AA). |
| Oxblood | `oxblood` | `#8A1E22` | «Not established» only: the dashed outline sample and the «What we still don't know» box. AA on bone. |
| Chrome | `chrome`, `chrome_2`, `chrome_3`, `chrome_line`, `chrome_mute`, `chrome_text`, `metis_soft` | `#0D0D0F` to `#F7B499` | Dark chrome for the cover, story cover, top bar, tab bar, Evidence Record and the data hero. Reading never sits on chrome. |
| Status | `warning_bg/text`, `danger_bg/text`, `success_text` | see tokens | Edition and freshness states (`--ok`, `--warn`, `--bad` alias them). |

The FCMO AI v0.2 product hues (`foundry`, `living`, `intelligence`) are not part of the palette. They survive only as the legacy segment markers in `paper.css` and retire with those markers. The `brands.group` and `brands.ai` colour sets are removed: there is one brand.

Rules:
- Colour never carries meaning alone. Evidence states always carry a shape and a word.
- Contrast is AA (4.5:1 for text) on every declared pair. `design/check_contrast.py` checks them; a new pair is added there, never waived.
- Dark chrome is structural, never a backdrop behind a headline. Plates sit beside a headline (desktop) or below it (phone), not behind it.

## Evidence grammar

| State | Sample | Word |
| --- | --- | --- |
| Established / Shown | Solid Ink block | «Shown» (zh: 已展示) |
| Claimed | Diagonal hatch in Ink, no fill | «Claimed» (zh: 仅声称) |
| Not established | Dashed Oxblood outline, Bone inside | «Not established» (zh: 尚未确立) |

The hatch appears only on the sample. Text always sits on a flat ground.

## Type

- Display: Inter Tight, weight 900 with -0.035em tracking for titles; 600 for UI.
- Reading: Source Serif 4 for dek and body, 17 to 19 px, 66 ch measure.
- Technical: JetBrains Mono, 12 px, caps, for kickers, labels and figures.
- zh-Hans: system sans for headlines (PingFang SC, Noto Sans CJK SC, Microsoft YaHei); body 17 px / 1.85; no caps, no tracking, `overflow-wrap:anywhere`.
- Scale: hero `clamp(2.1rem, 6vw, 4.9rem)`, section 3.2 rem, card 1.28 rem. Numerals in lists use `white-space:nowrap` with a fixed width.

## Grid and frame

- Frame: `--l-grid-max` (1360 px) with `--l-pad` (`clamp(16px, 4vw, 56px)`) on both sides. The page shell takes this frame. The landing main spans the viewport and holds its content in the same frame.
- Front: hero 7/5, cards 12 to 4+4+4. Story: 200 px / fluid / 320 px rail.
- Breakpoints: 1100 px (single column) and 760 px (phone: tab bar; compact evidence record before the body).
- Touch targets at least 44 px. Eight-point spacing.

## Components

The current class inventory is the comment at the top of `paper.css`. Classes outside that inventory are legacy and must not be added.

- Links: `a.story-card`, `a.plate-card` and `a.card-link` carry no underline; the title carries the link affordance.
- Data hero: always dark (bone text on ink) on every surface, including the story rail and the landing lead. Print is the only exception.
- Landing: the `page-landing` main is full width; its content is capped at the 1360 frame.
- Images: deterministic procedural plates (`tools/paper/plates.py`) with no text inside; fixed slots 16:10, 16:9 and 1200 x 630; alt text is decorative unless it names real content.
- Stylesheet budget: `paper.css` at most 112 KB (`PAPER_LIMIT` in `design/build_css.py`); the page budget is enforced by `tools/gates/size_budget.py`.

## Accessibility and motion

Visible focus (3 px Mêtis outline), keyboard access to every control, discernible names, no horizontal overflow at 390 px, stable media aspect ratios (CLS 0). Reduced motion disables nonessential motion. Non-English prose comes from committed editorial sources, never a silent view-time translation.

## Open items

- The `--group-*` and `--ai-*` aliases still sit in the generated token region of `paper.css`, because `design/build_css.py` (`legacy_alias_root`) emits them. Nothing in the hand-written stylesheet references them any more. Dropping them needs that file's owner.
- zh-Hans headline copy and the evidence words need native review before public launch.
