// Tiny DOM helpers. All text goes through textContent; no innerHTML anywhere.
export function h (tag, props, ...kids) {
  const el = document.createElement(tag)
  for (const [k, v] of Object.entries(props || {})) {
    if (v === false || v == null) continue
    if (k === 'class') el.className = v
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v)
    else if (k === 'dataset') Object.assign(el.dataset, v)
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v)
    else if (v === true) el.setAttribute(k, '')
    else el.setAttribute(k, v)
  }
  append(el, kids)
  return el
}
export function append (el, kids) {
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false) continue
    el.append(k instanceof Node ? k : document.createTextNode(String(k)))
  }
  return el
}
export const clear = el => { while (el.firstChild) el.firstChild.remove(); return el }
export const $ = (sel, root = document) => root.querySelector(sel)

export function ago (iso, t) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (s < 60) return t('ago.now')
  if (s < 3600) return t('ago.min', { n: Math.round(s / 60) })
  if (s < 86400) return t('ago.hour', { n: Math.round(s / 3600) })
  return t('ago.day', { n: Math.round(s / 86400) })
}
export function toast (msg, kind = '') {
  let box = document.getElementById('toasts')
  if (!box) { box = h('div', { id: 'toasts', role: 'status' }); document.body.append(box) }
  const el = h('div', { class: 'toast ' + kind }, msg)
  box.append(el); setTimeout(() => el.remove(), 4200)
}
const openModals = new Set()
export function closeModals () { for (const close of [...openModals]) close('route') }
export function modal ({ title, body, actions = [], wide = false, onClose }) {
  const back = h('div', { class: 'modal-back' })
  let closed = false
  const close = reason => { if (closed) return; closed = true; openModals.delete(close); back.remove(); document.removeEventListener('keydown', onKey); onClose && onClose(reason) }
  const onKey = e => { if (e.key === 'Escape') close() }
  const dlg = h('div', { class: 'modal' + (wide ? ' wide' : ''), role: 'dialog', 'aria-modal': 'true', 'aria-label': title },
    h('h2', null, title), h('div', { class: 'modal-body' }, body),
    h('div', { class: 'modal-actions' }, actions.map(a => h('button', { class: 'btn ' + (a.kind || ''), type: 'button', onclick: () => { if (a.onclick) a.onclick(close); else close() } }, a.label))))
  openModals.add(close); back.append(dlg); document.body.append(back); document.addEventListener('keydown', onKey)
  const first = dlg.querySelector('input,textarea,button.primary,button'); first && first.focus()
  return close
}
export function dots (locales, t) {
  const sym = s => s.state === 'ready' ? '●' : s.state === 'drafting' ? '◐' : s.state === 'later' ? '⏸' : '○'
  const name = { en: 'EN', 'es-419': 'ES', 'zh-Hans': '中文' }
  return h('span', { class: 'lang-dots', role: 'img', 'aria-label': Object.entries(locales).map(([l, s]) => `${name[l]} ${t('state.' + (s.state || 'empty'))}`).join(', ') },
    ['en', 'es-419', 'zh-Hans'].map(l => h('span', { class: 'ld ' + ((locales[l] || {}).state || 'empty'), 'aria-hidden': 'true' }, name[l], ' ', sym(locales[l] || {}))))
}
