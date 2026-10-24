import test from 'node:test'
import assert from 'node:assert/strict'
import { approvedAtMs, currentStage, elapsedMs, toMs } from '../src/progress-time.js'

test('the counter starts at the approval, not at the first check or at page load', () => {
  const approved = Date.parse('2026-10-24T15:00:00Z')
  const publication = { approved_at: '2026-10-24T15:00:00Z', timeline: [{ state: 'candidate', at: '2026-10-24T15:02:30Z' }] }
  assert.equal(approvedAtMs(publication, null), approved)
  assert.equal(elapsedMs(approvedAtMs(publication), approved + 150000), 150000)
})

test('epoch seconds and the approver device stamp are understood', () => {
  assert.equal(toMs(1792854000), 1792854000000)
  assert.equal(approvedAtMs({}, '1792854000000'), 1792854000000)
  assert.equal(approvedAtMs({ created: 1792854000.5 }, null), 1792854000500)
})

test('an unknown start hides the counter instead of inventing one', () => {
  assert.equal(approvedAtMs({ timeline: [{ state: 'candidate', at: '2026-10-24T15:02:30Z' }] }, null), 0)
  assert.equal(elapsedMs(0, Date.now()), -1)
})

test('approval is done as soon as a publication exists; the checks are the active step', () => {
  assert.equal(currentStage('approved', -1, 6), 1)
  assert.equal(currentStage('approved', 0, 6), 1)
  assert.equal(currentStage('merged', 3, 6), 3)
  assert.equal(currentStage('published', 5, 6), 5)
})
