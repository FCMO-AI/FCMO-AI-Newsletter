// usage: node studio_frames.mjs <studio base url> <essay site base url> <out dir>
// Contact sheet: every Studio screen and the essay page (en, es, zh) at 390 and 1440, light and dark.
import { mkdirSync } from 'node:fs'
import { session, go } from './studio_common.mjs'

const [studio, essay, out] = process.argv.slice(2)
if (!out) { console.error('usage: node studio_frames.mjs <studio url> <essay site url> <out dir>'); process.exit(2) }
mkdirSync(out, { recursive: true })
const slug = process.env.STUDIO_SLUG || 'el-trabajo-silencioso'
const reviewSlug = process.env.STUDIO_REVIEW_SLUG || slug
const essaySlug = process.env.STUDIO_ESSAY_SLUG || slug
let count = 0
for (const width of [1440, 390]) for (const theme of ['light', 'dark']) {
  const tag = `${width}-${theme}`
  const viewport = { width, height: width > 700 ? 900 : 844 }
  const shot = async (page, name, full = false) => { await page.screenshot({ path: `${out}/${name}-${tag}.png`, fullPage: full }); count++ }
  let s = await session(studio, { viewport, scheme: theme })
  const { page } = s
  await shot(page, '01-escritorio')
  await go(s, `#/p/${slug}/es-419`); await page.waitForSelector('.ed-body'); await page.waitForTimeout(900)
  await shot(page, '02-editor-inicio')
  await page.evaluate(() => scrollTo(0, 880)); await page.waitForTimeout(500); await shot(page, '03-editor-notas-margen')
  await page.evaluate(() => { scrollTo(0, 0); window.__studioEditor.focusEnd() }); await page.keyboard.press('Enter'); await page.keyboard.type('/'); await page.waitForTimeout(500); await shot(page, '04-editor-bloques')
  await page.keyboard.press('Escape'); await page.keyboard.press('Backspace')
  await page.evaluate(() => window.__studioEditor.focusStart())
  await page.click('.rail-btn >> text=Comprobaciones'); await page.waitForTimeout(900); await shot(page, '05-editor-comprobaciones')
  await page.click('.rail-btn >> text=Fuentes'); await page.waitForTimeout(500); await shot(page, '06-editor-fuentes')
  await go(s, `#/p/${slug}/en/translate/es-419`); await page.waitForSelector('.tr-row'); await page.waitForTimeout(500); await shot(page, '07-idiomas')
  await go(s, `#/p/${slug}/es-419/translate/zh-Hans`); await page.waitForSelector('.tr-row'); await page.waitForTimeout(500); await shot(page, '08-idiomas-zh')
  await go(s, `#/p/${slug}/es-419/preview`); await page.waitForSelector('.pv-frame'); await page.waitForTimeout(1800); await shot(page, '09-vista-previa')
  await go(s, `#/p/${slug}/publish`); await page.waitForSelector('.check-list'); await page.waitForTimeout(500); await shot(page, '10-publicar')
  await go(s, `#/p/${slug}/versions`); await page.waitForSelector('.ver-list'); await shot(page, '11-versiones')
  await go(s, '#/issues'); await page.waitForTimeout(500); await shot(page, '12-ediciones')
  await go(s, `#/p/${reviewSlug}/review`); await page.waitForSelector('.rv-panes'); await page.waitForTimeout(1800); await shot(page, '13-revision')
  await go(s, `#/p/${reviewSlug}/progress`)
  await page.waitForSelector('.timeline'); await page.waitForTimeout(300); await shot(page, '14-progreso')
  await s.browser.close()
  // the essay page as a reader gets it
  const { launch } = await import('./_common.mjs'); const browser = await launch()
  for (const [code, prefix] of [['en', ''], ['es', 'es/'], ['zh', 'zh/']]) {
    const ctx = await browser.newContext({ viewport, colorScheme: theme, reducedMotion: 'reduce' }); const p = await ctx.newPage()
    await p.goto(`${essay}${prefix}cartas/${essaySlug}/`, { waitUntil: 'networkidle' }); await p.waitForTimeout(600)
    await p.screenshot({ path: `${out}/15-ensayo-${code}-${tag}.png`, fullPage: true }); count++; await ctx.close()
  }
  await browser.close()
}
console.log(`${count} frames in ${out}`)
