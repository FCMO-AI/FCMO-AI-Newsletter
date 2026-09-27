# FCMO publication design v2

This is the shared visual and navigation contract for the Group landing, Newsletter, and FCMO AI technical paper. The product names are provisional pending O-8; change `PRODUCT_NAMES` in `tools/paper/routes.py` to rename them. The technical section front is `diario/` in every locale. Locale roots remain the FCMO Group landing; story, archive, edition, topic, organization, feed and sitemap routes retain their paths. `front.html` is the explicit legacy technical-front redirect in each locale.

## Brand zones and technical exposure

| Zone | Identity | Gradient | Purpose |
| --- | --- | --- | --- |
| Site root | FCMO Group | T0 with one FCMO AI T2/T3 depth well | Orient first-time readers toward Javier's letter or Matías's technical paper. |
| Newsletter, letters, beginner path and subscription | FCMO Group; Javier's fCMO identity where his voice is used | T0/T1 | Explain in human terms; give a clear entry and next step. |
| Technical daily paper | FCMO AI | T1 base, T2/T3 evidence and benchmark wells | Show what changed, what evidence supports, and what remains uncertain. |

Navigation toward mechanism may darken; navigation toward explanation may lighten. A dark well uses Ink as a structural field, Bone as reading light, restrained Mêtis signal, and actual evidence. A reverse Bone plate inside a dark technical surface is for explanations and limits. Never use darkness as generic technology theatre.

## Canonical tokens

`design/tokens.json` contains the values; `design/build_css.py` produces the stylesheet. FCMO Group v4.1: Ink `#0A0A0A`, Bone `#F2EFE8`, Stone `#8A857C`, Fog `#D9D5CC`, Rule DK `#2A2A28`, Body `#3A3A38`. FCMO AI v0.2: the shared Ink and Bone plus Mêtis `#F05A28`, Foundry `#BB5E4A`, Living `#73875A`, Intelligence `#5B7C93`. Accent colors identify intervention or real semantic states; they are not default body text. The existing darker text variant of Mêtis is used on Bone to meet contrast. Group display uses Inter Tight; AI display uses contemporary Inter Tight, serif for longer reading and inscription, and mono for data/state. Source files: Hub identity `readable/01_FCMO_Group_Identity_System_v4.1.txt`, `readable/03_FCMO_AI_Identity_System_v0.2.txt`, and `FCMO_TECHNICAL_EXPOSURE_GRADIENT_v0.1.md`. The [gradient visual reference](site-src/assets/brand/technical-exposure-reference.webp) is a review aid, not reader artwork.

## Scale and layout

Base body 18px, small 14px, metadata 12px, deck 20px. Display titles use fluid steps from 40px to 88px; dense story headlines step down according to measured title length. Use an eight point rhythm: 4, 8, 12, 16, 24, 32, 48, 64px. Main page measure is 80rem; long-form reading measure is 43rem. A wide two-column editorial front becomes one column below 850px; cards become one column below 520px. Maintain 16px outer gutters on narrow viewports, visible focus, no horizontal overflow, and a stable media aspect ratio.

## Component contract

| Component | Job and minimum behavior |
| --- | --- |
| Header and zone switch | FCMO Group and FCMO AI appear on every page; active zone is announced, search is always present. |
| Breadcrumbs | Home, technical section where relevant, current page; omit at locale roots. |
| Lead, standard, compact story cards | Lead holds artwork, title, deck, date and evidence context; standard adds the same orientation in a row; compact is for related or ranked lists. |
| Edition strip | Date, edition state and adjacent edition navigation. |
| Topic chip | Short linked taxonomy label, never a dead badge. |
| Glossary tooltip | Native-language plain definition, keyboard focus, and link to full glossary entry where available. |
| Evidence/benchmark well | Dark T2/T3 panel for source, metric, comparison, scope and limitation; reverse Bone plate for explanatory prose. |
| Subscribe block slot | `subscribe_block(zone, locale)` from `tools/paper/templates/subscribe.py`; account and delivery truth stay with the subscription lane. |
| Footer | Both brands, legal, methods, corrections, status and feeds. |
| Empty state | Say what is absent, why the surface still matters, and where to go next. |
| 404 | Localized return links to the Group root, technical front and search. |

Images should be deterministic data-driven SVG generated from published story, topic, organization or benchmark data. Preserve the existing Qwen3.8 Flash lead treatment and elevate it through the technical well. GPT illustration is reserved for a small number of section fronts, with editorial review and provenance. No stock photo, fake screenshot or generic AI imagery. An image never substitutes for a source citation.

## Page blueprints for p1 and p2

| Type | Opening | Body | Next step |
| --- | --- | --- | --- |
| Group landing | Human promise and two unambiguous routes | Javier letter/empty state, then FCMO AI depth well with lead and top stories | Start here, technical edition, subscription options |
| Newsletter front/letter | Human claim and author/date | Letter with a useful example and plain-language glossary | Next letter, beginner guide, subscription |
| Beginner guide | The reader's question | Short sections, definitions, one worked example | Related guide and technical source |
| Technical front | Latest lead and edition state | Top stories, beat paths, evidence signals | Today's edition and archive |
| Story | Localized headline, deck, byline, date and evidence state | What changed, why it matters, claims, limitations, source trail | Related stories, topic, previous/next in edition |
| Edition | Date and coverage summary | Ordered stories with clear ranking and beat labels | Previous/next edition |
| Archive, topic, organization | Scope, count and latest date | Useful filters and story cards | Neighboring topic or archive |
| Method/about/status | Clear question and current answer | Process, limitations or real operational state | Specific route to inspect or act |
| Search | Search field immediately available | Results with context and honest empty state | Refine or browse beats |
| Subscribe | What arrives and what is currently active | Consent, language and privacy details | Confirmed signup or feeds |
| 404 | Clear error in each locale | Three route options | Home, technical front, search |

Every page must answer what it is, why it matters and where to go next. All interactive elements need keyboard access and discernible names; reduced-motion preferences disable nonessential motion. Non-English prose comes from committed editorial sources, never a silent view-time translation.
