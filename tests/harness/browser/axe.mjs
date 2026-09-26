// usage: node axe.mjs <url>... [--viewport 390x844]... [--impact serious,critical]
//        [--min-font 12] [--no-axe] [--json OUT]
//
// Runs axe-core in the page and fails on violations whose impact is listed in
// --impact (default serious,critical). axe-core is loaded from AXE_CORE_PATH (a
// path to axe.min.js) or resolved as the axe-core package through NODE_PATH; when
// it cannot be found the script exits 2 with AXE_UNAVAILABLE instead of passing.
// --min-font N also fails when any element with visible text has a computed
// font-size below N px (use --no-axe to run only that check).
// Exit 0 pass, 1 fail, 2 browser or axe-core unavailable.
import { readFileSync } from 'node:fs'
import { parseArgs, parseViewport, launch, openPage, emit, resolvePath, unavailable, DEFAULT_VIEWPORTS, EXIT_OK, EXIT_FAIL } from './_common.mjs'

const args = parseArgs(process.argv.slice(2), { viewport: DEFAULT_VIEWPORTS, impact: 'serious,critical', 'min-font': 0, 'no-axe': false, json: '' })
if (!args._.length) { console.error('usage: node axe.mjs <url>... [--impact serious,critical] [--min-font 12]'); process.exit(2) }
const impacts = new Set(args.impact.split(',').map(s => s.trim()).filter(Boolean))

let axeSource = null
if (!args['no-axe']) {
  const axePath = resolvePath('AXE_CORE_PATH', 'axe-core/axe.min.js')
  if (!axePath) unavailable('AXE_UNAVAILABLE', 'axe-core not found; set AXE_CORE_PATH to axe.min.js or add its node_modules to NODE_PATH')
  try {
    axeSource = readFileSync(axePath, 'utf8')
  } catch (err) {
    unavailable('AXE_UNAVAILABLE', `cannot read ${axePath}: ${err.code || err.message}`)
  }
}

const browser = await launch()
const pages = []
let failed = false
for (const url of args._) {
  for (const vpText of args.viewport) {
    const viewport = parseViewport(vpText)
    const { context, page, status, error } = await openPage(browser, url, viewport)
    const entry = { url, viewport: vpText, status, error }
    let pass = !error
    if (!error && axeSource) {
      await page.addScriptTag({ content: axeSource })
      const result = await page.evaluate(async () => {
        const out = await window.axe.run(document, { resultTypes: ['violations'] })
        return { version: out.testEngine && out.testEngine.version, violations: out.violations.map(v => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, targets: v.nodes.slice(0, 5).map(n => n.target.join(' ')) })) }
      })
      const blocking = result.violations.filter(v => impacts.has(v.impact))
      Object.assign(entry, { axeVersion: result.version, violations: result.violations, blocking: blocking.length })
      pass = pass && blocking.length === 0
    }
    if (!error && args['min-font'] > 0) {
      const fonts = await page.evaluate((limit) => {
        let min = Infinity
        const small = []
        const walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_TEXT)
        const seen = new Set()
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const el = node.parentElement
          if (!el || seen.has(el) || !node.textContent.trim()) continue
          seen.add(el)
          const style = getComputedStyle(el)
          const rect = el.getBoundingClientRect()
          if (style.visibility === 'hidden' || style.display === 'none' || rect.width === 0 || rect.height === 0) continue
          if (el.closest('[aria-hidden="true"], .visually-hidden, .sr-only')) continue
          const size = parseFloat(style.fontSize)
          min = Math.min(min, size)
          if (size < limit && small.length < 10) small.push({ tag: el.tagName.toLowerCase(), size, text: node.textContent.trim().slice(0, 60) })
        }
        return { minFontPx: Number.isFinite(min) ? min : null, belowLimit: small }
      }, args['min-font'])
      Object.assign(entry, fonts)
      pass = pass && fonts.belowLimit.length === 0
    }
    entry.pass = pass
    failed = failed || !pass
    pages.push(entry)
    await context.close()
  }
}
await browser.close()
emit({ check: 'axe', impacts: [...impacts], minFont: args['min-font'] || null, pass: !failed, pages }, args.json)
process.exit(failed ? EXIT_FAIL : EXIT_OK)
