import { test } from 'node:test'
import assert from 'node:assert/strict'
import { stripWebpMetadata } from '../src/webp.js'
import { readFileSync } from 'node:fs'
test('Chrome canvas ICC profile is removed without changing image pixels', async () => {
  const bytes = readFileSync(new URL('../../../tests/fixtures/studio/chrome-canvas.webp', import.meta.url))
  const result = Buffer.from(await (await stripWebpMetadata(new Blob([bytes], { type: 'image/webp' }))).arrayBuffer())
  const chunks = buffer => { const out = {}; for (let p=12;p<buffer.length;) { const n=buffer.readUInt32LE(p+4); out[buffer.toString('ascii',p,p+4)]=buffer.subarray(p+8,p+8+n); p+=8+n+(n%2) } return out }
  const before=chunks(bytes), after=chunks(result)
  assert(before.ICCP); assert(!after.ICCP); assert.equal(after.VP8X[0] & 0x2c,0)
  assert.deepEqual(after['VP8 '], before['VP8 ']); assert.equal(result.readUInt32LE(4), result.length-8)
})
