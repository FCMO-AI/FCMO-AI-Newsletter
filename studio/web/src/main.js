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

async function updateReadiness (banner) {
  try {
    const state = await get('/api/publication-readiness')
    if (!banner.isConnected) return
    const own = state.credentials.find(c => c.user === session.me.user)
    const connection = own && !own.ready ? await get('/api/github/connect') : null
    if (!banner.isConnected) return
    const content = []
    for (const credential of state.credentials.filter(c => !c.ready)) {
      if (credential.user === session.me.user) content.push(githubConnectCard(connection))
      else content.push(h('p', null, document.documentElement.lang === 'en' ? credential.plain_en : credential.plain_es))
    }
    if (state.dry_run || !state.live_enabled) content.unshift(h('p', null, t('pub.private.mode')))
    banner.replaceChildren(...content)
    banner.hidden = !banner.childElementCount
  } catch { /* Authentication errors are handled by the shared API. */ }
}
function githubConnectCard (connection) {
  const state = connection?.state || 'idle'
  const status = state === 'ready' ? t('gh.ready') : state === 'waiting' ? t('gh.waiting') :
    state === 'timeout' ? t('gh.timeout') : state === 'cancelled' ? t('gh.cancelled') :
      state === 'error' ? t('gh.error') : state === 'starting' ? t('gh.starting') : ''
  const controls = []
  if (state === 'idle' || state === 'timeout' || state === 'cancelled' || state === 'error') {
    controls.push(h('button', { class: 'btn gh-connect-start', type: 'button', onclick: async e => {
      e.currentTarget.disabled = true
      try { await post('/api/github/connect'); await updateReadiness(document.getElementById('publication-readiness')) }
      catch { e.currentTarget.disabled = false }
    } }, t('gh.connect')))
  }
  if (connection?.code && state === 'waiting') {
    controls.push(h('strong', { class: 'gh-device-code', 'aria-label': t('gh.code') }, connection.code))
    controls.push(h('button', { class: 'btn', type: 'button', onclick: async () => {
      try { await navigator.clipboard.writeText(connection.code); toast(t('gh.copied')) } catch { toast(t('gh.copyError')) }
    } }, t('gh.copy')))
    if (connection.url === 'https://github.com/login/device') controls.push(h('a', { class: 'btn gh-device-link', href: connection.url, target: '_blank', rel: 'noopener noreferrer' }, t('gh.open')))
    controls.push(h('button', { class: 'link-btn', type: 'button', onclick: async () => { try { await del('/api/github/connect'); await updateReadiness(document.getElementById('publication-readiness')) } catch {} } }, t('gh.cancel')))
  }
  return h('div', { class: 'gh-connect', 'data-state': state },
    h('p', null, status || (document.documentElement.lang === 'en' ? connection?.plain_en : connection?.plain_es) || t('gh.missing')),
    h('div', { class: 'gh-connect-controls' }, controls))
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
