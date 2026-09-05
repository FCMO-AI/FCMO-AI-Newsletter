(() => {
  'use strict';
  const root = document.querySelector('[data-search-root]');
  if (!root) return;
  const input = root.querySelector('#fcmo-search');
  const evidence = root.querySelector('[data-filter="evidence"]');
  const impact = root.querySelector('[data-filter="impact"]');
  const count = root.querySelector('[data-search-count]');
  const results = root.querySelector('[data-search-results]');
  const source = root.dataset.source;
  let rows = [];

  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const storyHref = id => `/FCMO-AI-Newsletter/news/en/STORY-${String(id || '').replace(/^FCMO-/, '')}.html`;
  const haystack = row => [row.title,row.summary,row.why_it_matters,row.mechanism,...(row.topics||[]),...(row.organizations||[])].join(' ').toLowerCase();
  const score = row => Number(row.importance_effective_score ?? row.importance_score ?? 0);
  const render = row => `<article class="index-item"><div class="item-meta">${escapeHtml(row.primary_desk || row.development_type || 'Research')}</div><h2><a href="${storyHref(row.id)}">${escapeHtml(row.title)}</a></h2><div class="signals"><span class="signal">EVIDENCE ${escapeHtml(row.evidence_class || '—')}</span><span class="signal">${escapeHtml(row.confidence || '—')}</span><span class="signal strong">IMPACT ${score(row)}/10</span></div><p>${escapeHtml(row.summary || '')}</p></article>`;

  function apply() {
    const q = (input.value || '').trim().toLowerCase();
    const ev = evidence.value;
    const min = Number(impact.value || 0);
    const filtered = rows.filter(row => (!q || haystack(row).includes(q)) && (!ev || row.evidence_class === ev) && (!min || score(row) >= min));
    count.textContent = String(filtered.length);
    results.innerHTML = filtered.slice(0, 60).map(render).join('') || '<p class="empty">No public research matches those filters.</p>';
  }

  // Footnote: search is a read-only browser projection over the already-public
  // JSON index. It sends no query text to FCMO or any third-party service.
  fetch(source, {cache: 'no-store'})
    .then(r => { if (!r.ok) throw new Error(`search index ${r.status}`); return r.json(); })
    .then(data => { rows = Array.isArray(data) ? data : []; apply(); })
    .catch(() => { results.innerHTML = '<p class="empty">The local search index could not be loaded.</p>'; });
  [input, evidence, impact].forEach(el => el.addEventListener(el === input ? 'input' : 'change', apply));
})();
