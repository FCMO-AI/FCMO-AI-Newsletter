// Reuse the repository's already compiled dependencies when esbuild is absent.
// This bounded fallback compiles the login from current source. Other JS changes
// require esbuild; never hash fresh source over stale executable code.
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'

const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
export function loginSource (source) {
  const start = source.indexOf('export function login (')
  const end = source.indexOf('\nfunction where ', start)
  if (start < 0 || end < 0) throw Error('La compilación offline necesita la función de acceso conocida; usa esbuild.')
  return { body: source.slice(start, end).replace(/^export /, ''), rest: source.slice(0, start) + source.slice(end) }
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
    if (name === 'src/screens-home.js' || name === 'src/app.css') continue
    if (hash(read(name)) !== digest) throw Error(`La compilación offline no admite cambios en ${name}; usa esbuild.`)
  }
  const actual = fs.readdirSync(path.join(root, 'src')).filter(n => n.endsWith('.js')).sort()
  const expected = Object.keys(manifest.sources).filter(n => n.endsWith('.js')).map(n => path.basename(n)).sort()
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw Error('Hay módulos nuevos; reconstruye con esbuild.')
  const tail = 'addEventListener("hashchange",vt);'
  const code = seed.toString()
  const offset = code.lastIndexOf(tail)
  if (offset < 0 || code.indexOf('function di(') < 0) throw Error('El bundle offline tiene una estructura desconocida.')
  // The seed's internal names are pinned by its hash above. No eval, runtime
  // imports, network, new dependencies or minification in the fallback.
  const replacement = '\n{\nconst h = d, t = f, post = Q, ApiError = Fe;\n' + current.body + '\ndi = login;\n}\n'
  const css = read('src/app.css').toString()
  const directive = '@import "../../../site-src/assets/css/essay.css";'
  if (!css.startsWith(directive) || /@import/.test(css.slice(directive.length))) throw Error('El CSS offline necesita imports conocidos; usa esbuild.')
  return { js: code.slice(0, offset) + replacement + code.slice(offset),
    css: read('../../site-src/assets/css/essay.css').toString() + '\n' + css.slice(directive.length) }
}
