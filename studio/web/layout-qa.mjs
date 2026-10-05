// Private deterministic screenshots. Cookie arrives only via child environment.
import { launch } from '../../tests/harness/browser/_common.mjs'
import { writeFileSync } from 'node:fs'
const [origin, slug, out] = process.argv.slice(2)
const browser = await launch()
const checks = []; const frames = []
try {
  for (const loc of ['en', 'es-419', 'zh-Hans']) for (const width of [390, 1440]) for (const theme of ['light', 'dark']) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, colorScheme: theme, reducedMotion: 'reduce', extraHTTPHeaders: { Cookie: process.env.LAYOUT_QA_COOKIE } })
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort())
    const page = await context.newPage(); const errors = []
    page.on('pageerror', e => errors.push(String(e)))
    page.on('requestfailed', r => errors.push(new URL(r.url()).pathname))
    const response = await page.goto(`${origin}/preview/${slug}/${loc}/?w=${width}&theme=${theme}`, { waitUntil: 'networkidle' })
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    const name = `${loc}-${width}-${theme}.png`
    await page.screenshot({ path: `${out}/${name}`, fullPage: true }); frames.push(name)
    checks.push({ locale: loc, width, theme, ok: response.status() === 200 && overflow <= 1 && errors.length === 0, overflow, errors })
    await context.close()
  }
} finally { await browser.close() }
const report = { frames, checks }
writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2))
console.log(JSON.stringify(report))
process.exit(checks.every(c => c.ok) ? 0 : 1)
