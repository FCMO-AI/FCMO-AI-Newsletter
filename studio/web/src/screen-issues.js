import { get, put, post } from './api.js'
import { t, LOCALE_NAME, LOCALE_SHORT } from './i18n.js'
import { h, clear, dots, toast } from './ui.js'
import { shell, session } from './main.js'

const SLOTS = ['principal', 'essays', 'day-in-ai', 'notes']
const SLOT_LABEL = () => ({ principal: t('iss.main'), essays: t('iss.essay.slot'), 'day-in-ai': t('iss.day'), notes: t('iss.notes') })
export async function issuesScreen (root, slug) {
  const [allPieces, rawBriefs, editions] = await Promise.all([get('/api/pieces'), get('/api/library/briefs'), get('/api/issues')])
  const pieces = allPieces.filter(p => p.kind !== 'issue' && p.state === 'published')
  const briefs = rawBriefs.filter(b => b.status === 'live').map(b => ({ ...b, headline: b.headline?.['es-419'] || b.headline?.en || b.headline || b.slug, date: b.event_at || b.first_published_at, class: b.evidence_class, beat: b.beat }))
  const initial = slug ? editions.find(e => e.issue.id === slug) : null
  let rev = initial?.rev; let currentSlug = initial?.issue.id; let saving = false; let dirty = false
  const persisted = initial?.issue
  const issue = persisted ? { date: persisted.date, title: persisted.title, note: persisted.note, slots: Object.fromEntries(SLOTS.map(slot => [slot, persisted.slots.filter(x => x.slot === slot).map(x => x.ref)])) } : { date: new Date().toISOString().slice(0, 10), title: { en: '', 'es-419': '', 'zh-Hans': '' }, slots: Object.fromEntries(SLOTS.map(slot => [slot, []])), note: { en: '', 'es-419': '', 'zh-Hans': '' } }
  let tab = 'essays'; let q = ''; let cls = ''; let noteLoc = 'es-419'; let saveT
  async function save () {
    if (saving || !dirty || session.me.user !== 'matias') return
    saving = true; dirty = false
    try { const id = currentSlug || `${issue.date}-edicion-${crypto.randomUUID().slice(0, 8)}`; const doc = { schema: 'fcmo-issue-v1', id, date: issue.date, title: issue.title, note: issue.note, slots: SLOTS.flatMap(slot => issue.slots[slot].map(ref => ({ slot, ref }))) }; const r = currentSlug ? await put(`/api/issues/${currentSlug}`, { base_rev: rev, issue: doc }) : await post('/api/issues', doc); currentSlug = id; rev = r.rev; saveState.textContent = t('ed.saved') }
    catch (e) { dirty = true; saveState.textContent = e.data?.error_plain || t('err.generic') }
    finally { saving = false; if (dirty) saveT = setTimeout(save, 5000) }
  }
  const saveState = h('span', { class: 'save-state', role: 'status' }, t('ed.saved'))
  const persist = () => { dirty = true; saveState.textContent = t('ed.dirty'); clearTimeout(saveT); saveT = setTimeout(save, 800) }
  const lib = h('div', { class: 'lib' }); const canvas = h('div', { class: 'canvas' })
  const find = ref => !ref.startsWith('FCMO-P-') ? { kind: 'brief', b: briefs.find(b => b.id === ref) } : { kind: 'piece', p: pieces.find(p => p.meta.id === ref) }
  function add (slot, ref) { if (SLOTS.some(s => issue.slots[s].includes(ref))) return toast('Ya está en la edición'); issue.slots[slot].push(ref); persist(); drawCanvas() }
  function card (it) {
    if (it.kind === 'brief') {
      const b = it.b; if (!b) return h('div', { class: 'card gone' }, '?')
      return h('div', { class: 'card brief', draggable: 'true', 'data-ref': b.id }, h('p', { class: 'card-meta' }, b.date, ' · ', b.beat, ' · ', h('span', { class: 'cls c' + b.class }, t('iss.class'), ' ', b.class)), h('p', { class: 'card-title' }, b.headline), h('p', { class: 'muted small' }, t('iss.readonly')))
    }
    const p = it.p; if (!p) return h('div', { class: 'card gone' }, '?')
    const bad = !['en', 'es-419', 'zh-Hans'].every(l => ['ready', 'later'].includes((p.locales[l] || {}).state))
    return h('div', { class: 'card piece', draggable: 'true', 'data-ref': p.meta.id }, h('p', { class: 'card-meta' }, t('kind.' + p.kind), ' · ', p.author === 'javier' ? 'Javier' : 'Matías'), h('p', { class: 'card-title' }, p.title), dots(p.locales, t), bad ? h('p', { class: 'flag' }, '! ', t('iss.badlang')) : null)
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
        : pieces.filter(tabs.find(x => x[0] === tab)[2]).filter(p => !q || p.title.toLowerCase().includes(q.toLowerCase())).map(p => ({ kind: 'piece', p, ref: p.meta.id }))
      if (!items.length) body.append(h('p', { class: 'muted' }, t('iss.empty')))
      for (const it of items) {
        const slot = it.kind === 'brief' ? 'day-in-ai' : it.p.kind === 'essay' ? 'essays' : 'notes'
        const c = card(it); c.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', it.ref))
        body.append(h('div', { class: 'lib-item' }, c, h('button', { class: 'btn small', type: 'button', onclick: () => add(slot, it.ref), 'aria-label': t('iss.add') + ': ' + (it.p ? it.p.title : it.b.headline) }, '+ ', t('iss.add'))))
      }
    }
    drawList()
  }
  function drawCanvas () {
    clear(canvas)
    const title = h('input', { type: 'text', class: 'issue-title', placeholder: t('iss.canvas'), value: issue.title[noteLoc], 'aria-label': t('iss.canvas') }); title.addEventListener('input', () => { issue.title[noteLoc] = title.value; persist() })
    const date = h('input', { type: 'date', value: issue.date, disabled: !!currentSlug, 'aria-label': t('iss.date') }); date.addEventListener('input', () => { issue.date = date.value; persist() }); canvas.append(date, title)
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
    canvas.append(h('section', { class: 'slot editor-note' }, h('h3', null, t('iss.note')), h('div', { class: 'seg' }, ['en', 'es-419', 'zh-Hans'].map(l => h('button', { type: 'button', class: l === noteLoc ? 'on' : '', 'aria-pressed': String(l === noteLoc), onclick: () => { noteLoc = l; drawCanvas() } }, LOCALE_SHORT[l]))), ta))
  }
  drawLib(); drawCanvas()
  root.append(shell(h('div', { class: 'flow iss' }, h('h1', null, t('iss.title')), h('div', { class: 'btn-row' }, saveState, h('button', { class: 'btn', type: 'button', disabled: session.me.user !== 'matias', onclick: async () => { await save(); if (currentSlug && !dirty) location.hash = `#/p/${currentSlug}/publish` } }, t('ed.publish'))), h('div', { class: 'rows' }, editions.map(e => h('a', { class: 'row', href: '#/issues/' + e.issue.id }, e.issue.title.en || e.issue.id))), h('div', { class: 'iss-grid' }, h('section', { class: 'iss-lib' }, h('h2', null, t('iss.lib')), lib), h('section', { class: 'iss-canvas' }, h('h2', null, t('iss.canvas')), canvas))), { active: 'issues', wide: true }))
  return () => { clearTimeout(saveT); if (dirty) save() }
}
