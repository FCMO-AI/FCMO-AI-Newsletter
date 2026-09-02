(() => {
  'use strict';
  const node = document.getElementById('fcmo-i18n-data');
  const canonicalNode = document.getElementById('fcmo-data');
  if (!node || !canonicalNode) return;

  const bundle = JSON.parse(node.textContent);
  const canonical = JSON.parse(canonicalNode.textContent);
  const supported = ['en', 'es-419', 'zh-Hans'];
  const storageKey = 'fcmo-ai-newsletter-locale';

  function normalize(value) {
    if (!value) return null;
    const v = String(value).replace('_', '-').toLowerCase();
    if (v === 'en' || v.startsWith('en-')) return 'en';
    if (v === 'es' || v.startsWith('es-')) return 'es-419';
    if (v === 'zh' || v.startsWith('zh-')) return 'zh-Hans';
    return null;
  }
  function resolveLocale() {
    const explicit = normalize(new URL(location.href).searchParams.get('lang'));
    if (explicit) return explicit;
    try { const saved = normalize(localStorage.getItem(storageKey)); if (saved) return saved; } catch {}
    for (const language of (navigator.languages || [navigator.language])) {
      const candidate = normalize(language); if (candidate) return candidate;
    }
    return 'en';
  }

  const locale = resolveLocale();
  const pack = locale === 'en' ? null : bundle.packs[locale];
  document.documentElement.lang = locale;
  document.documentElement.dataset.fcmoLocale = locale;

  const phraseMap = new Map();
  if (pack) {
    for (const [source, translated] of Object.entries(pack.ui || {})) phraseMap.set(source, translated);
    for (const record of canonical.records || []) {
      const tr = pack.records?.[record.id];
      if (!tr) continue;
      for (const field of ['title', 'summary', 'why_it_matters']) {
        if (record[field] && tr[field]) phraseMap.set(record[field], tr[field]);
      }
    }
  }

  const deskLabels = {
    'es-419': {
      'agents_memory':'Agentes y memoria','architectures_scaling':'Arquitecturas y escalamiento','compute_hardware':'Cómputo y hardware',
      'efficiency':'Eficiencia','evaluation_science_interpretability':'Evaluación, ciencia e interpretabilidad','inference_systems':'Sistemas de inferencia',
      'labs_industry':'Laboratorios e industria','multimodality_world_models':'Multimodalidad y world models','open_ecosystem':'Ecosistema abierto',
      'policy_geopolitics':'Política y geopolítica','reasoning_posttraining':'Razonamiento y post-entrenamiento'
    },
    'zh-Hans': {
      'agents_memory':'智能体与记忆','architectures_scaling':'架构与扩展','compute_hardware':'计算与硬件','efficiency':'效率',
      'evaluation_science_interpretability':'评估、科学与可解释性','inference_systems':'推理系统','labs_industry':'实验室与产业',
      'multimodality_world_models':'多模态与 world model','open_ecosystem':'开放生态','policy_geopolitics':'政策与地缘政治','reasoning_posttraining':'推理与后训练'
    }
  };

  const uiExtra = {
    'es-419': {
      'Research Intelligence':'Inteligencia de investigación','public briefs':'dossiers públicos','Evidence A':'Evidencia A','open evidence gaps':'vacíos abiertos de evidencia','explicit relationships':'relaciones explícitas',
      'Machine-readable corpus →':'Corpus legible por máquinas →','Lead signal':'Señal principal','Front page':'Portada','Desks':'Secciones','Uncertainty docket':'Expediente de incertidumbre',
      'multi-source':'múltiples fuentes','source families':'familias de fuentes','claim records':'afirmaciones registradas','open gaps':'vacíos abiertos',
      'Claims':'Afirmaciones','Mechanism':'Mecanismo','Weak edge':'Punto débil','Provenance':'Procedencia','Complete desk →':'Ver sección completa →','Open full desk →':'Abrir sección completa →',
      'public briefs':'dossiers públicos','lead impact':'impacto principal','development':'desarrollo','developments':'desarrollos','Topic':'Tema','Organization':'Organización',
      'Library':'Biblioteca','Newsroom':'Redacción','Query the record.':'Consulta el registro.','Don’t scrape it.':'No lo extraigas con scraping.','Agent interface':'Interfaz para agentes'
    },
    'zh-Hans': {
      'Research Intelligence':'研究情报','public briefs':'公开档案','Evidence A':'A 级证据','open evidence gaps':'待补证据','explicit relationships':'明确关联',
      'Machine-readable corpus →':'机器可读语料库 →','Lead signal':'主信号','Front page':'首页','Desks':'栏目','Uncertainty docket':'不确定性清单',
      'multi-source':'多来源','source families':'来源组','claim records':'论断记录','open gaps':'待补证据','Claims':'论断','Mechanism':'机制','Weak edge':'薄弱环节','Provenance':'来源与谱系',
      'Complete desk →':'完整栏目 →','Open full desk →':'打开完整栏目 →','public briefs':'公开档案','lead impact':'最高影响','development':'项进展','developments':'项进展',
      'Topic':'主题','Organization':'机构','Library':'资料库','Newsroom':'编辑部','Query the record.':'查询公开记录。','Don’t scrape it.':'无需抓取。','Agent interface':'智能体接口'
    }
  };
  if (pack) for (const [a,b] of Object.entries(uiExtra[locale] || {})) phraseMap.set(a,b);

  function preserveWhitespace(raw, replacement) {
    const lead = raw.match(/^\s*/)?.[0] || '';
    const tail = raw.match(/\s*$/)?.[0] || '';
    return lead + replacement + tail;
  }
  function translateDynamic(text) {
    if (!pack) return text;
    let m;
    if ((m = text.match(/^(\d+) public briefs$/))) return locale === 'es-419' ? `${m[1]} dossiers públicos` : `${m[1]} 份公开档案`;
    if ((m = text.match(/^(\d+) open evidence gaps$/))) return locale === 'es-419' ? `${m[1]} vacíos abiertos de evidencia` : `${m[1]} 项待补证据`;
    if ((m = text.match(/^(\d+) explicit relationships$/))) return locale === 'es-419' ? `${m[1]} relaciones explícitas` : `${m[1]} 条明确关联`;
    if ((m = text.match(/^(\d+) of (\d+) public briefs$/))) return locale === 'es-419' ? `${m[1]} de ${m[2]} dossiers públicos` : `${m[2]} 份公开档案中显示 ${m[1]} 份`;
    if ((m = text.match(/^(\d+) briefs$/))) return locale === 'es-419' ? `${m[1]} dossiers` : `${m[1]} 份档案`;
    if ((m = text.match(/^Evidence ([A-D])$/))) return locale === 'es-419' ? `Evidencia ${m[1]}` : `${m[1]} 级证据`;
    if ((m = text.match(/^Impact (\d+) \/ 10$/))) return locale === 'es-419' ? `Impacto ${m[1]} / 10` : `影响 ${m[1]} / 10`;
    if ((m = text.match(/^(\d+) source families \/ (\d+) claim records \/ (\d+) open gaps$/))) return locale === 'es-419'
      ? `${m[1]} familias de fuentes / ${m[2]} afirmaciones / ${m[3]} vacíos abiertos`
      : `${m[1]} 组来源 / ${m[2]} 条论断 / ${m[3]} 项待补证据`;
    return text;
  }
  function translateTextNode(textNode) {
    if (!pack || !textNode.nodeValue) return;
    const trimmed = textNode.nodeValue.trim();
    if (!trimmed) return;
    let replacement = phraseMap.get(trimmed) || translateDynamic(trimmed);
    if (replacement !== trimmed) textNode.nodeValue = preserveWhitespace(textNode.nodeValue, replacement);
  }
  function translateAttributes(el) {
    if (!pack || el.nodeType !== 1) return;
    for (const attr of ['placeholder','aria-label','title']) {
      const value = el.getAttribute?.(attr); if (!value) continue;
      const replacement = phraseMap.get(value) || translateDynamic(value);
      if (replacement !== value) el.setAttribute(attr, replacement);
    }
  }
  function walk(root) {
    if (!pack || !root) return;
    if (root.nodeType === Node.TEXT_NODE) return translateTextNode(root);
    if (root.nodeType !== Node.ELEMENT_NODE && root.nodeType !== Node.DOCUMENT_FRAGMENT_NODE && root.nodeType !== Node.DOCUMENT_NODE) return;
    if (root.nodeType === Node.ELEMENT_NODE) translateAttributes(root);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    let current; while ((current = walker.nextNode())) {
      if (current.nodeType === Node.TEXT_NODE) translateTextNode(current); else translateAttributes(current);
    }
  }

  function selector() {
    if (document.getElementById('fcmo-language')) return;
    const header = document.querySelector('.topbar'); if (!header) return;
    const wrap = document.createElement('label'); wrap.className = 'fcmo-language';
    wrap.innerHTML = `<span>${locale === 'es-419' ? 'Idioma' : locale === 'zh-Hans' ? '语言' : 'Language'}</span><select id="fcmo-language" aria-label="Newsletter language"><optgroup label="Canonical source"><option value="en">English</option></optgroup><optgroup label="Curated translations"><option value="es-419">Español</option><option value="zh-Hans">简体中文</option></optgroup></select>`;
    header.appendChild(wrap);
    const select = wrap.querySelector('select'); select.value = locale;
    select.addEventListener('change', () => {
      const next = select.value;
      try { localStorage.setItem(storageKey, next); } catch {}
      const url = new URL(location.href); url.searchParams.set('lang', next); location.href = url.toString();
    });
  }

  function editorialOverrides() {
    if (!pack) return;
    const heroTitle = document.querySelector('.hero-copy h1');
    if (heroTitle) heroTitle.innerHTML = locale === 'es-419' ? 'Lo que <em>realmente importa</em> en IA.' : 'AI 中<em>真正重要</em>的进展。';
    const leadTitle = document.querySelector('.lead-body h2');
    if (leadTitle && /Agents crossed the boundary/.test(leadTitle.textContent)) leadTitle.innerHTML = locale === 'es-419'
      ? 'Los agentes cruzaron la frontera entre la <em>evaluación</em> y el mundo real.'
      : '智能体跨越了<em>评估环境</em>与现实世界之间的边界。';
    const footer = document.querySelector('.footer h2');
    if (footer) footer.innerHTML = locale === 'es-419' ? 'Primero la evidencia.<br><em>La memoria intacta.</em>' : '证据优先。<br><em>记忆完整。</em>';
  }

  function collapseCanonicalDossier() {
    if (!pack || !location.hash.startsWith('#/brief/')) return;
    const main = document.querySelector('.brief-main'); if (!main || main.querySelector(':scope > details.fcmo-canonical-dossier')) return;
    const sections = [...main.querySelectorAll(':scope > section')]; if (sections.length < 2) return;
    const details = document.createElement('details'); details.className = 'fcmo-canonical-dossier';
    const summary = document.createElement('summary');
    summary.textContent = locale === 'es-419' ? 'Registro técnico y probatorio canónico — English' : '权威技术与证据记录 — English';
    const note = document.createElement('p'); note.className = 'fcmo-canonical-note';
    note.textContent = locale === 'es-419'
      ? 'La noticia, su resumen y su interpretación editorial están traducidos de forma curada. El registro técnico profundo se conserva en inglés para mantener intactos matices probatorios, terminología e identificadores.'
      : '新闻正文、摘要和编辑判断均为策划式翻译。深层技术与证据记录保留英文，以避免改变证据限定、术语和稳定标识符。';
    const body = document.createElement('div'); body.className = 'fcmo-canonical-body';
    for (const section of sections.slice(1)) body.appendChild(section);
    details.append(summary, note, body); main.appendChild(details);
  }

  function localizedResearch() {
    if (!pack || !location.hash.startsWith('#/research')) return;
    const q = document.getElementById('rq'), list = document.getElementById('rlist'), count = document.getElementById('rcount');
    if (!q || !list || !count) return;
    const desk = document.getElementById('rdesk'), ev = document.getElementById('rev'), imp = document.getElementById('rimp'), sort = document.getElementById('rsort');
    const term = q.value.trim().toLocaleLowerCase(locale);
    let rows = (canonical.records || []).filter(r => {
      const tr = pack.records[r.id];
      const blob = [tr?.title,tr?.summary,tr?.why_it_matters,r.title,r.summary,(r.topics||[]).join(' '),(r.organizations||[]).join(' ')].join(' ').toLocaleLowerCase(locale);
      return (!term || blob.includes(term)) && (!desk.value || r.primary_desk === desk.value) && (!ev.value || r.evidence === ev.value) && r.importance >= Number(imp.value);
    });
    rows.sort((a,b)=>sort.value==='newest'?String(b.event_at).localeCompare(String(a.event_at)):sort.value==='evidence'?String(a.evidence).localeCompare(String(b.evidence))||b.importance-a.importance:b.importance-a.importance||String(b.event_at).localeCompare(String(a.event_at)));
    count.innerHTML = locale === 'es-419' ? `<b>${rows.length}</b> de ${canonical.records.length} dossiers públicos` : `共 ${canonical.records.length} 份公开档案，显示 <b>${rows.length}</b> 份`;
    list.innerHTML = rows.map(r => { const tr=pack.records[r.id]||r, dl=deskLabels[locale]?.[r.primary_desk]||r.desk||r.primary_desk;
      return `<a class="standalone-item" href="#/brief/${r.id}"><div class="meta">${escapeHtml(r.id)}<br>${escapeHtml(dl)}<br>${escapeHtml((r.event_at||'').slice(0,10))}</div><div><h3>${escapeHtml(tr.title)}</h3><p>${escapeHtml(tr.summary)}</p><div class="chips">${(r.topics||[]).slice(0,4).map(t=>`<span class="chip">${escapeHtml(t)}</span>`).join('')}</div></div><div class="standalone-score"><span>E${escapeHtml(r.evidence)}</span><strong>${r.importance}/10</strong></div></a>`;
    }).join('');
  }
  function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}

  let scheduled = false;
  function apply() {
    if (scheduled) return; scheduled = true;
    queueMicrotask(() => {
      scheduled = false; selector(); walk(document.body); editorialOverrides(); collapseCanonicalDossier();
    });
  }
  const observer = new MutationObserver(apply);
  observer.observe(document.documentElement, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:['placeholder','aria-label','title']});
  document.addEventListener('input', e => { if (pack && e.target?.id === 'rq') setTimeout(localizedResearch,0); }, true);
  document.addEventListener('change', e => { if (pack && ['rdesk','rev','rimp','rsort'].includes(e.target?.id)) setTimeout(localizedResearch,0); }, true);
  window.addEventListener('hashchange', () => setTimeout(() => { apply(); localizedResearch(); },0));

  window.FCMO_I18N = Object.freeze({
    schema: bundle.schema,
    canonicalLocale: 'en',
    supportedLocales: Object.freeze([...supported]),
    locale,
    curated: locale !== 'en',
    getTranslation(id) { return locale === 'en' ? null : (pack.records[id] || null); }
  });
  apply();
  setTimeout(localizedResearch,0);
})();
