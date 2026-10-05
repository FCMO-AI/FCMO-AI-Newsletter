// usage: node studio_publish.mjs <studio base url> [slug]
// The publish sheet blocks on a missing alt text with a plain sentence; "Llévame ahí" lands on that figure.
import { session, go, check, finish } from './studio_common.mjs'

const base = process.argv[2]; const slug = process.argv[3] || 'el-trabajo-silencioso'
if (!base) { console.error('usage: node studio_publish.mjs <url> [slug]'); process.exit(2) }
const s = await session(base); const { page } = s

const meta = await page.evaluate(async slug => (await fetch(`/api/pieces/${slug}`)).json(), slug)
await go(s, `#/p/${slug}/${meta.source_locale}`)
await page.waitForSelector('.ed-figure textarea')
const alt = page.locator('.ed-figure .fig-field textarea').first()
await alt.fill(''); await page.waitForTimeout(1200)

await go(s, `#/p/${slug}/publish`)
await page.waitForSelector('.check-list', { state: 'attached' })
const todo = page.locator('.check-list li.todo', { hasText: 'texto alternativo' }).first()
check('missing alt text is listed as a plain sentence', await todo.count() === 1, await todo.textContent().catch(() => ''))
check('the request button is blocked', await page.locator('button:has-text("Pedir revisión")').isDisabled())
check('the sheet says how many remain', (await page.textContent('.btn-row')).includes('por resolver'))
check('no code vocabulary on the sheet', !/\b(git|branch|json|sha|gate|commit)\b/i.test(await page.textContent('.sheet')))
await todo.locator('button:has-text("Llévame ahí")').click()
await page.waitForSelector('.ed-figure', { timeout: 8000 })
await page.waitForFunction(() => document.querySelector('.ed-figure.sel, .ed-figure.ProseMirror-selectednode'), null, { timeout: 8000 })
check('"Llévame ahí" selects that figure', true)
const vis = await page.waitForFunction(() => { const r = document.querySelector('.ed-figure').getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 }, null, { timeout: 5000 }).then(() => true, () => false)
check('and brings it into view', vis)

// repair it and the sheet unblocks
await page.locator('.ed-figure .fig-field textarea').first().fill('Una página de registro'); await page.waitForTimeout(1500)
await go(s, `#/p/${slug}/publish`); await page.waitForSelector('.check-list', { state: 'attached' })
check('after fixing, no alt-text item remains open', await page.locator('.check-list li.todo', { hasText: 'texto alternativo' }).count() === 0)
await finish(s)
