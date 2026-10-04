// The page: a ProseMirror editor styled exactly like the essay reading page.
import { EditorState, Plugin, PluginKey, TextSelection, NodeSelection } from 'prosemirror-state'
import { EditorView, Decoration, DecorationSet } from 'prosemirror-view'
import { history, undo, redo } from 'prosemirror-history'
import { keymap } from 'prosemirror-keymap'
import { baseKeymap, toggleMark, setBlockType, chainCommands, exitCode } from 'prosemirror-commands'
import { splitListItem } from 'prosemirror-schema-list'
import { schema, docToPM, pmToDoc, newId, plainText } from './docmodel.js'
import { h, clear } from './ui.js'
import { t } from './i18n.js'

const slashKey = new PluginKey('slash')
const focusKey = new PluginKey('focus')

export function createEditor (ctx) {
  // ctx: { mount, notesMount, doc, loc, sources(), figures(), updateFigure(id,patch), uploadFigure(file)->{fig_id}, askSource(cb), onChange(), readOnly, focusMode() }
  const wrap = ctx.mount
  const menuEl = h('div', { class: 'slash-menu', role: 'listbox', hidden: true })
  const bubbleEl = h('div', { class: 'bubble', role: 'toolbar', hidden: true, 'aria-label': 'Formato' })
  document.body.append(menuEl, bubbleEl)

  const sourceLabel = key => {
    const s = ctx.sources().find(x => x.key === key)
    if (!s) return key
    const base = s.title || s.author || key
    return base.length > 18 ? base.slice(0, 17) + '…' : base
  }

  /* ---------- node views ---------- */
  const figureView = (node, view, getPos) => {
    const dom = h('figure', { class: 'essay-figure ed-figure', contenteditable: 'false' })
    const render = n => {
      clear(dom)
      const id = n.attrs.fig
      const f = ctx.figures()[id] || {}
      dom.append(f.file ? h('img', { src: ctx.figureUrl(id), alt: (f.alt || {})[ctx.loc] || '', width: f.width, height: f.height }) : h('div', { class: 'fig-missing' }, t('fig.missing')))
      const field = (label, value, patch, hint, multiline) => {
        const el = multiline ? h('textarea', { rows: 2 }) : h('input', { type: 'text' })
        el.value = value || ''
        el.addEventListener('input', () => { patch(el.value); ctx.onChange() })
        return h('label', { class: 'fig-field' }, h('span', null, label), el, hint ? h('small', null, hint) : null)
      }
      dom.append(h('div', { class: 'fig-fields' },
        field(t('fig.alt', { lang: ctx.loc }), (f.alt || {})[ctx.loc], v => ctx.updateFigure(id, { alt: { ...(f.alt || {}), [ctx.loc]: v } }), t('fig.alt.h'), true),
        field(t('fig.cap', { lang: ctx.loc }), (f.caption || {})[ctx.loc], v => ctx.updateFigure(id, { caption: { ...(f.caption || {}), [ctx.loc]: v } }), '', true),
        h('div', { class: 'fig-pair' }, field(t('fig.credit'), f.credit, v => ctx.updateFigure(id, { credit: v })), field(t('fig.licence'), f.licence, v => ctx.updateFigure(id, { licence: v })))))
    }
    render(node)
    return { dom, stopEvent: e => dom.contains(e.target) && /INPUT|TEXTAREA|LABEL/.test(e.target.tagName), ignoreMutation: () => true, update: n => n.type === node.type && (render(n), true), selectNode () { dom.classList.add('sel') }, deselectNode () { dom.classList.remove('sel') } }
  }
  const evidenceView = (node, view, getPos) => {
    const dom = h('aside', { class: 'evidence-box ed-evidence', 'data-class': node.attrs.class })
    const contentDOM = h('div', { class: 'ev-limits', 'data-ph': t('ev.limits') })
    const select = h('select', { 'aria-label': t('ev.class'), contenteditable: 'false' }, ['A', 'B', 'C', 'D'].map(c => h('option', { value: c, selected: c === node.attrs.class }, t('ev.' + c))))
    const conf = h('input', { type: 'text', 'aria-label': t('ev.conf'), placeholder: t('ev.conf'), value: node.attrs.confidence || '', contenteditable: 'false' })
    const patch = attrs => { const pos = getPos(); view.dispatch(view.state.tr.setNodeMarkup(pos, null, { ...view.state.doc.nodeAt(pos).attrs, ...attrs })) }
    select.addEventListener('change', () => patch({ class: select.value }))
    conf.addEventListener('input', () => patch({ confidence: conf.value }))
    const head = h('div', { class: 'ev-head', contenteditable: 'false' }, h('strong', null, t('ev.title')), select, conf)
    dom.append(head, contentDOM)
    return { dom, contentDOM, stopEvent: e => head.contains(e.target), ignoreMutation: m => head.contains(m.target), update: n => { if (n.type !== node.type) return false; dom.dataset.class = n.attrs.class; if (select.value !== n.attrs.class) select.value = n.attrs.class; return true } }
  }
  const fnView = node => { const dom = h('sup', { class: 'fn-ref', 'data-fn': node.attrs.id, title: t('slash.fn') }); return { dom, update: n => n.type === node.type } }
  const citeView = node => {
    const dom = h('cite', { class: 'src-ref', 'data-key': node.attrs.key }); const set = n => { dom.textContent = `[${sourceLabel(n.attrs.key)}${n.attrs.locator ? ', ' + n.attrs.locator : ''}]` }
    set(node); return { dom, update: n => n.type === node.type && (set(n), true) }
  }

  /* ---------- notes (margin or end) ---------- */
  const notesEl = ctx.notesMount
  const noteEls = new Map()
  let view
  function renderNotes () {
    const fns = []
    view.state.doc.descendants((n, pos) => { if (n.type.name === 'fn') fns.push({ n, pos }) })
    const seen = new Set()
    const margin = matchMedia('(min-width:1100px)').matches
    notesEl.classList.toggle('margin', margin)
    let floor = 0
    const base = notesEl.getBoundingClientRect().top + scrollY
    fns.forEach(({ n, pos }, i) => {
      seen.add(n.attrs.id)
      let el = noteEls.get(n.attrs.id)
      if (!el) {
        const input = h('div', { class: 'note-text', contenteditable: ctx.readOnly ? 'false' : 'plaintext-only', role: 'textbox', 'aria-label': t('slash.fn'), 'data-ph': t('fn.placeholder'), spellcheck: 'true' })
        input.addEventListener('input', () => {
          const p = findFn(n.attrs.id); if (p == null) return
          const text = input.textContent
          view.dispatch(view.state.tr.setNodeAttribute(p, 'body', text ? [{ t: 'text', v: text }] : []).setMeta('noteEdit', true))
        })
        el = h('div', { class: 'note', 'data-fn': n.attrs.id }, h('span', { class: 'note-n' }), input)
        el.querySelector('.note-n').addEventListener('click', () => { const p = findFn(n.attrs.id); if (p != null) { view.dispatch(view.state.tr.setSelection(NodeSelection.create(view.state.doc, p))); view.focus() } })
        noteEls.set(n.attrs.id, el); notesEl.append(el)
      }
      el.querySelector('.note-n').textContent = i + 1
      const input = el.querySelector('.note-text')
      const want = plainText(n.attrs.body)
      if (document.activeElement !== input && input.textContent !== want) input.textContent = want
      el.style.top = ''
      if (margin) {
        const y = Math.max(view.coordsAtPos(pos).top + scrollY - base - 4, floor)
        el.style.top = y + 'px'; el.style.position = 'absolute'
        floor = y + el.offsetHeight + 10
      } else el.style.position = ''
      if (notesEl.children[i + 1] !== el) notesEl.insertBefore(el, notesEl.children[i + 1] || null)
    })
    for (const [id, el] of noteEls) if (!seen.has(id)) { el.remove(); noteEls.delete(id) }
    notesEl.hidden = fns.length === 0
  }
  const findFn = id => { let found = null; view.state.doc.descendants((n, pos) => { if (found == null && n.type.name === 'fn' && n.attrs.id === id) found = pos }); return found }
  function focusNote (id) { const el = noteEls.get(id); if (el) { el.querySelector('.note-text').focus(); el.scrollIntoView({ block: 'center' }) } }

  /* ---------- commands ---------- */
  const emptyPara = state => { const { $from } = state.selection; return $from.parent.type.name === 'p' && $from.parent.content.size === 0 }
  const blockRange = state => { const { $from } = state.selection; return { from: $from.before(), to: $from.after(), node: $from.parent } }
  function replaceBlock (state, nodes, selectIn) {
    const { from, to } = blockRange(state)
    const tr = state.tr.replaceWith(from, to, nodes)
    if (selectIn !== false) tr.setSelection(TextSelection.near(tr.doc.resolve(Math.min(from + 1, tr.doc.content.size)), 1))
    return tr.scrollIntoView()
  }
  const para = () => schema.nodes.p.create({ id: newId('b') })
  const items = [
    { id: 'h2', run: (s, d) => d(setBlockTypeTr(s, 'h2')) },
    { id: 'h3', run: (s, d) => d(setBlockTypeTr(s, 'h3')) },
    { id: 'quote', run: (s, d) => d(setBlockTypeTr(s, 'blockquote')) },
    { id: 'pull', run: (s, d) => d(setBlockTypeTr(s, 'pullquote')) },
    { id: 'ul', run: (s, d) => d(replaceBlock(s, schema.nodes.ul.create({ id: newId('b') }, schema.nodes.li.create()))) },
    { id: 'ol', run: (s, d) => d(replaceBlock(s, schema.nodes.ol.create({ id: newId('b') }, schema.nodes.li.create()))) },
    { id: 'hr', run: (s, d) => { const { from } = blockRange(s); const tr = replaceBlock(s, [schema.nodes.hr.create({ id: newId('b') }), para()], false); tr.setSelection(TextSelection.near(tr.doc.resolve(from + 2), 1)); d(tr) } },
    { id: 'fig', run: () => pickFigure() },
    { id: 'fn', run: (s, d) => insertFootnote() },
    { id: 'src', run: () => insertSource() },
    { id: 'ev', run: (s, d) => d(replaceBlock(s, schema.nodes.evidence.create({ id: newId('b'), class: 'B', confidence: '' }))) },
    { id: 'p', run: (s, d) => d(setBlockTypeTr(s, 'p')) }
  ]
  function setBlockTypeTr (state, type) {
    const { $from } = state.selection
    const attrs = { id: $from.parent.attrs.id || newId('b') }
    return state.tr.setBlockType($from.before(), $from.after(), schema.nodes[type], attrs).scrollIntoView()
  }
  function insertFootnote () {
    const id = newId('fn'); const { from, to } = view.state.selection
    const tr = view.state.tr.replaceWith(from, to, schema.nodes.fn.create({ id, body: [] }))
    view.dispatch(tr); setTimeout(() => focusNote(id), 30); return true
  }
  function insertSource () {
    ctx.askSource(({ key, locator }) => {
      view.focus(); const { from, to } = view.state.selection
      view.dispatch(view.state.tr.replaceWith(from, to, schema.nodes.cite.create({ key, locator: locator || '' })))
    })
    return true
  }
  async function pickFigure () {
    const input = h('input', { type: 'file', accept: 'image/*', hidden: true }); document.body.append(input)
    input.addEventListener('change', async () => {
      const file = input.files[0]; input.remove(); if (!file) return
      try {
        const { fig_id: figId } = await ctx.uploadFigure(file)
        const state = view.state
        const block = schema.nodes.figure.create({ id: newId('b'), fig: figId })
        const { $from } = state.selection
        const tr = $from.parent.type.name === 'p' && $from.parent.content.size === 0 ? state.tr.replaceWith($from.before(), $from.after(), [block, para()]) : state.tr.insert($from.after(), [block, para()])
        view.dispatch(tr.scrollIntoView())
      } catch (e) { ctx.onFigureError && ctx.onFigureError(e) }
    })
    input.click()
  }

  /* ---------- slash menu ---------- */
  let slashIdx = 0; let slashList = []
  function closeSlash () { menuEl.hidden = true; slashList = [] }
  function slashState (state) {
    const { selection } = state; if (!selection.empty || ctx.readOnly) return null
    const { $from } = selection; if ($from.parent.type.name !== 'p') return null
    const text = $from.parent.textContent
    const m = /^\/([\p{L} ]{0,20})$/u.exec(text); if (!m || $from.parentOffset !== text.length) return null
    return { query: m[1].toLowerCase(), from: $from.start(), to: $from.pos }
  }
  const labelOf = id => t('slash.' + id)
  function showSlash (v, st) {
    const q = st.query.normalize('NFD').replace(/[̀-ͯ]/g, '')
    slashList = items.filter(i => !q || labelOf(i.id).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').includes(q))
    slashIdx = Math.min(slashIdx, Math.max(0, slashList.length - 1))
    clear(menuEl)
    if (!slashList.length) menuEl.append(h('div', { class: 'slash-none' }, t('slash.none')))
    slashList.forEach((it, i) => menuEl.append(h('button', { type: 'button', role: 'option', 'aria-selected': i === slashIdx ? 'true' : 'false', class: 'slash-item' + (i === slashIdx ? ' on' : ''), onmousedown: e => { e.preventDefault(); chooseSlash(i) } },
      h('span', { class: 'slash-glyph', 'aria-hidden': 'true' }, { h2: 'H2', h3: 'H3', quote: '“', pull: '❝', ul: '•', ol: '1.', hr: '—', fig: '▣', fn: '¹', src: '[ ]', ev: '◧', p: '¶' }[it.id]),
      h('span', null, h('strong', null, labelOf(it.id)), h('small', null, t('slash.' + it.id + '.d'))))))
    const c = v.coordsAtPos(st.to); menuEl.hidden = false
    const w = Math.min(320, innerWidth - 24)
    menuEl.style.width = w + 'px'; menuEl.style.left = Math.max(12, Math.min(c.left, innerWidth - w - 12)) + 'px'
    const below = c.bottom + 8; const room = innerHeight - below
    menuEl.style.top = (room > 280 ? below : Math.max(8, c.top - menuEl.offsetHeight - 8)) + scrollY + 'px'
    const on = menuEl.querySelector('.on'); on && on.scrollIntoView({ block: 'nearest' })
  }
  function chooseSlash (i) {
    const st = slashState(view.state); const it = slashList[i]; if (!st || !it) return
    closeSlash()
    let tr = view.state.tr.delete(st.from, st.to); view.dispatch(tr)
    view.focus(); it.run(view.state, v => v && view.dispatch(v))
  }

  /* ---------- bubble ---------- */
  function updateBubble (v) {
    const sel = v.state.selection
    if (sel.empty || ctx.readOnly || sel instanceof NodeSelection || !sel.$from.parent.inlineContent) { bubbleEl.hidden = true; return }
    const a = v.coordsAtPos(sel.from); const b = v.coordsAtPos(sel.to)
    bubbleEl.hidden = false
    const w = bubbleEl.offsetWidth
    bubbleEl.style.left = Math.max(8, Math.min((a.left + b.right) / 2 - w / 2, innerWidth - w - 8)) + scrollX + 'px'
    bubbleEl.style.top = Math.max(8, a.top - bubbleEl.offsetHeight - 10) + scrollY + 'px'
    for (const btn of bubbleEl.querySelectorAll('[data-mark]')) btn.classList.toggle('on', v.state.doc.rangeHasMark(sel.from, sel.to, schema.marks[btn.dataset.mark]))
  }
  const link = () => {
    const sel = view.state.selection
    if (view.state.doc.rangeHasMark(sel.from, sel.to, schema.marks.link)) return toggleMark(schema.marks.link)(view.state, view.dispatch)
    const href = prompt(t('link.ask'), 'https://'); if (!href) return
    if (!/^https:\/\/\S+$/i.test(href)) { alert(t('link.bad')); return }
    toggleMark(schema.marks.link, { href })(view.state, view.dispatch)
  }
  const btn = (label, title, fn, mark) => h('button', { type: 'button', title, 'aria-label': title, 'data-mark': mark, onmousedown: e => { e.preventDefault(); fn(); view.focus() } }, label)
  bubbleEl.append(btn('B', t('bub.b'), () => toggleMark(schema.marks.strong)(view.state, view.dispatch), 'strong'), btn('I', t('bub.i'), () => toggleMark(schema.marks.em)(view.state, view.dispatch), 'em'),
    btn(t('bub.link'), t('bub.link'), link, 'link'), btn(t('bub.fn'), t('bub.fn'), insertFootnote), btn(t('bub.src'), t('bub.src'), insertSource))

  /* ---------- plugins ---------- */
  const ids = new Plugin({
    appendTransaction (trs, old, state) {
      if (!trs.some(x => x.docChanged)) return null
      const seen = new Set(); let tr = null
      state.doc.descendants((n, pos) => {
        if (n.type.spec.attrs && 'id' in n.type.spec.attrs && n.type.name !== 'fn') {
          if (!n.attrs.id || seen.has(n.attrs.id)) { tr = (tr || state.tr).setNodeAttribute(pos, 'id', newId('b')); }
          else seen.add(n.attrs.id)
        }
      })
      return tr
    }
  })
  const slash = new Plugin({
    key: slashKey,
    view: () => ({ update: v => { const st = slashState(v.state); if (st) { if (menuEl.hidden || true) showSlash(v, st) } else closeSlash() } }),
    props: {
      handleKeyDown (v, e) {
        if (menuEl.hidden || !slashList.length) { if (e.key === 'Escape') closeSlash(); return false }
        if (e.key === 'ArrowDown') { slashIdx = (slashIdx + 1) % slashList.length; showSlash(v, slashState(v.state)); return true }
        if (e.key === 'ArrowUp') { slashIdx = (slashIdx - 1 + slashList.length) % slashList.length; showSlash(v, slashState(v.state)); return true }
        if (e.key === 'Enter' || e.key === 'Tab') { chooseSlash(slashIdx); return true }
        if (e.key === 'Escape') { closeSlash(); return true }
        return false
      }
    }
  })
  const focusPlugin = new Plugin({
    key: focusKey,
    props: {
      decorations (state) {
        const { $from } = state.selection; if (!ctx.focusMode() || $from.depth < 1) return DecorationSet.empty
        return DecorationSet.create(state.doc, [Decoration.node($from.before(1), $from.after(1), { class: 'cur' })])
      }
    },
    view: () => ({ update (v, prev) { if (ctx.focusMode() && !v.state.selection.eq(prev.selection) && v.hasFocus()) { const c = v.coordsAtPos(v.state.selection.head); const target = innerHeight * 0.42; const d = c.top - target; if (Math.abs(d) > 30) scrollBy({ top: d, behavior: 'smooth' }) } } })
  })
  const enterKey = chainCommands(splitListItem(schema.nodes.li), (state, dispatch) => {
    const { $from } = state.selection
    if (['pullquote', 'blockquote', 'evidence'].includes($from.parent.type.name) && $from.parent.content.size === $from.parentOffset && $from.parent.textContent === '' ) { if (dispatch) dispatch(setBlockTypeTr(state, 'p')); return true }
    return false
  })
  const cursorDeco = new Plugin({ props: { attributes: { spellcheck: 'true' } } })
  const state = EditorState.create({
    doc: docToPM(ctx.doc),
    plugins: [history(), ids, slash, focusPlugin, cursorDeco,
      keymap({ 'Mod-z': undo, 'Mod-y': redo, 'Shift-Mod-z': redo, 'Mod-b': toggleMark(schema.marks.strong), 'Mod-i': toggleMark(schema.marks.em), 'Mod-k': () => { link(); return true }, Enter: enterKey, 'Shift-Enter': exitCode }),
      keymap(baseKeymap)]
  })
  view = new EditorView(wrap, {
    state, editable: () => !ctx.readOnly,
    nodeViews: { figure: figureView, evidence: evidenceView, fn: fnView, cite: citeView },
    handleClickOn (v, pos, node) { if (node.type.name === 'fn') { focusNote(node.attrs.id); return true } return false },
    attributes: { 'aria-label': t('ed.title'), 'aria-multiline': 'true', role: 'textbox', class: 'essay-body ed-body' },
    dispatchTransaction: tr => { const next = view.state.apply(tr); view.updateState(next); updateBubble(view); renderNotes(); syncEmpty(); if (tr.docChanged && !tr.getMeta('remote')) ctx.onChange() }
  })
  function syncEmpty () { wrap.classList.toggle('is-empty', empty()) }
  const empty = () => view.state.doc.childCount === 1 && view.state.doc.firstChild.type.name === 'p' && view.state.doc.firstChild.content.size === 0
  wrap.dataset.ph = t('ed.start')
  renderNotes(); syncEmpty()
  const mq = matchMedia('(min-width:1100px)'); const relayout = () => renderNotes()
  mq.addEventListener('change', relayout); addEventListener('resize', relayout); document.fonts && document.fonts.ready.then(relayout)
  addEventListener('scroll', () => updateBubble(view), { passive: true })

  return {
    view,
    getDoc: meta => pmToDoc(view.state.doc, meta),
    setDoc (doc) { const next = EditorState.create({ doc: docToPM(doc), plugins: view.state.plugins }); view.updateState(next); noteEls.forEach(e => e.remove()); noteEls.clear(); renderNotes(); syncEmpty() },
    cursor () { return { anchor: view.state.selection.anchor, head: view.state.selection.head } },
    restoreCursor (c) { try { if (c && c.anchor <= view.state.doc.content.size) view.dispatch(view.state.tr.setSelection(TextSelection.near(view.state.doc.resolve(c.anchor)))) } catch { /* stale cursor */ } },
    currentBlockId () { const { $from } = view.state.selection; return $from.depth ? $from.node(1).attrs.id : null },
    gotoBlock (id) { let pos = null; view.state.doc.forEach((n, off) => { if (n.attrs.id === id) pos = off }); if (pos == null) return false; const dom = view.nodeDOM(pos); dom && dom.scrollIntoView({ block: 'center', behavior: 'smooth' }); const node = view.state.doc.nodeAt(pos); view.dispatch(view.state.tr.setSelection(node.type.name === 'figure' ? NodeSelection.create(view.state.doc, pos) : TextSelection.near(view.state.doc.resolve(pos + 1)))); return true },
    headings () { const out = []; view.state.doc.forEach((n, off) => { if (n.type.name === 'h2' || n.type.name === 'h3') out.push({ id: n.attrs.id, level: n.type.name, text: n.textContent }) }); return out },
    refresh () { renderNotes() },
    refreshSources () { view.updateState(view.state) ; view.dispatch(view.state.tr.setMeta('refresh', true)) },
    insertSource, insertFootnote, focus: () => view.focus(),
    focusEnd () { view.focus(); view.dispatch(view.state.tr.setSelection(TextSelection.atEnd(view.state.doc)).scrollIntoView()) },
    focusStart () { view.focus(); view.dispatch(view.state.tr.setSelection(TextSelection.atStart(view.state.doc))) },
    destroy () { view.destroy(); menuEl.remove(); bubbleEl.remove() }
  }
}
