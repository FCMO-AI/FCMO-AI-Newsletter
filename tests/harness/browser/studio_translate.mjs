// usage: node studio_translate.mjs <studio base url> [slug]
// An edit in the source language flags the translated block; footnote and citation chips cannot be typed over.
import { session, go, check, finish } from './studio_common.mjs'

const base = process.argv[2]; const slug = process.argv[3] || 'el-trabajo-silencioso'
if (!base) { console.error('usage: node studio_translate.mjs <url> [slug]'); process.exit(2) }
const s = await session(base); const { page } = s
const saved = () => page.waitForFunction(() => document.querySelector('.save-state')?.textContent === 'Guardado', null, { timeout: 8000 })

const meta = await page.evaluate(async slug => (await fetch(`/api/pieces/${slug}`)).json(), slug)
const source = meta.source_locale; const target = source === 'en' ? 'es-419' : 'en'
await go(s, `#/p/${slug}/${source}/translate/${target}`)
await page.waitForSelector('.tr-row')
check('two aligned columns, one row per source block', await page.locator('.tr-row').count() >= 3)
check('chips are not editable', (await page.locator('.tr-tgt .chip').count()) >= 1 && (await page.locator('.tr-tgt .chip[contenteditable=false]').count()) === (await page.locator('.tr-tgt .chip').count()))
const chipBefore = await page.locator('.tr-tgt .chip').first().textContent()
// typing next to a chip must leave it intact
const rowWithChip = page.locator('.tr-row', { has: page.locator('.tr-tgt .chip') }).first()
await rowWithChip.locator('.tr-edit').click(); await page.keyboard.press('Control+End'); await page.keyboard.type(' (revisado)')
check('chip survives typing beside it', (await rowWithChip.locator('.chip').first().textContent()) === chipBefore)
await saved()
// editing the first target block records the source hash, so a later source change is detected
const first = page.locator('.tr-row').filter({ has: page.locator('.tr-edit') }).first().locator('.tr-edit')
await first.click(); await page.keyboard.press('Control+End'); await page.keyboard.type(' ok'); await saved()
check('no stale flags right after translating', await page.locator('.tr-tgt.stale').count() === 0)

await go(s, `#/p/${slug}/${source}`)
await page.waitForSelector('.ed-body')
await page.evaluate(() => window.__studioEditor.focusStart()); await page.keyboard.press('End'); await page.keyboard.type(' Cambio en el original.')
await saved()
await go(s, `#/p/${slug}/${source}/translate/${target}`); await page.waitForSelector('.tr-row')
check('source edit flags the target block', await page.locator('.tr-tgt.stale').count() >= 1)
check('the flag says so in plain words', (await page.locator('.tr-stale').first().textContent()) === 'El original cambió')
check('machine drafts are badged', (await page.locator('.tr-badge.agent').count()) >= 1 || (await page.locator('.tr-badge.human').count()) >= 1)
await finish(s)
