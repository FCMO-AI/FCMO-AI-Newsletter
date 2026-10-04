// Dev mock of the STUDIO-SPEC 7.1 API. Lane A2 serves the real one. State lives in memory.
// usage: node dev/server.mjs [port]   (login: javier or matias, password "estudio")
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { execFile } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { piece as fxPiece, sources as fxSources, figures as fxFigures, docs as fxDocs, LOCALES } from './fixture.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const web = path.resolve(here, '..')
const repo = path.resolve(web, '../..')
const port = Number(process.argv[2] || process.env.PORT || 8447)
const clone = o => JSON.parse(JSON.stringify(o))
const USERS = { javier: { key: 'javier', name: 'Javier', pw: 'estudio' }, matias: { key: 'matias', name: 'Matías', pw: 'estudio' } }
const sessions = new Map()
const now = () => new Date().toISOString()
const minutesAgo = m => new Date(Date.now() - m * 60000).toISOString()

function blankDoc (loc, title = '') { return { schema: 'fcmo-essay-doc-v1', locale: loc, title, dek: '', blocks: [{ id: 'b-' + crypto.randomBytes(4).toString('hex'), type: 'p', content: [] }], footnotes: {} } }
function mkPiece (o) {
  const p = { comments: [], versions: [], lock: {}, review: null, publication: null, cursor: {}, sources: [], figures: {}, kind: 'essay', ...o }
  p.versions.push({ rev: 1, at: minutesAgo(600), user: p.author, name: 'Primer borrador completo', snapshot: clone(p.docs) })
  return p
}
const store = {}
store[fxPiece.slug] = mkPiece({
  slug: fxPiece.slug, author: 'javier', state: 'draft', source_locale: 'es-419', updated_at: minutesAgo(14), piece: { ...fxPiece, status: 'draft' },
  locales: { 'es-419': { state: 'ready', reviewed: true, by: 'Javier', at: minutesAgo(30), origin: 'human_authored' }, en: { state: 'drafting', reviewed: false, origin: 'agent_draft' }, 'zh-Hans': { state: 'drafting', reviewed: false, origin: 'agent_draft' } },
  docs: Object.fromEntries(LOCALES.map(l => [l, { rev: 3, doc: clone(fxDocs[l]) }])), sources: clone(fxSources), figures: clone(fxFigures)
})
store['una-carta-corta'] = mkPiece({
  slug: 'una-carta-corta', author: 'matias', state: 'in_review', kind: 'letter', source_locale: 'en', updated_at: minutesAgo(95), piece: { ...fxPiece, id: 'FCMO-P-00000000cafe', slug: 'una-carta-corta', kind: 'letter', authors: [{ key: 'matias', name: 'Matías' }], source_locale: 'en' },
  locales: { en: { state: 'ready', reviewed: true, by: 'Matías', at: minutesAgo(100), origin: 'human_authored' }, 'es-419': { state: 'later' }, 'zh-Hans': { state: 'later' } },
  docs: { en: { rev: 2, doc: { ...blankDoc('en', 'A short letter on weeks'), dek: 'Notes from a quiet week.', blocks: [{ id: 'b-aaaaaaa1', type: 'p', content: [{ t: 'text', v: 'Some weeks are for finishing things.' }] }] } } },
  review: { state: 'requested', at: minutesAgo(90), note: '' }
})
store['historia-del-registro'] = mkPiece({
  slug: 'historia-del-registro', author: 'javier', state: 'published', source_locale: 'es-419', updated_at: minutesAgo(60 * 24 * 6), piece: { ...fxPiece, id: 'FCMO-P-0000000000aa', slug: 'historia-del-registro' },
  locales: { 'es-419': { state: 'ready', reviewed: true, by: 'Javier', at: minutesAgo(8000), origin: 'human_authored' }, en: { state: 'ready', reviewed: true, by: 'Javier', at: minutesAgo(8000), origin: 'human_translated' }, 'zh-Hans': { state: 'ready', reviewed: false, origin: 'agent_draft' } },
  docs: Object.fromEntries(LOCALES.map(l => [l, { rev: 5, doc: { ...clone(fxDocs[l]), title: { en: 'A short history of the ledger', 'es-419': 'Breve historia del registro', 'zh-Hans': '账本小史' }[l] } }]))
})

const wordCount = d => { const t = d.blocks.map(b => JSON.stringify([b.content, b.items])).join(' ').replace(/"v":"([^"]*)"/g, ' $1 ').replace(/[^\p{L}\p{N}\s]/gu, ' '); return (t.match(/[㐀-鿿]/g) || []).length + t.replace(/[㐀-鿿]/g, ' ').split(/\s+/).filter(w => w.length > 1 && !/^(t|text|content|id|type|items|attrs|marks|c)$/.test(w)).length }
function meta (p) {
  const src = p.docs[p.source_locale]
  const locales = {}
  for (const l of LOCALES) locales[l] = { ...(p.locales[l] || { state: 'empty' }), words: p.docs[l] ? wordCount(p.docs[l].doc) : 0, rev: p.docs[l] ? p.docs[l].rev : 0 }
  return { slug: p.slug, kind: p.kind, author: p.author, state: p.state, title: (src && src.doc.title) || 'Sin título', source_locale: p.source_locale, locales, cursor: p.cursor, lock: p.lock, comments_count: p.comments.filter(c => !c.resolved_at).length, updated_at: p.updated_at, words: src ? wordCount(src.doc) : 0, review: p.review }
}
function checks (p) {
  const out = []; const add = (id, ok, es, en, goto) => out.push({ id, ok, plain_es: es, plain_en: en, goto })
  const sl = p.source_locale; const d = p.docs[sl] && p.docs[sl].doc
  add('title', !!(d && d.title.trim()), 'El título está puesto.', 'The title is set.', { loc: sl })
  add('dek', !!(d && d.dek.trim()), 'Hay un subtítulo.', 'There is a dek.', { loc: sl })
  const active = LOCALES.filter(l => p.docs[l] && (p.locales[l] || {}).state !== 'later')
  for (const l of active) {
    const doc = p.docs[l].doc
    for (const b of doc.blocks.filter(b => b.type === 'figure')) {
      const f = p.figures[b.attrs.fig] || {}
      add(`alt-${l}-${b.id}`, !!(f.alt && f.alt[l]), `La figura tiene texto alternativo en ${l}.`, `The figure has alt text in ${l}.`, { loc: l, block_id: b.id })
      add(`credit-${b.id}`, !!(f.credit && f.licence), 'La figura tiene crédito y licencia.', 'The figure has credit and licence.', { loc: l, block_id: b.id })
    }
    const ids = new Set(); const walk = n => { if (Array.isArray(n)) n.forEach(walk); else if (n && typeof n === 'object') { if (n.t === 'fn') ids.add(n.id); Object.values(n).forEach(walk) } }
    walk(doc.blocks)
    for (const id of ids) add(`fn-${l}-${id}`, (doc.footnotes[id] || []).length > 0, 'Cada nota al pie tiene contenido.', 'Every footnote has content.', { loc: l })
    const st = p.locales[l] || {}
    add(`lang-${l}`, st.state === 'ready', `El idioma ${l} está listo o se publicará después.`, `${l} is ready or set to publish later.`, { loc: l })
  }
  const raw = JSON.stringify(p.docs)
  add('privacy', !/\/srv\/|\/home\/|@fcmo\.|password/i.test(raw), 'No hay marcas privadas en el texto.', 'No private markers in the text.', { loc: sl })
  add('gates', true, 'La construcción de prueba pasó todas las comprobaciones.', 'The candidate build passed every check.', null)
  return out
}
function words (a) { return a.split(/(\s+)/) }
function diffText (a, b) {
  const x = words(a); const y = words(b); const m = x.length; const n = y.length
  const L = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--) L[i][j] = x[i] === y[j] ? L[i + 1][j + 1] + 1 : Math.max(L[i + 1][j], L[i][j + 1])
  const ops = []; let i = 0; let j = 0
  const push = (op, text) => { const last = ops[ops.length - 1]; if (last && last.op === op) last.text += text; else ops.push({ op, text }) }
  while (i < m && j < n) { if (x[i] === y[j]) { push('eq', x[i]); i++; j++ } else if (L[i + 1][j] >= L[i][j + 1]) push('del', x[i++]); else push('add', y[j++]) }
  while (i < m) push('del', x[i++]); while (j < n) push('add', y[j++])
  return ops
}
const bt = b => JSON.stringify([b.content, b.items]).replace(/"v":"([^"]*)"/g, '$1 ').replace(/[\[\]{}",]|t:text|"t"|:/g, ' ').replace(/\s+/g, ' ').trim()
const blockText = b => { const parts = []; const w = n => { if (Array.isArray(n)) n.forEach(w); else if (n && typeof n === 'object') { if (typeof n.v === 'string') parts.push(n.v); if (n.t === 'fn') parts.push('[nota]'); if (n.t === 'cite') parts.push('[fuente]'); w(n.c); w(n.items); w(n.content) } }; w(b.content); w(b.items); return parts.join('') }
function diffDocs (a, b) {
  const am = new Map((a ? a.blocks : []).map(x => [x.id, x])); const out = []
  for (const blk of b.blocks) { const o = am.get(blk.id); if (!o) out.push({ id: blk.id, status: 'added', ops: [{ op: 'add', text: blockText(blk) }] }); else { const ops = diffText(blockText(o), blockText(blk)); out.push({ id: blk.id, status: ops.some(x => x.op !== 'eq') ? 'changed' : 'same', ops }); am.delete(blk.id) } }
  for (const [id, o] of am) out.push({ id, status: 'removed', ops: [{ op: 'del', text: blockText(o) }] })
  return { blocks: out, title: diffText(a ? a.title : '', b.title) }
}
const STEPS = [['candidate', 'Preparando una copia de prueba del sitio.', 'Building a test copy of the site.'], ['push', 'Enviando el texto aprobado.', 'Sending the approved text.'], ['pr', 'Abriendo la solicitud de publicación.', 'Opening the publication request.'], ['checks', 'Pasando las comprobaciones públicas.', 'Running the public checks.'], ['merge', 'Uniendo con el sitio.', 'Merging into the site.'], ['pages', 'Publicando el sitio.', 'Deploying the site.'], ['live', 'Comprobando que la página ya responde.', 'Checking that the page answers.']]
function publication (p) {
  if (!p.publication) return null
  const el = (Date.now() - p.publication.started) / 1000; const fail = /falla/i.test(p.docs[p.source_locale].doc.title); const idx = Math.floor(el / 2.2)
  const steps = STEPS.map(([id, es, en], i) => ({ id, plain_es: es, plain_en: en, state: fail && i === 3 && idx >= 3 ? 'failed' : i < idx && !(fail && i >= 3) ? 'done' : i === idx && !(fail && i >= 3) ? 'active' : 'waiting' }))
  const done = !fail && idx >= STEPS.length
  if (done && p.state !== 'published') { p.state = 'published'; p.piece.status = 'published' }
  return { steps, state: done ? 'published' : fail && idx >= 3 ? 'failed' : 'publishing', error_plain: fail && idx >= 3 ? 'La comprobación pública falló: la figura 2 no tiene texto alternativo en chino. Nada se publicó; el sitio sigue igual.' : null, live_urls: done ? LOCALES.map(l => ({ locale: l, url: `https://www.example.invalid/${{ en: '', 'es-419': 'es/', 'zh-Hans': 'zh/' }[l]}cartas/${p.slug}/` })) : [] }
}

const send = (res, code, body, type = 'application/json') => { res.writeHead(code, { 'content-type': type + '; charset=utf-8', 'cache-control': 'no-store' }); res.end(type === 'application/json' ? JSON.stringify(body) : body) }
const readBody = req => new Promise(r => { const c = []; req.on('data', x => c.push(x)); req.on('end', () => r(Buffer.concat(c))) })
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.png': 'image/png', '.webp': 'image/webp', '.json': 'application/json' }
function serveFile (res, file) { if (!file.startsWith(web) && !file.startsWith(path.join(repo, 'site-src')) && !file.startsWith(uploads)) return send(res, 403, 'no', 'text/plain'); fs.readFile(file, (e, buf) => { if (e) return send(res, 404, 'not found', 'text/plain'); res.writeHead(200, { 'content-type': (MIME[path.extname(file)] || 'application/octet-stream') + '; charset=utf-8', 'cache-control': 'no-store' }); res.end(buf) }) }
const uploads = fs.mkdtempSync(path.join(process.env.TMPDIR || '/tmp', 'studio-up-'))

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x'); const p = url.pathname
  const sid = /(?:^|; )studio=([^;]+)/.exec(req.headers.cookie || '')?.[1]; const sess = sessions.get(sid)
  const user = sess && USERS[sess.user]
  const J = async () => { const b = await readBody(req); try { return JSON.parse(b.toString() || '{}') } catch { return {} } }
  if (p === '/healthz') return send(res, 200, { ok: true })
  if (!p.startsWith('/api/') && !p.startsWith('/preview/')) {
    if (p.startsWith('/assets/')) { const rel = p.slice(8); for (const root of [path.join(repo, 'site-src', 'assets'), here, uploads]) { const f = path.join(root, rel); if (fs.existsSync(f) && fs.statSync(f).isFile()) return serveFile(res, f) } return send(res, 404, 'not found', 'text/plain') }
    const rel = p === '/' ? 'index.html' : p.slice(1)
    return serveFile(res, path.join(web, 'dist', rel))
  }
  if (p === '/api/login' && req.method === 'POST') {
    const b = await J(); const u = USERS[b.user]
    if (!u || u.pw !== b.password) return send(res, 401, { error: 'bad_credentials' })
    const id = crypto.randomBytes(16).toString('hex'); sessions.set(id, { user: u.key, csrf: crypto.randomBytes(12).toString('hex') })
    res.setHeader('set-cookie', `studio=${id}; Path=/; HttpOnly; SameSite=Strict`); return send(res, 200, { ok: true })
  }
  if (!user) return send(res, 401, { error: 'auth' })
  if (req.method !== 'GET' && req.headers['x-csrf-token'] !== sess.csrf) return send(res, 403, { error: 'csrf' })
  if (p === '/api/logout') { sessions.delete(sid); return send(res, 200, { ok: true }) }
  if (p === '/api/me') return send(res, 200, { user: user.key, name: user.name, ui_lang: 'es', csrf: sess.csrf, other: user.key === 'javier' ? 'Matías' : 'Javier' })
  let m
  if (p === '/api/pieces' && req.method === 'GET') { const st = url.searchParams.get('state'); return send(res, 200, Object.values(store).filter(x => !st || x.state === st).map(meta).sort((a, b) => b.updated_at.localeCompare(a.updated_at))) }
  if (p === '/api/pieces' && req.method === 'POST') {
    const b = await J(); const slug = (b.title || 'sin-titulo').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'sin-titulo'
    let s = slug; let i = 2; while (store[s]) s = `${slug}-${i++}`
    store[s] = mkPiece({ slug: s, author: user.key, kind: b.kind || 'essay', state: 'draft', source_locale: b.source_locale || 'es-419', updated_at: now(), piece: { ...fxPiece, id: 'FCMO-P-' + crypto.randomBytes(6).toString('hex'), slug: s, kind: b.kind || 'essay', authors: [{ key: user.key, name: user.name }] }, locales: { [b.source_locale || 'es-419']: { state: 'drafting' } }, docs: { [b.source_locale || 'es-419']: { rev: 1, doc: blankDoc(b.source_locale || 'es-419', b.title || '') } } })
    return send(res, 200, { slug: s })
  }
  if ((m = /^\/api\/pieces\/([^/]+)(\/.*)?$/.exec(p))) {
    const pc = store[m[1]]; if (!pc) return send(res, 404, { error: 'not_found' }); const sub = m[2] || ''; let k
    if (sub === '' ) return send(res, 200, meta(pc))
    if ((k = /^\/doc\/([^/]+)$/.exec(sub))) {
      const loc = k[1]
      if (req.method === 'GET') { if (!pc.docs[loc]) pc.docs[loc] = { rev: 0, doc: blankDoc(loc) }; return send(res, 200, pc.docs[loc]) }
      const b = await J(); const cur = pc.docs[loc] || { rev: 0, doc: blankDoc(loc) }
      if (b.base_rev !== cur.rev) return send(res, 409, { rev: cur.rev, doc: cur.doc, by: 'Matías', at: cur.at || now() })
      if (!b.doc || b.doc.schema !== 'fcmo-essay-doc-v1' || !Array.isArray(b.doc.blocks)) return send(res, 422, { error: 'schema' })
      pc.docs[loc] = { rev: cur.rev + 1, doc: b.doc, at: now() }; pc.cursor[loc] = b.cursor; pc.updated_at = now()
      if (!pc.locales[loc] || pc.locales[loc].state === 'empty') pc.locales[loc] = { state: 'drafting' }
      return send(res, 200, { rev: pc.docs[loc].rev })
    }
    if ((k = /^\/lock\/([^/]+)$/.exec(sub))) {
      const loc = k[1]; if (req.method === 'DELETE') { delete pc.lock[loc]; return send(res, 200, { ok: true }) }
      const b = await J(); const l = pc.lock[loc]
      if (l && l.user !== user.key && !b.take) return send(res, 409, { lock_user: USERS[l.user].name, at: l.at })
      pc.lock[loc] = { user: user.key, at: now() }; return send(res, 200, pc.lock[loc])
    }
    if (sub === '/sources') { if (req.method === 'PUT') { pc.sources = (await J()).sources || []; return send(res, 200, { ok: true }) } return send(res, 200, { sources: pc.sources }) }
    if (sub === '/figures') { if (req.method === 'PUT') { pc.figures = (await J()).figures || {}; return send(res, 200, { ok: true }) } return send(res, 200, { figures: pc.figures }) }
    if (sub === '/figures/upload') {
      const buf = await readBody(req); if (buf.length > 15e6 || buf.slice(8, 12).toString() !== 'WEBP') return send(res, 415, { error: 'webp_only' })
      const id = 'fig-' + crypto.randomBytes(4).toString('hex'); fs.mkdirSync(path.join(uploads, pc.slug), { recursive: true }); fs.writeFileSync(path.join(uploads, pc.slug, id + '.webp'), buf)
      pc.figures[id] = { file: `${pc.slug}/${id}.webp`, width: Number(req.headers['x-width'] || 1200), height: Number(req.headers['x-height'] || 630), credit: '', licence: '', alt: {}, caption: {} }
      return send(res, 200, { fig_id: id, figure: pc.figures[id] })
    }
    if ((k = /^\/locale\/([^/]+)\/state$/.exec(sub))) { const b = await J(); const l = k[1]; const cur = pc.locales[l] || {}; pc.locales[l] = { ...cur, state: b.state || cur.state, reviewed: !!b.reviewed, by: b.reviewed ? user.name : cur.by, at: b.reviewed ? now() : cur.at, origin: b.reviewed && cur.origin === 'agent_draft' ? 'agent_draft_human_edited' : cur.origin }; return send(res, 200, pc.locales[l]) }
    if (sub === '/versions' && req.method === 'GET') return send(res, 200, pc.versions.map(v => ({ rev: v.rev, at: v.at, user: USERS[v.user]?.name || v.user, name: v.name || null })).reverse())
    if (sub === '/versions' && req.method === 'POST') { const b = await J(); const rev = Math.max(0, ...pc.versions.map(v => v.rev)) + 1; pc.versions.push({ rev, at: now(), user: user.key, name: b.name || null, snapshot: clone(pc.docs) }); return send(res, 200, { rev }) }
    if ((k = /^\/versions\/(\d+)\/restore$/.exec(sub))) {
      const v = pc.versions.find(x => x.rev === Number(k[1])); if (!v) return send(res, 404, {})
      const rev = Math.max(...pc.versions.map(x => x.rev)) + 1; pc.versions.push({ rev, at: now(), user: user.key, name: 'Antes de restaurar', snapshot: clone(pc.docs) })
      for (const l of Object.keys(v.snapshot)) pc.docs[l] = { rev: (pc.docs[l]?.rev || 0) + 1, doc: clone(v.snapshot[l].doc) }
      return send(res, 200, { ok: true })
    }
    if (sub === '/diff') { if (url.searchParams.get('from') === 'published') return send(res, 404, { error: 'no_published' }); const loc = url.searchParams.get('loc'); const f = pc.versions.find(v => v.rev === Number(url.searchParams.get('from'))); const t = url.searchParams.get('to') === 'current' ? { snapshot: pc.docs } : pc.versions.find(v => v.rev === Number(url.searchParams.get('to'))); if (!t) return send(res, 404, {}); return send(res, 200, diffDocs(f && f.snapshot[loc] && f.snapshot[loc].doc, t.snapshot[loc].doc)) }
    if (sub === '/comments') { if (req.method === 'POST') { const b = await J(); const c = { id: crypto.randomBytes(4).toString('hex'), slug: pc.slug, locale: b.locale, block_id: b.block_id, user: user.name, at: now(), body: b.body, resolved_at: null }; pc.comments.push(c); return send(res, 200, c) } return send(res, 200, pc.comments) }
    if (sub === '/checks') return send(res, 200, checks(pc))
    if (sub === '/review/request') { const c = checks(pc); if (c.some(x => !x.ok)) return send(res, 422, { error: 'checks' }); pc.state = 'in_review'; pc.review = { state: 'requested', at: now() }; return send(res, 200, pc.review) }
    if ((k = /^\/review\/(approve|changes)$/.exec(sub))) {
      if (pc.author === user.key) return send(res, 403, { error: 'same_person' }); const b = await J()
      if (k[1] === 'approve') { pc.state = 'publishing'; pc.review = { state: 'approved', at: now(), note: b.note }; pc.publication = { started: Date.now() } } else { pc.state = 'changes_requested'; pc.review = { state: 'changes', at: now(), note: b.note } }
      return send(res, 200, pc.review)
    }
    if (sub === '/publication') return send(res, 200, publication(pc) || { steps: [], state: pc.state })
    if (sub === '/assist') return send(res, 200, { status: 'no_worker' })
    return send(res, 404, { error: 'no_route' })
  }
  if ((m = /^\/api\/comments\/([^/]+)\/resolve$/.exec(p))) { for (const pc of Object.values(store)) { const c = pc.comments.find(x => x.id === m[1]); if (c) { c.resolved_at = now(); return send(res, 200, c) } } return send(res, 404, {}) }
  if (p === '/api/library/briefs') return send(res, 200, [
    { id: 'FCMO-0A1B2C3D4E5F', date: '2026-10-03', headline: 'A lab reports faster long-context inference', class: 'B', beat: 'Models' },
    { id: 'FCMO-1B2C3D4E5F60', date: '2026-10-03', headline: 'A new benchmark questions agent evaluations', class: 'C', beat: 'Evaluation' },
    { id: 'FCMO-2C3D4E5F6071', date: '2026-10-02', headline: 'Open weights release changes local deployment costs', class: 'A', beat: 'Open models' },
    { id: 'FCMO-3D4E5F607182', date: '2026-10-02', headline: 'Robotics lab shares manipulation results', class: 'D', beat: 'Robotics' }])
  if (p.startsWith('/api/issues')) return send(res, 200, [])
  if (p === '/api/site/rollback') return send(res, 200, { ok: true })
  if (p.startsWith('/api/jobs/')) return send(res, 200, { status: 'no_worker' })
  if ((m = /^\/preview\/([^/]+)\/([^/]+)\/?$/.exec(p))) {
    const pc = store[m[1]]; const loc = m[2]; if (!pc || !pc.docs[loc]) return send(res, 404, 'no preview', 'text/plain')
    const st = pc.locales[loc] || {}
    const reqj = { piece: pc.piece, doc: pc.docs[loc].doc, sources: pc.sources, figures: Object.fromEntries(Object.entries(pc.figures).map(([k, f]) => [k, { ...f, file: f.file.startsWith('figures/') ? f.file : f.file }])), locale: loc, theme: url.searchParams.get('theme') || '', machine: st.origin === 'agent_draft' && !st.reviewed }
    const child = execFile('python3', [path.join(here, 'essay_pages.py'), '--stdin'], { cwd: repo, maxBuffer: 1 << 26 }, (e, out, err) => { if (e) return send(res, 500, String(err), 'text/plain'); send(res, 200, out, 'text/html') })
    child.stdin.end(JSON.stringify(reqj)); return
  }
  send(res, 404, { error: 'no_route' })
})
server.listen(port, '127.0.0.1', () => console.log(`studio dev mock on http://127.0.0.1:${port}/ (javier|matias / estudio)`))
