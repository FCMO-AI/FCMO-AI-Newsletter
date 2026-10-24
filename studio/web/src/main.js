import { get, post, del, setCsrf } from './api.js'
import { setLang, t } from './i18n.js'
import { h, clear, toast, closeModals } from './ui.js'
import { login, home } from './screens-home.js'
import { editorScreen } from './screen-editor.js'
import { translateScreen, previewScreen, publishScreen, reviewScreen, progressScreen, versionsScreen } from './screens-flow.js'
import { issuesScreen } from './screen-issues.js'

const app = document.getElementById('app')
export const session = { me: null }
let dispose = null
let rendering = 0

function applyTheme () {
  let v = 'auto'
  try { v = localStorage.getItem('studio:theme') || 'auto' } catch { /* storage blocked */ }
  document.documentElement.dataset.theme = v
}
export function cycleTheme () {
  const order = ['auto', 'light', 'dark']
  const cur = document.documentElement.dataset.theme || 'auto'
  const next = order[(order.indexOf(cur) + 1) % 3]
  try { localStorage.setItem('studio:theme', next) } catch { /* storage blocked */ }
  document.documentElement.dataset.theme = next
  return next
}
applyTheme()

// GitHub connection: a three-step guide for a non-technical person. The banner re-renders only when
// what it shows changes, so a click, a copied code or a focused button is never wiped by the 3 s poll.
const ghUi = { checking: false, notYet: false, opened: false, wasMissing: false, doneAt: 0, code: '' }
const refreshReadiness = () => { const b = document.getElementById('publication-readiness'); return b ? updateReadiness(b) : Promise.resolve() }
async function updateReadiness (banner) {
  try {
    const state = await get('/api/publication-readiness')
    if (!banner.isConnected) return
    const own = state.credentials.find(c => c.user === session.me.user)
    const missing = !!(own && !own.ready)
    const connection = missing ? await get('/api/github/connect') : null
    if (!banner.isConnected) return
    if (missing) ghUi.wasMissing = true
    else if (ghUi.wasMissing) { ghUi.wasMissing = false; ghUi.doneAt = Date.now(); ghUi.checking = false; ghUi.notYet = false; ghUi.opened = false }
    if (connection?.code !== ghUi.code) { ghUi.code = connection?.code || ''; ghUi.notYet = false; ghUi.opened = false }
    const justDone = !missing && Date.now() - ghUi.doneAt < 8000
    const sig = JSON.stringify([document.documentElement.lang, state.credentials.map(c => [c.user, c.ready, c.plain_es]), connection, state.dry_run, state.live_enabled, ghUi.checking, ghUi.notYet, ghUi.opened, justDone])
    if (banner.dataset.sig === sig) return
    banner.dataset.sig = sig
    const content = []
    if (justDone) content.push(h('p', { class: 'gh-done' }, h('span', { class: 'gh-tick', 'aria-hidden': 'true' }, '✓'), ' ', t('gh.done')))
    for (const credential of state.credentials.filter(c => !c.ready)) {
      if (credential.user === session.me.user) content.push(githubConnectCard(connection))
      else content.push(h('p', null, document.documentElement.lang === 'en' ? credential.plain_en : credential.plain_es))
    }
    if (state.dry_run || !state.live_enabled) content.unshift(h('p', null, t('pub.private.mode')))
    banner.replaceChildren(...content)
    banner.classList.toggle('has-guide', !!banner.querySelector('.gh-connect, .gh-done'))
    banner.hidden = !banner.childElementCount
  } catch { /* Authentication errors are handled by the shared API. */ }
}
async function confirmTyped () {
  ghUi.checking = true; ghUi.notYet = false
  await refreshReadiness()
  await new Promise(resolve => setTimeout(resolve, 1500)) // the login finishes a moment after GitHub accepts the code
  await refreshReadiness()
  ghUi.checking = false
  if (document.querySelector('#publication-readiness .gh-connect[data-state="waiting"]')) ghUi.notYet = true
  await refreshReadiness()
}
async function requestCode (button) {
  if (button) button.disabled = true
  ghUi.notYet = false; ghUi.opened = false
  try { await post('/api/github/connect') } catch { /* the card shows the error state on the next read */ }
  await refreshReadiness()
}
function githubConnectCard (connection) {
  // The card only renders while his own credential is not ready, so a 'ready' connection with no
  // usable credential is a dead end: offer to start again unless we are mid-confirmation.
  let state = connection?.state || 'idle'
  if (state === 'ready' && !ghUi.checking) state = 'idle'
  const who = session.me.other
  const head = (title, lead) => [h('h2', { class: 'gh-title' }, title), lead ? h('p', { class: 'gh-lead' }, lead) : null]
  const again = label => h('button', { class: 'btn primary gh-connect-start', type: 'button', onclick: e => requestCode(e.currentTarget) }, label)
  let body
  if (state === 'waiting' && connection.code) {
    const open = connection.url === 'https://github.com/login/device'
    const step = (n, title, hint, control, current) => h('li', { class: 'gh-step' + (current ? ' current' : ''), 'aria-current': current ? 'step' : null },
      h('span', { class: 'gh-n', 'aria-hidden': 'true' }, String(n)),
      h('div', { class: 'gh-step-body' }, h('strong', null, title), h('span', { class: 'gh-hint' }, hint), control))
    body = [...head(t('gh.guide.title'), t('gh.waiting')),
      h('ol', { class: 'gh-steps' },
        step(1, t('gh.step1'), t('gh.step1.hint'), open ? h('a', { class: 'btn gh-device-link' + (ghUi.opened ? '' : ' primary'), href: connection.url, target: '_blank', rel: 'noopener noreferrer', onclick: () => { ghUi.opened = true } }, t('gh.open'), ' ↗') : null, !ghUi.opened),
        step(2, t('gh.step2'), t('gh.step2.hint'), h('div', { class: 'gh-code-row' },
          h('strong', { class: 'gh-device-code', 'aria-label': t('gh.code') }, connection.code),
          h('button', { class: 'btn', type: 'button', onclick: async () => { try { await navigator.clipboard.writeText(connection.code); toast(t('gh.copied')) } catch { toast(t('gh.copyError')) } } }, t('gh.copy'))), ghUi.opened),
        step(3, t('gh.step3'), t('gh.step3.hint'), h('div', { class: 'gh-confirm' },
          h('button', { class: 'btn' + (ghUi.opened ? ' primary' : ''), type: 'button', disabled: ghUi.checking, onclick: () => confirmTyped() }, ghUi.checking ? t('gh.checking') : t('gh.step3')),
          ghUi.notYet ? h('p', { class: 'gh-notyet', role: 'status' }, t('gh.notyet')) : null), false)),
      h('button', { class: 'link-btn', type: 'button', onclick: async () => { try { await del('/api/github/connect') } catch {} await refreshReadiness() } }, t('gh.cancel'))]
  } else if (state === 'starting' || (state === 'waiting' && !connection.code)) {
    body = [...head(t('gh.guide.title'), t('gh.starting'))]
  } else if (state === 'ready') {
    body = [...head(t('gh.guide.title'), t('gh.checking'))]
  } else if (state === 'timeout') {
    body = [...head(t('gh.expired.title'), t('gh.expired.body')), again(t('gh.newcode'))]
  } else if (state === 'cancelled') {
    body = [...head(t('gh.cancelled.title'), t('gh.cancelled.body')), again(t('gh.newcode'))]
  } else if (state === 'error') {
    body = [...head(t('gh.error.title'), t('gh.error.body', { who })), again(t('gh.newcode'))]
  } else {
    body = [...head(t('gh.guide.title'), t('gh.guide.lead')), again(t('gh.guide.start'))]
  }
  return h('div', { class: 'gh-connect', 'data-state': state }, body)
}
setInterval(() => {
  const banner = document.getElementById('publication-readiness')
  if (session.me && banner) updateReadiness(banner)
}, 3000)

export function shell (content, { active = '', wide = false } = {}) {
  const me = session.me
  const readiness = me ? h('aside', { id: 'publication-readiness', class: 'publication-readiness', role: 'status', hidden: true }) : null
  if (readiness) setTimeout(() => updateReadiness(readiness), 0)
  const themeBtn = h('button', { class: 'icon-btn', type: 'button', title: t('nav.theme'), 'aria-label': t('nav.theme'), onclick: () => { cycleTheme() } }, h('span', { class: 'half', 'aria-hidden': 'true' }))
  return h('div', { class: 'shell' },
    h('a', { class: 'skip', href: '#main' }, t('nav.skip')),
    h('header', { class: 'topbar' },
      h('a', { class: 'brand', href: '#/' }, h('span', { class: 'brand-mark' }, 'fCMO'), h('span', { class: 'brand-name' }, 'Studio')),
      h('nav', { 'aria-label': 'Principal' },
        h('a', { href: '#/', 'aria-current': active === 'home' ? 'page' : null }, t('nav.home')),
        h('a', { href: '#/issues', 'aria-current': active === 'issues' ? 'page' : null }, t('nav.issues'))),
      h('div', { class: 'topbar-right' }, themeBtn,
        me ? h('span', { class: 'who' }, me.name) : null,
        me ? h('button', { class: 'link-btn', type: 'button', onclick: async () => { try { await post('/api/logout') } catch { /* already out */ } session.me = null; location.hash = '#/login'; route() } }, t('nav.logout')) : null)),
    h('main', { id: 'main', class: wide ? 'wide' : '' }, readiness, content))
}

async function ensureMe () {
  if (session.me) return true
  try { session.me = await get('/api/me'); session.expired = false; setCsrf(session.me.csrf); setLang(session.me.ui_lang || 'es'); return true } catch { return false }
}

const routes = [
  [/^#\/$|^$|^#$/, (r) => home(r)],
  [/^#\/issues(?:\/([^/]+))?$/, (r, m) => issuesScreen(r, m[1])],
  [/^#\/p\/([^/]+)\/([^/]+)\/translate(?:\/([^/]+))?$/, (r, m) => translateScreen(r, m[1], m[2], m[3])],
  [/^#\/p\/([^/]+)\/([^/]+)\/preview$/, (r, m) => previewScreen(r, m[1], m[2])],
  [/^#\/p\/([^/]+)\/publish$/, (r, m) => publishScreen(r, m[1])],
  [/^#\/p\/([^/]+)\/review$/, (r, m) => reviewScreen(r, m[1])],
  [/^#\/p\/([^/]+)\/progress$/, (r, m) => progressScreen(r, m[1])],
  [/^#\/p\/([^/]+)\/versions$/, (r, m) => versionsScreen(r, m[1])],
  [/^#\/p\/([^/]+)\/([^/]+)$/, (r, m) => editorScreen(r, m[1], m[2])],
  [/^#\/p\/([^/]+)$/, (r, m) => editorScreen(r, m[1], null)]
]

export async function route () {
  const mine = ++rendering
  if (dispose) { try { dispose() } catch { /* leaving */ } dispose = null }
  closeModals()
  const hash = location.hash || '#/'
  if (!(await ensureMe())) { clear(app); dispose = login(app, () => { location.hash = '#/'; route() }, session.expired ? t('login.expired') : ''); return }
  if (hash === '#/login') { location.hash = '#/'; return }
  const root = h('div', { class: 'screen' })
  clear(app); app.append(root)
  for (const [re, fn] of routes) {
    const m = re.exec(hash)
    if (m) {
      try { const d = await fn(root, m); if (mine === rendering) dispose = d || null; else if (d) d() } catch (e) { console.error(e); root.append(shell(h('div', { class: 'notice' }, t('err.generic')))) }
      return
    }
  }
  root.append(shell(h('div', { class: 'notice' }, t('err.notfound'))))
}
addEventListener('hashchange', route)
addEventListener('studio:unauth', () => { if (session.me) session.expired = true; session.me = null; route() })
route()
