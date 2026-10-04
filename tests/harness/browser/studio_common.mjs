// Shared helpers for the Studio browser tests. Credentials come from the environment,
// never from the repository: STUDIO_USER (default javier) and STUDIO_PASS.
import { launch, EXIT_OK, EXIT_FAIL } from './_common.mjs'

export const USER = process.env.STUDIO_USER || 'javier'
export const PASS = process.env.STUDIO_PASS || 'estudio'
export const results = []
export function check (name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail })
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail ? ' :: ' + detail : ''}`)
}
export async function session (base, { viewport = { width: 1440, height: 900 }, user = USER, pass = PASS, scheme = 'light' } = {}) {
  const browser = await launch()
  const context = await browser.newContext({ viewport, colorScheme: scheme, reducedMotion: 'reduce', acceptDownloads: false })
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', e => errors.push('pageerror: ' + String(e).slice(0, 300)))
  page.on('console', m => { if (m.type() === 'error' && !/status of 401|ERR_INTERNET_DISCONNECTED/.test(m.text())) errors.push(m.text().slice(0, 300)) })
  await page.goto(base)
  await page.waitForSelector('#u')
  await page.fill('#u', user); await page.fill('#p', pass); await page.click('button[type=submit]')
  await page.waitForSelector('.home-head')
  return { browser, context, page, errors, base: base.replace(/#.*$/, '').replace(/\/?$/, '/') }
}
export const go = async (s, hash) => { await s.page.goto(s.base + hash); await s.page.waitForTimeout(250) }
export function finish (s) {
  const failed = results.filter(r => !r.ok)
  if (s.errors && s.errors.length) { check('no console errors', false, s.errors.join(' | ')) }
  console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
  return s.browser.close().then(() => process.exit(failed.length ? EXIT_FAIL : EXIT_OK))
}
// A valid 64x40 PNG built in memory (no fixture file, no network).
import zlib from 'node:zlib'
function crc32 (buf) { let c; let crc = ~0; for (const b of buf) { c = (crc ^ b) & 0xff; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; crc = (crc >>> 8) ^ c } return ~crc >>> 0 }
function chunk (type, data) { const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td)); return Buffer.concat([len, td, crc]) }
function makePng (w, h) {
  const raw = Buffer.alloc((w * 3 + 1) * h)
  for (let y = 0; y < h; y++) { raw[y * (w * 3 + 1)] = 0; for (let x = 0; x < w; x++) { const o = y * (w * 3 + 1) + 1 + x * 3; raw[o] = 40 + x * 3; raw[o + 1] = 80 + y * 4; raw[o + 2] = 120 } }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))])
}
export const TINY_PNG = makePng(64, 40)
