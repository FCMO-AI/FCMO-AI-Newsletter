import { get, post, put, del, ApiError } from './api.js'
import { t, LOCALE_NAME, LOCALE_SHORT } from './i18n.js'
import { h, clear, modal, toast, ago } from './ui.js'
import { shell, session } from './main.js'
import { plainText } from './docmodel.js'
import { diffView } from './diffview.js'
import { suggestions } from './assistant.js'
import { amendDialog } from './publication-actions.js'
import { checksList, versionsPanel } from './drawers.js'

const LOCS = ['en', 'es-419', 'zh-Hans']
const crumbs = (slug, title, here) => h('div', { class: 'crumbs' }, h('a', { href: '#/' }, t('nav.home')), ' / ', h('a', { href: `#/p/${slug}` }, title), ' / ', h('span', null, here))
const other = () => session.me.other

/* ---------------- translate (S3) ---------------- */
function chip (n, notesOrder) {
  if (n.t === 'fn') return h('span', { class: 'chip fn', contenteditable: 'false', 'data-node': JSON.stringify(n), title: t('tr.chip') }, '¹ ' + (notesOrder.indexOf(n.id) + 1))
  return h('span', { class: 'chip cite', contenteditable: 'false', 'data-node': JSON.stringify(n), title: t('tr.chip') }, '[' + n.key.replace(/^src-/, '') + (n.locator ? ', ' + n.locator : '') + ']')
}
function inlineToDom (nodes, order, { tokens = false } = {}) {
  const frag = document.createDocumentFragment()
  for (const n of nodes || []) {
    if (n.t === 'text') {
      const text = n.v
      if (tokens) text.split(/(https?:\/\/\S+|\d[\d.,%]*)/).forEach((p, i) => frag.append(i % 2 ? h('span', { class: 'tok', contenteditable: 'false' }, p) : document.createTextNode(p)))
      else frag.append(document.createTextNode(text))
    } else if (n.t === 'link' || n.t === 'lang') frag.append(h('span', { class: 'chip', contenteditable: 'false', 'data-node': JSON.stringify(n) }, plainText(n.c))); else frag.append(chip(n, order))
  }
  return frag
}
function domToInline (el) {
  const out = []
  const push = v => { if (!v) return; const last = out[out.length - 1]; if (last && last.t === 'text' && !last.marks) last.v += v; else out.push({ t: 'text', v }) }
  const walk = node => { for (const c of node.childNodes) { if (c.nodeType === 3) push(c.nodeValue); else if (c.dataset && c.dataset.node) out.push(JSON.parse(c.dataset.node)); else if (c.tagName === 'BR') push('\n'); else walk(c) } }
  walk(el); return out
}

export async function translateScreen (root, slug, fromLoc, targetArg) {
  const meta = await get(`/api/pieces/${slug}`)
  const srcLoc = meta.source_locale
  const target = targetArg && targetArg !== srcLoc ? targetArg : LOCS.find(l => l !== srcLoc)
  const [src, tgtRes, figRes] = await Promise.all([get(`/api/pieces/${slug}/doc/${srcLoc}`), get(`/api/pieces/${slug}/doc/${target}`), get(`/api/pieces/${slug}/figures`)])
  let localCopy
  try { localCopy = JSON.parse(localStorage.getItem(`studio:buf:${slug}:${target}`) || 'null') } catch {}
  if (localCopy && JSON.stringify(localCopy.doc) !== JSON.stringify(tgtRes.doc)) {
    modal({ title: t('ed.restore.local'), body: t('ed.restore.local'), actions: [
      { label: t('ed.restore.drop'), onclick: close => { localStorage.removeItem(`studio:buf:${slug}:${target}`); close() } },
      { label: t('ed.restore.go'), kind: 'primary', onclick: async close => { try { await put(`/api/pieces/${slug}/doc/${target}`, { base_rev: tgtRes.rev, doc: localCopy.doc, cursor: {} }); localStorage.removeItem(`studio:buf:${slug}:${target}`); close(); location.reload() } catch (e) { toast(e.data?.error_plain || t('err.generic'), 'bad') } } }
    ] })
  }
  let rev = tgtRes.rev; const tdoc = tgtRes.doc; const figures = figRes
  let readOnly = !['draft', 'changes_requested', 'amending'].includes(meta.state); let dirty = false; let timer = null; let figT = null; let dead = false
  try { await post(`/api/pieces/${slug}/lock/${target}`) } catch (e) { if (e instanceof ApiError && e.status === 409) readOnly = true }
  const hb = setInterval(() => { if (!readOnly) post(`/api/pieces/${slug}/lock/${target}`).catch(() => {}) }, 60000)
  const byId = new Map(tdoc.blocks.map(b => [b.id, b]))
  if (!tdoc.blocks.length) {
    const fixed = nodes => nodes.map(n => n.t === 'text' ? { ...n, v: (n.v.match(/\d+(?:[.,]\d+)*/g) || []).join(' ') } : structuredClone(n))
    tdoc.blocks = src.doc.blocks.map(b => { const next = structuredClone(b); if (next.content) next.content = fixed(next.content); if (next.items) next.items = next.items.map(fixed); if (next.attrs?.limits) next.attrs.limits = fixed(next.attrs.limits); return next })
    for (const b of tdoc.blocks) byId.set(b.id, b)
    tdoc.footnotes = Object.fromEntries(Object.entries(src.doc.footnotes).map(([id, nodes]) => [id, fixed(nodes)]))
  }
  const order = d => { const ids = []; const w = n => { if (Array.isArray(n)) n.forEach(w); else if (n && typeof n === 'object') { if (n.t === 'fn') ids.push(n.id); Object.values(n).forEach(w) } }; w(d.blocks); return ids }
  const ord = order(src.doc)
  const langState = meta.locales[target] || { state: 'empty' }
  const state = h('span', { class: 'save-state', role: 'status' }, t('ed.saved'))
  const setState = k => { state.textContent = { saved: t('ed.saved'), saving: t('ed.saving'), dirty: t('ed.dirty'), offline: t('ed.offline') }[k] }

  async function save () {
    if (readOnly || dead || !dirty) return
    setState('saving'); dirty = false
    const blocks = src.doc.blocks.map(b => byId.get(b.id)).filter(Boolean)
    const extra = tdoc.blocks.filter(b => !src.doc.blocks.some(s => s.id === b.id))
    const next = { ...tdoc, blocks: [...blocks, ...extra] }
    try { const r = await put(`/api/pieces/${slug}/doc/${target}`, { base_rev: rev, doc: next, cursor: {} }); rev = r.rev; setState(dirty ? 'dirty' : 'saved'); try { if (!dirty) localStorage.removeItem(`studio:buf:${slug}:${target}`) } catch {} } catch (e) { dirty = true; if (e instanceof ApiError && e.status === 409) { modal({ title: t('conf.title'), body: t('conf.body', { who: e.data.by, at: '' }), actions: [{ label: t('conf.server'), onclick: () => location.reload() }, { label: t('conf.mine'), kind: 'primary', onclick: close => { rev = e.data.rev; close(); save() } }] }); return } else setState('offline'); timer = setTimeout(save, 6000) }
  }
  const changed = () => { if (readOnly) return; try { localStorage.setItem(`studio:buf:${slug}:${target}`, JSON.stringify({ doc: tdoc, base_rev: rev, at: Date.now() })) } catch {} dirty = true; setState('dirty'); clearTimeout(timer); timer = setTimeout(save, 1200) }

  const origin = langState.origin
  const badgeFor = b => (tgtRes.block_provenance[b?.id] || origin) === 'agent_draft' ? ['agent', t('tr.agent')] : (tgtRes.block_provenance[b?.id] || origin) === 'agent_draft_human_edited' ? ['edited', t('tr.agent.edited')] : ['human', t('tr.human')]
  const rows = h('div', { class: 'tr-rows' })
  for (const field of ['title', 'dek']) { const input = h('textarea', { rows: 2, readonly: readOnly, 'aria-label': t('ed.' + field) }); input.value = tdoc[field]; input.addEventListener('input', () => { tdoc[field] = input.value; changed() }); rows.append(h('div', { class: 'tr-cols tr-row' }, h('div', { class: 'tr-src', lang: srcLoc }, src.doc[field]), h('div', { class: 'tr-tgt', lang: target }, input))) }
  const head = h('div', { class: 'tr-cols tr-colhead' }, h('div', null, h('strong', null, t('tr.source')), ' · ', LOCALE_NAME[srcLoc]), h('div', null, h('strong', null, t('tr.target')), ' · ', LOCALE_NAME[target]))
  let n = 0
  for (const sb of src.doc.blocks) {
    n++
    const tb = byId.get(sb.id)
    const stale = tgtRes.source_changed.includes(sb.id)
    const left = h('div', { class: 'tr-src', lang: srcLoc, 'data-type': sb.type })
    const right = h('div', { class: 'tr-tgt' + (stale ? ' stale' : ''), lang: target, 'data-type': sb.type })
    if (sb.type === 'figure') {
      const f = figures[sb.attrs.fig] || {}
      left.append(h('div', { class: 'tr-fig' }, f.file ? h('img', { src: `/figures/${slug}/${sb.attrs.fig}/image.webp`, alt: '' }) : null, h('p', { class: 'muted small' }, (f.alt || {})[srcLoc] || '', ' · ', (f.caption || {})[srcLoc] || '')))
      const fld = (k, label) => { const el = h('textarea', { rows: 2, 'aria-label': label, placeholder: label, readonly: readOnly }); el.value = ((f[k] || {})[target]) || ''; el.addEventListener('input', () => { figures[sb.attrs.fig] = { ...f, [k]: { ...(f[k] || {}), [target]: el.value } }; clearTimeout(figT); figT = setTimeout(() => put(`/api/pieces/${slug}/figures`, figures).catch(() => {}), 800) }); return el }
      right.append(fld('alt', t('fig.alt', { lang: target })), fld('caption', t('fig.cap', { lang: target })))
    } else if (sb.type === 'hr') { left.append(h('hr')); right.append(h('hr')) } else {
      const isList = sb.type === 'ul' || sb.type === 'ol'
      const isEv = sb.type === 'evidence'
      const srcInline = isList ? (sb.items || []).flat() : isEv ? sb.attrs.limits : sb.content
      left.append(inlineToDom(srcInline, ord, { tokens: true }))
      const ed = h('div', { class: 'tr-edit', contenteditable: readOnly ? 'false' : 'true', spellcheck: 'true', 'data-ph': t('tr.paragraph', { n }), 'aria-label': t('tr.paragraph', { n }) })
      const tInline = tb ? (isList ? (tb.items || []).flat() : isEv ? (tb.attrs && tb.attrs.limits) : tb.content) : []
      if (isList) { const items = tb?.items || sb.items.map(() => []); for (const item of items) ed.append(h('div', { class: 'tr-list-item' }, inlineToDom(item, ord, { tokens: true }))) } else ed.append(inlineToDom(tInline, ord, { tokens: true }))
      ed.addEventListener('input', () => {
        const inl = domToInline(ed)
        let blk = byId.get(sb.id)
        if (!blk) { blk = { id: sb.id, type: sb.type, ...(isList ? { items: [] } : { content: [] }), attrs: sb.type === 'evidence' ? { ...sb.attrs } : {} }; byId.set(sb.id, blk); tdoc.blocks.push(blk) }
        if (isList) blk.items = [...ed.children].map(domToInline); else if (isEv) blk.attrs = { ...blk.attrs, class: sb.attrs.class, confidence: blk.attrs.confidence || sb.attrs.confidence, limits: inl }; else blk.content = inl
        // Source hashes and authorship come from the server, outside the document.
        right.classList.remove('stale'); const badge = right.querySelector('.tr-badge'); if (badge) { const assisted = (tgtRes.block_provenance[sb.id] || origin || '').startsWith('agent_'); badge.className = 'tr-badge ' + (assisted ? 'edited' : 'human'); badge.textContent = t(assisted ? 'tr.agent.edited' : 'tr.human') }
        changed()
      })
      right.append(ed)
      const [bc, bt] = badgeFor(tb)
      if (tb) right.append(h('div', { class: 'tr-meta' }, h('span', { class: 'tr-badge ' + bc }, bt), stale ? h('span', { class: 'tr-stale' }, t('tr.changed')) : null))
      else right.append(h('div', { class: 'tr-meta' }, h('button', { class: 'link-btn', type: 'button', disabled: readOnly, onclick: () => { ed.replaceChildren(inlineToDom(srcInline.filter(x => x.t !== 'text' || true), ord)); ed.dispatchEvent(new Event('input')) } }, t('tr.copy'))))
    }
    rows.append(h('div', { class: 'tr-cols tr-row' }, left, right))
  }

  for (const [id, body] of Object.entries(src.doc.footnotes)) {
    const input = h('div', { class: 'tr-edit', contenteditable: readOnly ? 'false' : 'true', 'aria-label': t('fn.heading') }); input.append(inlineToDom(tdoc.footnotes[id] || [], ord, { tokens: true })); input.addEventListener('input', () => { tdoc.footnotes[id] = domToInline(input); changed() }); rows.append(h('div', { class: 'tr-cols tr-row' }, h('div', { class: 'tr-src' }, inlineToDom(body, ord, { tokens: true })), h('div', { class: 'tr-tgt' }, input)))
  }
  async function mark (st, reviewed) { await save(); if (dirty) throw new Error('Save pending'); const r = await post(`/api/pieces/${slug}/locale/${target}/state`, { state: st, reviewed, confirmation: target === 'zh-Hans' && reviewed ? 'Leí y entiendo el texto chino' : '' }); toast('✓'); return r }
  const reviewBtn = h('button', { class: 'btn primary small', type: 'button', onclick: () => {
    const doIt = async close => { await save(); await mark('ready', true); close && close(); route2() }
    if (target === 'zh-Hans') { const cb = h('input', { type: 'checkbox' }); modal({ title: t('tr.review'), body: [h('p', null, t('tr.zh.ask')), h('label', { class: 'check' }, cb, ' ', t('tr.zh.confirm'))], actions: [{ label: t('tr.cancel') }, { label: t('tr.confirm'), kind: 'primary', onclick: close => { if (cb.checked) doIt(close) } }] }) } else doIt()
  } }, t('tr.review'))
  const route2 = () => { location.hash = `#/p/${slug}/${fromLoc}/translate/${target}`; location.reload() }
  const status = langState.state === 'ready' && langState.reviewed ? h('p', { class: 'tr-status ok' }, t('tr.reviewed', { who: langState.by || '', when: langState.at ? ago(langState.at, t) : '' })) : h('p', { class: 'tr-status' }, t('state.' + (langState.state || 'empty')), (langState.origin || '').startsWith('agent_') ? ' · ' + t('tr.agent') : '')
  const assist = h('button', { class: 'btn small ghost', type: 'button', onclick: async () => { await save(); await suggestions(slug, target, 'translate', assist) } }, t('tr.assist'))
  const tabs = h('nav', { class: 'lang-tabs', 'aria-label': t('tr.pick') }, LOCS.filter(l => l !== srcLoc).map(l => h('a', { href: `#/p/${slug}/${fromLoc}/translate/${l}`, class: 'lt ' + ((meta.locales[l] || {}).state || 'empty'), 'aria-current': l === target ? 'page' : null }, LOCALE_SHORT[l], ' ', h('span', { class: 'lt-dot' }, { ready: '●', drafting: '◐', later: '⏸', empty: '○' }[(meta.locales[l] || {}).state || 'empty']))))
  root.append(shell(h('div', { class: 'flow tr' }, crumbs(slug, meta.title, t('tr.title')),
    h('div', { class: 'flow-head' }, h('h1', null, t('tr.title')), tabs, state),
    h('div', { class: 'tr-actions' }, status, h('div', { class: 'btn-row' }, reviewBtn, h('button', { class: 'btn small', type: 'button', onclick: async () => { await mark('later', false); route2() } }, '⏸ ', t('tr.later')), langState.state === 'ready' ? h('button', { class: 'btn small ghost', type: 'button', onclick: async () => { await mark('drafting', false); route2() } }, t('tr.draft')) : null, assist, h('a', { class: 'btn small ghost', href: `#/p/${slug}/${target}` }, t('tr.edit')))),
    head, rows), { active: 'home', wide: true }))
  return () => { dead = true; clearTimeout(timer); clearInterval(hb); if (dirty && !readOnly) { const blocks = src.doc.blocks.map(b => byId.get(b.id)).filter(Boolean); fetch(`/api/pieces/${slug}/doc/${target}`, { method: 'PUT', keepalive: true, credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-csrf-token': session.me.csrf }, body: JSON.stringify({ base_rev: rev, doc: { ...tdoc, blocks }, cursor: {} }) }).catch(() => {}) } if (!readOnly) del(`/api/pieces/${slug}/lock/${target}`).catch(() => {}) }
}

/* ---------------- preview (S4) ---------------- */
function previewFrame ({ slug, loc, size, theme }) {
  const wrap = h('div', { class: 'pv-stage', 'data-size': size })
  const frame = h('iframe', { class: 'pv-frame', title: t('pv.title'), src: `/preview/${slug}/${loc}/?w=${size}&theme=${theme}`, sandbox: 'allow-same-origin allow-scripts' })
  frame.addEventListener('load', () => { try { frame.contentDocument.documentElement.dataset.theme = theme } catch {} })
  const fit = () => {
    const avail = wrap.clientWidth || 800; const w = Number(size)
    const k = Math.min(1, (avail - 2) / w)
    frame.style.width = w + 'px'; frame.style.height = Math.round(Math.max(520, innerHeight - 260) / k) + 'px'
    frame.style.transform = `scale(${k})`; frame.style.transformOrigin = 'top left'
    wrap.style.height = Math.round(Math.max(520, innerHeight - 260)) + 'px'
    frame.parentElement && (frame.parentElement.style.setProperty('--k', k))
  }
  wrap.append(frame); const ro = new ResizeObserver(fit); ro.observe(wrap); setTimeout(fit, 0)
  return { el: wrap, destroy: () => ro.disconnect() }
}
export function controls (state, change, locales) {
  const seg = (label, opts, key) => h('div', { class: 'seg', role: 'group', 'aria-label': label }, opts.map(([v, text]) => h('button', { type: 'button', 'aria-pressed': String(state[key] === v), class: state[key] === v ? 'on' : '', onclick: () => change({ [key]: v }) }, text)))
  return h('div', { class: 'pv-controls' },
    seg(t('pv.lang'), LOCS.filter(l => !locales || locales[l]).map(l => [l, LOCALE_SHORT[l]]), 'loc'),
    seg(t('pv.size'), [['390', t('pv.phone') + ' 390'], ['1440', t('pv.desktop') + ' 1440']], 'size'),
    seg(t('pv.theme'), [['light', t('pv.light')], ['dark', t('pv.dark')]], 'theme'))
}

export async function previewScreen (root, slug, loc0) {
  const meta = await get(`/api/pieces/${slug}`)
  const st = { loc: loc0, size: innerWidth < 700 ? '390' : '1440', theme: matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light' }
  const stage = h('div', { class: 'pv-main' }); const side = h('div', { class: 'pv-side' }); let frame
  const have = Object.fromEntries(LOCS.map(l => [l, meta.kind === 'issue' || (meta.locales[l] || {}).words > 0 || (meta.locales[l] || {}).state === 'later']))
  async function draw () {
    frame && frame.destroy(); clear(stage)
    stage.append(h('div', { class: 'pv-banner' }, '✓ ', t('pv.banner')), controls(st, p => { Object.assign(st, p); draw() }, have))
    if (!have[st.loc]) stage.append(h('p', { class: 'notice' }, t('pv.noloc'))); else { frame = previewFrame({ slug, ...st }); stage.append(frame.el) }
    clear(side); side.append(h('h2', null, t('dr.checks')), h('p', { class: 'muted', role: 'status' }, t('chk.running')))
    const cl = await checksList(slug, c => { location.hash = `#/p/${slug}/${c.loc || st.loc}` })
    clear(side); side.append(h('h2', null, t('dr.checks')), cl)
  }
  root.append(shell(h('div', { class: 'flow pv' }, crumbs(slug, meta.title, t('pv.title')), h('div', { class: 'pv-grid' }, stage, side), h('div', { class: 'btn-row' }, h('a', { class: 'btn', href: `#/p/${slug}/${st.loc}` }, '← ', t('pv.back')), meta.author === session.me.user ? h('a', { class: 'btn primary', href: `#/p/${slug}/publish` }, t('ed.publish')) : null)), { active: 'home', wide: true }))
  await draw()
  if (meta.author === session.me.user) { root.querySelector('.btn-row').append(h('button', { class: 'btn', onclick: async () => { const r = await post(`/api/pieces/${slug}/assist`, { kind: 'layout_qa', loc: st.loc }); toast(r.status === 'done' ? t('assist.qa.done') + (r.ok ? ' ✓' : ' !') : r.plain_es || t('err.generic')) } }, t('assist.qa'))) }
  if (meta.kind !== 'issue' && meta.author === session.me.user && ['published', 'withdrawn'].includes(meta.state)) {
    root.querySelector('.btn-row').append(h('button', { class: 'btn', onclick: () => amendDialog(meta) }, t('amend.correct')), h('button', { class: 'btn', onclick: () => amendDialog(meta, true) }, t('amend.withdraw')))
  }
  return () => frame && frame.destroy()
}

/* ---------------- publish sheet (S5) ---------------- */
export async function publishScreen (root, slug) {
  const meta = await get(`/api/pieces/${slug}`)
  const box = h('div', { class: 'pub-checks' })
  const act = h('div', { class: 'btn-row' })
  async function draw () {
    clear(box); clear(act); box.append(h('p', { class: 'muted', role: 'status' }, t('chk.running')))
    const list = await checksList(slug, c => { location.hash = meta.kind === 'issue' ? `#/issues/${slug}` : `#/p/${slug}/${c.loc || meta.source_locale}`; if (c.block_id) setTimeout(() => window.__studioGoto && window.__studioGoto(c.block_id), 800) })
    clear(box); box.append(list)
    const bad = list.list.filter(c => !c.ok)
    const mt = LOCS.filter(l => (meta.locales[l] || {}).state === 'ready' && ((meta.locales[l] || {}).origin || '').startsWith('agent_') && !(meta.locales[l] || {}).reviewed)
    if (mt.length) box.append(h('p', { class: 'notice soft' }, t('pub.mt', { langs: mt.map(l => LOCALE_NAME[l]).join(', ') })))
    const ask = h('button', { class: 'btn primary big', type: 'button', disabled: bad.length > 0 || meta.author !== session.me.user, onclick: async () => { try { await post(`/api/pieces/${slug}/review/request`); toast(t('pub.sent', { who: other() })); location.hash = '#/' } catch { toast(t('err.generic'), 'bad') } } }, t('pub.ask'))
    act.append(ask, h('button', { class: 'btn', type: 'button', onclick: draw }, t('pub.rerun'))); if (bad.length) act.append(h('span', { class: 'muted' }, t('pub.blocked', { n: bad.length })))
  }
  const mount = () => root.append(shell(h('div', { class: 'flow pub' }, crumbs(slug, meta.title, t('ed.publish')), h('h1', null, t('pub.title', { title: meta.title })), h('p', { class: 'lede' }, t('pub.lead', { who: other() })),
    h('div', { class: 'sheet' }, h('p', { class: 'notice soft' }, t('pub.public')), box, h('p', { class: 'reviewer' }, h('span', { class: 'avatar' }, other()[0]), t('pub.reviewer', { who: other() })), act)), { active: 'home' }))
  mount()
  await draw()
  return null
}

/* ---------------- review (S6) ---------------- */
export async function reviewScreen (root, slug) {
  const meta = await get(`/api/pieces/${slug}`)
  const mine = meta.author === session.me.user
  const st = { loc: meta.source_locale, size: innerWidth < 700 ? '390' : '1440', theme: 'light' }
  const stage = h('div', { class: 'rv-read' }); const diffBox = h('div', { class: 'rv-diff' }); const cmtBox = h('div', { class: 'rv-cmt' })
  let frame; let selectedBlock = null; let selectedText = ''
  const selectionHint = h('p', { class: 'hint', role: 'status' }, t('rev.pick'))
  const have = Object.fromEntries(LOCS.map(l => [l, meta.kind === 'issue' || (meta.locales[l] || {}).words > 0 || (meta.locales[l] || {}).state === 'later']))
  function drawRead () {
    frame && frame.destroy(); clear(stage)
    stage.append(h('div', { class: 'pv-banner' }, '✓ ', t('pv.banner')), controls(st, p => {
      if (p.loc && p.loc !== st.loc) { selectedBlock = null; selectedText = ''; selectionHint.textContent = t('rev.pick') }
      Object.assign(st, p); drawRead(); drawDiff(); drawCmt()
    }, have), selectionHint)
    frame = previewFrame({ slug, ...st }); stage.append(frame.el)
    frame.el.querySelector('iframe').addEventListener('load', e => {
      try { e.target.contentDocument.addEventListener('click', event => {
        const block = event.target.closest('.essay-body [id^="b-"]')
        if (!block) return
        selectedBlock = block.id; selectedText = block.textContent.trim().slice(0, 160)
        selectionHint.textContent = t('rev.selected', { text: selectedText }); drawCmt()
      }) } catch {}
    })
  }
  async function drawDiff () {
    clear(diffBox)
    if (!meta.published_rev) { diffBox.append(h('p', { class: 'muted' }, t('rev.none'))); return }
    try { const d = await get(`/api/pieces/${slug}/diff?from=published&to=current&loc=${st.loc}`); diffBox.append(diffView(d)) } catch { diffBox.append(h('p', { class: 'muted' }, t('rev.none'))) }
  }
  async function drawCmt () {
    const loc = st.loc; const { commentsPanel } = await import('./drawers.js')
    const panel = await commentsPanel(slug, loc, { block: () => selectedBlock, goto: id => {
      showTab('read'); try { stage.querySelector('iframe')?.contentDocument.getElementById(id)?.scrollIntoView() } catch {}
    } })
    if (st.loc !== loc) return
    clear(cmtBox); cmtBox.append(h('p', { class: 'hint' }, selectedBlock ? t('rev.selected', { text: selectedText }) : t('rev.pick')), panel)
  }
  const tabs = ['read', 'diff', 'cmt']; let tab = 'read'
  const panes = { read: stage, diff: diffBox, cmt: cmtBox }
  const tabBar = h('div', { class: 'seg rv-tabs', role: 'tablist' })
  function showTab (k) { tab = k; clear(tabBar); [['read', t('rev.preview')], ['diff', t('rev.changes.tab')], ['cmt', t('rev.comments')]].forEach(([id, l]) => tabBar.append(h('button', { type: 'button', role: 'tab', class: id === tab ? 'on' : '', 'aria-selected': String(id === tab), onclick: () => showTab(id) }, l))); for (const id of tabs) panes[id].hidden = id !== tab }
  const note = h('textarea', { rows: 2, placeholder: t('rev.note', { who: meta.author === 'javier' ? 'Javier' : 'Matías' }), 'aria-label': t('rev.note', { who: meta.author }) })
  const act = mine ? h('p', { class: 'notice soft' }, t('rev.own'), ' ', t('rev.waiting', { who: other() })) : h('div', { class: 'rv-act' }, note, h('div', { class: 'btn-row' },
    h('button', { class: 'btn primary big', type: 'button', onclick: () => modal({ title: t('rev.approve'), body: h('p', null, t('rev.confirm')), actions: [{ label: t('common.cancel') }, { label: t('rev.approve'), kind: 'primary', onclick: async close => { await post(`/api/pieces/${slug}/review/approve`, { note: note.value }); close(); location.hash = `#/p/${slug}/progress` } }] }) }, t('rev.approve')),
    h('button', { class: 'btn big', type: 'button', onclick: async () => { await post(`/api/pieces/${slug}/review/changes`, { note: note.value }); toast(t('rev.sent', { who: meta.author === 'javier' ? 'Javier' : 'Matías' })); location.hash = '#/' } }, t('rev.changes'))))
  drawRead(); drawDiff(); drawCmt(); showTab('read')
  root.append(shell(h('div', { class: 'flow rv' }, crumbs(slug, meta.title, t('rev.preview')), h('h1', null, t('rev.title', { title: meta.title })), tabBar, h('div', { class: 'rv-panes' }, stage, diffBox, cmtBox), act), { active: 'home', wide: true }))
  return () => frame && frame.destroy()
}

/* ---------------- progress (S7) ---------------- */
export async function progressScreen (root, slug) {
  const meta = await get(`/api/pieces/${slug}`)
  const box = h('div', { class: 'timeline' }); const head = h('h1', null, t('prog.title')); let alive = true; let tm
  async function poll () {
    if (!alive) return
    let p; try { p = await get(`/api/pieces/${slug}/publication`) } catch { tm = setTimeout(poll, 3000); return }
    clear(box)
    if (p.state === 'draft' && !(p.timeline || []).length) {
      box.append(h('div', { class: 'empty-state' }, h('h2', null, t('prog.empty.title')), h('p', null, t('prog.empty.lead', { who: meta.author === session.me.user ? other() : meta.author === 'javier' ? 'Javier' : 'Matías' })),
        h('ol', null, ['prog.empty.s1', 'prog.empty.s2', 'prog.empty.s3', 'prog.empty.s4'].map(k => h('li', null, t(k, { who: other() })))),
        meta.author === session.me.user ? h('a', { class: 'btn primary', href: `#/p/${slug}/publish` }, t('prog.empty.go')) : null))
      return
    }
    box.append(h('ol', { class: 'steps' }, (p.timeline || []).map(s => h('li', { class: s.state === 'failed' ? 'failed' : 'done' }, h('span', { class: 'dot', 'aria-hidden': 'true' }, s.state === 'failed' ? '!' : '✓'), h('span', null, s.plain_es)))))
    if (p.state === 'published') box.append(h('div', { class: 'result ok' }, h('h2', null, t('prog.done')), h('p', null, t('prog.live')), h('ul', null, (p.urls || []).map(u => h('li', null, h('a', { href: u.url, target: '_blank', rel: 'noopener' }, u.url)))), h('a', { class: 'btn', href: '#/' }, t('prog.home'))))
    else if (p.state === 'failed') box.append(h('div', { class: 'result bad' }, h('h2', null, t('prog.failed')), h('p', null, p.error_plain), h('a', { class: 'btn', href: `#/p/${slug}/${meta.source_locale}` }, t('attn.open'))))
    else tm = setTimeout(poll, 1500)
  }
  poll()
  root.append(shell(h('div', { class: 'flow prog' }, crumbs(slug, meta.title, t('prog.title')), head, h('p', { class: 'lede' }, meta.title), box), { active: 'home' }))
  return () => { alive = false; clearTimeout(tm) }
}

/* ---------------- versions (S9) ---------------- */
export async function versionsScreen (root, slug) {
  const meta = await get(`/api/pieces/${slug}`)
  const loc = meta.source_locale
  const holder = h('div', { class: 'ver-page' })
  holder.append(await versionsPanel(slug, loc, { save: async () => {}, onRestored: () => { toast(t('ver.restored')); route3() }, ready: () => true }))
  const route3 = () => { location.hash = `#/p/${slug}/${loc}` }
  root.append(shell(h('div', { class: 'flow ver' }, crumbs(slug, meta.title, t('dr.versions')), h('h1', null, t('ver.title', { title: meta.title })), holder), { active: 'home' }))
  return null
}
