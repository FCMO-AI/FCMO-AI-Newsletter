// usage: node overflow.mjs <url>... [--viewport 390x844]... [--tolerance 1] [--json OUT]
//
// Fails when a page scrolls horizontally: documentElement.scrollWidth > clientWidth
// (+ tolerance px). The report lists up to 10 elements whose right edge passes the
// viewport, with a short CSS path, so the offender can be fixed rather than hidden.
// Exit 0 pass, 1 overflow or load error, 2 no browser.
import { parseArgs, parseViewport, launch, openPage, emit, DEFAULT_VIEWPORTS, EXIT_OK, EXIT_FAIL } from './_common.mjs'

const args = parseArgs(process.argv.slice(2), { viewport: DEFAULT_VIEWPORTS, tolerance: 1, json: '' })
if (!args._.length) { console.error('usage: node overflow.mjs <url>... [--viewport WxH]'); process.exit(2) }

const browser = await launch()
const pages = []
let failed = false
for (const url of args._) {
  for (const vpText of args.viewport) {
    const viewport = parseViewport(vpText)
    const { context, page, status, error } = await openPage(browser, url, viewport)
    let measure = null
    if (!error) {
      measure = await page.evaluate((tolerance) => {
        const root = document.documentElement
        const clientWidth = root.clientWidth
        const cssPath = (el) => {
          const parts = []
          for (let node = el; node && node.nodeType === 1 && parts.length < 4; node = node.parentElement) {
            let part = node.tagName.toLowerCase()
            if (node.id) { part += '#' + node.id; parts.unshift(part); break }
            const cls = [...node.classList].slice(0, 2).join('.')
            if (cls) part += '.' + cls
            parts.unshift(part)
          }
          return parts.join(' > ')
        }
        const offenders = []
        for (const el of document.body ? document.body.querySelectorAll('*') : []) {
          const rect = el.getBoundingClientRect()
          if (rect.width > 0 && rect.right > clientWidth + tolerance) {
            offenders.push({ path: cssPath(el), right: Math.round(rect.right), width: Math.round(rect.width) })
            if (offenders.length >= 10) break
          }
        }
        return { scrollWidth: root.scrollWidth, clientWidth, offenders }
      }, args.tolerance)
    }
    const pass = !error && measure.scrollWidth <= measure.clientWidth + args.tolerance
    failed = failed || !pass
    pages.push({ url, viewport: vpText, status, error, ...(measure || {}), pass })
    await context.close()
  }
}
await browser.close()
emit({ check: 'overflow', pass: !failed, pages }, args.json)
process.exit(failed ? EXIT_FAIL : EXIT_OK)
