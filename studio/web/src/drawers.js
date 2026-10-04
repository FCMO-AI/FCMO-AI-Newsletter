import { get, post, put } from './api.js'
import { t } from './i18n.js'
import { h, clear, ago, modal, toast } from './ui.js'
import { diffView } from './diffview.js'

export function tocPanel (heads, go) {
  if (!heads.length) return h('p', { class: 'muted' }, t('dr.toc.empty'))
  let n = 0
  return h('ol', { class: 'toc-list' }, heads.map(x => { if (x.level === 'h2') n++; return h('li', { class: x.level }, h('button', { type: 'button', class: 'link-btn', onclick: () => go(x.id) }, x.level === 'h2' ? h('span', { class: 'n' }, String(n).padStart(2, '0')) : null, x.text || '…')) }))
}

export function sourcesPanel (sources, changed) {
  const root = h('div', { class: 'sources' })
  const draw = () => {
    clear(root)
    root.append(h('p', { class: 'hint' }, t('src.hint')))
    if (!sources.length) root.append(h('p', { class: 'muted' }, t('src.empty')))
    sources.forEach((s, i) => {
      const f = (label, k, type = 'text') => { const el = h('input', { type, value: s[k] || '' }); el.addEventListener('input', () => { s[k] = el.value; changed() }); return h('label', { class: 'f' }, h('span', null, label), el) }
      const cls = h('select', null, ['', 'A', 'B', 'C', 'D'].map(c => h('option', { value: c, selected: (s.evidence_class || '') === c }, c ? t('ev.' + c) : t('src.none'))))
      cls.addEventListener('change', () => { if (cls.value) s.evidence_class = cls.value; else delete s.evidence_class; changed() })
      root.append(h('details', { class: 'src', open: !s.title }, h('summary', null, h('strong', null, s.title || t('src.title')), h('small', null, [s.author, (s.date || '').slice(0, 4)].filter(Boolean).join(' · '))),
        f(t('src.title'), 'title'), f(t('src.author'), 'author'), f(t('src.publisher'), 'publisher'), h('div', { class: 'two' }, f(t('src.date'), 'date', 'date'), f(t('src.accessed'), 'accessed', 'date')), f(t('src.url'), 'url', 'url'), f(t('src.locator'), 'locator'),
        h('label', { class: 'f' }, h('span', null, t('src.class')), cls),
        h('button', { class: 'link-btn danger', type: 'button', onclick: () => { sources.splice(i, 1); changed(); draw() } }, t('src.del'))))
    })
    root.append(h('button', { class: 'btn small', type: 'button', onclick: () => { sources.push({ key: 'src-' + Math.random().toString(16).slice(2, 8), title: '', author: '', date: '', url: '', accessed: new Date().toISOString().slice(0, 10), publisher: '', locator: '' }); changed(); draw() } }, '+ ', t('src.add')))
  }
  draw(); return root
}

export async function checksList (slug, onGo, { lang = 'es' } = {}) {
  const list = await get(`/api/pieces/${slug}/checks`)
  const bad = list.filter(c => !c.ok)
  const root = h('div', { class: 'checks' }, h('p', { class: 'checks-sum ' + (bad.length ? 'todo' : 'ok') }, bad.length ? t('chk.todo', { n: bad.length }) : t('chk.ok')))
  const ul = h('ul', { class: 'check-list' }, list.map(c => h('li', { class: c.ok ? 'ok' : 'todo' },
    h('span', { class: 'mark', 'aria-hidden': 'true' }, c.ok ? '✓' : '○'), h('span', { class: 'sr-only' }, c.ok ? 'Listo: ' : 'Pendiente: '),
    h('span', { class: 'ctext' }, lang === 'en' ? c.plain_en : c.plain_es),
    !c.ok && c.goto ? h('button', { class: 'link-btn', type: 'button', onclick: () => onGo(c.goto) }, t('chk.go'), ' →') : null)))
  root.append(ul); root.list = list; return root
}

export async function versionsPanel (slug, loc, { save, onRestored, ready }) {
  const root = h('div', { class: 'versions' })
  const list = await get(`/api/pieces/${slug}/versions`)
  const name = h('input', { type: 'text', placeholder: t('ver.name') })
  root.append(h('div', { class: 'ver-new' }, name, h('button', { class: 'btn small', type: 'button', onclick: async () => { await save(); await post(`/api/pieces/${slug}/versions`, { name: name.value.trim() }); name.value = ''; toast(t('common.save') + ' ✓'); const fresh = await versionsPanel(slug, loc, { save, onRestored, ready }); root.replaceWith(fresh) } }, t('ver.save'))))
  if (!list.length) root.append(h('p', { class: 'muted' }, t('ver.empty')))
  root.append(h('ol', { class: 'ver-list' }, list.map(v => h('li', null,
    h('div', { class: 'ver-main' }, h('strong', null, v.name || t('ver.auto')), h('small', null, ago(v.at, t), ' · ', t('ver.by', { who: v.user }))),
    h('div', { class: 'ver-act' },
      h('button', { class: 'link-btn', type: 'button', onclick: async () => { const d = await get(`/api/pieces/${slug}/diff?from=${v.rev}&to=current&loc=${loc}`); modal({ title: t('ver.compare'), wide: true, body: diffView(d), actions: [{ label: t('common.close') }] }) } }, t('ver.compare')),
      ready() ? h('button', { class: 'link-btn', type: 'button', onclick: () => modal({ title: t('ver.restore') + ' · ' + (v.name || ago(v.at, t)), body: h('p', null, t('ver.confirm')), actions: [{ label: t('common.cancel') }, { label: t('ver.restore'), kind: 'primary', onclick: async close => { await save(); await post(`/api/pieces/${slug}/versions/${v.rev}/restore`); close(); onRestored() } }] }) }, t('ver.restore')) : null))))) 
  return root
}

export async function commentsPanel (slug, loc, { block, goto }) {
  const root = h('div', { class: 'comments' })
  const all = await get(`/api/pieces/${slug}/comments`)
  const open = all.filter(c => !c.resolved_at)
  const ta = h('textarea', { rows: 3, placeholder: t('cmt.ph'), 'aria-label': t('cmt.add') })
  root.append(h('p', { class: 'hint' }, t('cmt.never')), h('div', { class: 'cmt-new' }, ta, h('button', { class: 'btn small', type: 'button', onclick: async () => { if (!ta.value.trim()) return; await post(`/api/pieces/${slug}/comments`, { locale: loc, block_id: block(), body: ta.value.trim() }); const fresh = await commentsPanel(slug, loc, { block, goto }); root.replaceWith(fresh) } }, t('cmt.send'))))
  if (!open.length) root.append(h('p', { class: 'muted' }, t('cmt.empty')))
  open.forEach(c => root.append(h('div', { class: 'cmt' }, h('p', { class: 'cmt-meta' }, h('strong', null, c.user), ' · ', ago(c.at, t)), h('p', null, c.body),
    h('div', { class: 'ver-act' }, c.block_id ? h('button', { class: 'link-btn', type: 'button', onclick: () => goto(c.block_id) }, t('cmt.go')) : null,
      h('button', { class: 'link-btn', type: 'button', onclick: async () => { await post(`/api/comments/${c.id}/resolve`); const fresh = await commentsPanel(slug, loc, { block, goto }); root.replaceWith(fresh) } }, t('cmt.resolve'))))))
  return root
}
