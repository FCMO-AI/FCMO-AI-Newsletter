// The publish sheet asks a plain yes/no about emailing subscribers, without tool or format jargon.
import test from 'node:test'
import assert from 'node:assert/strict'
import { S } from '../src/i18n.js'

const JARGON = /feeds?\b|rss|atom|json|despliegue|deploy|webhook|\bgit\b/i
const keys = ['pub.email.q', 'pub.email.yes', 'pub.email.no', 'pub.email.title.off', 'pub.where', 'pub.email.after', 'pub.email.off', 'pub.email.state.on', 'pub.email.state.no']

test('email banner copy is plain in Spanish and English', () => {
  for (const lang of ['es', 'en']) {
    for (const key of keys) {
      assert.ok(S[lang][key], `${lang} ${key} exists`)
      assert.doesNotMatch(S[lang][key], JARGON, `${lang} ${key}`)
    }
  }
  assert.match(S.es['pub.email.q'], /^¿.*\?$/)
  assert.match(S.es['pub.email.yes'], /^Sí/)
  assert.match(S.es['pub.email.no'], /^No/)
})
