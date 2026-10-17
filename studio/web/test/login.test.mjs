// Exercise the same source function inserted into the offline bundle. No DOM
// package, editor dependencies, credential fixture on disk or network required.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { discoverLoginBindings, loginSource } from '../offline-build.mjs'

test('offline binding discovery follows generated names instead of pinned minifier aliases', () => {
  const bundle = 'function z(a,b){n("form",{class:"login-card"});f("login.bad");await X("/api/login",{});x instanceof Err&&x.status===0;" ".normalize("NFD").replace(/\\p{M}/gu,"")}'
  assert.deepEqual(discoverLoginBindings(bundle), { login: 'z', h: 'n', t: 'f', post: 'X', ApiError: 'Err' })
})

test('login sends accented and case variants as the canonical username', async () => {
  const source = fs.readFileSync(new URL('../src/screens-home.js', import.meta.url), 'utf8')
  for (const user of ['Matías', 'MATIAS', 'mati\u0301as', ' matias ']) {
    const nodes = new Map()
    let received, completed = false
    const h = (tag, attrs, ...children) => {
      const node = { tag, attrs, children, append () {}, select () {} }
      if (attrs?.id) nodes.set(attrs.id, node)
      if (tag === 'form') nodes.set('form', node)
      return node
    }
    const scope = { h, t: x => x, post: async (url, body) => { received = { url, ...body } }, ApiError: class extends Error {} }
    vm.runInNewContext(loginSource(source).body + '\nthis.login = login;', scope)
    scope.login({ append () {} }, () => { completed = true })
    nodes.get('u').value = user; nodes.get('p').value = 'unused-test-password'
    await nodes.get('form').attrs.onsubmit({ preventDefault () {} })
    assert.deepEqual(received, { url: '/api/login', user: 'matias', password: 'unused-test-password' })
    assert.equal(completed, true)
  }
})

test('an expired session says so on the login screen, and a plain visit does not', () => {
  const source = fs.readFileSync(new URL('../src/screens-home.js', import.meta.url), 'utf8')
  const render = notice => {
    const seen = []
    const h = (tag, attrs, ...children) => { seen.push({ tag, attrs, children }); return { tag, attrs, children, append () {} } }
    const scope = { h, t: x => x, post: async () => {}, ApiError: class extends Error {} }
    vm.runInNewContext(loginSource(source).body + '\nthis.login = login;', scope)
    scope.login({ append () {} }, () => {}, notice)
    return seen.filter(n => n.attrs && n.attrs.role === 'status' && n.attrs.class === 'notice')
  }
  assert.equal(render('Tu sesión terminó.').length, 1)
  assert.equal(render('').length, 0)
  assert.equal(render(undefined).length, 0)
})

test('modal actions run once per click burst and report failure instead of swallowing it', () => {
  const ui = fs.readFileSync(new URL('../src/ui.js', import.meta.url), 'utf8')
  assert.match(ui, /if \(btn\.disabled\) return/)
  assert.match(ui, /btn\.disabled = true/)
  assert.match(ui, /catch \(e\) \{ fail\.hidden = false/)
})
