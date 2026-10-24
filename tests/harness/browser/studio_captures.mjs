// usage: node studio_captures.mjs <studio base url> <slug> <out dir>
// Phone-width (390 px) frames of the editor and the publish sheet, for a human to read.
import fs from 'node:fs'
import { session, go, check, finish } from './studio_common.mjs'

const [base, slug, out] = process.argv.slice(2)
if (!base || !slug || !out) { console.error('usage: node studio_captures.mjs <url> <slug> <out dir>'); process.exit(2) }
fs.mkdirSync(out, { recursive: true })
const s = await session(base, { viewport: { width: 390, height: 844 } }); const { page } = s
const meta = await page.evaluate(async slug => (await fetch(`/api/pieces/${slug}`)).json(), slug)
await go(s, `#/p/${slug}/${meta.source_locale}`)
await page.waitForSelector('.ed-assist')
await page.screenshot({ path: out + '/editor-390.png', fullPage: true })
await go(s, `#/p/${slug}/publish`)
await page.waitForSelector('.distribution'); await page.waitForSelector('.check-list', { state: 'attached' })
await page.waitForTimeout(800)
await page.screenshot({ path: out + '/publicar-390.png', fullPage: true })
const box = page.locator('.distribution input[type=checkbox]')
check('email box is unchecked and disabled while email is off', !(await box.isChecked()) && await box.isDisabled())
check('the sheet explains why', (await page.textContent('.distribution')).includes('todavía no está activo'))
await go(s, '#/')
await page.waitForSelector('.home-head')
await page.screenshot({ path: out + '/inicio-390.png', fullPage: true })
check('rollback is behind Avanzado', await page.locator('details.advanced > summary').count() === 1 && !(await page.locator('details.advanced button').first().isVisible()))
await finish(s)
