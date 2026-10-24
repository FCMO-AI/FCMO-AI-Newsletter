import test from 'node:test'
import assert from 'node:assert/strict'
import { haltPlan } from '../src/publication-actions.js'
import { S } from '../src/i18n.js'

const base = { halted: true, author: 'javier' }

test('a publication that is not halted has no plan', () => {
  assert.equal(haltPlan({ halted: false, author: 'javier' }, 'matias'), null)
  assert.equal(haltPlan(null, 'matias'), null)
})

test('a technical halt can be resumed by either editor without a confirmation', () => {
  for (const reason of ['infra', 'effect']) for (const me of ['javier', 'matias']) {
    assert.deepEqual(haltPlan({ ...base, halt_reason: reason }, me), { integrity: false, canResume: true, confirm: false })
  }
})

test('an integrity halt can only be resumed by the reviewer, behind a confirmation', () => {
  for (const reason of ['foreign_merge', 'merge_outside']) {
    assert.deepEqual(haltPlan({ ...base, halt_reason: reason }, 'matias'), { integrity: true, canResume: true, confirm: true })
    assert.equal(haltPlan({ ...base, halt_reason: reason }, 'javier').canResume, false)
  }
})

test('every halt string exists in both languages and names no tool', () => {
  const keys = Object.keys(S.es).filter(k => k.startsWith('prog.halt.'))
  assert.ok(keys.length >= 9)
  for (const k of keys) {
    assert.ok(S.en[k], k)
    assert.doesNotMatch(S.es[k] + S.en[k], /git|GitHub|branch|merge|commit|JSON/i)
  }
})
