// Reproducible bundle: esbuild or the bounded offline compiler, plus local fonts.
import { offlineBundle } from './offline-build.mjs'
import fs from 'node:fs'
import crypto from 'node:crypto'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const dist = path.join(root, 'dist')
let build, fallback
try { ({ build } = await import('esbuild')) } catch (error) {
  if (error.code !== 'ERR_MODULE_NOT_FOUND' || !error.message.includes("'esbuild'")) throw error
  fallback = offlineBundle(root)
}
fs.rmSync(dist, { recursive: true, force: true })
fs.mkdirSync(path.join(dist, 'fonts'), { recursive: true })

if (build) {
  await build({
    entryPoints: [path.join(root, 'src/main.js')], bundle: true, minify: true, format: 'iife', target: 'es2022',
    outfile: path.join(dist, 'app.js'), legalComments: 'none', logLevel: 'warning'
  })
  await build({ entryPoints: [path.join(root, 'src/app.css')], bundle: true, minify: true, outfile: path.join(dist, 'app.css'), loader: { '.woff2': 'file' }, external: ['*.woff2'], logLevel: 'warning' })
} else {
  fs.writeFileSync(path.join(dist, 'app.js'), fallback.js)
  fs.writeFileSync(path.join(dist, 'app.css'), fallback.css)
}

const fontSrc = path.resolve(root, '../../site-src/assets/fonts')
for (const f of fs.readdirSync(fontSrc).sort()) if (f.endsWith('.woff2')) fs.copyFileSync(path.join(fontSrc, f), path.join(dist, 'fonts', f))
fs.copyFileSync(path.join(root, 'src/index.html'), path.join(dist, 'index.html'))
fs.copyFileSync(path.join(root, 'src/favicon.svg'), path.join(dist, 'favicon.svg'))
console.log('Interfaz de Studio reconstruida' + (fallback ? ' (compilación offline del acceso).' : '.'))

// Bind the served artifact to the exact editor source and locked dependencies.
const walk = dir => fs.readdirSync(dir).sort().flatMap(name => { const p = path.join(dir, name); return fs.statSync(p).isDirectory() ? walk(p) : [p] })
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')
const sources = Object.fromEntries(['build.mjs', 'offline-build.mjs', 'package.json', 'package-lock.json', ...walk(path.join(root, 'offline')).map(p => path.relative(root, p)), ...walk(path.join(root, 'src')).map(p => path.relative(root, p)), '../../site-src/assets/css/essay.css', ...fs.readdirSync(fontSrc).sort().filter(p => p.endsWith('.woff2')).map(p => '../../site-src/assets/fonts/' + p)].map(p => [p, hash(path.join(root, p))]))
const artifacts = Object.fromEntries(['app.js', 'app.css', 'index.html'].map(p => [p, hash(path.join(dist, p))]))
fs.writeFileSync(path.join(dist, 'build-manifest.json'), JSON.stringify({ schema: 'fcmo-studio-bundle-v1', sources, artifacts }, null, 2) + '\n')
