import { get, post, ApiError } from './api.js'
import { t, LOCALE_NAME } from './i18n.js'
import { h, ago, dots, modal, clear } from './ui.js'
import { shell, session } from './main.js'

export function login (root, done) {
  const err = h('p', { class: 'form-error', role: 'alert', hidden: true }, t('login.bad'))
  const user = h('input', { id: 'u', name: 'user', autocomplete: 'username', required: true, autofocus: true })
  const pass = h('input', { id: 'p', name: 'password', type: 'password', autocomplete: 'current-password', required: true })
  const form = h('form', { class: 'login-card', onsubmit: async e => {
    e.preventDefault(); err.hidden = true
    try { await post('/api/login', { user: user.value.trim().toLowerCase(), password: pass.value }); done() } catch (x) { err.hidden = false; err.textContent = x instanceof ApiError && x.status === 0 ? t('err.net') : t('login.bad'); pass.select() }
  } },
  h('div', { class: 'login-mark' }, 'fCMO', h('span', null, 'Studio')), h('h1', null, t('login.title')), h('p', { class: 'lede' }, t('login.lede')),
  h('label', { for: 'u' }, t('login.user')), user, h('label', { for: 'p' }, t('login.pass')), pass, err, h('button', { class: 'btn primary big', type: 'submit' }, t('login.go')))
  root.append(h('main', { class: 'login' }, form))
  return null
}

function where (p, me) {
  const mine = p.author === me.user
  if (p.state === 'draft' || p.state === 'changes_requested') return mine ? `#/p/${p.slug}/${p.source_locale}` : `#/p/${p.slug}/${p.source_locale}`
  if (p.state === 'in_review') return mine ? `#/p/${p.slug}/${p.source_locale}/preview` : `#/p/${p.slug}/review`
  if (p.state === 'publishing' || p.state === 'approved') return `#/p/${p.slug}/progress`
  return `#/p/${p.slug}/${p.source_locale}/preview`
}

export function newPieceDialog (kind) {
  const title = h('input', { type: 'text', placeholder: '…', 'aria-label': t('new.name') })
  let lang = 'es-419'
  const radios = ['es-419', 'en', 'zh-Hans'].map(l => h('label', { class: 'chip-radio' }, h('input', { type: 'radio', name: 'lang', value: l, checked: l === lang, onchange: () => { lang = l } }), h('span', null, LOCALE_NAME[l])))
  modal({ title: t('new.title') + ' · ' + t('kind.' + kind), body: [h('label', null, t('new.name'), title), h('p', { class: 'hint' }, t('new.hint')), h('fieldset', { class: 'chips' }, h('legend', null, t('new.lang')), radios)],
    actions: [{ label: t('common.cancel') }, { label: t('new.create'), kind: 'primary', onclick: async close => { const r = await post('/api/pieces', { kind, title: title.value.trim(), source_locale: lang }); close(); location.hash = `#/p/${r.slug}/${lang}` } }] })
}

export async function home (root) {
  const me = session.me
  const pieces = await get('/api/pieces')
  const search = h('input', { type: 'search', class: 'search', placeholder: t('home.search'), 'aria-label': t('home.search') })
  const body = h('div', { class: 'home' })
  const row = p => h('a', { class: 'row', href: where(p, me) },
    h('span', { class: 'row-main' }, h('strong', { class: 'row-title' }, p.title), h('span', { class: 'row-meta' }, t('kind.' + p.kind), ' · ', t('row.by', { who: p.author === me.user ? t('common.you') : (p.author === 'javier' ? 'Javier' : 'Matías') }), ' · ', t('row.words', { n: p.words.toLocaleString('es') }), ' · ', t('row.edited', { when: ago(p.updated_at, t) }))),
    dots(p.locales, t))
  const section = (title, list) => h('section', { class: 'block' }, h('h2', null, title, h('span', { class: 'count' }, list.length || '')), list.length ? h('div', { class: 'rows' }, list.map(row)) : h('p', { class: 'muted' }, t('home.none')))
  function draw () {
    const q = search.value.trim().toLowerCase()
    const list = pieces.filter(p => !q || p.title.toLowerCase().includes(q))
    const attn = []
    for (const p of pieces) {
      const who = p.author === 'javier' ? 'Javier' : 'Matías'
      if (p.state === 'in_review' && p.author !== me.user) attn.push({ p, text: t('attn.review', { who, title: p.title }), go: `#/p/${p.slug}/review`, cta: t('attn.read') })
      if (p.state === 'changes_requested' && p.author === me.user) attn.push({ p, text: t('attn.changes', { who: me.other, title: p.title }), go: `#/p/${p.slug}/${p.source_locale}`, cta: t('attn.open') })
      if (p.state === 'failed' && p.author === me.user) attn.push({ p, text: t('attn.failed', { title: p.title }), go: `#/p/${p.slug}/progress`, cta: t('attn.open') })
    }
    const last = pieces.filter(p => p.author === me.user && (p.state === 'draft' || p.state === 'changes_requested'))[0]
    clear(body)
    body.append(
      h('section', { class: 'block attention' }, h('h2', null, t('home.attention')),
        attn.length ? h('ul', { class: 'attn' }, attn.map(a => h('li', null, h('span', null, a.text), h('a', { class: 'btn small', href: a.go }, a.cta)))) : h('p', { class: 'muted' }, t('home.empty'))),
      last && !q ? h('section', { class: 'block' }, h('h2', null, t('home.continue')), h('a', { class: 'continue', href: where(last, me) }, h('span', { class: 'continue-title' }, last.title), h('span', { class: 'row-meta' }, t('row.edited', { when: ago(last.updated_at, t) }), ' · ', t('row.words', { n: last.words })), dots(last.locales, t))) : null,
      section(t('home.drafts'), list.filter(p => p.state === 'draft' || p.state === 'changes_requested')),
      section(t('home.review'), list.filter(p => ['in_review', 'approved', 'publishing'].includes(p.state))),
      section(t('home.published'), list.filter(p => p.state === 'published' || p.state === 'withdrawn')),
      h('section', { class: 'block' }, h('h2', null, t('home.editions')), h('a', { class: 'row', href: '#/issues' }, h('span', { class: 'row-main' }, h('strong', { class: 'row-title' }, t('iss.title')), h('span', { class: 'row-meta' }, t('iss.soon'))))))
  }
  search.addEventListener('input', draw); draw()
  root.append(shell(h('div', { class: 'home-wrap' },
    h('div', { class: 'home-head' }, h('div', null, h('p', { class: 'eyebrow' }, 'fCMO / Studio'), h('h1', null, t('home.hello', { name: me.name }))),
      h('div', { class: 'home-actions' }, h('button', { class: 'btn primary big', type: 'button', onclick: () => newPieceDialog('essay') }, '+ ', t('home.new')),
        h('button', { class: 'btn', type: 'button', onclick: () => newPieceDialog('letter') }, t('home.letter')), h('button', { class: 'btn', type: 'button', onclick: () => newPieceDialog('note') }, t('home.note')))),
    search, body), { active: 'home' }))
  return null
}
