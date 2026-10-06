// usage: node studio_a11y.mjs <studio base url> [--viewport WxH]... [--json OUT]
// Logs in, then runs axe-core (serious+critical) and a horizontal-overflow check on every Studio screen.
// axe-core comes from AXE_CORE_PATH or the axe-core package on NODE_PATH.
import { createRequire } from 'node:module'
import { writeFileSync } from 'node:fs'
import { session, check, finish, go } from './studio_common.mjs'

const argv = process.argv.slice(2); const base = argv[0]
if (!base || base.startsWith('--')) { console.error('usage: node studio_a11y.mjs <url> [--viewport WxH]'); process.exit(2) }
const viewports = []; let out = ''
for (let i = 1; i < argv.length; i++) { if (argv[i] === '--viewport') viewports.push(argv[++i]); else if (argv[i] === '--json') out = argv[++i] }
if (!viewports.length) viewports.push('1440x900', '390x844')
const require = createRequire(import.meta.url)
const axePath = process.env.AXE_CORE_PATH || require.resolve('axe-core/axe.min.js')
const slug = process.env.STUDIO_SLUG || 'el-trabajo-silencioso'
const screens = [['home', '#/'], ['editor', `#/p/${slug}/es-419`], ['translate', `#/p/${slug}/es-419/translate/en`], ['preview', `#/p/${slug}/es-419/preview`], ['publish', `#/p/${slug}/publish`], ['versions', `#/p/${slug}/versions`], ['issues', '#/issues'], ['review', `#/p/${process.env.STUDIO_REVIEW_SLUG || slug}/review`], ['progress', `#/p/${process.env.STUDIO_REVIEW_SLUG || slug}/progress`]]
const report = []
let s
for (const vp of viewports) {
  const [width, height] = vp.split('x').map(Number)
  s = await session(base, { viewport: { width, height }, bypassCSP: true })
  for (const [name, hash] of screens) {
    await go(s, hash); await s.page.waitForTimeout(900)
    await s.page.addScriptTag({ path: axePath })
    const res = await s.page.evaluate(async () => { const r = await axe.run(document, { resultTypes: ['violations'], rules: { 'color-contrast': { enabled: true } } }); return r.violations.filter(v => ['serious', 'critical'].includes(v.impact)).map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.slice(0, 3).map(n => n.target.join(' ')) })) })
    const over = await s.page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }))
    report.push({ screen: name, viewport: vp, violations: res, overflow: over.sw - over.cw })
    check(`axe ${name} ${vp}`, res.length === 0, JSON.stringify(res).slice(0, 400))
    check(`overflow ${name} ${vp}`, over.sw <= over.cw + 1, `${over.sw} > ${over.cw}`)
  }
  if (vp !== viewports[viewports.length - 1]) await s.browser.close()
}
if (out) writeFileSync(out, JSON.stringify(report, null, 1))
await finish(s)
