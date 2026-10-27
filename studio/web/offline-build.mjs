// Reuse the repository's already compiled dependencies when esbuild is absent.
// This bounded fallback compiles the login from current source. Other JS changes
// require esbuild; never hash fresh source over stale executable code.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { publicationBundle } from './offline/publication-compiler.mjs'

const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
export function loginSource (source) {
  const start = source.indexOf('export function login (')
  const end = source.indexOf('\nfunction where ', start)
  if (start < 0 || end < 0) throw Error('La compilación offline necesita la función de acceso conocida; usa esbuild.')
  return { body: source.slice(start, end).replace(/^export /, ''), rest: source.slice(0, start) + source.slice(end) }
}

// Locate the bundled login by behavior, then discover the minifier's current
// local names from that function. Do not couple the fallback to a prior build's
// symbol spellings.
function functionAt (code, marker) {
  const starts = [...code.matchAll(/function\s+([\w$]+)\s*\([^)]*\)\s*\{/g)]
  const containing = []
  for (const match of starts) {
    const open = match.index + match[0].lastIndexOf('{')
    let depth = 0, quote = '', escaped = false
    for (let i = open; i < code.length; i++) {
      const c = code[i]
      if (quote) {
        if (escaped) escaped = false
        else if (c === '\\') escaped = true
        else if (c === quote) quote = ''
        continue
      }
      if (c === '"' || c === "'" || c === '`') { quote = c; continue }
      if (c === '{') depth++
      else if (c === '}' && --depth === 0) {
        if (match.index <= marker && marker < i) containing.push({ name: match[1], start: match.index, end: i + 1 })
        break
      }
    }
  }
  if (containing.length !== 1) throw Error('El bundle offline no contiene una función de acceso única; usa esbuild.')
  return containing[0]
}

export function discoverLoginBindings (code) {
  const marker = code.indexOf('.normalize("NFD").replace(/\\p{M}/gu')
  if (marker < 0) throw Error('El bundle offline no contiene el marcador del acceso; usa esbuild.')
  const fn = functionAt(code, marker)
  const body = code.slice(fn.start, fn.end)
  const one = (pattern, label) => {
    const found = [...body.matchAll(pattern)]
    const names = [...new Set(found.map(match => match[1]))]
    if (names.length !== 1) throw Error(`No se pudo descubrir ${label} en el acceso offline; usa esbuild.`)
    return names[0]
  }
  const bindings = {
    login: fn.name,
    h: one(/([\w$]+)\("form",\{class:"login-card"/g, 'h'),
    t: one(/([\w$]+)\("login\.bad"\)/g, 't'),
    post: one(/([\w$]+)\("\/api\/login",\{/g, 'post'),
    ApiError: one(/instanceof\s*([\w$]+)&&[\w$]+\.status===0/g, 'ApiError')
  }
  if (new Set([bindings.h, bindings.t, bindings.post, bindings.ApiError]).size !== 4) throw Error('Los enlaces del acceso offline no son independientes; usa esbuild.')
  return bindings
}

export function offlineBundle (root) {
  const read = name => fs.readFileSync(path.join(root, name))
  const seed = read('offline/app.seed.js')
  const manifest = JSON.parse(read('offline/seed-manifest.json'))
  if (hash(seed) !== manifest.app_sha256) throw Error('El bundle offline no coincide con su huella.')
  const current = loginSource(read('src/screens-home.js').toString())
  const previous = loginSource(read('offline/screens-home.seed.js').toString())
  if (current.rest !== previous.rest) throw Error('Cambió código fuera del acceso; reconstruye con esbuild.')
  for (const [name, digest] of Object.entries(manifest.sources)) {
    if (['src/screens-home.js', 'src/app.css', 'src/screens-flow.js', 'src/publication-actions.js', 'src/i18n.js'].includes(name)) continue
    if (hash(read(name)) !== digest) throw Error(`La compilación offline no admite cambios en ${name}; usa esbuild.`)
  }
  const actual = fs.readdirSync(path.join(root, 'src')).filter(n => n.endsWith('.js')).sort()
  const expected = Object.keys(manifest.sources).filter(n => n.endsWith('.js')).map(n => path.basename(n)).sort()
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw Error('Hay módulos nuevos; reconstruye con esbuild.')
  const code = seed.toString()
  const tailMatches = [...code.matchAll(/addEventListener\("hashchange",[\w$]+\);/g)]
  if (tailMatches.length !== 1) throw Error('El bundle offline tiene una estructura desconocida.')
  const offset = tailMatches[0].index
  const bindings = discoverLoginBindings(code)
  // The discovered names are validated against this seed's content hash above.
  // No eval, runtime imports, network, new dependencies or minification here.
  const publicationChanged = ['src/screens-flow.js', 'src/publication-actions.js', 'src/i18n.js'].some(name => hash(read(name)) !== manifest.sources[name])
  const publication = publicationChanged ? publicationBundle(root, seed) : ''
  const replacement = `\n{\nconst h = ${bindings.h}, t = ${bindings.t}, post = ${bindings.post}, ApiError = ${bindings.ApiError};\n${current.body}\n${bindings.login} = login;\n}\n`
  const css = read('src/app.css').toString()
  const directive = '@import "../../../site-src/assets/css/essay.css";'
  if (!css.startsWith(directive) || /@import/.test(css.slice(directive.length))) throw Error('El CSS offline necesita imports conocidos; usa esbuild.')
  return { js: code.slice(0, offset) + replacement + publication + code.slice(offset),
    css: read('../../site-src/assets/css/essay.css').toString() + '\n' + css.slice(directive.length) }
}
