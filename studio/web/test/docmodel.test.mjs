import { test } from 'node:test'
import assert from 'node:assert/strict'
import { schema, docToPM, pmToDoc, newId } from '../src/docmodel.js'
import { docs } from '../dev/fixture.mjs'

for (const loc of Object.keys(docs)) {
  test(`round trip keeps the document identical (${loc})`, () => {
    const src = JSON.parse(JSON.stringify(docs[loc]))
    const pm = docToPM(src)
    const back = pmToDoc(pm, { locale: loc, title: src.title, dek: src.dek })
    assert.deepEqual(back, src)
  })
}

test('unknown block types are rejected, never stored', () => {
  const bad = { schema: 'fcmo-essay-doc-v1', locale: 'en', title: 'x', dek: '', blocks: [{ id: 'b-00000001', type: 'script', content: [] }], footnotes: {} }
  assert.throws(() => docToPM(bad), /unknown block/i)
})

test('javascript: links are dropped when pasting into the model', () => {
  const doc = { schema: 'fcmo-essay-doc-v1', locale: 'en', title: 't', dek: '', footnotes: {},
    blocks: [{ id: 'b-00000001', type: 'p', content: [{ t: 'link', href: 'javascript:alert(1)', c: [{ t: 'text', v: 'hi' }] }] }] }
  const back = pmToDoc(docToPM(doc), { locale: 'en', title: 't', dek: '' })
  assert.equal(JSON.stringify(back).includes('javascript'), false)
  assert.equal(back.blocks[0].content[0].v, 'hi')
})

test('new ids have the b-xxxxxxxx shape', () => {
  assert.match(newId('b'), /^b-[0-9a-f]{8}$/)
  assert.match(newId('fn'), /^fn-[0-9a-f]{8}$/)
})

test('schema has no raw html node', () => {
  assert.equal(Object.keys(schema.nodes).some(n => /html|script|raw/i.test(n)), false)
})
