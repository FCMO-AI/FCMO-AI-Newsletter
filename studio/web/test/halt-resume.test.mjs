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

test('an integrity halt can only be resumed by the author, behind a confirmation', () => {
  for (const reason of ['foreign_merge', 'merge_outside']) {
    assert.deepEqual(haltPlan({ ...base, halt_reason: reason }, 'javier'), { integrity: true, canResume: true, confirm: true })
    assert.equal(haltPlan({ ...base, halt_reason: reason }, 'matias').canResume, false)
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

import { progressView } from '../src/publication-actions.js'

test('a halted, unfinished publication puts the halt card first and freezes every live part', () => {
  for (const reason of ['infra', 'effect', 'foreign_merge']) for (const me of ['javier', 'matias']) {
    assert.deepEqual(progressView({ ...base, state: 'pr_open', halt_reason: reason }, me), { haltFirst: true, frozen: true, live: false })
  }
})

test('a running publication keeps its live ticker and ring, and finished ones show no halt card', () => {
  assert.deepEqual(progressView({ halted: false, state: 'pr_open', author: 'javier' }, 'matias'), { haltFirst: false, frozen: false, live: true })
  for (const state of ['published', 'failed']) assert.deepEqual(progressView({ ...base, state, halt_reason: 'infra' }, 'matias'), { haltFirst: false, frozen: false, live: false })
})
