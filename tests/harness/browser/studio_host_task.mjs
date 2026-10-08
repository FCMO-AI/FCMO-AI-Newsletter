// A writing/review task on the real listener; no dev API or model responses.
import assert from 'node:assert/strict'
import { writeFileSync } from 'node:fs'
import { session, go, PASS } from './studio_common.mjs'
import { launch } from './_common.mjs'

const [base, out] = process.argv.slice(2)
const slug = process.env.STUDIO_SLUG
const summary = { completed: false, loopback: true, publicPublication: false, checks: [], frames: [] }
const check = (name, ok) => { assert.ok(ok, name); summary.checks.push(name) }
const shot = async (page, name, tag) => {
  const file = `${name}-${tag}.png`
  await page.screenshot({ path: `${out}/${file}`, fullPage: true })
  summary.frames.push(file)
}
let s
try {
  s = await session(base)
  await s.page.getByText('Puedes escribir y revisar. La publicación pública está desactivada.', { exact: true }).waitFor({ timeout: 4000 })
  check('el modo privado declara que publicar está desactivado', true)
  await s.page.getByRole('button', { name: '+ Nuevo ensayo', exact: true }).click()
  await s.page.locator('.modal input[type=text]').fill('Una edición que conserva su evidencia')
  await s.page.locator('.modal input[value=en]').check()
  await s.page.getByRole('button', { name: 'Empezar a escribir', exact: true }).click()
  await s.page.waitForSelector('.ed-body')
  await s.page.locator('.ed-title').fill('Una edición que conserva su evidencia')
  await s.page.evaluate(() => window.__studioEditor.focusEnd())
  const prose = 'A newspaper earns trust when a reader can distinguish a confirmed result from an open question. Every edition should preserve the evidence behind its claims, the limits of that evidence, and the date when the information became available. Newer information can change a conclusion; it should never erase the record of what readers saw earlier.'
  await s.page.keyboard.insertText(prose)
  await s.page.waitForFunction(() => document.querySelector('.save-state')?.textContent === 'Guardado')
  const taskSlug = await s.page.evaluate(() => location.hash.split('/')[2])
  await s.page.reload(); await s.page.waitForSelector('.ed-body')
  check('el ensayo escrito se conserva al recargar', (await s.page.locator('.ed-body').innerText()).includes(prose))
  await go(s, `#/p/${taskSlug}/en/preview`)
  await s.page.frameLocator('.pv-frame').locator('.essay-body').first().waitFor()
  check('el renderer de producción muestra el texto escrito', (await s.page.frameLocator('.pv-frame').locator('.essay-body').allTextContents()).join(' ').includes(prose))
  await shot(s.page, 'tarea-ensayo', '1440-light')
  await go(s, `#/p/${slug}/publish`)
  check('la hoja de publicación declara que la aprobación queda privada', await s.page.locator('.sheet').getByText('La aprobación se guarda en Studio. La publicación pública está desactivada.', { exact: true }).isVisible())
  await s.page.getByRole('button', { name: 'Pedir revisión', exact: true }).click()
  await s.page.waitForSelector('.home-head')
  const review = await s.page.evaluate(async slug => (await fetch(`/api/pieces/${slug}`)).json(), slug)
  check('se pide revisión con los controles reales', review.state === 'in_review')
  await s.browser.close(); s = null
  s = await session(base, { user: 'matias' })
  await s.page.route('**/api/publication-readiness', route => route.fulfill({ status: 200, contentType: 'application/json', body: 'null' }))
  await go(s, `#/p/${slug}/review`)
  check('no se aprueba cuando el modo de publicación no pudo leerse', await s.page.getByRole('button', { name: 'Aprobar revisión privada', exact: true }).isDisabled())
  await s.page.getByText('No se pudo comprobar si la publicación está habilitada. Vuelve a comprobar antes de aprobar.', { exact: true }).waitFor()
  await shot(s.page, 'modo-no-leido', '1440-light')
  await s.page.unroute('**/api/publication-readiness')
  await s.page.getByRole('button', { name: 'Volver a comprobar', exact: true }).click()
  const approve = s.page.getByRole('button', { name: 'Aprobar revisión privada', exact: true })
  await approve.click()
  await s.page.getByText('La aprobación se guarda en Studio. La publicación pública está desactivada.', { exact: true }).waitFor()
  await s.page.locator('.modal').getByRole('button', { name: 'Aprobar revisión privada', exact: true }).click()
  await s.page.waitForSelector('.timeline')
  const status = await s.page.evaluate(async slug => (await fetch(`/api/pieces/${slug}/publication`)).json(), slug)
  check('la otra cuenta aprueba y el texto queda privado', status.state === 'approved' && !(status.urls || []).length)
  await s.browser.close(); s = null
  for (const width of [1440, 390]) for (const scheme of ['light', 'dark']) {
    const tag = `${width}-${scheme}`
    const browser = await launch()
    try {
      const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, colorScheme: scheme, reducedMotion: 'reduce' })
      const page = await context.newPage()
      await page.goto(base); await page.waitForSelector('#u'); await shot(page, '01-login', tag)
    } finally { await browser.close() }
    s = await session(base, { viewport: { width, height: width === 390 ? 844 : 900 }, scheme })
    const screens = [
      ['02-escritorio', '#/', '.home-head'], ['03-editor', `#/p/${taskSlug}/en`, '.ed-body'],
      ['04-idiomas-es', `#/p/${slug}/en/translate/es-419`, '.tr-row'],
      ['05-idiomas-zh', `#/p/${slug}/en/translate/zh-Hans`, '.tr-row'],
      ['06-vista-previa', `#/p/${taskSlug}/en/preview`, '.pv-frame'],
      ['07-publicar', `#/p/${taskSlug}/publish`, '.check-list'],
      ['08-versiones', `#/p/${taskSlug}/versions`, '.ver-list'],
      ['09-ediciones', '#/issues', '.iss'],
      ['10-revision', `#/p/${slug}/review`, '.rv-panes'],
      ['11-progreso-privado', `#/p/${slug}/progress`, '.timeline'],
    ]
    for (const [name, hash, selector] of screens) {
      await go(s, hash); await s.page.waitForSelector(selector, { state: 'attached' })
      if (hash.endsWith('/preview') || hash.endsWith('/review')) await s.page.frameLocator('.pv-frame').locator('.essay-body').first().waitFor()
      await s.page.waitForTimeout(250)
      check(`${name} cabe a ${width} en ${scheme}`, await s.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
      await shot(s.page, name, tag)
    }
    check(`sin errores de navegador ${tag}`, s.errors.length === 0)
    await s.browser.close(); s = null
  }
  summary.completed = true
  writeFileSync(`${out}/acceptance.json`, JSON.stringify(summary, null, 2) + '\n')
  console.log(`${summary.checks.length} comprobaciones; ${summary.frames.length} capturas; publicación pública desactivada.`)
} catch (error) {
  if (s) {
    await s.page.screenshot({ path: `${out}/failure.png`, fullPage: true })
    writeFileSync(`${out}/failure.json`, JSON.stringify({ error: String(error), hash: await s.page.evaluate(() => location.hash), text: await s.page.locator('body').innerText(), errors: s.errors }, null, 2) + '\n')
  }
  throw error
} finally { if (s) await s.browser.close() }
