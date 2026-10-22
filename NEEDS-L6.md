# NEEDS from lane L6 (story layout)

Story assembly lives in `tools/paper/build.py` (`_story`) and CSS in `site-src/assets/css/paper.css`, neither owned by L6.
The L6 builders are in `reader.py`: `story_view`, `story_signals`, `evidence_record`, `brief20`, `claim_ledger`, `unknowns_box`, `sources_bar`, `jump_bar`, `topic_pair`, `machine_strip`.
Wiring + CSS patch (tested, not committed because of ownership): /srv/fcmo/agents/work/newsletter/c6-diseno/build/L6-wiring.patch
(`git apply`; touches build.py `_story` plus helper methods `_topic_pair`, `_machine_strip`, and appends CSS to paper.css).

- Mobile budget: oracle fits only with the L4 shell (56 px bar). With the legacy shell the first screen is ~330 px taller. Simulated with the shell hidden: 20 s ends at 759 px at 390 (en).
- plate_html is "" until L8 `plates.plate(...)`; pass it to `story_view(plate_html=...)`.
- `_facts` (build.py) still prints "Importance x/10", raw topic names and org chips: drop the importance rows (DIRECCION §3) and use `labels.topic.<slug>`.
- Existing contract tests kept green by design: `<article class="story-layout title-*">`, `<header class="story-header">` with plain `<h1>`, `data-hero` wrapper, `edition-neighbors`, `related-reading`, `story-taxonomy`, `<div class="story-body"><div class="brief"`.
- Unit remaining red are other lanes: shell strings (L4), routes (L9), hatch rules in legacy CSS (L1 cleanup), raw topic slugs (_facts).
- Technical layer is a closed `<details>`; jump link `#technical` does not open it (small script could).
