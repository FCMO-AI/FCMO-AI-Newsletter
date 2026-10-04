import { get, put } from './api.js'
import { t, LOCALE_NAME, LOCALE_SHORT } from './i18n.js'
import { h, clear, dots, toast } from './ui.js'
import { shell } from './main.js'

const SLOTS = ['main', 'essays', 'day', 'notes']
const SLOT_LABEL = () => ({ main: t('iss.main'), essays: t('iss.essay.slot'), day: t('iss.day'), notes: t('iss.notes') })
const KEY = 'studio:issue:draft'
const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || 'null') } catch { return null } }
const store = v => { try { localStorage.setItem(KEY, JSON.stringify(v)) } catch { /* storage blocked */ } }

export async function issuesScreen (root) {
  const [pieces, briefs] = await Promise.all([get('/api/pieces'), get('/api/library/briefs')])
  const issue = load() || { title: '', slots: { main: [], essays: [], day: [], notes: [] }, note: { en: '', 'es-419': '', 'zh-Hans': '' } }
  let tab = 'essays'; let q = ''; let cls = ''; let noteLoc = 'es-419'; let saveT
  const persist = () => { store(issue); clearTimeout(saveT); saveT = setTimeout(() => put('/api/issues/draft', issue).catch(() => {}), 800) }
  const lib = h('div', { class: 'lib' }); const canvas = h('div', { class: 'canvas' })
  const find = ref => ref.startsWith('FCMO-') ? { kind: 'brief', b: briefs.find(b => b.id === ref) } : { kind: 'piece', p: pieces.find(p => p.slug === ref) }
  function add (slot, ref) { if (SLOTS.some(s => issue.slots[s].includes(ref))) return toast('Ya está en la edición'); issue.slots[slot].push(ref); persist(); drawCanvas() }
  function card (it) {
    if (it.kind === 'brief') {
      const b = it.b; if (!b) return h('div', { class: 'card gone' }, '?')
      return h('div', { class: 'card brief', draggable: 'true', 'data-ref': b.id }, h('p', { class: 'card-meta' }, b.date, ' · ', b.beat, ' · ', h('span', { class: 'cls c' + b.class }, t('iss.class'), ' ', b.class)), h('p', { class: 'card-title' }, b.headline), h('p', { class: 'muted small' }, t('iss.readonly')))
    }
    const p = it.p; if (!p) return h('div', { class: 'card gone' }, '?')
    const bad = !['en', 'es-419', 'zh-Hans'].every(l => ['ready', 'later'].includes((p.locales[l] || {}).state))
    return h('div', { class: 'card piece', draggable: 'true', 'data-ref': p.slug }, h('p', { class: 'card-meta' }, t('kind.' + p.kind), ' · ', p.author === 'javier' ? 'Javier' : 'Matías'), h('p', { class: 'card-title' }, p.title), dots(p.locales, t), bad ? h('p', { class: 'flag' }, '! ', t('iss.badlang')) : null)
  }
  function drawLib () {
    clear(lib)
    const tabs = [['essays', t('iss.essays'), p => p.kind === 'essay'], ['letters', t('iss.letters'), p => p.kind !== 'essay'], ['briefs', t('iss.briefs')]]
    lib.append(h('div', { class: 'seg', role: 'tablist' }, tabs.map(([id, l]) => h('button', { type: 'button', role: 'tab', class: id === tab ? 'on' : '', 'aria-selected': String(id === tab), onclick: () => { tab = id; drawLib() } }, l))))
    const f = h('input', { type: 'search', placeholder: t('iss.filter'), value: q, 'aria-label': t('iss.filter') }); f.addEventListener('input', () => { q = f.value; drawList() })
    const body = h('div', { class: 'lib-list' })
    lib.append(h('div', { class: 'lib-filter' }, f, tab === 'briefs' ? h('select', { 'aria-label': t('iss.class'), onchange: e => { cls = e.target.value; drawList() } }, ['', 'A', 'B', 'C', 'D'].map(c => h('option', { value: c, selected: c === cls }, c ? t('iss.class') + ' ' + c : t('iss.class')))) : null), body)
    function drawList () {
      clear(body)
      const items = tab === 'briefs' ? briefs.filter(b => (!q || (b.headline + b.date + b.beat).toLowerCase().includes(q.toLowerCase())) && (!cls || b.class === cls)).map(b => ({ kind: 'brief', b, ref: b.id }))
        : pieces.filter(tabs.find(x => x[0] === tab)[2]).filter(p => !q || p.title.toLowerCase().includes(q.toLowerCase())).map(p => ({ kind: 'piece', p, ref: p.slug }))
      if (!items.length) body.append(h('p', { class: 'muted' }, t('iss.empty')))
      for (const it of items) {
        const slot = it.kind === 'brief' ? 'day' : it.p.kind === 'essay' ? 'essays' : 'notes'
        const c = card(it); c.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', it.ref))
        body.append(h('div', { class: 'lib-item' }, c, h('button', { class: 'btn small', type: 'button', onclick: () => add(slot, it.ref), 'aria-label': t('iss.add') + ': ' + (it.p ? it.p.title : it.b.headline) }, '+ ', t('iss.add'))))
      }
    }
    drawList()
  }
  function drawCanvas () {
    clear(canvas)
    const title = h('input', { type: 'text', class: 'issue-title', placeholder: t('iss.canvas'), value: issue.title, 'aria-label': t('iss.canvas') }); title.addEventListener('input', () => { issue.title = title.value; persist() })
    canvas.append(title)
    const labels = SLOT_LABEL()
    for (const s of SLOTS) {
      const zone = h('section', { class: 'slot', 'data-slot': s }, h('h3', null, labels[s]), issue.slots[s].length ? null : h('p', { class: 'drop-hint' }, t('iss.drop')))
      zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('over') }); zone.addEventListener('dragleave', () => zone.classList.remove('over'))
      zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('over'); const ref = e.dataTransfer.getData('text/plain'); if (ref) { for (const x of SLOTS) issue.slots[x] = issue.slots[x].filter(r => r !== ref); issue.slots[s].push(ref); persist(); drawCanvas() } })
      issue.slots[s].forEach((ref, i) => {
        const list = issue.slots[s]
        zone.append(h('div', { class: 'slot-item' }, card(find(ref)), h('div', { class: 'slot-act' },
          h('button', { class: 'icon-btn', type: 'button', disabled: i === 0, 'aria-label': t('iss.up'), onclick: () => { [list[i - 1], list[i]] = [list[i], list[i - 1]]; persist(); drawCanvas() } }, '↑'),
          h('button', { class: 'icon-btn', type: 'button', disabled: i === list.length - 1, 'aria-label': t('iss.down'), onclick: () => { [list[i + 1], list[i]] = [list[i], list[i + 1]]; persist(); drawCanvas() } }, '↓'),
          h('button', { class: 'icon-btn', type: 'button', 'aria-label': t('iss.remove'), onclick: () => { list.splice(i, 1); persist(); drawCanvas() } }, '×'))))
      })
      canvas.append(zone)
    }
    const ta = h('textarea', { rows: 4, lang: noteLoc, 'aria-label': t('iss.note') }); ta.value = issue.note[noteLoc] || ''; ta.addEventListener('input', () => { issue.note[noteLoc] = ta.value; persist() })
    canvas.append(h('section', { class: 'slot note' }, h('h3', null, t('iss.note')), h('div', { class: 'seg' }, ['en', 'es-419', 'zh-Hans'].map(l => h('button', { type: 'button', class: l === noteLoc ? 'on' : '', 'aria-pressed': String(l === noteLoc), onclick: () => { noteLoc = l; drawCanvas() } }, LOCALE_SHORT[l]))), ta))
  }
  drawLib(); drawCanvas()
  root.append(shell(h('div', { class: 'flow iss' }, h('h1', null, t('iss.title')), h('div', { class: 'iss-grid' }, h('section', { class: 'iss-lib' }, h('h2', null, t('iss.lib')), lib), h('section', { class: 'iss-canvas' }, h('h2', null, t('iss.canvas')), canvas))), { active: 'issues', wide: true }))
  return null
}
