(() => {
  'use strict';
  const node = document.getElementById('fcmo-i18n-data');
  const canonicalNode = document.getElementById('fcmo-data');
  if (!node) return;

  const bundle = JSON.parse(node.textContent);
  const hasCanonical = Boolean(canonicalNode);
  const canonical = hasCanonical ? JSON.parse(canonicalNode.textContent) : { records: [] };
  const supported = ['en', 'es-419', 'zh-Hans'];
  const storageKey = 'fcmo-ai-newsletter-locale';
  const canonicalFrontierStorageKey = 'fcmo-ai-newsletter-canonical-frontier';

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
  const pack = locale === 'en' ? null : bundle.packs?.[locale] || null;
  document.documentElement.lang = locale;
  document.documentElement.dataset.fcmoLocale = locale;

  // Cada campo de prosa que el dossier renderiza, no solo los tres del resumen.
  const PROSE_STRINGS = ['title', 'summary', 'why_it_matters', 'why', 'importance_rationale'];
  const PROSE_LISTS = ['limitations', 'contradictory_evidence', 'engineering_implications',
    'policy_implications', 'research_implications'];
  const PROSE_OBJECT_LISTS = { claims: ['text'], evidence_gaps: ['description'], relationships: ['summary'] };

  const phraseMap = new Map();
  function registerPhrase(source, translated) {
    if (typeof source !== 'string' || typeof translated !== 'string') return;
    const key = source.trim();
    if (key.length < 2 || !translated.trim()) return;
    if (!phraseMap.has(key)) phraseMap.set(key, translated.trim());
  }
  function registerProse(source, translated) {
    if (!source || !translated) return;
    for (const field of PROSE_STRINGS) registerPhrase(source[field], translated[field]);
    for (const field of PROSE_LISTS) {
      const from = source[field], to = translated[field];
      if (!Array.isArray(from) || !Array.isArray(to) || from.length !== to.length) continue;
      from.forEach((value, i) => registerPhrase(value, to[i]));
    }
    for (const [field, keys] of Object.entries(PROSE_OBJECT_LISTS)) {
      const from = source[field], to = translated[field];
      if (!Array.isArray(from) || !Array.isArray(to) || from.length !== to.length) continue;
      from.forEach((value, i) => { for (const key of keys) registerPhrase(value?.[key], to[i]?.[key]); });
    }
    const from = source.technical, to = translated.technical;
    if (from && to) for (const [key, value] of Object.entries(from)) registerPhrase(value, to[key]);
  }
  if (pack) {
    for (const [source, translated] of Object.entries(pack.ui || {})) phraseMap.set(source, translated);
    for (const record of canonical.records || []) {
      const tr = pack.records?.[record.id];
      if (!tr) continue;
      registerProse(record, tr);
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
      'Opening the canonical FCMO AI Newsletter record…':'Abriendo el registro canónico de FCMO AI Newsletter…','Continue':'Continuar',
      'Machine-readable corpus →':'Corpus legible por máquinas →','Lead signal':'Señal principal','Front page':'Portada','Desks':'Secciones','Uncertainty docket':'Expediente de incertidumbre',
      'multi-source':'múltiples fuentes','source families':'familias de fuentes','claim records':'afirmaciones registradas','open gaps':'vacíos abiertos',
      'Claims':'Afirmaciones','Mechanism':'Mecanismo','Weak edge':'Punto débil','Provenance':'Procedencia','Complete desk →':'Ver sección completa →','Open full desk →':'Abrir sección completa →',
      'public briefs':'dossiers públicos','lead impact':'impacto principal','development':'desarrollo','developments':'desarrollos','Topic':'Tema','Organization':'Organización',
      'Library':'Biblioteca','Newsroom':'Redacción','Query the record.':'Consulta el registro.','Don’t scrape it.':'No lo extraigas con scraping.','Agent interface':'Interfaz para agentes'
    },
    'zh-Hans': {
      'Research Intelligence':'研究情报','public briefs':'公开档案','Evidence A':'A 级证据','open evidence gaps':'待补证据','explicit relationships':'明确关联',
      'Opening the canonical FCMO AI Newsletter record…':'正在打开 FCMO AI Newsletter 权威记录……','Continue':'继续',
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
  function translatePattern(text) {
    if (!pack) return text;
    let m;
    if ((m = text.match(/^(\d+)\s+(public briefs \/ complete corpus inside)$/))) {
      const translated = phraseMap.get(m[2]);
      if (translated) return `${m[1]} ${translated}`;
    }
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
    if ((m = text.match(/^(\d+) briefs? total$/))) return locale === 'es-419'
      ? `${m[1]} ${m[1] === '1' ? 'dossier' : 'dossiers'} en total` : `共 ${m[1]} 份档案`;
    if ((m = text.match(/^(\d+) total public briefs$/))) return locale === 'es-419'
      ? `${m[1]} ${m[1] === '1' ? 'dossier público' : 'dossiers públicos'} en total` : `共 ${m[1]} 份公开档案`;
    if ((m = text.match(/^(\d+) canonical briefs$/))) return locale === 'es-419'
      ? `${m[1]} ${m[1] === '1' ? 'dossier canónico' : 'dossiers canónicos'}` : `${m[1]} 份规范档案`;
    if ((m = text.match(/^(\d+) publication documents?$/))) return locale === 'es-419'
      ? `${m[1]} ${m[1] === '1' ? 'documento de publicación' : 'documentos de publicación'}` : `${m[1]} 份出版文档`;
    // La cabecera de una edicion llega como un solo nodo con marcas de tiempo
    // variables: se traduce la prosa fija y se conservan las fechas.
    if ((m = text.match(/^Published (\S+) . evidence cutoff (\S+) Historical snapshot: later evidence may be reflected in current research pages and corrections\. FCMO AI Newsletter Brief . (\S+) Evidence-first daily edition\. Importance measures consequence if true, not truth; candidates below remain explicitly investigating unless stated otherwise\.$/))) {
      return locale === 'es-419'
        ? `Publicado ${m[1]} · corte de evidencia ${m[2]} Instantánea histórica: la evidencia posterior puede reflejarse en las páginas de investigación actuales y en las correcciones. Dossier de FCMO AI Newsletter — ${m[3]} Edición diaria con la evidencia primero. La importancia mide la consecuencia si algo es cierto, no la verdad; los candidatos de abajo siguen explícitamente en investigación salvo que se indique lo contrario.`
        : `发布于 ${m[1]} · 证据截止 ${m[2]} 历史快照：后续证据可能反映在当前的研究页面与更正中。FCMO AI Newsletter 档案 — ${m[3]} 证据优先的每日版本。重要性衡量的是“若为真”的后果，而非真实性；除非另有说明，下列候选项仍明确处于调查中。`;
    }
    if ((m = text.match(/^Impact (\d+)\/10$/))) return locale === 'es-419' ? `Impacto ${m[1]}/10` : `影响 ${m[1]}/10`;
    if ((m = text.match(/^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4})$/))) {
      const month = MONTHS[locale]?.[m[2]];
      if (month) return locale === 'es-419' ? `${m[1]} ${month} ${m[3]}` : `${m[3]}年${month}月${Number(m[1])}日`;
    }
    return text;
  }
  const MONTHS = {
    'es-419': { Jan:'ene', Feb:'feb', Mar:'mar', Apr:'abr', May:'may', Jun:'jun',
      Jul:'jul', Aug:'ago', Sep:'sep', Oct:'oct', Nov:'nov', Dec:'dic' },
    'zh-Hans': { Jan:'1', Feb:'2', Mar:'3', Apr:'4', May:'5', Jun:'6',
      Jul:'7', Aug:'8', Sep:'9', Oct:'10', Nov:'11', Dec:'12' }
  };
  let upperIndex = null;
  function translateAtom(text) {
    const direct = phraseMap.get(text);
    if (direct) return direct;
    const dynamic = translatePattern(text);
    if (dynamic !== text) return dynamic;
    // Un rotulo en versalitas duras: 'AGENTS MEMORY' por 'Agents Memory'.
    if (text.length > 2 && text === text.toUpperCase() && /[A-Z]{3}/.test(text)) {
      if (!upperIndex) {
        upperIndex = new Map();
        for (const [source, value] of phraseMap) upperIndex.set(source.toUpperCase(), value);
      }
      const found = upperIndex.get(text);
      if (found) return locale === 'es-419' ? found.toUpperCase() : found;
    }
    return text;
  }
  // Una linea compuesta ('Agents Memory · Evidence A · Impact 8/10') nunca puede
  // estar en el catalogo entera: se traduce por segmentos y se rearma.
  const SEPARATORS = /( · | \/ | — )/;
  function translateDynamic(text) {
    if (!pack) return text;
    const atom = translateAtom(text);
    if (atom !== text) return atom;
    const affix = text.match(/^(.+?)(\s*(?:→|↗))$/);
    if (affix) {
      const inner = translateDynamic(affix[1]);
      if (inner !== affix[1]) return inner + affix[2];
    }
    if (SEPARATORS.test(text)) {
      const parts = text.split(SEPARATORS);
      let changed = false;
      const out = parts.map((part, i) => {
        if (i % 2) return part;
        const piece = part.trim();
        if (!piece) return part;
        const replaced = translateAtom(piece);
        if (replaced !== piece) { changed = true; return part.replace(piece, replaced); }
        return part;
      });
      if (changed) return out.join('');
    }
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
    for (const attr of ['placeholder','aria-label','title','label']) {
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

  // El texto legal se traduce para que se pueda leer, pero el ingles sigue
  // siendo la version que rige: cada bloque lo dice y enlaza a el.
  function legalNotice() {
    if (!pack) return;
    const href = (() => { const u = new URL(location.href); u.searchParams.set('lang', 'en'); return u.toString(); })();
    for (const block of document.querySelectorAll('[data-fcmo-legal="canonical"]')) {
      if (block.classList.contains('fcmo-footer-attribution')) continue;
      if (block.querySelector(':scope > .fcmo-legal-notice')) continue;
      const note = document.createElement('p');
      note.className = 'fcmo-legal-notice';
      const link = document.createElement('a');
      link.href = href;
      link.textContent = locale === 'es-419' ? 'versión en inglés' : '英文版本';
      if (locale === 'es-419') {
        note.append(document.createTextNode('Traducción de cortesía. La '), link,
          document.createTextNode(' es la que rige.'));
      } else {
        note.append(document.createTextNode('便利翻译，以'), link, document.createTextNode('为准。'));
      }
      block.insertBefore(note, block.firstChild);
    }
  }

  function editorialOverrides() {
    if (!pack) return;
    const heroTitle = document.querySelector('.hero-copy h1');
    const heroHTML = locale === 'es-419' ? 'Lo que <em>realmente importa</em> en IA.' : 'AI 中<em>真正重要</em>的进展。';
    if (heroTitle && heroTitle.innerHTML !== heroHTML) heroTitle.innerHTML = heroHTML;
    const leadTitle = document.querySelector('.lead-body h2');
    if (leadTitle && /Agents crossed the boundary/.test(leadTitle.textContent)) leadTitle.innerHTML = locale === 'es-419'
      ? 'Los agentes cruzaron la frontera entre la <em>evaluación</em> y el mundo real.'
      : '智能体跨越了<em>评估环境</em>与现实世界之间的边界。';
    const footer = document.querySelector('.footer h2');
    const footerHTML = locale === 'es-419' ? 'Primero la evidencia.<br><em>La memoria intacta.</em>' : '证据优先。<br><em>记忆完整。</em>';
    if (footer && footer.innerHTML !== footerHTML) footer.innerHTML = footerHTML;
  }

  function collapseCanonicalDossier() {
    if (!pack || !hasCanonical || !location.hash.startsWith('#/brief/')) return;
    const main = document.querySelector('.brief-main'); if (!main || main.querySelector(':scope > details.fcmo-canonical-dossier')) return;
    const evidenceEyebrows = new Set(['Technical dossier', 'Claims ledger', 'Open evidence gaps']);
    const sections = [...main.querySelectorAll(':scope > section')];
    const canonicalSections = sections.filter(section => evidenceEyebrows.has(section.querySelector(':scope > .eyebrow')?.textContent.trim()));
    if (!canonicalSections.length) return;
    const details = document.createElement('details'); details.className = 'fcmo-canonical-dossier';
    const summary = document.createElement('summary');
    const label = document.createElement('span'); label.className = 'fcmo-canonical-label';
    label.textContent = phraseMap.get('English canonical record') || 'English canonical record';
    const note = document.createElement('span'); note.className = 'fcmo-canonical-note';
    note.textContent = phraseMap.get('Technical evidence stays in English so its meaning is not altered.')
      || 'Technical evidence stays in English so its meaning is not altered.';
    summary.append(label, note);
    const body = document.createElement('div'); body.className = 'fcmo-canonical-body';
    main.insertBefore(details, canonicalSections[0]);
    for (const section of canonicalSections) body.appendChild(section);
    details.append(summary, body);
    try { details.open = localStorage.getItem(canonicalFrontierStorageKey) === 'open'; } catch {}
    details.addEventListener('toggle', () => {
      try { localStorage.setItem(canonicalFrontierStorageKey, details.open ? 'open' : 'closed'); } catch {}
    });
  }

  function localizedResearch() {
    if (!pack || !hasCanonical || !location.hash.startsWith('#/research')) return;
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
      scheduled = false; selector(); collapseCanonicalDossier(); legalNotice(); walk(document.body); editorialOverrides();
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
    getTranslation(id) { return locale === 'en' ? null : (pack?.records?.[id] || null); }
  });
  apply();
  setTimeout(localizedResearch,0);
})();
