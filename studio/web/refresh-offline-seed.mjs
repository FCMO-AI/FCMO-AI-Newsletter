// Rebuild the bounded offline seed from the current esbuild output.
// Run from any directory with: node studio/web/refresh-offline-seed.mjs
import fs from 'node:fs'
import path from 'node:path'
import crypto from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { discoverLoginBindings } from './offline-build.mjs'
import { build } from 'esbuild'

const root = path.dirname(fileURLToPath(import.meta.url))
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const walk = dir => fs.readdirSync(dir).sort().flatMap(name => {
  const file = path.join(dir, name)
  return fs.statSync(file).isDirectory() ? walk(file) : [file]
})

const js = await build({
  entryPoints: [path.join(root, 'src/main.js')], bundle: true, minify: true, format: 'iife', target: 'es2022',
  write: false, legalComments: 'none', logLevel: 'warning'
})
const app = js.outputFiles[0]?.contents
if (!app) throw Error('esbuild no produjo el bundle JS esperado.')
const bindings = discoverLoginBindings(Buffer.from(app).toString())
const screen = fs.readFileSync(path.join(root, 'src/screens-home.js'))
const seedDir = path.join(root, 'offline')
fs.writeFileSync(path.join(seedDir, 'app.seed.js'), app)
fs.writeFileSync(path.join(seedDir, 'screens-home.seed.js'), screen)

const names = ['package.json', 'package-lock.json', ...walk(path.join(root, 'src')).map(file => path.relative(root, file))]
const sources = Object.fromEntries(names.map(name => [name, hash(fs.readFileSync(path.join(root, name)))]))
const manifest = { app_sha256: hash(app), login_bindings: bindings, sources }
fs.writeFileSync(path.join(seedDir, 'seed-manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
console.log(`Semilla offline actualizada (${bindings.login}; h=${bindings.h}, t=${bindings.t}, post=${bindings.post}, ApiError=${bindings.ApiError}).`)
