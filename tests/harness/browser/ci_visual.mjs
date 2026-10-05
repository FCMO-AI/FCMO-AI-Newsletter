// All routes in every published locale at phone and desktop widths.
// Usage: node ci_visual.mjs <base-url> <routes.json> <public-origin>
import { readFileSync } from 'node:fs'
import { launch, openPage } from './_common.mjs'
const [baseText, routesPath, publicOriginText] = process.argv.slice(2)
if (!baseText || !routesPath || !publicOriginText) {
  console.error('usage: node ci_visual.mjs <base-url> <routes.json> <public-origin>')
  process.exit(2)
}

const base = new URL(baseText)
const publicOrigin = new URL(publicOriginText).origin
const basePath = base.pathname.endsWith('/') ? base.pathname : `${base.pathname}/`
const routes = JSON.parse(readFileSync(routesPath, 'utf8'))
if (!routes.some(route => route.path === '404.html')) routes.push({ path: '404.html', locale: 'en' })
const locales = new Set(['en', 'es-419', 'zh-Hans'])
const viewports = [{ width: 390, height: 844 }, { width: 1440, height: 900 }]
const workersCount = Math.min(6, Math.max(1, routes.length))
const errors = []
const internalLinks = new Set()
let cursor = 0

function localCandidateUrl(href, pageUrl) {
  if (!href || href.startsWith('#') || /^(mailto:|tel:|javascript:|data:)/i.test(href)) return null
  let target
  try { target = new URL(href, pageUrl) } catch { return null }
  if (target.origin !== base.origin && target.origin !== publicOrigin) return null
  if (!target.pathname.startsWith(basePath)) return null
  target.hash = ''
  return target
}

async function inspectRoute(browser, route) {
  const pageUrl = new URL(route.path, base).href
  const rowErrors = []
  for (const viewport of viewports) {
    const opened = await openPage(browser, pageUrl, viewport, {
      waitUntil: 'load', timeout: 30000, sameOriginOnly: true,
    })
    const { context, page, status: responseStatus, error: loadError, consoleErrors, failedRequests } = opened
    try {
      if (loadError) rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: browser check failed: ${loadError}`)
      if (responseStatus === null || responseStatus < 200 || responseStatus >= 400)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: document HTTP ${responseStatus}`)
      await page.evaluate(async () => {
        await document.fonts?.ready
        const images = [...document.images]
        for (const image of images) image.loading = 'eager'
        await Promise.race([
          Promise.all(images.map(image => image.decode().catch(() => undefined))),
          new Promise(resolve => setTimeout(resolve, 5000)),
        ])
      })
      const dom = await page.evaluate(() => {
        const root = document.documentElement
        const firstH1 = document.querySelector('h1')
        const images = [...document.images]
          .filter(image => image.complete && image.naturalWidth === 0)
          .map(image => image.currentSrc || image.src)
        const links = [...document.querySelectorAll('a[href]')].map(anchor => anchor.href)
        return {
          language: root.lang || '',
          h1: Boolean(firstH1 && firstH1.textContent.trim()),
          scrollWidth: root.scrollWidth,
          clientWidth: root.clientWidth,
          brokenImages: images,
          links,
        }
      })
      if (!dom.h1) rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: missing or empty h1`)
      if (dom.scrollWidth > dom.clientWidth)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: horizontal overflow ${dom.scrollWidth}>${dom.clientWidth}`)
      for (const image of dom.brokenImages)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: broken image ${image}`)
      if (dom.language !== route.locale)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: html lang=${JSON.stringify(dom.language)}`)
      for (const href of dom.links) {
        const target = localCandidateUrl(href, pageUrl)
        if (target) internalLinks.add(target.href)
      }
      for (const message of consoleErrors)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: console ${message}`)
      for (const message of failedRequests)
        rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: ${message}`)
    } catch (error) {
      rowErrors.push(`${route.locale} ${route.path || '/'} ${viewport.width}px: browser check failed: ${String(error).split('\n')[0]}`)
    } finally {
      await context.close()
    }
  }
  if (rowErrors.length) errors.push(...rowErrors)
}

const foundLocales = new Set(routes.map(route => route.locale))
const missingLocales = [...locales].filter(locale => !foundLocales.has(locale))
if (missingLocales.length) {
  console.error(`visual CI gate requires routes for all locales; missing ${missingLocales.join(', ')}`)
  process.exit(1)
}
if (!routes.length || routes.some(route => typeof route.path !== 'string' || !locales.has(route.locale))) {
  console.error('visual CI gate received an empty or malformed route manifest')
  process.exit(1)
}

const browser = await launch()
const workers = Array.from({ length: workersCount }, async () => {
  while (true) {
    const index = cursor++
    if (index >= routes.length) return
    await inspectRoute(browser, routes[index])
  }
})
await Promise.all(workers)

const linkErrors = []
const linkQueue = [...internalLinks]
let linkCursor = 0
const api = await browser.newPage()
const linkWorkers = Array.from({ length: 8 }, async () => {
  while (true) {
    const index = linkCursor++
    if (index >= linkQueue.length) return
    const href = linkQueue[index]
    const target = new URL(href)
    const localUrl = new URL(target.pathname + target.search, base).href
    try {
      const response = await api.request.get(localUrl, { timeout: 15000, failOnStatusCode: false })
      if (response.status() < 200 || response.status() >= 400)
        linkErrors.push(`broken internal link HTTP ${response.status()} ${target.pathname}${target.search}`)
    } catch (error) {
      linkErrors.push(`broken internal link ${target.pathname}${target.search}: ${String(error).split('\n')[0]}`)
    }
  }
})
await Promise.all(linkWorkers)
await api.close()
await browser.close()

const report = {
  status: errors.length || linkErrors.length ? 'fail' : 'pass',
  pageRoutes: routes.length,
  locales: [...locales],
  viewports,
  routeViewportChecks: routes.length * viewports.length,
  internalLinks: internalLinks.size,
  failures: [...errors, ...linkErrors],
}
console.log(JSON.stringify(report, null, 2))
if (report.failures.length) process.exit(1)
