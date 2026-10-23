// Dogfood battery for a THROWAWAY Studio instance (never the live one). See README.md.
// Env: PW_JAVIER, PW_MATIAS (throwaway passwords), FRAMES (screenshot dir, keep it out of the repo), FIGURE (any png), SLUG (flow battery).
import { chromium } from 'playwright'
import fs from 'node:fs'
const [,, PHASE = 'before', BASE = 'http://127.0.0.1:8497'] = process.argv
const OUT = (process.env.FRAMES || './frames')
const E = JSON.parse(fs.readFileSync(new URL('./essay.json', import.meta.url), 'utf8'))
const results = []
const rec = (cfg, task, ok, note = '') => { results.push({ cfg, task, ok, note }); console.log(ok ? 'PASS' : 'FAIL', cfg, task, note) }
const PW = { javier: process.env.PW_JAVIER, matias: process.env.PW_MATIAS }
const only = process.env.ONLY ? process.env.ONLY.split(',') : null
const browser = await chromium.launch()
async function newCtx (vw, scheme) {
  const ctx = await browser.newContext({ viewport: vw === 1440 ? { width: 1440, height: 900 } : { width: 390, height: 844 }, colorScheme: scheme, deviceScaleFactor: 1, isMobile: vw === 390, hasTouch: vw === 390 })
  const page = await ctx.newPage(); const errs = []
  page.on('pageerror', e => errs.push(String(e))); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()) })
  page.errs = errs
  return { ctx, page }
}
async function login (page, user, pw) {
  await page.goto(BASE + '/', { waitUntil: 'load' })
  await page.waitForSelector('#u')
  await page.fill('#u', user); await page.fill('#p', pw)
  await page.click('button[type=submit]')
}
for (const vw of [1440, 390]) for (const scheme of ['light', 'dark']) {
  const cfg = `${vw}-${scheme}`
  const shot = async (page, name, full = false) => page.screenshot({ path: `${OUT}/${PHASE}-${name}-${cfg}.png`, fullPage: full })
  const step = async (task, fn) => { if (only && !only.includes(task.split('-')[0])) return; try { const r = await fn(); rec(cfg, task, r !== false, typeof r === 'string' ? r : '') } catch (e) { rec(cfg, task, false, String(e).split('\n')[0].slice(0, 160)) } }
  const { ctx, page } = await newCtx(vw, scheme)
  let slug = ''
  // a login screen
  await step('a-login', async () => {
    await page.goto(BASE + '/', { waitUntil: 'load' }); await page.waitForSelector('#u'); await shot(page, 'a1-login')
    await login(page, 'Javier', PW.javier)
    await page.waitForSelector('.home-head', { timeout: 8000 }); await shot(page, 'a2-escritorio')
    const ov = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); return ov > 0 ? 'h-overflow ' + ov : true
  })
  // b write essay
  await step('b-write', async () => {
    await page.click('button:has-text("Nuevo")').catch(() => {})
    await page.waitForSelector('.modal input[type=text], dialog input[type=text], [role=dialog] input[type=text]', { timeout: 5000 })
    await page.fill('[role=dialog] input[type=text], .modal input[type=text]', 'Por qué la lentitud es una forma de precisión')
    await shot(page, 'b0-nuevo')
    await page.click('button:has-text("Empezar a escribir")'); await page.waitForSelector('.ed-title', { timeout: 8000 })
    slug = page.url().split('/p/')[1].split('/')[0]
    await shot(page, 'b1-vacio')
    await page.fill('.ed-title', E.title); await page.fill('.ed-dek', E.dek)
    await page.click('.ed-mount .ProseMirror'); 
    for (let i = 0; i < E.paras.length; i++) {
      await page.keyboard.type(E.paras[i], { delay: 0 }); await page.keyboard.press('Enter')
      if (i === 1) { // figure
        await page.keyboard.type('/'); await page.waitForSelector('.slash-menu:not([hidden])')
        if (i === 1) await shot(page, 'b2-slash')
        const [fc] = await Promise.all([page.waitForEvent('filechooser'), page.keyboard.type('Figura').then(() => page.keyboard.press('Enter'))])
        await fc.setFiles((process.env.FIGURE || './fig1.png')); await page.waitForSelector('.ed-figure img, .ed-figure .fig-missing', { timeout: 15000 })
        await page.waitForTimeout(600)
        await page.click('.ed-mount .ProseMirror > p:last-child').catch(() => {}); await page.keyboard.press('End')
      }
      if (i === 3) { await page.keyboard.type('/'); await page.keyboard.type('Cita destacada'); await page.keyboard.press('Enter'); await page.keyboard.type(E.pull); await page.keyboard.press('Enter'); await page.keyboard.press('Enter') }
      if (i === 5) { await page.keyboard.type('/'); await page.keyboard.type('Nota al pie'); await page.waitForTimeout(150); await page.keyboard.press('Enter'); await page.waitForTimeout(300); await page.keyboard.type(E.fn); await page.waitForTimeout(200); await page.click('.ed-mount .ProseMirror > p:last-child').catch(() => {}) ; await page.keyboard.press('Control+End') }
    }
    await page.waitForTimeout(800)
    const words = await page.textContent('.words').catch(() => '')
    await shot(page, 'b3-ensayo'); await shot(page, 'b4-ensayo-full', true)
    const ov = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)
    const n = { fig: await page.locator('.ed-figure').count(), pull: await page.locator('.ed-mount .essay-pull, .ed-mount blockquote.pullquote, .ed-mount [data-type=pullquote], .ed-mount .pullquote').count(), fn: await page.locator('.note-text').count() }
    return (ov > 0 ? 'h-overflow ' + ov + ' ' : '') + JSON.stringify(n) + ' ' + words
  })
  // c save/reload
  await step('c-save', async () => {
    await page.waitForFunction(() => /Guardado/.test(document.querySelector('.save-state')?.textContent || ''), null, { timeout: 15000 })
    await page.reload({ waitUntil: 'load' }); await page.waitForSelector('.ed-title')
    await page.waitForTimeout(800)
    const t = await page.inputValue('.ed-title'); const txt = await page.textContent('.ed-mount')
    await shot(page, 'c1-recargado')
    return t === E.title && txt.includes('paciencia de quien la escribió') && (await page.locator('.ed-figure').count()) === 1 && (await page.locator('.note-text').count()) === 1
  })
  await ctx.close()
  if (slug) console.log('SLUG', cfg, slug)
}

await browser.close()
