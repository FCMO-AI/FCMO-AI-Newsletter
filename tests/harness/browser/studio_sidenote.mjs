// usage: node studio_sidenote.mjs <studio base url> <seeded slug with a footnote>
// The margin note (.sidenote, shown from 1100 px) must stay inside the viewport: no sideways scroll at the widths where it appears.
import { session, check, finish } from './studio_common.mjs'
const [base, slug] = process.argv.slice(2)
if (!base || !slug) { console.error('usage: node studio_sidenote.mjs <url> <slug>'); process.exit(2) }
const s = await session(base); const { page } = s
for (const width of [1100, 1280, 1440, 1920]) for (const loc of ['en', 'es-419']) {
  await page.setViewportSize({ width, height: 900 })
  await page.goto(`${s.base}preview/${slug}/${loc}/?w=${width}&theme=light`, { waitUntil: 'networkidle' })
  const m = await page.evaluate(() => { const n = document.querySelector('.sidenote'); const r = n && n.getBoundingClientRect()
    return { notes: document.querySelectorAll('.sidenote').length, right: r ? Math.round(r.right) : null, left: r ? Math.round(r.left) : null, over: document.documentElement.scrollWidth - document.documentElement.clientWidth, w: document.documentElement.clientWidth } })
  check(`${loc} @${width}: the margin note exists`, m.notes > 0, JSON.stringify(m))
  check(`${loc} @${width}: the margin note stays inside the viewport and the page does not scroll sideways`, m.notes > 0 && m.right <= m.w && m.left >= 0 && m.over <= 1, JSON.stringify(m))
}
await finish(s)
