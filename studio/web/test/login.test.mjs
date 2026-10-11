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
