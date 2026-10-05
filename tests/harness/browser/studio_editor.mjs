// usage: node studio_editor.mjs <studio base url>   (STUDIO_USER / STUDIO_PASS optional)
// Write 300 words, a footnote, a citation and a figure; reload; go offline mid-typing; reconnect.
import { session, go, check, finish, TINY_PNG } from './studio_common.mjs'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const base = process.argv[2]
if (!base) { console.error('usage: node studio_editor.mjs <url>'); process.exit(2) }
const s = await session(base)
const { page } = s
// Register interception before typing: the protocol subscription is asynchronous.
// Keep it enabled through this journey, so the Enter key cannot race its setup.
page.on('filechooser', () => {})
const words = Array.from({ length: 300 }, (_, i) => ['luz', 'pausa', 'registro', 'promesa', 'clara', 'tiempo'][i % 6]).join(' ')

await page.click('text=Nuevo ensayo')
await page.fill('.modal input[type=text]', 'Prueba de escritura ' + Date.now().toString(36))
await page.click('text=Empezar a escribir')
await page.waitForSelector('.ed-body')
await page.click('.ed-title'); await page.keyboard.type('Una prueba larga'); await page.keyboard.press('Enter'); await page.keyboard.type('Un subtítulo'); await page.keyboard.press('Enter')
await page.keyboard.insertText(words); await page.keyboard.press('Enter')
const stateText = () => page.textContent('.save-state')
const saved = async () => { await page.waitForFunction(() => document.querySelector('.save-state')?.textContent === 'Guardado', null, { timeout: 8000 }) }

// footnote via the slash menu
await page.keyboard.type('/nota al'); await page.waitForSelector('.slash-menu:not([hidden]) .slash-item'); await page.keyboard.press('Enter')
await page.waitForSelector('.note .note-text')
await page.keyboard.type('Esta es la nota.')
check('footnote appears in the notes column', await page.locator('.ed-body sup.fn-ref').count() === 1 && (await page.textContent('.note .note-text')) === 'Esta es la nota.', await page.textContent('.note .note-text'))
await page.evaluate(() => window.__studioEditor.focusEnd()); await page.keyboard.press('Enter')

// citation: make a source from the picker
await page.keyboard.type('[[')
await page.waitForSelector('.modal')
await page.click('.modal >> text=Nueva fuente…')
await page.waitForSelector('.ed-body cite.src-ref')
check('citation inserted through [[ shortcut', await page.locator('.ed-body cite.src-ref').count() === 1)
await page.locator('.drawer input[type=url]').fill('https://example.org/source')
const fields = page.locator('.drawer details label.f input')
await fields.nth(0).fill('Una fuente pública'); await fields.nth(1).fill('Editorial de prueba'); await fields.nth(2).fill('FCMO')
await page.waitForTimeout(1800)
await page.evaluate(() => window.__studioEditor.focusEnd()); await page.keyboard.press('Enter')

// figure through the file chooser (re-encoded to WebP in the browser)
await page.keyboard.type('/figura'); await page.waitForSelector('.slash-menu:not([hidden]) .slash-item')
const chooser = page.waitForEvent('filechooser', {timeout: 10000}).catch(async e => { console.error('CHOOSER', JSON.stringify({errors:s.errors, state:await page.evaluate(()=>({menu:document.querySelector('.slash-menu')?.innerText, hidden:document.querySelector('.slash-menu')?.hidden, active:document.activeElement?.outerHTML.slice(0,100), inputs:document.querySelectorAll('input[type=file]').length, activation:navigator.userActivation.isActive, end:document.querySelector('.ed-body')?.innerText.slice(-100)}))})); throw e }); await page.keyboard.press('Enter')
await (await chooser).setFiles({ name: 'foto.png', mimeType: 'image/png', buffer: TINY_PNG })
await page.waitForSelector('.ed-figure img', { timeout: 8000 })
check('figure inserted with its own fields', await page.locator('.ed-figure .fig-field').count() >= 3)
await page.evaluate(() => window.__studioEditor.focusStart()); await page.keyboard.press('End')
await saved()
const before = await page.evaluate(() => ({ text: document.querySelector('.ed-body').innerText, title: document.querySelector('.ed-title').value, cursor: window.__studioEditor.cursor().anchor }))
const hash = await page.evaluate(() => location.hash)
check('autosave reports Guardado', (await stateText()) === 'Guardado')

await page.reload(); await page.waitForSelector('.ed-body'); await page.waitForTimeout(500)
const after = await page.evaluate(() => ({ text: document.querySelector('.ed-body').innerText, title: document.querySelector('.ed-title').value, cursor: window.__studioEditor.cursor().anchor }))
check('reload keeps the text identical', before.text === after.text && before.title === after.title)
check('reload keeps the cursor', before.cursor === after.cursor, `${before.cursor} vs ${after.cursor}`)
check('300 words survived', after.text.includes(words))
const persistedSources = await page.evaluate(async () => { const slug = location.hash.split('/')[2]; return (await fetch(`/api/pieces/${slug}/sources`)).json() })
check('source survives reload through the real API', persistedSources.length === 1 && persistedSources[0].url === 'https://example.org/source')

// offline mid-typing
await page.evaluate(() => window.__studioEditor.focusEnd())
await s.context.setOffline(true)
await page.keyboard.type(' SIN-RED-uno')
await page.waitForFunction(() => /Sin conexi/.test(document.querySelector('.save-state')?.textContent || ''), null, { timeout: 12000 })
await page.keyboard.type(' SIN-RED-dos')
const buf = await page.evaluate(() => Object.keys(localStorage).filter(k => k.startsWith('studio:buf:')).length)
check('local copy kept while offline', buf >= 1)
await s.context.setOffline(false)
await page.evaluate(() => dispatchEvent(new Event('online')))
await saved()
await page.reload(); await page.waitForSelector('.ed-body')
const txt = await page.evaluate(() => document.querySelector('.ed-body').innerText)
check('nothing lost after reconnecting', txt.includes('SIN-RED-uno') && txt.includes('SIN-RED-dos'))
if (process.env.DOGFOOD_ACTIVE === 'local-bare-only') {
  const drag = spawnSync(process.execPath, [fileURLToPath(new URL('./studio_drag.mjs', import.meta.url)), base], { env: process.env, encoding: 'utf8', timeout: 120000 })
  console.log(drag.stdout || ''); if (drag.status) console.error(drag.stderr)
  check('photo drop and issue reordering in isolated dogfood', drag.status === 0)
  const dialog = spawnSync(process.execPath, [fileURLToPath(new URL('./studio_modal.mjs', import.meta.url)), base], { env: process.env, encoding: 'utf8', timeout: 120000 })
  console.log(dialog.stdout || ''); if (dialog.status) console.error(dialog.stderr)
  check('recovery dialog remains within its screen in isolated dogfood', dialog.status === 0)
}
await finish(s)
