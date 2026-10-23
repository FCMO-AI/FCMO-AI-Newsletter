# paper.css component class inventory

Moved out of paper.css in c6 round 3 to keep the stylesheet under its byte cap. The classes are still the contract for the template lanes.

```
/* COMPONENT CLASS INVENTORY (c6, contract for the template lanes; classes are real and styled below).
   Surfaces/utility: surface-ink | surface-bone (set the palette; reading uses bone) · frame (max 1360, fluid padding) · block (vertical section) · block-head + block-title · rubric (+ rubric-accent) mono caps label.
   Shell (L4): topbar > frame.topbar-in > a.brandmark(.brandmark-sym) + nav.topnav (a[aria-current]) + nav.langsel (3 links, a[aria-current]) + a.btn-cta · nav.tabbar (5 links: Today, Archive, Search, Corrections, Subscribe; <=760px) · footbar (+ footbar-links, footbar-fine) · btn, btn-ghost.
   Evidence grammar: sample sample-shown|sample-claimed|sample-gap (never colour alone) · chip chip-shown|chip-claimed|chip-gap > .sample + .chip-word · evrow (+ evrow-grade, one per item: class word + sample, sources, gaps).
   Front (L5): cover > frame.cover-grid > .cover-main (rubric, h1.cover-title, p.cover-dek, evrow, .cover-actions) + .cover-side (.receipt, .plate) · receipt (receipt-title, dl dt/dd, .receipt-na on the "not established" row, .receipt-nums > div > b + span) · board (3-col grid) of plate-card (+ plate-card-wide full row; plate-card-body, -title, -dek) · method-band (method-band-title with em, band-trio > div > b, ul.band-counts > li > span) · format-filter (a[aria-current]) · ol.wire > li.wire-row (wire-date, wire-format, wire-title, wire-meta, evrow) · table.wire-table · ul.topic-tiles > li > a > b · trio (Corrections/Method/Status) · subscribe-block + ul.feeds.
   Plates: .plate[data-ratio="16:10"|"16:9"|"og"] fixed slots, holds inline svg or img (CLS 0).
   Story (L6): story-cover > frame.story-cover-grid (nav.crumbs, h1.story-title, evrow) + .plate · srcbar (SOURCES) · jumpbar (Claims/Sources/Gaps/Limits/Technical) · read-layout > read-toc + .read-body + .read-rail · read20 (3 cells, last .read20-na) · read-layer (details, long layers only) · ul.claims > li.claim > .claim-class(.chip-gap) + p · unknowns (unknowns-title) · mr (machine-readable strip) · pn (prev/next) · related (plate-card x3).
   Evidence Record (rail and lead note): er (er-title, er-grade > .er-grade-plate, ol.er-bar > li.er-seg-shown|er-seg-claimed|er-seg-gap, dl.er-legend, .er-counts > div > b + span, ul.er-in-story).
   Dark chrome only on cover, story-cover, topbar, tabbar, er. zh-Hans is handled by html[lang] variables (--c6-ui etc.), not per-component rules. */
```
