import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import os from 'node:os'
import path from 'node:path'
import { publicationParts, publicationBundle } from '../offline/publication-compiler.mjs'
import { S } from '../src/i18n.js'

const root = new URL('../', import.meta.url).pathname
const { sheet } = publicationParts(root)
function element (tag, attrs, ...children) {
  return { tag, attrs: attrs || {}, children: children.flat(Infinity).filter(Boolean),
    append (...nodes) { this.children.push(...nodes.flat(Infinity).filter(Boolean)) },
    get firstChild () { return this.children[0] } }
}
const buttons = node => (node.tag === 'button' ? [node] : []).concat(...(node.children || []).filter(n => typeof n === 'object').map(buttons))
async function render (checks = [{ ok: true }], readiness = { live_enabled: true, email_enabled: false }) {
  const meta = { author: 'javier', state: 'draft', kind: 'essay', title: 'Prueba', source_locale: 'es-419', head_rev: 1, locales: {}, meta: { status: 'published', distribution: { email: false } } }
  const calls = [], location = { hash: '' }, target = element('main')
  const scope = { location, session: { me: { user: 'javier' } }, h: element,
    t: k => S.es[k] || k, clear: n => { n.children = [] }, toast () {}, shell: n => n, crumbs: () => '', other: () => '', LOCS: [], LOCALE_NAME: {},
    get: async url => url.endsWith('/publication-readiness') ? readiness : meta,
    post: async (url, body) => { calls.push({ url, body }) },
    checksList: async () => Object.assign(element('section'), { list: checks }) }
  vm.runInNewContext(sheet.body.replace(/^export /, '') + '\nthis.render = publishScreen;', scope)
  await scope.render(target, 'prueba')
  return { target, calls, location }
}
test('the author presses Publicar and goes directly to progress with no reviewer step', async () => {
  const { target, calls, location } = await render()
  const button = buttons(target).find(b => b.children.includes('Publicar'))
  assert.ok(button); assert.equal(button.attrs.disabled, false)
  await button.attrs.onclick({ currentTarget: button.attrs })
  assert.equal(calls.filter(c => c.url.endsWith('/review/request')).length, 1)
  assert.equal(calls.filter(c => c.url.endsWith('/review/approve')).length, 0)
  assert.equal(location.hash, '#/p/prueba/progress')
  assert.equal(JSON.stringify(target).includes('Matías'), false)
})
test('a red automatic check and unread or disabled publication keep Publicar disabled', async () => {
  for (const [checks, readiness] of [[[{ ok: false }], { live_enabled: true }], [[{ ok: true }], null], [[{ ok: true }], { live_enabled: false }]]) {
    const { target } = await render(checks, readiness)
    assert.equal(buttons(target).find(b => b.children.includes('Publicar')).attrs.disabled, true)
  }
})
test('the served offline bundle includes the current publication function', async () => {
  const code = fs.readFileSync(new URL('../dist/app.js', import.meta.url), 'utf8')
  assert.ok(code.includes(sheet.body.replace(/^export /, '')))
  assert.match(code, /nl=publishScreen; Hr=haltPlan/)
  assert.equal(S.es['prog.done'], 'Publicado y verificado')
})

test('offline compilation refuses a changed dependency seed', () => {
  assert.throws(() => publicationBundle(root, Buffer.from('changed')), /semilla/)
})
test('offline compilation refuses source drift outside the authorized publication regions', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-publication-'))
  try {
    fs.mkdirSync(path.join(tmp, 'src')); fs.mkdirSync(path.join(tmp, 'offline'))
    for (const file of ['src/screens-flow.js', 'src/publication-actions.js', 'src/i18n.js', 'offline/publication-rest.json']) fs.copyFileSync(path.join(root, file), path.join(tmp, file))
    fs.appendFileSync(path.join(tmp, 'src/screens-flow.js'), '\n// unrelated drift\n')
    const seed = fs.readFileSync(path.join(root, 'offline/app.seed.js'))
    assert.throws(() => publicationBundle(tmp, seed), /fuera de la publicación/)
  } finally { fs.rmSync(tmp, { recursive: true, force: true }) }
})
