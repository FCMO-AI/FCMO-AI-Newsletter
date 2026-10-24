// The connect card renders only while the person's own credential is not usable. A connection that
// says 'ready' in that situation (session closed, token revoked, Studio not restarted) must offer
// 'Empezar', never a card with no button.
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'

const source = fs.readFileSync(new URL('../src/main.js', import.meta.url), 'utf8')
const start = source.indexOf('function githubConnectCard')
const end = source.indexOf('\nsetInterval(', start)
assert.ok(start > 0 && end > start, 'githubConnectCard must stay a top-level function')

function render (connection, ghUi) {
  const h = (tag, attrs, ...children) => ({ tag, attrs: attrs || {}, children: children.flat(Infinity).filter(Boolean) })
  const scope = { h, t: key => key, ghUi, session: { me: { other: 'Matías' } }, requestCode () {}, confirmTyped () {}, toast () {}, del: async () => {}, refreshReadiness: async () => {}, navigator: {} }
  vm.runInNewContext(source.slice(start, end) + '\nthis.card = githubConnectCard;', scope)
  return scope.card(connection)
}
const buttons = node => (node.tag === 'button' ? [node] : []).concat(...(node.children || []).filter(c => c && typeof c === 'object').map(buttons))

test("a 'ready' connection with no usable credential shows the Start button", () => {
  const card = render({ state: 'ready' }, { checking: false, notYet: false, opened: false })
  assert.equal(card.attrs['data-state'], 'idle')
  const labels = buttons(card).map(b => b.children[0])
  assert.deepEqual(labels, ['gh.guide.start'])
})

test("while the confirmation is running, 'ready' still shows the checking message and no Start button", () => {
  const card = render({ state: 'ready' }, { checking: true, notYet: false, opened: false })
  assert.equal(card.attrs['data-state'], 'ready')
  assert.deepEqual(buttons(card), [])
})
