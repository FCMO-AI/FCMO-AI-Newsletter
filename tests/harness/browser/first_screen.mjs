// usage: node first_screen.mjs <url>... [--viewport 390x844]... [--selector CSS] [--shots PREFIX]
//        [--allow-errors] [--json OUT]
//
// Checks that the lead headline is inside the first screen: the first element
// matching --selector (default: the lead story headline, then any main heading)
// must be visible with top >= 0 and top + height <= viewport height. Also fails on
// console errors, failed requests (>= 400 or network errors) and non-2xx pages
// unless --allow-errors. Prints one JSON report; exit 0 pass, 1 fail, 2 no browser.
import { parseArgs, parseViewport, launch, openPage, emit, DEFAULT_VIEWPORTS, EXIT_OK, EXIT_FAIL } from './_common.mjs'

const DEFAULT_SELECTOR = '[data-lead] h1, [data-lead] h2, .lead h1, .lead h2, main h1, main h2, h1'
const args = parseArgs(process.argv.slice(2), { viewport: DEFAULT_VIEWPORTS, selector: DEFAULT_SELECTOR, shots: '', 'allow-errors': false, json: '' })
if (!args._.length) { console.error('usage: node first_screen.mjs <url>... [--viewport WxH] [--selector CSS]'); process.exit(2) }

const browser = await launch()
const pages = []
let failed = false
for (const url of args._) {
  for (const vpText of args.viewport) {
    const viewport = parseViewport(vpText)
    const { context, page, status, error, consoleErrors, failedRequests } = await openPage(browser, url, viewport)
    let lead = null
    if (!error) {
      lead = await page.evaluate((selector) => {
        for (const el of document.querySelectorAll(selector)) {
          const rect = el.getBoundingClientRect()
          const style = getComputedStyle(el)
          if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
            return { tag: el.tagName.toLowerCase(), text: el.innerText.trim().slice(0, 140), top: Math.round(rect.top), height: Math.round(rect.height), bottom: Math.round(rect.bottom) }
          }
        }
        return null
      }, args.selector)
    }
    if (args.shots) await page.screenshot({ path: `${args.shots}-${vpText}-${pages.length}.png` }).catch(() => {})
    const within = Boolean(lead && lead.top >= 0 && lead.bottom <= viewport.height)
    const errorsOk = args['allow-errors'] || (consoleErrors.length === 0 && failedRequests.length === 0 && status !== null && status < 400)
    const pass = !error && within && errorsOk
    failed = failed || !pass
    pages.push({ url, viewport: vpText, status, error, lead, withinFirstScreen: within, consoleErrors, failedRequests: failedRequests.slice(0, 20), pass })
    await context.close()
  }
}
await browser.close()
emit({ check: 'first_screen', selector: args.selector, pass: !failed, pages }, args.json)
process.exit(failed ? EXIT_FAIL : EXIT_OK)
