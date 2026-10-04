import { get, post, put, del, api, ApiError } from './api.js'
import { t, LOCALE_NAME, LOCALE_SHORT } from './i18n.js'
import { h, clear, modal, toast, ago } from './ui.js'
import { shell, session } from './main.js'
import { createEditor } from './editor.js'
import { wordCount } from './docmodel.js'
import { diffView } from './diffview.js'
import { sourcesPanel, checksList, versionsPanel, commentsPanel, tocPanel } from './drawers.js'

const LOCS = ['en', 'es-419', 'zh-Hans']
const bufKey = (slug, loc) => `studio:buf:${slug}:${loc}`
const readBuf = k => { try { return JSON.parse(localStorage.getItem(k) || 'null') } catch { return null } }
const writeBuf = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* storage blocked */ } }
const dropBuf = k => { try { localStorage.removeItem(k) } catch { /* storage blocked */ } }

export async function editorScreen (root, slug, locArg) {
  const me = session.me
  const meta = await get(`/api/pieces/${slug}`)
  const loc = locArg && LOCS.includes(locArg) ? locArg : meta.source_locale
  const [server, srcRes, figRes] = await Promise.all([get(`/api/pieces/${slug}/doc/${loc}`), get(`/api/pieces/${slug}/sources`), get(`/api/pieces/${slug}/figures`)])
  const S = { rev: server.rev, sources: srcRes.sources || [], figures: figRes.figures || {}, dirty: false, focus: false, readOnly: false, offline: false, timer: null, bufTimer: null, saving: false, dead: false }
  let doc = server.doc
  const key = bufKey(slug, loc)
  const isEmptyDoc = d => !d.title && d.blocks.length <= 1 && !(d.blocks[0] && d.blocks[0].content && d.blocks[0].content.length)

  // lock
  let lockUser = null
  try { await post(`/api/pieces/${slug}/lock/${loc}`) } catch (e) { if (e instanceof ApiError && e.status === 409) { S.readOnly = true; lockUser = (e.data && e.data.lock_user) || 'Otra persona' } }
  const heartbeat = setInterval(() => { if (!S.readOnly) post(`/api/pieces/${slug}/lock/${loc}`).catch(() => {}) }, 60000)

  /* ---------- page skeleton ---------- */
  const title = h('textarea', { class: 'essay-title ed-title', rows: 1, placeholder: t('ed.title'), 'aria-label': t('ed.title'), spellcheck: 'true', readonly: S.readOnly })
  const dek = h('textarea', { class: 'essay-dek ed-dek', rows: 1, placeholder: t('ed.dek'), 'aria-label': t('ed.dek'), spellcheck: 'true', readonly: S.readOnly })
  const auto = el => { el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px' }
  const mount = h('div', { class: 'ed-mount' })
  const notes = h('div', { class: 'notes', hidden: true }, h('p', { class: 'notes-title' }, t('fn.heading')))
  const byline = h('p', { class: 'essay-byline' })
  const banner = h('div', { class: 'banners' })
  const page = h('article', { class: 'essay ed', lang: loc, 'data-kind': meta.kind },
    h('header', { class: 'essay-head' }, h('p', { class: 'essay-kicker' }, (meta.author === 'javier' ? 'fCMO / Javier' : 'FCMO AI / Matías') + ' · ' + t('kind.' + meta.kind)), title, dek, byline),
    h('div', { class: 'ed-stage' }, mount, notes))
  const saveState = h('span', { class: 'save-state', role: 'status' }, t('ed.saved'))
  const wordsEl = h('span', { class: 'words' })
  const drawer = h('aside', { class: 'drawer', hidden: true, 'aria-label': 'Panel' })
  const rail = h('div', { class: 'rail', role: 'tablist' })
  let openTab = null

  const editor = createEditor({
    mount, notesMount: notes, doc, loc, readOnly: S.readOnly,
    sources: () => S.sources, figures: () => S.figures, focusMode: () => S.focus,
    updateFigure (id, patch) { S.figures[id] = { ...(S.figures[id] || {}), ...patch }; clearTimeout(S.figT); S.figT = setTimeout(() => put(`/api/pieces/${slug}/figures`, { figures: S.figures }).catch(() => {}), 900) },
    uploadFigure: async file => {
      toast(t('fig.uploading'))
      try {
        const bmp = await createImageBitmap(file); const max = 2400; const k = Math.min(1, max / Math.max(bmp.width, bmp.height))
        const c = document.createElement('canvas'); c.width = Math.round(bmp.width * k); c.height = Math.round(bmp.height * k); c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height)
        const blob = await new Promise(res => c.toBlob(res, 'image/webp', 0.88))
        const r = await api('POST', `/api/pieces/${slug}/figures/upload`, blob, { headers: { 'x-width': c.width, 'x-height': c.height } })
        S.figures[r.fig_id] = r.figure; return r
      } catch (e) { toast(t('fig.fail'), 'bad'); throw e }
    },
    askSource: cb => askSource(cb),
    onChange: () => changed()
  })
  editor.view.dom.addEventListener('focusin', () => {})

  function meta2 () { return { locale: loc, title: title.value, dek: dek.value } }
  function current () { return editor.getDoc(meta2()) }
  function refreshStats () {
    const d = current(); const w = wordCount(d)
    wordsEl.textContent = t('ed.words', { n: w.toLocaleString('es') })
    const min = Math.max(1, Math.ceil(w / (loc === 'zh-Hans' ? 400 : 230)))
    byline.textContent = ''
    byline.append(h('span', { class: 'essay-by' }, t('ed.byline', { who: meta.author === 'javier' ? 'Javier' : 'Matías' })), h('span', { class: 'essay-read' }, t('ed.min', { n: min })))
  }
  function setSave (kind) {
    saveState.dataset.kind = kind
    saveState.textContent = { saved: t('ed.saved'), saving: t('ed.saving'), offline: t('ed.offline'), dirty: t('ed.dirty') }[kind]
  }
  function changed () {
    if (S.readOnly) return
    S.dirty = true; setSave('dirty'); refreshStats()
    clearTimeout(S.bufTimer); S.bufTimer = setTimeout(() => writeBuf(key, { at: Date.now(), base_rev: S.rev, doc: current() }), 250)
    clearTimeout(S.timer); S.timer = setTimeout(save, 1400)
    clearTimeout(S.chkT); S.chkT = setTimeout(() => { if (openTab === 'checks') renderDrawer() }, 2500)
  }
  async function save (force) {
    if (S.saving || S.readOnly || S.dead) return
    if (!S.dirty && !force) return
    S.saving = true; setSave('saving')
    const snapshot = current(); S.dirty = false
    try {
      const r = await put(`/api/pieces/${slug}/doc/${loc}`, { base_rev: S.rev, doc: snapshot, cursor: editor.cursor() })
      S.rev = r.rev; S.offline = false
      if (!S.dirty) { dropBuf(key); setSave('saved') } else { setSave('dirty'); S.timer = setTimeout(save, 600) }
    } catch (e) {
      S.dirty = true
      if (e instanceof ApiError && e.status === 409) conflict(e.data)
      else if (e instanceof ApiError && e.status === 0) { S.offline = true; setSave('offline'); writeBuf(key, { at: Date.now(), base_rev: S.rev, doc: snapshot }); S.timer = setTimeout(save, 5000) }
      else { setSave('dirty'); toast(t('err.generic'), 'bad'); S.timer = setTimeout(save, 8000) }
    } finally { S.saving = false }
  }
  addEventListener('online', onOnline); function onOnline () { if (S.dirty) save() }
  addEventListener('beforeunload', beforeUnload); function beforeUnload () { if (S.dirty) writeBuf(key, { at: Date.now(), base_rev: S.rev, doc: current() }) }

  function conflict (srv) {
    const mine = current()
    modal({ title: t('conf.title'), body: [h('p', null, t('conf.body', { who: srv.by || '…', at: srv.at ? new Date(srv.at).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }) : '' }))],
      actions: [
        { label: t('conf.diff'), onclick: () => { modal({ title: t('conf.diff'), wide: true, body: diffView(diffLocal(srv.doc, mine)), actions: [{ label: t('common.close') }] }) } },
        { label: t('conf.mine'), kind: 'primary', onclick: close => { S.rev = srv.rev; S.dirty = true; close(); save(true) } },
        { label: t('conf.server'), onclick: close => { S.rev = srv.rev; applyDoc(srv.doc); S.dirty = false; dropBuf(key); setSave('saved'); close() } }] })
  }
  function diffLocal (a, b) {
    const txt = d => d.blocks.map(x => ({ id: x.id, text: JSON.stringify([x.content, x.items]).replace(/"v":"([^"]*)"/g, '$1 ').replace(/\{"t":"[a-z]+"\}|[\[\]{}",:]|\bt\b|\btext\b|\bmarks\b/g, ' ').replace(/\s+/g, ' ').trim() }))
    const am = new Map(txt(a).map(x => [x.id, x.text])); const out = []
    for (const x of txt(b)) out.push({ id: x.id, status: !am.has(x.id) ? 'added' : am.get(x.id) === x.text ? 'same' : 'changed', ops: am.get(x.id) === x.text ? [{ op: 'eq', text: x.text }] : [{ op: 'del', text: am.get(x.id) || '' }, { op: 'add', text: x.text }] })
    return { blocks: out }
  }
  function applyDoc (d) { doc = d; title.value = d.title || ''; dek.value = d.dek || ''; auto(title); auto(dek); editor.setDoc(d); refreshStats() }

  title.value = doc.title || ''; dek.value = doc.dek || ''
  for (const el of [title, dek]) { el.addEventListener('input', () => { auto(el); changed() }); el.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); (el === title ? dek : { focus: () => editor.focus() }).focus() } }) }

  /* ---------- sources ---------- */
  const saveSources = () => { clearTimeout(S.srcT); S.srcT = setTimeout(() => put(`/api/pieces/${slug}/sources`, { sources: S.sources }).catch(() => toast(t('err.generic'), 'bad')), 700) }
  function askSource (cb) {
    const loc2 = h('input', { type: 'text', placeholder: t('src.locator') })
    const list = h('div', { class: 'pick-list' }, S.sources.length ? S.sources.map(s => h('button', { type: 'button', class: 'pick', onclick: () => { close(); cb({ key: s.key, locator: loc2.value.trim() }) } }, h('strong', null, s.title || s.key), h('small', null, [s.author, s.date && s.date.slice(0, 4)].filter(Boolean).join(' · ')))) : h('p', { class: 'muted' }, t('src.empty')))
    const close = modal({ title: t('src.pick'), body: [list, h('label', null, t('src.locator'), loc2)], actions: [{ label: t('common.cancel') }, { label: t('src.new'), onclick: c => { const k = 'src-' + Math.random().toString(16).slice(2, 8); S.sources.push({ key: k, title: '', author: '', date: '', url: '', accessed: '', locator: '', evidence_class: '' }); saveSources(); c(); showTab('sources'); cb({ key: k, locator: loc2.value.trim() }) } }] })
  }

  /* ---------- drawers ---------- */
  const TABS = [['toc', t('dr.toc')], ['versions', t('dr.versions')], ['sources', t('dr.sources')], ['comments', t('dr.comments')], ['checks', t('dr.checks')]]
  function showTab (id) { openTab = id === openTab ? null : id; renderDrawer(); renderRail() }
  function renderRail () { clear(rail); TABS.forEach(([id, label]) => rail.append(h('button', { type: 'button', role: 'tab', class: 'rail-btn' + (openTab === id ? ' on' : ''), 'aria-selected': openTab === id ? 'true' : 'false', onclick: () => showTab(id) }, label))) }
  async function renderDrawer () {
    drawer.hidden = !openTab; document.body.classList.toggle('drawer-open', !!openTab)
    clear(drawer); if (!openTab) return
    drawer.append(h('div', { class: 'drawer-head' }, h('h2', null, TABS.find(x => x[0] === openTab)[1]), h('button', { class: 'icon-btn', type: 'button', 'aria-label': t('dr.close'), onclick: () => showTab(openTab) }, '×')))
    const body = h('div', { class: 'drawer-body' }); drawer.append(body)
    if (openTab === 'toc') body.append(tocPanel(editor.headings(), id => editor.gotoBlock(id)))
    if (openTab === 'sources') body.append(sourcesPanel(S.sources, () => { saveSources(); editor.refresh() }))
    if (openTab === 'versions') body.append(await versionsPanel(slug, loc, { save: () => save(true), onRestored: async () => { const d = await get(`/api/pieces/${slug}/doc/${loc}`); S.rev = d.rev; applyDoc(d.doc); toast(t('ver.restored')) }, ready: () => !S.readOnly }))
    if (openTab === 'comments') body.append(await commentsPanel(slug, loc, { block: () => editor.currentBlockId(), goto: id => editor.gotoBlock(id) }))
    if (openTab === 'checks') { await save(); body.append(await checksList(slug, c => goto(c))) }
  }
  function goto (c) {
    if (!c) return
    if (c.loc && c.loc !== loc) { location.hash = `#/p/${slug}/${c.loc}`; setTimeout(() => c.block_id && window.__studioGoto && window.__studioGoto(c.block_id), 700); return }
    if (c.block_id) editor.gotoBlock(c.block_id); else title.focus()
  }
  window.__studioGoto = id => { const e = window.__studioEditor; e && e.gotoBlock(id) }
  window.__studioEditor = editor
  renderRail()

  /* ---------- bars ---------- */
  const langTabs = h('nav', { class: 'lang-tabs', 'aria-label': t('ed.lang') }, LOCS.map(l => {
    const st = (meta.locales[l] || {}).state || 'empty'
    return h('a', { href: `#/p/${slug}/${l}`, class: 'lt ' + st, 'aria-current': l === loc ? 'page' : null }, LOCALE_SHORT[l], h('span', { class: 'lt-dot', 'aria-hidden': 'true' }, { ready: '●', drafting: '◐', later: '⏸', empty: '○' }[st]))
  }))
  const focusBtn = h('button', { class: 'btn ghost small', type: 'button', 'aria-pressed': 'false', onclick: () => { S.focus = !S.focus; focusBtn.setAttribute('aria-pressed', S.focus); document.body.classList.toggle('focus-mode', S.focus); editor.refresh(); editor.view.dispatch(editor.view.state.tr) } }, h('span', { class: 'half', 'aria-hidden': 'true' }), ' ', t('ed.focus'))
  const bar = h('div', { class: 'ed-bar' },
    h('div', { class: 'ed-bar-left' }, focusBtn, wordsEl, saveState),
    langTabs,
    h('div', { class: 'ed-bar-right' }, h('a', { class: 'btn small', href: `#/p/${slug}/${loc}/translate/${loc === meta.source_locale ? LOCS.find(l => l !== loc) : loc}` }, t('ed.translate')),
      h('a', { class: 'btn small', href: `#/p/${slug}/${loc}/preview` }, t('ed.preview')), h('a', { class: 'btn primary small', href: `#/p/${slug}/publish` }, t('ed.publish'))))
  const top = h('div', { class: 'ed-top' }, h('a', { class: 'back', href: '#/' }, '← ', t('ed.back')), h('span', { class: 'ed-top-title' }, meta.title))

  // banners
  if (S.readOnly) banner.append(h('div', { class: 'banner' }, h('span', null, t('ed.readonly', { who: lockUser })), h('button', { class: 'btn small', type: 'button', onclick: async () => { await post(`/api/pieces/${slug}/lock/${loc}`, { take: true }); route() } }, t('ed.take'))))
  const buf = readBuf(key)
  if (buf && !S.readOnly && JSON.stringify(buf.doc) !== JSON.stringify(doc)) {
    const b = h('div', { class: 'banner' }, h('span', null, t('ed.restore.local')), h('button', { class: 'btn small primary', type: 'button', onclick: () => { applyDoc(buf.doc); S.dirty = true; changed(); b.remove() } }, t('ed.restore.go')), h('button', { class: 'btn small ghost', type: 'button', onclick: () => { dropBuf(key); b.remove() } }, t('ed.restore.drop')))
    banner.append(b)
  }
  if (loc !== meta.source_locale && isEmptyDoc(doc)) {
    const b = h('div', { class: 'banner' }, h('span', null, t('ed.empty.lang')), h('a', { class: 'btn small primary', href: `#/p/${slug}/${meta.source_locale}/translate/${loc}` }, t('ed.empty.start')), h('button', { class: 'btn small ghost', type: 'button', onclick: () => b.remove() }, t('ed.empty.blank')))
    banner.append(b)
  }

  root.append(shell(h('div', { class: 'ed-layout' }, top, banner, h('div', { class: 'ed-main' }, page, h('div', { class: 'drawer-col' }, rail, drawer)), bar), { active: 'home', wide: true }))
  setTimeout(() => { auto(title); auto(dek); refreshStats(); setSave('saved'); editor.restoreCursor(meta.cursor && meta.cursor[loc]); if (isEmptyDoc(doc)) title.focus() }, 0)
  const onResize = () => { auto(title); auto(dek) }
  addEventListener('resize', onResize)

  return () => {
    S.dead = true; clearTimeout(S.timer); clearInterval(heartbeat)
    removeEventListener('online', onOnline); removeEventListener('beforeunload', beforeUnload); removeEventListener('resize', onResize)
    document.body.classList.remove('drawer-open', 'focus-mode')
    if (S.dirty && !S.readOnly) { writeBuf(key, { at: Date.now(), base_rev: S.rev, doc: current() }); fetch(`/api/pieces/${slug}/doc/${loc}`, { method: 'PUT', keepalive: true, credentials: 'same-origin', headers: { 'content-type': 'application/json', 'x-csrf-token': session.me.csrf }, body: JSON.stringify({ base_rev: S.rev, doc: current(), cursor: editor.cursor() }) }).then(() => dropBuf(key)).catch(() => {}) }
    if (!S.readOnly) del(`/api/pieces/${slug}/lock/${loc}`).catch(() => {})
    editor.destroy()
  }
}
import { route } from './main.js'
