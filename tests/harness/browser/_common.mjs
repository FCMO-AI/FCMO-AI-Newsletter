// Shared helpers for the browser harness scripts (first_screen, overflow, axe).
//
// Playwright is not a dependency of this repository. Point Node at an existing
// install with NODE_PATH=<dir>/node_modules (or PLAYWRIGHT_MODULE=<path to the
// playwright package>). CHROME_PATH overrides the browser binary. When Playwright
// cannot be loaded the scripts exit 2 with BROWSER_UNAVAILABLE: never a silent pass.
import { createRequire } from 'node:module'
import { writeFileSync } from 'node:fs'

const require = createRequire(import.meta.url)

export const EXIT_OK = 0
export const EXIT_FAIL = 1
export const EXIT_UNAVAILABLE = 2
export const DEFAULT_VIEWPORTS = ['1440x900', '390x844']

export function unavailable (code, detail) {
  console.error(`${code}: ${detail}`)
  process.exit(EXIT_UNAVAILABLE)
}

export function loadModule (envVar, name) {
  const candidates = []
  if (process.env[envVar]) candidates.push(process.env[envVar])
  candidates.push(name)
  const errors = []
  for (const candidate of candidates) {
    try {
      return require(candidate)
    } catch (err) {
      errors.push(`${candidate}: ${err.code || err.message}`)
    }
  }
  return { error: errors.join('; ') }
}

export function resolvePath (envVar, spec) {
  if (process.env[envVar]) return process.env[envVar]
  try {
    return require.resolve(spec)
  } catch {
    return null
  }
}

export function parseViewport (text) {
  const match = /^(\d+)x(\d+)$/.exec(text)
  if (!match) throw new Error(`bad viewport ${text} (expected WIDTHxHEIGHT)`)
  return { width: Number(match[1]), height: Number(match[2]) }
}

// Minimal flag parser: --name value, --flag, and positional URLs.
export function parseArgs (argv, spec) {
  const out = { _: [] }
  for (const [key, def] of Object.entries(spec)) out[key] = Array.isArray(def) ? [...def] : def
  const seen = new Set()
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (!arg.startsWith('--')) { out._.push(arg); continue }
    const key = arg.slice(2)
    if (!(key in spec)) throw new Error(`unknown option ${arg}`)
    if (typeof spec[key] === 'boolean') { out[key] = true; continue }
    const value = argv[++i]
    if (value === undefined) throw new Error(`option ${arg} needs a value`)
    if (Array.isArray(spec[key])) {
      if (!seen.has(key)) { out[key] = []; seen.add(key) }
      out[key].push(value)
    } else {
      out[key] = typeof spec[key] === 'number' ? Number(value) : value
    }
  }
  return out
}

export async function launch () {
  const pw = loadModule('PLAYWRIGHT_MODULE', 'playwright')
  if (pw.error || !pw.chromium) unavailable('BROWSER_UNAVAILABLE', `cannot load playwright (${pw.error || 'no chromium export'}); set NODE_PATH or PLAYWRIGHT_MODULE`)
  const options = {}
  if (process.env.CHROME_PATH) options.executablePath = process.env.CHROME_PATH
  try {
    return await pw.chromium.launch(options)
  } catch (err) {
    unavailable('BROWSER_UNAVAILABLE', `chromium did not start: ${String(err.message || err).split('\n')[0]}`)
  }
}

// Open url in a fresh context and collect console errors and failed requests.
export async function openPage (browser, url, viewport, { reducedMotion = true } = {}) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1, reducedMotion: reducedMotion ? 'reduce' : 'no-preference' })
  const page = await context.newPage()
  const consoleErrors = []
  const failedRequests = []
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 300)) })
  page.on('pageerror', e => consoleErrors.push('pageerror: ' + String(e).slice(0, 300)))
  page.on('requestfailed', r => failedRequests.push(`${r.url().slice(0, 200)} ${r.failure()?.errorText || ''}`.trim()))
  page.on('response', r => { if (r.status() >= 400) failedRequests.push(`${r.status()} ${r.url().slice(0, 200)}`) })
  let status = null
  let error = null
  try {
    const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
    status = response ? response.status() : null
  } catch (err) {
    error = String(err.message || err).split('\n')[0]
  }
  return { context, page, status, error, consoleErrors, failedRequests }
}

export function emit (report, outPath) {
  const text = JSON.stringify(report, null, 1)
  if (outPath) writeFileSync(outPath, text + '\n')
  console.log(text)
}
