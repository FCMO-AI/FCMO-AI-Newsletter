// Dogfood battery for a THROWAWAY Studio instance (never the live one). See README.md.
// Env: PW_JAVIER, PW_MATIAS (throwaway passwords), FRAMES (screenshot dir, keep it out of the repo), FIGURE (any png), SLUG (flow battery).
import { chromium } from 'playwright'
import fs from 'node:fs'
const [,, PHASE = 'before', BASE = 'http://127.0.0.1:8497'] = process.argv
const OUT = (process.env.FRAMES || './frames')
const PW = { javier: process.env.PW_JAVIER, matias: process.env.PW_MATIAS }
const slug = process.env.SLUG
const only = process.env.ONLY ? process.env.ONLY.split(',') : null
const results = []
const browser = await chromium.launch()
for (const vw of [1440, 390]) for (const scheme of ['light', 'dark']) {
  const cfg = `${vw}-${scheme}`
  const mk = async () => { const ctx = await browser.newContext({ viewport: vw === 1440 ? { width: 1440, height: 900 } : { width: 390, height: 844 }, colorScheme: scheme, isMobile: vw === 390, hasTouch: vw === 390 }); const page = await ctx.newPage(); page.errs = []; page.on('pageerror', e => page.errs.push(String(e))); return { ctx, page } }
  const shot = (page, n, full) => page.screenshot({ path: `${OUT}/${PHASE}-${n}-${cfg}.png`, fullPage: !!full })
  const login = async (page, u) => { await page.goto(BASE + '/'); await page.waitForSelector('#u'); await page.fill('#u', u); await page.fill('#p', PW[u]); await page.click('button[type=submit]'); await page.waitForSelector('.home-head') }
  const noX = async page => { const o = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); return o > 0 ? ' h-overflow ' + o : '' }
  const step = async (task, fn) => { if (only && !only.includes(task.split('-')[0])) return; const t0 = Date.now(); try { const r = await fn(); results.push({ cfg, task, ok: r !== false || false }); console.log(r === false || (typeof r === 'string' && r.includes('FAIL')) ? 'FAIL' : 'PASS', cfg, task, typeof r === 'string' ? r : '', (Date.now() - t0) + 'ms') } catch (e) { console.log('FAIL', cfg, task, String(e).split('\n')[0].slice(0, 200)) } }
  const J = await mk()
  await step('d-translate', async () => {
    await login(J.page, 'javier')
    await J.page.goto(`${BASE}/#/p/${slug}/es-419/translate/en`); await J.page.waitForTimeout(2500); await shot(J.page, 'd1-traducir-en')
    const a = await noX(J.page)
    await J.page.goto(`${BASE}/#/p/${slug}/es-419/translate/zh-Hans`); await J.page.waitForTimeout(2500); await shot(J.page, 'd2-traducir-zh')
    return (await noX(J.page)) + a + ' ' + (await J.page.textContent('main, body')).slice(0, 0)
  })
  await step('e-preview', async () => {
    const t0 = Date.now()
    await J.page.goto(`${BASE}/#/p/${slug}/es-419/preview`)
    await J.page.waitForTimeout(1500); await shot(J.page, 'e0-preview-cargando')
    await J.page.waitForFunction(() => !/Construyendo/.test(document.body.innerText) && document.querySelector('iframe'), null, { timeout: 170000 }); await J.page.waitForTimeout(2500)
    await shot(J.page, 'e1-vista-previa'); return `ready in ${Date.now() - t0}ms` + (await noX(J.page))
  })
  await step('f-publish', async () => {
    await J.page.goto(`${BASE}/#/p/${slug}/publish`); await J.page.waitForTimeout(3000); await shot(J.page, 'f1-publicar', true); return (await noX(J.page))
  })
  await step('h-errors', async () => {
    if (!(await J.page.$('.home-head, .ed-title'))) await login(J.page, 'javier')
    // wrong password
    const W = await mk(); await W.page.goto(BASE + '/'); await W.page.waitForSelector('#u'); await W.page.fill('#u', 'javier'); await W.page.fill('#p', 'not-the-right-password'); await W.page.click('button[type=submit]'); await W.page.waitForSelector('.form-error:not([hidden])'); await shot(W.page, 'h1-clave-mala')
    const msg = await W.page.textContent('.form-error'); await W.ctx.close()
    // double submit new piece
    await J.page.goto(BASE + '/#/'); await J.page.waitForSelector('.home-head'); await J.page.click('button:has-text("Nuevo")'); await J.page.fill('[role=dialog] input[type=text], .modal input[type=text]', 'Doble clic')
    const before = (await J.page.evaluate(() => fetch('/api/pieces').then(r => r.json()))).length
    await J.page.dblclick('button:has-text("Empezar a escribir")'); await J.page.waitForTimeout(3000)
    const after = (await J.page.evaluate(() => fetch('/api/pieces').then(r => r.json()))).length
    const dbl = after - before
    // offline save
    await J.page.waitForSelector('.ed-title'); await J.page.click('.ed-mount .ProseMirror'); await J.ctx.setOffline(true); await J.page.keyboard.type('Escribo sin red.'); await J.page.waitForTimeout(5000); await shot(J.page, 'h2-sin-conexion')
    const st = await J.page.textContent('.save-state'); await J.ctx.setOffline(false); await J.page.waitForTimeout(6000); await shot(J.page, 'h3-reconectado')
    const st2 = await J.page.textContent('.save-state')
    // expired session
    await J.ctx.clearCookies(); await J.page.click('.ed-mount .ProseMirror'); await J.page.keyboard.type(' tras expirar'); await J.page.waitForTimeout(6000); await shot(J.page, 'h4-sesion-expirada')
    const st3 = await J.page.textContent('body'); 
    return `wrong:"${msg}" dbl:+${dbl} offline:"${st}" back:"${st2}" expired-has-login:${!!(await J.page.$('#u'))} expired-notice:${!!(await J.page.$('.login-card .notice'))} ` + (dbl > 1 ? 'FAIL double-submit ' : '') + (await J.page.$('.login-card .notice') ? '' : 'FAIL no-expiry-notice')
  })
  await J.ctx.close()
  const M = await mk()
  await step('g-matias', async () => {
    await login(M.page, 'matias'); await shot(M.page, 'g1-escritorio')
    await M.page.goto(`${BASE}/#/p/${slug}/es-419`); await M.page.waitForSelector('.ed-title'); await M.page.waitForTimeout(1500); await shot(M.page, 'g2-lectura')
    const ro = await M.page.locator('.banner').allTextContents()
    return ro.join('|').slice(0, 120) + (await noX(M.page))
  })
  await M.ctx.close()
}
await browser.close()
