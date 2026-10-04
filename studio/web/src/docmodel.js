// Closed document model: fcmo-essay-doc-v1 <-> ProseMirror. No raw HTML node exists.
import { Schema } from 'prosemirror-model'

const hex = n => [...crypto.getRandomValues(new Uint8Array(n / 2))].map(b => b.toString(16).padStart(2, '0')).join('')
export const newId = prefix => `${prefix}-${hex(8)}`
const idAttr = { id: { default: '' } }
const safeHref = h => typeof h === 'string' && (/^https:\/\//i.test(h) || (h.startsWith('/') && !h.startsWith('//')))

export const schema = new Schema({
  nodes: {
    doc: { content: 'block+' },
    text: { group: 'inline' },
    p: { group: 'block', content: 'inline*', attrs: idAttr, parseDOM: [{ tag: 'p' }], toDOM: n => ['p', { 'data-id': n.attrs.id }, 0] },
    h2: { group: 'block', content: 'inline*', attrs: idAttr, defining: true, parseDOM: [{ tag: 'h2' }], toDOM: n => ['h2', { 'data-id': n.attrs.id }, 0] },
    h3: { group: 'block', content: 'inline*', attrs: idAttr, defining: true, parseDOM: [{ tag: 'h3' }], toDOM: n => ['h3', { 'data-id': n.attrs.id }, 0] },
    blockquote: { group: 'block', content: 'inline*', attrs: { ...idAttr, cite: { default: '' } }, defining: true, parseDOM: [{ tag: 'blockquote' }], toDOM: n => ['blockquote', { 'data-id': n.attrs.id }, 0] },
    pullquote: { group: 'block', content: 'inline*', attrs: idAttr, defining: true, parseDOM: [{ tag: 'aside.pullquote' }], toDOM: n => ['aside', { class: 'pullquote', 'data-id': n.attrs.id }, 0] },
    ul: { group: 'block', content: 'li+', attrs: idAttr, parseDOM: [{ tag: 'ul' }], toDOM: n => ['ul', { 'data-id': n.attrs.id }, 0] },
    ol: { group: 'block', content: 'li+', attrs: idAttr, parseDOM: [{ tag: 'ol' }], toDOM: n => ['ol', { 'data-id': n.attrs.id }, 0] },
    li: { content: 'inline*', defining: true, parseDOM: [{ tag: 'li' }], toDOM: () => ['li', 0] },
    hr: { group: 'block', attrs: idAttr, parseDOM: [{ tag: 'hr' }], toDOM: n => ['hr', { 'data-id': n.attrs.id }] },
    figure: { group: 'block', atom: true, selectable: true, draggable: true, attrs: { ...idAttr, fig: { default: '' } }, toDOM: n => ['figure', { 'data-fig': n.attrs.fig, 'data-id': n.attrs.id }] },
    evidence: { group: 'block', content: 'inline*', defining: true, attrs: { ...idAttr, class: { default: 'B' }, confidence: { default: '' } }, toDOM: n => ['aside', { class: 'evidence-box', 'data-class': n.attrs.class, 'data-id': n.attrs.id }, 0] },
    fn: { group: 'inline', inline: true, atom: true, selectable: true, attrs: { id: { default: '' }, body: { default: [] } }, toDOM: n => ['sup', { class: 'fn-ref', 'data-fn': n.attrs.id }, '•'] },
    cite: { group: 'inline', inline: true, atom: true, selectable: true, attrs: { key: { default: '' }, locator: { default: '' } }, toDOM: n => ['cite', { class: 'src-ref', 'data-key': n.attrs.key }, `[${n.attrs.key}]`] }
  },
  marks: {
    em: { parseDOM: [{ tag: 'em' }, { tag: 'i' }], toDOM: () => ['em', 0] },
    strong: { parseDOM: [{ tag: 'strong' }, { tag: 'b' }], toDOM: () => ['strong', 0] },
    link: { attrs: { href: {} }, inclusive: false, parseDOM: [{ tag: 'a[href]', getAttrs: d => (safeHref(d.getAttribute('href')) ? { href: d.getAttribute('href') } : false) }], toDOM: m => ['a', { href: m.attrs.href }, 0] },
    lang: { attrs: { lang: { default: 'en' } }, inclusive: false, toDOM: m => ['span', { lang: m.attrs.lang, class: 'quote-orig' }, 0] }
  }
})

const TEXT_BLOCKS = new Set(['p', 'h2', 'h3', 'blockquote', 'pullquote'])

function inlineToPM (nodes, marks = []) {
  const out = []
  for (const n of nodes || []) {
    if (n.t === 'text') {
      const ms = [...marks, ...(n.marks || []).filter(m => m === 'em' || m === 'strong').map(m => schema.marks[m].create())]
      if (n.v) out.push(schema.text(n.v, ms))
    } else if (n.t === 'link') {
      if (safeHref(n.href)) out.push(...inlineToPM(n.c, [...marks, schema.marks.link.create({ href: n.href })]))
      else out.push(...inlineToPM(n.c, marks))
    } else if (n.t === 'lang') out.push(...inlineToPM(n.c, [...marks, schema.marks.lang.create({ lang: n.lang })]))
    else if (n.t === 'fn') out.push(schema.nodes.fn.create({ id: n.id }))
    else if (n.t === 'cite') out.push(schema.nodes.cite.create({ key: n.key, locator: n.locator || '' }))
    else throw new Error(`unknown inline ${n.t}`)
  }
  return out
}

export function docToPM (doc) {
  const blocks = doc.blocks.map(b => {
    const id = b.id || newId('b')
    if (TEXT_BLOCKS.has(b.type)) {
      const attrs = { id }
      if (b.type === 'blockquote') attrs.cite = (b.attrs && b.attrs.cite) || ''
      return schema.nodes[b.type].create(attrs, inlineToPM(b.content))
    }
    if (b.type === 'ul' || b.type === 'ol') return schema.nodes[b.type].create({ id }, (b.items || []).map(it => schema.nodes.li.create(null, inlineToPM(it))))
    if (b.type === 'hr') return schema.nodes.hr.create({ id })
    if (b.type === 'figure') return schema.nodes.figure.create({ id, fig: (b.attrs || {}).fig || '' })
    if (b.type === 'evidence') return schema.nodes.evidence.create({ id, class: (b.attrs || {}).class || 'B', confidence: (b.attrs || {}).confidence || '' }, inlineToPM((b.attrs || {}).limits))
    throw new Error(`unknown block type ${b.type}`)
  })
  const root = schema.nodes.doc.create(null, blocks.length ? blocks : [schema.nodes.p.create({ id: newId('b') })])
  // footnote bodies travel on the node so the editor can edit them in place
  const notes = doc.footnotes || {}
  root.descendants(n => { if (n.type.name === 'fn') n.attrs.body = notes[n.attrs.id] || [] })
  return root
}

function inlineFromPM (node) {
  const out = []
  node.forEach(child => {
    if (child.type.name === 'fn') return out.push({ t: 'fn', id: child.attrs.id })
    if (child.type.name === 'cite') { const c = { t: 'cite', key: child.attrs.key }; if (child.attrs.locator) c.locator = child.attrs.locator; return out.push(c) }
    const flags = child.marks.filter(m => m.type.name === 'em' || m.type.name === 'strong').map(m => m.type.name)
    let item = { t: 'text', v: child.text }
    if (flags.length) item.marks = flags
    const link = child.marks.find(m => m.type.name === 'link')
    if (link && safeHref(link.attrs.href)) item = { t: 'link', href: link.attrs.href, c: [item] }
    const lang = child.marks.find(m => m.type.name === 'lang')
    if (lang) item = { t: 'lang', lang: lang.attrs.lang, c: [item] }
    out.push(item)
  })
  return out
}

export function pmToDoc (root, { locale, title, dek }) {
  const blocks = []
  const footnotes = {}
  const seen = new Set()
  root.forEach(node => {
    const type = node.type.name
    let id = node.attrs.id
    if (!id || seen.has(id)) id = newId('b')
    seen.add(id)
    node.descendants(n => { if (n.type.name === 'fn') footnotes[n.attrs.id] = n.attrs.body || [] })
    if (TEXT_BLOCKS.has(type)) {
      const b = { id, type, content: inlineFromPM(node) }
      if (type === 'blockquote' && node.attrs.cite) b.attrs = { cite: node.attrs.cite }
      blocks.push(b)
    } else if (type === 'ul' || type === 'ol') {
      const items = []
      node.forEach(li => items.push(inlineFromPM(li)))
      blocks.push({ id, type, items })
    } else if (type === 'hr') blocks.push({ id, type, content: [] })
    else if (type === 'figure') blocks.push({ id, type, content: [], attrs: { fig: node.attrs.fig } })
    else if (type === 'evidence') blocks.push({ id, type, content: [], attrs: { class: node.attrs.class, confidence: node.attrs.confidence, limits: inlineFromPM(node) } })
  })
  return { schema: 'fcmo-essay-doc-v1', locale, title, dek, blocks, footnotes }
}

export function plainText (inline) { return (inline || []).map(n => n.v || (n.c ? plainText(n.c) : '')).join('') }
export function wordCount (doc) {
  const text = doc.blocks.map(b => plainText(b.content) + ' ' + (b.items || []).map(plainText).join(' ')).join(' ')
  const cjk = (text.match(/[㐀-鿿]/g) || []).length
  return cjk + text.replace(/[㐀-鿿]/g, ' ').split(/\s+/).filter(Boolean).length
}
