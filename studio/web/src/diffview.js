import { h } from './ui.js'
const LABEL = { added: 'nuevo', removed: 'quitado', changed: 'cambiado' }
export function diffView (diff, { showSame = false } = {}) {
  const blocks = diff.blocks || []
  const changed = blocks.filter(b => b.status !== 'same')
  const root = h('div', { class: 'diff' })
  if (diff.title && diff.title.some(o => o.op !== 'eq')) root.append(h('p', { class: 'diff-block title' }, opsEl(diff.title)))
  if (!changed.length) root.append(h('p', { class: 'muted' }, 'Sin diferencias.'))
  for (const b of showSame ? blocks : changed) root.append(h('p', { class: 'diff-block ' + b.status }, b.status !== 'same' ? h('span', { class: 'diff-tag' }, LABEL[b.status]) : null, opsEl(b.ops)))
  const same = blocks.length - changed.length
  if (!showSame && same && changed.length) root.append(h('p', { class: 'muted small' }, `${same} párrafos sin cambios`))
  return root
}
function opsEl (ops) {
  return h('span', null, (ops || []).map(o => o.op === 'add' ? h('ins', null, o.text) : o.op === 'del' ? h('del', null, o.text) : o.text))
}
